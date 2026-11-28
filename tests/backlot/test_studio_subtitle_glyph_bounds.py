from pathlib import Path
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from backlot.server import create_app
from lib import studio_subtitle_glyph_bounds as glyphs, studio_editor as editor
from tests.backlot.test_studio_editor import project, add


def edl(mode='burn'):
    return {'output':{'ratio':'custom','width':160,'height':128},
            'subtitle_style':{'mode':mode,'size':120,'position':'bottom'},
            'subtitle_layout':{'safe_area':{'left':.1,'right':.1,'top':.1,'bottom':.1}},
            'cues':[{'start_seconds':2,'end_seconds':3,'text':'No borrar la negación.'}]}


def test_measures_pixel_bbox_with_temporary_ass_and_persists_nothing(monkeypatch):
    seen={};frame=bytearray(160*128)
    for y in range(20,28):
        for x in range(44,89):frame[y*160+x]=220
    class Result:
        returncode=0
        stdout=bytes(frame)
        stderr=b''
    def run(args,**kwargs):
        seen['args']=args;seen['kwargs']=kwargs
        seen['ass']=Path(kwargs['cwd'],'cue.ass').read_text(encoding='utf-8')
        assert args[args.index('-i')+1]=='color=c=black:s=160x128:r=1:d=1'
        return Result()
    monkeypatch.setattr(glyphs,'require_media',lambda name:'/local/ffmpeg')
    monkeypatch.setattr(glyphs.subprocess,'run',run)
    result=glyphs.measure(edl(),0)
    assert result['bbox']==[44,20,89,28]
    assert result['fits_safe_area'] is True
    assert result['safe_rect']==[16,13,144,115]
    assert 'No borrar la negación.' in seen['ass']
    assert seen['args'][-1]=='pipe:1'
    assert not Path(seen['kwargs']['cwd']).exists()


def test_outside_bbox_is_reported_without_changing_edl(monkeypatch):
    source=edl();before=deepcopy(source);frame=bytearray(160*90);frame[5*160+5]=255
    monkeypatch.setattr(glyphs,'require_media',lambda name:'/local/ffmpeg')
    monkeypatch.setattr(glyphs.subprocess,'run',lambda *a,**k:type('Result',(),{
        'returncode':0,'stdout':bytes(frame),'stderr':b''})())
    result=glyphs.measure(source,0)
    assert result['fits_safe_area'] is False and result['bbox']==[5,5,6,6]
    assert source==before


def test_nonburn_empty_bad_index_and_large_resolution_fail_before_ffmpeg(monkeypatch):
    calls=[]
    monkeypatch.setattr(glyphs.subprocess,'run',lambda *a,**k:calls.append(a))
    with pytest.raises(ValueError,match='quemados'):glyphs.measure(edl('soft'),0)
    with pytest.raises(ValueError,match='No existe'):glyphs.measure(edl(),1)
    huge=edl();huge['output'].update(width=8192,height=4096)
    with pytest.raises(ValueError,match='límite'):glyphs.measure(huge,0)
    assert calls==[]


def test_quality_api_returns_editor_revision_and_measurement(project,monkeypatch):
    pid,key,_=project
    add(pid,key)
    monkeypatch.setattr(glyphs,'measure',lambda state,index:{
        'status':'measured','bbox':[10,10,30,20],'safe_rect':[8,8,56,56],
        'fits_safe_area':True,'width':64,'height':64,'pixel_threshold':32})
    client=TestClient(create_app(),base_url='http://127.0.0.1')
    response=client.get(f'/api/studio/editor/{pid}/subtitles/quality/cues/0/glyphs')
    assert response.status_code==200,response.text
    assert response.json()['revision']==editor.state(pid)['revision']
    assert response.json()['cue_index']==0 and response.json()['bbox']==[10,10,30,20]
