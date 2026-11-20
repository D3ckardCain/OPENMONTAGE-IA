import pytest
from lib import production_studio as studio
from lib.language_versions import create_versions


@pytest.fixture
def source(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    studio.save_json(tmp_path/'base/production_request.json',{'title':'Tema original','brief':'Investigar el tema','pipeline':'animated-explainer','language':'es','reference':'https://example.org','automatic':True})
    captured=[]
    def create(data):
        pid='version-'+str(len(captured));captured.append(data)
        studio.save_json(tmp_path/pid/'production_request.json',data)
        return {'project_id':pid}
    monkeypatch.setattr(studio,'create_production',create)
    return captured


def test_versions_are_independent_guided_requests_and_repeat_is_reused(source):
    report=create_versions('base',['en','ko'])
    assert [item['status'] for item in report['versions']]==['created','created']
    assert all(item['automatic'] is False for item in source)
    assert source[1]['language']=='ko' and 'canciones' in source[1]['brief']
    assert source[0]['reference']=='https://example.org'
    assert report['generation_started'] is False and report['media_copied'] is False
    assert create_versions('base',['en'])['versions'][0]['status']=='existing'
    assert len(source)==2


@pytest.mark.parametrize('languages',[[],['es'],['en','EN'],['../../bad'],['en']*11,'en'])
def test_invalid_versions_create_nothing(source,languages):
    with pytest.raises(ValueError):create_versions('base',languages)
    assert source==[]


def test_missing_existing_version_is_reported_without_duplicate(source):
    result=create_versions('base',['en'])
    project=studio.project_path(result['versions'][0]['project_id'])
    (project/'production_request.json').unlink()
    assert create_versions('base',['en'])['versions'][0]['status']=='unavailable'
    assert len(source)==1


def test_api_only_accepts_languages(source):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    assert client.post('/api/studio/language-versions/base',json={'languages':['en'],'automatic':True}).status_code==400
    assert client.post('/api/studio/language-versions/base',json={'languages':['en']}).json()['generation_started'] is False


def test_partial_failure_keeps_prepared_version_registered(source,monkeypatch):
    original=studio.create_production
    def create(data):
        if data['language']=='ko':raise ValueError('Fixture failure')
        return original(data)
    monkeypatch.setattr(studio,'create_production',create)
    result=create_versions('base',['en','ko','de'])
    assert [entry['status'] for entry in result['versions']]==['created','failed']
    assert create_versions('base',['en'])['versions'][0]['status']=='existing'
    assert len(source)==1


def test_list_versions_survives_reopening_and_marks_unavailable(source):
    from lib.language_versions import list_versions
    result=create_versions('base',['en','ko'])
    assert len(list_versions('base')['versions'])==2
    (studio.project_path(result['versions'][0]['project_id'])/'production_request.json').unlink()
    report=list_versions('base')
    assert [entry['status'] for entry in report['versions']]==['unavailable','existing']
    assert report['generation_started'] is False
    assert len(source)==2


def test_requirements_do_not_probe_runtimes_or_certify_languages(source,monkeypatch):
    from lib import model_adapters
    from lib.language_versions import local_requirements
    monkeypatch.setattr(model_adapters,'CATALOG',{'voice':{},'translator':{},'video':{}})
    monkeypatch.setattr(model_adapters,'spec',lambda family:{'capability':{'voice':'tts','translator':'translation','video':'video_generation'}[family]})
    calls=[]
    def diagnostics(family,probe):
        assert probe is False
        calls.append(family)
        return {'ready':True,'model_dir':'/fixture','problems':[],'required_modules':['fixture']}
    monkeypatch.setattr(model_adapters,'diagnostics',diagnostics)
    report=local_requirements('base')
    assert calls==['voice','translator']
    assert report['generation_started'] is False and report['network_requests_started']==0
    assert all(not item['language_support_verified'] and not item['runtime_checked'] for item in report['candidates'])
