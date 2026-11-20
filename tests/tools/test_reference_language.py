import pytest
from lib import production_studio as studio
from lib import reference_language as language

@pytest.fixture
def project(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    studio.save_json(tmp_path/'fixture/production_request.json',{'reference':'https://youtu.be/abcdefghijk'})
    studio.save_json(tmp_path/'fixture/reference_analysis.json',{'status':'partial','transcript':{'language':'en'}})
    return tmp_path/'fixture'


def test_detection_is_only_suggestion_until_explicit_confirmation(project):
    report=language.read('fixture')
    assert report['detected_language']=='en' and report['confirmed_language'] is None
    assert language.confirm('fixture','en-US')['confirmed_language']=='en-US'


def test_changed_reference_or_analysis_invalidates_confirmation(project):
    language.confirm('fixture','en')
    studio.save_json(project/'reference_analysis.json',{'status':'completed','transcript':{'language':'ko'}})
    report=language.read('fixture')
    assert report['confirmation_outdated'] is True and report['confirmed_language'] is None
    assert report['detected_language']=='ko'


def test_invalid_language_is_not_saved(project):
    with pytest.raises(ValueError):language.confirm('fixture','../../invalid')
    assert not (project/'reference_language.json').exists()
