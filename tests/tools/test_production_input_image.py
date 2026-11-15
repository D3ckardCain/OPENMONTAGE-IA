import base64
import io

import pytest
from PIL import Image
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_studio as studio
from lib.production_input_image import stage_image


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(studio, 'PROJECTS_DIR', tmp_path)
    studio.save_json(tmp_path/'one'/'production_request.json', {})
    return tmp_path/'one'


def encoded(fmt='PNG'):
    data=io.BytesIO();Image.new('RGB',(64,32),'red').save(data,format=fmt)
    return {'image_base64':base64.b64encode(data.getvalue()).decode()}


@pytest.mark.parametrize('fmt', ['PNG','JPEG'])
def test_image_is_validated_persisted_and_reused(project,fmt):
    first=stage_image('one',encoded(fmt))
    assert first['width']==64 and first['height']==32
    assert first['comfyui_uploaded'] is False and first['generation_started'] is False
    assert stage_image('one',encoded(fmt))==first
    assert len(list((project/'source_images').glob('*')))==1


@pytest.mark.parametrize('data',[{'image_base64':'%%%'},{'image_base64':''},
    {'image_base64':base64.b64encode(b'<html>not an image</html>').decode()},encoded('GIF')])
def test_invalid_image_does_not_replace_source(project,data):
    first=stage_image('one',encoded())
    with pytest.raises(ValueError):stage_image('one',data)
    assert studio.read_json(project/'source_image.json')==first


def test_route_never_contacts_comfyui(project,monkeypatch):
    import requests
    def forbidden(*args,**kwargs):raise AssertionError('No network allowed')
    monkeypatch.setattr(requests.sessions.Session,'request',forbidden)
    with TestClient(create_app(),base_url='http://127.0.0.1:4750') as client:
        url='/api/studio/source-images/one'
        assert client.get(url).json()['image'] is None
        saved=client.post(url,json=encoded())
        assert saved.status_code==200
        assert client.get(url).json()['image']==saved.json()
        assert client.post('/api/studio/source-images/missing',json=encoded()).status_code==404
