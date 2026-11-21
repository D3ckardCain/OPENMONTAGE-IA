"""Build the studio comparison table for the supported football editions."""
from lib.football_comparisons import collect
from tools.football.brasileirao import COMPETITIONS as CG_COMPETITIONS, ClassificacaoLeague, competition_scope
from tools.football.ligamx import ASCompetition, LigaMX, TOURNAMENTS

from tools.football.eredivisie import Eredivisie, SCOPE as EREDIVISIE_SCOPE
from tools.football.official_asian_cup import OfficialAsianCup, SCOPE as ASIAN_SCOPE
from tools.football.official_bundesliga import OfficialBundesliga, SEASON as DFL_SEASON
from tools.football.official_jleague import COMPETITIONS as JLEAGUE_COMPETITIONS, OfficialJLeague
from tools.football.official_mls import OfficialMLS, SCOPE as MLS_SCOPE
from tools.football.official_ofc import OfficialOFC, SCOPE as OFC_SCOPE
from tools.football.official_premier import OfficialPremier, SCOPE as PREMIER_SCOPE

TEAM_LABELS = {
    'Belgium': 'Bélgica', 'Brazil': 'Brasil', 'Cameroon': 'Camerún', 'Canada': 'Canadá',
    'Croatia': 'Croacia', 'Denmark': 'Dinamarca', 'England': 'Inglaterra', 'France': 'Francia',
    'Germany': 'Alemania', 'Iran': 'Irán', 'Japan': 'Japón', 'Mexico': 'México',
    'Morocco': 'Marruecos', 'Netherlands': 'Países Bajos', 'Poland': 'Polonia',
    'Saudi Arabia': 'Arabia Saudí', 'South Korea': 'Corea del Sur', 'Spain': 'España',
    'Switzerland': 'Suiza', 'Tunisia': 'Túnez', 'USA': 'EE.UU', 'Wales': 'Gales',
}


DEFAULT_EDITION = 'world_cup_2022:2022:final_tournament'
EDITIONS = {':'.join(map(str, key)): (key, label) for key, label in TOURNAMENTS.items()
            if key[2] != 'qualifying'}
for competition, (_, label, season) in CG_COMPETITIONS.items():
    phase = competition_scope(competition)['phase']
    key = (competition, season, phase)
    EDITIONS[':'.join(map(str, key))] = (key, label)


STANDALONE_EDITIONS = {
    ('bundesliga', DFL_SEASON, 'regular_season'): ('Bundesliga 2024/25', OfficialBundesliga),
    ('bundesliga_2', DFL_SEASON, 'regular_season'): ('2. Bundesliga 2024/25', OfficialBundesliga),
    (EREDIVISIE_SCOPE['competition'], EREDIVISIE_SCOPE['season'], EREDIVISIE_SCOPE['phase']):
        ('Eredivisie 2025/26', Eredivisie),
    (ASIAN_SCOPE['competition'], ASIAN_SCOPE['season'], ASIAN_SCOPE['phase']):
        ('Copa Asiática Qatar 2023', OfficialAsianCup),
    (OFC_SCOPE['competition'], OFC_SCOPE['season'], OFC_SCOPE['phase']):
        ('Copa de Naciones OFC 2024', OfficialOFC),
    (MLS_SCOPE['competition'], MLS_SCOPE['season'], MLS_SCOPE['phase']):
        ('MLS 2025 · Temporada regular', OfficialMLS),
    (PREMIER_SCOPE['competition'], PREMIER_SCOPE['season'], PREMIER_SCOPE['phase']):
        ('Premier League 2024/25 · hasta jornada 29', OfficialPremier),
}
STANDALONE_EDITIONS.update({
    (competition, 2025, phase): (f'{label} 2025', OfficialJLeague)
    for competition, (label, phase) in JLEAGUE_COMPETITIONS.items()
})
NAME_ONLY = {'bundesliga', 'bundesliga_2', *JLEAGUE_COMPETITIONS}
for key, (label, _) in STANDALONE_EDITIONS.items():
    EDITIONS[':'.join(map(str, key))] = (key, label)


def edition_options():
    return [{'id': key, 'label': item[1], 'team_filter': item[0][0] not in NAME_ONLY}
            for key, item in EDITIONS.items()]


def compare_edition(players, edition=DEFAULT_EDITION):
    (competition, season, phase), _ = EDITIONS[edition]
    args = {'season': season}
    if (competition, season, phase) in STANDALONE_EDITIONS:
        tool = STANDALONE_EDITIONS[(competition, season, phase)][1]()
        if isinstance(tool, (OfficialBundesliga, OfficialJLeague)):
            args['competition'] = competition
    elif competition in CG_COMPETITIONS:
        tool = ClassificacaoLeague()
        args.update(competition=competition, search_by_name=True)
    elif competition == 'ligamx':
        tool = LigaMX()
        args['phase'] = phase
    else:
        tool = ASCompetition()
        args['competition'] = competition

    def execute(connector, inputs):
        outcome = tool.execute(inputs)
        if inputs.get('search_by_name') and not (outcome.data or {}).get('ready_for_script'):
            outcome = tool.execute(dict(inputs, search_by_name=False))
        return {'data': outcome.data, 'success': outcome.success, 'error': outcome.error}

    names = []
    for player in players:
        team = player.get('team', '').strip()
        if team and competition in NAME_ONLY:
            raise ValueError('Esta fuente identifica por el nombre publicado')
        if edition == DEFAULT_EDITION:
            team = TEAM_LABELS.get(team, team)
        name = player['name'].strip()
        if not name:
            raise ValueError('Indica el nombre de ambos jugadores')
        names.append(f'{name} ({team})' if team else name)
    args['names'] = names
    comparison = collect('competition', [{
        'connector': tool.name, 'inputs': args,
    }], execute)
    section = comparison['sections'][0]
    return {'report': section['report'], 'metric_matrix': section['metric_matrix'],
            'display_metrics': section['display_metrics'], 'errors': section['errors'],
            'failed_metrics': (section['report'] or {}).get('failed_metrics', {}),
            'coverage_note': (section['report'] or {}).get('coverage'),
            'phase_note': ('La fuente publica cifras de la edición sin desglose verificable por fase.'
                           if phase == 'provider_edition' and competition in CG_COMPETITIONS else None)}
