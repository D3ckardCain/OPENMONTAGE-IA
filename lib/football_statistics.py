"""Project official football results onto the common player-statistics fields."""
from lib.sports_sources import FOOTBALL_STANDARD_METRICS

# Explicit equivalences only. In particular, do not infer minutes from an
# undocumented time unit or translate a provider's xG model into another's.
UEFA_NAMES = {
    'matches_appearance': 'matches_played',
    'goals': 'goals', 'assists': 'assists', 'attempts': 'shots',
    'attempts_on_target': 'shots_on_target', 'attempts_off_target': 'shots_off_target',
    'attempts_blocked': 'shots_blocked', 'offsides': 'offsides',
    'penalty_scored': 'penalty_goals', 'penalty_miss': 'penalties_missed',
    'passes_long_attempted': 'long_balls_attempted', 'passes_long_completed': 'long_balls_completed',
    'dribbling_successful': 'dribbles_completed',
    'passes_attempted': 'passes_attempted', 'passes_completed': 'passes_completed',
    'cross_attempted': 'crosses_attempted', 'cross_completed': 'crosses_completed',
    'aerialduel': 'aerial_duels_won', 'aerialduel_total': 'aerial_duels_contested',
    'recovered_ball': 'recoveries', 'tackles_won': 'tackles_won',
    'clearance_completed': 'clearances', 'blocked': 'blocks',
    'clean_sheet': 'clean_sheets', 'goals_conceded': 'goals_conceded', 'saves': 'saves',
    'saves_on_penalty': 'penalties_saved',
    'fouls_committed': 'fouls_committed', 'fouls_suffered': 'fouls_suffered',
    'yellow_cards': 'yellow_cards', 'red_cards': 'red_cards', 'top_speed': 'top_speed',
    'distance_covered': 'distance_covered', 'sprints': 'sprints',
}
FIFA_NAMES = {'Goals': 'goals', 'Assists': 'assists', 'MatchesPlayed': 'matches_played'}


def standard_values(row, facts, values, names, source):
    fields = dict.fromkeys(FOOTBALL_STANDARD_METRICS)
    for original, raw in values.items():
        metric = names.get(original) if names is not None else original
        if metric not in fields:
            continue
        value = raw.get('value') if isinstance(raw, dict) else raw
        if value is None:
            continue
        fact = facts.get(original, {})
        url = fact.get('source_url') or source.get('url')
        timestamp = fact.get('retrieved_at') or source.get('retrieved_at') or source.get('consultado_utc')
        if url and timestamp:
            fields[metric] = {
                'value': value,
                'source_metric': original,
                'source_url': url,
                'retrieved_at': timestamp,
                'unit': fact.get('unit') or (raw.get('unit') if isinstance(raw, dict) else None),
            }
            if fact.get('provider_definition'):
                fields[metric]['provider_definition'] = fact['provider_definition']
    row['standard_statistics'] = fields


def normalize_uefa_row(row, values, source):
    by_metric = row.get('fuente_por_metrica', {})
    facts = {metric: {'source_url': origin['url'], 'retrieved_at': origin['consultado_utc']}
             for metric, origin in by_metric.items()}
    standard_values(row, facts, values, UEFA_NAMES,
                    {} if 'fuente_por_metrica' in row else source)


def add_standard_statistics(report):
    """Keep the original report and source-specific metrics for existing exporters."""
    source = report.get('source') or report.get('fuente')
    player_ranking = (report.get('tipo') == 'ranking'
                      and report.get('alcance', {}).get('entidad') == 'player')
    if source == 'UEFA' and (player_ranking or report.get('tipo') in ('comparativa_jugadores', 'postal_jugador')):
        for row in report['registros']:
            normalize_uefa_row(row, row['estadisticas'], row.get('fuente_estadisticas') or {})
    elif source == 'UEFA':
        if 'desglose_por_temporada_equipo' in report:
            rows = report['desglose_por_temporada_equipo']
            provenance = report
        elif report.get('tipo') == 'estadisticas_jugador_por_equipo_sin_sumar':
            rows = report['registros']
            provenance = report['consultas'][0]
        else:
            return report
        for row in rows:
            values = {item['name']: item for item in row.get('statistics', [])
                      if isinstance(item, dict) and 'name' in item}
            normalize_uefa_row(row, values, provenance)
    elif source in ('FIFA', 'J.League', 'MLS', 'DFL') and report.get('type') in (
            'player_statistics', 'player_comparison', 'collectible_card'):
        for row in report['records']:
            facts = {fact['metric']: fact for fact in row.get('facts', [])}
            values = row.get('statistics', facts)
            names = FIFA_NAMES if source == 'FIFA' else None
            # FIFA's final query is the verified season statistics feed.
            provenance = report['queries'][-1] if source == 'FIFA' and report.get('queries') else {}
            standard_values(row, facts, values, names, provenance)
    return report
