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
        research=None
        if request.get('research_idea'):
            from lib.project_channel_evidence import verified
            from lib.project_video_observations import verified_rows
            snapshot,idea,_=verified(source,request)
            observations=verified_rows(source,request)
            research={'snapshot':snapshot,'idea':idea,'observations':observations}
        from lib.football_comparison_dossier import latest_for_agent, save_to_project
        selection=latest_for_agent(project_id, include_report=True)
        from lib.reference_language import read as source_language
        confirmed=source_language(project_id)['confirmed_language']
        if confirmed and any(code.lower().split('-')[0]==confirmed.lower().split('-')[0] for code in languages):raise ValueError('Excluye el idioma original confirmado: '+confirmed)
        if any(code.lower()==request['language'].lower() for code in languages):raise ValueError('Elige idiomas distintos del idioma objetivo del proyecto base')
        ledger=studio.read_json(source/'language_versions.json',{'versions':{}})
        fingerprint_data={key:request.get(key) for key in ('title','brief','pipeline','reference','language')}
        if selection['available']:
            fingerprint_data['football_selection_id']=selection['selection_id']
        if research:
            fingerprint_data['research_idea_sha256']=request['research_idea_sha256']
            fingerprint_data['research_observations_sha256']=request.get('research_observations_sha256')
        fingerprint=hashlib.sha256(json.dumps(fingerprint_data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        results=[]
        for language in languages:
            key=fingerprint+':'+language.lower()
            existing=ledger['versions'].get(key)
            if existing:
                try:studio.project_path(existing['project_id'])
                except (OSError,ValueError):
                    results.append({'language':language,'status':'unavailable','project_id':existing['project_id'],'message':'La versión registrada no está disponible; revisa su carpeta antes de duplicarla'});continue
                if existing.get('source_football_selection'):
                    child=latest_for_agent(existing['project_id'])
                    original=existing['source_football_selection']
                    if not child['available'] or child.get('selection_id')!=original.get('selection_id'):
                        results.append({**existing,'status':'selection_changed','can_enqueue':False,
                            'message':'La selección deportiva de esta versión cambió; revisa el proyecto antes de producir'});continue
                if existing.get('source_channel_research'):
                    if problem:=research_provenance_problem(studio.project_path(existing['project_id']),existing['source_channel_research']):
                        results.append({**existing,'status':'research_changed','can_enqueue':False,'message':problem});continue
                results.append({**existing,'status':'existing'});continue
            brief=request['brief']+'\n\nVersión localizada para '+language+'. Investigar y escribir un guion propio en el idioma objetivo. Adaptar voz, subtítulos, títulos, miniatura, música y referencias culturales. Detectar el idioma de canciones y diálogos; sustituir recursos cuando corresponda con material autorizado. No basta con traducir letras ni invertir la imagen. Revisar exactitud, licencias y naturalidad antes de exportar.'
            if len(brief)>12000:raise ValueError('El encargo base es demasiado largo para añadir las instrucciones de localización')
            created=None
            try:
                created=studio.create_production({'title':(request['title'][:140]+' · '+language)[:150],
                    'brief':brief,'pipeline':request['pipeline'],'language':language,'reference':request.get('reference',''),'automatic':False})
                if research:
                    child=studio.project_path(created['project_id'])
                    child_request=studio.read_json(child/'production_request.json')
                    for field in ('research_idea','research_idea_sha256','research_observations_sha256'):
                        child_request[field]=request.get(field)
                    studio.save_json(child/'artifacts/channel_research_snapshot.json',research['snapshot'])
                    studio.save_json(child/'artifacts/channel_idea_source.json',research['idea'])
                    if research['observations'] is not None:
                        studio.save_json(child/'artifacts/video_observations_snapshot.json',research['observations'])
                    studio.save_json(child/'production_request.json',child_request)
                    from lib.project_channel_evidence import verified
                    verified(child,child_request)
                    verified_rows(child,child_request)
                if selection['available']:
                    copied=save_to_project(created['project_id'], selection['report'], selection['selected_metrics'])
                    if copied['selection']['selection_id']!=selection['selection_id']:
                        raise ValueError('La selección de la versión no coincide con la original')
                    studio.save_json(studio.project_path(created['project_id'])/'artifacts/source_football_selection.json',
                        {'project_id':project_id,'selection_id':selection['selection_id'],'sha256':selection['sha256']})
                entry={'project_id':created['project_id'],'language':language,'created_at':studio.now()}
                if selection['available']:
                    entry['source_football_selection']={'project_id':project_id,
                        'selection_id':selection['selection_id'],'sha256':selection['sha256']}
                if research:
                    entry['source_channel_research']={'project_id':project_id,
                        'research_idea':request['research_idea'],
                        'research_idea_sha256':request['research_idea_sha256'],
                        'snapshot_sha256':research['snapshot']['report_sha256'],
                        'research_observations_sha256':request.get('research_observations_sha256')}
                    studio.save_json(studio.project_path(created['project_id'])/'artifacts/source_channel_research.json',
                        entry['source_channel_research'])
                ledger['versions'][key]=entry
                studio.save_json(source/'language_versions.json',ledger)
                results.append({**entry,'status':'created'})
            except (OSError,ValueError,KeyError) as exc:
                failure={'language':language,'status':'failed','message':str(exc)[:1200]}
                if created:failure['project_id']=created['project_id'];failure['message']+='; el proyecto se creó pero no se pudo registrar: revísalo antes de reintentar'
                results.append(failure);break
    return {'versions':results,'generation_started':False,'media_copied':False,'automatic_approval':False}


def selection_provenance_problem(project):
    """Check a localized project's own selection against its creation snapshot."""
    research_marker=project/'artifacts/source_channel_research.json'
    if research_marker.is_symlink():return 'Procedencia de investigación inválida; revisa la versión'
    if research_marker.is_file():
        try:
            original=studio.read_json(research_marker)
            if problem:=research_provenance_problem(project,original):return problem
        except (OSError,ValueError,KeyError,TypeError):
            return 'No se pudo validar la procedencia de investigación de esta versión'
    marker=project/'artifacts/source_football_selection.json'
    if not marker.exists() and not marker.is_symlink():return None
    if marker.is_symlink():return 'Procedencia deportiva inválida; revisa la versión'
    from lib.football_comparison_dossier import latest_for_agent
    try:
        original=studio.read_json(marker)
        child=latest_for_agent(project.name)
        if (not isinstance(original,dict) or not child['available'] or
                child['selection_id']!=original.get('selection_id')):
            return 'La selección deportiva de la versión cambió; revisa el proyecto antes de producir'
    except (OSError,ValueError,KeyError,TypeError):
        return 'No se pudo validar la selección deportiva de esta versión'
    return None


def research_provenance_problem(project,original):
    from lib.project_channel_evidence import verified
    from lib.project_video_observations import verified_rows
    try:
        if not isinstance(original,dict):return 'Procedencia de investigación inválida; revisa la versión'
        request=studio.read_json(project/'production_request.json')
        snapshot,_,_=verified(project,request)
        verified_rows(project,request)
        if (request.get('research_idea')!=original.get('research_idea')
                or request.get('research_idea_sha256')!=original.get('research_idea_sha256')
                or request.get('research_observations_sha256')!=original.get('research_observations_sha256')
                or snapshot['report_sha256']!=original.get('snapshot_sha256')):
            return 'La investigación de esta versión cambió; revisa el proyecto antes de producir'
    except (OSError,ValueError,KeyError,TypeError):
        return 'No se pudo validar la investigación de esta versión'
    return None


def list_versions(project_id):
    source=studio.project_path(project_id)
    with studio.LOCK:
        ledger=studio.read_json(source/'language_versions.json',{'versions':{}})
        records=[dict(entry) for entry in ledger['versions'].values()]
    summary={'total':len(records),'rendered':0,'awaiting_human':0,'blocked':0,'unavailable':0}
    for entry in records:
        try:
            path=studio.project_path(entry['project_id']);entry['status']='existing'
            if entry.get('source_football_selection'):
                from lib.football_comparison_dossier import latest_for_agent
                child=latest_for_agent(entry['project_id'])
                original=entry['source_football_selection']
                if not child['available'] or child.get('selection_id')!=original.get('selection_id'):
                    entry.update(status='selection_changed',message='La selección deportiva de esta versión cambió; revisa el proyecto antes de producir')
            if entry.get('source_channel_research'):
                if problem:=research_provenance_problem(path,entry['source_channel_research']):
                    entry.update(status='research_changed',message=problem)
            job=studio.read_json(path/'job.json',{})
            verification=studio.read_json(path/'render_verification.json',{})
            delivery=studio.read_json(path/'final_delivery.json',{})
            entry.update(job_status=job.get('status','unknown'),message=entry.get('message') or job.get('message',''),
                updated_at=job.get('updated_at'),verification_status=verification.get('status','unknown'),
                final_copy_registered=delivery.get('copied',False))
            if entry['job_status'] in ('rendered','awaiting_human','blocked'):summary[entry['job_status']]+=1
            entry['can_enqueue']=entry['job_status']!='rendered' and entry['status']=='existing'
        except (OSError,ValueError,KeyError,TypeError) as exc:
            entry.update(status='unavailable',can_enqueue=False,message=str(exc)[:600]);summary['unavailable']+=1
    return {'versions':records,'summary':summary,'generation_started':False}


def local_requirements(project_id):
    """Inspect configured local files without invoking runtimes or models."""
    from lib import model_adapters
    studio.project_path(project_id)
    target=studio.read_json(studio.project_path(project_id)/'production_request.json').get('language')
    candidates=[]
    for family in model_adapters.CATALOG:
        capability=model_adapters.spec(family)['capability']
        if capability not in ('tts','translation','transcription'):continue
        try:
            report=model_adapters.diagnostics(family,probe=False)
            from lib.model_languages import binding
            try:language_binding=binding(family,target) if target else None;language_problem=None
            except ValueError as exc:language_binding=None;language_problem=str(exc)
            matching_voices=[]
            if family=='kokoro' and target and language_binding:
                from lib.model_languages import local_voices
                matching_voices=local_voices(target,report.get('model_dir'))
            candidates.append({'family':family,'capability':capability,
                'files_configured':report['ready'],'model_dir':report.get('model_dir'),
                'target_language':target,'language_binding':language_binding,'language_problem':language_problem,
                'matching_local_voices':matching_voices,
                'problems':report['problems'],'required_modules':report.get('required_modules',[]),
                'language_support_verified':False,'runtime_checked':False})
        except (OSError,ValueError,KeyError,TypeError) as exc:
            candidates.append({'family':family,'capability':capability,'files_configured':False,
                'problems':[str(exc)[:600]],'language_support_verified':False,'runtime_checked':False})
    return {'target_language':target,'candidates':candidates,'generation_started':False,'network_requests_started':0,
        'note':'Revisión de archivos y configuración. No prueba dependencias, compatibilidad de idioma, voz, calidad ni rendimiento. El productor debe elegir un motor compatible antes de generar.'}
