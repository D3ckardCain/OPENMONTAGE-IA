"""Explicit synthetic cancellation fixture. Uses Studio stop, never kills Ollama."""
import hashlib
import json
import re
import threading
import time
import uuid
from pathlib import Path
from lib import production_studio as studio, production_agent as agent
from lib.agent_conversation import Conversation
from lib.local_agent_probe import prepared_model

SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _path(pid):
    if not re.fullmatch(r'inference-probe-[0-9a-f]{32}', pid):
        raise ValueError('INFERENCE_PROBE_ID: diagnóstico inválido')
    path = studio.project_path(pid)
    if studio.read_json(path/'production_request.json', {}).get('diagnostic_kind') != 'ollama_cancellation':
        raise ValueError('INFERENCE_PROBE_ID: no es esta fixture')
    return path


def inspect(pid):
    path = _path(pid)
    report = studio.read_json(path/'inference_probe.json', {})
    return {**report, 'project_id': pid, 'job': studio.read_json(path/'job.json', {}),
            'active': pid in agent.ACTIVE}


def _receipts(path):
    messages = studio.read_json(path/'agent_session.json', {}).get('messages', [])
    return [m for m in messages if m.get('role') == 'tool']


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def start(pid=None):
    from lib import production_queue as queue, reference_analysis
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError('INFERENCE_PROBE_CHANGED: reinicia Studio')
    resume = pid is not None
    path = _path(pid) if resume else None
    if resume:
        report = studio.read_json(path/'inference_probe.json', {})
        if report.get('status') != 'stopped' or not report.get('model_unloaded_verified'):
            raise ValueError('INFERENCE_PROBE_RESUME: requiere parada y descarga verificadas')
    pid = pid or 'inference-probe-' + uuid.uuid4().hex
    path = path or studio.PROJECTS_DIR/pid
    with queue.LOCK, agent.ACTIVE_LOCK, reference_analysis.LOCK:
        if queue.WORKER is not None or agent.ACTIVE or reference_analysis.ACTIVE:
            raise ValueError('INFERENCE_PROBE_BUSY: tarea local activa')
        stop = threading.Event()
        thread = threading.Thread(target=_run, args=(pid,path,stop,resume), daemon=True, name=pid)
        agent.ACTIVE[pid] = (thread,stop)
        try:
            if not resume:
                path.mkdir()
                studio.save_json(path/'production_request.json', {'project_id':pid, 'pipeline':'animation',
                    'title':'Diagnóstico sintético de cancelación', 'diagnostic_fixture':True,
                    'diagnostic_kind':'ollama_cancellation'})
            thread.start()
        except BaseException:
            agent.ACTIVE.pop(pid,None)
            raise
    return {'started':True,'project_id':pid, 'resume':resume,
            'stop_url':'/api/studio/projects/'+pid+'/stop',
            'status_url':'/api/studio/agent/probe-cancellation/'+pid}


def _run(pid,path,stop,resume):
    report = studio.read_json(path/'inference_probe.json', {})
    instance = None
    def save(**values):
        report.update(values, updated_at=studio.now())
        studio.save_json(path/'inference_probe.json', report)
    try:
        previous = {key:report.get(key) for key in ('status','transport','model_unloaded_verified','server_inference_stopped_evidence')} if resume else None
        save(status='preparing', cost_usd=0, creative_content_generated=False, probe_sha256=SOURCE_SHA256,
             previous_result=previous, model_unloaded_verified=False, transport={}, resumed=resume,
             server_inference_stopped_evidence='not_verified')
        base,model,tag,show = prepared_model()
        from tools.analysis import freecad_units
        from tools.tool_registry import ToolRegistry
        registry = ToolRegistry()
        registry.register_module(freecad_units)
        instance = agent.LocalAgent(pid, registry=registry, cancel=stop)
        instance.status('running','Diagnóstico textual sintético local')
        instance.instruction('skills/'+instance.manifest['stages'][0]['skill']+'.md')
        save(model=model, model_manifest_digest=tag.get('digest'), model_transport='local_ollama',
             ollama_version=studio.local_request(base,'/api/version').get('version'))
        initial = [{'role':'system','content':'Synthetic transport diagnostic. No tools or real-world content.'},
                   {'role':'user','content':'Reply only OK.' if resume else
                    'Protocol stress fixture: output the sequence A B C D repeatedly, separated by spaces, for 500 repetitions. No explanation.'}]
        if not resume:
            # Explicitly simulated seed message, actual native dispatch and durable receipt.
            args = {'name':'freecad_units','inputs':{'project_id':pid,'source_unit':'in','target_unit':'mm','values':[1]}}
            instance._chat = lambda m,t: {'role':'assistant','tool_calls':[
                {'function':{'name':'execute_tool','arguments':args}}]}
            seed = Conversation(instance, initial, tools=[])
            seed.turn()
            if json.loads(_receipts(path)[0]['content'])['data']['values'] != [25.4]:
                raise ValueError('INFERENCE_PROBE_TOOL: no se confirmó FreeCAD')
            instance._chat = None
            save(seed_model_simulated=True, completed_native_tool_calls=1,
                 completed_receipts_sha256=_digest(_receipts(path)))
        elif _digest(_receipts(path)) != report['completed_receipts_sha256']:
            raise ValueError('INFERENCE_PROBE_RECEIPT_CHANGED: no se reanuda')
        def reject_dispatch(name,args):
            raise ValueError('INFERENCE_PROBE_NO_TOOLS: solo texto; no se ejecutó herramienta')
        instance.dispatch = reject_dispatch
        def progress(evidence): save(status='inferring', transport=evidence)
        conversation = Conversation(instance, initial, tools=[], chat_options={
            'context_tokens':4096, 'max_output_tokens':16 if resume else 512,
            'thinking':False if 'thinking' in show.get('capabilities',[]) else None,
            'stream':True, 'progress':progress})
        try:
            conversation.turn()
        except agent.Pause as exc:
            if exc.status == 'stopped': outcome='stopped'
            elif exc.status == 'awaiting_input': outcome='completed' if resume else 'completed_before_cancel'
            else: raise
        else: raise ValueError('INFERENCE_PROBE_PROTOCOL: respuesta inesperada')
        # Loading alone is not proof of inference; chunks/done and model absence are separate evidence.
        deadline = time.monotonic()+15
        unloaded = False
        while time.monotonic()<deadline:
            if not studio.local_request(base,'/api/ps').get('models'):
                unloaded=True
                break
            time.sleep(0.2)
        unchanged = _digest(_receipts(path)) == report['completed_receipts_sha256']
        save(status=outcome, model_unloaded_verified=unloaded,
             server_inference_stopped_evidence='no_models_loaded_after_exclusive_request' if unloaded else 'not_verified',
             receipts_unchanged=unchanged, resumed=resume,
             model_attempts=conversation.state.get('model_attempts',[]))
        instance.status(outcome,'Diagnóstico: '+outcome+'; transporte y descarga registrados por separado')
    except Exception as exc:
        save(status='blocked',error=str(exc)[:1000])
        if instance: instance.status('blocked',str(exc)[:600])
    finally:
        with agent.ACTIVE_LOCK: agent.ACTIVE.pop(pid,None)
