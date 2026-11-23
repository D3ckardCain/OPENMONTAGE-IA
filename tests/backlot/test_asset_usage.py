from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_studio as studio
from lib import production_agent as agent
from lib.project_asset_sources import save,usage


def test_usage_joins_declared_media_with_provenance(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    pid=studio.create_production({'title':'Uso','brief':'Video',
        'pipeline':'animated-explainer','language':'es'})['project_id']
    project=studio.project_path(pid)
    folder=project/'assets';folder.mkdir(exist_ok=True)
    (folder/'one.png').write_bytes(b'own image')
    item={'path':'assets/one.png','source_kind':'own','source_url':'','license_url':'',
          'creator':'','license_name':'','commercial_use':'yes','modifications':'yes','notes':''}
    save(pid,{'entry':item,'expected_revision':None})
    studio.save_json(project/'artifacts/asset_manifest.json',{'version':'1.0','assets':[
        {'id':'1','path':'assets/one.png','type':'image','source_tool':'local','scene_id':'s1'},
        {'id':'2','path':'assets/missing.mp4','type':'video','source_tool':'local','scene_id':'s1'},
        {'id':'3','path':'../outside.mp4','type':'video','source_tool':'local','scene_id':'s1'}]})
    studio.save_json(project/'artifacts/scene_batch.json',{'scenes':[
        {'image':{'path':'assets/one.png'},'takes':[{'path':'assets/missing.mp4'}]}]})
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    first=client.get('/api/studio/asset-usage/'+pid+'?limit=1').json()
    assert first['total']==2 and first['registered_total']==1 and first['unregistered_total']==1
    assert first['rows'][0]['path']=='assets/missing.mp4'
    assert first['next_offset']==1 and first['problems']
    next_page=agent.LocalAgent(pid).dispatch('project_asset_usage',{'offset':1,'limit':1})
    assert first['rows'][0]['file_present'] is False
    assert next_page['rows'][0]['path']=='assets/one.png'
    assert next_page['rows'][0]['declared_in']==['asset_manifest','scene_batch:image']
    assert next_page['next_offset'] is None
    assert client.get('/api/studio/asset-usage/'+pid+'?limit=51').status_code==422


def test_usage_rejects_unbounded_manifest_and_symlink(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    pid=studio.create_production({'title':'Límites','brief':'Video',
        'pipeline':'animated-explainer','language':'es'})['project_id']
    project=studio.project_path(pid)
    studio.save_json(project/'artifacts/asset_manifest.json',{'assets':[{'path':'assets/a.png'}]*501})
    import pytest
    with pytest.raises(ValueError):usage(pid)
    (project/'artifacts/asset_manifest.json').unlink()
    (project/'artifacts/asset_manifest.json').symlink_to(tmp_path/'outside.json')
    with pytest.raises(ValueError):usage(pid)
