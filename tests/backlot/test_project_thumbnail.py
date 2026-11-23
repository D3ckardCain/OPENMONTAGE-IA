import base64
import io

import pytest
from PIL import Image
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_studio as studio
from lib import production_agent as agent
from lib.packaging_options import save as save_packaging
from lib.project_thumbnail import current
from lib.editorial_freshness import research_index,current as is_current
from lib.project_channel_evidence import project_problem


def payload(width=640,height=360,color='red'):
    buffer=io.BytesIO()
    Image.new('RGB',(width,height),color).save(buffer,format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()


def test_thumbnail_checks_selection_integrity_and_render_freshness(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    pid=studio.create_production({'title':'Portada','brief':'Video propio',
        'pipeline':'animated-explainer','language':'es'})['project_id']
    options=[{'id':str(i),'title':f'Título {i}','overlay':'Texto',
        'visual_concept':'Imagen original','source_note':'Revisar derechos'} for i in (1,2)]
    selected=save_packaging(pid,{'options':options,'selected_id':'1','expected_revision':None})
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    url='/api/studio/project-thumbnail/'+pid
    assert client.get(url).json()['status']=='missing'
    assert client.post(url,json={'image_base64':payload(400,200),
        'expected_packaging_revision':selected['revision']}).status_code==400
    assert client.post(url,json={'image_base64':payload(),
        'expected_packaging_revision':'0'*64}).status_code==400
    image=client.post(url,json={'image_base64':payload(),
        'expected_packaging_revision':selected['revision']}).json()
    assert image['status']=='review' and image['width']==640 and image['selected_id']=='1'
    assert agent.LocalAgent(pid).dispatch('project_thumbnail',{})['sha256']==image['sha256']
    path=studio.project_path(pid)
    baseline=research_index(path)
    receipt={'status':'passed','finished_at':'2026-11-22T10:00:00+00:00','channel_research':baseline}
    assert is_current(receipt,[],None,baseline)
    studio.save_json(path/'render_verification.json',receipt)
    changed=client.post(url,json={'image_base64':payload(color='blue'),
        'expected_packaging_revision':selected['revision']}).json()
    assert changed['sha256']!=image['sha256']
    assert not is_current(receipt,[],None,research_index(path))
    file=path/'thumbnails'/changed['filename']
    file.write_bytes(b'changed')
    assert client.get(url).status_code==400
    assert project_problem(path) is not None
    with pytest.raises(ValueError,match='alterada'):agent.start(pid)


def test_thumbnail_missing_after_verification_blocks_queue(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    pid=studio.create_production({'title':'Portada','brief':'Video',
        'pipeline':'animated-explainer','language':'es'})['project_id']
    options=[{'id':str(i),'title':f'Título {i}','overlay':'',
        'visual_concept':'Imagen original','source_note':''} for i in (1,2)]
    chosen=save_packaging(pid,{'options':options,'selected_id':'1','expected_revision':None})
    from lib.project_thumbnail import stage
    stage(pid,{'image_base64':payload(),'expected_packaging_revision':chosen['revision']})
    project=studio.project_path(pid)
    studio.save_json(project/'render_verification.json',{'channel_research':research_index(project)})
    (project/'artifacts/thumbnail_review.json').unlink()
    assert project_problem(project) is not None
