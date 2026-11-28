import threading
import pytest
from lib import production_studio as studio,production_agent as agent,reference_analysis
from lib.reference_reuse import reuse


@pytest.fixture
def projects(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    monkeypatch.setattr(agent,'ACTIVE',{})
    monkeypatch.setattr(reference_analysis,'ACTIVE',set())
    for pid in ('base','en','ko','other'):
        studio.save_json(tmp_path/pid/'production_request.json',{'reference':'https://youtu.be/abcdefghijk'})
    studio.save_json(tmp_path/'base/language_versions.json',{'versions':{'en':{'project_id':'en'},'ko':{'project_id':'ko'}}})
    studio.save_json(tmp_path/'base/reference_analysis.json',{'status':'partial','transcript':{'text':'Evidence'},'gaps':['Vision unavailable'],'external_fact_check':'not_performed'})
    return tmp_path


def test_reuse_is_snapshot_preserves_gaps_and_does_not_copy_media(projects,monkeypatch):
    monkeypatch.setattr(reference_analysis,'analyze',lambda *args:pytest.fail('Inference started'))
    result=reuse('base',['en','ko'])
    assert [item['status'] for item in result['versions']]==['shared','shared']
    snapshot=studio.read_json(projects/'en/reference_analysis.json')
    assert snapshot['status']=='partial' and snapshot['gaps']==['Vision unavailable']
    assert snapshot['external_fact_check']=='not_performed'
    assert snapshot['reuse']['media_copied'] is False
    assert reuse('base',['en'])['versions'][0]['status']=='existing'
    assert result['generation_started'] is False and result['network_requests_started']==0
    assert {path.name for path in (projects/'en').iterdir()}=={'production_request.json','reference_analysis.json'}
    studio.save_json(projects/'base/reference_analysis.json',{'status':'completed'})
    assert studio.read_json(projects/'en/reference_analysis.json')==snapshot


def test_conflicting_report_or_unrelated_project_prevents_all_writes(projects):
    studio.save_json(projects/'ko/reference_analysis.json',{'status':'completed','analysis':'Different'})
    with pytest.raises(ValueError,match='otro análisis'):reuse('base',['en','ko'])
    assert not (projects/'en/reference_analysis.json').exists()
    with pytest.raises(ValueError,match='registradas'):reuse('base',['other'])


def test_reuse_checks_reference_and_running_tasks(projects):
    studio.save_json(projects/'en/production_request.json',{'reference':'different'})
    with pytest.raises(ValueError,match='no coincide'):reuse('base',['en'])
    agent.ACTIVE['manual']=(None,threading.Event())
    with pytest.raises(ValueError,match='termine'):reuse('base',['ko'])


def test_reuse_rejects_unfinished_source_and_api_extra_parameters(projects):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    studio.save_json(projects/'base/reference_analysis.json',{'status':'queued'})
    with pytest.raises(ValueError,match='terminado'):reuse('base',['en'])
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    assert client.post('/api/studio/reference-reuse/base',json={'project_ids':['en'],'force':True}).status_code==400


def test_producer_reuses_explicit_snapshot_without_download_or_models(projects,monkeypatch):
    reuse('base',['en'])
    cancel=threading.Event();agent.ACTIVE['en']=(None,cancel)
    monkeypatch.setattr(reference_analysis,'download_reference',lambda *args:pytest.fail('download'))
    monkeypatch.setattr(reference_analysis,'analyze',lambda *args:pytest.fail('model'))
    result=reference_analysis.run_for_producer('en',{},cancel)
    assert result['status']=='partial' and result['reuse']['base_project_id']=='base'
    assert not (projects/'en/reference_analysis').exists()
    with pytest.raises(ValueError):reference_analysis.run_for_producer('en',{},threading.Event())


def test_changed_snapshot_or_reference_blocks_reuse(projects):
    from lib.reference_reuse import saved_snapshot
    reuse('base',['en','ko'])
    snapshot=studio.read_json(projects/'en/reference_analysis.json');snapshot['transcript']={'text':'changed'}
    studio.save_json(projects/'en/reference_analysis.json',snapshot)
    with pytest.raises(ValueError,match='cambió'):saved_snapshot('en')
    studio.save_json(projects/'ko/production_request.json',{'reference':'another'})
    with pytest.raises(ValueError,match='referencia actual'):saved_snapshot('ko')
