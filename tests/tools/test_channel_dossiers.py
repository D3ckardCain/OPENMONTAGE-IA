import json
import pytest

from lib import production_studio as studio
from lib.channel_dossiers import save,read,list_saved

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
