"""Aggregate the official OFC Nations Cup goalscorer lists by stage."""
import re

from tools.football.brasileirao import fetch
from tools.football.official_premier import OfficialPremier
from tools.football.uefa import DOM
from tools.football.uefa_names import normalized

URL = 'https://www.oceaniafootball.com/ofc-mens-nations-cup-2024/'
SCOPE = {'competition': 'ofc_nations_cup', 'season': 2024, 'phase': 'final_tournament', 'category': 'men'}
STAGES = {'Group A': 3, 'Group B': 6, 'Semi-Finals': 2, '3rd Place Play-off': 1, 'Final': 1}
TITLE = "OFC Men's Nations Cup 2024"


def parse(html):
    document = DOM()
    document.feed(html)
    canonical = document.root.first('link', rel='canonical')
    heading = document.root.first('h1')
    if not canonical or canonical.attrs.get('href') != URL or not heading or heading.text() != TITLE.replace("'", '’'):
        raise ValueError('Edición OFC inesperada')
    stage, stages = None, {}
    for node in document.root.walk():
        if node.tag == 'h1' and node.attrs.get('class') == 'comet-schedule-title':
            stage = node.text().removeprefix(TITLE + ' - ')
            if stage not in STAGES or stage in stages:
                raise ValueError('Fase OFC inválida o repetida')
            stages[stage] = {}
        if node.tag != 'table' or stage is None:
            continue
        first = node.first('th')
        if not first:
            continue
        category = 'scores' if first.text().startswith('Match Day ') else 'players' if re.fullmatch(r'[0-9]+ Goals?', first.text()) else None
        if not category:
            continue
        if category in stages[stage]:
            raise ValueError('Tabla OFC duplicada')
        stages[stage][category] = list(node.walk('tr'))
    if set(stages) != set(STAGES):
        raise ValueError('Faltan fases OFC')
    goals = {}
    for stage, tables in stages.items():
        if set(tables) != {'scores', 'players'}:
            raise ValueError('Faltan tablas OFC')
        scores = [cell.text() for row in tables['scores'] for cell in row.walk('td')
                  if re.fullmatch(r'[0-9]+ : [0-9]+', cell.text())]
        if len(scores) != STAGES[stage]:
            raise ValueError('Cantidad de partidos OFC inesperada')
        expected = sum(int(value) for score in scores for value in score.split(' : '))
        count, subtotal, seen = None, 0, set()
        for row in tables['players']:
            header = row.first('th')
            if header:
                match = re.fullmatch(r'([1-9][0-9]*) Goals?', header.text())
                if not match:
                    raise ValueError('Cabecera de goleadores OFC inválida')
                count = int(match[1])
                continue
            cell = row.first('td')
            if not count or not cell:
                raise ValueError('Fila de goleadores OFC inválida')
            for player in cell.text().split(', '):
                match = re.fullmatch(r'(.+) \(([^()]+)\)', player)
                if not match:
                    raise ValueError('Identidad OFC inválida')
                name, team = match.groups()
                key = f'{normalized(name)}:{normalized(team)}'
                if key in seen:
                    raise ValueError('Goleador OFC repetido en una fase')
                seen.add(key)
                subtotal += count
                goals[key] = (name, team, goals.get(key, (None, None, 0))[2] + count)
        if expected - subtotal != (1 if stage in ('Group A', 'Group B') else 0):
            raise ValueError('Goleadores y marcadores OFC no coinciden: ' + stage)
    return {'goals': goals}, []


class OfficialOFC(OfficialPremier):
    name = 'official_ofc_nations_cup_live'
    provider = 'ofc_official'
    side_effects = ['read_public_ofc_goalscorers']
    install_instructions = 'Consulta HTTPS a las tablas oficiales de la OFC. Requiere curl en PATH.'
    input_schema = {
        **OfficialPremier.input_schema,
        'properties': {**OfficialPremier.input_schema['properties'], 'season': {'const': 2024}},
    }
    report_scope = SCOPE
    report_url = URL
    report_source = 'OFC'
    report_units = {}
    report_coverage = 'Goles de grupos, semifinales, tercer puesto y final. La OFC atribuye 44 de los 46 goles del marcador a jugadores en estas tablas. Las ausencias quedan sin cifra.'

    def read_rankings(self):
        return parse(fetch(URL))
