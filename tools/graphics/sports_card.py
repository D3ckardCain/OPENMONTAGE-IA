"""Local SVG layouts from sourced FIFA reports; no model, network or portraits."""
from html import escape
import json
import math
from pathlib import Path
from tools.base_tool import BaseTool, ToolResult, ToolTier, ToolRuntime, ToolStability, ResourceProfile

_LABELS={'Goals':'Goles','Assists':'Asistencias','MatchesPlayed':'Partidos','TimePlayed':'Tiempo jugado'}


def render(report):
    if report.get('source')!='FIFA' or report.get('ready_for_script') is not True:
        raise ValueError('Se requiere un informe FIFA resuelto y sin métricas ausentes')
    kind=report.get('type'); records=report.get('records',[])
    count={'collectible_card':1,'player_comparison':2}.get(kind)
    if count is None or len(records)!=count: raise ValueError('Informe de postal o comparativa inválido')
    queries=report.get('queries')
    if not isinstance(queries,list) or not queries: raise ValueError('Faltan fuentes')
    scope=report.get('scope',{})
    if not scope.get('season_id') or not scope.get('competition_id'): raise ValueError('Falta alcance')
    panels=[]
    for record in records:
        identity=record.get('identity',{})
        if not identity.get('name') or not identity.get('fdh_player_id'): raise ValueError('Falta identidad oficial')
        if kind=='collectible_card':facts=record.get('facts',[])
        else:
            facts=[{'metric':k,**v,'entity_id':record.get('entity_id'),'scope':scope,
                    'source_url':queries[-1].get('url'),'retrieved_at':queries[-1].get('retrieved_at')}
                   for k,v in record.get('statistics',{}).items()]
        if not 1<=len(facts)<=6: raise ValueError('Selecciona entre una y seis métricas para esta plantilla')
        seen=set()
        for fact in facts:
            value=fact.get('value');url=fact.get('source_url','')
            if type(value) not in (int,float) or not math.isfinite(value):raise ValueError('Cifra ausente o inválida')
            if not isinstance(fact.get('metric'),str) or fact['metric'] in seen:raise ValueError('Métrica inválida o repetida')
            seen.add(fact['metric'])
            if fact.get('entity_id')!=identity['fdh_player_id'] or fact.get('scope')!=scope:raise ValueError('Cifra de otro jugador o alcance')
            if not url.startswith('https://fdh-api.fifa.com/') or not fact.get('retrieved_at'):raise ValueError('Falta procedencia de la cifra')
            if not any(q.get('url')==url and q.get('retrieved_at')==fact['retrieved_at'] for q in queries):raise ValueError('Fuente ajena al expediente')
        panels.append((identity,facts))
    if count==2 and [f['metric'] for f in panels[0][1]]!=[f['metric'] for f in panels[1][1]]:
        raise ValueError('Las métricas comparadas deben coincidir')
    def text(x,y,value,size=28,color='#e6edf3'):
        value=str(value)
        if len(value)>100:raise ValueError('Texto demasiado largo para la plantilla')
        return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-family="sans-serif">{escape(value)}</text>'
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350" viewBox="0 0 1080 1350">',
           '<metadata>'+escape(json.dumps(report,ensure_ascii=False))+'</metadata>',
           '<rect width="1080" height="1350" fill="#0d1117"/>',
           text(54,82,'FÚTBOL · '+('COMPARATIVA' if count==2 else 'POSTAL DE ESTADÍSTICAS'),30,'#58a6ff'),
           text(54,130,'Competición FIFA '+str(scope['competition_id'])+' · Edición '+str(scope['season_id']),24)]
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
        parts.append(text(x+26,405,'ID FIFA '+identity['player_id'],21,'#8b949e'))
        for n,fact in enumerate(facts):
            y=490+n*105
            parts.append(text(x+26,y,_LABELS.get(fact['metric'],fact['metric']),22,'#8b949e'))
            parts.append(text(x+26,y+49,fact['value'],42))
    parts += [text(54,1232,'Fuente: FIFA · Consulta '+str(queries[-1]['retrieved_at'])[:10],23),
              text(54,1270,'Datos de esta edición. Sin puntuaciones de habilidad inventadas.',20,'#8b949e'),'</svg>']
    return ''.join(parts)


class SportsCard(BaseTool):
    name='sports_card_svg'
    version='0.1.0'
    provider='local'
    tier=ToolTier.CORE
    runtime=ToolRuntime.LOCAL
    stability=ToolStability.EXPERIMENTAL
    capability='sports_card_design'
    capabilities=['sports_card_design']
    dependencies=[]
    install_instructions='SVG local, biblioteca estándar Python; sin modelos ni red.'
    resource_profile=ResourceProfile(cpu_cores=1,ram_mb=128,vram_mb=0,disk_mb=1,network_required=False)
    input_schema={'type':'object','required':['report','output_path'],'additionalProperties':False,'properties':{
        'report':{'type':'object'},'output_path':{'type':'string','minLength':1}}}
    def execute(self,inputs):
        from jsonschema import validate
        try:
            validate(inputs,self.input_schema)
            path=Path(inputs['output_path'])
            if path.suffix.lower()!='.svg':raise ValueError('La salida debe ser SVG')
            svg=render(inputs['report'])
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(svg,encoding='utf-8')
            return ToolResult(success=True,data={'output_path':str(path),'format':'svg','video_rendered':False},artifacts=[str(path)],cost_usd=0)
        except Exception as exc:return ToolResult(success=False,error='SPORTS_CARD_REJECTED: '+str(exc),cost_usd=0)
