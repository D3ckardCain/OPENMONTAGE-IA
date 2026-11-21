"""Player statistics from the official MLS 2025 club goalscorer report."""
import re
import urllib.request
from datetime import datetime, timezone

from tools.base_tool import BaseTool, ResourceProfile, ToolResult, ToolRuntime, ToolStability, ToolTier
from tools.football.uefa import DOM
from tools.football.uefa_names import normalized

SOURCE_URL = 'https://es.mlssoccer.com/noticias/estos-son-los-maximos-goleadores-de-cada-equipo-de-mls-en-2025'
SCOPE = {'competition': 'mls', 'season': 2025, 'phase': 'regular_season', 'category': 'men'}
METRICS = {'goals': 'goals', 'assists': 'assists', 'matches_played': 'matches', 'minutes_played': 'min'}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Redirección MLS no admitida')


def fetch():
    request = urllib.request.Request(SOURCE_URL, headers={'Cache-Control': 'no-cache'})
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=25) as response:
        body = response.read(4_000_001)
    if len(body) > 4_000_000:
        raise ValueError('Documento MLS demasiado grande')
    return body.decode('utf-8'), {'url': SOURCE_URL, 'retrieved_at': datetime.now(timezone.utc).isoformat()}


def parse(html):
    parser = DOM()
    parser.feed(html)
    root = parser.root
    heading = root.first('h1')
    body = next((node for node in root.walk('div')
                 if 'oc-c-article__body' in (node.attrs.get('class') or '').split()), None)
    canonical = root.first('link', rel='canonical')
    if (not canonical or canonical.attrs.get('href') != SOURCE_URL or not heading
            or heading.text() != 'Estos son los máximos goleadores de cada equipo de MLS en 2025'
            or not body or 'temporada regular de MLS 2025' not in body.text()):
        raise ValueError('La fuente MLS no acredita la temporada regular de 2025')
    records = []
    player = None
    for node in body.children:
        if isinstance(node, str) or 'body-part' not in (node.attrs.get('class') or '').split():
            continue
        links = [(link.attrs.get('href') or '', link.text()) for link in node.walk('a') if link.text()]
        names = [(path, name) for path, name in links if re.fullmatch(r'/jugadores/[a-z0-9-]+/', path)]
        clubs = [name for path, name in links if re.fullmatch(r'/clubes/[a-z0-9-]+/', path)]
        if names:
            if len(names) != 1 or len(clubs) != 1 or player:
                raise ValueError('Identidad o club MLS ambiguos')
            player = (names[0][0], names[0][1], clubs[0])
            continue
        text = node.text()
        if not text.startswith('ESTADÍSTICAS:'):
            continue
        match = re.fullmatch(r'ESTADÍSTICAS: ([0-9]+) goles?, ([0-9]+) asistencias? en ([0-9]+) partidos? - ([0-9.]+) minutos', text)
        if not player or not match or not re.fullmatch(r'[0-9]+|[0-9]{1,3}(?:\.[0-9]{3})+', match[4]):
            raise ValueError('Fila estadística MLS inválida')
        path, name, club = player
        values = [int(raw.replace('.', '')) for raw in match.groups()]
        records.append((path, name, club, dict(zip(METRICS, values))))
        player = None
    if player or not records or len({row[0] for row in records}) != len(records):
        raise ValueError('Fuente MLS incompleta o con jugadores duplicados')
    return records


class OfficialMLS(BaseTool):
    name = 'official_mls_live'
    version = '0.1.0'
    provider = 'mls_official'
    tier = ToolTier.SOURCE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    capability = 'football_statistics'
    capabilities = ['football_statistics', 'official_live_data']
    dependencies = []
    idempotency_key_fields = []
    side_effects = ['read_public_mls_report']
    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=128, vram_mb=0, disk_mb=0, network_required=True)
    install_instructions = 'Consulta HTTPS a un informe público de MLS. Sin cuenta ni pago.'
    input_schema = {'type': 'object', 'additionalProperties': False, 'required': ['action', 'season', 'names'],
                    'properties': {
                        'action': {'enum': ['compare_players', 'collectible_card']},
                        'season': {'type': 'integer', 'const': 2025},
                        'names': {'type': 'array', 'minItems': 1, 'maxItems': 2,
                                  'items': {'type': 'string', 'minLength': 1, 'maxLength': 150}},
                    }}

    def execute(self, inputs):
        from jsonschema import validate

        try:
            validate(inputs, self.input_schema)
            card = inputs['action'] == 'collectible_card'
            names = [normalized(name) for name in inputs['names']]
            if len(names) != (1 if card else 2) or len(set(names)) != len(names):
                raise ValueError('Indica un nombre para la postal o dos distintos para la comparativa')
            html, source = fetch()
            roster = parse(html)
            scope = dict(SCOPE)
            records, unresolved = [], []
            for name, key in zip(inputs['names'], names):
                matches = [row for row in roster if normalized(row[1]) == key]
                if len(matches) != 1:
                    unresolved.append(name)
                    continue
                player_id, official_name, club, stats = matches[0]
                facts = [{'metric': metric, 'value': value, 'unit': METRICS[metric], 'entity_id': player_id,
                          'scope': scope, 'source_url': source['url'], 'retrieved_at': source['retrieved_at']}
                         for metric, value in stats.items()]
                records.append({'entity_id': player_id, 'identity': {'entity_id': player_id, 'name': official_name},
                                'club': club, 'statistics': stats, 'facts': facts})
            data = {'source': 'MLS', 'type': 'collectible_card' if card else 'player_comparison', 'scope': scope,
                    'records': records, 'queries': [source], 'unresolved': unresolved,
                    'ready_for_script': not unresolved, 'coverage': 'Máximos goleadores por club, temporada regular 2025.'}
            return ToolResult(success=True, data=data, artifacts=[], cost_usd=0, from_cache=False)
        except (OSError, ValueError) as exc:
            return ToolResult(success=False, error='MLS_QUERY_REJECTED: ' + str(exc),
                              data={'fresh_query_failed': True, 'stale_fallback': False}, cost_usd=0, from_cache=False)
