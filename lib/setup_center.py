"""Read-only local discovery, environment plans and structured runtime settings.

Discovery never executes candidates. Plans list imports, not an unverified pip
command or a claim of working package versions. No installers are launched.
"""
from pathlib import Path
import os
import sys
from lib import production_studio as studio
from lib import external_applications as applications
from lib import model_adapters as adapters

SKIP={'.git','node_modules','site-packages','__pycache__','models','descargas_modelos',
      'bibliotecas_geografia','bibliotecas_tecnicas','$recycle.bin','system volume information'}
MAX_ENTRIES=20000
MAX_DEPTH=6


def discover(data):
    if set(data)-{'roots'}:raise ValueError('Indica únicamente roots')
    roots=data.get('roots',studio.settings()['resource_roots'])
    if not isinstance(roots,list) or len(roots)>16 or any(not isinstance(p,str) or not p or len(p)>4000 or not Path(p).is_absolute() for p in roots):raise ValueError('Usa hasta 16 carpetas absolutas')
    roots=list(dict.fromkeys(str(Path(p).resolve()) for p in roots))
    names={name.casefold():key for key,row in applications.CATALOG.items() for name in row['executables']}
    found={key:[] for key in applications.CATALOG};pythons=[];installers=[];errors=[];scanned=[];count=0;limited=False
    seen=set()
    for value in roots:
        root=Path(value)
        if not root.is_dir():scanned.append({'path':value,'available':False});continue
        scanned.append({'path':value,'available':True});stack=[(root,0)]
        while stack and count<MAX_ENTRIES:
            folder,depth=stack.pop();key=os.path.normcase(str(folder))
            if key in seen:continue
            seen.add(key)
            try:
                with os.scandir(folder) as entries:
                    for entry in entries:
                        count+=1
                        if count>MAX_ENTRIES:limited=True;break
                        try:
                            if entry.is_symlink():continue
                            if entry.is_dir(follow_symlinks=False):
                                if entry.name.casefold() in SKIP:continue
                                if depth<MAX_DEPTH:stack.append((Path(entry.path),depth+1))
                                else:limited=True
                                continue
                            if not entry.is_file(follow_symlinks=False):continue
                            name=entry.name.casefold();path=str(Path(entry.path).resolve())
                            if name in names:
                                bucket=found[names[name]]
                                if path not in bucket and len(bucket)<20:bucket.append(path)
                            elif name in ('python.exe','python','python3'):
                                if path not in pythons and len(pythons)<30:pythons.append(path)
                            elif name.endswith('.exe') and any(t in name for t in ('avogadro','openmodelica','setup','installer')):
                                if len(installers)<40:installers.append(path)
                        except OSError:
                            if len(errors)<20:errors.append('No se pudo consultar '+entry.path)
            except OSError:
                if len(errors)<20:errors.append('No se pudo leer '+str(folder))
        if stack or count>=MAX_ENTRIES:limited=True
    configured={a['id']:a for a in applications.catalog()}
    return {'roots':scanned,'entries_examined':min(count,MAX_ENTRIES),'limited':limited,
        'limits':{'entries':MAX_ENTRIES,'depth':MAX_DEPTH},'errors':errors,
        'applications':[{'id':key,'label':row['label'],'candidates':sorted(found[key]),
            'configured_executable':configured[key]['executable'],
            'recommendation':found[key][0] if len(found[key])==1 and not configured[key]['configured'] else None}
            for key,row in applications.CATALOG.items()],
        'python_candidates':sorted(pythons),'installers_not_executed':installers,
        'executed_files':0,'configuration_changed':False,
        'note':'Búsqueda limitada por carpetas. La coincidencia del nombre no verifica el ejecutable; los modelos se localizan por catálogo, sin recorrer sus pesos.'}


def environment_plan(family):
    if family not in adapters.CATALOG:raise ValueError('Familia desconocida')
    cfg=adapters.configuration(family);spec=adapters.spec(family)
    info=adapters.diagnostics(family,probe=False)
    root=studio.REPO_ROOT/'.runtimes'/family
    expected=root/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    source_keys={'wan-camera':'camera-script','wan-control':'control-script','wan-s2v':'s2v-script','framepack':'framepack-script'}
    source=None
    if family in source_keys:
        source=studio.read_json(studio.REPO_ROOT/'docs/runtime_sources.json')[source_keys[family]]
    return {'family':family,'backend':spec['backend'],'configuration':cfg,
        'model_candidates':[{'path':str(p),'available':p.is_dir()} for p in adapters.model_candidates(family)],
        'selected_model_dir':info.get('model_dir'),'problems':info['problems'],
        'python_executable':cfg.get('python_executable') or sys.executable,
        'suggested_environment_dir':str(root),'suggested_python_path':str(expected),
        'imports_required':spec['dependencies'],'package_versions_validated':False,
        'dependency_probe_performed':False,'environment_created':False,'installation_started':False,
        'source_reference':source,'platform_requirement':info.get('platform_requirement'),
        'next_steps':(['Vincular pesos y Python aislado','Comprobar imports y versiones del motor','Realizar prueba de inferencia al final']
            if spec['backend']=='native' else ['Revisar variante de pesos y nodos','Preparar workflow API sin generar','Realizar prueba de inferencia al final']),
        'inference_verified':False}


def report():
    from lib.workflow_preparation import recipes
    from lib.storage_layout import readiness
    plans=[environment_plan(family) for family in adapters.CATALOG]
    return {'created_at':studio.now(),'models':plans,'applications':applications.catalog(),
        'storage':readiness(studio.REPO_ROOT,studio.PROJECTS_DIR),
        'total_families':len(plans),'prepared_recipes':sum(r['preparation_implemented'] for r in recipes()),
        'scope':'configuration_without_dependency_probes_or_inference','model_loads_started':0,
        'summary':'Requisitos locales y rutas; dependencias e inferencia todavía sin comprobar.'}


def save_report():
    value=report();studio.save_json(studio.CONFIG_DIR/'setup-report.json',value)
    return value


def _paths(data,keys):
    if set(data)!=set(keys):raise ValueError('Completa estos campos: '+', '.join(keys))
    result={}
    for name in keys:
        value=data[name]
        if not isinstance(value,str) or not value or len(value)>4000 or not Path(value).is_absolute():raise ValueError('Usa una ruta local absoluta para '+name)
        path=Path(value).resolve()
        if not path.exists():raise ValueError('No está conectado o no existe: '+name)
        result[name]=str(path)
    return result


def runtime_fields(family):
    if family=='framepack':return {'backbone_dir':'Carpeta HunyuanVideo (text encoders, tokenizers y VAE)','vision_dir':'Carpeta flux_redux_bfl (image_encoder y feature_extractor)'}
    if family=='magihuman':return {'distill_dir':'Pesos del modelo distill','audio_model_path':'Stable Audio Open local',
        'txt_model_path':'T5Gemma local','vae_model_path':'Wan2.2 TI2V 5B local',
        'student_config_path':'Configuración Turbo VAE (.json)','student_ckpt_path':'Checkpoint Turbo VAE (.ckpt)'}
    raise ValueError('Este motor no utiliza este formulario auxiliar')


def read_runtime_settings(family):
    fields=runtime_fields(family);cfg=adapters.configuration(family)
    saved=studio.read_json(studio.CONFIG_DIR/'runtime_inputs'/(family+'.json'),{})
    return {'family':family,'fields':fields,'values':{key:saved.get(key,'') for key in fields},'runtime_config':cfg.get('runtime_config'),'inference_verified':False}


def save_runtime_settings(family,data):
    fields=runtime_fields(family);paths=_paths(data,fields)
    if family=='framepack':
        for key,names in {'backbone_dir':['text_encoder','text_encoder_2','tokenizer','tokenizer_2','vae'],
                          'vision_dir':['image_encoder','feature_extractor']}.items():
            for name in names:
                if not (Path(paths[key])/name).is_dir():raise ValueError('Falta '+name+' dentro de '+key)
        config=paths
    else:
        if not Path(paths['distill_dir']).is_dir():raise ValueError('distill_dir debe ser una carpeta')
        for key in ('audio_model_path','txt_model_path','vae_model_path'):
            if not Path(paths[key]).is_dir():raise ValueError(key+' debe ser una carpeta')
        for key,suffix in [('student_config_path','.json'),('student_ckpt_path','.ckpt')]:
            if not Path(paths[key]).is_file() or Path(paths[key]).suffix.lower()!=suffix:raise ValueError('Archivo incompatible: '+key)
        student=Path(paths['student_config_path'])
        if student.stat().st_size>2000000 or not isinstance(studio.read_json(student),dict):raise ValueError('Configuración Turbo VAE inválida')
        if Path(paths['student_ckpt_path']).stat().st_size==0:raise ValueError('Checkpoint Turbo VAE vacío')
        config={'engine_config':{'load':paths['distill_dir'],'distill':True,'cp_size':1},
            'evaluation_config':{'cfg_number':1,'num_inference_steps':8,'use_turbo_vae':True,
                **{key:value for key,value in paths.items() if key!='distill_dir'}}}
    with studio.LOCK:
        path=studio.CONFIG_DIR/'runtime_configs'/(family+'.json');studio.save_json(path,config)
        adapters.configure(family,{'runtime_config':str(path.resolve())})
        studio.save_json(studio.CONFIG_DIR/'runtime_inputs'/(family+'.json'),paths)
    return {'saved':True,'family':family,'runtime_config':str(path),'generation_started':False,'model_files_moved':False}
