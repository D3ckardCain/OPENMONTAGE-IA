import base64
import io

import pytest
from PIL import Image
from lib import production_studio as studio
from lib import model_adapters as adapters
from lib.production_input_image import stage_image
from lib.model_comfy_adapter import prepare_i2v_image


@pytest.fixture
def prepared(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    studio.save_json(studio.PROJECTS_DIR/'one'/'production_request.json',{})
    stream=io.BytesIO();Image.new('RGB',(64,32)).save(stream,format='PNG')
    record=stage_image('one',{'image_base64':base64.b64encode(stream.getvalue()).decode()})
    adapters.configure('wan',{'preset':'wan22-14b-i2v-4step'})
    return tmp_path,record


class FakeClient:
    server_url='http://127.0.0.1:8188'
    def __init__(self):self.uploads=[]
    def upload_image(self,path,name):
        self.uploads.append((path,name))
        return 'registered.png'


def test_transfer_binds_registered_filename_without_mutating_inputs(prepared):
    root,record=prepared;client=FakeClient()
    inputs={'project_id':'one','text':'A moving subject'}
    bound,source=prepare_i2v_image('wan',inputs,client,root/'ledger.json')
    assert bound['server_image']=='registered.png'
    assert 'server_image' not in inputs
    assert len(client.uploads)==1
    assert source['sha256']==record['sha256']


def test_resume_does_not_upload_and_rejects_changed_source(prepared):
    root,record=prepared;client=FakeClient();ledger=root/'ledger.json'
    studio.save_json(ledger,{'prompt_id':'job','server':client.server_url,'source_image':{
        'sha256':record['sha256'],'server_image':'old.png'}})
    bound,_=prepare_i2v_image('wan',{'project_id':'one','text':'Motion','resume_prompt_id':'job'},client,ledger)
    assert bound['server_image']=='old.png' and not client.uploads
    studio.save_json(ledger,{'prompt_id':'different'})
    with pytest.raises(ValueError,match='reanudación'):
        prepare_i2v_image('wan',{'project_id':'one','text':'Motion','resume_prompt_id':'job'},client,ledger)
    assert not client.uploads


def test_invalid_parameters_and_modified_image_never_upload(prepared):
    root,record=prepared;client=FakeClient()
    with pytest.raises(ValueError,match='cuatro'):
        prepare_i2v_image('wan',{'project_id':'one','text':'Motion','steps':20},client,root/'ledger.json')
    (studio.PROJECTS_DIR/'one'/record['relative_path']).write_bytes(b'changed')
    with pytest.raises(ValueError,match='cambió'):
        prepare_i2v_image('wan',{'project_id':'one','text':'Motion'},client,root/'ledger.json')
    assert not client.uploads


def test_explicit_server_image_does_not_upload(prepared):
    root,_=prepared;client=FakeClient()
    bound,source=prepare_i2v_image('wan',{'server_image':'existing.png'},client,root/'ledger.json')
    assert bound['server_image']=='existing.png' and source is None and not client.uploads


def test_execution_timeout_resumes_without_resubmitting_or_uploading(prepared,monkeypatch):
    from lib import model_comfy_adapter as module
    from tools._comfyui.client import ComfyUIError
    root,_=prepared;client=FakeClient();client.submits=0;client.polls=0
    def submit(graph):
        client.submits+=1
        assert graph['97']['inputs']['image']=='registered.png'
        return 'job'
    def poll(*args,**kwargs):
        client.polls+=1
        if client.polls==1:raise ComfyUIError('timeout',prompt_id='job')
        return {'outputs':{'108':{'video':[{'filename':'result.mp4'}]}}}
    client.submit=submit;client.poll=poll
    client.download=lambda filename,subfolder,path,folder_type:path.write_bytes(b'fake-test-media')
    monkeypatch.setattr(module,'ComfyUIClient',lambda **kwargs:client)
    monkeypatch.setattr(module,'validate_graph',lambda *args:None)
    settings={**studio.settings(),'comfyui_url':client.server_url}
    monkeypatch.setattr(studio,'settings',lambda:settings)
    inputs={'project_id':'one','text':'Motion'}
    with pytest.raises(ComfyUIError):module.execute_workflow('wan',inputs,root)
    assert studio.read_json(root/'comfy-wan-job.json')['status']=='recovery_required'
    with pytest.raises(ComfyUIError,match='ya tiene un trabajo') as repeated:
        module.execute_workflow('wan',inputs,root)
    assert repeated.value.prompt_id=='job'
    assert client.submits==1 and len(client.uploads)==1
    result=module.execute_workflow('wan',{**inputs,'resume_prompt_id':'job'},root)
    assert result['success'] is True
    assert client.submits==1 and len(client.uploads)==1
    assert studio.read_json(root/'comfy-wan-job.json')['status']=='completed'


def test_download_failure_preserves_job_for_recovery(prepared,monkeypatch):
    from lib import model_comfy_adapter as module
    from tools._comfyui.client import ComfyUIError
    root,_=prepared;client=FakeClient()
    client.submit=lambda graph:'download-job'
    client.poll=lambda *args,**kwargs:{'outputs':{'108':{'video':[{'filename':'clip.mp4'}]}}}
    def failed_download(*args):raise OSError('disk full fixture')
    client.download=failed_download
    monkeypatch.setattr(module,'ComfyUIClient',lambda **kwargs:client)
    monkeypatch.setattr(module,'validate_graph',lambda *args:None)
    with pytest.raises(ComfyUIError) as error:
        module.execute_workflow('wan',{'project_id':'one','text':'Motion'},root)
    assert error.value.prompt_id=='download-job'
    saved=studio.read_json(root/'comfy-wan-job.json')
    assert saved['status']=='recovery_required' and 'disk full' in saved['last_error']
    assert len(client.uploads)==1


def test_agent_to_real_adapter_bridge_with_simulated_server(prepared,monkeypatch):
    from types import SimpleNamespace
    from lib.production_agent import LocalAgent
    from lib import model_comfy_adapter as module
    from tools.models.local_adapters import model_wan
    root,_=prepared
    studio.save_json(studio.PROJECTS_DIR/'one'/'production_request.json',{
        'project_id':'one','pipeline':'animated-explainer','title':'Fixture','automatic':False})
    monkeypatch.setattr(adapters,'diagnostics',lambda family:{'ready':True,'backend':'comfyui','problems':[]})
    client=FakeClient();submitted=[]
    def submit(graph):submitted.append(graph);return 'agent-job'
    client.submit=submit
    client.poll=lambda *args,**kwargs:{'outputs':{'108':{'video':[{'filename':'clip.mp4'}]}}}
    client.download=lambda filename,subfolder,path,folder_type:path.write_bytes(b'simulated-not-real-video')
    monkeypatch.setattr(module,'ComfyUIClient',lambda **kwargs:client)
    def local_request(server,path,**kwargs):
        name=path.rsplit('/',1)[-1]
        return {name:{'input':{},'output_node':name=='SaveVideo'}}
    monkeypatch.setattr(studio,'local_request',local_request)
    tool=model_wan()
    worker=LocalAgent('one',registry=SimpleNamespace(get=lambda name:tool))
    stage=worker.manifest['stages'][0]
    worker.instruction('skills/'+stage['skill']+'.md')
    worker.instruction('.agents/skills/comfyui/SKILL.md')
    result=worker.dispatch('execute_tool',{'name':'model_wan','inputs':{
        'project_id':'one','text':'Original motion test','output_dir':'assets/i2v-test','seed':0}})
    assert result['success'] is True,result
    assert len(submitted)==1 and len(client.uploads)==1
    assert submitted[0]['97']['inputs']['image']=='registered.png'
    assert submitted[0]['93']['inputs']['text']=='Original motion test'
    assert result['data']['prompt_id']=='agent-job'
    output=studio.PROJECTS_DIR/'one'/'assets/i2v-test'/'wan-0.mp4'
    assert output.read_bytes()==b'simulated-not-real-video'
