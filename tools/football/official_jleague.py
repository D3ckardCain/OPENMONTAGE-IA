"""Read the visible official J.League player rankings for an explicit season."""
import re
import urllib.request
from datetime import datetime, timezone

from tools.base_tool import BaseTool, ResourceProfile, ToolResult, ToolRuntime, ToolStability, ToolTier
from tools.football.uefa import DOM
from tools.football.uefa_names import normalized

BASE_URL = 'https://www.jleague.jp'
ROW_CLASS = 'm-ranking-player-list-item'


DIVISIONS = ('j1', 'j2', 'j3')
COMPETITIONS = {division: (f'{division.upper()} League', 'league') for division in DIVISIONS}
COMPETITIONS['leaguecup'] = ('Levain Cup', 'cup')
METRICS = {'goals': ('score', 'Top scorers'), 'assists': ('assist', 'Assists')}


def ranking_url(season, metric, competition='j1'):
    return f'{BASE_URL}/en/{competition}/stats/player/{season}/{METRICS[metric][0]}/search-list/'


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


def parse_ranking(html, season, metric, competition='j1'):
    dom = DOM()
    dom.feed(html)
    canonical = dom.root.first('link', rel='canonical')
    title = dom.root.first('title')
    if (not canonical or canonical.attrs.get('href') != ranking_url(season, metric, competition)
            or not title or title.text() != f'{season} Season - {METRICS[metric][1]} | {COMPETITIONS[competition][0]} Player Stats | Official Website of J.LEAGUE'):
        raise ValueError('La página no acredita la división o copa, la temporada y la métrica solicitadas')

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
            raise ValueError('Fila estadística J.League inválida')
        rows.append((name, links.get(id(row)), int(score)))
    if not rows:
        raise ValueError('La página oficial no mostró filas estadísticas')
    return rows


def profile_url(player_id):
    if not re.fullmatch(r'[0-9]+', player_id):
        raise ValueError('ID oficial J.League inválido')
    return f'{BASE_URL}/en/player/{player_id}/'


def profile_goals(html, player_id, name, season, competition='j1'):
    dom = DOM()
    dom.feed(html)
    canonical = dom.root.first('link', rel='canonical')
    title = dom.root.first('title')
    name_parts = normalized(name).split()
    accepted_names = {normalized(name)}
    # The English profiles sometimes put the family name first.
    if len(name_parts) == 2:
        accepted_names.add(' '.join(reversed(name_parts)))
    if (not canonical or canonical.attrs.get('href') != profile_url(player_id)
            or not title or normalized(title.text().split('|')[0]) not in accepted_names):
        raise ValueError('El perfil J.League no acredita la identidad')
    values = []
    for table in dom.root.walk('table'):
        headers = [[cell.text() for cell in row.walk('th')] for row in table.walk('tr') if row.first('th')]
        if headers != [['Season', 'Club', 'League', 'League Cup', 'U-21'],
                       ['App.', 'Goals', 'App.', 'Goals', 'App.', 'Goals']]:
            continue
        for row in table.walk('tr'):
            cells = list(row.walk('td'))
            if (len(cells) == 8 and cells[0].text() == str(season)
                    and cells[1].text().endswith(' ' + competition.upper())):
                values.append(cells[3].text())
    if len(values) != 1 or not re.fullmatch(r'[0-9]+', values[0]):
        raise ValueError('El perfil no acredita una única cifra de goles de la división solicitada para la temporada')
    return int(values[0])


def make_report(rankings, names, scope, queries, kind):
    records, unresolved, profile_queries = [], [], []
    for name in names:
        key = normalized(name)
        found, missing = {}, {}
        for metric, rows in rankings.items():
            matches = [row for row in rows if normalized(row[0]) == key]
            if len(matches) == 1 and matches[0][1]:
                found[metric] = matches[0]
                continue
            reason = {0: 'not_in_visible_ranking', 1: 'official_id_missing'}.get(len(matches), 'ambiguous')
            missing[metric] = reason
        ids = {row[1] for row in found.values()}
        if len(ids) > 1:
            unresolved.append({'name': name, 'reason': 'conflicting_official_ids'})
            continue
        if not found:
            unresolved.extend({'name': name, 'metric': metric, 'value': None, 'reason': reason}
                              for metric, reason in missing.items())
            continue
        official_name, player_id, _ = next(iter(found.values()))
        sources = dict(queries)
        if scope['competition'] in DIVISIONS and missing.get('goals') == 'not_in_visible_ranking':
            try:
                html, query = fetch(profile_url(player_id))
                goals = profile_goals(html, player_id, official_name, scope['season'], scope['competition'])
            except (OSError, ValueError):
                missing['goals'] = 'profile_goals_unverified'
            else:
                found['goals'] = (official_name, player_id, goals)
                sources['goals'] = query
                profile_queries.append(query)
                del missing['goals']
        unresolved.extend({'name': name, 'metric': metric, 'value': None, 'reason': reason}
                          for metric, reason in missing.items())
        facts = [
            {'metric': metric, 'value': found[metric][2], 'unit': metric, 'entity_id': player_id,
             'scope': scope, 'source_url': sources[metric]['url'], 'retrieved_at': sources[metric]['retrieved_at']}
            for metric in rankings if metric in found
        ]
        records.append({
            'entity_id': player_id,
            'identity': {'entity_id': player_id, 'name': official_name},
            'statistics': {metric: found[metric][2] if metric in found else None for metric in rankings},
            'statistics_source': dict(next(iter(queries.values()))) if len(queries) == 1 else None,
            'facts': facts,
        })
    if len({row['entity_id'] for row in records}) != len(records):
        raise ValueError('La comparativa requiere dos jugadores distintos')
    return {'source': 'J.League', 'type': kind, 'scope': scope, 'queries': list(queries.values()) + profile_queries,
            'records': records, 'unresolved': unresolved, 'ready_for_script': not unresolved,
            'visible_rows': len(next(iter(rankings.values()))) if len(rankings) == 1 else None,
            'visible_rows_by_metric': {metric: len(rows) for metric, rows in rankings.items()},
            'coverage': 'Rankings oficiales visibles. Una ausencia en la lista no equivale a cero.'}


class OfficialJLeague(BaseTool):
    name = 'official_jleague_live'
    version = '0.6.0'
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
                        'competition': {'enum': list(COMPETITIONS)},
                        'metrics': {'type': 'array', 'minItems': 1, 'uniqueItems': True,
                                    'items': {'enum': list(METRICS)}},
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
            competition = inputs.get('competition', 'j1')
            rankings, queries = {}, {}
            for metric in inputs.get('metrics', ['goals']):
                html, queries[metric] = fetch(ranking_url(season, metric, competition))
                rankings[metric] = parse_ranking(html, season, metric, competition)
            scope = {'competition': competition, 'season': season, 'phase': COMPETITIONS[competition][1], 'category': 'men'}
            kind = 'collectible_card' if card else 'player_comparison'
            data = make_report(rankings, names, scope, queries, kind)
            return ToolResult(success=True, data=data, artifacts=[], cost_usd=0, from_cache=False)
        except Exception as exc:
            return ToolResult(success=False, error='JLEAGUE_QUERY_REJECTED: ' + str(exc),
                              data={'fresh_query_failed': True, 'stale_fallback': False},
                              cost_usd=0, from_cache=False)
