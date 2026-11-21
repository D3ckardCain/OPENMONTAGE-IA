"""Round-level research for the 2022 men's World Cup using StatsBomb events."""
import json
from collections import Counter
from datetime import datetime, timezone
import urllib.request

from lib.football_statistics import standard_values
from tools.football.official_premier import NoRedirect
from tools.football.uefa_names import normalized

BASE = 'https://raw.githubusercontent.com/statsbomb/open-data/master/data/'
CALENDAR = BASE + 'matches/43/106.json'
ROUNDS = {
    'group': ('Group Stage', 48), 'round_of_16': ('Round of 16', 8),
    'quarterfinal': ('Quarter-finals', 4), 'semifinal': ('Semi-finals', 2),
    'third_place': ('3rd Place Final', 1), 'final': ('Final', 1),
}
PROPERTIES = {
    'round': {'enum': list(ROUNDS)},
    'players': {'type': 'array', 'minItems': 2, 'maxItems': 2, 'items': {
        'type': 'object', 'required': ['name', 'team'], 'additionalProperties': False,
        'properties': {key: {'type': 'string', 'minLength': 1, 'maxLength': 100}
                       for key in ('name', 'team')},
    }},
}


def fetch(url):
    with urllib.request.build_opener(NoRedirect()).open(url, timeout=15) as response:
        raw = response.read(12_000_001)
    if len(raw) > 12_000_000:
        raise ValueError('Respuesta de StatsBomb demasiado grande')
    return json.loads(raw), {'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat()}


def match_players(events, match):
    players, teams = {}, set()
    goals = Counter()

    def enter(player, team):
        return players.setdefault(player['id'], {
            'name': player['name'], 'team': team,
            'statistics': {'matches_played': 1, 'goals': 0, 'shots': 0},
        })

    for event in events:
        if event['period'] not in (1, 2, 3, 4):
            continue
        kind = event['type']['name']
        if kind not in ('Starting XI', 'Substitution', 'Shot', 'Own Goal For'):
            continue
        team = event['team']['name']
        if kind == 'Starting XI':
            lineup = event['tactics']['lineup']
            if len(lineup) != 11 or team in teams:
                raise ValueError('Alineación de partido incompleta o duplicada')
            teams.add(team)
            for item in lineup:
                enter(item['player'], team)
        elif kind == 'Substitution':
            enter(event['substitution']['replacement'], team)
        elif kind == 'Shot':
            stats = players[event['player']['id']]['statistics']
            stats['shots'] += 1
            if event['shot']['outcome']['name'] == 'Goal':
                stats['goals'] += 1
                goals[team] += 1
        elif kind == 'Own Goal For':
            goals[team] += 1
    home, away = (match[side + '_team'][side + '_team_name'] for side in ('home', 'away'))
    if teams != {home, away} or goals[home] != match['home_score'] or goals[away] != match['away_score']:
        raise ValueError('Los eventos no concuerdan con las alineaciones y el marcador')
    return players


def compare(round, players, read=fetch):
    try:
        matches, calendar_source = read(CALENDAR)
        validate_calendar(matches)
        stage, _ = ROUNDS[round]
        wanted = {normalized(player['team']) for player in players}
        scope = {'competition': 'world_cup_2022', 'season': 2022, 'phase': 'final_tournament',
                 'round': round, 'category': 'men'}
        roster, queries = {}, [calendar_source]
        for match in matches:
            teams = {normalized(match[side + '_team'][side + '_team_name']) for side in ('home', 'away')}
            if match['competition_stage']['name'] != stage or not teams.intersection(wanted):
                continue
            url = BASE + f"events/{match['match_id']}.json"
            events, source = read(url)
            queries.append(source)
            for identifier, entry in match_players(events, match).items():
                key = (identifier, normalized(entry['team']))
                if key[1] not in wanted:
                    continue
                row = roster.setdefault(key, {'entity_id': f'statsbomb:{identifier}', 'name': entry['name'],
                                               'team': entry['team'], 'statistics': Counter(), 'sources': []})
                row['statistics'].update(entry['statistics'])
                row['sources'].append(source)
        records, unresolved = [], []
        for subject in players:
            words = set(normalized(subject['name']).split())
            candidates = [row for (_, team), row in roster.items()
                          if team == normalized(subject['team']) and words
                          and words <= set(normalized(row['name']).split())]
            if len(candidates) == 1 and candidates[0] not in records:
                row = candidates[0]
                standard_values(row, {}, row['statistics'], None, calendar_source)
                for metric in row['statistics']:
                    row['standard_statistics'][metric]['match_sources'] = row['sources']
                records.append(row)
            else:
                unresolved.append(subject)
        return {'source': 'StatsBomb', 'type': 'round_player_research', 'scope': scope,
                'records': records, 'unresolved': unresolved, 'queries': queries,
                'coverage': 'Partidos, goles y tiros. Incluye prórroga y excluye la tanda de penaltis.',
                'attribution_url': 'https://github.com/statsbomb/open-data#terms--conditions',
                'export_available': False}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError('No se pudo verificar la ronda de Qatar 2022: ' + str(exc)) from exc


def validate_calendar(matches):
    expected = {stage: count for stage, count in ROUNDS.values()}
    if (len({match['match_id'] for match in matches}) != 64
            or Counter(match['competition_stage']['name'] for match in matches) != expected
            or any(match['competition']['competition_id'] != 43 or match['season']['season_id'] != 106
                   or type(match['match_id']) is not int or match['match_id'] <= 0 or match['match_status'] != 'available' for match in matches)):
        raise ValueError('El calendario de la edición está incompleto o no coincide')
