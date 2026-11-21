"""Read the public DFL player rankings in independent metric requests."""
import json
import re
import urllib.request
from datetime import datetime, timezone

from tools.base_tool import BaseTool, ResourceProfile, ToolResult, ToolRuntime, ToolStability, ToolTier
from tools.football.uefa import DOM
from tools.football.uefa_names import normalized

COMPETITIONS = {'bundesliga': ('bundesliga', 'DFL-COM-000001'),
                'bundesliga_2': ('2bundesliga', 'DFL-COM-000002')}
METRICS = {'goals': ('goals', 'shotsAtGoalSuccessful'),
           'assists': ('assists', 'assists'),
           'shots': ('shots', 'shotsAtGoal')}
SEASON = '2024-2025'


def page_url(competition, metric):
    slug, _ = COMPETITIONS[competition]
    page, _ = METRICS[metric]
    return f'https://www.bundesliga.com/en/{slug}/stats/players/{page}/{SEASON}'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Redirección DFL no admitida')


def fetch(url):
    request = urllib.request.Request(url, headers={'Cache-Control': 'no-cache'})
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=20) as response:
        body = response.read(4_000_001)
    if len(body) > 4_000_000:
        raise ValueError('Documento DFL demasiado grande')
    return body.decode('utf-8')


def parse(html, competition, metric):
    parser = DOM()
    parser.feed(html)
    canonical = parser.root.first('link', rel='canonical')
    state = parser.root.first('script', id='ng-state', type='application/json')
    if not canonical or canonical.attrs.get('href') != page_url(competition, metric) or not state:
        raise ValueError('La página DFL no acredita el alcance solicitado')
    _, competition_id = COMPETITIONS[competition]
    _, provider_metric = METRICS[metric]
    endpoint = (f'https://wapp.bapi.bundesliga.com/all/{competition_id}/seasons/DFL-SEA-0001K8'
                f'/stats/playerRankings/{provider_metric}.json')
    entries = [entry['b'] for entry in json.loads(state.text()).values()
               if isinstance(entry, dict) and entry.get('u') == endpoint and entry.get('s') == 200
               and isinstance(entry.get('b'), dict) and len(entry['b']) == 10]
    if len(entries) != 1:
        raise ValueError('Ranking principal DFL ausente o ambiguo')
    for player_id, row in entries[0].items():
        if (not re.fullmatch(r'DFL-OBJ-[A-Z0-9]+', player_id)
                or row['dflDatalibraryObjectId'] != player_id or not normalized(row['name'])
                or not re.fullmatch(r'DFL-CLU-[A-Z0-9]+', row['club']['dflDatalibraryClubId'])
                or type(row['value']) is not int or row['value'] < 0):
            raise ValueError('Fila DFL inválida')
    return entries[0]


class OfficialBundesliga(BaseTool):
    name = 'official_bundesliga_live'
    version = '0.1.0'
    provider = 'dfl_official'
    tier = ToolTier.SOURCE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    capability = 'football_statistics'
    capabilities = ['football_statistics', 'official_live_data']
    dependencies = []
    idempotency_key_fields = []
    side_effects = ['read_public_dfl_rankings']
    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=128, vram_mb=0, disk_mb=0, network_required=True)
    install_instructions = 'Consultas HTTPS a rankings públicos DFL. Sin cuenta ni pago.'
    input_schema = {
        'type': 'object', 'additionalProperties': False,
        'required': ['action', 'competition', 'season', 'names'],
        'properties': {
            'action': {'enum': ['compare_players', 'collectible_card']},
            'competition': {'enum': list(COMPETITIONS)},
            'season': {'const': SEASON},
            'names': {'type': 'array', 'minItems': 1, 'maxItems': 2,
                      'items': {'type': 'string', 'minLength': 1, 'maxLength': 150}},
        },
    }

    def execute(self, inputs):
        from jsonschema import ValidationError, validate

        try:
            validate(inputs, self.input_schema)
        except ValidationError as exc:
            return ToolResult(success=False, error=exc.message, cost_usd=0, from_cache=False)
        card = inputs['action'] == 'collectible_card'
        names = [normalized(name) for name in inputs['names']]
        if not all(names) or len(names) != (1 if card else 2) or len(set(names)) != len(names):
            return ToolResult(success=False, error='Indica un nombre para la postal o dos distintos para la comparativa',
                              cost_usd=0, from_cache=False)

        competition = inputs['competition']
        scope = {'competition': competition, 'season': SEASON, 'phase': 'regular_season', 'category': 'men'}
        queries, failures, roster = [], {}, {}
        for metric in METRICS:
            url = page_url(competition, metric)
            try:
                ranking = parse(fetch(url), competition, metric)
            except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
                failures[metric] = str(exc)
                continue
            source = {'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(), 'metric': metric}
            queries.append(source)
            for player_id, row in ranking.items():
                record = roster.setdefault(player_id, {
                    'entity_id': player_id,
                    'identity': {'entity_id': player_id, 'name': row['name']},
                    'statistics': {}, 'facts': [], 'club_ids': [],
                })
                club_id = row['club']['dflDatalibraryClubId']
                if club_id not in record['club_ids']:
                    record['club_ids'].append(club_id)
                value = row['value']
                record['statistics'][metric] = value
                record['facts'].append({'metric': metric, 'value': value, 'unit': metric, 'entity_id': player_id,
                                        'scope': scope, 'source_url': url, 'retrieved_at': source['retrieved_at']})

        records, unresolved = [], []
        for original, name in zip(inputs['names'], names):
            matches = [record for record in roster.values() if normalized(record['identity']['name']) == name]
            if len(matches) == 1:
                records.append(matches[0])
            else:
                unresolved.append(original)
        shared = set.intersection(*(set(record['statistics']) for record in records)) if records else set()
        data = {'source': 'DFL', 'type': 'collectible_card' if card else 'player_comparison', 'scope': scope,
                'records': records, 'queries': queries, 'failed_metrics': failures, 'unresolved': unresolved,
                'ready_for_script': not failures and not unresolved and bool(shared),
                'coverage': 'Diez entradas publicadas por ranking de la temporada 2024/25.'}
        return ToolResult(success=bool(queries), data=data, error=None if queries else 'DFL_QUERY_FAILED',
                          cost_usd=0, from_cache=False)
