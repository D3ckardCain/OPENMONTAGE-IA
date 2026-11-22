from lib.editorial_freshness import current,delivery_current


def test_later_editorial_revision_supersedes_saved_render_verification():
    verification={'status':'passed','finished_at':'2026-11-22T10:00:00+00:00'}
    reviews=[{'decision':'approved','at':'2026-11-22T09:00:00+00:00'},
             {'decision':'revision_requested','at':'2026-11-22T10:01:00+00:00'}]
    assert current(verification,reviews) is False
    assert current({'status':'passed','finished_at':'2026-11-22T10:02:00+00:00'},reviews) is True
    assert current(verification,[{'decision':'revision_requested','at':'bad'}]) is False


def test_no_revision_keeps_saved_technical_result_current():
    assert current({'status':'passed'},[]) is True
    assert current({'status':'failed'},[]) is False


def test_final_copy_must_match_verified_source_and_follow_verification():
    verification={'status':'passed','finished_at':'2026-11-22T10:00:00+00:00',
                  'outputs':[{'path':'/project/renders/final.mp4','sha256':'a'*64}]}
    delivery={'copied':True,'delivered_at':'2026-11-22T10:01:00+00:00',
              'outputs':[{'source':'/project/renders/final.mp4','sha256':'a'*64}]}
    assert delivery_current(verification,delivery,[]) is True
    assert delivery_current(verification,{**delivery,'outputs':[{'source':'/project/renders/final.mp4','sha256':'b'*64}]},[]) is False
    assert delivery_current(verification,{**delivery,'delivered_at':'2026-11-22T09:59:00+00:00'},[]) is False
    assert delivery_current(verification,{**delivery,'outputs':[]},[]) is False
    assert delivery_current(verification,delivery,[{'decision':'revision_requested','at':'2026-11-22T10:02:00+00:00'}]) is False


def test_new_saved_football_selection_supersedes_prior_render():
    verification={'status':'passed','football_selection':{'selection_id':'a'*64,'sha256':'b'*64}}
    assert current(verification,[],{'selection_id':'a'*64,'sha256':'b'*64}) is True
    assert current(verification,[],{'selection_id':'c'*64,'sha256':'d'*64}) is False
    assert current(verification,[],None) is False
    assert current({'status':'passed'},[],{'selection_id':'c'*64,'sha256':'d'*64}) is False
