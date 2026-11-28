"""Strict local V3 loading using the pinned upstream MIT classes; no Hub calls."""
from __future__ import annotations
import gc


def strict_state(module,state,derived=()):
    """Allow only named locally derived buffers, then use strict=True."""
    target=module.state_dict()
    missing=set(target)-set(state);extra=set(state)-set(target)
    buffers=dict(module.named_buffers())
    if extra or not missing<=set(derived) or not missing<=set(buffers):
        raise ValueError('ABI V3 incompatible: missing='+str(sorted(missing))+' unexpected='+str(sorted(extra)))
    wrong=[name for name in set(target)&set(state) if tuple(target[name].shape)!=tuple(state[name].shape)]
    if wrong:raise ValueError('Formas V3 incompatibles: '+str(sorted(wrong)))
    complete=dict(state)
    complete.update({name:buffers[name] for name in missing})
    module.load_state_dict(complete,strict=True)
    return dict(strict=True,tensors_from_checkpoint=len(state),derived_buffers=sorted(missing))


def load_profile(profile_id,device='cuda'):
    # Import heavy libraries only in the isolated worker/explicit qualification.
    try:from lib.voice_preparation import catalog
    except ImportError:from voice_preparation import catalog
    row=next((r for r in catalog()['profiles'] if r['id']==profile_id),None)
    if row is None:raise ValueError('Perfil regional desconocido')
    if any(row[key]['status']!='verified_cached' for key in ('main','decoder','voice_encoder')) or not row['tokenizer']['verified_cached']:
        raise ValueError('Recursos regionales ausentes, parciales o cambiados; verificar explícitamente antes de cargar')
    import torch
    from safetensors.torch import load_file
    from chatterbox.mtl_tts import T3,T3Config,S3Gen,VoiceEncoder,MTLTokenizer,ChatterboxMultilingualTTS
    if device!='cuda' or not torch.cuda.is_available():
        raise ValueError('Este loader regional solo está preparado para CUDA; no cambia a CPU automáticamente')
    free,total=torch.cuda.mem_get_info()
    if free<6*1024**3:raise ValueError('Memoria CUDA libre inferior al margen de 6 GiB; no se cargaron pesos')
    report=dict(profile_id=profile_id,device=device,free_bytes_before=free,total_bytes=total,components={},watermark=True)
    with torch.device(device):ve=VoiceEncoder()
    state=torch.load(row['voice_encoder']['path'],map_location=device,weights_only=True)
    report['components']['voice_encoder']=strict_state(ve,state)
    del state;ve.eval()
    with torch.device(device):t3=T3(T3Config.multilingual())
    state=load_file(row['main']['path'],device=device)
    report['components']['t3']=strict_state(t3,state)
    del state;t3.eval();gc.collect();torch.cuda.empty_cache()
    with torch.device(device):decoder=S3Gen()
    decoder.to(device)
    state=load_file(row['decoder']['path'],device=device)
    report['components']['decoder']=strict_state(decoder,state,('tokenizer._mel_filters','tokenizer.window'))
    del state;decoder.eval();gc.collect();torch.cuda.empty_cache()
    tokenizer=MTLTokenizer(row['tokenizer']['path'])
    model=ChatterboxMultilingualTTS(t3,decoder,ve,tokenizer,device,conds=None)
    if model.watermarker is None:raise ValueError('Perth no disponible; no se omite la marca de agua')
    report.update(loaded=True,sample_rate=model.sr,allocated_bytes=torch.cuda.memory_allocated(),
                  peak_allocated_bytes=torch.cuda.max_memory_allocated(),synthesis=False)
    return model,report


def generate_bounded(model,text,reference,max_new_tokens=160,**parameters):
    """Bound the upstream hardcoded 1000-token call without patching its source."""
    if not isinstance(text,str) or not text.strip() or len(text)>240:
        raise ValueError('La muestra regional requiere entre 1 y 240 caracteres')
    if type(max_new_tokens) is not int or not 32<=max_new_tokens<=512:
        raise ValueError('Presupuesto regional entre 32 y 512 tokens')
    original=model.t3.inference
    def limited(*args,**kwargs):
        kwargs['max_new_tokens']=min(kwargs.get('max_new_tokens',max_new_tokens),max_new_tokens)
        return original(*args,**kwargs)
    model.t3.inference=limited
    try:
        return model.generate(text,language_id='es',audio_prompt_path=str(reference),**parameters)
    finally:model.t3.inference=original
