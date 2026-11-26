"""Read-only regional voice preparation. No imports of Torch, YAML execution or Hub."""
import json
from pathlib import Path
try:
    from lib.hyperframes_staging import identity
except ImportError:
    from hyperframes_staging import identity

ROOT=Path(__file__).resolve().parents[1]
MODEL_ROOT=Path('C:/OPENMONTAJE-IA/DESCARGAS_MODELOS')
CACHE=ROOT/'.runtime/voice-resources/verified-files.json'
SHARED=ROOT/'.backlot/studio/voice_resources.json'
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


def cosyvoice3(folder=None):
    discover=folder is None
    folder=Path(folder) if folder else MODEL_ROOT/'FunAudioLLM--Fun-CosyVoice3-0.5B-2512'
    weights={name:verified_file(folder/name,*value) for name,value in COSY_WEIGHTS.items()}
    problems=[name+': '+row['status'] for name,row in weights.items() if row['status']!='verified_cached']
    missing=[name for name in COSY_AUX if not (folder/name).is_file()]
    problems.extend('Auxiliar ausente: '+name for name in missing)
    problems.append('Runtime Windows independiente no acreditado; no cargar YAML/pt ni reutilizar dependencias Qwen incompatibles')
    candidates=[]
    if discover and SHARED.is_file() and SHARED.stat().st_size<=16000:
        try:
            selected=json.loads(SHARED.read_text(encoding='utf-8')).get('cosyvoice3_candidate_root')
            if selected and Path(selected).is_absolute() and Path(selected).is_dir():
                found={name:verified_file(Path(selected)/name,*value) for name,value in COSY_WEIGHTS.items()}
                candidates.append(dict(path=selected,weights=found,
                    all_expected_sizes_present=all(r['status'] in ('verified_cached','unverified_or_changed') for r in found.values()),
                    inference_verified=False))
        except (OSError,ValueError,TypeError):pass
    return dict(contract='cosyvoice3-standard-preparation-v1',revision='29e01c4e8d000f4bcd70751be16fa94bf3d85a18',
       code_revision='074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc',ready=False,weights=weights,missing_auxiliaries=missing,
       excluded_alternatives=['llm.rl.pt','flow.decoder.estimator.fp32.onnx','speech_tokenizer_v3.batch.onnx'],
       model_license_label='Apache-2.0',commercial_scope='unresolved_academic_examples_disclaimer_discussion19',
       evaluation_load_performed=False,yaml_executed=False,weights_read=False,problems=problems,
       existing_candidates=candidates,new_weight_downloads_recommended=False)


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


def catalog():
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
        rows.append(dict(id=key,locale=spec['locale'],language_id='es',revision=spec['revision'],license='MIT model card',
            ready=False,preview_available=False,inference_verified=False,main=main,decoder=decoder_info,
            tokenizer=dict(path=str(token),present=token.is_file(),verified_cached=cached_token(token),official_git_blob=TOKENIZER_BLOB),
            voice_encoder=ve,
            shared_decoder_sha256=DECODER['sha256'],problems=problems,
            isolated_python_prepared=(ROOT/'.runtime/chatterbox/venv/Scripts/python.exe').is_file(),
            inference_dependencies_installed=False,automatic_download=False,weights_read=False))
    return {'contract':'chatterbox-regional-preparation-v1','profiles':rows,
        'note':'Preparación y diagnóstico; ninguna voz regional operativa acreditada. No usar el loader V2 ni Turbo inglés como fallback.'}


def guard_request(inputs):
    key=inputs.get('regional_profile')
    if key not in PROFILES:raise ValueError('Perfil regional Chatterbox desconocido')
    if inputs.get('language') not in ('es','Spanish','es-ES','es-MX','es-419'):
        raise ValueError('Perfil regional español; no cambia a inglés')
    row=next(row for row in catalog()['profiles'] if row['id']==key)
    raise ValueError('Chatterbox regional no preparado: '+'; '.join(row['problems']))
