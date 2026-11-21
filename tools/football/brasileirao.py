"""Read paged Brasileirão Série A statistics from Classificação Geral."""
import re
import subprocess
from datetime import datetime, timezone

from tools.base_tool import BaseTool, ResourceProfile, ToolResult, ToolRuntime, ToolStability, ToolTier
from tools.football.uefa import DOM
from tools.football.uefa_names import normalized

URL = 'https://classificacaogeral.com.br/en/jogadores/brasileirao/2025'
SCOPE = {'competition': 'brasil', 'season': 2025, 'phase': 'regular_season', 'category': 'men'}
FIELDS = {
    'goals': 'Goals', 'assists': 'Assists', 'matches_played': 'Played',
    'minutes_played': 'Minutes', 'yellow_cards': 'YC', 'second_yellow_cards': 'Second yellow card',
    'red_cards': 'RC', 'goals_per_game': 'Goals/game', 'minutes_per_goal': 'Min/goal',
}
UNITS = {'goals_per_game': 'goals/game', 'minutes_per_goal': 'min/goal', 'minutes_played': 'min'}


def page_url(page):
    return URL if page == 1 else f'{URL}?page={page}'


def fetch(url):
    try:
        result = subprocess.run(['curl', '--disable', '--fail', '--silent', '--show-error',
                                 '--max-time', '12', '--max-filesize', '1000000', url],
                                capture_output=True, check=True, timeout=14)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise OSError('Falló la descarga de la página del Brasileirão') from exc
    return result.stdout.decode('utf-8')


def parse(html, page):
    parser = DOM()
    parser.feed(html)
    root = parser.root
    canonical = root.first('link', rel='canonical')
    heading = root.first('h1')
    table = root.first('table', **{'class': 'player-statistics'})
    if (not canonical or canonical.attrs.get('href') != page_url(page) or not heading
            or heading.text() != 'Players Brasileirão Série A 2025' or not table):
        raise ValueError('La página no acredita la competición, temporada y página solicitadas')
    next_link = root.first('a', rel='next')
    if next_link and next_link.attrs.get('href') != f'/en/jogadores/brasileirao/2025?page={page + 1}':
        raise ValueError('Paginación inesperada')
    records = {}
    for row in list(table.walk('tr'))[1:]:
        identity = row.first('th', scope='row')
        link = identity.first('a') if identity else None
        match = re.fullmatch(r'/en/jogador/([0-9]+)/([\w-]+)', link.attrs.get('href', '')) if link else None
        club = row.first('td', **{'class': 'player-club'})
        if not match or not link.text() or not club or match[1] in records:
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
        records[match[1]] = (link.text(), match[2].replace('-', ' '), club.text(), stats)
    if not records:
        raise ValueError('Página sin jugadores')
    return records, bool(next_link)


def resolve(roster, names):
    records, unresolved = [], []
    for name in names:
        key = normalized(name)
        matches = [record for entries in roster.values() for record in entries
                   if key in (record['entity_id'], normalized(record['full_name']),
                              normalized(record['identity']['name']))]
        if len(matches) == 1 and matches[0] not in records:
            records.append(matches[0])
        else:
            unresolved.append(name)
    return records, unresolved


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
        scope = dict(SCOPE)
        start_page = inputs.get('start_page', 1)
        next_page = start_page
        max_pages = 3 * inputs.get('max_blocks', 2)
        for page in range(start_page, min(start_page + max_pages, 101)):
            url = page_url(page)
            try:
                rows, has_next = parse(fetch(url), page)
            except (ValueError, OSError) as exc:
                failures[page] = str(exc)
                break
            source = {'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(), 'page': page}
            queries.append(source)
            for entity, (name, full_name, club, stats) in rows.items():
                facts = [{'metric': metric, 'value': value, 'unit': UNITS.get(metric, metric),
                          'entity_id': entity, 'scope': scope, 'source_url': url,
                          'retrieved_at': source['retrieved_at']} for metric, value in stats.items()]
                roster.setdefault(entity, []).append({
                    'entity_id': entity, 'identity': {'entity_id': entity, 'name': name},
                    'full_name': full_name, 'club': club, 'statistics': stats, 'facts': facts,
                })
            next_page = page + 1 if has_next else None
            if next_page is None or ((page - start_page + 1) % 3 == 0
                                     and not resolve(roster, inputs['names'])[1]):
                break

        records, unresolved = resolve(roster, inputs['names'])
        shared = set.intersection(*(set(row['statistics']) for row in records)) if records else set()
        data = {'source': 'Classificação Geral', 'type': 'collectible_card' if card else 'player_comparison',
                'scope': scope, 'records': records, 'queries': queries, 'failed_pages': failures,
                'next_page': next_page, 'unresolved': unresolved, 'ready_for_script': not failures and not unresolved and bool(shared),
                'coverage': 'Coincidencias de los bloques consultados, de hasta tres páginas cada uno. Usa el ID o el nombre completo para resolver homónimos.'}
        return ToolResult(success=bool(queries), error=None if queries else 'BRASILEIRAO_QUERY_FAILED',
                          data=data, cost_usd=0, from_cache=False)
