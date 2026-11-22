import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_studio as studio
from lib import production_agent as agent
from lib.packaging_options import read,save


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
    options[1]['title']=options[0]['title']
    assert client.post(url,json={**payload,'expected_revision':result['revision']}).status_code==400
    options[1]['title']='Otro enfoque'
    assert client.post(url,json={**payload,'selected_id':'3','expected_revision':result['revision']}).status_code==400
    path=studio.project_path(pid)/'artifacts/packaging_options.json'
    studio.save_json(path,{**studio.read_json(path),'selected_id':'1'})
    with pytest.raises(ValueError,match='alteradas'):read(pid)


def test_packaging_rejects_unbounded_variants(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    pid=studio.create_production({'title':'Video','brief':'Preparar opciones',
        'pipeline':'animated-explainer','language':'es'})['project_id']
    item={'id':'1','title':'Primero','overlay':'Texto','visual_concept':'Visual','source_note':''}
    with pytest.raises(ValueError):save(pid,{'options':[item], 'selected_id':None,'expected_revision':None})
