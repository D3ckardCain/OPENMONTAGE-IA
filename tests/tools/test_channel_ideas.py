import pytest

from lib import production_studio as studio
from lib.channel_dossiers import save
from lib.channel_ideas import create,list_drafts

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
