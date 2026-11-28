"""Revisioned SFX insertion/favourites and receipts on the existing manual project."""
from copy import deepcopy
import hashlib
import json
import re
import shutil
import uuid
from lib import production_studio as studio, studio_editor as edit
from lib import studio_sfx_catalog as library


def favorites(edl,data):
    ids=data.get('ids')
    if not isinstance(ids,list) or len(ids)>500 or any(not isinstance(x,str) for x in ids):
        raise ValueError('Lista de favoritos del proyecto inválida')
    for key in ids:library.find(key)
    edl['sfx_favorites']=sorted(set(ids))


def receipt(pid,request_id):
    if not isinstance(request_id,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{16,80}',request_id):
        raise ValueError('ID de solicitud SFX inválido')
    value=edit.state(pid);row=value.get('sfx_receipts',{}).get(request_id)
    if row is None:raise FileNotFoundError('Solicitud SFX no registrada; no se confirma inserción')
    applied=any(c['id']==row['clip_id'] for c in value['edit_decisions']['audio_tracks'])
    return {**value,'sfx_receipt':{**row,'currently_applied':applied},'reused':True}


def insert(pid,data,origin='user'):
    if origin not in ('user','agent'):raise ValueError('Procedencia desconocida')
    if set(data)-{'request_id','revision','asset_id','start_seconds','in_seconds','out_seconds','gain'}:
        raise ValueError('Parámetro SFX desconocido')
    request_id=data.get('request_id')
    if not isinstance(request_id,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{16,80}',request_id):
        raise ValueError('ID de solicitud SFX inválido')
    payload={k:v for k,v in data.items() if k!='revision'}
    try:fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True,allow_nan=False).encode()).hexdigest()
    except (ValueError,TypeError) as exc:raise ValueError('Parámetros SFX inválidos') from exc
    with edit.guard(pid,origin):
        value=edit.state(pid);previous=value.get('sfx_receipts',{}).get(request_id)
        if previous:
            if previous['request_sha256']!=fingerprint:raise edit.Conflict('ID SFX reutilizado con otros parámetros')
            return receipt(pid,request_id)
        edit._revision(value,data.get('revision'))
        manifest,row=library.find(data.get('asset_id'))
        if len(value.get('sfx_receipts',{}))>=1000:raise ValueError('Límite de 1000 recibos SFX por proyecto')
        edl=deepcopy(value['edit_decisions']);duration=edit.duration(edl)
        start=edit.number(data['start_seconds'],0,duration)
        first=edit.number(data.get('in_seconds',0),0,row['duration'])
        last=edit.number(data['out_seconds'],first+.001,row['duration'])
        if last-first<.001-1e-8 or start+last-first>duration+1e-8:
            raise ValueError('El efecto debe durar al menos 1 ms y caber en el montaje; ajusta su recorte')
        gain=edit.number(data.get('gain',1),0,4)
        source_id=next((key for key,s in edl['sources'].items() if s['sha256']==row['sha256'] and s['kind']=='audio'),None)
        project=studio.project_path(pid)
        license_name='assets/sfx/LICENSES-MotionGraphics-'+manifest['revision']+'.md'
        license_path=project/license_name
        license_text=manifest['license_text']
        provenance={'id':row['id'],'repository':manifest['repository'],'revision':manifest['revision'],
            'license':row['license'],'license_evidence':row['license_evidence'],
            'license_path':license_name,'aliases':row['aliases']}
        if license_path.exists() and license_path.read_text(encoding='utf-8')!=license_text:
            raise edit.Conflict('La atribución guardada fue modificada; conservar y revisar')
        if source_id is None:
            source_id=uuid.uuid4().hex
            relative='assets/sfx/'+row['sha256']+'.ogg';target=project/relative
            cache_path,_=library.materialize(row['id']);before=library.identity(cache_path)
            recovered_frozen=target.exists() and any(r.get('asset_id')==row['id'] and r.get('frozen_identity')==library.identity(target)
                for r in value.get('sfx_receipts',{}).values())
            if target.exists() and not recovered_frozen:
                # An unregistered file may be a partial previous copy; never
                # overwrite it or silently trust a new unverified identity.
                raise edit.Conflict('Ya existe un efecto sin registro; recuperar el estado y revisar')
            info={k:row[k] for k in ('duration','audio','kind')}
            edl['sources'][source_id]={**info,'path':relative,'sha256':row['sha256'],'bytes':row['bytes'],
                'mtime_ns':0,'original_name':row['name'],'imported_at':studio.now(),'origin':origin,
                'sfx_provenance':provenance}
            if recovered_frozen:
                edl['sources'][source_id]['mtime_ns']=target.stat().st_mtime_ns
                target=None
        else:
            edit.source(pid,source_id)
            edl['sources'][source_id].setdefault('sfx_provenance',provenance)
            target=None
        clip_id=uuid.uuid4().hex
        edl['audio_tracks'].append({'id':clip_id,'source':edl['sources'][source_id]['path'],'source_id':source_id,
            'in_seconds':first,'out_seconds':last,'start_seconds':start,'speed':1,'muted':False,
            'gain':gain,'fade_in':0,'fade_out':0,'sfx_catalog_id':row['id']})
        edit._validate_edit(edl)
        if target is not None:
            target.parent.mkdir(parents=True,exist_ok=True)
            with cache_path.open('rb') as src,target.open('xb') as dest:shutil.copyfileobj(src,dest)
            if library.identity(cache_path)!=before or target.stat().st_size!=row['bytes']:
                raise edit.Conflict('El efecto cambió durante su copia; conservar y revisar')
            edl['sources'][source_id]['mtime_ns']=target.stat().st_mtime_ns
        if not license_path.exists():
            license_path.parent.mkdir(parents=True,exist_ok=True)
            with license_path.open('x',encoding='utf-8') as stream:stream.write(license_text)
        saved={'request_id':request_id,'request_sha256':fingerprint,'status':'completed','asset_id':row['id'],
            'clip_id':clip_id,'source_id':source_id,'at_seconds':start,'in_seconds':first,'out_seconds':last,
            'origin':origin,'completed_at':studio.now(),'revision':value['revision']+1}
        saved['frozen_identity']=library.identity(project/edl['sources'][source_id]['path'])
        value.setdefault('sfx_receipts',{})[request_id]=saved
        edit._commit(pid,value,edl,origin,'sfx_insert')
        return receipt(pid,request_id)
