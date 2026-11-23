from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_studio as studio
from lib import production_agent as agent
from lib.project_asset_sources import save,coverage


def test_coverage_pages_registered_and_missing_files(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    pid=studio.create_production({'title':'Cobertura','brief':'Video local',
        'pipeline':'animated-explainer','language':'es'})['project_id']
    project=studio.project_path(pid)
    folder=project/'assets';folder.mkdir(exist_ok=True)
    for i in range(3):(folder/f'asset{i}.png').write_bytes(f'image {i}'.encode())
    (folder/'notes.txt').write_text('No es medio')
    (folder/'outside.png').symlink_to(tmp_path/'not_in_project.png')
    item={'path':'assets/asset0.png','source_kind':'own','source_url':'','license_url':'',
        'creator':'','license_name':'','commercial_use':'yes','modifications':'yes','notes':''}
    save(pid,{'entry':item,'expected_revision':None})
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    base='/api/studio/asset-coverage/'+pid
    first=client.get(base+'?limit=2').json()
    assert first['total']==3 and first['registered_total']==1 and first['unregistered_total']==2
    assert first['skipped_symlinks']==1 and first['complete_scan']
    assert first['next_offset']==2 and len(first['rows'])==2
    assert first['rows'][0]['status']=='registered'
    second=agent.LocalAgent(pid).dispatch('project_asset_coverage',{'offset':2,'limit':2})
    assert len(second['rows'])==1 and second['next_offset'] is None
    assert client.get(base+'?limit=51').status_code==422


def test_coverage_stops_at_bounded_file_count(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    pid=studio.create_production({'title':'Límite','brief':'Video',
        'pipeline':'animated-explainer','language':'es'})['project_id']
    folder=studio.project_path(pid)/'assets';folder.mkdir(exist_ok=True)
    for i in range(1001):(folder/f'{i:04d}.png').touch()
    result=coverage(pid,limit=50)
    assert result['total']==1000 and result['complete_scan'] is False
    assert result['next_offset']==50


def test_coverage_stops_when_many_nonmedia_entries(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    pid=studio.create_production({'title':'Entradas','brief':'Video',
        'pipeline':'animated-explainer','language':'es'})['project_id']
    folder=studio.project_path(pid)/'assets';folder.mkdir(exist_ok=True)
    for i in range(2001):(folder/f'{i:04d}.txt').touch()
    result=coverage(pid)
    assert result['total']==0 and result['complete_scan'] is False
