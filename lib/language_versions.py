"""Prepare independent localized projects without running or copying media."""
import hashlib
import json
import re
from lib import production_studio as studio


def create_versions(project_id,languages):
    if not isinstance(languages,list) or not 1<=len(languages)<=10:raise ValueError('Indica entre 1 y 10 idiomas')
    if any(not isinstance(code,str) or not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]+)*',code) for code in languages):raise ValueError('Usa códigos de idioma como en, ko o pt-BR')
    if len({code.lower() for code in languages})!=len(languages):raise ValueError('No repitas idiomas')
    with studio.LOCK:
        source=studio.project_path(project_id)
        request=studio.read_json(source/'production_request.json')
        if any(code.lower()==request['language'].lower() for code in languages):raise ValueError('Elige idiomas distintos del idioma objetivo del proyecto base')
        ledger=studio.read_json(source/'language_versions.json',{'versions':{}})
        fingerprint=hashlib.sha256(json.dumps({key:request.get(key) for key in ('title','brief','pipeline','reference','language')},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        results=[]
        for language in languages:
            key=fingerprint+':'+language.lower()
            existing=ledger['versions'].get(key)
            if existing:
                try:studio.project_path(existing['project_id'])
                except (OSError,ValueError):
                    results.append({'language':language,'status':'unavailable','project_id':existing['project_id'],'message':'La versión registrada no está disponible; revisa su carpeta antes de duplicarla'});continue
                results.append({**existing,'status':'existing'});continue
            brief=request['brief']+'\n\nVersión localizada para '+language+'. Investigar y escribir un guion propio en el idioma objetivo. Adaptar voz, subtítulos, títulos, miniatura, música y referencias culturales. Detectar el idioma de canciones y diálogos; sustituir recursos cuando corresponda con material autorizado. No basta con traducir letras ni invertir la imagen. Revisar exactitud, licencias y naturalidad antes de exportar.'
            if len(brief)>12000:raise ValueError('El encargo base es demasiado largo para añadir las instrucciones de localización')
            created=None
            try:
                created=studio.create_production({'title':(request['title'][:140]+' · '+language)[:150],
                    'brief':brief,'pipeline':request['pipeline'],'language':language,'reference':request.get('reference',''),'automatic':False})
                entry={'project_id':created['project_id'],'language':language,'created_at':studio.now()}
                ledger['versions'][key]=entry
                studio.save_json(source/'language_versions.json',ledger)
                results.append({**entry,'status':'created'})
            except (OSError,ValueError,KeyError) as exc:
                failure={'language':language,'status':'failed','message':str(exc)[:1200]}
                if created:failure['project_id']=created['project_id'];failure['message']+='; el proyecto se creó pero no se pudo registrar: revísalo antes de reintentar'
                results.append(failure);break
    return {'versions':results,'generation_started':False,'media_copied':False,'automatic_approval':False}


def list_versions(project_id):
    source=studio.project_path(project_id)
    with studio.LOCK:
        ledger=studio.read_json(source/'language_versions.json',{'versions':{}})
        records=[dict(entry) for entry in ledger['versions'].values()]
    summary={'total':len(records),'rendered':0,'awaiting_human':0,'blocked':0,'unavailable':0}
    for entry in records:
        try:
            path=studio.project_path(entry['project_id']);entry['status']='existing'
            job=studio.read_json(path/'job.json',{})
            verification=studio.read_json(path/'render_verification.json',{})
            delivery=studio.read_json(path/'final_delivery.json',{})
            entry.update(job_status=job.get('status','unknown'),message=job.get('message',''),
                updated_at=job.get('updated_at'),verification_status=verification.get('status','unknown'),
                final_copy_registered=delivery.get('copied',False))
            if entry['job_status'] in ('rendered','awaiting_human','blocked'):summary[entry['job_status']]+=1
            entry['can_enqueue']=entry['job_status']!='rendered'
        except (OSError,ValueError,KeyError,TypeError) as exc:
            entry.update(status='unavailable',can_enqueue=False,message=str(exc)[:600]);summary['unavailable']+=1
    return {'versions':records,'summary':summary,'generation_started':False}


def local_requirements(project_id):
    """Inspect configured local files without invoking runtimes or models."""
    from lib import model_adapters
    studio.project_path(project_id)
    candidates=[]
    for family in model_adapters.CATALOG:
        capability=model_adapters.spec(family)['capability']
        if capability not in ('tts','translation','transcription'):continue
        try:
            report=model_adapters.diagnostics(family,probe=False)
            candidates.append({'family':family,'capability':capability,
                'files_configured':report['ready'],'model_dir':report.get('model_dir'),
                'problems':report['problems'],'required_modules':report.get('required_modules',[]),
                'language_support_verified':False,'runtime_checked':False})
        except (OSError,ValueError,KeyError,TypeError) as exc:
            candidates.append({'family':family,'capability':capability,'files_configured':False,
                'problems':[str(exc)[:600]],'language_support_verified':False,'runtime_checked':False})
    return {'candidates':candidates,'generation_started':False,'network_requests_started':0,
        'note':'Revisión de archivos y configuración. No prueba dependencias, compatibilidad de idioma, voz, calidad ni rendimiento. El productor debe elegir un motor compatible antes de generar.'}
