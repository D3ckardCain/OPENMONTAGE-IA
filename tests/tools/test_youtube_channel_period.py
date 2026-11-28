from datetime import datetime,timedelta,timezone

from tools.research.youtube_channel_period import audit_channel

CHANNEL='UC'+'a'*22
NOW=datetime(2026,11,22,tzinfo=timezone.utc)


class Client:
    def __init__(self,older_page=True):self.calls={};self.older_page=older_page
    def get(self,resource,**params):
        self.calls[resource]=self.calls.get(resource,0)+1
        if resource=='channels':return {'items':[{'id':CHANNEL,'snippet':{'title':'Demo'},'contentDetails':{'relatedPlaylists':{'uploads':'uploads'}}}]}
        if resource=='playlistItems':
            if params.get('pageToken'):
                old=(NOW-timedelta(days=40)).isoformat()
                return {'items':[{'contentDetails':{'videoId':'v'+'2'*10,'videoPublishedAt':old}}],
                        **({'nextPageToken':'third'} if not self.older_page else {})}
            recent=(NOW-timedelta(days=2)).isoformat()
            return {'items':[{'contentDetails':{'videoId':'v'+'1'*10,'videoPublishedAt':recent}}],
                    'nextPageToken':'next'}
        if resource=='videos':
            return {'items':[{'id':'v'+'1'*10,'snippet':{'channelId':CHANNEL,'publishedAt':NOW.isoformat()},
                              'statistics':{'viewCount':'900'},'contentDetails':{'duration':'PT1M'}}]}
        raise AssertionError(resource)
    def batches(self,resource,ids,part):return self.get(resource,id=','.join(ids),part=part)['items']


def test_period_paginates_and_merges_before_analysis():
    client=Client()
    report=audit_channel(CHANNEL,30,10,client,NOW)
    assert report['complete_period'] is True
    assert report['pages_read']==2 and report['requests']['playlistItems']==2
    assert len(report['publications'])==1 and report['analysis']['median_views']==900
    assert report['analysis']['top_publication_share'] is None


def test_page_limit_marks_period_incomplete():
    report=audit_channel(CHANNEL,30,1,Client(),NOW)
    assert report['complete_period'] is False
    assert report['pages_read']==1


def test_shorter_window_stops_at_old_page():
    report=audit_channel(CHANNEL,7,10,Client(),NOW)
    assert report['complete_period'] is True
    assert (datetime.fromisoformat(report['cutoff_at_utc'])-datetime.fromisoformat(report['since_utc'])).days==7
