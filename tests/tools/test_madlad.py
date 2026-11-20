from contextlib import nullcontext
from types import SimpleNamespace
import sys
import pytest
from lib import model_adapter_worker as worker


@pytest.mark.parametrize('mode',['valid','unknown','long','segmented','cut'])
def test_madlad_worker_uses_only_local_t5_and_never_truncates(tmp_path,monkeypatch,mode):
    calls=[];generated=[]
    class Batch(dict):
        def to(self,device):return self
    class Tokenizer:
        unk_token_id=0
        eos_token_id=1
        def encode(self,text,**kwargs):return [1]*(513 if mode=='long' else len(text))
        @classmethod
        def from_pretrained(cls,path,**kwargs):
            assert kwargs=={'local_files_only':True};calls.append('tokenizer');return cls()
        def convert_tokens_to_ids(self,value):assert value=='<2ko>';return 0 if mode=='unknown' else 42
        def __call__(self,text,**kwargs):
            assert text.startswith('<2ko> ') and kwargs['truncation'] is False
            return Batch(input_ids=SimpleNamespace(shape=(1,513 if mode=='long' else 3)))
        def batch_decode(self,ids,**kwargs):return ['fixture translation']
    class Model:
        @classmethod
        def from_pretrained(cls,path,**kwargs):
            assert kwargs=={'local_files_only':True,'use_safetensors':True};calls.append('model');return cls()
        def to(self,device):return self
        def eval(self):return self
        def generate(self,**kwargs):
            assert kwargs['max_new_tokens']==512;generated.append(kwargs);return [[99 if mode=='cut' else 1]]
    monkeypatch.setitem(sys.modules,'transformers',SimpleNamespace(T5Tokenizer=Tokenizer,T5ForConditionalGeneration=Model))
    monkeypatch.setattr(worker,'torch_setup',lambda data:(SimpleNamespace(inference_mode=nullcontext),'cpu',None))
    text='Hello '*200 if mode=='segmented' else 'Hello'
    request={'family':'madlad','model_dir':str(tmp_path),'output_dir':str(tmp_path),'inputs':{'text':text,'language':'ko'}}
    if mode in ('valid','segmented'):
        result=worker.run(request)
        assert all(chunk['translation']=='fixture translation' for chunk in result['result']['segments'])
        assert ''.join(chunk['text'] for chunk in result['result']['segments'])==text
        assert len(generated)>1 if mode=='segmented' else len(generated)==1
        assert result['result']['quality_review_required'] is True
        assert calls==['tokenizer','model']
    else:
        with pytest.raises(ValueError):worker.run(request)
        assert calls==(['tokenizer','model'] if mode=='cut' else ['tokenizer'])
