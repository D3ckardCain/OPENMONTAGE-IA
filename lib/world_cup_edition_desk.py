"""Build the studio comparison table for the supported football editions."""
from lib.football_comparisons import collect
from tools.football.brasileirao import COMPETITIONS as CG_COMPETITIONS, ClassificacaoLeague, competition_scope
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
for competition, (_, label, season) in CG_COMPETITIONS.items():
    phase = competition_scope(competition)['phase']
    key = (competition, season, phase)
    EDITIONS[':'.join(map(str, key))] = (key, label)


def edition_options():
    return [{'id': key, 'label': item[1]} for key, item in EDITIONS.items()]


def compare_edition(players, edition=DEFAULT_EDITION):
    (competition, season, phase), _ = EDITIONS[edition]
    args = {'season': season}
    if competition in CG_COMPETITIONS:
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
            'phase_note': ('La fuente publica cifras de la edición sin desglose verificable por fase.'
                           if phase == 'provider_edition' and competition in CG_COMPETITIONS else None)}
