"""Copy verified renders to the configured final-output disk, preserving originals."""
import hashlib
import shutil
import uuid
from pathlib import Path
from lib import production_studio as studio
from lib.storage_layout import read_config


def digest(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(4*1024*1024),b''):value.update(chunk)
    return value.hexdigest()


def deliver(project_id,outputs):
    project=studio.project_path(project_id)
    configured=read_config(studio.REPO_ROOT).get('final_outputs_dir')
    if not configured:return {'mode':'project_renders','copied':False,'outputs':outputs}
    root=Path(configured)
    if not root.is_dir():raise ValueError('El disco de videos finales no está conectado. Se conservó la copia de trabajo.')
    root=root.resolve();folder=root/project_id
    if folder.is_symlink():raise ValueError('El destino final del proyecto no puede ser un enlace simbólico')
    folder.mkdir(exist_ok=True)
    records=[]
    for item in outputs:
        source=Path(item['path'])
        if not source.is_absolute():source=project/source
        source=source.resolve();source.relative_to((project/'renders').resolve())
        if not source.is_file() or not source.stat().st_size:raise ValueError('Falta el render verificado')
        checksum=digest(source);dest=folder/(source.stem+'-'+checksum[:12]+source.suffix)
        if dest.is_symlink():raise ValueError('El archivo final no puede ser un enlace simbólico')
        if dest.exists():
            if digest(dest)!=checksum:raise ValueError('Hay un archivo distinto en el destino; no se sobrescribió')
        else:
            if shutil.disk_usage(root).free<source.stat().st_size:raise ValueError('No hay espacio suficiente en el disco de finales')
            temp=folder/('.delivery-'+uuid.uuid4().hex+'.tmp')
            try:
                shutil.copyfile(source,temp)
                if digest(temp)!=checksum:raise ValueError('La copia final no superó la comprobación de integridad')
                temp.replace(dest)
            finally:temp.unlink(missing_ok=True)
        records.append({'source':str(source),'path':str(dest),'sha256':checksum,'bytes':dest.stat().st_size})
    report={'mode':'dedicated_final_directory','copied':True,'outputs':records,'delivered_at':studio.now()}
    studio.save_json(project/'final_delivery.json',report)
    return report
