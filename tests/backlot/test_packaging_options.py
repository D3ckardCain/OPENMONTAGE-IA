import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_studio as studio
from lib import production_agent as agent
from lib.packaging_options import read,save
from lib.editorial_freshness import research_index,current
from lib.project_channel_evidence import project_problem


def test_packaging_options_selection_is_local_and_versioned(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    pid=studio.create_production({'title':'Video original','brief':'Preparar portada',
        'pipeline':'animated-explainer','language':'es'})['project_id']
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    url='/api/studio/packaging-options/'+pid
    assert client.get(url).json()['status']=='empty'
    options=[{'id':str(i),'title':f'Una idea distinta {i}','overlay':f'Idea {i}',
              'visual_concept':'Fotografía propia con tipografía legible',
              'source_note':'Comprobar datos y derechos'} for i in (1,2)]
    payload={'options':options,'selected_id':'2','expected_revision':None}
    result=client.post(url,json=payload).json()
    assert result['status']=='draft' and result['selected_id']=='2'
    assert agent.LocalAgent(pid).dispatch('project_packaging_options',{})['revision']==result['revision']
    assert client.post(url,json=payload).status_code==400
    assert not (studio.project_path(pid)/'artifacts/thumbnail.png').exists()
    project=studio.project_path(pid)
    baseline=research_index(project)
    assert baseline['packaging_revision']==result['revision']
    receipt={'status':'passed','finished_at':'2026-11-22T10:00:00+00:00','channel_research':baseline}
    assert current(receipt,[],None,baseline)
    options[1]['title']=options[0]['title']
    assert client.post(url,json={**payload,'expected_revision':result['revision']}).status_code==400
    options[1]['title']='Otro enfoque'
    assert client.post(url,json={**payload,'selected_id':'3','expected_revision':result['revision']}).status_code==400
    updated=client.post(url,json={**payload,'selected_id':'1','expected_revision':result['revision']}).json()
    assert updated['revision']!=result['revision']
    assert not current(receipt,[],None,research_index(project))
    path=studio.project_path(pid)/'artifacts/packaging_options.json'
    studio.save_json(path,{**studio.read_json(path),'selected_id':'2'})
    with pytest.raises(ValueError,match='alteradas'):read(pid)
    assert project_problem(project) is not None
    assert research_index(project)=={'invalid':True}
    with pytest.raises(ValueError,match='alteradas'):agent.start(pid)
    studio.save_json(path,{**studio.read_json(path),'selected_id':'1'})
    studio.save_json(project/'render_verification.json',receipt)
    path.unlink()
    assert project_problem(project) is not None
    with pytest.raises(ValueError,match='ausente'):agent.start(pid)


def test_packaging_rejects_unbounded_variants(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    pid=studio.create_production({'title':'Video','brief':'Preparar opciones',
        'pipeline':'animated-explainer','language':'es'})['project_id']
    item={'id':'1','title':'Primero','overlay':'Texto','visual_concept':'Visual','source_note':''}
    with pytest.raises(ValueError):save(pid,{'options':[item], 'selected_id':None,'expected_revision':None})
