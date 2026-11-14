import unittest
from unittest.mock import patch
from tools.research.youtube_client import YouTube,Filters,Unavailable,duration_seconds
CID='UC'+'a'*22
class Fake:
 def __init__(self,language='en',subs='1000',duration='PT2M',views='100000',hidden=False):self.calls=[];self.language=language;self.subs=subs;self.duration=duration;self.views=views;self.hidden=hidden
 def __call__(self,r,p):
  self.calls.append((r,p))
  if r=='search':return {'items':[{'id':{'videoId':'video1'}}]}
  if r=='channels':return {'items':[{'id':CID,'snippet':{'title':'Example'},'statistics':{'subscriberCount':self.subs,'hiddenSubscriberCount':self.hidden},'contentDetails':{'relatedPlaylists':{'uploads':'UUtest'}}}]}
  if r=='playlistItems':return {'items':[{'contentDetails':{'videoId':'video1'}}]}
  return {'items':[{'id':'video1','snippet':{'channelId':CID,'defaultAudioLanguage':self.language,'title':'Example'},'statistics':{'viewCount':self.views},'contentDetails':{'duration':self.duration},'status':{'license':'youtube'}}]}
class Tests(unittest.TestCase):
 def search(self,f=None,**kwargs):return YouTube('test',Fake(**kwargs)).search('animals',f)
 def test_filters(self):self.assertEqual(len(self.search(Filters(min_views=50000,max_subscribers=2000))['results']),1)
 def test_hidden_not_zero(self):self.assertEqual(self.search(Filters(min_subscribers=0),hidden=True)['results'],[])
 def test_unknown_language(self):self.assertEqual(self.search(Filters(language='de',strict_language=True),language=None)['results'],[])
 def test_language_variant(self):self.assertEqual(len(self.search(Filters(language='en',strict_language=True),language='en-GB')['results']),1)
 def test_duration_not_short_proof(self):self.assertIsNone(self.search(Filters(format='short_candidate'))['results'][0]['shorts_confirmed'])
 def test_no_earnings_guess(self):
  r=self.search()['results'][0]
  for k in ('monetized','rpm','revenue'):self.assertIsNone(r[k])
 def test_no_write(self):
  with patch('builtins.open',side_effect=AssertionError('Disk forbidden')):self.search()
 def test_fresh_calls(self):
  f=Fake();c=YouTube('test',f);c.search('animals');c.search('animals');self.assertEqual(sum(r=='search' for r,p in f.calls),2)
 def test_duration_days(self):self.assertEqual(duration_seconds('P1DT1H2M3S'),90123)
 def test_bad_duration(self):
  with self.assertRaises(Unavailable):duration_seconds('unknown')
 def test_inverted_limits(self):
  with self.assertRaises(Unavailable):Filters(min_views=100,max_views=10).validate()
 def test_partial_scope(self):
  c=YouTube('test',lambda r,p:{'items':[],'nextPageToken':'next'})
  r=c.search('animals');self.assertFalse(r['scope']['search_pages_exhausted']);self.assertFalse(r['scope']['global_coverage'])
 def test_channel_uploads(self):self.assertEqual(len(YouTube('test',Fake()).channel(CID)['results']),1)
 def test_error_no_fallback(self):
  with self.assertRaises(Unavailable):YouTube('test',lambda r,p:{'error':'quota'}).search('animals')
if __name__=='__main__':unittest.main()
