"""Read-only regional voice preparation. No imports of Torch, YAML execution or Hub."""
import json
import hashlib
from importlib import metadata
from pathlib import Path
try:
    from lib.hyperframes_staging import identity
except ImportError:
    from hyperframes_staging import identity

ROOT=Path(__file__).resolve().parents[1]
MODEL_ROOT=Path('C:/OPENMONTAJE-IA/DESCARGAS_MODELOS')
CACHE=ROOT/'.runtime/voice-resources/verified-files.json'
SHARED=ROOT/'.backlot/studio/voice_resources.json'
QUALIFICATIONS=ROOT/'.runtime/chatterbox/qualifications.json'
PROFILES={
 'chatterbox-es-mx-latam':dict(folder='ResembleAI--Chatterbox-Multilingual-es-mx-latam',locale='es-MX/es-419',
   revision='27e595bf2fe7be0533ca299d9afafcde08b7cca7',filename='t3_es_mx_latam.safetensors',bytes=2143990280,
   sha256='c66c4517f11c2b35a56e28615c0689deb864cbc411e329552223bbd0a6a063f8'),
 'chatterbox-es-es':dict(folder='ResembleAI--Chatterbox-Multilingual-es-es',locale='es-ES',
   revision='7262b364e3222ba9446c9289e7485eadc47ed902',filename='t3_es_es.safetensors',bytes=2143990264,
   sha256='d85844b13ea8cb45e95b8d84a55bcfeccb2d743035cf304ee3d778fc6be39546'),
}
DECODER=dict(filename='s3gen_v3.safetensors',bytes=1056381804,
             sha256='4a46190f3dccc2230fbb3488a930bccc925862ee68f2662433dfcfe93ce6c2cb')
TOKENIZER_BLOB='d27fb3f2fd38ca39b7bbfbf83a13b3c617e551df'
COSY_WEIGHTS={
 'llm.pt':(2024669519,'69f43bd545131c30e98947fb360ea8b4dc9916d8e83dded7757c7ea4f5a24970'),
 'flow.pt':(1329116148,'a6fab32a7825e5b0bc855ddd948f8db9370b0a786fbc249caa4595e95b608e4b'),
 'hift.pt':(83202622,'b279d7641eb97ae55b3b540cfba4f953c26492a2df758328a89a4d007ab87a65'),
 'speech_tokenizer_v3.onnx':(969451503,'23236a74175dbdda47afc66dbadd5bcb41303c467a57c261cb8539ad9db9208d'),
 'campplus.onnx':(28303423,'a6ac6a63997761ae2997373e2ee1c47040854b4b759ea41ec48e4e42df0f4d73'),
 'CosyVoice-BlankEN/model.safetensors':(988097824,'130282af0dfa9fe5840737cc49a0d339d06075f83c5a315c3372c9a0740d0b96'),
}
COSY_AUX=['config.json','configuration.json','cosyvoice3.yaml',
 'CosyVoice-BlankEN/config.json','CosyVoice-BlankEN/generation_config.json',
 'CosyVoice-BlankEN/merges.txt','CosyVoice-BlankEN/tokenizer_config.json','CosyVoice-BlankEN/vocab.json']
COSY_AUX_BLOBS={
 'config.json':'9e26dfeeb6e641a33dae4961196235bdb965b21b',
 'configuration.json':'5e812fae901c12933ac69ebf3eb79d0eb49bbab4',
 'cosyvoice3.yaml':'2eda7e5007d99f6b17fbe7bd751cf54e3cde29ea',
 'CosyVoice-BlankEN/config.json':'463b055262b6c66c4629a74a4b300bfe2ed31d3c',
 'CosyVoice-BlankEN/generation_config.json':'dfc11073787daf1b0f9c0f1499487ab5f4c93738',
 'CosyVoice-BlankEN/merges.txt':'90d3d82d027eadcc6a5e77c38eb82d43fc51b53b',
 'CosyVoice-BlankEN/tokenizer_config.json':'ff55d7b9eb1384e5d4d7e75dc0f564c1a8833d6e',
 'CosyVoice-BlankEN/vocab.json':'4783fe10ac3adce15ac8f358ef5462739852c569',
}


def cached_auxiliaries(folder):
    """Receipt and current identity, without reading or executing YAML/model content."""
    try:
        if not CACHE.is_file() or CACHE.stat().st_size>1000000:return False
        rows=json.loads(CACHE.read_text(encoding='utf-8'))
        for name,blob in COSY_AUX_BLOBS.items():
            path=Path(folder)/name
            if not path.is_file() or Path(str(path)+'.fdmdownload').exists():return False
            row=rows.get(str(path.resolve()),{})
            if row.get('identity')!=identity(path) or row.get('git_blob_sha1')!=blob:return False
        return True
    except (OSError,ValueError,TypeError,AttributeError):return False


def cosyvoice_cpu_preflight(available_bytes=None):
    """Conservative allocation estimate, not a measurement of model peak usage."""
    if available_bytes is None:
        import os
        if os.name=='nt':
            import ctypes
            class Memory(ctypes.Structure):
                _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[
                    (name,ctypes.c_ulonglong) for name in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
            memory=Memory();memory.length=ctypes.sizeof(memory)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):available_bytes=memory.available
    pt=sum(size for name,(size,_) in COSY_WEIGHTS.items() if name.endswith('.pt'))
    onnx=sum(size for name,(size,_) in COSY_WEIGHTS.items() if name.endswith('.onnx'))
    blank=COSY_WEIGHTS['CosyVoice-BlankEN/model.safetensors'][0]
    required=2*pt+onnx+blank+1024**3
    return dict(available_physical_bytes=available_bytes,estimated_required_available_bytes=required,
                estimate_basis='2x PT checkpoint bytes + ONNX + transient BlankEN + 1GiB margin',
                headroom_ok=available_bytes>=required if available_bytes is not None else None,
                peak_measured=False,weights_loaded=False)


def chatterbox_runtime(site=None):
    """Inspect isolated distribution metadata only; installation is not qualification."""
    site=Path(site) if site else ROOT/'.runtime/chatterbox/venv/Lib/site-packages'
    expected={'torch':'2.6.0','torchaudio':'2.6.0','transformers':'5.2.0',
              'diffusers':'0.29.0','safetensors':'0.5.3','resemble-perth':'1.0.1'}
    installed={};observed={}
    if site.is_dir():
        for dist in metadata.distributions(path=[str(site)]):
            name=(dist.metadata.get('Name') or '').lower().replace('_','-')
            if name in expected:installed[name]=dist.version
            if name in ('s3tokenizer','numpy','librosa','tokenizers','conformer','pyloudnorm','omegaconf','chatterbox-tts'):
                observed[name]=dist.version
    matching=all(installed.get(name,'').split('+')[0]==version for name,version in expected.items())
    return dict(expected=expected,installed=installed,observed=observed,declared_core_versions_present=matching,
                imports_verified=False,loader_verified=False,weights_loaded=False,
                inspection='isolated_distribution_metadata_only')


def cosyvoice3(folder=None):
    discover=folder is None
    folder=Path(folder) if folder else MODEL_ROOT/'FunAudioLLM--Fun-CosyVoice3-0.5B-2512'
    weights={name:verified_file(folder/name,*value) for name,value in COSY_WEIGHTS.items()}
    problems=[name+': '+row['status'] for name,row in weights.items() if row['status']!='verified_cached']
    missing=[name for name in COSY_AUX if not (folder/name).is_file()]
    problems.extend('Auxiliar ausente: '+name for name in missing)
    problems.append('Runtime Windows independiente no acreditado; no cargar YAML/pt ni reutilizar dependencias Qwen incompatibles')
    cpu_preflight=cosyvoice_cpu_preflight()
    if cpu_preflight['headroom_ok'] is False:
        problems.append('RAM CPU disponible inferior al margen conservador estimado de '+str(cpu_preflight['estimated_required_available_bytes'])+' bytes; no cargar pesos')
    candidates=[]
    if discover and SHARED.is_file() and SHARED.stat().st_size<=16000:
        try:
            selected=json.loads(SHARED.read_text(encoding='utf-8')).get('cosyvoice3_candidate_root')
            if selected and Path(selected).is_absolute() and Path(selected).is_dir():
                found={name:verified_file(Path(selected)/name,*value) for name,value in COSY_WEIGHTS.items()}
                candidates.append(dict(path=selected,weights=found,
                    all_expected_sizes_present=all(r['status'] in ('verified_cached','unverified_or_changed') for r in found.values()),
                    all_weights_verified=all(r['status']=='verified_cached' for r in found.values()),
                    auxiliaries_verified=cached_auxiliaries(selected),
                    inference_verified=False))
        except (OSError,ValueError,TypeError):pass
    return dict(contract='cosyvoice3-standard-preparation-v1',revision='29e01c4e8d000f4bcd70751be16fa94bf3d85a18',
       code_revision='074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc',ready=False,weights=weights,missing_auxiliaries=missing,
       excluded_alternatives=['llm.rl.pt','flow.decoder.estimator.fp32.onnx','speech_tokenizer_v3.batch.onnx'],
       model_license_label='Apache-2.0',commercial_scope='unresolved_academic_examples_disclaimer_discussion19',
       evaluation_load_performed=False,yaml_executed=False,weights_read=False,problems=problems,
       all_weights_verified=all(r['status']=='verified_cached' for r in weights.values()),
       auxiliaries_verified=cached_auxiliaries(folder),
       existing_candidates=candidates,new_weight_downloads_recommended=False,
       cpu_preflight=cpu_preflight)


def verified_file(path,expected_bytes,sha):
    path=Path(path)
    if Path(str(path)+'.fdmdownload').exists() or path.suffix=='.fdmdownload':
        return {'status':'download_incomplete','path':str(path),'read':False}
    if not path.is_file():return {'status':'missing_or_queued','path':str(path),'read':False}
    value=identity(path)
    if value[2]!=expected_bytes:return {'status':'size_mismatch','path':str(path),'bytes':value[2],'read':False}
    try:
        if CACHE.is_file() and CACHE.stat().st_size>1000000:raise ValueError('Caché fuera de presupuesto')
        rows=json.loads(CACHE.read_text(encoding='utf-8')) if CACHE.exists() else {}
        row=rows.get(str(path.resolve()),{})
        status='verified_cached' if row.get('identity')==value and row.get('sha256')==sha else 'unverified_or_changed'
        return dict(status=status,path=str(path),bytes=value[2],read=False)
    except (OSError,ValueError,TypeError,AttributeError):
        return dict(status='verification_cache_unavailable',path=str(path),read=False)


def regional_signature(row,runtime):
    """Bind actual QA to resources and code metadata; never hash model content."""
    paths=[Path(row[k]['path']) for k in ('main','decoder','tokenizer','voice_encoder')]
    paths.append(ROOT/'lib/chatterbox_regional_runtime.py')
    paths.append(ROOT/'.runtime/chatterbox/venv/Scripts/python.exe')
    code=ROOT/'.runtime/chatterbox/venv/Lib/site-packages/chatterbox'
    paths.extend(sorted(code.rglob('*.py')) if code.is_dir() else [])
    payload=dict(profile_id=row['id'],model_revision=row['revision'],
                 source_revision='ab55923c27757c90cfcc407baa57dc25a7d25217',
                 installed=runtime['installed'],observed=runtime.get('observed',{}),files=[[str(p.resolve()),identity(p)] for p in paths])
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()


def regional_qualification(row,runtime):
    try:
        if not runtime['declared_core_versions_present'] or not QUALIFICATIONS.is_file() or QUALIFICATIONS.stat().st_size>32768:return None
        value=json.loads(QUALIFICATIONS.read_text(encoding='utf-8')).get(row['id'])
        if not value or value.get('signature')!=regional_signature(row,runtime):return None
        output=Path(value['output'])
        if not output.is_file() or identity(output)!=value['output_identity']:return None
        if value.get('success') is not True:return None
        return value
    except (OSError,ValueError,TypeError,KeyError,AttributeError):return None


def cached_sample(profile_id):
    """Recover an existing WAV independently of GPU/model availability."""
    if profile_id not in PROFILES and profile_id!='chatterbox-turbo-en':raise FileNotFoundError('Perfil de muestra desconocido')
    try:
        if not QUALIFICATIONS.is_file() or QUALIFICATIONS.stat().st_size>32768:raise ValueError('Recibo ausente')
        row=json.loads(QUALIFICATIONS.read_text(encoding='utf-8'))[profile_id]
        path=Path(row['output']).resolve()
        path.relative_to((ROOT/'projects').resolve())
        if path.suffix.lower()!='.wav' or not path.is_file() or identity(path)!=row['output_identity'] or row.get('success') is not True:
            raise ValueError('La muestra no coincide con su recibo')
        return path,dict(profile_id=profile_id,duration_seconds=row['duration_seconds'],sample_rate=row['sample_rate'],
                         origin='existing_completed_sample',new_synthesis=False,human_listening_performed=False)
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        raise FileNotFoundError('Muestra guardada no disponible: '+str(exc)) from exc


def saved_samples():
    """Completed receipts only; Turbo may appear later without another UI update."""
    result=[]
    labels={key:spec['locale'] for key,spec in PROFILES.items()}
    labels['chatterbox-turbo-en']='en · Turbo'
    for key,locale in labels.items():
        try:
            _,sample=cached_sample(key)
            result.append(dict(id=key,locale=locale,cached_sample={**sample,'available':True,
                'url':'/api/studio/editor/chatterbox/profiles/'+key+'/sample'}))
        except FileNotFoundError:pass
    return result


def catalog():
    runtime=chatterbox_runtime()
    try:
        if SHARED.is_file() and SHARED.stat().st_size>16000:raise ValueError('Registro compartido fuera de presupuesto')
        shared=json.loads(SHARED.read_text(encoding='utf-8')) if SHARED.is_file() else {}
    except (OSError,ValueError):shared={}
    rows=[]
    for key,spec in PROFILES.items():
        folder=MODEL_ROOT/spec['folder']
        main=verified_file(folder/spec['filename'],spec['bytes'],spec['sha256'])
        # Both regional official trees declare the same V3 decoder and tokenizer.
        decoder_paths=[folder/DECODER['filename'],*[MODEL_ROOT/p['folder']/DECODER['filename'] for p in PROFILES.values() if p!=spec]]
        decoder=next((p for p in decoder_paths if p.is_file()),decoder_paths[0])
        decoder_info=verified_file(decoder,DECODER['bytes'],DECODER['sha256'])
        tokenizer_paths=[folder/'grapheme_mtl_merged_expanded_v1.json',
            *[MODEL_ROOT/p['folder']/'grapheme_mtl_merged_expanded_v1.json' for p in PROFILES.values() if p!=spec]]
        if shared.get('chatterbox_tokenizer'):tokenizer_paths.append(Path(shared['chatterbox_tokenizer']))
        def cached_token(path):
            try:
                if not path.is_file() or not CACHE.is_file() or CACHE.stat().st_size>1000000:return False
                row=json.loads(CACHE.read_text(encoding='utf-8')).get(str(path.resolve()),{})
                return row.get('identity')==identity(path) and row.get('git_blob_sha1')==TOKENIZER_BLOB
            except (OSError,ValueError,TypeError):return False
        token=next((p for p in tokenizer_paths if cached_token(p)),next((p for p in tokenizer_paths if p.is_file()),tokenizer_paths[0]))
        ve=verified_file(Path(shared.get('chatterbox_voice_encoder') or folder/'ve.pt'),5698626,
            '4b16d836bc598509860f6fa068165a8bb5e9ac84f05582dfcf278a5a372879f1')
        problems=[]
        if main['status']!='verified_cached':problems.append('T3 regional: '+main['status'])
        if decoder_info['status']!='verified_cached':problems.append('Decoder V3 compartido: '+decoder_info['status'])
        if not cached_token(token):problems.append('Tokenizer compartido ausente/en cola o sin verificación; no duplicar descarga')
        if ve['status']!='verified_cached':problems.append('Voice encoder: '+ve['status'])
        problems.extend(['Loader regional V3 no acreditado: el from_local upstream revisado carga s3gen.pt, no s3gen_v3.safetensors',
            'Código alternativo del Space requiere revisión de licencia/atribuciones y compatibilidad Windows antes de instalar/cargar',
            'Perth/referencia autorizada y entorno de inferencia aún no acreditados'])
        row=dict(id=key,locale=spec['locale'],language_id='es',revision=spec['revision'],license='MIT model card',
            ready=False,preview_available=False,inference_verified=False,main=main,decoder=decoder_info,
            tokenizer=dict(path=str(token),present=token.is_file(),verified_cached=cached_token(token),official_git_blob=TOKENIZER_BLOB),
            voice_encoder=ve,
            shared_decoder_sha256=DECODER['sha256'],problems=problems,
            isolated_python_prepared=(ROOT/'.runtime/chatterbox/venv/Scripts/python.exe').is_file(),
            inference_dependencies_installed=runtime['declared_core_versions_present'],
            runtime_preparation=runtime,automatic_download=False,weights_read=False)
        qualification=regional_qualification(row,runtime)
        resources_ok=all(row[k]['status']=='verified_cached' for k in ('main','decoder','voice_encoder')) and row['tokenizer']['verified_cached']
        if qualification and resources_ok:
            row.update(ready=True,inference_verified=True,qualification=qualification,problems=[],
                       execution_scope='CUDA bounded Spanish sample, authorized reference required; regional Audio preview controls pending',
                       python_executable=str(ROOT/'.runtime/chatterbox/venv/Scripts/python.exe'))
        try:
            _,sample=cached_sample(key)
            row['cached_sample']={**sample,'available':True,'url':'/api/studio/editor/chatterbox/profiles/'+key+'/sample'}
        except FileNotFoundError:row['cached_sample']={'available':False}
        rows.append(row)
    return {'contract':'chatterbox-regional-preparation-v1','profiles':rows,'samples':saved_samples(),
        'note':'Reproduce muestras existentes sin sintetizar. La generación regional desde Audio sigue pendiente. Una muestra no acredita naturalidad. Sin fallback V2/Turbo inglés.'}


def guard_request(inputs):
    key=inputs.get('regional_profile')
    if key not in PROFILES:raise ValueError('Perfil regional Chatterbox desconocido')
    if inputs.get('language') not in ('es','Spanish','es-ES','es-MX','es-419'):
        raise ValueError('Perfil regional español; no cambia a inglés')
    row=next(row for row in catalog()['profiles'] if row['id']==key)
    if not row['ready']:raise ValueError('Chatterbox regional no preparado: '+'; '.join(row['problems']))
    if inputs.get('reference_authorized') is not True:raise ValueError('La referencia de voz requiere autorización explícita')
    if not inputs.get('reference_audio') or not Path(inputs['reference_audio']).is_file() or not Path(inputs['reference_audio']).stat().st_size:raise ValueError('Falta audio de referencia local autorizado')
    if inputs.get('device')!='cuda':raise ValueError('El perfil regional acreditado requiere CUDA; no cambia a CPU')
    if not isinstance(inputs.get('text'),str) or not inputs['text'].strip() or len(inputs['text'])>240:
        raise ValueError('La muestra regional requiere entre 1 y 240 caracteres')
    limit=inputs.get('max_new_tokens',160)
    if type(limit) is not int or not 32<=limit<=512:raise ValueError('Presupuesto regional entre 32 y 512 tokens')
    return row
