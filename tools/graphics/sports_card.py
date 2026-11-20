"""Local SVG layouts from sourced FIFA reports; no model, network or portraits."""
from html import escape
import json
import math
import re
from pathlib import Path
from tools.football.official_jleague import COMPETITIONS as JLEAGUE_COMPETITIONS, METRICS as JLEAGUE_METRICS, profile_url, ranking_url
from tools.base_tool import BaseTool, ToolResult, ToolTier, ToolRuntime, ToolStability, ResourceProfile

_LABELS={'rank':'Puesto en el ranking WBA','goals':'Goles','assists':'Asistencias','duels_won':'Duelos ganados','interceptions':'Intercepciones','clean_sheets':'Porterías a cero','yellow_cards':'Tarjetas amarillas','red_cards':'Tarjetas rojas','matches_played':'Partidos jugados','minutes_played':'Minutos jugados','shots':'Tiros','shots_on_target':'Tiros a puerta','homeRuns':'Jonrones','rbi':'Carreras impulsadas','avg':'Promedio de bateo','inningsPitched':'Innings lanzados','era':'Promedio carreras limpias','strikeOuts':'Ponches','gamesPlayed':'Partidos','Goals':'Goles','Assists':'Asistencias','MatchesPlayed':'Partidos','TimePlayed':'Tiempo jugado'}


def uefa_report(report, selected=False):
    if report.get('tipo') not in ('comparativa_jugadores','postal_jugador') or (not selected and report.get('ready_for_script') is not True):
        raise ValueError('Comparativa UEFA bloqueada o no admitida')
    sources=report.get('consultas',[])
    queries=[dict(q,retrieved_at=q.get('consultado_utc')) for q in sources]
    rows=[]
    for row in report.get('registros',[]):
        origin=row.get('fuente_estadisticas')
        if not isinstance(origin,dict) or origin not in sources:
            raise ValueError('Falta la página exacta de procedencia del jugador UEFA')
        rows.append({'entity_id':row['id'],'identity':{'entity_id':row['id'],'name':row['nombre']},
                     'statistics':row['estadisticas'],'statistics_source':dict(origin,retrieved_at=origin.get('consultado_utc'))})
    if report['tipo']=='postal_jugador':
        scope=report.get('alcance',{})
        for row in rows:
            origin=row['statistics_source']
            row['facts']=[{'metric':metric,'value':value,'entity_id':row['entity_id'],'scope':scope,
                           'source_url':origin['url'],'retrieved_at':origin['retrieved_at']}
                          for metric,value in row['statistics'].items()]
    return {'source':'UEFA','type':'collectible_card' if report['tipo']=='postal_jugador' else 'player_comparison','ready_for_script':report.get('ready_for_script'),
            'scope':report.get('alcance',{}),'queries':queries,'records':rows,
            'competition':report.get('competicion'),'original_report':report}


METRIC_SELECTION = {'type': 'array', 'minItems': 1, 'maxItems': 6, 'uniqueItems': True,
                    'items': {'type': 'string', 'minLength': 1, 'maxLength': 100}}


def render(report, metrics=None):
    if report.get('fuente')=='UEFA':report=uefa_report(report, selected=metrics is not None)
    source=report.get('source')
    allow_partial = metrics is not None and source in ('FIFA', 'UEFA', 'J.League')
    if source not in ('FIFA','MLB','UEFA','WBA','J.League') or (not allow_partial and report.get('ready_for_script') is not True):
        raise ValueError('Se requiere un informe deportivo resuelto y sin métricas ausentes')
    kind=report.get('type'); records=report.get('records',[])
    count={'collectible_card':1,'player_comparison':2}.get(kind)
    if count is None or len(records)!=count: raise ValueError('Informe de postal o comparativa inválido')
    queries=report.get('queries')
    if not isinstance(queries,list) or not queries: raise ValueError('Faltan fuentes')
    scope=report.get('scope',{})
    if source=='FIFA' and (not scope.get('season_id') or not scope.get('competition_id')): raise ValueError('Falta alcance')
    if source=='UEFA' and (not scope.get('competitionId') or not scope.get('seasonYear') or not scope.get('phase')):raise ValueError('Falta alcance UEFA explícito')
    if source=='WBA' and (scope.get('category')!='men' or not re.fullmatch(r'[0-9]{4}-(0[1-9]|1[0-2])',str(scope.get('as_of_month',''))) or not scope.get('division') or kind!='collectible_card'):raise ValueError('Alcance WBA no admitido')
    if source=='MLB' and (scope.get('sport_id')!=1 or scope.get('game_type')!='R' or not scope.get('season') or scope.get('group') not in ('hitting','pitching')):raise ValueError('Alcance MLB no admitido')
    if source == 'J.League':
        competition = JLEAGUE_COMPETITIONS.get(scope.get('competition'))
        if (not competition or type(scope.get('season')) is not int or not 1993 <= scope['season'] <= 9999
                or scope.get('phase') != competition[1] or scope.get('category') != 'men'):
            raise ValueError('Alcance J.League no admitido')
    panels=[]
    for record in records:
        identity=record.get('identity',{})
        entity=identity.get('fdh_player_id') if source=='FIFA' else identity.get('entity_id')
        if not identity.get('name') or not entity: raise ValueError('Falta identidad oficial')
        if kind=='collectible_card' or source=='J.League':facts=record.get('facts',[])
        elif source in ('MLB','UEFA'):
            origin=record.get('statistics_source',{})
            facts=[{'metric':k,'value':v,'entity_id':record.get('entity_id'),'scope':scope,'source_url':origin.get('url'),'retrieved_at':origin.get('retrieved_at')} for k,v in record.get('statistics',{}).items()]
        else:
            facts=[{'metric':k,**v,'entity_id':record.get('entity_id'),'scope':scope,
                    'source_url':queries[-1].get('url'),'retrieved_at':queries[-1].get('retrieved_at')}
                   for k,v in record.get('statistics',{}).items()]
        if metrics is not None:
            by_metric = {fact['metric']: fact for fact in facts}
            if len(by_metric) != len(facts) or any(metric not in by_metric for metric in metrics):
                raise ValueError('Falta una métrica seleccionada o figura repetida')
            facts = [by_metric[metric] for metric in metrics]
        if not 1<=len(facts)<=6: raise ValueError('Selecciona entre una y seis métricas para esta plantilla')
        seen=set()
        for fact in facts:
            value=fact.get('value');url=fact.get('source_url','')
            numeric=type(value) in (int,float) and math.isfinite(value)
            original_rate=source in ('MLB','UEFA') and isinstance(value,str) and re.fullmatch(r'-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)',value)
            if source=='WBA' and (fact.get('metric')!='rank' or type(value) is not int or not 1<=value<=15):raise ValueError('Solo puestos WBA del 1 al 15')
            if not (numeric or original_rate):raise ValueError('Cifra ausente o inválida')
            if not isinstance(fact.get('metric'),str) or fact['metric'] in seen:raise ValueError('Métrica inválida o repetida')
            seen.add(fact['metric'])
            if fact.get('entity_id')!=entity or fact.get('scope')!=scope:raise ValueError('Cifra de otro jugador o alcance')
            if source == 'J.League':
                metric = fact['metric']
                if metric not in JLEAGUE_METRICS or type(value) is not int or value < 0:
                    raise ValueError('Cifra J.League inválida')
                allowed = {ranking_url(scope['season'], metric, scope['competition'])}
                if metric == 'goals' and scope['phase'] == 'league':
                    allowed.add(profile_url(entity))
                if url not in allowed:
                    raise ValueError('Cifra o fuente J.League inválida')
            elif not isinstance(url,str) or not url.startswith('https://fdh-api.fifa.com/' if source=='FIFA' else 'https://compstats.uefa.com/' if source=='UEFA' else 'https://www.wbaboxing.com/' if source=='WBA' else 'https://statsapi.mlb.com/') or not fact.get('retrieved_at'):raise ValueError('Falta procedencia de la cifra')
            if not fact.get('retrieved_at') or not any(q.get('url')==url and q.get('retrieved_at')==fact['retrieved_at'] for q in queries):raise ValueError('Fuente ajena al expediente')
        if source=='MLB':
            identity=dict(identity,team_name=[{'Description':(record.get('team') or {}).get('name','Temporada regular MLB')}])
        panels.append((identity,facts))
    if count==2 and [f['metric'] for f in panels[0][1]]!=[f['metric'] for f in panels[1][1]]:
        raise ValueError('Las métricas comparadas deben coincidir')
    def text(x,y,value,size=28,color='#e6edf3'):
        value=str(value)
        if len(value)>100:raise ValueError('Texto demasiado largo para la plantilla')
        return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-family="sans-serif">{escape(value)}</text>'
    evidence = report if metrics is None else dict(report, displayed_metrics=metrics)
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350" viewBox="0 0 1080 1350">',
           '<metadata>'+escape(json.dumps(evidence,ensure_ascii=False))+'</metadata>',
           '<rect width="1080" height="1350" fill="#0d1117"/>',
           text(54,82,('BÉISBOL · ' if source=='MLB' else 'BOXEO · ' if source=='WBA' else 'FÚTBOL · ')+('COMPARATIVA' if count==2 else 'POSTAL DE RANKING' if source=='WBA' else 'POSTAL DE ESTADÍSTICAS'),30,'#58a6ff'),
           text(54,130,next((v['Description'] for v in (scope.get('season_name') or []) if isinstance(v,dict) and v.get('Description')), 'Estadísticas de la edición consultada') if source=='FIFA' else 'WBA · Ranking masculino · '+scope['as_of_month'] if source=='WBA' else 'UEFA · '+str(report.get('competition'))+' · '+str(scope['seasonYear'])+' · '+str(scope['phase']) if source=='UEFA' else competition[0]+' · '+str(scope['season']) if source=='J.League' else 'MLB '+str(scope['season'])+' · Temporada regular · '+('Bateo' if scope['group']=='hitting' else 'Pitcheo'),24)]
    width=972/count
    for index,(identity,facts) in enumerate(panels):
        x=int(54+index*width)
        parts.append(f'<rect x="{x}" y="180" width="{int(width-18)}" height="1000" rx="24" fill="#161b22" stroke="#30363d"/>')
        # Wrap official names into short lines rather than shrinking them illegibly.
        words=identity['name'].split();lines=['']
        for word in words:
            if len(word)>24:raise ValueError('Nombre requiere otra plantilla')
            if len(lines[-1])+len(word)+1>24:lines.append('')
            lines[-1]=(lines[-1]+' '+word).strip()
        if len(lines)>3:raise ValueError('Nombre requiere otra plantilla')
        for n,line in enumerate(lines):parts.append(text(x+26,250+n*45,line,34))
        parts.append(text(x+26,405,next((v['Description'] for v in (identity.get('team_name') or []) if isinstance(v,dict) and v.get('Description')), 'Estadísticas del torneo'),21,'#8b949e'))
        for n,fact in enumerate(facts):
            y=490+n*105
            parts.append(text(x+26,y,_LABELS.get(fact['metric'],fact['metric']),22,'#8b949e'))
            parts.append(text(x+26,y+49,fact['value'],42))
    parts += [text(54,1232,'Fuente: '+source+' · Consulta '+str(queries[-1]['retrieved_at'])[:10],23),
              text(54,1270,'Puesto del mes publicado · No es récord de combates' if source=='WBA' else 'Estadísticas de esta edición · Fuente oficial',20,'#8b949e'),'</svg>']
    return ''.join(parts)


def rasterize(svg, path):
    """Rasterize only our rect/text subset using core Pillow, without SVG plugins."""
    import xml.etree.ElementTree as ET
    from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
    root=ET.fromstring(svg)
    image=Image.new('RGB',(1080,1350),'#0d1117');draw=ImageDraw.Draw(image)
    info=PngImagePlugin.PngInfo()
    for node in root:
        kind=node.tag.rsplit('}',1)[-1]
        if kind=='metadata':
            info.add_text('openmontage_evidence',node.text or '')
        elif kind=='rect':
            x=int(node.get('x',0));y=int(node.get('y',0))
            box=(x,y,x+int(node.get('width')),y+int(node.get('height')))
            draw.rounded_rectangle(box,radius=int(node.get('rx',0)),fill=node.get('fill'),outline=node.get('stroke'))
        elif kind=='text':
            size=int(node.get('font-size'));font=None
            for candidate in ('DejaVuSans.ttf','arial.ttf'):
                try:font=ImageFont.truetype(candidate,size);break
                except OSError:pass
            if font is None:raise ValueError('Se necesita una fuente TrueType DejaVu Sans o Arial para PNG')
            draw.text((int(node.get('x')),int(node.get('y'))),node.text or '',font=font,fill=node.get('fill'),anchor='ls')
        else:raise ValueError('Elemento no soportado por el rasterizador local')
    image.save(path,format='PNG',pnginfo=info)


class SportsCard(BaseTool):
    name='sports_card_svg'
    version='0.3.0'
    provider='local'
    tier=ToolTier.CORE
    runtime=ToolRuntime.LOCAL
    stability=ToolStability.EXPERIMENTAL
    capability='sports_card_design'
    capabilities=['sports_card_design']
    dependencies=[]
    install_instructions='SVG local y PNG mediante Pillow (dependencia principal). PNG necesita Arial o DejaVu Sans; sin modelos ni red.'
    resource_profile=ResourceProfile(cpu_cores=1,ram_mb=128,vram_mb=0,disk_mb=1,network_required=False)
    input_schema={'type':'object','required':['report','output_path'],'additionalProperties':False,'properties':{
        'report':{'type':'object'},'output_path':{'type':'string','minLength':1},
        'metrics':METRIC_SELECTION}}
    def get_info(self):
        from lib.sports_export_requirements import png_requirements
        info=super().get_info()
        info['output_readiness']={'svg':{'available':True,'missing':[]},'png':png_requirements()}
        return info

    def execute(self,inputs):
        from jsonschema import validate
        try:
            validate(inputs,self.input_schema)
            path=Path(inputs['output_path'])
            suffix=path.suffix.lower()
            if suffix not in ('.svg','.png'):raise ValueError('La salida debe ser SVG o PNG')
            svg=render(inputs['report'], inputs.get('metrics'))
            path.parent.mkdir(parents=True,exist_ok=True)
            if suffix=='.svg':path.write_text(svg,encoding='utf-8')
            else:rasterize(svg,path)
            return ToolResult(success=True,data={'output_path':str(path),'format':suffix[1:],'video_rendered':False},artifacts=[str(path)],cost_usd=0)
        except Exception as exc:return ToolResult(success=False,error='SPORTS_CARD_REJECTED: '+str(exc),cost_usd=0)
