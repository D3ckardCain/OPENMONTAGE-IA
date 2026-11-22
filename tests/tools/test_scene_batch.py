"""Scene manifests are prepared only from an approved plan; no generation occurs."""
import pytest

from lib import production_studio as studio
from lib.scene_batch import approved_plan,approve_take,prepare,read,record_media


@pytest.fixture
def planned(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    project=studio.PROJECTS_DIR/'demo'
    studio.save_json(project/'production_request.json',{'title':'Demo'})
    plan={'version':'1.0','scenes':[
        {'id':'s01','type':'generated','description':'Aparece Ada','start_seconds':0,'end_seconds':5,
         'character_actions':[{'character_id':'ada','action_sequence':['walk']}]},
        {'id':'s02','type':'generated','description':'Ada viaja','start_seconds':5,'end_seconds':10,
         'character_actions':[{'character_id':'ada','action_sequence':['turn']}]}]}
    checkpoint={'project_id':'demo','status':'completed','human_approved':True,'artifacts':{'scene_plan':plan}}
    studio.save_json(project/'checkpoint_scene_plan.json',checkpoint)
    payload={'aspect_ratio':'9:16','image_prompts':{'s01':'Ada en un puerto','s02':'Ada en un barco'},
             'motion_prompts':{'s01':'Camina','s02':'Gira'},
             'character_anchors':{'ada':'Mismo rostro, abrigo azul y sombrero rojo'}}
    return project,checkpoint,payload


def test_prepare_keeps_order_identity_and_is_idempotent(planned):
    project,checkpoint,payload=planned
    first=prepare('demo',payload)
    assert first['created'] is True and first['manifest']['scene_count']==2
    assert [row['scene_id'] for row in first['manifest']['scenes']]==['s01','s02']
    assert all(row['character_anchors']['ada']==payload['character_anchors']['ada'] for row in first['manifest']['scenes'])
    assert all(row['status']=='planned' and row['takes']==[] and not row['identity_reviewed'] for row in first['manifest']['scenes'])
    assert prepare('demo',payload)['created'] is False
    assert read('demo')['generation_started'] is False
    assert not (project/'renders').exists()


def test_incomplete_or_changed_plan_does_not_overwrite_manifest(planned):
    project,checkpoint,payload=planned
    missing={**payload,'motion_prompts':{'s01':'Camina'}}
    with pytest.raises(ValueError,match='exactamente un prompt'):
        prepare('demo',missing)
    with pytest.raises(ValueError,match='ancla visual'):
        prepare('demo',{**payload,'character_anchors':{}})
    checkpoint['human_approved']=False
    studio.save_json(project/'checkpoint_scene_plan.json',checkpoint)
    with pytest.raises(ValueError,match='Aprueba primero'):
        prepare('demo',payload)
    checkpoint['human_approved']=True
    studio.save_json(project/'checkpoint_scene_plan.json',checkpoint)
    prepare('demo',payload)
    before=(project/'artifacts/scene_batch.json').read_bytes()
    with pytest.raises(ValueError,match='manifiesto distinto'):
        prepare('demo',{**payload,'image_prompts':{**payload['image_prompts'],'s02':'Otra imagen'}})
    assert (project/'artifacts/scene_batch.json').read_bytes()==before


def test_scene_batch_api_exposes_preparation_without_generation(planned):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    _,_,payload=planned
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    assert client.get('/api/studio/scene-batch/demo').json()['available'] is False
    plan=client.get('/api/studio/scene-batch-plan/demo')
    assert plan.status_code==200
    assert [scene['id'] for scene in plan.json()['scenes']]==['s01','s02']
    assert plan.json()['scenes'][0]['character_ids']==['ada']
    assert plan.json()['scene_plan_sha256']==approved_plan('demo')['scene_plan_sha256']
    result=client.post('/api/studio/scene-batch/demo',json=payload)
    assert result.status_code==200 and result.json()['manifest']['scene_count']==2
    assert client.get('/api/studio/scene-batch/demo').json()['generation_started'] is False
    assert client.post('/api/studio/scene-batch/demo',json={}).status_code==400


def test_register_and_approve_existing_local_media(planned,monkeypatch):
    from PIL import Image
    from types import SimpleNamespace
    import lib.scene_batch as batch
    import lib.media_executables as executables
    project,_,payload=planned
    prepare('demo',payload)
    (project/'assets').mkdir()
    Image.new('RGB',(64,64),'blue').save(project/'assets/s01.png')
    (project/'assets/s01.mp4').write_bytes(b'example-video-bytes')
    monkeypatch.setattr(executables,'require_media',lambda name:'ffprobe')
    monkeypatch.setattr(batch.subprocess,'run',lambda *args,**kwargs:SimpleNamespace(returncode=0,stdout='{"streams":[{"codec_type":"video","width":64,"height":64}],"format":{"duration":"5.0"}}'))
    image=record_media('demo',{'scene_id':'s01','kind':'image','relative_path':'assets/s01.png'})
    assert image['scene']['status']=='image_ready'
    take=record_media('demo',{'scene_id':'s01','kind':'video','relative_path':'assets/s01.mp4'})['scene']['takes'][0]
    with pytest.raises(ValueError,match='confirma la revisión'):
        approve_take('demo',{'scene_id':'s01','sha256':take['sha256'],'identity_reviewed':False})
    assert approve_take('demo',{'scene_id':'s01','sha256':take['sha256'],'identity_reviewed':True})['scene']['status']=='approved'
    assert read('demo')['scenes'][0]['approved_take_id']==take['sha256']
    (project/'assets/s01.mp4').write_bytes(b'changed')
    with pytest.raises(ValueError,match='cambió en disco'):
        approve_take('demo',{'scene_id':'s01','sha256':take['sha256'],'identity_reviewed':True})


def test_scene_media_route_rejects_path_escape(planned):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    _,_,payload=planned
    prepare('demo',payload)
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    r=client.post('/api/studio/scene-batch-media/demo',json={'scene_id':'s01','kind':'image','relative_path':'../outside.png'})
    assert r.status_code==400


def test_preview_uses_registered_image_and_does_not_advance(planned,monkeypatch):
    import time
    from types import SimpleNamespace
    from PIL import Image
    from lib import model_adapters,production_agent,reference_analysis
    from lib import model_comfy_adapter
    from lib import scene_batch as batch
    import lib.media_executables as executables
    project,_,payload=planned
    prepare('demo',payload)
    (project/'assets').mkdir()
    Image.new('RGB',(64,64),'blue').save(project/'assets/s01.png')
    record_media('demo',{'scene_id':'s01','kind':'image','relative_path':'assets/s01.png'})
    monkeypatch.setattr(model_adapters,'configuration',lambda family:{'preset':'wan22-14b-i2v-4step'})
    monkeypatch.setattr(model_adapters,'diagnostics',lambda family:{'ready':True})
    monkeypatch.setattr(executables,'require_media',lambda name:'ffprobe')
    monkeypatch.setattr(batch.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout='{"streams":[{"codec_type":"video","width":288,"height":512}],"format":{"duration":"4.0"}}'))
    monkeypatch.setattr(production_agent,'ACTIVE',{})
    monkeypatch.setattr(reference_analysis,'ACTIVE',{})
    seen=[]
    def fake_workflow(family,inputs,output):
        seen.append((family,inputs))
        video=output/'wan-0.mp4';video.write_bytes(b'preview')
        return {'outputs':[str(video)]}
    monkeypatch.setattr(model_comfy_adapter,'execute_workflow',fake_workflow)
    result=batch.start_preview('demo','s01')
    assert result['started']
    for _ in range(200):
        if read('demo')['scenes'][0]['takes']:break
        time.sleep(.01)
    assert len(read('demo')['scenes'][0]['takes'])==1
    assert read('demo')['scenes'][1]['takes']==[]
    assert seen[0][0]=='wan' and seen[0][1]['image_sha256']==read('demo')['scenes'][0]['image']['sha256']
    assert seen[0][1]['frames']==49 and seen[0][1]['width']==288


def test_preview_requires_explicit_i2v_profile(planned,monkeypatch):
    from lib import model_adapters
    from lib.scene_batch import start_preview
    _,_,payload=planned
    prepare('demo',payload)
    monkeypatch.setattr(model_adapters,'configuration',lambda family:{'preset':'wan22-14b-t2v-4step'})
    with pytest.raises(ValueError,match='Selecciona explícitamente'):
        start_preview('demo','s01')


def test_edit_readiness_checks_every_approved_take_against_plan(planned,monkeypatch):
    from PIL import Image
    from types import SimpleNamespace
    from lib import scene_batch as batch
    from lib.scene_edit import readiness
    import lib.media_executables as executables
    project,_,payload=planned
    prepare('demo',payload)
    (project/'assets').mkdir()
    monkeypatch.setattr(executables,'require_media',lambda name:'ffprobe')
    monkeypatch.setattr(batch.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout='{"streams":[{"codec_type":"video","width":288,"height":512}],"format":{"duration":"5"}}'))
    for name in ('s01','s02'):
        Image.new('RGB',(288,512),'blue').save(project/'assets'/f'{name}.png')
        (project/'assets'/f'{name}.mp4').write_bytes(name.encode())
        record_media('demo',{'scene_id':name,'kind':'image','relative_path':f'assets/{name}.png'})
        take=record_media('demo',{'scene_id':name,'kind':'video','relative_path':f'assets/{name}.mp4'})['scene']['takes'][0]
        if name=='s01':approve_take('demo',{'scene_id':name,'sha256':take['sha256'],'identity_reviewed':True})
    assert not readiness('demo')['ready']
    assert readiness('demo')['scenes'][0]['ready']
    assert 'Falta una toma aprobada' in readiness('demo')['scenes'][1]['problems'][0]
    second=read('demo')['scenes'][1]['takes'][0]
    approve_take('demo',{'scene_id':'s02','sha256':second['sha256'],'identity_reviewed':True})
    assert readiness('demo')['ready']
    (project/'assets/s01.mp4').write_bytes(b'altered')
    assert not readiness('demo')['ready']
    assert 'Cambió la toma aprobada' in readiness('demo')['scenes'][0]['problems']


def test_silent_scene_preview_requires_explicit_fit_and_records_output(planned,monkeypatch):
    import time
    from PIL import Image
    from types import SimpleNamespace
    from lib import scene_batch as batch,scene_preview,production_agent,reference_analysis
    import lib.media_executables as executables
    project,_,payload=planned
    prepare('demo',payload)
    (project/'assets').mkdir()
    monkeypatch.setattr(executables,'require_media',lambda name:name)
    monkeypatch.setattr(scene_preview,'require_media',lambda name:name)
    def run(cmd,**kwargs):
        if cmd[0]=='ffprobe':
            if 'scene-preview-' in cmd[-1]:
                return SimpleNamespace(returncode=0,stdout='{"streams":[{"codec_type":"video","width":720,"height":1280}],"format":{"duration":"10"}}',stderr='')
            return SimpleNamespace(returncode=0,stdout='{"streams":[{"codec_type":"video","width":288,"height":512}],"format":{"duration":"4"}}',stderr='')
        output=__import__('pathlib').Path(cmd[-1]);output.write_bytes(b'rendered '+output.name.encode())
        return SimpleNamespace(returncode=0,stdout='',stderr='')
    monkeypatch.setattr(batch.subprocess,'run',run)
    monkeypatch.setattr(production_agent,'ACTIVE',{})
    monkeypatch.setattr(reference_analysis,'ACTIVE',{})
    for name in ('s01','s02'):
        Image.new('RGB',(288,512),'blue').save(project/'assets'/f'{name}.png')
        (project/'assets'/f'{name}.mp4').write_bytes(name.encode())
        record_media('demo',{'scene_id':name,'kind':'image','relative_path':f'assets/{name}.png'})
        take=record_media('demo',{'scene_id':name,'kind':'video','relative_path':f'assets/{name}.mp4'})['scene']['takes'][0]
        approve_take('demo',{'scene_id':name,'sha256':take['sha256'],'identity_reviewed':True})
    from lib.scene_edit import readiness
    assert not readiness('demo')['ready']
    assert readiness('demo','trim_or_hold')['ready']
    with pytest.raises(ValueError,match='Montaje pendiente'):
        scene_preview.start('demo','exact')
    scene_preview.start('demo','trim_or_hold')
    for _ in range(200):
        if scene_preview.state('demo')['status']!='running':break
        time.sleep(.01)
    report=scene_preview.state('demo')
    assert report['status']=='completed',report
    assert [item['scene_id'] for item in report['choices']]==['s01','s02']
    assert report['audio_included'] is False
    assert (project/report['output']['path']).is_file()
