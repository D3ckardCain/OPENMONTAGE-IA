"""Read competition-scoped player rankings from AS."""
import re
import urllib.request
from datetime import datetime, timezone

from tools.base_tool import BaseTool, ResourceProfile, ToolResult, ToolRuntime, ToolStability, ToolTier
from tools.football.uefa import DOM
from tools.football.uefa_names import normalized

TOURNAMENTS = {
    ('ligamx', 2025, 'apertura'): 'Liga MX Apertura 2025',
    ('ligamx', 2026, 'clausura'): 'Liga MX - Clausura 2026',
    ('saudi', '2025-2026', 'provider_edition'): 'Liga Saudí 2025/2026',
    ('afcon', 2025, 'provider_edition'): 'Copa África 2025',
    ('gold_cup', 2025, 'provider_edition'): 'Copa Oro 2025',
    ('euro_2024', 2024, 'final_tournament'): 'Eurocopa 2024',
    ('copa_america', 2024, 'provider_edition'): 'Copa América 2024',
}
DEFAULT_TOURNAMENT = ('ligamx', 2025, 'apertura')


def tournament_scope(tournament):
    competition, year, phase = tournament
    return {'competition': competition, 'season': year, 'phase': phase, 'category': 'men'}


RANKINGS = {
    'goals': 'goles', 'assists': 'asistencias-de-gol', 'shots': 'disparos',
    'shots_on_target': 'disparos-a-puerta', 'passes_completed': 'pases-buenos',
    'passes_attempted': 'pases', 'crosses_completed': 'centros-buenos',
    'crosses_attempted': 'centros', 'penalty_goals': 'goles-de-penalti',
    'penalties_taken': 'penaltis-lanzados', 'offsides': 'fueras-de-juego',
    'matches_played': 'partidos-disputados', 'starts': 'partidos-jugados-de-titular',
    'minutes_played': 'minutos-totales-disputados', 'interceptions': 'intercepciones',
    'recoveries': 'recuperaciones-de-posesion', 'fouls_committed': 'faltas-cometidas',
    'fouls_suffered': 'faltas-recibidas', 'yellow_cards': 'tarjetas-amarillas',
    'second_yellow_cards': 'segundas-tarjetas-amarillas', 'red_cards': 'tarjetas-rojas',
    'saves': 'paradas-del-portero', 'goals_conceded': 'goles-encajados',
    'clean_sheets': 'partidos-con-la-porteria-a-cero',
    'penalties_saved': 'penaltis-parados-por-el-portero', 'own_goals': 'goles-en-propia-puerta',
}
def ranking_urls(tournament):
    competition, year, phase = tournament
    slug = {'saudi': 'arabia_saudi', 'afcon': 'copa_africa', 'gold_cup': 'copa_oro_concacaf', 'copa_america': 'copa_america', 'euro_2024': 'eurocopa'}.get(competition, f'mexico_{phase}')
    edition = str(year).replace('-', '_')
    base = f'https://as.com/resultados/futbol/{slug}/{edition}/ranking/jugadores/'
    return {metric: base + slug + '/' for metric, slug in RANKINGS.items()}
DEFAULT_METRICS = ('goals', 'assists', 'shots')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Redirección AS no admitida')


def fetch(url):
    with urllib.request.build_opener(NoRedirect()).open(url, timeout=15) as response:
        body = response.read(3_000_001)
    if len(body) > 3_000_000:
        raise ValueError('Ranking AS demasiado grande')
    return body.decode('utf-8')


def parse(html, metric, tournament=DEFAULT_TOURNAMENT):
    document = DOM()
    document.feed(html)
    canonical = document.root.first('link', rel='canonical')
    heading = document.root.first('h1')
    table = document.root.first('table')
    if (not canonical or canonical.attrs.get('href') != ranking_urls(tournament)[metric] or not heading
            or heading.text() != 'Rankings de jugadores ' + TOURNAMENTS[tournament] or not table):
        raise ValueError('Ranking AS con torneo o métrica inesperados')
    records = {}
    for row in list(table.walk('tr'))[1:]:
        player = row.first('td', **{'class': 'player'})
        club = row.first('td', **{'class': 'team'})
        score = row.first('td', **{'class': 'a_tb_rk'})
        if not player or not player.text() or not club or not club.text() or not score:
            raise ValueError('Fila AS incompleta')
        raw = score.text()
        if not re.fullmatch(r'[0-9]+|[0-9]{1,3}(?:[.,][0-9]{3})+', raw):
            raise ValueError('Valor AS inválido')
        name, team = player.text(), club.text()
        link = player.first('a')
        match = re.fullmatch(r'/resultados/ficha/deportista/[^/]+/([0-9]+)/', link.attrs.get('href', '')) if link else None
        profile = match[1] if match else normalized(name)
        key = (profile, normalized(team))
        if key in records:
            raise ValueError('Jugador y equipo AS duplicados')
        records[key] = (name, team, int(raw.replace('.', '').replace(',', '')))
    if not records:
        raise ValueError('Ranking AS sin jugadores')
    return records


class LigaMX(BaseTool):
    name = 'ligamx_player_stats'
    version = '0.1.0'
    provider = 'as_rankings'
    tier = ToolTier.SOURCE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    capability = 'football_statistics'
    capabilities = ['football_statistics']
    dependencies = []
    idempotency_key_fields = []
    side_effects = ['read_public_ligamx_rankings']
    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=128, vram_mb=0, disk_mb=0, network_required=True)
    install_instructions = 'Consultas HTTPS públicas a AS.'
    input_schema = {
        'type': 'object', 'additionalProperties': False, 'required': ['action', 'season', 'names'],
        'properties': {
            'action': {'enum': ['compare_players', 'collectible_card']},
            'season': {'enum': [2025, 2026]},
            'phase': {'enum': ['apertura', 'clausura']},
            'metrics': {'type': 'array', 'minItems': 1, 'maxItems': 6, 'uniqueItems': True,
                        'items': {'enum': list(RANKINGS)}},
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

        year = inputs['season']
        competition = inputs.get('competition', 'ligamx')
        phase = 'apertura' if year == 2025 else 'clausura'
        tournament = (competition, year, inputs.get('phase', phase) if competition == 'ligamx' else 'final_tournament' if competition == 'euro_2024' else 'provider_edition')
        if tournament not in TOURNAMENTS:
            return ToolResult(success=False, error='Edición no disponible en AS', cost_usd=0, from_cache=False)
        scope = tournament_scope(tournament)
        urls = ranking_urls(tournament)
        roster, queries, failures = {}, [], {}
        for metric in inputs.get('metrics', DEFAULT_METRICS):
            url = urls[metric]
            try:
                rows = parse(fetch(url), metric, tournament)
            except (OSError, ValueError) as exc:
                failures[metric] = str(exc)
                continue
            retrieved = datetime.now(timezone.utc).isoformat()
            queries.append({'url': url, 'metric': metric, 'retrieved_at': retrieved, 'rows': len(rows)})
            for (profile, team), (name, club, value) in rows.items():
                key = f'{profile}:{team}'
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
        data = {'source': 'AS', 'type': 'collectible_card' if card else 'player_comparison',
                'scope': scope, 'records': records, 'queries': queries, 'failed_metrics': failures,
                'unresolved': unresolved, 'shared_metrics': sorted(shared), 'ready_for_script': not failures and not unresolved and bool(shared),
                'coverage': 'Filas publicadas por AS para el torneo solicitado. La ausencia en un ranking queda sin valor.'}
        return ToolResult(success=bool(queries), error=None if queries else 'LIGAMX_QUERY_FAILED' if competition == 'ligamx' else 'AS_QUERY_FAILED',
                          data=data, cost_usd=0, from_cache=False)


class ASCompetition(LigaMX):
    name = 'as_competition_player_stats'
    side_effects = ['read_public_as_rankings']
    input_schema = {
        **LigaMX.input_schema,
        'required': [*LigaMX.input_schema['required'], 'competition'],
        'properties': {
            **{key: value for key, value in LigaMX.input_schema['properties'].items() if key != 'phase'},
            'competition': {'enum': ['saudi', 'afcon', 'gold_cup', 'copa_america', 'euro_2024']},
            'season': {'enum': [2024, 2025, '2025-2026']},
        },
    }
