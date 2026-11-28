import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_studio as studio
from lib import production_agent as agent
from lib.editorial_freshness import research_index,current
from lib.project_channel_evidence import project_problem


def entry(path='assets/example.png'):
    return {'path':path,'source_kind':'stock','source_url':'https://example.org/asset',
        'license_url':'https://example.org/license','creator':'Autor','license_name':'Licencia declarada',
        'commercial_use':'unknown','modifications':'unknown','notes':'Revisar alcance antes de publicar'}


def test_asset_provenance_binds_existing_file_and_render(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    pid=studio.create_production({'title':'Procedencia','brief':'Video nuevo',
        'pipeline':'animated-explainer','language':'es'})['project_id']
    project=studio.project_path(pid)
    file=project/'assets/example.png';file.parent.mkdir(exist_ok=True);file.write_bytes(b'local fixture')
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    url='/api/studio/asset-sources/'+pid
    assert client.get(url).json()['status']=='empty'
    saved=client.post(url,json={'entry':entry(),'expected_revision':None}).json()
    assert saved['status']=='draft' and len(saved['entries'])==1
    from lib.project_asset_sources import _hash_file
    before=_hash_file.cache_info().hits
    client.get(url)
    assert _hash_file.cache_info().hits>before
    assert agent.LocalAgent(pid).dispatch('project_asset_sources',{})['revision']==saved['revision']
    assert client.post(url,json={'entry':entry(),'expected_revision':None}).status_code==400
    baseline=research_index(project)
    receipt={'status':'passed','finished_at':'2026-11-22T10:00:00+00:00','channel_research':baseline}
    assert current(receipt,[],None,baseline)
    studio.save_json(project/'render_verification.json',receipt)
    file.write_bytes(b'changed')
    assert client.get(url).status_code==400
    assert project_problem(project) is not None
    assert research_index(project)=={'invalid':True}
    assert not current(receipt,[],None,research_index(project))
    with pytest.raises(ValueError,match='alterado'):agent.start(pid)


def test_asset_provenance_rejects_external_path_and_missing_license(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    pid=studio.create_production({'title':'Procedencia','brief':'Video',
        'pipeline':'animated-explainer','language':'es'})['project_id']
    from lib.project_asset_sources import save
    for value in ('../outside','assets/../../outside','/absolute'):
        with pytest.raises(ValueError):save(pid,{'entry':entry(value),'expected_revision':None})
    item=entry();item['license_url']=''
    with pytest.raises(ValueError,match='licencia'):save(pid,{'entry':item,'expected_revision':None})
    path=studio.project_path(pid)/'assets/x.png';path.parent.mkdir(exist_ok=True)
    path.symlink_to(tmp_path/'outside')
    with pytest.raises(ValueError):save(pid,{'entry':entry('assets/x.png'),'expected_revision':None})


def test_missing_ledger_after_render_is_blocked(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    pid=studio.create_production({'title':'Procedencia','brief':'Video',
        'pipeline':'animated-explainer','language':'es'})['project_id']
    project=studio.project_path(pid);file=project/'assets/example.png'
    file.parent.mkdir(exist_ok=True);file.write_bytes(b'asset')
    from lib.project_asset_sources import save
    save(pid,{'entry':entry(),'expected_revision':None})
    studio.save_json(project/'render_verification.json',{'channel_research':research_index(project)})
    (project/'artifacts/asset_sources.json').unlink()
    assert project_problem(project) is not None
