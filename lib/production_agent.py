"""Bounded local-agent transport and tool bridge.

The model reads the manifests, delegates editorial work and chooses tools. Python
only transports messages, validates calls, persists checkpoints and owns job state.
There is no hardcoded creative script or silent paid-provider fallback.
"""
from __future__ import annotations
import json
import math
import subprocess
import threading
import time
from pathlib import Path
from urllib.parse import quote
from jsonschema import validate
from lib import production_studio as studio
from lib.checkpoint import get_next_stage, get_latest_checkpoint, write_checkpoint
from lib.pipeline_loader import load_pipeline_readonly
from tools.base_tool import ToolRuntime, ToolTier, ToolStatus

ACTIVE={}
ACTIVE_LOCK=threading.Lock()
ROLES={'research':'Investigador: hechos, fuentes, actualidad y límites de evidencia.',
       'writer':'Guionista: estructura original, títulos, narración y satisfacción.',
       'visual':'Director visual: escenas y recursos adecuados; nada de sustituir movimiento sin aprobación.',
       'audio':'Director de audio: voz, música autorizada y adaptación cultural por idioma.',
       'editor':'Editor: montaje, composición, exportación y correspondencia entre imagen y narración.',
       'reviewer':'Revisor: evidencia, originalidad, continuidad, derechos y requisitos del manifiesto.'}


def descriptor(name,description,properties=None,required=None):
    return {'type':'function','function':{'name':name,'description':description,'parameters':{
        'type':'object','additionalProperties':False,'properties':properties or {},'required':required or []}}}

from lib.football_comparisons import REQUEST_PROPERTIES as FOOTBALL_COMPARISON_PROPERTIES
from lib.world_cup_rounds import PROPERTIES as WORLD_CUP_ROUND_PROPERTIES

TOOLS=[
 descriptor('sports_sources','Localiza fuentes oficiales por deporte y región para comparativas y tarjetas. No contiene estadísticas ni certifica conectores pendientes.',{'sport':{'enum':['football','boxing','baseball']},'region':{'enum':['world','europe','americas','asia','africa','arab','oceania']}}),
 descriptor('football_comparison','Reúne todas las métricas publicadas de dos jugadores por fuente y edición. En modo player consulta las eliminatorias verificables en secciones aparte. Presenta los datos y espera la selección explícita del usuario antes de exportar.',FOOTBALL_COMPARISON_PROPERTIES,['scope','sources']),
 descriptor('select_football_comparison_metrics','Valida la selección explícita del usuario y prepara los datos para sports_card_svg o sports_card_video.',{'comparison':{'type':'object'},'section':{'type':'integer','minimum':0},'metrics':{'type':'array','minItems':1,'maxItems':6,'uniqueItems':True,'items':{'type':'string'}}},['comparison','section','metrics']),
 descriptor('football_saved_selection','Lee la última selección deportiva guardada. Solicita include_report=true para obtener el informe completo listo para sports_card_svg o sports_card_video; puede ser grande. La vista previa no autoriza publicar.',{'include_report':{'type':'boolean'}}),
 descriptor('world_cup_2022_round','Consulta por ronda de Qatar 2022 los partidos jugados, goles y tiros de dos jugadores con datos de StatsBomb para investigación. Sus términos excluyen uso comercial y este informe queda fuera de los exportadores.',WORLD_CUP_ROUND_PROPERTIES,['round','players']),
 descriptor('world_cup_2022_round_goals','Compara goles acreditados en una ronda de Qatar 2022 con OpenFootball. Presenta las cifras y espera la selección del usuario antes de exportar.',WORLD_CUP_ROUND_PROPERTIES,['round','players']),
 descriptor('select_round_research_metrics','Selecciona cifras de Qatar 2022 para revisar en pantalla. Disponible para investigación con StatsBomb.',{'report':{'type':'object'},'metrics':{'type':'array','minItems':1,'maxItems':3,'uniqueItems':True,'items':{'enum':['matches_played','goals','shots']}}},['report','metrics']),
 descriptor('read_instruction','Lee instrucciones o esquemas del repositorio.',{'path':{'type':'string'}},['path']),
 descriptor('project_state','Lee solicitud, etapas, resultados y artefactos del proyecto.'),
 descriptor('project_channel_evidence','Lee el expediente copiado en este proyecto en páginas verificadas de hasta 50 publicaciones.',{'offset':{'type':'integer','minimum':0},'limit':{'type':'integer','minimum':1,'maximum':50}}),
 descriptor('project_vidiq_observations','Lee observaciones manuales de vidIQ de los videos de referencia, separadas de las cifras de YouTube, en páginas de hasta 50.',{'offset':{'type':'integer','minimum':0},'limit':{'type':'integer','minimum':1,'maximum':50}}),
 descriptor('project_channel_performance','Lee la copia verificada del CSV de rendimiento de este proyecto en páginas de hasta 50 filas. Son cifras aportadas, no datos oficiales.',{'offset':{'type':'integer','minimum':0},'limit':{'type':'integer','minimum':1,'maximum':50}}),
 descriptor('project_script_outline','Lee el borrador editorial de cinco bloques, separado del guion de producción. Sus referencias y hechos requieren revisión.'),
 descriptor('project_packaging_options','Lee variantes de título y concepto de miniatura con la selección editorial del proyecto. No certifica CTR ni genera imágenes.'),
 descriptor('project_translation','Lee una traducción local guardada por fragmentos antes de repetirla. Conserva la obligación de revisar idioma y adaptación cultural; no genera ni aprueba el guion.',{'offset':{'type':'integer','minimum':0},'limit':{'type':'integer','minimum':1,'maximum':20}}),
 descriptor('project_source_image','Consulta la imagen de entrada preparada de este proyecto; no la envía a ComfyUI ni inicia generación.'),
 descriptor('project_comfy_jobs','Lee registros locales del proyecto para recuperar prompt_id y output_dir. No verifica la cola del servidor ni inicia trabajos.'),
 descriptor('reference_analysis','Lee el análisis local del video de referencia: transcripción, fotogramas, observaciones y límites. No inventa verificaciones externas.'),
 descriptor('analyze_project_reference','Analiza la referencia seleccionada dentro de la tarea del productor, con motores locales en CPU. Sin parámetros reutiliza el análisis compartido válido, aunque sea parcial. Con opciones explícitas ejecuta un nuevo análisis. Reutiliza el video guardado; no verifica hechos externos.',{
     'frames':{'type':'integer','minimum':1,'maximum':12},'vision':{'type':'boolean'},'transcribe':{'type':'boolean'},
     'summary':{'type':'boolean'},'vision_model':{'enum':['smolvlm','qwen-vl']}}),
 descriptor('resource_status','Consulta servidores, GPU y carpetas de recursos; no descarga pesos.'),
 descriptor('model_download_plan','Prepara una lista revisable de un modelo usando al menos dos inventarios. Excluye rutas registradas y candidatos en otras ubicaciones. No descarga, no instala y no demuestra ausencia actual.',{'group_id':{'type':'string'}},['group_id']),
 descriptor('model_catalog','Consulta catálogo e inventarios; group_id devuelve archivos, carpetas y URLs sin descargarlos.',{'group_id':{'type':'string'}}),
 descriptor('project_files','Lista archivos existentes del proyecto, sin leer recursos externos.'),
 descriptor('read_project_file','Lee un archivo de texto del proyecto.',{'path':{'type':'string'}},['path']),
 descriptor('write_project_file','Crea textos, subtítulos o código de composición en assets/ o workspaces/.',{'path':{'type':'string'},'content':{'type':'string','maxLength':300000}},['path','content']),
 descriptor('read_artifact','Lee un artefacto JSON del proyecto.',{'name':{'type':'string'}},['name']),
 descriptor('write_artifact','Guarda un artefacto JSON; los artefactos conocidos validan su esquema.',{'name':{'type':'string'},'data':{'type':'object'}},['name','data']),
 descriptor('list_tools','Descubre contratos locales por capacidad; no ejecuta herramientas.',{'capability':{'type':'string'}}),
 descriptor('tool_info','Lee contrato real, disponibilidad, instalación y skills de una herramienta.',{'name':{'type':'string'}},['name']),
 descriptor('execute_tool','Ejecuta una herramienta local disponible de coste cero; usa rutas del proyecto.',{'name':{'type':'string'},'inputs':{'type':'object'}},['name','inputs']),
 descriptor('wan_presets','Lee perfiles WAN locales y su configuración actual.'),
 descriptor('select_wan_preset','Selecciona explícitamente el perfil WAN previamente anunciado y registra el cambio; no descarga modelos.',{'preset':{'enum':['wan22-5b-t2v','wan22-14b-t2v-4step','wan22-14b-i2v-4step']}},['preset']),
 descriptor('language_resources','Consulta archivos locales de voz, traducción y transcripción para el idioma objetivo. Para Kokoro devuelve nombres de voces con prefijo compatible; usa uno de ellos explícitamente. No carga modelos ni certifica pronunciación.'),
 descriptor('adapter_status','Diagnóstico del adaptador, pesos locales y dependencias; no descarga.',{'family':{'type':'string'}},['family']),
 descriptor('comfy_nodes','Consulta esquemas y modelos registrados en nodos ComfyUI concretos.',{'classes':{'type':'array','items':{'type':'string'},'maxItems':12}},['classes']),
 descriptor('bind_workflow','Vincula un workflow API ya creado dentro del proyecto a una familia de modelos.',{'family':{'type':'string'},'path':{'type':'string'},'output_node':{'type':'string'}},['family','path','output_node']),
 descriptor('inspect_image','Inspecciona una imagen real del proyecto con el modelo local; requiere capacidad de visión.',{'path':{'type':'string'},'question':{'type':'string','maxLength':4000}},['path','question']),
 descriptor('consult_agent','Consulta a un especialista local. Devuelve análisis, no autoriza acciones.',{'role':{'enum':list(ROLES)},'task':{'type':'string'}},['role','task']),
 descriptor('checkpoint','Guarda evidencia de la etapa actual y respeta sus aprobaciones.',{'stage':{'type':'string'},'status':{'enum':['in_progress','completed','awaiting_human','failed']},'artifacts':{'type':'object'},'message':{'type':'string'}},['stage','status','artifacts']),
 descriptor('finish','Finaliza solo si existe un render comprobable, o comunica bloqueo concreto.',{'message':{'type':'string'},'blocked':{'type':'boolean'}},['message','blocked'])]


class Pause(Exception):
    def __init__(self,status,message):self.status=status;super().__init__(message)


class LocalAgent:
    def __init__(self,pid,chat=None,registry=None,cancel=None):
        self.pid=pid;self.path=studio.project_path(pid)
        self.request=studio.read_json(self.path/'production_request.json')
        self.manifest=load_pipeline_readonly(self.request['pipeline'])
        self.config=studio.settings();self._chat=chat;self.registry=registry
        self.cancel=cancel or threading.Event();self.reads=set();self.calls=0
        self._stage_timer=None;self._timed_stage=None

    def event(self,kind,message,**extra):
        with studio.LOCK:
            job=studio.read_json(self.path/'job.json',{})
            events=job.get('events',[]);events.append({'at':studio.now(),'kind':kind,'message':message,**extra})
            job.update(updated_at=studio.now(),message=message,events=events[-500:])
            studio.save_json(self.path/'job.json',job)

    def status(self,status,message):
        with studio.LOCK:
            job=studio.read_json(self.path/'job.json',{})
            job.update(status=status,updated_at=studio.now(),message=message)
            studio.save_json(self.path/'job.json',job)

    def pending_editorial_revision(self):
        stage=get_next_stage(studio.PROJECTS_DIR,self.pid,self.request['pipeline'])
        if not isinstance(stage,str):return None
        cp=studio.read_json(self.path/('checkpoint_'+stage+'.json'),{})
        review=cp.get('review',{}) if isinstance(cp,dict) else {}
        if (cp.get('status')=='failed' and isinstance(review,dict)
                and review.get('editorial_decision')=='revision_requested'
                and isinstance(review.get('reason'),str)):
            return {'stage':stage,'reason':review['reason'],
                    'instruction':'Corrige esta etapa según el motivo editorial antes de escribir un checkpoint nuevo; conserva la revisión anterior en el historial.'}
        return None

    def chat(self,messages,tools=None):
        if self.cancel.is_set():raise Pause('stopped','Detenido entre acciones; los artefactos ya creados se conservan.')
        if self._chat:return self._chat(messages,tools)
        if not self.config['model']:raise Pause('blocked','Selecciona primero un modelo local de Ollama.')
        data={'model':self.config['model'],'messages':messages,'stream':False,'keep_alive':0,
              'options':{'num_ctx':32768,'num_predict':8192}}
        if tools is not None:data['tools']=tools
        response=studio.local_request(self.config['ollama_url'],'/api/chat',data,timeout=180)
        message=response.get('message')
        if not isinstance(message,dict):raise ValueError('Ollama no devolvió un mensaje válido')
        return message

    def registry_ready(self):
        if self.registry is None:
            from tools.tool_registry import registry
            registry.ensure_discovered();self.registry=registry
        return self.registry

    @staticmethod
    def permitted(tool):
        # Hybrid selectors can dispatch paid providers; use a concrete local tool.
        return tool.runtime in (ToolRuntime.LOCAL,ToolRuntime.LOCAL_GPU) and tool.tier!=ToolTier.PUBLISH

    def instruction(self,path):
        target=(studio.REPO_ROOT/path).resolve()
        rel=target.relative_to(studio.REPO_ROOT.resolve())
        if rel.parts[0] not in ('skills','.agents','schemas','pipeline_defs','docs') and rel.as_posix() not in ('AGENT_GUIDE.md','PROJECT_CONTEXT.md'):
            raise ValueError('Solo se leen instrucciones del proyecto')
        if not target.is_file() or target.stat().st_size>500000:raise ValueError('Instrucción ausente o demasiado grande')
        text=target.read_text(encoding='utf-8');self.reads.add(rel.as_posix())
        return text

    def artifact_path(self,name):
        import re
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,80}',name):raise ValueError('Nombre de artefacto inválido')
        return self.path/'artifacts'/(name+'.json')

    def verify_outputs(self):
        from lib.checkpoint import get_completed_stages
        complete=set(get_completed_stages(studio.PROJECTS_DIR,self.pid,self.request['pipeline']))
        required={s['name'] for s in self.manifest['stages'] if s['name']!='publish'}
        if not required<=complete:raise ValueError('Quedan etapas de producción sin completar')
        report=studio.read_json(self.artifact_path('render_report'),{})
        outputs=report.get('outputs',[])
        from lib.render_verification import verify
        return verify(self.pid,outputs)

    def dispatch(self,name,args):
        spec=next((t['function'] for t in TOOLS if t['function']['name']==name),None)
        if not spec:raise ValueError('Llamada desconocida')
        validate(args,spec['parameters'])
        if name=='project_channel_evidence':
            from lib.project_channel_evidence import page
            return page(self.path,self.request,**args)
        if name=='project_vidiq_observations':
            from lib.project_video_observations import page
            return page(self.path,self.request,**args)
        if name=='project_channel_performance':
            from lib.project_channel_performance import page
            return page(self.path,self.request,**args)
        if name=='project_script_outline':
            from lib.script_outline import read
            return read(self.pid)
        if name=='project_packaging_options':
            from lib.packaging_options import read
            return read(self.pid)
        if name=='read_instruction':return self.instruction(args['path'])
        if name=='sports_sources':
            from lib.sports_sources import catalog
            return catalog(**args)
        if name=='football_comparison':
            from lib.football_comparisons import collect
            return collect(**args, execute=lambda connector, inputs: self.dispatch(
                'execute_tool', {'name': connector, 'inputs': inputs}))
        if name=='select_football_comparison_metrics':
            from lib.football_comparisons import select
            return select(**args)
        if name=='football_saved_selection':
            from lib.football_comparison_dossier import latest_for_agent
            return latest_for_agent(self.pid, args.get('include_report', False))
        if name=='world_cup_2022_round':
            from lib.world_cup_rounds import compare
            return compare(**args)
        if name=='world_cup_2022_round_goals':
            from lib.world_cup_open_goals import compare
            return compare(**args)
        if name=='select_round_research_metrics':
            from lib.world_cup_rounds import select_research_metrics
            return select_research_metrics(**args)
        if name=='project_state':return studio.production_state(self.pid)
        if name=='reference_analysis':
            from lib.reference_analysis import read
            return read(self.pid)
        if name=='analyze_project_reference':
            stage=get_next_stage(studio.PROJECTS_DIR,self.pid,self.request['pipeline'])
            definition=next((s for s in self.manifest['stages'] if s['name']==stage),{})
            if 'skills/'+definition.get('skill','')+'.md' not in self.reads or 'skills/meta/video-reference-analyst.md' not in self.reads:
                raise ValueError('Lee primero las instrucciones de la etapa y del análisis de referencias')
            from lib.reference_analysis import run_for_producer
            self.event('reference_analysis','Analizando referencia elegida con motores locales en CPU')
            report=run_for_producer(self.pid,args,self.cancel)
            self.event('reference_analysis','Análisis de referencia: '+report['status'])
            return report
        if name=='project_comfy_jobs':
            from lib.comfy_job_records import project_jobs
            return project_jobs(self.pid)
        if name=='project_translation':
            from lib.project_translation import read_for_agent
            return read_for_agent(self.pid,args.get('offset',0),args.get('limit',10))
        if name=='project_source_image':
            from lib.production_input_image import current_image
            return {'project_id':self.pid,'image':current_image(self.pid),
                    'usage':'Para WAN I2V usa project_id de este proyecto y text en execute_tool. La imagen se transfiere solo al ejecutar. No inventes server_image.'}
        if name=='resource_status':return studio.runtime_status()
        if name=='model_download_plan':
            from lib.download_plan import plan
            return plan(args['group_id'])
        if name=='model_catalog':
            data=studio.resource_catalog()
            if args.get('group_id'):
                group=next((g for g in data['groups'] if g['id']==args['group_id']),None)
                if group is None:raise ValueError('Grupo de modelos desconocido')
                return {'group':group,'notes':data['notes'],'inventories_imported':len(data['inventories'])}
            statuses=('recorded_size_match','recorded_path_size_unknown','recorded_size_mismatch','possible_elsewhere_size_match','temporary_download_recorded','not_recorded')
            return {'inventories':data['inventories'],'notes':data['notes'],
                'interpretation':'No registrado no significa ausente. Revisa ambos inventarios, candidatos y descargas posteriores antes de sugerir descargar.',
                'groups':[{'id':g['id'],'label':g['label'],'files':len(g['files']),
                    'recorded':sum(f['status']=='recorded_size_match' for f in g['files']),
                    'inventory_status_counts':{status:sum(f['status']==status for f in g['files']) for status in statuses}}
                    for g in data['groups']]}

        if name=='project_files':
            paths=[]
            for p in self.path.rglob('*'):
                if p.is_file() and not p.is_symlink():
                    p.resolve().relative_to(self.path.resolve())
                    paths.append({'path':p.relative_to(self.path).as_posix(),'bytes':p.stat().st_size})
                if len(paths)>=1000:break
            return {'files':paths,'limit':1000}
        if name in ('read_project_file','write_project_file'):
            p=Path(args['path'])
            if not p.is_absolute():p=self.path/p
            p=p.resolve();relative=p.relative_to(self.path.resolve())
            if name=='read_project_file':
                if not p.is_file() or p.stat().st_size>500000:raise ValueError('Archivo ausente o demasiado grande')
                return {'path':str(p),'content':p.read_text(encoding='utf-8')}
            if not relative.parts or relative.parts[0] not in ('assets','workspaces'):raise ValueError('Escribe archivos de trabajo en assets/ o workspaces/; usa checkpoint para las etapas')
            if p.suffix.lower() not in ('.txt','.md','.json','.srt','.vtt','.ass','.svg','.html','.css','.js','.jsx','.ts','.tsx','.csv','.yaml','.yml'):raise ValueError('Formato de texto no admitido')
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(args['content'],encoding='utf-8')
            return {'saved':str(p),'bytes':p.stat().st_size}
        if name=='read_artifact':return studio.read_json(self.artifact_path(args['name']),{})
        if name=='write_artifact':
            if args['name'] in ('decision_log', 'football_comparison_selection',
                                'channel_idea_source', 'channel_research_snapshot',
                                'video_observations_snapshot', 'source_channel_research'):
                raise ValueError('Artefacto reservado del estudio')
            from schemas.artifacts import ARTIFACT_NAMES, validate_artifact
            if args['name'] in ARTIFACT_NAMES:validate_artifact(args['name'],args['data'])
            studio.save_json(self.artifact_path(args['name']),args['data'])
            return {'saved':str(self.artifact_path(args['name']))}
        if name=='list_tools':
            reg=self.registry_ready()
            return [{'name':t.name,'capability':t.capability,'runtime':t.runtime.value,'install_instructions':t.install_instructions}
                    for t in reg._tools.values() if self.permitted(t) and (not args.get('capability') or t.capability==args['capability'])]
        if name in ('tool_info','execute_tool'):
            tool=self.registry_ready().get(args['name'])
            if tool is None or not self.permitted(tool):raise ValueError('Solo herramientas concretas locales, sin publicación ni proveedores de pago')
            if name=='tool_info':return tool.get_info()
            inputs=dict(args['inputs']);validate(inputs,tool.input_schema)
            stage=get_next_stage(studio.PROJECTS_DIR,self.pid,self.request['pipeline'])
            definition=next((s for s in self.manifest['stages'] if s['name']==stage),{})
            if 'skills/'+definition.get('skill','')+'.md' not in self.reads:raise ValueError('Lee primero las instrucciones de la etapa actual')
            for field in ('output_path','output_dir'):
                if field in tool.input_schema.get('properties',{}) and not inputs.get(field):raise ValueError('Indica explícitamente '+field+' dentro del proyecto')
            price=tool.estimate_cost(inputs)
            if not isinstance(price,(int,float)) or not math.isfinite(price) or price!=0:raise ValueError('La estimación no es cero verificable')
            if tool.get_status()!=ToolStatus.AVAILABLE:raise ValueError('Herramienta no disponible: '+tool.install_instructions)
            for skill in tool.agent_skills:
                if not any(x.startswith('.agents/skills/'+skill+'/') for x in self.reads):raise ValueError('Lee primero el skill '+skill)
            for key,value in inputs.items():
                if key in ('output_path','output_dir','project_dir','workspace_dir','workdir') and value:
                    dest=Path(value)
                    if not dest.is_absolute():dest=self.path/dest
                    dest=dest.resolve();dest.relative_to(self.path.resolve());inputs[key]=str(dest)
            if 'project_id' in inputs and inputs['project_id']!=self.pid:raise ValueError('La herramienta apunta a otro proyecto')
            self.event('tool','Ejecutando '+tool.name)
            result=tool.execute(inputs)
            data=result.data
            if result.success and tool.name in ('official_uefa_live', 'official_fifa_live', 'official_jleague_live', 'official_mls_live', 'official_bundesliga_live', 'official_premier_live', 'brasileirao_player_stats', 'classificacao_league_player_stats', 'eredivisie_player_stats', 'ligamx_player_stats', 'as_competition_player_stats', 'official_asian_cup_live', 'official_ofc_nations_cup_live'):
                from lib.football_statistics import add_standard_statistics
                data=add_standard_statistics(data)
            return {'success':result.success,'data':data,'error':result.error,'cost_usd':result.cost_usd,
                    'artifacts':list(result.artifacts or [])}
        if name=='wan_presets':
            from lib.wan_presets import catalog
            from lib.model_adapters import configuration
            return {'presets':catalog(),'current':configuration('wan')}
        if name=='select_wan_preset':
            from lib.model_adapters import configure
            value=configure('wan',{'preset':args['preset']})
            self.event('adapter','Perfil WAN seleccionado explícitamente: '+args['preset'])
            return value
        if name=='language_resources':
            from lib.language_versions import local_requirements
            return local_requirements(self.pid)
        if name=='adapter_status':
            from lib.model_adapters import diagnostics,CATALOG
            if args['family'] not in CATALOG:raise ValueError('Familia desconocida')
            return diagnostics(args['family'])
        if name=='comfy_nodes':
            result={}
            for cls in args['classes']:
                if len(cls)>150:raise ValueError('Nombre de nodo demasiado largo')
                result[cls]=studio.local_request(self.config['comfyui_url'],'/object_info/'+quote(cls,safe=''),timeout=10).get(cls)
            return result
        if name=='bind_workflow':
            from lib.model_adapters import configure,spec,CATALOG
            from lib.model_comfy_adapter import validate_graph
            family=args['family']
            if family not in CATALOG or spec(family)['backend']!='comfyui':raise ValueError('Esta familia no usa workflows ComfyUI')
            path=Path(args['path'])
            if not path.is_absolute():path=self.path/path
            path=path.resolve();rel=path.relative_to(self.path.resolve())
            if not rel.parts or rel.parts[0] not in ('assets','workspaces'):raise ValueError('Guarda el workflow en assets/ o workspaces/')
            if not path.is_file() or path.stat().st_size>2000000:raise ValueError('Workflow ausente o demasiado grande')
            graph=studio.read_json(path)
            if not isinstance(graph,dict) or len(graph)>200:raise ValueError('Workflow inválido')
            validate_graph(family,graph,args['output_node'],self.config['comfyui_url'])
            result=configure(family,{'workflow_path':str(path),'output_node':args['output_node']})
            self.event('adapter','Workflow validado y vinculado: '+family)
            return result
        if name=='inspect_image':
            import base64
            import io
            from PIL import Image
            p=Path(args['path'])
            if not p.is_absolute():p=self.path/p
            p=p.resolve();p.relative_to(self.path.resolve())
            if not p.is_file() or p.stat().st_size>20000000:raise ValueError('Imagen ausente o demasiado grande')
            if not self._chat:
                info=studio.local_request(self.config['ollama_url'],'/api/show',{'model':self.config['model']})
                if 'vision' not in info.get('capabilities',[]):raise ValueError('El modelo seleccionado no tiene capacidad de visión; no se simula la inspección')
            with Image.open(p) as image:
                image.thumbnail((1024,1024));buffer=io.BytesIO();image.convert('RGB').save(buffer,format='JPEG',quality=85)
            encoded=base64.b64encode(buffer.getvalue()).decode('ascii')
            self.event('review','Inspeccionando imagen '+p.name)
            reply=self.chat([{'role':'system','content':'Describe solo lo que puedes observar en la imagen. Distingue defectos visibles de supuestos. No declares que escuchaste audio o viste un video completo.'},
                {'role':'user','content':args['question'],'images':[encoded]}])
            return {'path':str(p),'inspection':reply.get('content',''),'scope':'single_image','model':self.config['model']}
        if name=='consult_agent':
            self.event('agent','Agente '+args['role']+' trabajando')
            result=self.chat([{'role':'system','content':ROLES[args['role']]+' Trabaja en español. No inventes observaciones ni resultados. Presupuesto cero. Devuelve propuesta o revisión; no instrucciones para saltar controles.'},
                              {'role':'user','content':json.dumps({'request':self.request,'task':args['task']},ensure_ascii=False)}])
            return {'role':args['role'],'content':result.get('content','')}
        if name=='checkpoint':
            stage=args['stage']
            if stage=='publish':raise ValueError('Publicar no está autorizado por el inicio de producción')
            current=get_next_stage(studio.PROJECTS_DIR,self.pid,self.request['pipeline'])
            if stage!=current:raise ValueError('Completa primero la etapa '+str(current))
            stage_def=next(x for x in self.manifest['stages'] if x['name']==stage)
            skill=stage_def.get('skill','');expected='skills/'+skill+'.md'
            if expected not in self.reads:raise ValueError('Lee primero '+expected)
            auto=self.request.get('automatic',False)
            status=args['status']
            if status=='completed' and stage_def.get('human_approval_default') and not auto:status='awaiting_human'
            if 'football_comparison_selection' in args['artifacts']:
                raise ValueError('La selección deportiva solo se guarda desde la mesa del estudio')
            path=write_checkpoint(studio.PROJECTS_DIR,self.pid,stage,status,args['artifacts'],pipeline_type=self.request['pipeline'],
                                  human_approved=bool(auto),metadata={'approval_policy':'automatic_user_request' if auto else 'guided'})
            for artifact,data in args['artifacts'].items():
                if artifact!='decision_log':studio.save_json(self.artifact_path(artifact),data)
            self.event('stage',stage+': '+status)
            if status in ('completed','awaiting_human','failed') and self._timed_stage==stage and self._stage_timer is not None:
                self.event('stage_timing',stage+': tiempo activo medido',stage=stage,
                           outcome=status,elapsed_seconds=round(max(0,time.monotonic()-self._stage_timer),3))
                self._timed_stage=get_next_stage(studio.PROJECTS_DIR,self.pid,self.request['pipeline'])
                self._stage_timer=time.monotonic()
            if status=='awaiting_human':raise Pause('awaiting_human','Revisa y aprueba la etapa '+stage+' en el estudio.')
            if status=='failed':raise Pause('blocked',args.get('message') or 'La etapa '+stage+' falló; revisa sus requisitos.')
            return {'checkpoint':str(path),'next_stage':get_next_stage(studio.PROJECTS_DIR,self.pid,self.request['pipeline'])}
        if name=='finish':
            if args['blocked']:raise Pause('blocked',args['message'])
            outputs=self.verify_outputs()
            from lib.final_delivery import deliver
            delivery=deliver(self.pid,outputs)
            if delivery['copied']:self.event('delivery','Videos finales copiados y verificados en el destino configurado')
            raise Pause('rendered',args['message']+' Exportación lista; publicación no ejecutada.')

    def run(self):
        from lib.resource_sampling import ResourceSampler
        sampler=ResourceSampler()
        try:
            sampler.start()
            self._timed_stage=get_next_stage(studio.PROJECTS_DIR,self.pid,self.request['pipeline'])
            self._stage_timer=time.monotonic()
            self.status('running','Agente productor iniciando')
            if not self._chat:
                cfg=self.config
                reply=studio.local_request(cfg['ollama_url'],'/api/tags')
                if cfg['model'] not in [x.get('name') for x in reply.get('models',[])]:
                    raise Pause('blocked','Falta seleccionar un modelo instalado en Ollama. No se descarga ni se paga automáticamente.')
                import os
                os.environ['COMFYUI_SERVER_URL']=cfg['comfyui_url']
            contract=(studio.REPO_ROOT/'docs'/'PRODUCTION_AGENT_CONTRACT_ES.md').read_text()
            guide=self.instruction('AGENT_GUIDE.md')
            messages=[{'role':'system','content':contract+'\n'+guide},
                      {'role':'user','content':json.dumps({'request':self.request,'project_directory':str(self.path),'manifest':self.manifest,
                        'next_stage':get_next_stage(studio.PROJECTS_DIR,self.pid,self.request['pipeline']),'user_clarifications':studio.read_json(self.path/'user_clarifications.json',[]),
                        'pending_editorial_revision':self.pending_editorial_revision(),
                        'source_image':self.dispatch('project_source_image',{}),
                        'reference_analysis':self.dispatch('reference_analysis',{})},ensure_ascii=False)}]
            for _ in range(self.config['max_turns']):
                if sum(len(json.dumps(m)) for m in messages)>450000:raise Pause('blocked','Se alcanzó el límite de contexto. Artefactos conservados para reanudar.')
                message=self.chat(messages,TOOLS);messages.append(message)
                calls=message.get('tool_calls',[])
                if not calls:
                    raise Pause('awaiting_input',message.get('content') or 'El modelo no emitió llamadas de herramientas. Revisa compatibilidad del modelo.')
                if len(calls)>16:raise ValueError('Demasiadas llamadas simultáneas')
                for call in calls:
                    if self.cancel.is_set():raise Pause('stopped','Detenido entre acciones; no se cancelan silenciosamente renders ya enviados.')
                    fn=call.get('function',{});args=fn.get('arguments',{})
                    if isinstance(args,str):args=json.loads(args)
                    try:
                        result=self.dispatch(fn.get('name'),args)
                    except Pause:raise
                    except Exception as exc:
                        result={'error':str(exc)[:1200]};self.event('error',str(exc)[:1200])
                    content=json.dumps(result,ensure_ascii=False,default=str)
                    if len(content)>100000:content=json.dumps({'error':'Resultado demasiado grande; solicita una capacidad o artefacto concreto.'})
                    messages.append({'role':'tool','tool_name':fn.get('name'),'content':content})
                studio.save_json(self.path/'agent_session.json',{'updated_at':studio.now(),'messages':messages})
            raise Pause('blocked','Límite de turnos alcanzado. Se conserva el estado para revisar y reanudar.')
        except Pause as exc:self.status(exc.status,str(exc))
        except Exception as exc:
            self.status('blocked','El agente se detuvo: '+str(exc)[:600])
        finally:
            try:
                studio.save_json(self.path/'resource_usage.json',{**sampler.finish(),'recorded_at':studio.now()})
            finally:
                with ACTIVE_LOCK:ACTIVE.pop(self.pid,None)


def start(pid):
    project=studio.project_path(pid)
    request=studio.read_json(project/'production_request.json')
    from lib.project_channel_evidence import require_valid
    require_valid(project,request)
    from lib.project_video_observations import verified_rows
    if request.get('research_idea'):verified_rows(project,request)
    from lib.language_versions import selection_provenance_problem
    if problem:=selection_provenance_problem(project):raise ValueError(problem)
    from lib.storage_layout import readiness
    storage=readiness(studio.REPO_ROOT,studio.PROJECTS_DIR)
    if not storage['ready']:raise ValueError('Almacenamiento no preparado: '+'; '.join(storage['problems']))
    with ACTIVE_LOCK:
        from lib import reference_analysis
        with reference_analysis.LOCK:
            if reference_analysis.ACTIVE:raise ValueError('Espera a que termine el análisis local del video')
        if pid in ACTIVE:raise ValueError('Este proyecto ya tiene un agente activo')
        if ACTIVE:raise ValueError('Ya hay una producción activa; espera para compartir la GPU')
        stop=threading.Event();agent=LocalAgent(pid,cancel=stop)
        thread=threading.Thread(target=agent.run,daemon=True,name='production-'+pid)
        ACTIVE[pid]=(thread,stop)
        thread.start()
    return {'started':True,'project_id':pid}


def stop(pid):
    studio.project_path(pid)
    with ACTIVE_LOCK:
        if pid not in ACTIVE:return {'requested':False}
        ACTIVE[pid][1].set()
    return {'requested':True,'note':'Se detendrá entre acciones; una petición o render en curso puede continuar hasta su timeout.'}


def approve(pid):
    p=studio.project_path(pid);req=studio.read_json(p/'production_request.json')
    from lib.project_channel_evidence import require_valid
    require_valid(p,req)
    if req.get('research_idea'):
        from lib.project_video_observations import verified_rows
        verified_rows(p,req)
    from lib.language_versions import selection_provenance_problem
    if problem:=selection_provenance_problem(p):raise ValueError(problem)
    with ACTIVE_LOCK:
        if pid in ACTIVE:raise ValueError('El agente sigue activo')
    current=get_next_stage(studio.PROJECTS_DIR,pid,req['pipeline'])
    cp=studio.read_json(p/('checkpoint_'+str(current)+'.json'),{})
    if cp.get('status')!='awaiting_human' or current=='publish':raise ValueError('No hay una etapa de producción pendiente de aprobación')
    write_checkpoint(studio.PROJECTS_DIR,pid,current,'completed',cp['artifacts'],pipeline_type=req['pipeline'],human_approved=True)
    _record_editorial_review(p,current,'approved','')
    return start(pid)


def _record_editorial_review(path,stage,decision,reason):
    with studio.LOCK:
        reviews=studio.read_json(path/'editorial_reviews.json',[])
        if not isinstance(reviews,list):reviews=[]
        reviews.append({'stage':stage,'decision':decision,'reason':reason,'at':studio.now()})
        studio.save_json(path/'editorial_reviews.json',reviews[-200:])


def request_revision(pid,reason):
    if not isinstance(reason,str) or not 1<=len(reason.strip())<=2000:
        raise ValueError('Describe el cambio solicitado (máximo 2000 caracteres)')
    p=studio.project_path(pid);req=studio.read_json(p/'production_request.json')
    with ACTIVE_LOCK:
        if pid in ACTIVE:raise ValueError('El agente sigue activo')
    current=get_next_stage(studio.PROJECTS_DIR,pid,req['pipeline'])
    cp=studio.read_json(p/('checkpoint_'+str(current)+'.json'),{})
    if cp.get('status')!='awaiting_human' or current=='publish':
        raise ValueError('No hay una etapa pendiente de revisión')
    reason=reason.strip()
    write_checkpoint(studio.PROJECTS_DIR,pid,current,'failed',cp['artifacts'],pipeline_type=req['pipeline'],
                     review={'editorial_decision':'revision_requested','reason':reason})
    _record_editorial_review(p,current,'revision_requested',reason)
    with studio.LOCK:
        job=studio.read_json(p/'job.json',{})
        job.update(status='awaiting_input',message='Revisión solicitada en '+current+': '+reason,updated_at=studio.now())
        studio.save_json(p/'job.json',job)
    return {'revision_requested':True,'stage':current,'generation_started':False}
