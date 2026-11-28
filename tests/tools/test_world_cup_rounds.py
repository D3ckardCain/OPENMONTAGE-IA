import pytest

from lib.world_cup_rounds import select_research_metrics
from tools.graphics.sports_card import render


def test_round_metrics_preserve_evidence_and_remain_research_only():
    evidence = {'source_url': 'https://example.test/event', 'value': 0}
    report = {
        'type': 'round_player_research', 'source': 'StatsBomb', 'unresolved': [],
        'scope': {'round': 'final'}, 'export_available': False,
        'records': [
            {'name': player, 'team': team, 'standard_statistics': {'goals': evidence}}
            for player, team in [('A', 'Argentina'), ('B', 'France')]
        ],
    }
    selection = select_research_metrics(report, ['goals'])
    assert selection['metrics'] == [{'metric': 'goals', 'values': [evidence, evidence]}]
    assert selection['export_available'] is False
    assert selection['commercial_use_allowed'] is False
    with pytest.raises(ValueError):
        select_research_metrics(report, ['shots'])
    with pytest.raises(ValueError):
        render(report, ['goals'])


def test_openfootball_counts_extra_time_without_shootout_or_own_goals():
    from lib.world_cup_open_goals import parse

    text = """= World Cup 2022 # in Qatar
▪ Quarter-finals
22:00 Netherlands 2-2 a.e.t. (2-2, 1-0), 3-4 pen. Argentina @ Lusail
 (Player A 83', 90+11'; Player B 35'(o.g.) Player C 120'(pen.))
"""
    matches, goals = parse(text)
    assert matches == {'quarterfinal': 1}
    assert goals['quarterfinal'] == {('Netherlands', 'Player A'): 2, ('Argentina', 'Player C'): 1}
