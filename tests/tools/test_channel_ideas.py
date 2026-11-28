import pytest

from lib import production_studio as studio
from lib.channel_dossiers import save
from lib.channel_ideas import create,list_drafts,compare

CHANNEL='UC'+'a'*22
VIDEO='abcdefghijk'


def dossier():
    return {'source':'YouTube Data API','channel_id':CHANNEL,
            'retrieved_at_utc':'2026-11-22T00:00:00Z','since_utc':'2026-10-23T00:00:00Z',
            'cutoff_at_utc':'2026-11-22T00:00:00Z','complete_period':False,
            'publications':[{'id':VIDEO,'title':'Título del otro canal','viewCount':100}]}


def proposal(snapshot,**changes):
    return {'channel_id':CHANNEL,'snapshot_id':snapshot,'video_ids':[VIDEO],
            'title':'Una historia propia sobre la creación de videos',
            'angle':'Estudiar los pasos reales de producción local y comprobar cada afirmación con fuentes.',
            'audience':'Creadores en español','language':'es','format':'long',**changes}


def test_draft_keeps_source_evidence_and_is_not_approval(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path)
    source=save(dossier())
    idea=create(proposal(source['id']))
    assert idea['snapshot_sha256']==source['report_sha256']
    assert idea['references'][0]['viewCount_at_source']==100
    assert idea['status']=='draft' and idea['fact_review_required'] and idea['rights_review_required']
    assert list_drafts(CHANNEL)[0]['id']==idea['id']


def test_foreign_video_or_copied_title_rejected(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path)
    source=save(dossier())
    with pytest.raises(ValueError,match='ajena'):create(proposal(source['id'],video_ids=['bbbbbbbbbbb']))
    with pytest.raises(ValueError,match='título propio'):create(proposal(source['id'],title='Título del otro canal'))
    assert list_drafts(CHANNEL)==[]


def test_compare_drafts_keeps_snapshots_separate_and_does_not_rank(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path)
    first=save(dossier())
    a=create(proposal(first['id']))
    second_report={**dossier(),'retrieved_at_utc':'2026-11-23T00:00:00Z',
                   'publications':[{'id':VIDEO,'title':'Título del otro canal','viewCount':200}]}
    second=save(second_report)
    b=create(proposal(second['id'],title='Otra historia editorial de producción',format='short'))
    result=compare(CHANNEL,[a['id'],b['id']])
    assert result['same_snapshot'] is False and result['shared_reference_ids']==[VIDEO]
    assert [item['references'][0]['viewCount_at_source'] for item in result['proposals']]==[100,200]
    assert all('score' not in item for item in result['proposals'])
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    response=client.post('/api/research/channels/ideas/'+CHANNEL+'/compare',json={'idea_ids':[a['id'],b['id']]})
    assert response.status_code==200 and response.json()['same_snapshot'] is False
    assert response.headers['cache-control']=='no-store'
    assert client.post('/api/research/channels/ideas/'+CHANNEL+'/compare',json={'idea_ids':[a['id'],a['id']]}).status_code==400
