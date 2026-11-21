"""Build the studio comparison table for the supported AS editions."""
from lib.football_comparisons import collect
from tools.football.ligamx import ASCompetition, LigaMX, TOURNAMENTS

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


def edition_options():
    return [{'id': key, 'label': item[1]} for key, item in EDITIONS.items()]


def compare_edition(players, edition=DEFAULT_EDITION):
    (competition, season, phase), _ = EDITIONS[edition]
    tool = LigaMX() if competition == 'ligamx' else ASCompetition()
    args = {'season': season}
    if competition == 'ligamx':
        args['phase'] = phase
    else:
        args['competition'] = competition

    def execute(connector, inputs):
        outcome = tool.execute(inputs)
        return {'data': outcome.data, 'success': outcome.success, 'error': outcome.error}

    names = []
    for player in players:
        team = player.get('team', '').strip()
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
            'failed_metrics': (section['report'] or {}).get('failed_metrics', {})}
