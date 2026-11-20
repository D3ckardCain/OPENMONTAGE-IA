"""Resolve names within a freshly queried UEFA ranking, without guessing IDs."""
import re
import unicodedata


def normalized(name):
    if not isinstance(name,str) or not 1<=len(name.strip())<=150:raise ValueError('Nombre requerido, máximo 150 caracteres')
    result=' '.join(re.findall(r'[^\W_]+',''.join(c for c in unicodedata.normalize('NFKD',name.casefold()) if not unicodedata.combining(c)),re.UNICODE))
    if not result:raise ValueError('Nombre vacío')
    return result


def resolve(client,competition,edition,names,metrics,phase='TOURNAMENT'):
    if not isinstance(names,list) or not 1<=len(names)<=10:raise ValueError('Indicar entre uno y diez nombres')
    targets=[normalized(n) for n in names]
    report=client.ranking(competition,edition,'player',metrics,phase)
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
                        'candidatos':candidates})
    return {**report,'tipo':'resolucion_por_nombres','registros':results,
            'poblacion_consultada':'ranking_de_las_metricas_solicitadas',
            'limite_identidad':'Ausencia en este ranking no demuestra ausencia del torneo. Filas múltiples por equipo no se suman ni se resuelven arbitrariamente.'}


def compare(client,competition,edition,names,metrics,phase='TOURNAMENT'):
    if not isinstance(names,list) or len(names)!=2:raise ValueError('Indicar exactamente dos jugadores')
    report=resolve(client,competition,edition,names,metrics,phase)
    if any(row['estado']!='resolved' for row in report['registros']):
        return {**report,'tipo':'comparativa_bloqueada','ready_for_script':False}
    rows=[r['candidatos'][0] for r in report['registros']]
    if rows[0]['id']==rows[1]['id']:raise ValueError('La comparativa requiere jugadores distintos')
    return {**report,'tipo':'comparativa_jugadores','registros':rows,
            'ready_for_script':not any(r.get('metricas_no_disponibles') or any(r.get('estadisticas',{}).get(m) is None for m in metrics) for r in rows)}
