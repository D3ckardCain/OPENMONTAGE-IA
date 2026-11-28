from fastapi.testclient import TestClient

from backlot.server import create_app
from lib import final_source_trace as trace, production_studio as studio


def test_trace_exact_scene_chain_and_unknown_render(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    project=studio.PROJECTS_DIR/'one'
    studio.save_json(project/'production_request.json',{'title':'one'})
    choice={'scene_id':'s1','path':'assets/video/take.mp4','sha256':'a'*64,'seconds':4}
    video={'path':'renders/scene-preview-1.mp4','sha256':'b'*64}
    mixed={'path':'renders/scene-audio-preview-2.mp4','sha256':'c'*64}
    studio.save_json(project/'artifacts/scene_edit_preview.json',{'status':'completed','attempt':'1','choices':[choice],'output':video})
    studio.save_json(project/'artifacts/scene_audio_preview.json',{'status':'completed','attempt':'2',
        'video_attempt':'1','video':video,'narration':{'path':'assets/voice.wav','sha256':'d'*64},
        'music':None,'output':mixed})
    studio.save_json(project/'render_verification.json',{'status':'passed','outputs':[
        {'path':str(project/mixed['path']),'sha256':mixed['sha256']},
        {'path':str(project/'renders/other.mp4'),'sha256':'e'*64}]})
    monkeypatch.setattr(trace,'asset_sources',lambda *args:{'entries':[
        {'path':choice['path'],'sha256':choice['sha256'],'commercial_use':'yes'}]})
    result=trace.inspect('one')
    first,second=result['outputs']
    assert first['trace_complete'] is True
    assert first['chain']==['scene_preview','scene_audio_preview']
    assert [row['role'] for row in first['inputs']]==['scene_take','narration']
    assert first['inputs'][0]['registered'] is True
    assert first['inputs'][1]['registered'] is False
    assert second['trace_complete'] is False and second['inputs']==[]
    assert result['generation_started'] is False


def test_trace_rejects_broken_parent_and_wrong_hash(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    project=studio.PROJECTS_DIR/'one'
    studio.save_json(project/'production_request.json',{'title':'one'})
    video={'path':'renders/scene-preview.mp4','sha256':'a'*64}
    mixed={'path':'renders/scene-audio.mp4','sha256':'b'*64}
    studio.save_json(project/'artifacts/scene_edit_preview.json',{'status':'completed','attempt':'1',
        'choices':[],'output':video})
    studio.save_json(project/'artifacts/scene_audio_preview.json',{'status':'completed','attempt':'2',
        'video_attempt':'wrong','video':video,'output':mixed})
    studio.save_json(project/'render_verification.json',{'status':'passed','outputs':[
        {'path':mixed['path'],'sha256':mixed['sha256']},
        {'path':video['path'],'sha256':'c'*64}]})
    monkeypatch.setattr(trace,'asset_sources',lambda *args:{'entries':[]})
    rows=trace.inspect('one')['outputs']
    assert rows[0]['trace_complete'] is False and rows[0]['problem'] and rows[0]['inputs']==[]
    assert rows[1]['receipt_stage'] is None


def test_empty_scenes_or_missing_narration_never_claim_complete_trace(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    project=studio.PROJECTS_DIR/'one'
    studio.save_json(project/'production_request.json',{'title':'one'})
    preview={'path':'renders/preview.mp4','sha256':'b'*64}
    mixed={'path':'renders/mixed.mp4','sha256':'c'*64}
    studio.save_json(project/'artifacts/scene_edit_preview.json',{'status':'completed','attempt':'1',
        'choices':[],'output':preview})
    studio.save_json(project/'render_verification.json',{'status':'passed','outputs':[preview]})
    monkeypatch.setattr(trace,'asset_sources',lambda *args:{'entries':[]})
    row=trace.inspect('one')['outputs'][0]
    assert row['receipt_stage']=='scene_preview' and row['trace_complete'] is False and row['inputs']==[]
    studio.save_json(project/'artifacts/scene_edit_preview.json',{'status':'completed','attempt':'1',
        'choices':[{'scene_id':'s1','path':'assets/take.mp4','sha256':'a'*64}],'output':preview})
    studio.save_json(project/'artifacts/scene_audio_preview.json',{'status':'completed','attempt':'2',
        'video_attempt':'1','video':preview,'narration':None,'music':None,'output':mixed})
    studio.save_json(project/'render_verification.json',{'status':'passed','outputs':[mixed]})
    row=trace.inspect('one')['outputs'][0]
    assert row['receipt_stage']=='scene_audio_preview' and row['trace_complete'] is False
    assert row['inputs']==[] and 'audio' in row['problem']


def test_trace_api_is_read_only(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    studio.save_json(studio.PROJECTS_DIR/'one/production_request.json',{'title':'one'})
    result=TestClient(create_app(),base_url='http://127.0.0.1:4750').get('/api/studio/finals/one/sources')
    assert result.status_code==200 and result.json()['outputs']==[]
