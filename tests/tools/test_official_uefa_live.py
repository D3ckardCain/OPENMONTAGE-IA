import unittest
from unittest.mock import patch
from tools.football.official_uefa import OfficialUEFA
from tools.football.uefa_live import Reply
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
 def test_womens_champions_uses_its_own_official_context(self):
  tool = OfficialUEFA()
  page = 'https://www.uefa.com/womenschampionsleague/history/'
  config = """
window.competitionFolder = 'wucl';
window.competitionId = '28';
window.currentSeason = 2027;
window.apiKey = 'fixture';
window.compStatsApiUrl = 'https://compstats.uefa.com/';
window.compApiUrl = 'https://comp.uefa.com/';
window.matchApiUrl = 'https://match.uefa.com/';
"""
  with patch.object(tool.client.transport, 'get', return_value=Reply(config, page, 'fixture')) as get:
   context = tool.client.context('women_champions')
   get.assert_called_once_with(page)
  self.assertIn('women_champions', tool.input_schema['properties']['competition']['enum'])
  self.assertEqual(context.competition_id, '28')
  self.assertEqual(context.current_edition, 2027)

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


def test_player_id_batches_recover_metrics_without_combining_teams(monkeypatch):
 from types import SimpleNamespace
 from tools.football.uefa import UEFAHTTPError

 tool = OfficialUEFA()
 requests = []
 context = SimpleNamespace(competition='champions', competition_id='1', current_edition=2027,
                           stats_url='https://compstats.uefa.com/')
 monkeypatch.setattr(tool.client, 'context', lambda competition: context)

 def request(ctx, scope, player_id, metrics):
  requests.append(metrics)
  assert scope['seasonYear'] == 2024 and scope['phase'] == 'TOURNAMENT'
  if 'assists' in metrics:
   raise UEFAHTTPError(500)
  rows = [{'playerId': player_id, 'teamId': team, 'statistics': [
      {'name': metric, 'value': value} for metric in metrics]} for team, value in [('10', '0'), ('20', '2')]]
  return rows, {'url': 'https://compstats.uefa.com/' + metrics[0], 'consultado_utc': '2026-11-20'}

 monkeypatch.setattr(tool.client, '_player_request', request)
 result = tool.execute({'action': 'player', 'competition': 'champions', 'edition': 2024,
                        'player_id': '100', 'metrics': ['goals', 'assists']})
 assert result.success, result.error
 assert requests == [['goals', 'assists'], ['goals'], ['assists']]
 assert result.data['batch_query']['status'] == 'partial'
 assert result.data['batch_query']['failed_batches'][0]['metrics'] == ['assists']
 rows = result.data['registros']
 assert [row['teamId'] for row in rows] == ['10', '20']
 assert [row['statistics'][0]['value'] for row in rows] == ['0', '2']
 assert all(row['metricas_no_disponibles'] == ['assists'] for row in rows)
 assert all(row['fuente_por_metrica']['goals'] == result.data['consultas'][0] for row in rows)


def test_ranking_batches_preserve_order_and_join_by_player_and_team(monkeypatch):
 from tools.football.uefa import UEFAHTTPError

 tool = OfficialUEFA()
 calls = []

 def ranking(competition, edition, entity, metrics, phase, team_id, order):
  calls.append(metrics)
  if 'saves' in metrics:
   raise UEFAHTTPError(500)
  source = {'url': 'https://compstats.uefa.com/' + metrics[0], 'consultado_utc': '2026-11-20'}
  entries = [('1', '10', 8), ('2', '20', 3)] if metrics == ['goals'] else [
      ('2', '20', 5), ('1', '999', 100), ('1', '10', 0)]
  return {'alcance': {'seasonYear': edition, 'phase': phase, 'metricas': metrics},
          'consultas': [source], 'registros': [
              {'id': pid, 'team_id': team, 'estadisticas': {metrics[0]: value},
               'fuente_estadisticas': source, 'posicion': position}
              for position, (pid, team, value) in enumerate(entries, 1)]}

 monkeypatch.setattr(tool.client, 'ranking', ranking)
 result = tool.execute({'action': 'ranking', 'competition': 'champions', 'edition': 2024,
                        'entity': 'player', 'metrics': ['goals', 'assists', 'saves']})
 assert result.success, result.error
 assert calls == [['goals'], ['assists', 'saves'], ['assists'], ['saves']]
 first, second = result.data['registros']
 assert [(r['id'], r['posicion']) for r in (first, second)] == [('1', 1), ('2', 2)]
 assert first['estadisticas'] == {'goals': 8, 'assists': 0, 'saves': None}
 assert first['fuente_por_metrica']['assists'] == result.data['consultas'][1]
 assert result.data['batch_query']['status'] == 'partial'
