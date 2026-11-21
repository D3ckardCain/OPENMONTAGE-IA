"""Read the Premier League's 2024/25 Matchweek 29 leadership tables."""
import re
import urllib.request
from datetime import datetime, timezone

from tools.base_tool import BaseTool, ResourceProfile, ToolResult, ToolRuntime, ToolStability, ToolTier
from tools.football.uefa import DOM, Node
from tools.football.uefa_names import normalized

URL = 'https://www.premierleague.com/en/news/4271603'
SCOPE = {'competition': 'premier', 'season': '2024-2025', 'phase': 'regular_season',
         'category': 'men', 'through_matchweek': 29}
TABLES = {
    'Most goals': ('goals', 'Goals'),
    'Most shots': ('shots', 'Shots'),
    'Most big chances missed': ('big_chances_missed', 'Big chances missed'),
    'Most assists': ('assists', 'Assists'),
    'Most Expected Assists (xA)': ('expected_assists', 'xA'),
    'Most chances created': ('chances_created', 'Chances created'),
    'Most successful passes': ('passes_completed', 'Succ. passes'),
    'Most dribbles completed': ('dribbles_completed', 'Dribbles completed'),
    'Most duels won': ('duels_won', 'Duels won'),
    'Most aerial duels won': ('aerial_duels_won', 'Aerial duels won'),
    'Most tackles won': ('tackles_won', 'Tackles won'),
    'Most blocks': ('blocks', 'Blocks'),
    'Most interceptions': ('interceptions', 'Interceptions'),
    'Most clearances': ('clearances', 'Clearances'),
    'Most recoveries (outfield players)': ('recoveries', 'Recoveries'),
    'Fastest players': ('top_speed', 'Top speed (km/h)'),
    'Most sprints': ('sprints', 'Sprints'),
    'Most distance covered': ('distance_covered', 'Distance (km)'),
    'Most saves': ('saves', 'Saves'),
    'Best save percentage (min. 20 saves)': ('save_percentage', 'Save %'),
}
METRICS = tuple(metric for metric, _ in TABLES.values())
UNITS = {'top_speed': 'km/h', 'distance_covered': 'km', 'save_percentage': '%'}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Redirección de Premier League no admitida')


def fetch():
    with urllib.request.build_opener(NoRedirect()).open(URL, timeout=20) as response:
        body = response.read(2_000_001)
    if len(body) > 2_000_000:
        raise ValueError('Informe de Premier League demasiado grande')
    return body.decode('utf-8')


def parse(html):
    parser = DOM()
    parser.feed(html)
    root = parser.root
    canonical = root.first('link', rel='canonical')
    if (not canonical or canonical.attrs.get('href') != URL
            or not any('2024/25 Premier League' in p.text() and 'first 29 Matchweeks' in p.text()
                       for p in root.walk('p'))):
        raise ValueError('El informe no acredita el corte de la jornada 29')
    report, failures = {}, set(METRICS)
    for container in root.walk('div'):
        heading = None
        for node in container.children:
            if not isinstance(node, Node):
                continue
            if node.tag == 'h6':
                heading = TABLES.get(node.text())
            if node.tag != 'table' or heading is None:
                continue
            metric, column = heading
            heading = None
            if metric in report:
                raise ValueError('Tabla duplicada en el informe')
            rows = list(node.walk('tr'))
            if not rows or [cell.text() for cell in rows[0].walk('td')] != ['Player', column]:
                continue
            rankings = {}
            for row in rows[1:]:
                player = row.first('th')
                number = row.first('td')
                if not player or not number:
                    raise ValueError('Fila incompleta en el informe')
                raw = number.text()
                pattern = r'[0-9]+(?:\.[0-9]+)?' if metric in UNITS or metric == 'expected_assists' else r'(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)'
                if not re.fullmatch(pattern + ('%' if metric == 'save_percentage' else ''), raw):
                    raise ValueError('Cifra no reconocida en el informe')
                value = float(raw.rstrip('%')) if '.' in raw else int(raw.rstrip('%').replace(',', ''))
                for name, club in re.findall(r"([^()]+?)\s+\(([A-Z]{3})\)", player.text()):
                    name = name.strip(' ,')
                    key = f'{normalized(name)}:{club}'
                    if key in rankings:
                        raise ValueError('Jugador duplicado en una tabla')
                    rankings[key] = (name, club, value)
            if rankings:
                report[metric] = rankings
                failures.remove(metric)
    return report, sorted(failures)


class OfficialPremier(BaseTool):
    name = 'official_premier_live'
    version = '0.1.0'
    provider = 'premier_official'
    tier = ToolTier.SOURCE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    capability = 'football_statistics'
    capabilities = ['football_statistics', 'official_live_data']
    dependencies = []
    idempotency_key_fields = []
    side_effects = ['read_public_premier_report']
    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=128, vram_mb=0, disk_mb=0, network_required=True)
    install_instructions = 'Informe público por jornadas de Premier League. Sin cuenta ni pago.'
    input_schema = {
        'type': 'object', 'additionalProperties': False, 'required': ['action', 'season', 'names'],
        'properties': {
            'action': {'enum': ['compare_players', 'collectible_card']},
            'season': {'const': SCOPE['season']},
            'names': {'type': 'array', 'minItems': 1, 'maxItems': 2, 'uniqueItems': True,
                      'items': {'type': 'string', 'minLength': 1, 'maxLength': 150}},
        },
    }

    def execute(self, inputs):
        from jsonschema import ValidationError, validate

        try:
            validate(inputs, self.input_schema)
            card = inputs['action'] == 'collectible_card'
            if len(inputs['names']) != (1 if card else 2):
                raise ValueError('Indica un nombre para la postal o dos para comparar')
            rankings, failures = parse(fetch())
            if not rankings:
                raise ValueError('El informe carece de rankings reconocidos')
        except (ValidationError, ValueError, OSError) as exc:
            return ToolResult(success=False, error=str(exc), cost_usd=0, from_cache=False)

        scope = dict(SCOPE)
        source = {'url': URL, 'retrieved_at': datetime.now(timezone.utc).isoformat()}
        roster = {}
        for metric, ranking in rankings.items():
            for key, (name, club, value) in ranking.items():
                record = roster.setdefault(key, {'entity_id': key, 'club': club,
                                                 'identity': {'name': name, 'entity_id': key},
                                                 'statistics': {}, 'facts': []})
                record['statistics'][metric] = value
                record['facts'].append({'metric': metric, 'value': value, 'unit': UNITS.get(metric, metric),
                                        'entity_id': key, 'scope': scope, 'source_url': URL,
                                        'retrieved_at': source['retrieved_at']})

        records, unresolved = [], []
        for name in inputs['names']:
            matches = [row for row in roster.values()
                       if normalized(name) in (normalized(row['identity']['name']),
                                               normalized(f"{row['identity']['name']} ({row['club']})"))]
            if len(matches) == 1 and matches[0] not in records:
                records.append(matches[0])
            else:
                unresolved.append(name)
        shared = set.intersection(*(set(row['statistics']) for row in records)) if records else set()
        data = {'source': 'Premier League', 'type': 'collectible_card' if card else 'player_comparison',
                'scope': scope, 'records': records, 'queries': [source], 'failed_metrics': failures,
                'unresolved': unresolved, 'ready_for_script': not unresolved and bool(shared),
                'coverage': 'Líderes publicados hasta la jornada 29. Usa el nombre publicado y, si hace falta, el club entre paréntesis.'}
        return ToolResult(success=True, data=data, cost_usd=0, from_cache=False)
