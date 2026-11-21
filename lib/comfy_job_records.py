"""Read existing project job ledgers without contacting ComfyUI."""
import os
from pathlib import Path

from lib import production_studio as studio


def project_jobs(project_id):
    root=studio.project_path(project_id).resolve()
    jobs=[];warnings=[];visited=0
    for directory,folders,files in os.walk(root,followlinks=False):
        folders[:]=sorted(f for f in folders if not (Path(directory)/f).is_symlink())
        visited+=1
        if visited>1000:
            warnings.append('Se alcanzó el límite de 1000 carpetas; la lista puede estar incompleta')
            break
        for name in sorted(files):
            if not name.startswith('comfy-') or not name.endswith('-job.json'):continue
            path=Path(directory)/name
            if path.is_symlink():continue
            try:
                path.resolve().relative_to(root)
                if path.stat().st_size>200000:raise ValueError('Registro demasiado grande')
                data=studio.read_json(path)
                if not isinstance(data,dict) or not isinstance(data.get('prompt_id'),str) or not data['prompt_id']:
                    raise ValueError('Identificador ausente')
                jobs.append({'record':path.relative_to(root).as_posix(),
                    'family':data.get('family'),'prompt_id':data['prompt_id'],
                    'status':data.get('status','unknown'),'last_error':data.get('last_error'),
                    'submitted_at':data.get('submitted_at'),'completed_at':data.get('completed_at'),
                    'output_dir':str(path.parent),'resume_prompt_id':data['prompt_id'],
                    'server_state_verified':False})
            except (ValueError,OSError,TypeError) as exc:
                warnings.append(path.relative_to(root).as_posix()+': '+str(exc))
            if len(jobs)>=100:
                warnings.append('Se muestran como máximo 100 registros')
                return {'jobs':jobs,'warnings':warnings}
    return {'jobs':jobs,'warnings':warnings}
