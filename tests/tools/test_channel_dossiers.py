import json
import pytest

from lib import production_studio as studio
from lib.channel_dossiers import save,read,list_saved,compare

CHANNEL='UC'+'a'*22


def report(views):
    return {'source':'YouTube Data API','channel_id':CHANNEL,
            'retrieved_at_utc':'2026-11-22T00:00:00+00:00',
            'since_utc':'2026-10-23T00:00:00+00:00','cutoff_at_utc':'2026-11-22T00:00:00+00:00',
            'complete_period':False,'publications':[{'id':'abcdefghijk','viewCount':views}]}


def test_snapshots_are_immutable_and_attributed(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path)
    first=save(report(100));second=save(report(150))
    assert first['id']!=second['id']
    assert read(CHANNEL,first['id'])['report']['publications'][0]['viewCount']==100
    assert read(CHANNEL,second['id'])['report']['publications'][0]['viewCount']==150
    assert len(list_saved(CHANNEL))==2


def test_changed_snapshot_is_rejected(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path)
    first=save(report(100))
    path=tmp_path/'research/channel_audits'/CHANNEL/(first['id']+'.json')
    record=json.loads(path.read_text());record['report']['publications'][0]['viewCount']=999
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError,match='alterado'):read(CHANNEL,first['id'])
    with pytest.raises(ValueError,match='canal'):list_saved('../other')


def test_comparison_uses_only_same_video_with_non_decreasing_known_views(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path)
    old=report(100);old['publications'] += [{'id':'bbbbbbbbbbb','viewCount':40},
                                             {'id':'ccccccccccc','viewCount':70},
                                             {'id':'ddddddddddd','viewCount':3}]
    first=save(old)
    new=report(150);new['retrieved_at_utc']='2026-11-23T00:00:00+00:00'
    new['publications'] += [{'id':'bbbbbbbbbbb','viewCount':None},
                            {'id':'ccccccccccc','viewCount':60},
                            {'id':'eeeeeeeeeee','viewCount':200}]
    second=save(new)
    result=compare(CHANNEL,first['id'],second['id'])
    assert result['elapsed_hours']==24
    assert result['comparable_count']==1 and result['comparable_views_delta']==50
    assert result['changes'][0]['average_views_per_hour']==2.08
    assert result['new_video_ids']==['eeeeeeeeeee']
    assert result['absent_video_ids']==['ddddddddddd']
    assert result['unknown_view_ids']==['bbbbbbbbbbb']
    assert result['decreased_views'][0]['id']=='ccccccccccc'
    with pytest.raises(ValueError,match='posterior'):compare(CHANNEL,second['id'],first['id'])
