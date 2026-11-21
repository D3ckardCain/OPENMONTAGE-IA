"""Read the AFC's published Asian Cup Qatar 2023 player leaderboards."""
import re

from tools.football.official_premier import OfficialPremier, fetch
from tools.football.uefa import DOM
from tools.football.uefa_names import normalized

URL = 'https://www.the-afc.com/en/national/afc_asian_cup/news/afc_asian_cup_qatar_2023_the_stats_leaders.html'
SCOPE = {'competition': 'asian_cup', 'season': 2023, 'phase': 'final_tournament', 'category': 'men'}
SECTIONS = {
    'Goals': 'goals', 'Assists': 'assists', 'Chances Created': 'chances_created',
    'Clearances': 'clearances', 'Duels Won': 'duels_won',
    'Shooting Conversion Rate (minimum 10 shots)': 'shot_conversion_rate',
    'Saves': 'saves', 'Passing Accuracy (minimum 200 passes)': 'pass_accuracy',
    'Interceptions': 'interceptions', 'Dribbles Completed': 'dribbles_completed',
}
UNITS = {'pass_accuracy': '%', 'shot_conversion_rate': '%'}


def parse(html):
    document = DOM()
    document.feed(html)
    canonical = document.root.first('link', rel='canonical')
    heading = document.root.first('h1')
    if (not canonical or canonical.attrs.get('href') != URL or not heading
            or heading.text() != 'AFC Asian Cup Qatar 2023™: The Stats Leaders'):
        raise ValueError('Competición o edición AFC inesperada')
    rankings, seen, current = {}, set(), None
    for node in document.root.walk('div'):
        if 'article-child-content' not in (node.attrs.get('class') or '').split():
            continue
        content = next((block for block in node.walk('div')
                        if 'content-text-mapper' in (block.attrs.get('class') or '').split()), None)
        if not content:
            continue
        label = content.first('strong')
        if label:
            current = SECTIONS.get(label.text())
            continue
        if not current or not re.match(r'[0-9]+\. ', content.text()):
            continue
        if current in seen:
            raise ValueError('Ranking AFC duplicado')
        seen.add(current)
        rows = {}
        for line in re.split(r' (?=[0-9]+\. )', content.text()):
            match = re.fullmatch(r'[0-9]+\. (.+?), (.+?) [–-] ([0-9]+(?:\.[0-9]+)?)(%?)', line)
            if not match or bool(match[4]) != (current in UNITS):
                rows = {}
                break
            name, team, raw, _ = match.groups()
            value = float(raw) if current in UNITS else int(raw) if raw.isdecimal() else None
            key = f'{normalized(name)}:{normalized(team)}'
            if value is None or key in rows or (current in UNITS and value > 100):
                rows = {}
                break
            rows[key] = (name, team, value)
        if rows:
            rankings[current] = rows
        current = None
    return rankings, sorted(set(SECTIONS.values()) - rankings.keys())


class OfficialAsianCup(OfficialPremier):
    name = 'official_asian_cup_live'
    provider = 'afc_official'
    side_effects = ['read_public_afc_leaders']
    install_instructions = 'Consulta HTTPS al informe oficial de líderes de la AFC.'
    input_schema = {
        **OfficialPremier.input_schema,
        'properties': {**OfficialPremier.input_schema['properties'], 'season': {'const': 2023}},
    }
    report_scope = SCOPE
    report_url = URL
    report_source = 'AFC'
    report_units = UNITS
    report_coverage = 'Líderes publicados para Qatar 2023. Conversión con mínimo 10 tiros y precisión con mínimo 200 pases.'

    def read_rankings(self):
        return parse(fetch(URL))
