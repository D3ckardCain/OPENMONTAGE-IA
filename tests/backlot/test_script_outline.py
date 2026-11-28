from fastapi.testclient import TestClient
from lib import production_studio as studio
from lib import production_agent as agent
from lib.script_outline import read
from backlot.server import create_app


def test_editorial_outline_is_versioned_and_separate_from_pipeline_script(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    pid=studio.create_production({'title':'Historia original','brief':'Video en español',
        'pipeline':'animated-explainer','language':'es'})['project_id']
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    url='/api/studio/script-outline/'+pid
    template=client.get(url).json()
    assert template['status']=='empty' and len(template['blocks'])==5
    assert agent.LocalAgent(pid).dispatch('project_script_outline',{})['status']=='empty'
    template['blocks'][0].update(narration='Una historia original por investigar',
        voice_direction='Pausa antes del dato',visual_direction='Mostrar cronología',source_ref='Revisar fuente primaria')
    payload={key:template[key] for key in ('title','target_seconds','blocks')}
    payload['expected_revision']=None
    saved=client.post(url,json=payload).json()
    assert saved['status']=='draft' and saved['analysis']['without_source']==[]
    assert saved['analysis']['word_count']==5
    assert agent.LocalAgent(pid).dispatch('project_script_outline',{})['revision']==saved['revision']
    assert not (studio.project_path(pid)/'artifacts/script.json').exists()
    assert client.post(url,json=payload).status_code==400
    path=studio.project_path(pid)/'artifacts/editorial_script_outline.json'
    studio.save_json(path,{**studio.read_json(path),'title':'Alterado'})
    assert client.get(url).status_code==400
    assert not (studio.project_path(pid)/'artifacts/script.json').exists()


def test_outline_rejects_oversized_or_unknown_fields(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    pid=studio.create_production({'title':'Borrador','brief':'Video','pipeline':'animated-explainer',
        'language':'es'})['project_id']
    from lib.script_outline import save
    blank=read(pid)
    blank['blocks'][0]['narration']='Texto'
    payload={key:blank[key] for key in ('title','target_seconds','blocks')}
    payload['expected_revision']=None
    payload['blocks'][0]['narration']='x'*4001
    import pytest
    with pytest.raises(ValueError):save(pid,payload)
    payload['blocks'][0]['narration']='Texto'
    payload['unexpected']='x'
    with pytest.raises(ValueError):save(pid,payload)
