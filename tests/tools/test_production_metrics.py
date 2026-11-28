from lib import production_metrics, production_queue


def test_saved_queue_timings_report_only_measured_runs(monkeypatch):
    monkeypatch.setattr(production_queue, 'read', lambda: {'status': 'paused', 'items': [
        {'project_id': 'one', 'title': 'Primero', 'status': 'completed',
         'started_at': '2026-11-22T10:00:00+00:00',
         'finished_at': '2026-11-22T10:02:30+00:00', 'message': 'Terminado'},
        {'project_id': 'two', 'title': 'Segundo', 'status': 'blocked',
         'started_at': '2026-11-22T10:03:00+00:00', 'message': 'Falta un recurso'},
    ]})
    result=production_metrics.snapshot()
    assert result['completed_runs_measured']==1
    assert result['elapsed_seconds_total']==150
    assert result['projects'][0]['elapsed_seconds']==150
    assert result['projects'][1]['elapsed_seconds'] is None
    assert result['ram_peak_mb'] is None and result['estimate_48_per_week'] is None
    assert result['generation_started'] is False
    assert result['pilot_candidate']['queue_projects_considered']==2
    assert result['pilot_candidate']['completed']==1
    assert result['pilot_candidate']['completed_with_duration']==1
    assert result['pilot_candidate']['measurements_complete'] is False


def test_pilot_candidate_only_marks_ten_measured_completed_queue_records(monkeypatch):
    items=[{'project_id':f'fixture-{index}','status':'completed',
            'started_at':'2026-11-22T10:00:00+00:00','finished_at':'2026-11-22T10:01:00+00:00'}
           for index in range(11)]
    monkeypatch.setattr(production_queue,'read',lambda:{'status':'completed','items':items})
    result=production_metrics.snapshot()['pilot_candidate']
    assert result['queue_projects_considered']==10 and result['queue_projects_total']==11
    assert result['completed']==10 and result['completed_with_duration']==10
    assert result['completed_with_ram']==0 and result['completed_with_vram']==0
    assert result['measurements_complete'] is False


def test_pilot_candidate_measurement_coverage_requires_all_ten(tmp_path,monkeypatch):
    from lib import production_studio as studio
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    items=[]
    for index in range(10):
        pid=f'fixture-{index}'
        studio.save_json(tmp_path/pid/'production_request.json',{})
        studio.save_json(tmp_path/pid/'resource_usage.json',{
            'host_ram_peak_mb':1000,'gpu_vram_peak_mb':500})
        items.append({'project_id':pid,'status':'completed',
            'started_at':'2026-11-22T10:00:00+00:00','finished_at':'2026-11-22T10:01:00+00:00'})
    monkeypatch.setattr(production_queue,'read',lambda:{'status':'completed','items':items})
    result=production_metrics.snapshot()['pilot_candidate']
    assert result['measurements_complete'] is True
    assert result['completed_with_ram']==10 and result['completed_with_vram']==10


def test_frozen_pilot_keeps_membership_when_queue_changes(tmp_path,monkeypatch):
    from lib import production_studio as studio
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    ids=[f'pilot-{index}' for index in range(10)]
    studio.save_json(studio.CONFIG_DIR/'production_pilots.json',[
        {'id':'fixed','created_at':'2026-11-22T10:00:00+00:00',
         'projects_root':str(studio.PROJECTS_DIR.resolve()),'project_ids':ids}])
    items=[{'project_id':'other','status':'completed'}]+[
        {'project_id':pid,'status':'pending'} for pid in reversed(ids[1:])]
    monkeypatch.setattr(production_queue,'read',lambda:{'status':'paused','items':items})
    report=production_metrics.snapshot()['pilot_candidate']
    assert report['frozen'] is True and report['missing_from_queue']==1
    assert report['queue_projects_considered']==9 and report['completed']==0
    assert report['measurements_complete'] is False


def test_frozen_pilot_ignores_same_project_id_from_another_disk(tmp_path,monkeypatch):
    from lib import production_studio as studio
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    ids=[f'pilot-{index}' for index in range(10)]
    studio.save_json(studio.CONFIG_DIR/'production_pilots.json',[
        {'projects_root':str(studio.PROJECTS_DIR.resolve()),'project_ids':ids}])
    monkeypatch.setattr(production_queue,'read',lambda:{'status':'paused','items':[
        {'project_id':ids[0],'projects_root':str(tmp_path/'other'),'status':'completed'}]})
    pilot=production_metrics.snapshot()['pilot_candidate']
    assert pilot['frozen'] is True and pilot['missing_from_queue']==10
    assert pilot['completed']==0


def test_pilot_aggregates_exclude_other_queue_projects(tmp_path,monkeypatch):
    from lib import production_studio as studio
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    ids=[f'pilot-{index}' for index in range(10)]
    studio.save_json(studio.CONFIG_DIR/'production_pilots.json',[
        {'projects_root':str(studio.PROJECTS_DIR.resolve()),'project_ids':ids}])
    items=[]
    for pid in ids+['outside']:
        studio.save_json(studio.PROJECTS_DIR/pid/'production_request.json',{})
        if pid!='pilot-9':
            studio.save_json(studio.PROJECTS_DIR/pid/'render_verification.json',{
                'status':'passed','finished_at':'2026-11-22T10:01:00+00:00',
                'outputs':[{'path':str(studio.PROJECTS_DIR/pid/'renders/final.mp4'),'sha256':'a'*64}]})
        if pid not in ('pilot-8','pilot-9'):
            studio.save_json(studio.PROJECTS_DIR/pid/'final_delivery.json',{
                'copied':True,'delivered_at':'2026-11-22T10:02:00+00:00',
                'outputs':[{'source':str(studio.PROJECTS_DIR/pid/'renders/final.mp4'),'sha256':'a'*64}]})
        studio.save_json(studio.PROJECTS_DIR/pid/'resource_usage.json',{
            'host_ram_peak_mb':9000 if pid=='outside' else 1000,
            'gpu_vram_peak_mb':8000 if pid=='outside' else 500,
            'recorded_at':'2026-11-22T10:01:00+00:00'})
        studio.save_json(studio.PROJECTS_DIR/pid/'editorial_reviews.json',[
            {'stage':'idea','decision':'revision_requested' if pid=='outside' else 'approved'}])
        items.append({'project_id':pid,'status':'completed',
                      'started_at':'2026-11-22T10:00:00+00:00',
                      'finished_at':'2026-11-22T10:01:00+00:00',
                      'retry_history':[{'status':'blocked'}] if pid=='outside' else []})
    monkeypatch.setattr(production_queue,'read',lambda:{'status':'completed','items':items})
    report=production_metrics.snapshot()
    assert report['ram_peak_mb']==9000
    pilot=report['pilot_candidate']
    assert pilot['completed_elapsed_seconds_total']==600
    assert pilot['ram_peak_mb']==1000 and pilot['vram_peak_mb']==500
    assert pilot['retries_recorded']==0
    assert pilot['editorial_first_decisions_count']==10 and pilot['first_pass_approval_rate']==1
    assert pilot['completed_with_render_verification']==9
    assert pilot['completed_with_final_copy']==8


def test_invalid_or_reversed_timestamps_never_make_up_a_duration():
    assert production_metrics._seconds('bad', '2026-11-22T10:00:00+00:00') is None
    assert production_metrics._seconds('2026-11-22T10:01:00+00:00',
                                       '2026-11-22T10:00:00+00:00') is None


def test_retry_causes_are_reported_without_counting_old_duration_twice(monkeypatch):
    monkeypatch.setattr(production_queue,'read',lambda:{'status':'paused','items':[
        {'project_id':'missing','status':'pending','retry_history':[
            {'status':'blocked','message':'Falta un modelo','started_at':'2026-11-22T10:00:00+00:00',
             'finished_at':'2026-11-22T10:02:00+00:00','retried_at':'2026-11-22T10:03:00+00:00'}]}]})
    report=production_metrics.snapshot()
    assert report['retries_recorded']==1 and report['elapsed_seconds_total']==0
    assert report['projects'][0]['retry_history'][0]['message']=='Falta un modelo'
    assert report['retry_causes_by_status']=={'blocked':1}
    assert report['first_pass_approval_rate'] is None


def test_approved_stages_require_saved_checkpoint_evidence(tmp_path,monkeypatch):
    from lib import production_studio as studio
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    monkeypatch.setattr(studio,'load_pipeline_readonly',lambda name:{'stages':[{'name':'script'},{'name':'assets'}]})
    studio.save_json(tmp_path/'one/production_request.json',{'pipeline':'example'})
    studio.save_json(tmp_path/'one/checkpoint_script.json',{'status':'completed','human_approved':True})
    studio.save_json(tmp_path/'one/checkpoint_assets.json',{'status':'awaiting_human','human_approved':False})
    monkeypatch.setattr(production_queue,'read',lambda:{'status':'paused','items':[{'project_id':'one','status':'awaiting_human'}]})
    report=production_metrics.snapshot()
    assert report['approved_stage_count']==1
    assert report['projects'][0]['approved_stages']==['script']
    assert report['first_pass_approval_rate'] is None


def test_editorial_first_decision_rate_uses_explicit_reviews_only(tmp_path,monkeypatch):
    from lib import production_studio as studio
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    studio.save_json(tmp_path/'one/production_request.json',{})
    studio.save_json(tmp_path/'one/editorial_reviews.json',[
        {'stage':'idea','decision':'revision_requested','reason':'Corregir'},
        {'stage':'idea','decision':'approved'},
        {'stage':'script','decision':'approved'}])
    monkeypatch.setattr(production_queue,'read',lambda:{'status':'paused','items':[{'project_id':'one','status':'pending'}]})
    report=production_metrics.snapshot()
    assert report['editorial_first_decisions_count']==2
    assert report['first_pass_approval_rate']==0.5


def test_retry_resource_peaks_are_preserved_without_treating_old_sample_as_current(tmp_path,monkeypatch):
    from lib import production_studio as studio
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    studio.save_json(tmp_path/'one/production_request.json',{})
    studio.save_json(tmp_path/'one/resource_usage.json',{
        'host_ram_peak_mb':2500,'gpu_vram_peak_mb':800,'recorded_at':'2026-11-22T10:02:00+00:00'})
    monkeypatch.setattr(production_queue,'read',lambda:{'status':'paused','items':[
        {'project_id':'one','status':'pending','retry_history':[
            {'status':'blocked','resource_usage':{'host_ram_peak_mb':2500,'gpu_vram_peak_mb':800}}]}]})
    report=production_metrics.snapshot()
    assert report['projects'][0]['resource_usage'] is None
    assert report['ram_peak_mb']==2500 and report['vram_peak_mb']==800


def test_stage_timings_current_attempt_excludes_prior_events(tmp_path,monkeypatch):
    from lib import production_studio as studio
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    studio.save_json(tmp_path/'one/production_request.json',{})
    studio.save_json(tmp_path/'one/job.json',{'events':[
        {'kind':'stage_timing','stage':'script','elapsed_seconds':12,'at':'2026-11-22T10:01:00+00:00'},
        {'kind':'stage_timing','stage':'script','elapsed_seconds':4,'at':'2026-11-22T10:11:00+00:00'}]})
    monkeypatch.setattr(production_queue,'read',lambda:{'status':'paused','items':[
        {'project_id':'one','status':'blocked','started_at':'2026-11-22T10:10:00+00:00',
         'finished_at':'2026-11-22T10:12:00+00:00',
         'retry_history':[{'stage_active_seconds':{'script':12}}]}]})
    row=production_metrics.snapshot()['projects'][0]
    assert row['stage_active_seconds']=={'script':4}
    assert row['retry_history'][0]['stage_active_seconds']=={'script':12}


def test_stage_timings_are_summed_only_from_saved_valid_events(tmp_path, monkeypatch):
    from lib import production_studio as studio
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    studio.save_json(tmp_path/'one/production_request.json',{})
    studio.save_json(tmp_path/'one/job.json',{'events':[
        {'kind':'stage_timing','stage':'research','elapsed_seconds':3.5},
        {'kind':'stage_timing','stage':'research','elapsed_seconds':2},
        {'kind':'stage_timing','stage':'script','elapsed_seconds':7},
        {'kind':'stage_timing','stage':'script','elapsed_seconds':-1},
        {'kind':'stage','stage':'edit','elapsed_seconds':999},
    ]})
    studio.save_json(tmp_path/'one/resource_usage.json',{
        'host_ram_peak_mb':6400,'gpu_vram_peak_mb':2800,'samples':3})
    monkeypatch.setattr(production_queue,'read',lambda:{'status':'paused','items':[
        {'project_id':'one','status':'completed'}]})
    result=production_metrics.snapshot()['projects'][0]
    assert result['stage_active_seconds']=={'research':5.5,'script':7}
    assert result['resource_usage']['host_ram_peak_mb']==6400
    assert production_metrics.snapshot()['ram_peak_mb']==6400
    assert production_metrics.snapshot()['vram_peak_mb']==2800


def test_studio_metrics_endpoint_does_not_start_work(monkeypatch):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    monkeypatch.setattr(production_queue, 'read', lambda: {'status':'paused','items':[]})
    response=TestClient(create_app(),base_url='http://127.0.0.1:4750').get('/api/studio/production-metrics')
    assert response.status_code==200
    assert response.json()['projects']==[] and response.json()['generation_started'] is False
