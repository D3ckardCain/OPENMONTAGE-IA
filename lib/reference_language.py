"""Separate detected language suggestions from explicit source-language choices."""
import hashlib
import json
import re
from lib import production_studio as studio


def code(value):
    if not isinstance(value,str) or not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]+)*',value):raise ValueError('Usa un código de idioma como en, es o ko')
    return value


def evidence(project_id):
    path=studio.project_path(project_id)
    request=studio.read_json(path/'production_request.json')
    report=studio.read_json(path/'reference_analysis.json',{})
    value={'reference':request.get('reference',''),'analysis':report}
    fingerprint=hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return path,report,fingerprint


def read(project_id):
    path,report,fingerprint=evidence(project_id)
    saved=studio.read_json(path/'reference_language.json',{})
    detected=report.get('transcript',{}).get('language') if isinstance(report.get('transcript'),dict) else None
    try:detected=code(detected)
    except ValueError:detected=None
    current=saved.get('evidence_sha256')==fingerprint
    return {'confirmed_language':saved.get('language') if current else None,'detected_language':detected,
        'confirmation_outdated':bool(saved) and not current,'confirmation_required_for_exclusion':True,
        'note':'El idioma detectado es una sugerencia de la transcripción y puede fallar con música, varios idiomas o poco diálogo. Confírmalo para excluirlo de las versiones.'}


def confirm(project_id,language):
    language=code(language)
    path,report,fingerprint=evidence(project_id)
    studio.save_json(path/'reference_language.json',{'language':language,'evidence_sha256':fingerprint,'confirmed_at':studio.now(),'method':'user_confirmation'})
    return read(project_id)
