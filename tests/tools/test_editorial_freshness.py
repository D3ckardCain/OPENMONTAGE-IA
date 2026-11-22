from lib.editorial_freshness import current


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
