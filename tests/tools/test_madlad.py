from contextlib import nullcontext
from types import SimpleNamespace
import sys
import pytest
from lib import model_adapter_worker as worker


@pytest.mark.parametrize('mode',['valid','unknown','long'])
def test_madlad_worker_uses_only_local_t5_and_never_truncates(tmp_path,monkeypatch,mode):
    calls=[]
    class Batch(dict):
        def to(self,device):return self
    class Tokenizer:
        unk_token_id=0
        @classmethod
        def from_pretrained(cls,path,**kwargs):
            assert kwargs=={'local_files_only':True};calls.append('tokenizer');return cls()
        def convert_tokens_to_ids(self,value):assert value=='<2ko>';return 0 if mode=='unknown' else 42
        def __call__(self,text,**kwargs):
            assert text=='<2ko> Hello' and kwargs['truncation'] is False
            return Batch(input_ids=SimpleNamespace(shape=(1,513 if mode=='long' else 3)))
        def batch_decode(self,ids,**kwargs):return ['fixture translation']
    class Model:
        @classmethod
        def from_pretrained(cls,path,**kwargs):
            assert kwargs=={'local_files_only':True,'use_safetensors':True};calls.append('model');return cls()
        def to(self,device):return self
        def eval(self):return self
        def generate(self,**kwargs):assert kwargs['max_new_tokens']==512;return [[1]]
    monkeypatch.setitem(sys.modules,'transformers',SimpleNamespace(T5Tokenizer=Tokenizer,T5ForConditionalGeneration=Model))
    monkeypatch.setattr(worker,'torch_setup',lambda data:(SimpleNamespace(inference_mode=nullcontext),'cpu',None))
    request={'family':'madlad','model_dir':str(tmp_path),'output_dir':str(tmp_path),'inputs':{'text':'Hello','language':'ko'}}
    if mode=='valid':
        result=worker.run(request)
        assert result['result']['text']=='fixture translation'
        assert result['result']['quality_review_required'] is True
        assert calls==['tokenizer','model']
    else:
        with pytest.raises(ValueError):worker.run(request)
        assert calls==['tokenizer']
