import unittest
from unittest.mock import patch
from tools.football.official_uefa import OfficialUEFA
from tools.base_tool import _is_cacheable
from tools.tool_registry import ToolRegistry
class Stub:
 def __init__(self):self.calls=0
 def definitions(self,competition):self.calls+=1;return {'source':'test','request':self.calls}
class Integration(unittest.TestCase):
 def tool(self):
  t=OfficialUEFA();t.client=Stub();return t
 def test_discoverable(self):
  from tools.football import official_uefa
  self.assertIn('official_uefa_live',ToolRegistry().register_module(official_uefa))
 def test_no_cached_statistics(self):
  t=self.tool();args={'action':'definitions','competition':'champions'}
  with patch.dict('os.environ',{'OPENMONTAGE_ASSET_CACHE':'1'}),patch('lib.asset_cache.get_default_asset_cache',side_effect=AssertionError('Cache forbidden')):
   a=t.execute(args);b=t.execute(args)
  self.assertTrue(a.success);self.assertTrue(b.success);self.assertNotEqual(a.data,b.data);self.assertFalse(b.from_cache);self.assertEqual(b.artifacts,[])
 def test_no_paths_accepted(self):
  t=self.tool();r=t.execute({'action':'definitions','competition':'champions','output_path':'stats.json'})
  self.assertFalse(r.success);self.assertEqual(t.client.calls,0)
 def test_extra_parameters_not_silently_ignored(self):
  t=self.tool();r=t.execute({'action':'definitions','competition':'champions','edition':2027})
  self.assertFalse(r.success)
 def test_errors_dont_return_old_data(self):
  t=self.tool()
  with patch.object(t.client,'definitions',side_effect=OSError('network down')):r=t.execute({'action':'definitions','competition':'champions'})
  self.assertFalse(r.success);self.assertFalse(r.data['stale_fallback'])
 def test_cost_and_network(self):
  t=self.tool();self.assertEqual(t.estimate_cost({}),0);self.assertTrue(t.resource_profile.network_required);self.assertFalse(_is_cacheable(t,{'output_path':'x.json'}))
if __name__=='__main__':unittest.main()
