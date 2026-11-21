"""Resolve names within a freshly queried UEFA ranking, without guessing IDs."""
import re
import unicodedata


def normalized(name):
    if not isinstance(name,str) or not 1<=len(name.strip())<=150:raise ValueError('Nombre requerido, máximo 150 caracteres')
    result=' '.join(re.findall(r'[^\W_]+',''.join(c for c in unicodedata.normalize('NFKD',name.casefold()) if not unicodedata.combining(c)),re.UNICODE))
    if not result:raise ValueError('Nombre vacío')
    return result


def resolve(client,competition,edition,names,metrics,phase='TOURNAMENT',*,ranking_query=None):
    if not isinstance(names,list) or not 1<=len(names)<=10:raise ValueError('Indicar entre uno y diez nombres')
    targets=[normalized(n) for n in names]
    report = ranking_query(metrics) if ranking_query else client.ranking(competition,edition,'player',metrics,phase)
    if report.get('paginacion_agotada') is not True:raise ValueError('No se puede resolver identidad con un ranking incompleto')
    records=report.get('registros')
    if not isinstance(records,list):raise ValueError('Ranking no estructurado')
    results=[]
    for name,target in zip(names,targets):
        candidates=[]
        for row in records:
            official=row.get('nombre')
            if not official:continue
            alias=normalized(official)
            if target==alias or (' '+target+' ') in (' '+alias+' '):
                candidates.append(row)
        results.append({'nombre_solicitado':name,'estado':'resolved' if len(candidates)==1 else 'ambiguous' if candidates else 'not_found_in_ranking',
                        'candidatos':candidates,
                        'nombres_oficiales_para_aclarar':list(dict.fromkeys(r['nombre'] for r in candidates)) if len(candidates)>1 else []})
    return {**report,'tipo':'resolucion_por_nombres','registros':results,
            'diagnostico_identidad':{'filas_consultadas':len(records),'filas_con_nombre':sum(bool(r.get('nombre')) for r in records)},
            'poblacion_consultada':'ranking_de_las_metricas_solicitadas',
            'limite_identidad':'Ausencia en este ranking no demuestra ausencia del torneo. Filas múltiples por equipo no se suman ni se resuelven arbitrariamente.'}


def compare(client,competition,edition,names,metrics,phase='TOURNAMENT',*,ranking_query=None):
    if not isinstance(names,list) or len(names)!=2:raise ValueError('Indicar exactamente dos jugadores')
    report=resolve(client,competition,edition,names,metrics,phase,ranking_query=ranking_query)
    if any(row['estado']!='resolved' for row in report['registros']):
        return {**report,'tipo':'comparativa_bloqueada','ready_for_script':False}
    rows=[r['candidatos'][0] for r in report['registros']]
    if rows[0]['id']==rows[1]['id']:raise ValueError('La comparativa requiere jugadores distintos')
    return {**report,'tipo':'comparativa_jugadores','registros':rows,
            'ready_for_script':not any(r.get('metricas_no_disponibles') or any(r.get('estadisticas',{}).get(m) is None for m in metrics) for r in rows)}


def collectible_card(client,competition,edition,names,metrics,phase='TOURNAMENT',*,ranking_query=None):
    if not isinstance(names,list) or len(names)!=1:raise ValueError('La postal requiere exactamente un jugador')
    report=resolve(client,competition,edition,names,metrics,phase,ranking_query=ranking_query)
    result=report['registros'][0]
    if result['estado']!='resolved':
        return {**report,'tipo':'postal_bloqueada','ready_for_script':False}
    row=result['candidatos'][0]
    missing=row.get('metricas_no_disponibles') or [m for m in metrics if row.get('estadisticas',{}).get(m) is None]
    return {**report,'tipo':'postal_jugador','registros':[row],'ready_for_script':not missing,
            'retrato':None,'permiso_retrato':'no_proporcionado','palmares':None,'puntuacion_habilidad':None,'rendered':False}


def complete_standard_report(player_query, report, metrics):
    """Fetch small player-statistic batches after the ranking resolves identities."""
    from tools.football.uefa import Unavailable
    from tools.football.uefa_batches import checked_statistics, metric_batches, split_rejected_batch

    kind = report['tipo']
    if kind == 'resolucion_por_nombres':
        records = [row['candidatos'][0] for row in report['registros'] if row['estado'] == 'resolved']
    elif kind in ('comparativa_jugadores', 'postal_jugador'):
        records = report['registros']
    else:
        return report

    scope_keys = ('competitionId', 'seasonYear', 'phase')
    scope = {key: report['alcance'][key] for key in scope_keys}
    failures = []
    split_batches = 0
    for row in records:
        values = row['estadisticas'] = {metric: row['estadisticas'].get(metric) for metric in metrics}
        sources = row['fuente_por_metrica'] = {}
        remaining = []
        for metric in metrics:
            if values.get(metric) is not None:
                if row.get('fuente_estadisticas'):
                    sources[metric] = row['fuente_estadisticas']
            else:
                values[metric] = None
                remaining.append(metric)
        pending = metric_batches(remaining)
        while pending:
            batch = pending.popleft()
            try:
                detail = player_query(row['id'], batch)
                if any(detail['alcance'][key] != value for key, value in scope.items()):
                    raise Unavailable('UEFA devolvió un lote de otra competición, edición o fase')
                matching = [item for item in detail['registros']
                            if str(item.get('playerId')) == row['id']
                            and str(item.get('teamId')) == row['team_id']]
                if len(matching) != 1:
                    raise Unavailable('UEFA no confirmó una fila del equipo resuelto')
                origin, = detail['consultas']
                if not origin.get('url') or not origin.get('consultado_utc'):
                    raise Unavailable('UEFA no confirmó la procedencia del lote')
                found = checked_statistics(matching[0]['statistics'], batch)
            except (ValueError, OSError, KeyError, TypeError) as exc:
                if split_rejected_batch(pending, batch, exc):
                    split_batches += 1
                    continue
                failures.append({'player_id': row['id'], 'team_id': row['team_id'],
                                 'metrics': batch, 'reason': str(exc)})
                continue
            if origin not in report['consultas']:
                report['consultas'].append(origin)
            for metric, item in found.items():
                value = item['value']
                if value is not None:
                    values[metric] = value
                    sources[metric] = origin
        row['metricas_no_disponibles'] = [metric for metric in metrics if values[metric] is None]
    report['alcance']['metricas'] = metrics
    incomplete = bool(failures) or any(row['metricas_no_disponibles'] for row in records)
    report['standard_query'] = {'status': 'partial' if incomplete else 'complete',
                                'requested_metrics': metrics, 'failed_batches': failures,
                                'split_batches': split_batches}
    if kind != 'resolucion_por_nombres':
        report['ready_for_script'] = not incomplete
    return report
