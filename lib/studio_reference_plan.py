"""Reference-linked canonical scene_plan; no automatic director or generation."""
from copy import deepcopy
import re
from lib import studio_editor as editor
from schemas.artifacts import validate_artifact
from jsonschema import ValidationError


def _hash(value):
    if not isinstance(value,str) or not re.fullmatch('[a-f0-9]{64}',value):
        raise ValueError('Se requiere SHA256 explícito de evidencia/imagen')
    return value


def apply(edl,data):
    if data.get('input_edl_sha256')!=editor.edit_digest(edl):
        raise editor.Conflict('El proyecto cambió; revisa el plan sobre la base actual')
    plan=deepcopy(data['plan'])
    try:validate_artifact('scene_plan',plan)
    except ValidationError as exc:raise ValueError('scene_plan inválido: '+exc.message[:300]) from exc
    scenes=plan['scenes']
    if not 1<=len(scenes)<=100:raise ValueError('Plan limitado a1–100escenas')
    ids=[s['id'] for s in scenes]
    if len(set(ids))!=len(ids):raise ValueError('IDs de escena repetidos')
    previous=0
    for scene in scenes:
        start=editor.number(scene['start_seconds']);end=editor.number(scene['end_seconds'],start)
        if end<=start or start<previous:raise ValueError('Escenas ordenadas y sin solapes; tiempos positivos')
        previous=end
    meta=plan.get('metadata',{})
    if meta.get('reference_contract')!='studio-reference-plan-v1':raise ValueError('Falta contrato de referencia explícito')
    evidence=meta.get('evidence')
    if not isinstance(evidence,list) or not 1<=len(evidence)<=100:raise ValueError('Falta evidencia de referencia acotada')
    receipts={}
    for item in evidence:
        source=edl['sources'][item['source_id']]
        if item.get('source_sha256')!=source['sha256']:raise editor.Conflict('Cambió la fuente de referencia')
        receipt=_hash(item['receipt_sha256'])
        if receipt in receipts:raise ValueError('Recibo de referencia duplicado')
        a,b=(editor.number(v,0,source['duration']) for v in item['requested_range'])
        if b<=a or item.get('coverage')!='partial_sampled_images_only':raise ValueError('Declara intervalo y cobertura muestreada parcial')
        frames=item.get('frames')
        if not isinstance(frames,list) or not 1<=len(frames)<=12:raise ValueError('Referencia limitada a1–12fotogramas por recibo')
        for frame in frames:
            pts=editor.number(frame['pts_seconds'],a,b)
            if pts>=b:raise ValueError('PTS fuera del intervalo de referencia semiabierto')
            _hash(frame['sha256'])
        receipts[receipt]=item
    links=meta.get('scene_refs',{});notes=meta.get('scene_notes',{})
    if set(links)!=set(ids) or set(notes)-set(ids):raise ValueError('Asocia referencias/notas a IDs de escena válidos')
    markers={m['id']:m for m in edl.get('markers',[])}
    fingerprints={}
    for scene in scenes:
        refs=links[scene['id']];note_ids=notes.get(scene['id'],[])
        if not isinstance(refs,list) or not 1<=len(refs)<=12 or any(r not in receipts for r in refs):raise ValueError('Referencia de escena no encontrada')
        if not isinstance(note_ids,list) or len(note_ids)>50 or any(n not in markers for n in note_ids):raise ValueError('Comentario temporal no encontrado; reutiliza marcadores del editor')
        fingerprints[scene['id']]=editor.edit_digest(dict(scene=scene,style=plan.get('style_playbook'),
            references=[receipts[r] for r in refs],notes=[markers[n] for n in note_ids]))
    pairs=meta.get('comparisons',[])
    if not isinstance(pairs,list) or len(pairs)>100:raise ValueError('Comparaciones limitadas a100')
    for pair in pairs:
        if pair.get('scene_id') not in ids or pair.get('clock')!='reference_source_pts':raise ValueError('Comparación requiere escena/reloj explícitos')
        before,after=pair['before'],pair['after'];_hash(before['frame_sha256']);_hash(after['frame_sha256'])
        if before.get('source_sha256')!=after.get('source_sha256') or before.get('source_sha256') not in {s['sha256'] for s in edl['sources'].values()}:
            raise ValueError('Comparación debe declarar la misma referencia de origen')
        a,b=(editor.number(v['pts_seconds']) for v in [before,after])
        if abs(a-b)>1e-9:raise ValueError('Antes/después requieren el mismo instante, no imágenes de tiempos distintos')
        if not any(item['source_sha256']==before['source_sha256'] and
                   any(abs(frame['pts_seconds']-a)<1e-9 and frame['sha256']==before['frame_sha256'] for frame in item['frames'])
                   for item in receipts.values()):raise ValueError('El antes debe corresponder a un fotograma declarado en la evidencia')
        # A changed comparison invalidates its associated scene, never unrelated scenes.
        sid=pair['scene_id'];fingerprints[sid]=editor.edit_digest([fingerprints[sid],pair])
    old=edl.get('reference_plan_origin',{}).get('scene_fingerprints',{})
    edl['reference_plan']=plan
    edl['reference_plan_origin']=dict(contract='studio-reference-plan-v1',scene_fingerprints=fingerprints,
        changed_ids=[sid for sid in ids if old.get(sid)!=fingerprints[sid]],
        unchanged_ids=[sid for sid in ids if old.get(sid)==fingerprints[sid]],removed_ids=[sid for sid in old if sid not in fingerprints],
        generation_performed=False,evidence_validation='declared_hash_bindings_not_redecoded',
        comments_clock='project_timeline_markers_not_implicitly_reference_pts',
        review_status='pending_human_review_not_inferred_from_similarity')
