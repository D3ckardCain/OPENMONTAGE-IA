"""CPU-only isolated synthesis with explicit files and network disabled."""
import hashlib
import importlib.metadata
import json
import sys
import wave
from pathlib import Path
from lib.model_adapter_worker import block_network


def main():
    data = json.load(sys.stdin)
    block_network()
    from piper import PiperVoice, SynthesisConfig
    version = importlib.metadata.version('piper-tts')
    if tuple(map(int, version.split('.')[:2])) < (1, 5):
        raise ValueError('Piper >=1.5 required')
    model = Path(data['model'])
    # Verify each small bundle at use time, including its exact model card.
    for reference in data['references']['files']:
        file = model.parent / reference['name']
        with file.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if file.stat().st_size != reference['bytes'] or digest != reference['sha256']:
            raise ValueError('Resource changed: ' + reference['name'])
    voice = PiperVoice.load(model, config_path=str(model) + '.json', use_cuda=False)
    with open(data['output'], 'xb') as stream:
        with wave.open(stream, 'wb') as wav:
            voice.synthesize_wav(data['text'], wav, SynthesisConfig(speaker_id=data['speaker_id']))
    with wave.open(data['output'], 'rb') as wav:
        result = dict(output=data['output'], frames=wav.getnframes(), sample_rate=wav.getframerate(),
                      seconds=wav.getnframes()/wav.getframerate(), speaker_id=data['speaker_id'],
                      piper_version=version, provenance=data['references'], listening_validated=False)
    result['text_sha256'] = hashlib.sha256(data['text'].encode('utf-8')).hexdigest()
    with Path(data['output']).open('rb') as stream:
        result['wave_sha256'] = hashlib.file_digest(stream,'sha256').hexdigest()
    Path(data['output'] + '.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
