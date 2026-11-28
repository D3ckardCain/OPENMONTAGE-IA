"""Check that every approved scene is still suitable for an exact-length edit."""
import math

from lib import production_studio as studio
from lib import scene_batch


def readiness(project_id,fit_policy='exact'):
    if fit_policy not in ('exact','trim_or_hold'):
        raise ValueError('Elige duración exacta o recortar/mantener último fotograma')
    project=studio.project_path(project_id)
    manifest=scene_batch.read(project_id)
    if not manifest.get('scenes'):
        return {'ready':False,'problems':['Prepara primero el manifiesto de escenas'],'scenes':[]}
    problems=[];rows=[]
    try:
        if scene_batch.approved_plan(project_id)['scene_plan_sha256']!=manifest['scene_plan_sha256']:
            problems.append('El plan aprobado cambió desde la creación del manifiesto')
    except (ValueError,KeyError) as exc:
        problems.append(str(exc))
    for scene in manifest['scenes']:
        errors=[];selected=None;actual=None
        if not scene.get('identity_reviewed') or not scene.get('approved_take_id'):
            errors.append('Falta una toma aprobada con revisión visual de identidad')
        else:
            selected=next((take for take in scene['takes'] if take['sha256']==scene['approved_take_id']),None)
            if not selected:errors.append('La toma aprobada ya no está registrada')
        image=scene.get('image')
        if not image:errors.append('Falta la imagen de entrada')
        else:
            try:
                if scene_batch._media(project,image['path'],'image')['sha256']!=image['sha256']:
                    errors.append('Cambió la imagen de entrada')
            except (ValueError,OSError,KeyError) as exc:errors.append('Imagen inaccesible: '+str(exc))
        if selected:
            try:
                verified=scene_batch._media(project,selected['path'],'video')
                if verified['sha256']!=selected['sha256']:errors.append('Cambió la toma aprobada')
                actual=verified['duration_seconds']
                ratio=verified['width']/verified['height']
                expected=9/16 if manifest['aspect_ratio']=='9:16' else 16/9
                if abs(ratio/expected-1)>.03:errors.append('Formato de la toma incompatible con '+manifest['aspect_ratio'])
                target=scene['end_seconds']-scene['start_seconds']
                if not math.isfinite(target) or target<=0:
                    errors.append('Duración objetivo inválida')
                elif fit_policy=='exact' and abs(actual-target)>max(.25,target*.02):
                    errors.append(f'Duración real {actual:.2f} s frente a {target:.2f} s del plan; requiere decidir ajuste')
            except (ValueError,OSError,KeyError) as exc:errors.append('Toma inaccesible: '+str(exc))
        rows.append({'scene_id':scene['scene_id'],'ready':not errors,'problems':errors,
                     'approved_take':selected['path'] if selected else None,'duration_seconds':actual})
    return {'ready':not problems and all(row['ready'] for row in rows),'problems':problems,
            'scenes':rows,'scene_count':len(rows),'aspect_ratio':manifest['aspect_ratio'],
            'fit_policy':fit_policy}
