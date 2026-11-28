"""New retrain gate regressions; no models or synthesis, no Spanish tests."""
import copy
import pytest
from lib.studio_piper import vctk_blocked, VCTK_RETRAINED_REVISION, VCTK_RETRAINED_SHA256


def bundle():
    return (dict(revision=VCTK_RETRAINED_REVISION, files=[dict(name='en_GB-vctk-medium.onnx', sha256=VCTK_RETRAINED_SHA256)]),
            dict(piper_version='1.5.0', num_speakers=109, speaker_id_map={str(i):i for i in range(109)}),
            'Finetuned from hifi_tts_92. Cori Samuel. Requires Piper 1.5 or higher.')


def test_exact_retrain_allows_synthesis():
    assert not vctk_blocked(*bundle())


@pytest.mark.parametrize('change', ['revision', 'hash', 'legacy_version', 'count', 'duplicate_id', 'range', 'lessac', 'missing_card'])
def test_drift_keeps_vctk_blocked(change):
    reference, config, card = copy.deepcopy(bundle())
    if change == 'revision': reference['revision'] = 'legacy'
    if change == 'hash': reference['files'][0]['sha256'] = '0'*64
    if change == 'legacy_version': config['piper_version'] = '1.0.0'
    if change == 'count': config['num_speakers'] = 108
    if change == 'duplicate_id': config['speaker_id_map']['108'] = 0
    if change == 'range': config['speaker_id_map']['108'] = 109
    if change == 'lessac': card += ' Finetuned from lessac.'
    if change == 'missing_card': card = ''
    assert vctk_blocked(reference, config, card)
