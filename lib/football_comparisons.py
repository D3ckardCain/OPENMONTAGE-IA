"""Collect football comparison evidence before a human selects display metrics."""
from copy import deepcopy

from jsonschema import ValidationError

from lib.football_statistics import add_standard_statistics
from lib.sports_sources import FOOTBALL_METRIC_GROUPS, FOOTBALL_METRIC_LABELS_ES, FOOTBALL_STANDARD_METRICS
from tools.football.ligamx import RANKINGS
from tools.football.official_jleague import METRICS as JLEAGUE_METRICS
from tools.graphics.sports_card import render, uefa_report

CONNECTORS = (
    'official_uefa_live', 'official_fifa_live', 'official_jleague_live',
    'official_mls_live', 'official_bundesliga_live', 'official_premier_live',
    'brasileirao_player_stats', 'classificacao_league_player_stats',
    'eredivisie_player_stats', 'ligamx_player_stats', 'as_competition_player_stats',
    'official_asian_cup_live', 'official_ofc_nations_cup_live',
)
AS_CONNECTORS = ('ligamx_player_stats', 'as_competition_player_stats')
BATCH_CONNECTORS = (*AS_CONNECTORS, 'official_jleague_live')
REQUEST_PROPERTIES = {
    'scope': {'enum': ['competition', 'player']},
    'sources': {'type': 'array', 'minItems': 1, 'maxItems': 12, 'items': {
        'type': 'object', 'required': ['connector', 'inputs'], 'additionalProperties': False,
        'properties': {
            'connector': {'enum': list(CONNECTORS)},
            'inputs': {'type': 'object'},
            'qualification': {'type': 'boolean'},
        },
    }},
}


def requests(connector, inputs):
    """Expand provider selections without changing the common output schema."""
    args = {key: value for key, value in inputs.items() if key != 'metrics'}
    args['action'] = 'compare_players'
    if connector in AS_CONNECTORS:
        metrics = list(RANKINGS)
        return [dict(args, metrics=metrics[i:i + 6]) for i in range(0, len(metrics), 6)]
    if connector == 'official_jleague_live':
        metrics = list(JLEAGUE_METRICS)
        return [dict(args, metrics=metrics[i:i + 6]) for i in range(0, len(metrics), 6)]
    if connector == 'official_uefa_live':
        args['metrics'] = 'all'
    return [args]


def merge_batches(batches):
    compatible = [report for report in batches if len(report['records']) == 2
                  and len({row['entity_id'] for row in report['records']}) == 2]
    if not compatible:
        return None
    merged = deepcopy(compatible[0])
    merged['queries'], merged['failed_metrics'], merged['unresolved'] = [], {}, []
    if 'visible_rows_by_metric' in merged:
        merged['visible_rows_by_metric'] = {}
        merged['visible_rows'] = None
    ids = [row['entity_id'] for row in merged['records']]
    for row in merged['records']:
        row['facts'], row['statistics'] = [], {}
    for report in batches:
        if report['scope'] != merged['scope']:
            raise ValueError('Los lotes no corresponden a la misma edición')
        if report.get('source') != merged.get('source'):
            raise ValueError('Los lotes proceden de fuentes distintas')
        merged['queries'].extend(report['queries'])
        merged['failed_metrics'].update(report['failed_metrics'])
        if 'visible_rows_by_metric' in merged:
            merged['visible_rows_by_metric'].update(report.get('visible_rows_by_metric', {}))
        if report in compatible and [row['entity_id'] for row in report['records']] != ids:
            raise ValueError('Los lotes identificaron jugadores distintos')
        merged['unresolved'].extend(report.get('unresolved', []))
        if report not in compatible:
            if not report.get('unresolved'):
                merged['unresolved'].append({'name': 'Lote incompleto', 'reason': 'incomplete_batch'})
            continue
        by_id = {row['entity_id']: row for row in report['records']}
        for row in merged['records']:
            addition = by_id.get(row['entity_id'])
            if addition:
                row['facts'].extend(addition['facts'])
                row['statistics'].update(addition['statistics'])
    merged['shared_metrics'] = sorted(set.intersection(*(set(row['statistics']) for row in merged['records'])))
    merged['ready_for_script'] = not merged['failed_metrics'] and not merged['unresolved'] and bool(merged['shared_metrics'])
    return add_standard_statistics(merged)


def collect(scope, sources, execute):
    jobs, gaps, sections = [], [], []
    for source in sources:
        connector, inputs = source['connector'], dict(source['inputs'])
        as_euro = connector == 'as_competition_player_stats' and inputs.get('competition') == 'euro_2024'
        explicit_qualifier = (source.get('qualification', False)
                              or inputs.get('phase') in ('QUALIFYING', 'qualifying')
                              or (connector == 'official_uefa_live' and inputs.get('competition') == 'qualifiers'))
        if explicit_qualifier and scope == 'competition':
            raise ValueError('Las eliminatorias solo se solicitan en el historial del jugador')
        if explicit_qualifier and connector != 'official_uefa_live' and not as_euro:
            raise ValueError('La fuente indicada no valida el alcance de eliminatorias')
        if connector == 'official_uefa_live':
            inputs['phase'] = 'QUALIFYING' if explicit_qualifier else 'TOURNAMENT'
        if as_euro and explicit_qualifier:
            inputs['phase'] = 'qualifying'
        jobs.append((connector, inputs, explicit_qualifier))
        if scope == 'player' and connector == 'official_uefa_live' and not explicit_qualifier:
            jobs.append((connector, dict(inputs, phase='QUALIFYING'), True))
        elif scope == 'player' and as_euro and not explicit_qualifier:
            jobs.append((connector, dict(inputs, phase='qualifying'), True))
        elif scope == 'player' and (connector in ('official_fifa_live', 'official_asian_cup_live', 'official_ofc_nations_cup_live')
                                    or inputs.get('competition') in ('world_cup_2022', 'afcon', 'gold_cup', 'copa_america')):
            gaps.append({'connector': connector, 'inputs': inputs,
                         'detail': 'Esta ruta no acredita eliminatorias de la edición.'})

    for connector, inputs, qualification in jobs:
        outcomes = []
        for args in requests(connector, inputs):
            try:
                outcomes.append(execute(connector, args))
            except (ValueError, ValidationError) as exc:
                outcomes.append({'success': False, 'error': str(exc)})
        batches = [item['data'] for item in outcomes if item.get('success') and item.get('data')]
        errors = [item.get('error') for item in outcomes if not item.get('success')]
        try:
            report = merge_batches(batches) if connector in BATCH_CONNECTORS else (batches[0] if batches else None)
        except ValueError as exc:
            errors.append(str(exc))
            report = None
        if report and connector in BATCH_CONNECTORS and errors:
            report['ready_for_script'] = False
        sections.append({'connector': connector, 'inputs': inputs, 'qualification': qualification,
                         'report': report, 'batches': batches, 'errors': errors,
                         'display_metrics': display_metrics(report),
                         'metric_matrix': metric_matrix(report)})
    return {'type': 'football_comparison', 'scope': scope, 'standard_metrics': list(FOOTBALL_STANDARD_METRICS),
            'sections': sections, 'qualification_gaps': gaps}


def display_metrics(report):
    if not report:
        return []
    try:
        export = uefa_report(report, selected=True) if report.get('fuente') == 'UEFA' else report
    except (KeyError, ValueError):
        return []
    records = export.get('records') or []
    if len(records) != 2:
        return []
    if export.get('source') == 'FIFA':
        return sorted(set.intersection(*(
            {metric for metric, stat in row.get('statistics', {}).items() if stat.get('value') is not None}
            for row in records)))
    return sorted(set.intersection(*({fact['metric'] for fact in row.get('facts', [])
                                      if fact.get('value') is not None} for row in records)))


def metric_matrix(report):
    """Report all common fields and preserve source-native alternatives."""
    if not report:
        return []
    report = add_standard_statistics(deepcopy(report))
    records = report.get('records') or report.get('registros') or []
    if len(records) != 2:
        return []
    standards = [row.get('standard_statistics', {}) for row in records]
    common = display_metrics(report)
    matrix = []
    mapped = set()
    groups = {metric: group for group, fields in FOOTBALL_METRIC_GROUPS.items() for metric in fields}
    for metric in FOOTBALL_STANDARD_METRICS:
        values = [row.get(metric) for row in standards]
        keys = {entry['source_metric'] for entry in values if entry}
        mapped.update(keys)
        display_key = next(iter(keys)) if len(keys) == 1 and all(values) else None
        matrix.append({'metric': metric, 'label': FOOTBALL_METRIC_LABELS_ES[metric],
                       'group': groups[metric], 'standard': True, 'values': values,
                       'display_metric': display_key if display_key in common else None})
    try:
        export = uefa_report(report, selected=True) if report.get('fuente') == 'UEFA' else report
    except (KeyError, ValueError):
        return matrix
    native = []
    for row in export.get('records', []):
        facts = {fact['metric']: fact for fact in row.get('facts', []) if fact.get('value') is not None}
        if export.get('source') == 'FIFA' and export.get('queries'):
            source = export['queries'][-1]
            facts = {key: dict(value, source_url=source.get('url'), retrieved_at=source.get('retrieved_at'))
                     for key, value in row.get('statistics', {}).items() if value.get('value') is not None}
        native.append(facts)
    if len(native) == 2:
        for metric in sorted((native[0].keys() | native[1].keys()) - mapped):
            matrix.append({'metric': metric, 'standard': False, 'values': [row.get(metric) for row in native],
                           'display_metric': metric if metric in common else None})
    return matrix


def select(comparison, section, metrics):
    if comparison.get('type') != 'football_comparison' or not 0 <= section < len(comparison.get('sections', [])):
        raise ValueError('Sección de comparativa inexistente')
    if not 1 <= len(metrics) <= 6 or len(set(metrics)) != len(metrics):
        raise ValueError('Selecciona entre una y seis métricas distintas')
    report = comparison['sections'][section]['report']
    if not report:
        raise ValueError('La sección carece de informe verificable')
    render(report, metrics)
    return {'report': report, 'metrics': metrics}
