from pathlib import Path
import pytest
from lib import production_studio as studio
from lib.final_catalog import catalog


@pytest.fixture
def projects(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    for pid in ('first','second'):
        studio.save_json(tmp_path/pid/'production_request.json',{'title':pid})
    return tmp_path


def test_catalog_reports_saved_delivery_without_rehashing(projects,monkeypatch):
    final=projects/'finals/first/delivered.mp4';final.parent.mkdir(parents=True);final.write_bytes(b'fixture')
    from lib import final_catalog
    monkeypatch.setattr(final_catalog,'read_config',lambda *args:{'final_outputs_dir':str(projects/'finals')})
    studio.save_json(projects/'first/final_delivery.json',{'copied':True,'mode':'dedicated_final_directory','outputs':[{'path':str(final),'sha256':'saved'}]})
    studio.save_json(projects/'first/render_verification.json',{'status':'passed',
                     'football_selection':{'selection_id':'a'*64,'selected_metrics':['goals']}})
    report=catalog();row=report['projects'][0]
    assert row['outputs'][0]['available'] is True
    assert row['outputs'][0]['integrity_rechecked'] is False
    assert row['football_selection']['selection_id'] == 'a'*64
    final.unlink();assert catalog()['projects'][0]['outputs'][0]['available'] is False
    assert report['generation_started'] is False


def test_catalog_rejects_receipt_paths_outside_configured_final_folder(projects,monkeypatch):
    from lib import final_catalog
    outside=projects/'other.mp4';outside.write_bytes(b'fixture')
    monkeypatch.setattr(final_catalog,'read_config',lambda *args:{'final_outputs_dir':str(projects/'finals')})
    studio.save_json(projects/'first/final_delivery.json',{'copied':True,'outputs':[{'path':str(outside)}]})
    assert catalog()['projects'][0]['outputs'][0]['available'] is False


def test_catalog_does_not_present_copied_render_as_final_without_destination(projects,monkeypatch):
    from lib import final_catalog
    render=projects/'first/renders/video.mp4';render.parent.mkdir();render.write_bytes(b'fixture')
    monkeypatch.setattr(final_catalog,'read_config',lambda *args:{})
    studio.save_json(projects/'first/final_delivery.json',{'copied':True,'outputs':[{'path':str(render)}]})
    row=catalog()['projects'][0]
    assert row['copied'] is True and row['outputs'][0]['available'] is False


def test_catalog_preserves_errors_and_marks_partial_results(projects):
    (projects/'first/final_delivery.json').write_text('{broken')
    studio.save_json(projects/'second/render_verification.json',{'status':'failed','outputs':[]})
    report=catalog()
    assert len(report['errors'])==1 and len(report['projects'])==1
    assert catalog(limit=1)['truncated'] is True


def test_catalog_uses_project_renders_without_delivery(projects):
    render=projects/'first/renders/result.mp4';render.parent.mkdir();render.write_bytes(b'fixture')
    studio.save_json(projects/'first/render_verification.json',{'status':'passed','outputs':[{'path':'renders/result.mp4'}]})
    row=catalog()['projects'][0]
    assert row['copied'] is False and row['outputs'][0]['available'] is True


def test_catalog_api(projects):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    response=TestClient(create_app(),base_url='http://127.0.0.1:4750').get('/api/studio/finals')
    assert response.status_code==200
    assert response.json()['generation_started'] is False


def test_disconnected_project_root_is_not_reported_as_empty_catalog(projects,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',projects/'disconnected')
    report=catalog()
    assert report['root_available'] is False
    assert report['projects']==[]
