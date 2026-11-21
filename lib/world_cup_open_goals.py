"""Qatar 2022 round goals from the public-domain OpenFootball match records."""
import re
from collections import Counter
from datetime import datetime, timezone

from lib.football_statistics import add_standard_statistics
from lib.world_cup_rounds import ROUNDS
from tools.football.official_premier import fetch
from tools.football.uefa_names import normalized

BASE = 'https://raw.githubusercontent.com/openfootball/worldcup/master/2022--qatar/'
LABELS = {'group': 'Grupos', 'round_of_16': 'Octavos', 'quarterfinal': 'Cuartos',
          'semifinal': 'Semifinales', 'third_place': 'Tercer puesto', 'final': 'Final'}
URLS = {key: BASE + ('cup.txt' if key == 'group' else 'cup_finals.txt') for key in ROUNDS}
HEADINGS = {'Round of 16': 'round_of_16', 'Quarter-finals': 'quarterfinal',
            'Semi-finals': 'semifinal', 'Match for third place': 'third_place', 'Final': 'final'}
TEAMS = ('Qatar|Ecuador|Senegal|Netherlands|England|Iran|USA|Wales|Argentina|Saudi Arabia|Mexico|Poland|'
         'France|Australia|Denmark|Tunisia|Spain|Costa Rica|Germany|Japan|Belgium|Canada|Morocco|Croatia|'
         'Brazil|Serbia|Switzerland|Cameroon|Portugal|Ghana|Uruguay|South Korea')
SCORE = re.compile(rf'(?:[0-9]{{2}}:[0-9]{{2}}\s+)?({TEAMS})\s+(\d+)-(\d+)'
                   rf'(?:\s+a\.e\.t\.?)?(?:\s+\([\d, -]+\))?(?:, \d+-\d+ pen\.)?\s+({TEAMS})\s+@.+')
GOAL = re.compile(r"\s*(?:(?P<name>[^\d,;()]+?)\s+|,?\s*)(?P<minute>\d+(?:\+\d+)?)'"
                  r"\s*(?P<kind>\((?:pen\.|p|o\.g\.)\))?")


def scorer_counts(line, home, away, first, second):
    if not line.startswith('(') or not line.endswith(')'):
        raise ValueError('Falta el bloque de goleadores')
    sides = line[1:-1].split(';')
    if len(sides) == 1 and first == 0:
        sides.insert(0, '')
    if len(sides) == 1 and second == 0:
        sides.append('')
    if len(sides) != 2:
        raise ValueError('Goleadores sin equipo verificable')
    counts = Counter()
    for team, expected, content in zip((home, away), (first, second), sides):
        name, offset, found = None, 0, 0
        content = content.strip()
        while offset < len(content):
            event = GOAL.match(content, offset)
            if not event:
                raise ValueError('Evento de gol no reconocido: ' + content[offset:])
            name = event['name'].strip() if event['name'] else name
            if not name:
                raise ValueError('Falta el nombre del goleador')
            if event['kind'] != '(o.g.)':
                counts[team, name] += 1
            found += 1
            offset = event.end()
        if found != expected:
            raise ValueError('Los goleadores no concuerdan con el marcador')
    return counts


def parse(text):
    if not text.startswith('= World Cup 2022 '):
        raise ValueError('Edición OpenFootball inesperada')
    stage, matches, goals = None, Counter(), {}
    lines = iter(text.splitlines())
    for raw in lines:
        line = raw.strip()
        if line.startswith('▪ '):
            label = line[2:]
            stage = 'group' if re.fullmatch(r'Group [A-H]', label) else HEADINGS.get(label)
            continue
        score = SCORE.fullmatch(line) if stage else None
        if not score:
            continue
        home, first, second, away = score.groups()
        matches[stage] += 1
        if int(first) + int(second) == 0:
            continue
        block = next(lines, '').strip()
        while block.count('(') > block.count(')'):
            continuation = next(lines, '').strip()
            if not continuation:
                raise ValueError('Bloque de goles incompleto')
            block += ' ' + continuation
        goals.setdefault(stage, Counter()).update(scorer_counts(block, home, away, int(first), int(second)))
    return matches, goals


def compare(round, players):
    url = URLS[round]
    matches, goals = parse(fetch(url))
    expected = {key: count for key, (_, count) in ROUNDS.items() if URLS[key] == url}
    if matches != expected:
        raise ValueError('Calendario incompleto o inesperado')
    scope = {'competition': 'world_cup_2022', 'season': 2022, 'phase': 'final_tournament',
             'round': round, 'category': 'men'}
    query = {'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat()}
    records, unresolved = [], []
    for player in players:
        name = normalized(player['name'])
        candidates = [(team, alias, goals_scored) for (team, alias), goals_scored in goals[round].items()
                      if normalized(team) == normalized(player['team'])
                      and (' ' + name + ' ') in (' ' + normalized(alias) + ' ')]
        if not candidates:
            unresolved.append(player)
            continue
        canonical = max((normalized(row[1]) for row in candidates), key=len)
        if any((' ' + normalized(row[1]) + ' ') not in (' ' + canonical + ' ') for row in candidates):
            unresolved.append(player)
            continue
        entity = normalized(player['team']) + ':' + canonical
        if any(row['entity_id'] == entity for row in records):
            raise ValueError('Se identificó al mismo jugador dos veces')
        value = sum(row[2] for row in candidates)
        records.append({'entity_id': entity, 'identity': {'name': max((row[1] for row in candidates), key=len), 'entity_id': entity},
                        'team': candidates[0][0], 'statistics': {'goals': value},
                        'facts': [{**query, 'metric': 'goals', 'value': value, 'unit': 'goals',
                                   'scope': scope, 'entity_id': entity, 'source_url': url}]})
    return add_standard_statistics({'source': 'OpenFootball', 'type': 'player_comparison', 'scope': scope,
                                    'records': records, 'queries': [query], 'unresolved': unresolved,
                                    'ready_for_script': len(records) == 2 and not unresolved})
