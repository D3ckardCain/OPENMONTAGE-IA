"""Offline fixtures; no rembg install, real weights or actual segmentation."""
import copy
import pytest
from lib import bg_remove_local as local
from tools.enhancement.bg_remove import BgRemove
from tests.tools.test_bg_remove_api import prepared


@pytest.mark.parametrize('case,code',[
    ('implicit_model','unsupported_model'),('cloud_model','unsupported_model'),
    ('no_review','license_unreviewed'),('nc','license_ineligible'),
    ('paid','license_ineligible'),('wrong_review','license_wrong_artifact'),
    ('floating_revision','license_unreviewed'),('wrong_hash','model_hash_mismatch'),
    ('missing_weight','missing_model'),('original_output','output_exists'),
    ('existing_output','output_exists'),('outside_project','path_outside_project'),
    ('bad_color','invalid_parameters'),('bad_matting','invalid_parameters')])
def test_failures_are_explicit_before_inference(prepared,case,code):
    data,provider,selected,project,source,weight=prepared;data=copy.deepcopy(data)
    if case=='implicit_model':data.pop('model')
    if case=='cloud_model':data['model']='bria-rmbg'
    if case=='no_review':data.pop('license_review')
    if case=='nc':data['license_review']['license_id']='CC-BY-NC-4.0'
    if case=='paid':data['license_review']['requires_paid_agreement']=True
    if case=='wrong_review':data['license_review']['model_sha256']='0'*64
    if case=='floating_revision':data['license_review']['revision']='main'
    if case=='wrong_hash':data['model_sha256']=data['license_review']['model_sha256']='0'*64
    if case=='missing_weight':data['model_path']=str(weight.with_name('absent.onnx'))
    if case=='original_output':data['output_path']=data['input_path']
    if case=='existing_output':(project/'assets/output.png').write_bytes(b'KEEP')
    if case=='outside_project':data['output_path']=str(project.parent/'outside.png')
    if case=='bad_color':data['bg_color']='#ZZYYXX'
    if case=='bad_matting':data['alpha_matting']='true'
    original=source.read_bytes();result=BgRemove().execute(data)
    assert not result.success and result.data['error_code']==code,result
    provider.remove.assert_not_called();provider.new_session.assert_not_called()
    assert not selected and source.read_bytes()==original and result.artifacts==[]
    if case=='existing_output':assert (project/'assets/output.png').read_bytes()==b'KEEP'


def test_cache_reuses_identity_and_rejects_modified_weight(prepared,monkeypatch):
    from lib import studio_editor as editor
    data,_,_,_,_,weight=prepared;actual=editor.digest;calls=[]
    def checked(path):calls.append(str(path));return actual(path)
    monkeypatch.setattr(editor,'digest',checked)
    local.preflight(data);local.preflight(data)
    assert len(calls)==2
    weight.write_bytes(b'MODIFIED DIFFERENT SIZE')
    result=BgRemove().execute(data)
    assert not result.success and result.data['error_code']=='model_hash_mismatch'
    assert len(calls)==3


def test_racing_output_is_not_overwritten_or_deleted(prepared):
    data,provider,_,project,_,_=prepared;output=project/'assets/output.png'
    def race(image,**kwargs):output.write_bytes(b'OTHER WRITER');return image.convert('RGBA')
    provider.remove.side_effect=race;result=BgRemove().execute(data)
    assert not result.success and not result.artifacts and output.read_bytes()==b'OTHER WRITER'


def test_changed_input_is_not_published(prepared):
    data,provider,_,project,source,_=prepared
    def changed(image,**kwargs):source.write_bytes(b'changed by simulated external writer');return image.convert('RGBA')
    provider.remove.side_effect=changed;result=BgRemove().execute(data)
    assert not result.success and not result.artifacts and not (project/'assets/output.png').exists()


def test_provider_error_preserves_original(prepared):
    data,provider,_,project,source,_=prepared;original=source.read_bytes()
    provider.remove.side_effect=RuntimeError('synthetic provider failure');result=BgRemove().execute(data)
    assert not result.success and 'synthetic provider failure' in result.error
    assert source.read_bytes()==original and not (project/'assets/output.png').exists()


def test_background_is_explicit_and_dimensions_recorded(prepared):
    data,_,_,_,_,_=prepared;data['bg_color']='#00FF00';data['alpha_matting']=True
    result=BgRemove().execute(data)
    assert result.success,result.error
    assert (result.data['width'],result.data['height'],result.data['mode'])==(8,8,'RGB')
    assert result.data['alpha_matting'] is True


def test_changed_weight_during_provider_call_is_not_published(prepared):
    data,provider,_,project,_,weight=prepared
    def changed(image,**kwargs):weight.write_bytes(b'CHANGED BY EXTERNAL WRITER');return image.convert('RGBA')
    provider.remove.side_effect=changed;result=BgRemove().execute(data)
    assert not result.success and result.data['error_code']=='model_hash_mismatch'
    assert not (project/'assets/output.png').exists()


def test_missing_alpha_is_not_reported_as_transparency(prepared):
    data,provider,_,project,_,_=prepared
    provider.remove.side_effect=lambda image,**kwargs:image.convert('RGB')
    result=BgRemove().execute(data)
    assert not result.success and 'alpha' in result.error
    assert not (project/'assets/output.png').exists()


def test_license_failure_does_not_read_model_or_source(prepared):
    data,provider,_,_,_,_=prepared;data['license_review']['commercial_use']='unknown'
    result=BgRemove().execute(data)
    assert not result.success and result.data['error_code']=='license_ineligible'
    assert local._hash.cache_info().misses==0
    provider.remove.assert_not_called()


def test_no_remote_parameter_is_accepted(prepared):
    data,provider,_,_,_,_=prepared;data['remote_url']='https://example.invalid/api'
    result=BgRemove().execute(data)
    assert not result.success and result.data['error_code']=='invalid_parameters'
    provider.remove.assert_not_called()
