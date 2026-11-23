"""Read a verified render's exact scene input chain when local receipts exist."""
import re
from pathlib import Path

from lib import production_studio as studio
from lib.project_asset_sources import read as asset_sources


STAGES=(('artifacts/scene_edit_preview.json','scene_preview'),
        ('artifacts/scene_audio_preview.json','scene_audio_preview'),
        ('artifacts/scene_subtitles.json','scene_subtitles'),
        ('artifacts/scene_burned_subtitles.json','scene_burned_subtitles'))


def _valid_input(item):
    if not isinstance(item,dict):return False
    path,digest=item.get('path'),item.get('sha256')
    if not isinstance(path,str) or not path or len(path)>500 or '\\' in path:return False
    relative=Path(path)
    return (not relative.is_absolute() and '..' not in relative.parts and
            relative.parts[0] in ('assets','source_images','thumbnails') and
            isinstance(digest,str) and bool(re.fullmatch('[0-9a-f]{64}',digest)))


def inspect(project_id):
    project=studio.project_path(project_id)
    verification=studio.read_json(project/'render_verification.json',{})
    outputs=verification.get('outputs',[]) if isinstance(verification,dict) else []
    if not isinstance(outputs,list) or len(outputs)>16:raise ValueError('Recibo de render inválido')
    receipts={}
    for filename,kind in STAGES:
        path=project/filename
        if path.is_symlink():continue
        record=studio.read_json(path,{})
        if isinstance(record,dict) and record.get('status')=='completed' and isinstance(record.get('output'),dict):
            receipts[kind]=record
    registered={row['path']:row for row in asset_sources(project_id)['entries']}
    rows=[]
    for output in outputs:
        if not isinstance(output,dict):raise ValueError('Salida verificada inválida')
        raw,sha=output.get('path'),output.get('sha256')
        if not isinstance(raw,str) or not isinstance(sha,str):raise ValueError('Salida verificada inválida')
        path=Path(raw)
        if not path.is_absolute():path=project/path
        try:relative=path.resolve().relative_to(project.resolve()).as_posix()
        except ValueError:relative=None
        matched=None
        for kind,receipt in receipts.items():
            saved=receipt['output']
            if saved.get('path')==relative and saved.get('sha256')==sha:
                matched=kind;break
        chain=[];inputs=[];problem=None
        if matched:
            order=['scene_preview','scene_audio_preview','scene_subtitles','scene_burned_subtitles']
            for kind in order[:order.index(matched)+1]:
                record=receipts.get(kind)
                if record is None:
                    problem='Falta un recibo intermedio de este montaje.';break
                if kind=='scene_preview':
                    choices=record.get('choices')
                    if not isinstance(choices,list) or not 1<=len(choices)<=100:
                        problem='Selección de escenas ausente o demasiado grande.';break
                    inputs.extend({'role':'scene_take','scene_id':choice.get('scene_id'),
                                   'path':choice.get('path'),'sha256':choice.get('sha256')}
                                  for choice in choices if isinstance(choice,dict))
                    if (len(inputs)!=len(choices) or any(not isinstance(row['scene_id'],str) or
                            not row['scene_id'] or not _valid_input(row) for row in inputs)):
                        problem='Selección de escenas inválida.';break
                elif kind=='scene_audio_preview':
                    parent=receipts['scene_preview']
                    if record.get('video_attempt')!=parent.get('attempt') or record.get('video')!=parent.get('output'):
                        problem='El audio no corresponde al montaje de escenas.';break
                    if not _valid_input(record.get('narration')) or (record.get('music') is not None and
                            not _valid_input(record.get('music'))):
                        problem='Pistas de audio ausentes o inválidas.';break
                    for role in ('narration','music'):
                        track=record.get(role)
                        if track:inputs.append({'role':role,'path':track.get('path'),'sha256':track.get('sha256')})
                elif kind=='scene_subtitles':
                    parent=receipts['scene_audio_preview']
                    if record.get('source_attempt')!=parent.get('attempt') or record.get('source')!=parent.get('output'):
                        problem='Los subtítulos no corresponden al audio.';break
                    inputs.append({'role':'subtitles','path':record.get('srt_path'),'sha256':record.get('srt_sha256')})
                    if not _valid_input(inputs[-1]):problem='SRT ausente o inválido.';break
                else:
                    parent=receipts['scene_subtitles']
                    if (record.get('source_attempt')!=parent.get('attempt') or
                            record.get('source_sha256')!=parent['output'].get('sha256') or
                            record.get('srt_sha256')!=parent.get('srt_sha256')):
                        problem='El video subtitulado no corresponde al SRT aprobado.';break
                chain.append(kind)
        if problem:inputs=[]
        for item in inputs:
            row=registered.get(item['path'])
            item['registered']=bool(row and row['sha256']==item['sha256'])
            item['commercial_use']=row['commercial_use'] if item['registered'] else None
        rows.append({'output_path':raw,'output_sha256':sha,'receipt_stage':matched,
                     'trace_complete':bool(matched and not problem),'chain':chain,'inputs':inputs,
                     'problem':problem or (None if matched else 'No existe recibo de entradas para este render.')})
    return {'project_id':project_id,'verification_status':verification.get('status') if isinstance(verification,dict) else None,
            'outputs':rows,'generation_started':False,
            'note':'Coincidencia con recibos guardados, sin recalcular hashes actuales. Las licencias declaradas requieren revisión; la integridad de archivos se comprueba aparte.'}
