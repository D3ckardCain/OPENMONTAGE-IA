import json
import wave
import pytest
from lib import voice_preparation as voices
from lib.hyperframes_staging import identity


@pytest.fixture
def sample(tmp_path,monkeypatch):
    monkeypatch.setattr(voices,'ROOT',tmp_path)
    monkeypatch.setattr(voices,'QUALIFICATIONS',tmp_path/'receipt.json')
    path=tmp_path/'projects'/'qa'/'voice.wav';path.parent.mkdir(parents=True)
    with wave.open(str(path),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(b'\0\0'*240)
    row=dict(output=str(path),output_identity=identity(path),success=True,duration_seconds=.01,sample_rate=24000)
    voices.QUALIFICATIONS.write_text(json.dumps({'chatterbox-es-es':row}))
    return path,row


def test_saved_sample_does_not_require_models_or_gpu(sample,monkeypatch):
    monkeypatch.setattr(voices,'chatterbox_runtime',lambda:pytest.fail('No runtime discovery for audio recovery'))
    path,report=voices.cached_sample('chatterbox-es-es')
    assert path==sample[0] and not report['new_synthesis']


def test_changed_or_unknown_sample_is_rejected(sample):
    with pytest.raises(FileNotFoundError):voices.cached_sample('unknown')
    sample[0].write_bytes(b'changed-fixture')
    with pytest.raises(FileNotFoundError,match='recibo'):voices.cached_sample('chatterbox-es-es')


def test_receipt_cannot_expose_file_outside_projects(sample,tmp_path):
    outside=tmp_path/'outside.wav';outside.write_bytes(b'fixture')
    row={**sample[1],'output':str(outside),'output_identity':identity(outside)}
    voices.QUALIFICATIONS.write_text(json.dumps({'chatterbox-es-es':row}))
    with pytest.raises(FileNotFoundError):voices.cached_sample('chatterbox-es-es')


def test_turbo_is_listed_only_with_completed_audio_receipt(sample):
    assert [r['id'] for r in voices.saved_samples()]==['chatterbox-es-es']
    voices.QUALIFICATIONS.write_text(json.dumps({'chatterbox-turbo-en':sample[1]}))
    rows=voices.saved_samples()
    assert len(rows)==1 and rows[0]['id']=='chatterbox-turbo-en' and rows[0]['locale']=='en · Turbo'
    assert not rows[0]['cached_sample']['new_synthesis']
