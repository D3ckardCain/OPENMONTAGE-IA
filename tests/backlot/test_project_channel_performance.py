import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_studio as studio
from lib import production_agent as agent
from lib.channel_performance import FIELDS, import_csv
from lib.editorial_freshness import research_index, current
from lib.project_channel_evidence import project_problem


def test_project_keeps_private_performance_copy_and_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(studio, 'PROJECTS_DIR', tmp_path/'projects')
    monkeypatch.setattr(studio, 'CONFIG_DIR', tmp_path/'config')
    csv = ','.join(FIELDS)+'\n'+'\n'.join(
        f'https://www.youtube.com/watch?v=abcdefghijk,2026-11-{day:02d},2026-11-{day:02d},100,4,20,10,20'
        for day in (1, 2, 3))+'\n'
    imported = import_csv(csv)
    data = {'title':'Rendimiento real','brief':'Crear un video nuevo con evidencia separada',
            'pipeline':'animated-explainer','language':'es','automatic':False,
            'performance_import_id':imported['id']}
    pid = studio.create_production(data)['project_id']
    path = studio.project_path(pid)
    request = studio.read_json(path/'production_request.json')
    assert request['performance_import_sha256'] == imported['sha256']
    assert research_index(path)['performance_import_sha256'] == imported['sha256']
    worker = agent.LocalAgent(pid)
    first = worker.dispatch('project_channel_performance', {'limit':2})
    assert first['status']=='verified' and first['next_offset']==2
    assert worker.dispatch('project_channel_performance', {'offset':2,'limit':2})['next_offset'] is None
    client = TestClient(create_app(), base_url='http://127.0.0.1:4750')
    assert client.get('/api/studio/channel-performance/'+pid+'?limit=1').json()['next_offset']==1
    assert client.get('/api/studio/projects/'+pid).json()['channel_performance']['status']=='verified'
    assert project_problem(path) is None
    baseline = research_index(path)
    receipt = {'status':'passed','finished_at':'2026-11-22T10:00:00+00:00','channel_research':baseline}
    assert current(receipt, [], None, baseline)
    original = studio.read_json(path/'artifacts/channel_performance_snapshot.json')
    studio.save_json(path/'artifacts/channel_performance_snapshot.json',{**original,'rows':[]})
    with pytest.raises(ValueError,match='alterado'):
        worker.dispatch('project_channel_performance',{})
    assert project_problem(path) is not None
    assert research_index(path)=={'invalid':True}
    assert not current(receipt, [], None, research_index(path))
    assert client.get('/api/studio/projects/'+pid).json()['channel_performance']['status']=='invalid'
    assert client.get('/api/studio/channel-performance/'+pid).status_code==400
    with pytest.raises(ValueError,match='alterado'):
        agent.start(pid)
    studio.save_json(path/'artifacts/channel_performance_snapshot.json',original)
    assert research_index(path)==baseline
    # The project remains tied to its own copy even if the import directory disappears.
    (studio.CONFIG_DIR/'research/channel_performance'/(imported['id']+'.json')).unlink()
    assert worker.dispatch('project_channel_performance',{})['row_total']==3


def test_invalid_import_id_rejected_before_project_creation(tmp_path, monkeypatch):
    monkeypatch.setattr(studio, 'PROJECTS_DIR', tmp_path/'projects')
    monkeypatch.setattr(studio, 'CONFIG_DIR', tmp_path/'config')
    with pytest.raises((ValueError, FileNotFoundError)):
        studio.create_production({'title':'Inválido','brief':'Prueba','pipeline':'animated-explainer',
                                  'language':'es','performance_import_id':'../inexistente'})
    assert not (tmp_path/'projects').exists()
