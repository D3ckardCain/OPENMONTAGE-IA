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
    assert json.loads(c.state['messages'][-1]['content']) == {'error': str(error)}
    assert studio.read_json(c.path)['in_flight'] is None
    instance.chat.side_effect = lambda messages, tools, **kw: (
        message(call(2)) if json.loads(messages[-1]['content'])['error'] == str(error) else None)
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
    instance.chat.return_value = message(call(1))
    instance.dispatch.side_effect = KeyboardInterrupt()
    c = Conversation(instance, INITIAL.copy(), tools=[])
    with pytest.raises(KeyboardInterrupt): c.turn()
    assert studio.read_json(c.path)['in_flight']['call_index'] == 0
    with pytest.raises(Pause, match='AGENT_SESSION_UNCERTAIN'):
        Conversation(instance, INITIAL.copy(), tools=[])
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
    assert summary['summary']['status'] == 'ok'
    assert summary['summary']['data']['artifact_id'] == 'artifact-17'
    assert c.state['compactions'][0]['tool_call_id'] == call_id
    assert studio.read_json(c.path)['messages'][-1]['content'] == c.state['messages'][-1]['content']
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
    assert not (instance.path / 'agent-session-archive').exists()
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
