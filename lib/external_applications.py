"""Explicit local application bindings. Installers are never launched as tools."""
from pathlib import Path
import subprocess
import threading
from lib import production_studio as studio

CATALOG={
 'node':{'label':'Node.js','purpose':'Motor JavaScript local para los flujos de composición','executables':['node.exe','node'],'extensions':[],'mode':'managed_cli'},
 'rhubarb':{'label':'Rhubarb Lip Sync','purpose':'Diagnóstico y claves de boca desde audio local','executables':['rhubarb.exe','rhubarb'],'extensions':[],'mode':'managed_cli','automation_tools':['rhubarb_doctor','rhubarb_lip_sync']},
 'openscad':{'label':'OpenSCAD','purpose':'Abrir y editar diseños CAD paramétricos','executables':['openscad.exe','openscad'],'extensions':['.scad'],'mode':'desktop'},
 'kinovea':{'label':'Kinovea','purpose':'Revisar y anotar videos para análisis de movimiento','executables':['Kinovea.exe'],'extensions':['.mp4','.avi','.mkv','.mov','.wmv','.kva'],'mode':'desktop'},
 'krita':{'label':'Krita','purpose':'Editar ilustraciones y proyectos de pintura','executables':['krita.exe','krita'],'extensions':['.kra','.ora','.png','.jpg','.jpeg','.tif','.tiff','.psd'],'mode':'desktop','inspection_tools':['krita_document_inspect']},
 'ffmpeg':{'label':'FFmpeg','purpose':'Extracción, montaje y exportación desde los flujos del Estudio','executables':['ffmpeg.exe','ffmpeg'],'extensions':[],'mode':'managed_cli','setting':'ffmpeg_path'},
 'ffprobe':{'label':'FFprobe','purpose':'Medición de duración, resolución y pistas','executables':['ffprobe.exe','ffprobe'],'extensions':[],'mode':'managed_cli','setting':'ffprobe_path'},
 'yt-dlp':{'label':'yt-dlp','purpose':'Descargar referencias desde el Estudio','executables':['yt-dlp.exe','yt-dlp'],'extensions':[],'mode':'managed_cli','setting':'yt_dlp_path'},
 'deno':{'label':'Deno','purpose':'Motor JavaScript usado por el descargador','executables':['deno.exe','deno'],'extensions':[],'mode':'managed_cli','setting':'deno_path'},
 'avogadro':{'label':'Avogadro','purpose':'Preparar estructuras moleculares','executables':['avogadro2.exe','avogadro.exe'],'extensions':['.cml','.xyz','.mol','.sdf','.pdb'],'mode':'desktop'},
 'openmodelica':{'label':'OpenModelica','purpose':'Modelar y simular sistemas físicos','executables':['OMEdit.exe'],'extensions':['.mo'],'mode':'desktop'},
 'solvespace':{'label':'SolveSpace','purpose':'Diseñar geometría y mecanismos','executables':['solvespace.exe','solvespace_single_core_x64.exe'],'extensions':['.slvs'],'mode':'desktop'},
 'blender':{'label':'Blender','automation_tools':['blender_world'],'purpose':'Crear escenas y animación 3D','executables':['blender.exe','blender'],'extensions':['.blend'],'mode':'desktop'},
 'freecad':{'label':'FreeCAD','purpose':'Preparar modelos CAD','executables':['FreeCAD.exe','FreeCAD'],'extensions':['.FCStd'],'mode':'desktop'},
 'qgis':{'label':'QGIS','purpose':'Preparar mapas y escenas geográficas','executables':['qgis-bin.exe','qgis-ltr-bin.exe','qgis'],'extensions':['.qgs','.qgz'],'mode':'desktop','numeric_tools':['qgis_coordinates']},
}
CHILDREN={}
LOCK=threading.Lock()


def configuration():return studio.read_json(studio.CONFIG_DIR/'applications.json',{})


def catalog():
    cfg=configuration();result=[]
    with LOCK:
        for key,item in CATALOG.items():
            executable=studio.settings().get(item['setting'],'') if item.get('setting') else cfg.get(key,{}).get('executable','')
            path=Path(executable) if executable else None
            child=CHILDREN.get(key)
            result.append({'id':key,**item,'executable':executable,'configured':bool(executable),
                'file_found':bool(path and path.is_file()),'integration':'managed_pipeline' if item['mode']=='managed_cli' else 'managed_scene_workflow_and_project_file_handoff' if item.get('automation_tools') else 'project_file_handoff',
                'inference_verified':False,'running_managed_process':bool(child and child.poll() is None)})
    return result


def configure(identifier,data):
    if identifier not in CATALOG:raise ValueError('Aplicación desconocida')
    if set(data)!={'executable'} or not isinstance(data['executable'],str):raise ValueError('Indica executable')
    path=Path(data['executable'])
    if not path.is_absolute() or path.name.casefold() not in {n.casefold() for n in CATALOG[identifier]['executables']}:
        raise ValueError('Selecciona el ejecutable instalado o portable admitido, no su instalador')
    if not path.is_file():raise ValueError('El ejecutable no está disponible')
    if CATALOG[identifier].get('setting'):
        studio.configure({CATALOG[identifier]['setting']:str(path)})
        return {'saved':True,'launched':False}
    with studio.LOCK:
        cfg=configuration();cfg[identifier]={'executable':str(path)};studio.save_json(studio.CONFIG_DIR/'applications.json',cfg)
    return {'saved':True,'launched':False}


def launch(identifier,project_id,relative_file=None):
    if identifier not in CATALOG:raise ValueError('Aplicación desconocida')
    if CATALOG[identifier]['mode']=='managed_cli':raise ValueError('Esta herramienta se utiliza mediante los flujos del Estudio, no se abre una consola independiente')
    project=studio.project_path(project_id).resolve()
    cfg=configuration().get(identifier,{})
    path=Path(cfg.get('executable',''))
    if not path.is_absolute() or not path.is_file():raise ValueError('Configura primero la aplicación instalada')
    if path.name.casefold() not in {n.casefold() for n in CATALOG[identifier]['executables']}:raise ValueError('Ejecutable no admitido')
    arguments=[str(path)]
    process_options={}
    if identifier=='qgis' and path.suffix.lower()=='.exe':
        from lib.qgis_runtime import launch_options
        arguments,process_options=launch_options(path,studio.CONFIG_DIR/'qgis')
    if relative_file:
        source=(project/relative_file).resolve();source.relative_to(project)
        if not source.is_file() or source.suffix.lower() not in {x.lower() for x in CATALOG[identifier]['extensions']}:raise ValueError('Archivo de proyecto no compatible')
        arguments.append(str(source))
    with LOCK:
        existing=CHILDREN.get(identifier)
        if existing and existing.poll() is None:raise ValueError('Esta aplicación ya tiene un proceso abierto desde el Estudio')
        logdir=project/'application_logs';logdir.mkdir(exist_ok=True)
        with (logdir/(identifier+'.log')).open('ab') as log:
            child=subprocess.Popen(arguments,cwd=str(project),stdin=subprocess.DEVNULL,stdout=log,stderr=log,shell=False,**process_options)
        CHILDREN[identifier]=child
    record={'application':identifier,'pid':child.pid,'started_at':studio.now(),'file':relative_file,'status':'launched_not_verified'}
    studio.save_json(logdir/(identifier+'-last.json'),record)
    return record
