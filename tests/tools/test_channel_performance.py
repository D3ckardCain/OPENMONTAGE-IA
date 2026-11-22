import pytest
from lib import production_studio as studio
from lib.channel_performance import FIELDS,import_csv,read,list_saved


@pytest.fixture
def isolated(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path)


def csv_file(*rows):
    return ','.join(FIELDS)+'\n'+'\n'.join(rows)+'\n'


def test_import_preserves_period_and_only_derives_supported_ratios(isolated):
    payload=csv_file('https://www.youtube.com/watch?v=abcdefghijk,2026-10-01,2026-10-31,1000,40,200,60,120',
                     'https://www.youtube.com/watch?v=bbbbbbbbbbb,2026-10-01,2026-10-31,,,50,,')
    saved=import_csv(payload);record=read(saved['id'])
    assert record['rows'][0]['clicks_per_impression_percent']==4
    assert record['rows'][0]['average_watch_percent']==50
    assert record['rows'][1]['clicks_per_impression_percent'] is None
    assert record['rows'][1]['average_watch_percent'] is None
    assert list_saved()['imports'][0]['rows']==[]
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    page=client.get('/api/research/channel-performance/'+saved['id']+'?limit=1').json()
    assert page['next_offset']==1 and len(page['rows'])==1
    assert client.get('/api/research/channel-performance/'+saved['id']+'?offset=1&limit=1').json()['next_offset'] is None
    assert client.get('/api/research/channel-performance/'+saved['id']+'?limit=51').status_code==422
    assert client.post('/api/research/channel-performance',json={'csv_text':payload}).status_code==200


@pytest.mark.parametrize('line',[
    'https://www.youtube.com/watch?v=abcdefghijk,2026-10-31,2026-10-01,100,5,10,20,40',
    'https://www.youtube.com/watch?v=abcdefghijk,2026-10-01,2026-10-31,10,11,10,20,40',
    'https://www.youtube.com/watch?v=abcdefghijk,2026-10-01,2026-10-31,,5,10,20,40',
    'https://www.youtube.com/watch?v=abcdefghijk,2026-10-01,2026-10-31,100,5,10,NaN,40',
])
def test_invalid_import_does_not_save(isolated,line):
    with pytest.raises(ValueError):import_csv(csv_file(line))
    assert list_saved()['total']==0
