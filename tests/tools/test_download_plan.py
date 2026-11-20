import pytest
from lib import production_studio as studio
from lib.download_plan import plan


def fixture_catalog():
    def file(name,status='not_recorded',folder='D:/weights/one'):
        return {'filename':name,'status':status,'destination_folder':folder,'download_url':'https://example.org/'+name,'size_bytes':None}
    return {'inventories':[{'Serie':'A'},{'Serie':'B'}],'groups':[{'id':'one','files':[file('model.safetensors'),file('already.bin','recorded_path_size_unknown'),file('other.bin','possible_elsewhere_size_match')]},{'id':'two','files':[file('model.safetensors',folder='D:/weights/two')]}]}


def test_plan_excludes_recorded_candidates_and_groups_colliding_names(monkeypatch):
    monkeypatch.setattr(studio,'resource_catalog',fixture_catalog)
    report=plan()
    assert report['planned_files']==2 and len(report['folders'])==2
    assert report['filename_collisions_across_folders']==['model.safetensors']
    assert report['excluded']['recorded_path_size_unknown']==1
    assert report['downloads_started']==0


def test_plan_requires_distinct_inventories_and_valid_urls(monkeypatch):
    data=fixture_catalog();data['inventories']=[{'Serie':'A'},{'Serie':'A'}]
    monkeypatch.setattr(studio,'resource_catalog',lambda:data)
    with pytest.raises(ValueError,match='distintos'):plan()
    data['inventories'][1]={'Serie':'B'}
    data['groups'][0]['files'][0]['download_url']='https://user:secret@example.org/file'
    assert plan()['planned_files']==1
    assert len(plan()['without_download_url'])==1


def test_download_plan_api_is_read_only(monkeypatch):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    monkeypatch.setattr(studio,'resource_catalog',fixture_catalog)
    response=TestClient(create_app(),base_url='http://127.0.0.1:4750').get('/api/studio/download-plan')
    assert response.status_code==200
    assert response.json()['downloads_started']==0
