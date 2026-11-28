"""Content-addressed project copies, with bounded-identity reuse and no clobber."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid


def identity(path):
    s=path.stat()
    return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def stage(source,workspace):
    source=source.resolve();workspace=workspace.resolve()
    if not source.is_file():raise ValueError('Medio ausente o no es archivo: '+str(source))
    try:
        source.relative_to(workspace)
        return source
    except ValueError:
        pass
    folder=workspace/'assets';folder.mkdir(exist_ok=True)
    folder.resolve().relative_to(workspace)
    cache=workspace/'.openmontage-staging.json'
    if cache.is_symlink():raise ValueError('Registro de staging enlazado; no se modifica')
    data=json.loads(cache.read_text(encoding='utf-8')) if cache.exists() else {'contract':'hf-staging-v1','sources':{}}
    if data.get('contract')!='hf-staging-v1' or not isinstance(data.get('sources'),dict):raise ValueError('Registro de staging no reconocido; no se sobrescribe')
    key=str(source);before=identity(source);row=data['sources'].get(key,{})
    if row.get('identity')==before:
        target=folder/row['name']
        target.resolve().relative_to(folder.resolve())
        if target.is_file() and not target.is_symlink() and row.get('target_identity')==identity(target):return target
    sha=digest(source)
    if identity(source)!=before:raise ValueError('El medio cambió durante su huella')
    target=folder/('om-hf-'+sha+source.suffix.lower())
    if target.exists():
        if target.is_symlink() or not target.is_file() or digest(target)!=sha:raise ValueError('Destino ocupado por un archivo distinto; se conserva')
    else:
        # xb never replaces a path another source or actor has already created.
        try:
            with source.open('rb') as src,target.open('xb') as dst:shutil.copyfileobj(src,dst,1024*1024)
        except FileExistsError as exc:raise ValueError('Destino apareció durante staging; no se sobrescribe') from exc
        if identity(source)!=before:
            target.unlink()  # Only the new file created by this invocation.
            raise ValueError('El medio cambió durante su copia')
    data['sources'][key]={'identity':before,'sha256':sha,'name':target.name,'target_identity':identity(target)}
    temporary=cache.with_name(cache.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        temporary.write_text(json.dumps(data,sort_keys=True),encoding='utf-8');os.replace(temporary,cache)
    finally:temporary.unlink(missing_ok=True)
    return target
