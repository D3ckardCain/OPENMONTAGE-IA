"""Read the visible official J1 top-scorer list for an explicit season."""
import re
import urllib.request
from datetime import datetime, timezone

from tools.base_tool import BaseTool, ResourceProfile, ToolResult, ToolRuntime, ToolStability, ToolTier
from tools.football.uefa import DOM
from tools.football.uefa_names import normalized

BASE_URL = 'https://www.jleague.jp'
ROW_CLASS = 'm-ranking-player-list-item'


def goals_url(season):
    return f'{BASE_URL}/en/j1/stats/player/{season}/score/search-list/'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Redirección J.League no admitida')


def fetch(url):
    request = urllib.request.Request(url, headers={'Cache-Control': 'no-cache'})
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=25) as response:
        data = response.read(4_000_001)
        if len(data) > 4_000_000:
            raise ValueError('Página J.League demasiado grande')
        return data.decode('utf-8'), {
            'url': url,
            'retrieved_at': datetime.now(timezone.utc).isoformat(),
            'http_date': response.headers.get('Date'),
        }


def parse_goals(html, season):
    dom = DOM()
    dom.feed(html)
    canonical = dom.root.first('link', rel='canonical')
    title = dom.root.first('title')
    if (not canonical or canonical.attrs.get('href') != goals_url(season)
            or not title or title.text() != f'{season} Season - Top scorers | J1 League Player Stats | Official Website of J.LEAGUE'):
        raise ValueError('La página no acredita J1, la temporada solicitada y el ranking de goles')

    links = {}
    for link in dom.root.walk('a', **{'class': ROW_CLASS + '__link'}):
        row = link.first('div', **{'class': ROW_CLASS})
        player = re.fullmatch(r'/en/player/([0-9]+)/', link.attrs.get('href') or '')
        if row and player:
            links[id(row)] = player[1]

    rows = []
    for row in dom.root.walk('div', **{'class': ROW_CLASS}):
        name = row.attrs.get('name') or ''
        score = row.attrs.get('score') or ''
        points = next((p.text() for p in row.walk('p')
                       if ROW_CLASS + '__points' in (p.attrs.get('class') or '').split()), None)
        if not name.strip() or not re.fullmatch(r'[0-9]+', score) or score != points:
            raise ValueError('Fila de goles J1 inválida')
        rows.append((name, links.get(id(row)), int(score)))
    if not rows:
        raise ValueError('La página oficial no mostró filas de goles')
    return rows


def make_report(rows, names, scope, query, kind):
    records, unresolved = [], []
    for name in names:
        key = normalized(name)
        matches = [row for row in rows if normalized(row[0]) == key]
        if len(matches) != 1 or not matches[0][1]:
            reason = {0: 'not_in_visible_ranking', 1: 'official_id_missing'}.get(len(matches), 'ambiguous')
            unresolved.append({'name': name, 'reason': reason})
            continue
        official_name, player_id, goals = matches[0]
        records.append({
            'entity_id': player_id,
            'identity': {'entity_id': player_id, 'name': official_name},
            'statistics': {'goals': goals},
            'statistics_source': dict(query),
            'facts': [{'metric': 'goals', 'value': goals, 'unit': 'goals', 'entity_id': player_id,
                       'scope': scope, 'source_url': query['url'], 'retrieved_at': query['retrieved_at']}],
        })
    if len({row['entity_id'] for row in records}) != len(records):
        raise ValueError('La comparativa requiere dos jugadores distintos')
    return {'source': 'J.League', 'type': kind, 'scope': scope, 'queries': [query], 'records': records,
            'unresolved': unresolved, 'ready_for_script': not unresolved, 'visible_rows': len(rows),
            'coverage': 'Ranking oficial visible. Una ausencia en la lista no equivale a cero goles.'}


class OfficialJLeague(BaseTool):
    name = 'official_jleague_live'
    version = '0.1.0'
    provider = 'jleague_official'
    tier = ToolTier.SOURCE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    capability = 'football_statistics'
    capabilities = ['football_statistics', 'official_live_data']
    dependencies = []
    idempotency_key_fields = []
    side_effects = ['read_public_jleague_statistics_page']
    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=256, vram_mb=0, disk_mb=0, network_required=True)
    install_instructions = 'Consulta HTTPS a J.League desde Python local, sin cuenta ni pago.'
    supports = {'offline': False, 'persistent_cache': False, 'official_sources': True}
    input_schema = {'type': 'object', 'additionalProperties': False, 'required': ['action', 'season', 'names'],
                    'properties': {
                        'action': {'enum': ['compare_players', 'collectible_card']},
                        'season': {'type': 'integer', 'minimum': 1993, 'maximum': 9999},
                        'names': {'type': 'array', 'minItems': 1, 'maxItems': 2,
                                  'items': {'type': 'string', 'minLength': 1, 'maxLength': 150}},
                    }}

    def execute(self, inputs):
        from jsonschema import validate

        try:
            validate(inputs, self.input_schema)
            names = inputs['names']
            keys = {normalized(name) for name in names}
            card = inputs['action'] == 'collectible_card'
            if len(names) != (1 if card else 2) or len(keys) != len(names):
                raise ValueError('Indica un nombre para la postal o dos nombres distintos para la comparativa')
            season = inputs['season']
            html, query = fetch(goals_url(season))
            scope = {'competition': 'j1', 'season': season, 'phase': 'league', 'category': 'men'}
            kind = 'collectible_card' if card else 'player_comparison'
            data = make_report(parse_goals(html, season), names, scope, query, kind)
            return ToolResult(success=True, data=data, artifacts=[], cost_usd=0, from_cache=False)
        except Exception as exc:
            return ToolResult(success=False, error='JLEAGUE_QUERY_REJECTED: ' + str(exc),
                              data={'fresh_query_failed': True, 'stale_fallback': False},
                              cost_usd=0, from_cache=False)
