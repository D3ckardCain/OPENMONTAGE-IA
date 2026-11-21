"""Read separate Eredivisie 2025/26 rankings from Voetbal International."""
import re
import urllib.request
from datetime import datetime, timezone

from tools.base_tool import BaseTool, ResourceProfile, ToolResult, ToolRuntime, ToolStability, ToolTier
from tools.football.uefa import DOM
from tools.football.uefa_names import normalized

BASE = 'https://www.vi.nl/competities/eredivisie/2025-2026/statistieken/'
SCOPE = {'competition': 'eredivisie', 'season': '2025-2026', 'phase': 'provider_edition', 'category': 'men'}
RANKINGS = {'goals': ('topscorers', 'Topscorers'), 'assists': ('assists', 'Assists')}
URLS = {metric: BASE + slug for metric, (slug, _) in RANKINGS.items()}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Redirección VI no admitida')


def fetch(url):
    with urllib.request.build_opener(NoRedirect()).open(url, timeout=15) as response:
        body = response.read(3_000_001)
    if len(body) > 3_000_000:
        raise ValueError('Ranking VI demasiado grande')
    return body.decode('utf-8')


def parse(html, metric):
    document = DOM()
    document.feed(html)
    canonical = document.root.first('link', rel='canonical')
    heading = document.root.first('h1')
    tables = list(document.root.walk('table'))
    if (not canonical or canonical.attrs.get('href') != URLS[metric] or not heading
            or heading.text() != RANKINGS[metric][1] + ' VriendenLoterij Eredivisie 2025-2026'
            or len(tables) != 1):
        raise ValueError('Ranking VI con competición, temporada o métrica inesperada')
    records = {}
    for row in list(tables[0].walk('tr'))[1:]:
        if not row.children:
            continue
        name = row.first('td', **{'data-column': 'name'})
        link = name.first('a') if name else None
        club_cell = row.first('td', **{'data-column': 'club'})
        club = club_cell.first('img') if club_cell else None
        score = row.first('td', **{'data-column': 'score'})
        key = link.attrs.get('href', '') if link else ''
        if (not re.fullmatch(r'/spelers/[a-z0-9-]+', key) or not link.text()
                or not club or not club.attrs.get('alt') or not score
                or not re.fullmatch(r'[0-9]+', score.text())):
            raise ValueError('Fila VI incompleta o duplicada')
        row_key = (key, club.attrs['alt'])
        if row_key in records:
            raise ValueError('Jugador y club VI duplicados')
        records[row_key] = (link.text(), int(score.text()))
    if not records:
        raise ValueError('Ranking VI sin jugadores')
    return records


class Eredivisie(BaseTool):
    name = 'eredivisie_player_stats'
    version = '0.1.0'
    provider = 'voetbal_international'
    tier = ToolTier.SOURCE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    capability = 'football_statistics'
    capabilities = ['football_statistics']
    dependencies = []
    idempotency_key_fields = []
    side_effects = ['read_public_eredivisie_rankings']
    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=128, vram_mb=0, disk_mb=0, network_required=True)
    install_instructions = 'Consultas HTTPS públicas a Voetbal International.'
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
        except (ValidationError, ValueError) as exc:
            return ToolResult(success=False, error=str(exc), cost_usd=0, from_cache=False)

        scope = dict(SCOPE)
        roster, queries, failures = {}, [], {}
        for metric, url in URLS.items():
            try:
                rows = parse(fetch(url), metric)
            except (OSError, ValueError) as exc:
                failures[metric] = str(exc)
                continue
            retrieved = datetime.now(timezone.utc).isoformat()
            queries.append({'url': url, 'metric': metric, 'retrieved_at': retrieved})
            for (profile, club), (name, value) in rows.items():
                key = f'{profile}:{club}'
                entry = roster.setdefault(key, {'entity_id': key, 'identity': {'entity_id': key, 'name': name},
                                                'club': club, 'profile': profile, 'statistics': {}, 'facts': []})
                entry['statistics'][metric] = value
                entry['facts'].append({'metric': metric, 'value': value, 'unit': metric, 'entity_id': key, 'scope': scope,
                                       'source_url': url, 'retrieved_at': retrieved})

        records, unresolved = [], []
        for name in inputs['names']:
            matches = [entry for entry in roster.values()
                       if name == entry['profile'] or normalized(name) in (
                           normalized(entry['identity']['name']),
                           normalized(f"{entry['identity']['name']} ({entry['club']})"))]
            if len(matches) == 1 and all(row['profile'] != matches[0]['profile'] for row in records):
                records.append(matches[0])
            else:
                unresolved.append(name)
        shared = set.intersection(*(set(entry['statistics']) for entry in records)) if records else set()
        data = {'source': 'Voetbal International', 'type': 'collectible_card' if card else 'player_comparison',
                'scope': scope, 'records': records, 'queries': queries, 'failed_metrics': failures,
                'unresolved': unresolved, 'ready_for_script': not failures and not unresolved and bool(shared),
                'coverage': 'Rankings de goles y asistencias publicados por VI. Las ausencias se conservan sin valor.'}
        return ToolResult(success=bool(queries), error=None if queries else 'EREDIVISIE_QUERY_FAILED',
                          data=data, cost_usd=0, from_cache=False)
