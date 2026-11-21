"""Atomic local translation checkpoints; resume only on an explicit worker run."""
import hashlib
import json
import os
import tempfile
from pathlib import Path


def fingerprint(model,language,chunks,max_new_tokens):
    files=[]
    for pattern in ('model*.safetensors','model*.index.json','config.json','generation_config.json','tokenizer_config.json','tokenizer.json','special_tokens_map.json','added_tokens.json','spiece.model'):
        for path in sorted(Path(model).glob(pattern)):
            stat=path.stat();files.append((path.name,stat.st_size,stat.st_mtime_ns))
    value={'model':str(Path(model).resolve()),'files':files,'language':language,
        'chunks':chunks,'max_new_tokens':max_new_tokens,'format':1}
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def load(path,key,chunks):
    if not path.exists():return []
    value=json.loads(path.read_text(encoding='utf-8'))
    completed=value.get('completed')
    if value.get('fingerprint')!=key or not isinstance(completed,list) or len(completed)>len(chunks):raise ValueError('Checkpoint de traducción incompatible; revisa el archivo de progreso')
    for index,item in enumerate(completed):
        if not isinstance(item,dict) or any(item.get(field)!=chunks[index][field] for field in ('index','start','end','text')) or not isinstance(item.get('translation'),str):raise ValueError('Checkpoint de traducción inválido; no se reutilizó')
    return completed


def save(path,key,completed):
    descriptor,name=tempfile.mkstemp(prefix='.translation-',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(descriptor,'w',encoding='utf-8') as stream:
            json.dump({'fingerprint':key,'completed':completed},stream,ensure_ascii=False);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)
