from tools.research.youtube_research import YouTubeResearch

def test_no_secret_in_error(monkeypatch):
    monkeypatch.setenv('YOUTUBE_API_KEY','secret-fixture')
    def fail(*args,**kwargs):raise RuntimeError('secret-fixture')
    monkeypatch.setattr('tools.research.youtube_research.YouTube',fail)
    result=YouTubeResearch().execute({'mode':'search','query':'animals'})
    assert not result.success
    assert 'secret-fixture' not in result.error
    assert result.artifacts == []

def test_reject_output_and_unknown_filters():
    for extra in ({'output_path':'/tmp/results.json'},{'filters':{'rpm':10}}):
        result=YouTubeResearch().execute({'mode':'search','query':'animals',**extra})
        assert not result.success

def test_adapter_passes_filters(monkeypatch):
    class Client:
        def search(self,query,filters,region,after,before,pages):
            assert filters.min_views == 1000
            assert query == 'animals'
            return {'results':[], 'rpm':None}
    monkeypatch.setattr('tools.research.youtube_research.YouTube',Client)
    result=YouTubeResearch().execute({'mode':'search','query':'animals','filters':{'min_views':1000}})
    assert result.success and result.data['rpm'] is None


def test_missing_key_reports_unavailable(monkeypatch):
    from tools.base_tool import ToolStatus
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    assert YouTubeResearch().get_status() == ToolStatus.UNAVAILABLE

def test_registry_discovers_adapter():
    from tools.tool_registry import ToolRegistry
    from tools.research import youtube_research
    assert "youtube_research" in ToolRegistry().register_module(youtube_research)
