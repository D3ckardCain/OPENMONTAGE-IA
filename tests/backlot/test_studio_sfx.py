"""New local SFX contract with explicit synthetic non-audio fixtures."""
import hashlib
import uuid
import zipfile
from copy import deepcopy
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import studio_editor as edit, production_studio as studio
from lib import studio_sfx as sfx, studio_sfx_catalog as catalog
from tests.backlot.test_studio_editor import project,command,add


@pytest.fixture
def sounds(project,tmp_path,monkeypatch):
    pid,key,_=project;add(pid,key)
    config=tmp_path/'config';monkeypatch.setattr(studio,'CONFIG_DIR',config)
    archive=tmp_path/'explicit-fixture.zip';data=b'non-audio offline SFX fixture; never AV evidence';sha=hashlib.sha256(data).hexdigest()
    with zipfile.ZipFile(archive,'w') as z:z.writestr('test/impact.ogg',data)
    row={'id':'sfx-'+sha,'sha256':sha,'bytes':len(data),'duration':.5,'channels':1,'sample_rate':48000,
        'kind':'audio','audio':True,'name':'Synthetic impact','category':'impact','category_es':'Impacto',
        'library':'Explicit offline fixture','license':'CC0-1.0','license_evidence':'synthetic_test_not_real_asset',
        'aliases':[{'file':'impact.ogg','archive_entry':'test/impact.ogg','author':'Synthetic fixture',
                    'source_url':'https://example.com/test','git_blob':catalog.git_blob(data)}]}
    manifest={'revision':catalog.REVISION,'repository':catalog.REPOSITORY,'archive':str(archive),
        'archive_identity':catalog.identity(archive),'source_files':1,'assets':[row],'license_text':'Synthetic test license, not real SFX evidence'}
    studio.save_json(config/'sfx-catalog.json',manifest)
    return pid,row,archive,config


def payload(pid,row,**extra):
    return {'request_id':uuid.uuid4().hex,'revision':edit.state(pid)['revision'],'asset_id':row['id'],
            'start_seconds':1,'in_seconds':0,'out_seconds':.4,'gain':.5,**extra}


def test_catalog_search_pagination_and_favorites_never_materialize(sounds,monkeypatch):
    pid,row,archive,config=sounds
    monkeypatch.setattr(catalog.zipfile,'ZipFile',lambda *a,**k: (_ for _ in ()).throw(AssertionError('No archive content read while browsing')))
    assert catalog.catalog('impacto')['total']==1
    assert catalog.catalog('not present')['total']==0
    assert catalog.catalog(ids=[])['total']==0
    assert catalog.catalog(offset=1)['items']==[]
    assert not (config/'sfx-preview-cache').exists()


def test_insert_receipt_is_idempotent_across_stale_revision_and_undo(sounds):
    pid,row,_,_=sounds;data=payload(pid,row);value=sfx.insert(pid,data)
    assert value['sfx_receipt']['currently_applied']
    assert sfx.insert(pid,data)['revision']==value['revision']
    assert len(edit.state(pid)['edit_decisions']['audio_tracks'])==1
    before=edit.state(pid)
    with pytest.raises(edit.Conflict):sfx.insert(pid,{**data,'gain':.7})
    assert edit.state(pid)==before
    command(pid,'undo');assert not sfx.insert(pid,data)['sfx_receipt']['currently_applied']
    assert not edit.state(pid)['edit_decisions']['audio_tracks']


def test_frozen_source_license_history_and_new_insert_after_undo(sounds):
    pid,row,_,_=sounds;first=sfx.insert(pid,payload(pid,row));source=first['edit_decisions']['sources'][first['sfx_receipt']['source_id']]
    path=studio.project_path(pid)/source['path'];identity=catalog.identity(path)
    assert (studio.project_path(pid)/source['sfx_provenance']['license_path']).is_file()
    command(pid,'undo');command(pid,'redo');command(pid,'save')
    assert edit.state(pid)['edit_decisions']['audio_tracks'][0]['sfx_catalog_id']==row['id']
    command(pid,'undo');sfx.insert(pid,payload(pid,row,start_seconds=2))
    assert catalog.identity(path)==identity
    assert len(list((studio.project_path(pid)/'assets/sfx').glob('*.ogg')))==1
    assert len(edit.state(pid)['edit_decisions']['audio_tracks'])==1


def test_bad_insert_does_not_copy_or_mutate_project(sounds):
    pid,row,_,_=sounds
    for extra in ({'gain':True},{'start_seconds':9.8},{'out_seconds':.6},{'out_seconds':.0005},
                  {'asset_id':'../secret'},{'extra':'unexpected'}):
        before=edit.state(pid)
        with pytest.raises((ValueError,edit.Conflict)):sfx.insert(pid,payload(pid,row,**extra))
        assert edit.state(pid)==before
    assert not (studio.project_path(pid)/'assets/sfx').exists()


def test_project_favorites_do_not_change_av_identity_or_other_projects(sounds):
    pid,row,_,_=sounds;before=edit.state(pid)
    value=command(pid,'sfx_favorites',ids=[row['id']])
    assert value['render_sha256']==before['render_sha256']
    other=edit.create('Separate project')['project_id']
    assert not edit.state(other)['edit_decisions'].get('sfx_favorites')
    command(pid,'undo');assert edit.state(pid)['edit_decisions']==before['edit_decisions']


def test_changed_missing_archive_and_cache_are_clear_errors(sounds):
    pid,row,archive,config=sounds;path,_=catalog.materialize(row['id']);assert path.is_file()
    path.write_bytes(b'changed private cache')
    with pytest.raises(ValueError,match='Caché'):catalog.materialize(row['id'])
    archive.unlink()
    assert not catalog.catalog()['available']
    with pytest.raises(ValueError):catalog.materialize(row['id'])


def test_existing_preparation_uses_identity_without_rehash(sounds,monkeypatch):
    _,_,archive,config=sounds
    monkeypatch.setattr(catalog.hashlib,'sha256',lambda *a: (_ for _ in ()).throw(AssertionError('Do not repeat verified hashes')))
    result=catalog.prepare(archive,config/'sfx-catalog.json')
    assert result['reused'] and result['new_hashes']==0


def test_agent_catalog_insert_receipt_and_ui_capability(sounds,monkeypatch):
    from tools.video import studio_project_edit as bridge
    pid,row,_,_=sounds;client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    def transport(path,data=None):
        response=client.get('/api/studio/editor/'+path) if data is None else client.post('/api/studio/editor/'+path,json=data)
        assert response.status_code==200,response.text
        return response.json()
    monkeypatch.setattr(bridge,'request',transport);tool=bridge.StudioProjectEdit()
    assert 'sfx_catalog' in client.get('/api/studio/editor/capabilities').json()['commands']
    assert tool.execute({'project_id':pid,'action':'sfx_catalog','sfx':{'q':'impacto'}}).data['total']==1
    data=payload(pid,row);result=tool.execute({'project_id':pid,'action':'sfx_insert','sfx':data})
    assert result.success and edit.state(pid)['events'][-1]['origin']=='agent'
    assert tool.execute({'project_id':pid,'action':'sfx_receipt','request_id':data['request_id']}).data['sfx_receipt']['currently_applied']


def test_ogg_header_bounds_are_checked_without_decoding():
    import struct
    ident=b'\x01vorbis'+struct.pack('<I',0)+bytes([1])+struct.pack('<I',48000)+b'\0'*14
    header=b'OggS'+bytes([0,6])+struct.pack('<QII',48000,123,0)+b'\0'*4+bytes([1,len(ident)])
    result=catalog.ogg_info(header+ident)
    assert result['duration']==1 and result['sample_rate']==48000
    with pytest.raises(ValueError):catalog.ogg_info((header+ident)[:-1])


def test_short_click_is_not_rejected_by_video_frame_duration(sounds):
    pid,row,_,_=sounds
    value=sfx.insert(pid,payload(pid,row,out_seconds=.03))
    assert value['edit_decisions']['audio_tracks'][0]['out_seconds']==.03


def test_spanish_common_tags_match_english_filename_without_model(sounds):
    _,_,_,config=sounds;value=studio.read_json(config/'sfx-catalog.json')
    value['assets'][0]['name']='Kenney impactpunch heavy 000'
    studio.save_json(config/'sfx-catalog.json',value)
    assert catalog.catalog('puñetazo fuerte')['total']==1
