"""Read paged league player statistics from Classificação Geral."""
import re
import subprocess
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlencode, urlsplit

from tools.base_tool import BaseTool, ResourceProfile, ToolResult, ToolRuntime, ToolStability, ToolTier
from tools.football.uefa import DOM
from tools.football.uefa_names import normalized

BASE = 'https://classificacaogeral.com.br/en/jogadores'
COMPETITIONS = {
    'brasil': ('brasileirao', 'Brasileirão Série A 2025', 2025),
    'laliga': ('la-liga', 'La Liga 2025/26', '2025-2026'),
    'premier': ('premier-league', 'Premier League 2025/26', '2025-2026'),
    'serie_a': ('serie-a-italiana', 'Italian Serie A 2025/26', '2025-2026'),
    'ligue1': ('ligue-1', 'Ligue 1 2025/26', '2025-2026'),
    'portugal': ('primeira-liga', 'Primeira Liga 2025/26', '2025-2026'),
    'argentina': ('campeonato-argentino', 'Argentine Primera División 2025', 2025),
    'libertadores': ('libertadores', 'Copa Libertadores 2025', 2025),
    'sudamericana': ('copa-sul-americana', 'Copa Sudamericana 2025', 2025),
}


def competition_scope(competition):
    phase = 'provider_edition' if competition in ('argentina', 'libertadores', 'sudamericana') else 'regular_season'
    return {'competition': competition, 'season': COMPETITIONS[competition][2],
            'phase': phase, 'category': 'men'}


FIELDS = {
    'goals': 'Goals', 'assists': 'Assists', 'matches_played': 'Played',
    'minutes_played': 'Minutes', 'yellow_cards': 'YC', 'second_yellow_cards': 'Second yellow card',
    'red_cards': 'RC', 'goals_per_game': 'Goals/game', 'minutes_per_goal': 'Min/goal',
}
UNITS = {'goals_per_game': 'goals/game', 'minutes_per_goal': 'min/goal', 'minutes_played': 'min'}


def page_url(page, competition='brasil', search=None):
    slug = COMPETITIONS[competition][0]
    url = f'{BASE}/{slug}/2025'
    params = {}
    if search:
        params['q'] = search
    if page > 1:
        params['page'] = page
    return f'{url}?{urlencode(params)}' if params else url


def valid_source(url, competition):
    if not isinstance(url, str):
        return False
    parts = urlsplit(url)
    params = parse_qs(parts.query)
    page = params.get('page', ['1'])[0]
    search = params.get('q', [None])[0]
    return (bool(re.fullmatch(r'[1-9][0-9]{0,2}', page))
            and url == page_url(int(page), competition, search))


def fetch(url):
    try:
        result = subprocess.run(['curl', '--disable', '--fail', '--silent', '--show-error',
                                 '--max-time', '12', '--max-filesize', '1000000', url],
                                capture_output=True, check=True, timeout=14)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise OSError('Falló la descarga de la página de Classificação Geral') from exc
    return result.stdout.decode('utf-8')


def parse(html, page, competition='brasil', search=None):
    parser = DOM()
    parser.feed(html)
    root = parser.root
    canonical = root.first('link', rel='canonical')
    heading = root.first('h1')
    table = root.first('table', **{'class': 'player-statistics'})
    if (not canonical or canonical.attrs.get('href') != page_url(page, competition) or not heading
            or heading.text() != 'Players ' + COMPETITIONS[competition][1]):
        raise ValueError('La página no acredita la competición, temporada y página solicitadas')
    field = root.first('input', name='q')
    if search and (not field or field.attrs.get('value') != search):
        raise ValueError('La página no confirma el filtro solicitado')
    if not table:
        if search and any(node.text() == 'No records found for these filters.' for node in root.walk('h2')):
            return {}, False
        raise ValueError('Página sin tabla estadística')
    next_link = root.first('a', rel='next')
    if next_link:
        expected = urlsplit(page_url(page + 1, competition, search))
        actual = urlsplit(next_link.attrs.get('href', ''))
        if (actual.scheme or actual.netloc or actual.path != expected.path
                or parse_qs(actual.query) != parse_qs(expected.query)):
            raise ValueError('Paginación inesperada')
    records = {}
    for row in list(table.walk('tr'))[1:]:
        identity = row.first('th', scope='row')
        link = identity.first('a') if identity else None
        match = re.fullmatch(r'/en/jogador/([0-9]+)/([\w-]+)', link.attrs.get('href', '')) if link else None
        club = row.first('td', **{'class': 'player-club'})
        if not match or not link.text() or not club or not club.text():
            raise ValueError('Identidad de jugador incompleta o duplicada')
        cells = {cell.attrs.get('data-label'): cell.text() for cell in row.walk('td')}
        stats = {}
        for metric, label in FIELDS.items():
            raw = cells.get(label)
            if raw in (None, '', '-', '—'):
                continue
            pattern = r'(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)'
            if metric in ('goals_per_game', 'minutes_per_goal'):
                pattern += r'(?:\.[0-9]+)?'
            if not re.fullmatch(pattern, raw):
                raise ValueError('Valor estadístico inválido')
            raw = raw.replace(',', '')
            stats[metric] = float(raw) if '.' in raw else int(raw)
        key = (match[1], normalized(club.text()))
        if key in records:
            raise ValueError('Jugador y club duplicados en una página')
        records[key] = (link.text(), match[2].replace('-', ' '), club.text(), stats)
    if not records:
        raise ValueError('Página sin jugadores')
    return records, bool(next_link)


def resolve(roster, names):
    records, unresolved = [], []
    for name in names:
        key = normalized(name)
        matches = [record for entries in roster.values() for record in entries
                   if key in (record['entity_id'], normalized(record['full_name']),
                              normalized(record['identity']['name']),
                              normalized(f"{record['identity']['name']} ({record['club']})"))]
        if len(matches) == 1 and all(row['entity_id'] != matches[0]['entity_id'] for row in records):
            records.append(matches[0])
        else:
            unresolved.append(name)
    return records, unresolved


def collect(roster, rows, scope, source):
    for (entity, _), (name, full_name, club, stats) in rows.items():
        facts = [{'metric': metric, 'value': value, 'unit': UNITS.get(metric, metric),
                  'entity_id': entity, 'scope': scope, 'source_url': source['url'],
                  'retrieved_at': source['retrieved_at']} for metric, value in stats.items()]
        roster.setdefault(entity, []).append({
            'entity_id': entity, 'identity': {'entity_id': entity, 'name': name},
            'full_name': full_name, 'club': club, 'statistics': stats, 'facts': facts,
        })


class Brasileirao(BaseTool):
    name = 'brasileirao_player_stats'
    version = '0.2.0'
    provider = 'classificacao_geral'
    tier = ToolTier.SOURCE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    capability = 'football_statistics'
    capabilities = ['football_statistics']
    dependencies = []
    idempotency_key_fields = []
    side_effects = ['read_public_brasileirao_pages']
    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=128, vram_mb=0, disk_mb=0, network_required=True)
    install_instructions = 'Consulta HTTPS pública a Classificação Geral. Requiere curl en PATH.'
    input_schema = {
        'type': 'object', 'additionalProperties': False, 'required': ['action', 'season', 'names'],
        'properties': {
            'action': {'enum': ['compare_players', 'collectible_card']},
            'season': {'const': 2025},
            'names': {'type': 'array', 'minItems': 1, 'maxItems': 2, 'uniqueItems': True,
                      'items': {'type': 'string', 'minLength': 1, 'maxLength': 150}},
            'start_page': {'type': 'integer', 'minimum': 1, 'maximum': 100},
            'search_by_name': {'type': 'boolean'},
            'max_blocks': {'type': 'integer', 'minimum': 1, 'maximum': 4},
        },
    }

    def execute(self, inputs):
        from jsonschema import ValidationError, validate

        try:
            validate(inputs, self.input_schema)
        except ValidationError as exc:
            return ToolResult(success=False, error=exc.message, cost_usd=0, from_cache=False)
        card = inputs['action'] == 'collectible_card'
        if len(inputs['names']) != (1 if card else 2):
            return ToolResult(success=False, error='Indica un nombre para la postal o dos para comparar',
                              cost_usd=0, from_cache=False)

        queries, failures, roster = [], {}, {}
        competition = inputs.get('competition', 'brasil')
        scope = competition_scope(competition)
        if scope['season'] != inputs['season']:
            return ToolResult(success=False, error='Temporada no admitida para esta competición',
                              cost_usd=0, from_cache=False)
        if inputs.get('search_by_name'):
            return self.search(inputs['names'], scope, card)
        start_page = inputs.get('start_page', 1)
        next_page = start_page
        max_pages = 3 * inputs.get('max_blocks', 2)
        for page in range(start_page, min(start_page + max_pages, 101)):
            url = page_url(page, competition)
            try:
                rows, has_next = parse(fetch(url), page, competition)
            except (ValueError, OSError) as exc:
                failures[page] = str(exc)
                break
            source = {'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(), 'page': page}
            queries.append(source)
            collect(roster, rows, scope, source)
            next_page = page + 1 if has_next else None
            if next_page is None or ((page - start_page + 1) % 3 == 0
                                     and not resolve(roster, inputs['names'])[1]):
                break

        records, unresolved = resolve(roster, inputs['names'])
        shared = set.intersection(*(set(row['statistics']) for row in records)) if records else set()
        data = {'source': 'Classificação Geral', 'type': 'collectible_card' if card else 'player_comparison',
                'scope': scope, 'records': records, 'queries': queries, 'failed_pages': failures,
                'next_page': next_page, 'unresolved': unresolved, 'ready_for_script': not failures and not unresolved and bool(shared),
                'coverage': 'Coincidencias de los bloques consultados, de hasta tres páginas cada uno. Usa el ID, nombre completo o nombre publicado con el club entre paréntesis para resolver coincidencias.'}
        return ToolResult(success=bool(queries), error=None if queries else 'BRASILEIRAO_QUERY_FAILED',
                          data=data, cost_usd=0, from_cache=False)


    def search(self, names, scope, card):
        competition = scope['competition']
        queries, failures, roster = [], {}, {}
        for name in names:
            words = name.split(' (', 1)[0].split()
            if not words or len(words[-1]) > 80 or words[-1].isdecimal():
                failures[name] = 'La búsqueda directa requiere un nombre publicado'
                continue
            term = words[-1]
            url = page_url(1, competition, term)
            try:
                rows, has_next = parse(fetch(url), 1, competition, term)
            except (OSError, ValueError) as exc:
                failures[name] = str(exc)
                continue
            source = {'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(), 'search': term}
            queries.append(source)
            if has_next:
                failures[name] = 'Filtro demasiado amplio. Usa la consulta por páginas.'
                continue
            candidates = {}
            collect(candidates, rows, scope, source)
            matches, _ = resolve(candidates, [name])
            for row in matches:
                key = row['entity_id']
                if not any(other['club'] == row['club'] for other in roster.get(key, [])):
                    roster.setdefault(key, []).append(row)
        records, unresolved = resolve(roster, names)
        shared = set.intersection(*(set(row['statistics']) for row in records)) if records else set()
        data = {'source': 'Classificação Geral', 'type': 'collectible_card' if card else 'player_comparison',
                'scope': scope, 'records': records, 'queries': queries, 'failed_searches': failures,
                'unresolved': unresolved, 'ready_for_script': not failures and not unresolved and bool(shared),
                'coverage': 'Consultas independientes por apellido y coincidencia exacta del nombre publicado.'}
        return ToolResult(success=bool(queries), error=None if queries else 'PLAYER_SEARCH_FAILED',
                          data=data, cost_usd=0, from_cache=False)


class ClassificacaoLeague(Brasileirao):
    name = 'classificacao_league_player_stats'
    version = '0.1.0'
    side_effects = ['read_public_league_player_pages']
    input_schema = {
        **Brasileirao.input_schema,
        'required': [*Brasileirao.input_schema['required'], 'competition'],
        'properties': {
            **Brasileirao.input_schema['properties'],
            'competition': {'enum': list(COMPETITIONS)},
            'season': {'enum': list(dict.fromkeys(row[2] for row in COMPETITIONS.values()))},
        },
    }
