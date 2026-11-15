"""WAN profile contracts, without model inference or downloads."""
import pytest
from lib import production_studio as studio
from lib import model_adapters as adapters
from lib.model_comfy_adapter import graph_config,validate_graph
from lib.wan_presets import catalog,config,apply_parameters
from fastapi.testclient import TestClient
from backlot.server import create_app

@pytest.fixture
def isolated(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    from lib import production_agent
    monkeypatch.setattr(production_agent,'ACTIVE',{})
    return tmp_path


def test_profile_selection_is_explicit_and_preserves_legacy(isolated):
    assert adapters.configuration('wan')['preset']=='wan22-14b-t2v-4step'
    custom=isolated/'custom.json';studio.save_json(custom,{'graph':'fixture'})
    adapters.configure('wan',{'workflow_path':str(custom),'output_node':'output'})
    assert 'preset' not in adapters.configuration('wan')
    chosen=adapters.configure('wan',{'preset':'wan22-5b-t2v'})
    assert chosen['output_node']=='11' and chosen['workflow_path'].endswith('wan22-5b-t2v.json')
    adapters.configure('wan',{'workflow_path':chosen['workflow_path'],'output_node':chosen['output_node']})
    assert adapters.configuration('wan')['preset']=='wan22-5b-t2v'
    with pytest.raises(ValueError):adapters.configure('kokoro',{'preset':'wan22-5b-t2v'})
    with pytest.raises(ValueError):adapters.configure('wan',{'preset':'unknown'})
    with pytest.raises(ValueError):adapters.configure('wan',{'preset':'wan22-5b-t2v','workflow_path':str(custom)})


def test_5b_graph_requires_only_the_catalogued_5b_stack(isolated):
    adapters.configure('wan',{'preset':'wan22-5b-t2v'})
    graph,output=graph_config('wan',{'text':'An original visual test','seed':0,'width':512,'height':320,'frames':17,'steps':8})
    assert output=='11'
    assert graph['1']['inputs']['unet_name']=='wan2.2_ti2v_5B_fp16.safetensors'
    assert graph['3']['inputs']['vae_name']=='wan2.2_vae.safetensors'
    assert graph['4']['inputs']['text']=='An original visual test'
    assert graph['8']['inputs']['seed']==0
    assert graph['7']['inputs']['length']==17
    assert not any(node['class_type']=='LoraLoaderModelOnly' for node in graph.values())
    expected={e['path'].split('/')[-1] for e in adapters.CATALOG['wan']['entries']}
    assert set(next(x for x in catalog() if x['id']=='wan22-5b-t2v')['required_models'])<=expected

@pytest.mark.parametrize('changes',[{'width':500},{'height':300},{'frames':16},{'text':''}])
def test_invalid_profile_inputs_are_rejected(isolated,changes):
    adapters.configure('wan',{'preset':'wan22-5b-t2v'})
    with pytest.raises(ValueError):graph_config('wan',{'text':'A moving subject',**changes})


def test_14b_steps_and_prompts_cannot_be_confused_with_5b(isolated):
    graph,_=graph_config('wan',{'text':'Original prompt','seed':0})
    assert graph['2']['inputs']['text']=='Original prompt'
    assert graph['12']['inputs']['noise_seed']==0
    assert graph['12']['inputs']['steps']==4
    with pytest.raises(ValueError,match='cuatro'):graph_config('wan',{'text':'Original prompt','steps':20})


def test_node_and_model_registration_are_checked_before_execution(isolated,monkeypatch):
    adapters.configure('wan',{'preset':'wan22-5b-t2v'})
    graph,output=graph_config('wan',{'text':'Original prompt'})
    required={'UNETLoader':('unet_name','wan2.2_ti2v_5B_fp16.safetensors'),'CLIPLoader':('clip_name','umt5_xxl_fp8_e4m3fn_scaled.safetensors'),'VAELoader':('vae_name','wan2.2_vae.safetensors')}
    def lookup(server,path,**kw):
        name=path.rsplit('/',1)[-1];definition={}
        if name in required:field,weight=required[name];definition[field]=[[weight]]
        return {name:{'input':{'required':definition},'output_node':name=='SaveVideo'}}
    monkeypatch.setattr(studio,'local_request',lookup)
    validate_graph('wan',graph,output,'http://127.0.0.1:8188')
    monkeypatch.setattr(studio,'local_request',lambda *a,**kw:{})
    with pytest.raises(ValueError,match='Falta el nodo'):validate_graph('wan',graph,output,'http://127.0.0.1:8188')


def test_preset_api_can_select_5b_without_starting_inference(isolated):
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    assert len(client.get('/api/studio/wan-presets').json()['presets'])==3
    result=client.post('/api/studio/adapters/wan',json={'preset':'wan22-5b-t2v'})
    assert result.status_code==200 and result.json()['preset']=='wan22-5b-t2v'
    assert client.get('/api/studio/wan-presets').json()['current']['preset']=='wan22-5b-t2v'


def test_i2v_profile_requires_image_and_binds_correct_nodes(isolated):
    adapters.configure('wan',{'preset':'wan22-14b-i2v-4step'})
    with pytest.raises(ValueError,match='server_image'):
        graph_config('wan',{'text':'A moving subject'})
    graph,output=graph_config('wan',{'text':'A moving subject','server_image':'source.png',
        'negative_prompt':'blur','seed':0,'width':512,'height':320,'frames':17,'fps':16,'steps':4})
    assert output=='108'
    assert graph['97']['inputs']['image']=='source.png'
    assert graph['93']['inputs']['text']=='A moving subject'
    assert graph['89']['inputs']['text']=='blur'
    assert graph['98']['inputs']['width']==512
    assert graph['98']['inputs']['height']==320
    assert graph['98']['inputs']['length']==17
    assert graph['86']['inputs']['noise_seed']==0
    assert graph['86']['inputs']['steps']==graph['85']['inputs']['steps']==4
    assert graph['94']['inputs']['fps']==16
    assert graph['95']['inputs']['unet_name'].startswith('wan2.2_i2v_high')
    assert graph['96']['inputs']['unet_name'].startswith('wan2.2_i2v_low')
    with pytest.raises(ValueError,match='cuatro'):
        graph_config('wan',{'text':'Motion','server_image':'source.png','steps':20})
    with pytest.raises(ValueError,match='múltiplos'):
        graph_config('wan',{'text':'Motion','server_image':'source.png','width':500})
