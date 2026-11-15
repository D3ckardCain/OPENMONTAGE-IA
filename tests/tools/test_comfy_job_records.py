from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_studio as studio
from lib.comfy_job_records import project_jobs
from lib.production_agent import LocalAgent


def test_records_are_local_scoped_and_available_to_agent(tmp_path,monkeypatch):
    import requests
    def forbidden(*args,**kwargs):raise AssertionError('No network permitted')
    monkeypatch.setattr(requests.sessions.Session,'request',forbidden)
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    for pid in ('one','two'):studio.save_json(tmp_path/pid/'production_request.json',{})
    studio.save_json(tmp_path/'one/assets/scene/comfy-wan-job.json',{
        'prompt_id':'known-job','family':'wan','status':'recovery_required','last_error':'timeout'})
    studio.save_json(tmp_path/'two/assets/comfy-wan-job.json',{'prompt_id':'other-job'})
    with TestClient(create_app(),base_url='http://127.0.0.1:4750') as client:
        result=client.get('/api/studio/comfy-jobs/one').json()
        assert len(result['jobs'])==1
        job=result['jobs'][0]
        assert job['resume_prompt_id']=='known-job'
        assert job['server_state_verified'] is False
        assert job['last_error']=='timeout'
    agent=LocalAgent.__new__(LocalAgent);agent.pid='one'
    assert agent.dispatch('project_comfy_jobs',{})==result


def test_bad_and_symlinked_records_do_not_break_or_escape_project(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    studio.save_json(tmp_path/'one/production_request.json',{})
    (tmp_path/'one/comfy-bad-job.json').write_text('{invalid')
    studio.save_json(tmp_path/'outside/comfy-private-job.json',{'prompt_id':'secret'})
    (tmp_path/'one/link').symlink_to(tmp_path/'outside',target_is_directory=True)
    (tmp_path/'one/comfy-link-job.json').symlink_to(tmp_path/'outside/comfy-private-job.json')
    result=project_jobs('one')
    assert not result['jobs'] and len(result['warnings'])==1
