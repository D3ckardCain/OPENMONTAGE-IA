"""Real adapter contracts, local file discovery and isolated transport tests.

No model weights are downloaded; dependency APIs use small controlled fixtures.
"""
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace,ModuleType
import pytest
from lib import model_adapters as adapters
from lib import model_adapter_worker as worker
from lib import production_studio as studio
from lib.model_comfy_adapter import graph_config,validate_graph,execute_workflow

@pytest.fixture
def isolated(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    adapters.dependency_probe.cache_clear()
    return tmp_path


def fake_model(root,family):
    e=next(e for e in adapters.CATALOG[family]['entries'] if '/DESCARGAS_MODELOS/' in e['destination'])
    name=e['destination'].split('/DESCARGAS_MODELOS/')[1].split('/')[0]
    path=root/'DESCARGAS_MODELOS'/name;path.mkdir(parents=True)
    for relative in adapters.expected_files(family,path):
        p=path/relative;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text('{}' if p.suffix=='.json' else 'fixture')
    return path


def test_registry_discovers_concrete_family_tools_without_importing_weights(isolated):
    from tools.tool_registry import ToolRegistry
    reg=ToolRegistry();reg.discover('tools.models')
    assert len(reg.list_all())==47
    assert reg.get('model_kokoro').capability=='tts'
    assert reg.get('model_wan').capability=='video_generation'
    assert reg.get('model_m2m100').estimate_cost({})==0


def test_resource_root_finds_models_without_moving_files(isolated,monkeypatch):
    model=fake_model(isolated,'faster-whisper')
    studio.configure({'resource_roots':[str(isolated)]})
    monkeypatch.setattr(adapters,'dependency_probe',lambda *a:{m:True for m in a[1]})
    info=adapters.diagnostics('faster-whisper')
    assert info['ready'] and info['model_dir']==str(model)
    assert not info['inference_verified']
    (model/'model.bin').unlink()
    info=adapters.diagnostics('faster-whisper')
    assert not info['ready'] and 'model.bin' in info['missing_files']


def test_moved_model_and_shard_index_are_checked(isolated,monkeypatch):
    model=fake_model(isolated,'qwen3');moved=isolated/'moved-model';model.rename(moved)
    adapters.configure('qwen3',{'model_dir':str(moved)})
    studio.save_json(moved/'model.safetensors.index.json',{'weight_map':{'parameter':'missing-shard.safetensors'}})
    monkeypatch.setattr(adapters,'dependency_probe',lambda *a:{m:True for m in a[1]})
    assert 'missing-shard.safetensors' in adapters.diagnostics('qwen3')['missing_files']


def test_configuration_and_runtime_remain_independent(isolated):
    adapters.configure('kokoro',{'python_executable':sys.executable,'model_dir':str(isolated/'weights')})
    studio.configure({'model':'local-producer'})
    assert adapters.configuration('kokoro')['model_dir']==str(isolated/'weights')
    with pytest.raises(ValueError):adapters.configure('kokoro',{'python_executable':'relative/python'})
    with pytest.raises(ValueError):adapters.configure('absent',{})


def test_missing_dependencies_block_without_starting_inference(isolated,monkeypatch):
    from tools.models.local_adapters import model_kokoro
    monkeypatch.setattr(adapters,'dependency_probe',lambda *a:{m:False for m in a[1]})
    result=model_kokoro().execute({'output_dir':str(isolated/'outputs'),'text':'Hola'})
    assert not result.success
    assert result.data['adapter']['inference_verified'] is False
    assert not list((isolated/'outputs').glob('*request.json'))


def test_native_adapter_subprocess_uses_offline_environment_and_real_outputs(isolated,monkeypatch):
    from tools.models.local_adapters import model_minilm
    model=fake_model(isolated,'minilm');adapters.configure('minilm',{'model_dir':str(model)})
    monkeypatch.setattr(adapters,'dependency_probe',lambda *a:{m:True for m in a[1]})
    calls=[]
    def run(command,**kwargs):
        calls.append((command,kwargs))
        request=studio.read_json(command[-2]);out=Path(request['output_dir'])/'embedding.json';studio.save_json(out,{'embeddings':[[0.5]]})
        studio.save_json(command[-1],{'success':True,'outputs':[str(out)]})
        return SimpleNamespace(returncode=0,stderr='')
    monkeypatch.setattr(adapters.subprocess,'run',run)
    result=model_minilm().execute({'output_dir':str(isolated/'output'),'text':'contenido original'})
    assert result.success
    env=calls[0][1]['env'];assert env['HF_HUB_OFFLINE']=='1' and env['TRANSFORMERS_OFFLINE']=='1'
    assert env['CUDA_VISIBLE_DEVICES']==''
    assert calls[0][0][0]==sys.executable


def test_native_worker_failure_and_timeout_are_not_success(isolated,monkeypatch):
    from tools.models.local_adapters import model_minilm
    monkeypatch.setattr(adapters,'diagnostics',lambda f:{'ready':True,'backend':'native','model_dir':str(isolated),'python_executable':sys.executable})
    monkeypatch.setattr(adapters.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=1,stderr='Runtime not installed'))
    assert not model_minilm().execute({'output_dir':str(isolated/'output'),'text':'a'}).success
    def timeout(*a,**k):raise subprocess.TimeoutExpired('python',10)
    monkeypatch.setattr(adapters.subprocess,'run',timeout)
    assert 'Timeout' in model_minilm().execute({'output_dir':str(isolated/'output'),'text':'a'}).error


def test_faster_whisper_worker_reads_local_weights_and_writes_timestamps(isolated,monkeypatch):
    model=isolated/'weights';model.mkdir();source=isolated/'voice.wav';source.write_bytes(b'fixture')
    calls=[]
    class Whisper:
        def __init__(self,path,**kwargs):calls.append((path,kwargs))
        def transcribe(self,path,**kwargs):return iter([SimpleNamespace(start=0,end=1,text='Hola',words=[SimpleNamespace(start=0,end=1,word='Hola',probability=.9)])]),SimpleNamespace(language='es',duration=1)
    module=ModuleType('faster_whisper');module.WhisperModel=Whisper;monkeypatch.setitem(sys.modules,'faster_whisper',module)
    result=worker.run({'family':'faster-whisper','model_dir':str(model),'inputs':{'input_path':str(source),'language':'es'},'output_dir':str(isolated)})
    assert calls[0][1]['local_files_only'] is True
    assert studio.read_json(result['outputs'][0])['segments'][0]['words'][0]['word']=='Hola'


def test_worker_cli_failure_returns_machine_readable_response(isolated):
    request=isolated/'request.json';response=isolated/'response.json'
    studio.save_json(request,{'family':'minilm','model_dir':str(isolated/'missing'),'inputs':{},'output_dir':str(isolated)})
    result=subprocess.run([sys.executable,str(Path(worker.__file__)),str(request),str(response)],capture_output=True,text=True)
    assert result.returncode==1
    assert studio.read_json(response)['success'] is False


def graph(family='wan'):
    weight=adapters.CATALOG[family]['entries'][0]['path'].split('/')[-1]
    return {'1':{'class_type':'UNETLoader','inputs':{'unet_name':weight}},'2':{'class_type':'SaveVideo','inputs':{'images':['1',0],'filename_prefix':'fixture'}}}


def test_workflow_requires_real_api_nodes_and_registered_model(isolated,monkeypatch):
    g=graph()
    with pytest.raises(ValueError):graph_config('wan',{'workflow_json':{'nodes':[]}})
    with pytest.raises(ValueError):graph_config('wan',{'workflow_json':g,'output_node':'2','bindings':{'missing':{}}})
    def info(server,path,**kwargs):
        name=path.rsplit('/',1)[-1]
        return {name:{'input':{'required':{'unet_name':[[g['1']['inputs']['unet_name']]]}},'output_node':name=='SaveVideo'}}
    monkeypatch.setattr(studio,'local_request',info)
    validate_graph('wan',g,'2','http://127.0.0.1:8188')
    with pytest.raises(ValueError,match='familia'):validate_graph('mochi',g,'2','http://127.0.0.1:8188')
    g['1']['inputs']['unet_name']='unknown.safetensors'
    with pytest.raises(ValueError):validate_graph('wan',g,'2','http://127.0.0.1:8188')


def test_comfy_export_and_resume_keep_job_identity(isolated,monkeypatch):
    import lib.model_comfy_adapter as comfy
    g=graph();path=isolated/'workflow.json';studio.save_json(path,g)
    adapters.configure('wan',{'workflow_path':str(path),'output_node':'2'})
    monkeypatch.setattr(comfy,'validate_graph',lambda *a:None)
    submissions=[]
    class Client:
        def __init__(self,**kwargs):pass
        def submit(self,g):submissions.append(g);return 'prompt-fixture'
        def poll(self,prompt_id,**kwargs):return {'outputs':{'2':{'video':[{'filename':'server.mp4'}]}}}
        def download(self,filename,subfolder,dest,kind):dest.write_bytes(b'actual download fixture')
    monkeypatch.setattr(comfy,'ComfyUIClient',Client)
    result=execute_workflow('wan',{},isolated)
    assert Path(result['outputs'][0]).suffix=='.mp4'
    result=execute_workflow('wan',{'resume_prompt_id':'prompt-fixture'},isolated)
    assert len(submissions)==1
    with pytest.raises(ValueError):execute_workflow('wan',{'resume_prompt_id':'unrelated'},isolated)

def test_comfy_graph_rejects_declared_paid_api_nodes(isolated,monkeypatch):
    g=graph()
    monkeypatch.setattr(studio,'local_request',lambda server,path,**kw:{path.rsplit('/',1)[-1]:{'api_node':True,'output_node':True}})
    with pytest.raises(ValueError,match='presupuesto cero'):validate_graph('wan',g,'2','http://127.0.0.1:8188')


def test_native_network_guard_covers_connect_and_connect_ex(monkeypatch):
    import socket
    original=socket.socket.connect;original_ex=socket.socket.connect_ex;original_sendto=socket.socket.sendto
    monkeypatch.setattr(socket.socket,'connect',original)
    monkeypatch.setattr(socket.socket,'connect_ex',original_ex)
    monkeypatch.setattr(socket.socket,'sendto',original_sendto)
    worker.block_network()
    # Guard rejection happens before opening any real socket.
    for method in [socket.socket.connect,socket.socket.connect_ex]:
        with pytest.raises(RuntimeError,match='sin red'):method(None,('example.invalid',443))

def test_kokoro_does_not_require_unused_voices(isolated,monkeypatch):
    model=fake_model(isolated,'kokoro');studio.configure({'resource_roots':[str(isolated)]})
    voices=list((model/'voices').glob('*.pt'));assert len(voices)>1
    voices[0].unlink()
    monkeypatch.setattr(adapters,'dependency_probe',lambda *a:{m:True for m in a[1]})
    info=adapters.diagnostics('kokoro')
    assert info['ready']
    assert 'voices/'+voices[0].name in info['optional_missing_files']
    assert voices[1].stem in info['available_voices']


def test_html_weight_blocks_adapter_before_runtime_launch(isolated,monkeypatch):
    from tools.models.local_adapters import model_minilm
    model=fake_model(isolated,'minilm');adapters.configure('minilm',{'model_dir':str(model)})
    weight=next(path for path in model.iterdir() if path.suffix in ('.safetensors','.bin'))
    weight.write_text('<html>Access denied</html>')
    monkeypatch.setattr(adapters,'dependency_probe',lambda *args:{module:True for module in args[1]})
    monkeypatch.setattr(adapters.subprocess,'run',lambda *args,**kwargs:pytest.fail('Invalid weights must not start a process'))
    report=adapters.diagnostics('minilm')
    assert report['ready'] is False and weight.name in report['suspicious_files']
    result=model_minilm().execute({'output_dir':str(isolated/'output'),'text':'fixture'})
    assert result.success is False and 'HTML' in result.error


def test_corrupt_optional_voice_preserves_other_voices_but_cannot_run(isolated,monkeypatch):
    from tools.models.local_adapters import model_kokoro
    model=fake_model(isolated,'kokoro');adapters.configure('kokoro',{'model_dir':str(model)})
    voices=sorted((model/'voices').glob('*.pt'));voice=voices[0]
    voice.write_text('version https://git-lfs.github.com/spec/v1\noid sha256:fixture')
    monkeypatch.setattr(adapters,'dependency_probe',lambda *args:{module:True for module in args[1]})
    monkeypatch.setattr(adapters.subprocess,'run',lambda *args,**kwargs:pytest.fail('Invalid voice must not start a process'))
    report=adapters.diagnostics('kokoro')
    assert report['ready'] is True
    assert voice.stem not in report['available_voices']
    assert 'voices/'+voice.name in report['suspicious_files']
    result=model_kokoro().execute({'output_dir':str(isolated/'output'),'text':'fixture','language':voice.stem[0],'voice':voice.stem})
    assert result.success is False and 'Voz local inválida' in result.error
