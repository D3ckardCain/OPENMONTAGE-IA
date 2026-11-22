import hashlib

from lib import final_integrity,production_studio as studio


def test_on_demand_integrity_checks_source_and_final_without_modifying_files(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    project=studio.PROJECTS_DIR/'one'
    studio.save_json(project/'production_request.json',{'title':'one'})
    source=project/'renders/video.mp4';source.parent.mkdir();source.write_bytes(b'original video')
    final=tmp_path/'finals/one/video.mp4';final.parent.mkdir(parents=True);final.write_bytes(source.read_bytes())
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(final_integrity,'read_config',lambda *args:{'final_outputs_dir':str(tmp_path/'finals')})
    studio.save_json(project/'render_verification.json',{'status':'passed',
        'finished_at':'2026-11-22T10:00:00+00:00','outputs':[{'path':str(source),'sha256':sha}]})
    studio.save_json(project/'final_delivery.json',{'copied':True,'delivered_at':'2026-11-22T10:01:00+00:00',
        'outputs':[{'source':str(source),'path':str(final),'sha256':sha}]})
    result=final_integrity.inspect('one')
    assert result['all_files_match'] is True and result['final_copy_current'] is True
    assert result['receipt_manifest_matches'] is True
    assert result['outputs'][0]['final_result']=='matches' and result['generation_started'] is False
    final.write_bytes(b'changed')
    result=final_integrity.inspect('one')
    assert result['all_files_match'] is False and result['outputs'][0]['final_result']=='hash_mismatch'


def test_duplicate_final_receipt_cannot_report_all_files_matching(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    project=studio.PROJECTS_DIR/'one'
    studio.save_json(project/'production_request.json',{'title':'one'})
    source=project/'renders/video.mp4';source.parent.mkdir();source.write_bytes(b'video')
    final=tmp_path/'finals/one/video.mp4';final.parent.mkdir(parents=True);final.write_bytes(b'video')
    sha=hashlib.sha256(b'video').hexdigest()
    monkeypatch.setattr(final_integrity,'read_config',lambda *args:{'final_outputs_dir':str(tmp_path/'finals')})
    studio.save_json(project/'render_verification.json',{'status':'passed','outputs':[{'path':str(source),'sha256':sha}]})
    record={'source':str(source),'path':str(final),'sha256':sha}
    studio.save_json(project/'final_delivery.json',{'copied':True,'outputs':[record,record]})
    result=final_integrity.inspect('one')
    assert result['outputs'][0]['source_result']=='matches'
    assert result['receipt_manifest_matches'] is False and result['all_files_match'] is False


def test_integrity_rejects_path_outside_project_and_missing_video(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    project=studio.PROJECTS_DIR/'one'
    studio.save_json(project/'production_request.json',{'title':'one'})
    outside=tmp_path/'outside.mp4';outside.write_bytes(b'other')
    sha=hashlib.sha256(outside.read_bytes()).hexdigest()
    studio.save_json(project/'render_verification.json',{'status':'passed','outputs':[
        {'path':str(outside),'sha256':sha},
        {'path':str(project/'renders/missing.mp4'),'sha256':sha}]})
    monkeypatch.setattr(final_integrity,'read_config',lambda *args:{})
    result=final_integrity.inspect('one')
    assert [row['source_result'] for row in result['outputs']]==['invalid_path','missing']
    assert result['all_files_match'] is False


def test_integrity_api_is_explicit_read_only(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    studio.save_json(studio.PROJECTS_DIR/'one/production_request.json',{'title':'one'})
    monkeypatch.setattr(final_integrity,'read_config',lambda *args:{})
    result=TestClient(create_app(),base_url='http://127.0.0.1:4750').get('/api/studio/finals/one/integrity')
    assert result.status_code==200 and result.json()['generation_started'] is False
    assert result.json()['integrity_rechecked'] is True
