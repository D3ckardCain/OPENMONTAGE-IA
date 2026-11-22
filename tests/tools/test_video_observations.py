import pytest

from lib import production_studio as studio
from lib.video_observations import add,read,video_id

URL='https://www.youtube.com/watch?v=rd8TQwkQ4zs'


def payload(**updates):
    return {'video_url':URL,'views':80100,'vph':21,'engagement_percent':2.7,
            'outlier_ratio':19.7,'seo_score':40.3,'notes':'Cifra observada en Edge',**updates}


def test_manual_observation_is_attributed_and_append_only(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path)
    first=add(payload());second=add(payload(views=80200,vph=20))
    assert first['source']=='vidIQ Edge (transcripción manual)'
    assert first['video_id']=='rd8TQwkQ4zs'
    assert [r['views'] for r in read('rd8TQwkQ4zs')]==[80100,80200]
    assert second['observed_at_utc'] and read('abcdefghijk')==[]


@pytest.mark.parametrize('change',[
    {'video_url':'http://www.youtube.com/watch?v=rd8TQwkQ4zs'},
    {'video_url':'https://other.example/watch?v=rd8TQwkQ4zs'},
    {'views':-1},{'views':1.5},{'engagement_percent':101},{'seo_score':float('nan')},
    {'views':None,'vph':None,'engagement_percent':None,'outlier_ratio':None,'seo_score':None}])
def test_invalid_or_empty_observation_rejected(tmp_path,monkeypatch,change):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path)
    with pytest.raises(ValueError):add(payload(**change))
    assert read()==[]


def test_video_id_is_canonical():
    assert video_id(URL+'&t=20')=='rd8TQwkQ4zs'
