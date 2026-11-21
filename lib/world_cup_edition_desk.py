"""Build the studio comparison table for the complete Qatar 2022 tournament."""
from lib.football_comparisons import collect
from tools.football.ligamx import ASCompetition

TEAM_LABELS = {
    'Belgium': 'Bélgica', 'Brazil': 'Brasil', 'Cameroon': 'Camerún', 'Canada': 'Canadá',
    'Croatia': 'Croacia', 'Denmark': 'Dinamarca', 'England': 'Inglaterra', 'France': 'Francia',
    'Germany': 'Alemania', 'Iran': 'Irán', 'Japan': 'Japón', 'Mexico': 'México',
    'Morocco': 'Marruecos', 'Netherlands': 'Países Bajos', 'Poland': 'Polonia',
    'Saudi Arabia': 'Arabia Saudí', 'South Korea': 'Corea del Sur', 'Spain': 'España',
    'Switzerland': 'Suiza', 'Tunisia': 'Túnez', 'USA': 'EE.UU', 'Wales': 'Gales',
}


def compare_edition(players):
    tool = ASCompetition()

    def execute(connector, inputs):
        outcome = tool.execute(inputs)
        return {'data': outcome.data, 'success': outcome.success, 'error': outcome.error}

    names = [f"{player['name']} ({TEAM_LABELS.get(player['team'], player['team'])})" for player in players]
    comparison = collect('competition', [{
        'connector': tool.name, 'inputs': {'competition': 'world_cup_2022', 'season': 2022, 'names': names},
    }], execute)
    section = comparison['sections'][0]
    return {'report': section['report'], 'metric_matrix': section['metric_matrix'],
            'display_metrics': section['display_metrics'], 'errors': section['errors'],
            'failed_metrics': (section['report'] or {}).get('failed_metrics', {})}
