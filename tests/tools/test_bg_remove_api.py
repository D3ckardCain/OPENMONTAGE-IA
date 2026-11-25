"""Existing selection regression, updated for the explicit local-only contract."""
import hashlib
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock
import pytest
from PIL import Image
from lib import production_studio as studio, bg_remove_local as local
from tools.enhancement.bg_remove import BgRemove


@pytest.fixture
def prepared(monkeypatch, tmp_path):
    project=tmp_path/'projects/bg-test';(project/'assets').mkdir(parents=True)
    (project/'production_request.json').write_text('{}',encoding='utf-8')
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    source=project/'assets/input.png';Image.new('RGB',(8,8),(10,20,30)).save(source)
    weight=tmp_path/'prepared.onnx';weight.write_bytes(b'SYNTHETIC NOT AN ONNX MODEL')
    sha=hashlib.sha256(weight.read_bytes()).hexdigest()
    data={'project_id':'bg-test','input_path':'assets/input.png','output_path':'assets/output.png',
        'model':'isnet-general-use','model_path':str(weight),'model_sha256':sha,
        'license_review':{'status':'reviewed','commercial_use':'yes','requires_paid_agreement':False,
            'license_id':'Apache-2.0','license_url':'https://example.invalid/fixture/LICENSE',
            'source_url':'https://example.invalid/fixture/model.onnx','revision':'fixture-v1','model_sha256':sha}}
    provider=ModuleType('rembg')
    provider.new_session=MagicMock(side_effect=AssertionError('No default factory/download allowed'))
    provider.remove=MagicMock(side_effect=lambda image,**kwargs:image.convert('RGBA'))
    selected=[]
    def model_class(name):
        class Session:
            @classmethod
            def name(cls):return name
            @classmethod
            def download_models(cls,*args,**kwargs):raise AssertionError('Upstream download hook must never run')
            def __init__(self,model,options,**kwargs):
                self.path=self.__class__.download_models()
                self.inner_session=SimpleNamespace(get_providers=lambda:kwargs['providers'])
                selected.append((model,self.path))
        return Session
    monkeypatch.setitem(sys.modules,'rembg',provider)
    monkeypatch.setitem(sys.modules,'onnxruntime',SimpleNamespace(SessionOptions=SimpleNamespace))
    for name,(module,cls) in local.MODELS.items():
        fake=ModuleType('rembg.sessions.'+module);setattr(fake,cls,model_class(name));monkeypatch.setitem(sys.modules,fake.__name__,fake)
    local._hash.cache_clear()
    return data,provider,selected,project,source,weight


def test_bg_remove_selects_prepared_session_without_default_factory(prepared):
    data,provider,selected,project,source,_=prepared;original=source.read_bytes()
    result=BgRemove().execute(data)
    assert result.success,result.error
    assert selected==[('isnet-general-use',data['model_path'])]
    provider.new_session.assert_not_called()
    kwargs=provider.remove.call_args.kwargs
    assert 'model_name' not in kwargs and kwargs['session'].path==data['model_path']
    assert result.data['provenance']['model_sha256']==data['model_sha256']
    assert result.data['provenance']['input_sha256']==hashlib.sha256(original).hexdigest()
    assert result.data['provenance']['output_sha256']==hashlib.sha256((project/'assets/output.png').read_bytes()).hexdigest()
    assert result.data['provenance']['license_status']=='operator_declared_not_independently_verified'
    assert result.data['mode']=='RGBA' and source.read_bytes()==original
