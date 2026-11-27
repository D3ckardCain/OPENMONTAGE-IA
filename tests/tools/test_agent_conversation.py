"""Offline protocol simulations; no live model or native application in CI."""
import json
import hashlib
import threading
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from lib.agent_conversation import Conversation
from lib.production_agent import Pause
from lib import production_studio as studio


def call(value, name='numeric', **extra):
    return {'function': {'name': name, 'arguments': {'value': value}}, **extra}


def message(*calls):
    return {'role': 'assistant', 'content': '', 'tool_calls': list(calls)}


@pytest.fixture
def instance(tmp_path):
    return SimpleNamespace(path=tmp_path, request={'synthetic': True}, reads=set(),
        instruction=Mock(), chat=Mock(), dispatch=Mock(), event=Mock(), cancel=threading.Event())


INITIAL = [{'role': 'system', 'content': 'Synthetic numeric fixture only.'},
           {'role': 'user', 'content': 'Use returned values in the next call.'}]


def test_results_and_provenance_reach_next_model_call(instance):
    instance.chat.side_effect = [message(call(1, id='one')), message(call(25.4))]
    result = {'success': True, 'data': {'values': [25.4], 'provenance': {'source_sha256': 'a'*64}}}
    instance.dispatch.return_value = result
    c = Conversation(instance, INITIAL.copy(), tools=[])
    c.turn()
    def next_chat(messages, tools, **kw):
        assert json.loads(messages[-1]['content']) == result
        assert messages[-1]['tool_call_id'] == 'one'
        return message(call(25.4))
    instance.chat.side_effect = next_chat
    c.turn()
    assert instance.dispatch.call_args.args == ('numeric', {'value': 25.4})
    saved = studio.read_json(c.path)
    assert saved['next_call'] == 1 and saved['in_flight'] is None
    assert all(item.get('conversation_attempt_id') for item in saved['tool_call_history'])


def test_cancel_and_new_instance_resume_remaining_call_without_replay(instance):
    instance.chat.return_value = message(call(1), call(2))
    def dispatch(name, args):
        instance.cancel.set()
        return {'value': args['value']}
    instance.dispatch.side_effect = dispatch
    c = Conversation(instance, INITIAL.copy(), tools=[])
    with pytest.raises(Pause) as stopped: c.turn()
    assert stopped.value.status == 'stopped'
    assert studio.read_json(c.path)['next_call'] == 1
    instance.cancel.clear()
    instance.dispatch.side_effect = None
    instance.dispatch.return_value = {'value': 2}
    # A distinct transport object reads the on-disk receipt, not in-memory state.
    resumed = Conversation(instance, INITIAL.copy(), tools=[])
    resumed.turn()
    assert instance.chat.call_count == 1
    assert [c.args[1]['value'] for c in instance.dispatch.call_args_list] == [1, 2]
    assert len([m for m in resumed.state['messages'] if m['role'] == 'tool']) == 2


def test_cancel_before_model_makes_no_request(instance):
    instance.cancel.set()
    with pytest.raises(Pause): Conversation(instance, INITIAL.copy(), tools=[]).turn()
    instance.chat.assert_not_called()
    instance.dispatch.assert_not_called()


def test_initial_context_is_not_mutated_or_duplicated_on_resume(instance):
    from copy import deepcopy
    initial=deepcopy(INITIAL)
    instance.chat.return_value=message(call(1))
    instance.dispatch.return_value={'success':True}
    Conversation(instance,initial,tools=[]).turn()
    assert initial==INITIAL
    instance.chat.return_value={'role':'assistant','content':'OK'}
    resumed=Conversation(instance,initial,tools=[])
    with pytest.raises(Pause):resumed.turn()
    assert len([m for m in resumed.state['messages'] if m.get('role')=='tool'])==1


@pytest.mark.parametrize('error', [ValueError('invalid units'), OSError('isolated worker timeout')])
def test_errors_are_delivered_to_next_model_without_success_claim(instance, error):
    instance.chat.return_value = message(call(1))
    instance.dispatch.side_effect = error
    c = Conversation(instance, INITIAL.copy(), tools=[])
    c.turn()
    receipt=json.loads(c.state['messages'][-1]['content'])
    assert receipt['error']['message']==str(error)
    assert receipt['error']['outcome']=='unknown'
    assert receipt['error']['retryable'] is False
    assert receipt['error']['reconcile_before_retry'] is True
    assert studio.read_json(c.path)['in_flight'] is None
    instance.chat.side_effect = lambda messages, tools, **kw: (
        message(call(2)) if json.loads(messages[-1]['content'])['error']['message'] == str(error) else None)
    instance.dispatch.side_effect = None
    instance.dispatch.return_value = {'success': True}
    c.turn()


def test_malformed_arguments_are_structured_error_not_crash(instance):
    instance.chat.return_value = message({'function': {'name': 'numeric', 'arguments': '{bad json'}})
    c = Conversation(instance, INITIAL.copy(), tools=[])
    c.turn()
    assert 'error' in json.loads(c.state['messages'][-1]['content'])
    instance.dispatch.assert_not_called()


def test_interruption_after_intent_blocks_unsafe_replay(instance):
    instance.chat.return_value = message(call('synthetic-private-argument', id='call-uncertain-1'))
    instance.dispatch.side_effect = KeyboardInterrupt()
    c = Conversation(instance, INITIAL.copy(), tools=[])
    with pytest.raises(KeyboardInterrupt): c.turn()
    saved = studio.read_json(c.path)
    assert saved['in_flight']['call_index'] == 0
    attempt_id = saved['in_flight']['conversation_attempt_id']
    assert len(attempt_id) == 32
    with pytest.raises(Pause, match='AGENT_SESSION_UNCERTAIN') as blocked:
        Conversation(instance, INITIAL.copy(), tools=[])
    message_text = str(blocked.value)
    assert 'tool=numeric' in message_text
    assert 'tool_call_id=call-uncertain-1' in message_text
    assert f'conversation_attempt_id={attempt_id}' in message_text
    assert 'request_id=not_recorded' in message_text
    assert 'synthetic-private-argument' not in message_text
    assert instance.dispatch.call_count == 1


def test_failed_receipt_write_keeps_uncertain_intent_on_disk(instance, monkeypatch):
    instance.chat.return_value = message(call(1), call(2))
    instance.dispatch.return_value = {'success': True}
    c = Conversation(instance, INITIAL.copy(), tools=[])
    save = studio.save_json
    def fail_receipt(path, value):
        if value.get('next_call') == 1:
            raise OSError('synthetic disk failure after dispatch')
        return save(path, value)
    monkeypatch.setattr(studio, 'save_json', fail_receipt)
    with pytest.raises(OSError, match='disk failure'): c.turn()
    assert instance.dispatch.call_count == 1
    assert studio.read_json(c.path)['in_flight'] is not None
    with pytest.raises(Pause, match='AGENT_SESSION_UNCERTAIN'):
        Conversation(instance, INITIAL.copy(), tools=[])


def test_gate_pause_stops_batch_and_is_not_replayed(instance):
    instance.chat.return_value = message(call(1, 'checkpoint'), call(2, 'should_not_run'))
    instance.dispatch.side_effect = Pause('awaiting_human', 'Review required')
    c = Conversation(instance, INITIAL.copy(), tools=[])
    with pytest.raises(Pause): c.turn()
    assert c.state['in_flight'] is None
    assert c.state['next_call'] == len(c.state['pending']) == 1
    instance.dispatch.assert_called_once()


def test_request_change_blocks_and_legacy_evidence_preserved(instance):
    studio.save_json(instance.path/'agent_session.json', {'messages': ['historical']})
    Conversation(instance, INITIAL.copy(), tools=[])
    assert studio.read_json(instance.path/'agent_session_legacy.json')['messages'] == ['historical']
    instance.request['changed'] = True
    with pytest.raises(Pause, match='AGENT_SESSION_REQUEST_CHANGED'):
        Conversation(instance, INITIAL.copy(), tools=[])


def test_model_failure_keeps_receipts_and_no_dispatch(instance):
    instance.chat.side_effect = OSError('synthetic model timeout')
    c = Conversation(instance, INITIAL.copy(), tools=[])
    with pytest.raises(OSError): c.turn()
    instance.dispatch.assert_not_called()
    assert studio.read_json(c.path)['messages'] == INITIAL


def test_cancelled_inference_keeps_receipts_and_discards_partial_response(instance):
    instance.chat.return_value=message(call(1))
    instance.dispatch.return_value={'success':True,'data':{'value':25.4}}
    c=Conversation(instance,INITIAL.copy(),tools=[])
    c.turn()
    before=[m for m in c.state['messages'] if m.get('role')=='tool']
    instance.last_transport={'transport_closed':True,'server_inference_stopped':'not_verified'}
    instance.chat.side_effect=Pause('stopped','synthetic cancel during read')
    with pytest.raises(Pause):c.turn()
    saved=studio.read_json(c.path)
    assert saved['model_attempts'][-1]['status']=='cancelled'
    assert saved['model_attempts'][-1]['transport']['transport_closed']
    instance.chat.side_effect=None
    instance.chat.return_value={'role':'assistant','content':'OK'}
    resumed=Conversation(instance,INITIAL.copy(),tools=[])
    with pytest.raises(Pause):resumed.turn()
    assert [m for m in resumed.state['messages'] if m.get('role')=='tool']==before
    instance.dispatch.assert_called_once()


@pytest.mark.parametrize('calls', [None, [None], [{'function': None}], [call(1)]*17])
def test_malformed_model_batches_never_dispatch(instance, calls):
    instance.chat.return_value = {'role': 'assistant', 'tool_calls': calls}
    with pytest.raises(ValueError, match='AGENT_PROTOCOL'):
        Conversation(instance, INITIAL.copy(), tools=[]).turn()
    instance.dispatch.assert_not_called()


def test_completed_large_receipt_is_archived_and_summarized_without_losing_pair(instance):
    c = Conversation(instance, INITIAL.copy(), tools=[])
    call_id = 'receipt-large-1'
    complete = json.dumps({'status': 'ok', 'data': {'artifact_id': 'artifact-17', 'text': 'x' * 91000},
                           'provenance': {'source_sha256': 'a' * 64}}, separators=(',', ':'))
    c.state['messages'].extend([
        {'role': 'assistant', 'content': '', 'tool_calls': [{'id': call_id, 'function': {'name': 'read_fixture'}}]},
        {'role': 'tool', 'tool_name': 'read_fixture', 'tool_call_id': call_id, 'content': complete},
    ])
    c.state.update(pending=[{'id': call_id, 'function': {'name': 'read_fixture'}}], next_call=1, in_flight=None)

    result = c.compact_completed_context()
    summary = json.loads(c.state['messages'][-1]['content'])
    archive = instance.path / summary['archive_path']
    record = json.loads(archive.read_text(encoding='utf-8'))

    assert result['compacted'] == 1
    assert result['characters_after'] < result['characters_before']
    assert c.state['messages'][-2]['tool_calls'][0]['id'] == c.state['messages'][-1]['tool_call_id'] == call_id
    assert summary['receipt_sha256'] == hashlib.sha256(complete.encode('utf-8')).hexdigest()
    assert record['content'] == complete and record['receipt_sha256'] == summary['receipt_sha256']
    assert summary['artifact_name'].startswith('agent_receipt_')
    assert summary['summary']['status'] == 'ok'
    assert summary['summary']['data']['artifact_id'] == 'artifact-17'
    assert c.state['compactions'][0]['tool_call_id'] == call_id
    assert studio.read_json(c.path)['messages'][-1]['content'] == c.state['messages'][-1]['content']
    instance.dispatch.assert_not_called()



def test_aggregate_medium_receipts_compact_without_breaking_pairs(instance):
    c = Conversation(instance, INITIAL.copy(), tools=[])
    messages = list(INITIAL)
    messages.append({'role': 'user', 'content': 'context-' * 9000})
    pending = []
    originals = []
    for index in range(3):
        call_id = f'medium-receipt-{index}'
        call = {'id': call_id, 'function': {'name': 'read_fixture', 'arguments': {'page': index}}}
        receipt = json.dumps({'status': 'ok', 'data': {'text': chr(97 + index) * 9000}},
                             separators=(',', ':'))
        pending.append(call)
        originals.append((call_id, receipt))
        messages.extend([
            {'role': 'assistant', 'content': '', 'tool_calls': [call]},
            {'role': 'tool', 'tool_name': 'read_fixture', 'tool_call_id': call_id, 'content': receipt},
        ])
    c.state['messages'] = messages
    c.state.update(pending=pending, next_call=len(pending), in_flight=None)
    c.save()

    result = c.compact_completed_context()

    assert result['compacted'] >= 1
    assert result['characters_before'] > 90000
    assert result['characters_after'] <= 90000
    for index, (call_id, original) in enumerate(originals):
        assistant, tool = messages[3 + 2 * index], messages[4 + 2 * index]
        assert assistant['tool_calls'][0]['id'] == tool['tool_call_id'] == call_id
        if json.loads(tool['content']).get('compacted'):
            summary = json.loads(tool['content'])
            archive = instance.path / summary['archive_path']
            record = json.loads(archive.read_text(encoding='utf-8'))
            assert record['content'] == original
            assert record['receipt_sha256'] == hashlib.sha256(original.encode('utf-8')).hexdigest()
            assert summary['receipt_characters'] == len(original)
    assert c.state['compactions']
    assert studio.read_json(c.path)['messages'] == c.state['messages']
    instance.dispatch.assert_not_called()

def test_uncertain_or_incomplete_batch_is_never_compacted(instance):
    c = Conversation(instance, INITIAL.copy(), tools=[])
    complete = json.dumps({'data': {'text': 'y' * 20000}})
    c.state['messages'].append({'role': 'tool', 'tool_name': 'read_fixture', 'content': complete})
    c.state.update(pending=[{'function': {'name': 'write_fixture'}}], next_call=0,
                   in_flight={'call_index': 0, 'function': {'name': 'write_fixture'}})
    c.save()

    before = c.state['messages'][-1]['content']
    result = c.compact_completed_context()

    assert result == {'compacted': 0, 'reason': 'batch_incomplete'}
    assert c.state['messages'][-1]['content'] == before
    assert not list((instance.path / 'artifacts').glob('agent_receipt_*.json'))
    assert studio.read_json(c.path)['in_flight']['call_index'] == 0


def test_prepared_native_conversion_cancel_resume_with_simulated_model(tmp_path, monkeypatch):
    """Optional native FreeCAD; deterministic fake model, never Ollama or geometry."""
    from lib import production_agent as agent
    from tools.analysis import freecad_units
    from tools.tool_registry import ToolRegistry
    if freecad_units.FreecadUnits().get_status().value != 'available':
        pytest.skip('Prepared FreeCAD runtime required for native cancellation fixture')
    monkeypatch.setattr(studio, 'PROJECTS_DIR', tmp_path)
    pid = 'synthetic-native-resume'
    path = tmp_path/pid
    path.mkdir()
    studio.save_json(path/'production_request.json', {'project_id': pid, 'pipeline': 'animation', 'diagnostic_fixture': True})
    registry = ToolRegistry()
    registry.register_module(freecad_units)
    calls = []
    for source, target, values in [('in', 'mm', [1]), ('mm', 'cm', [25.4])]:
        calls.append({'function': {'name': 'execute_tool', 'arguments': {'name': 'freecad_units',
            'inputs': {'project_id': pid, 'source_unit': source, 'target_unit': target, 'values': values}}}})
    model = Mock(return_value=message(*calls))
    first = agent.LocalAgent(pid, registry=registry, chat=model)
    first.instruction('skills/'+first.manifest['stages'][0]['skill']+'.md')
    original = first.dispatch
    def stop_after_native(name, args):
        r = original(name, args)
        assert r['success'] and r['data']['values'] == [25.4]
        first.cancel.set()
        return r
    first.dispatch = stop_after_native
    with pytest.raises(Pause): Conversation(first, INITIAL.copy(), tools=[]).turn()
    second = agent.LocalAgent(pid, registry=registry, chat=Mock(side_effect=AssertionError('No extra model call on resume')))
    resumed = Conversation(second, INITIAL.copy(), tools=[])
    resumed.turn()
    receipts = [json.loads(m['content']) for m in resumed.state['messages'] if m['role'] == 'tool']
    assert [r['data']['values'] for r in receipts] == [[25.4], [2.54]]
    assert all(r['data']['provenance']['network_accessed'] is False for r in receipts)
    model.assert_called_once()

def test_large_receipt_over_100k_is_archived_before_context_reuse(instance):
    complete=json.dumps({'data':{'text':'x'*110000}},separators=(',',':'))
    instance.chat.side_effect=[message(call(1)),{'role':'assistant','content':'Resultado recibido.'}]
    instance.dispatch.return_value={'payload':complete}
    c=Conversation(instance,INITIAL.copy(),tools=[])
    c.turn()
    assert len(c.state['messages'][-1]['content'])>100000
    with pytest.raises(Pause) as waiting:c.turn()
    assert waiting.value.status=='awaiting_input'
    tool_receipt=next(m for m in reversed(c.state['messages'])
                      if m.get('role')=='tool' and m.get('tool_name')=='numeric')
    summary=json.loads(tool_receipt['content'])
    archive=instance.path/summary['archive_path']
    record=json.loads(archive.read_text(encoding='utf-8'))
    assert json.loads(record['content'])['payload']==complete
    assert summary['receipt_sha256']==hashlib.sha256(record['content'].encode('utf-8')).hexdigest()


def test_identical_tool_call_without_project_progress_stops_before_duplicate(instance):
    instance.chat.side_effect=[message(call(1)),message(call(1))]
    instance.dispatch.return_value={'value':'same'}
    c=Conversation(instance,INITIAL.copy(),tools=[])
    c.turn()
    with pytest.raises(Pause,match='AGENT_LOOP_NO_PROGRESS'):
        c.turn()
    assert instance.dispatch.call_count==1
    assert c.state['tool_call_history'][-1]['before']==c.state['tool_call_history'][-1]['after']
    assert studio.read_json(c.path)['in_flight'] is None


def test_uncertain_write_is_not_replayed_after_project_changes_but_other_work_can_continue(instance):
    instance.chat.side_effect=[message(call(1,id='write-1')),message(call(1,id='write-retry')),
                                message(call(2,id='independent'))]
    def dispatch(name,args):
        if args['value']==1:
            return {'success':False,'request_id':'request-uncertain-1','error':{
                'code':'tool_execution_outcome_unknown','outcome':'unknown',
                'recoverable':True,'retryable':False,'reconcile_before_retry':True}}
        return {'success':True,'data':{'value':2}}
    instance.dispatch.side_effect=dispatch
    c=Conversation(instance,INITIAL.copy(),tools=[])
    c.turn()
    assert c.state['tool_call_history'][-1]['outcome']=='unknown'
    assert c.state['tool_call_history'][-1]['request_id']=='request-uncertain-1'
    studio.save_json(instance.path/'artifacts'/'synthetic-possible-commit.json',{'revision':2})
    with pytest.raises(Pause,match='AGENT_TOOL_OUTCOME_UNCERTAIN') as blocked:c.turn()
    assert 'request-uncertain-1' in str(blocked.value)
    assert instance.dispatch.call_count==1
    c.turn()
    assert instance.dispatch.call_count==2
    assert instance.dispatch.call_args.args==('numeric',{'value':2})



def test_model_usage_from_ollama_is_visible_as_job_event(instance):
    instance.last_transport={'ollama_usage':{'prompt_eval_count':321,'eval_count':17,
        'total_duration':800000,'load_duration':100000,'prompt_eval_duration':400000,'eval_duration':300000}}
    instance.chat.return_value={'role':'assistant','content':'Listo.','tool_calls':[]}
    c=Conversation(instance,INITIAL.copy(),tools=[])
    with pytest.raises(Pause) as paused:c.turn()
    assert str(paused.value)=='Listo.'
    event=next(call for call in instance.event.call_args_list if call.args[0]=='model_usage')
    assert 'prompt 321 tokens' in event.args[1]
    assert 'respuesta 17 tokens' in event.args[1]
    assert 'total 0.8 ms' in event.args[1]
    assert event.kwargs['ollama_usage']==instance.last_transport['ollama_usage']


def test_missing_ollama_usage_does_not_emit_estimated_metrics(instance):
    instance.chat.return_value={'role':'assistant','content':'Listo.','tool_calls':[]}
    with pytest.raises(Pause) as paused:Conversation(instance,INITIAL.copy(),tools=[]).turn()
    assert str(paused.value)=='Listo.'
    assert not any(call.args[0]=='model_usage' for call in instance.event.call_args_list)
