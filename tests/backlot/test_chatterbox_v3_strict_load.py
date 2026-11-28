from types import SimpleNamespace
import pytest
from lib.chatterbox_regional_runtime import strict_state


class Module:
    def __init__(self):
        self.weight=SimpleNamespace(shape=(2,3))
        self.window=SimpleNamespace(shape=(4,))
        self.loaded=False
    def state_dict(self):return {'weight':self.weight,'window':self.window}
    def named_buffers(self):return [('window',self.window)]
    def load_state_dict(self,state,strict):
        assert strict is True and set(state)=={'weight','window'}
        assert state['window'] is self.window
        self.loaded=True


def test_only_derived_buffer_can_be_supplied_locally():
    module=Module()
    result=strict_state(module,{'weight':module.weight},derived=('window',))
    assert module.loaded and result['strict'] and result['derived_buffers']==['window']


def test_missing_weight_cannot_be_accepted_as_derived():
    module=Module()
    with pytest.raises(ValueError,match='ABI V3 incompatible'):
        strict_state(module,{},derived=('window','weight'))
    assert not module.loaded


def test_generation_budget_overrides_upstream_hardcoded_limit_and_restores():
    from lib.chatterbox_regional_runtime import generate_bounded
    calls=[]
    def original(**kwargs):calls.append(kwargs);return 'real-call-result'
    model=SimpleNamespace(t3=SimpleNamespace(inference=original))
    model.generate=lambda text,**kwargs:model.t3.inference(max_new_tokens=1000)
    assert generate_bounded(model,'Prueba','reference.wav',max_new_tokens=160)=='real-call-result'
    assert calls==[{'max_new_tokens':160}] and model.t3.inference is original
    def failing(text,**kwargs):
        model.t3.inference(max_new_tokens=1000)
        raise RuntimeError('fixture failure')
    model.generate=failing
    with pytest.raises(RuntimeError,match='fixture failure'):generate_bounded(model,'Prueba','reference.wav')
    assert model.t3.inference is original


def test_shape_mismatch_and_unexpected_key_fail_before_load():
    module=Module()
    with pytest.raises(ValueError,match='Formas V3 incompatibles'):
        strict_state(module,{'weight':SimpleNamespace(shape=(3,2))},derived=('window',))
    with pytest.raises(ValueError,match='ABI V3 incompatible'):
        strict_state(module,{'weight':module.weight,'surprise':module.weight},derived=('window',))
    assert not module.loaded
