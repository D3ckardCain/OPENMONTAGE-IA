"""Filesystem fixtures only: no discovery candidates or model engines execute."""
from pathlib import Path
import pytest
from lib import setup_center as setup
from lib import production_studio as studio
from lib import model_adapters as adapters


@pytest.fixture
def isolated(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    studio.PROJECTS_DIR.mkdir()
    return tmp_path


def file(root,relative):
    path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'not executed fixture')
    return path


def test_discovery_separates_installers_and_never_executes_or_applies(isolated,monkeypatch):
    executable=file(isolated,'tools/solvespace_single_core_x64.exe')
    installer=file(isolated,'downloads/Avogadro2-2.1.0-win64.exe')
    python=file(isolated,'ComfyUI/python_embeded/python.exe')
    file(isolated,'DESCARGAS_MODELOS/weights/python.exe')
    def forbidden(*args,**kwargs):raise AssertionError('No execution or configuration during discovery')
    monkeypatch.setattr(setup.applications,'configure',forbidden)
    monkeypatch.setattr(setup.applications.subprocess,'Popen',forbidden)
    result=setup.discover({'roots':[str(isolated)]})
    solve=next(a for a in result['applications'] if a['id']=='solvespace')
    assert solve['candidates']==[str(executable)] and solve['recommendation']==str(executable)
    assert result['installers_not_executed']==[str(installer)]
    assert result['python_candidates']==[str(python)]
    assert not result['configuration_changed'] and result['executed_files']==0
    assert not (studio.CONFIG_DIR/'applications.json').exists()


def test_ambiguous_candidates_do_not_recommend_or_replace_current_path(isolated):
    old=file(isolated,'old/ffmpeg.exe');new=file(isolated,'new/ffmpeg.exe')
    setup.applications.configure('ffmpeg',{'executable':str(old)})
    result=setup.discover({'roots':[str(isolated)]})
    ffmpeg=next(a for a in result['applications'] if a['id']=='ffmpeg')
    assert set(ffmpeg['candidates'])=={str(old),str(new)}
    assert ffmpeg['recommendation'] is None
    assert studio.settings()['ffmpeg_path']==str(old)


def test_offline_root_and_scan_limits_are_explicit(isolated,monkeypatch):
    for i in range(8):file(isolated,f'file{i}.txt')
    monkeypatch.setattr(setup,'MAX_ENTRIES',3)
    result=setup.discover({'roots':[str(isolated),str(isolated/'offline')]})
    assert result['limited'] and result['entries_examined']==3
    assert result['roots'][1]['available'] is False
    with pytest.raises(ValueError):setup.discover({'roots':['relative']})


def test_discovery_does_not_follow_links_outside_selected_roots(isolated):
    outside=isolated.parent/(isolated.name+'-outside');outside.mkdir()
    file(outside,'ffmpeg.exe')
    try:(isolated/'link').symlink_to(outside,target_is_directory=True)
    except OSError:pytest.skip('No se permiten enlaces en este sistema')
    result=setup.discover({'roots':[str(isolated)]})
    assert not next(a for a in result['applications'] if a['id']=='ffmpeg')['candidates']


def test_setup_report_has_all_families_without_import_probes_or_model_loads(isolated,monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('Dependency probe must not run')
    monkeypatch.setattr(adapters,'dependency_probe',forbidden)
    result=setup.report()
    assert result['total_families']==48 and result['prepared_recipes']==48
    assert not any(row['dependency_probe_performed'] or row['installation_started'] or row['environment_created'] for row in result['models'])
    assert result['model_loads_started']==0
    setup.save_report()
    assert studio.read_json(studio.CONFIG_DIR/'setup-report.json')['total_families']==48


def test_framepack_config_is_created_from_existing_auxiliary_folders(isolated):
    backbone=isolated/'backbone';vision=isolated/'vision'
    for name in ['text_encoder','text_encoder_2','tokenizer','tokenizer_2','vae']:(backbone/name).mkdir(parents=True)
    for name in ['image_encoder','feature_extractor']:(vision/name).mkdir(parents=True)
    data={'backbone_dir':str(backbone),'vision_dir':str(vision)}
    result=setup.save_runtime_settings('framepack',data)
    assert result['generation_started'] is False and result['model_files_moved'] is False
    config=Path(adapters.configuration('framepack')['runtime_config'])
    assert studio.read_json(config)==data
    assert setup.read_runtime_settings('framepack')['values']==data
    old=config.read_bytes()
    with pytest.raises(ValueError):setup.save_runtime_settings('framepack',{**data,'vision_dir':str(isolated/'offline')})
    assert config.read_bytes()==old


def test_magihuman_config_preserves_all_local_paths(isolated):
    data={}
    for name in ['distill_dir','audio_model_path','txt_model_path','vae_model_path']:
        path=isolated/name;path.mkdir();data[name]=str(path)
    data['student_config_path']=str(file(isolated,'turbo/config.json'))
    studio.save_json(data['student_config_path'],{'fixture_config':True})
    data['student_ckpt_path']=str(file(isolated,'turbo/weights.ckpt'))
    result=setup.save_runtime_settings('magihuman',data)
    cfg=studio.read_json(result['runtime_config'])
    assert cfg['engine_config']=={'load':data['distill_dir'],'distill':True,'cp_size':1}
    assert cfg['evaluation_config']['txt_model_path']==data['txt_model_path']
    assert cfg['evaluation_config']['student_ckpt_path']==data['student_ckpt_path']
    assert setup.read_runtime_settings('magihuman')['values']==data
    with pytest.raises(ValueError):setup.save_runtime_settings('magihuman',{**data,'unexpected':'/somewhere'})


def test_agent_can_read_setup_report_without_mutating_configuration(isolated):
    from tools.desktop.application_center import LocalSetupReport
    result=LocalSetupReport().execute({})
    assert result.success and result.data['total_families']==48
    assert not LocalSetupReport().execute({'run_models':True}).success
    assert not studio.CONFIG_DIR.exists()


def test_configured_ffmpeg_is_used_in_runtime_status_even_without_path(isolated,monkeypatch):
    exe=file(isolated,'tools/ffmpeg.exe');studio.configure({'ffmpeg_path':str(exe)})
    monkeypatch.setattr(studio.shutil,'which',lambda name:None)
    def offline(*args,**kwargs):raise OSError('offline server fixture')
    monkeypatch.setattr(studio,'local_request',offline)
    report=studio.runtime_status()
    assert report['ffmpeg_ready'] is True
    assert not report['inference_verified']


def test_setup_api_routes_and_busy_configuration_guard(isolated,monkeypatch):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    from lib import production_agent,reference_analysis
    client=TestClient(create_app(),base_url='http://127.0.0.1')
    assert client.get('/api/studio/setup').json()['total_families']==48
    assert client.get('/api/studio/setup/runtime/framepack').json()['fields']['backbone_dir']
    assert client.post('/api/studio/setup/discover',json={'roots':[str(isolated)]}).json()['executed_files']==0
    assert client.post('/api/studio/setup/report',json={}).status_code==200
    assert client.post('/api/studio/setup/report',json={'unexpected':1}).status_code==400
    monkeypatch.setattr(production_agent,'ACTIVE',{'fixture':object()})
    assert client.post('/api/studio/setup/runtime/framepack',json={}).status_code==409
    assert client.post('/api/studio/applications/ffmpeg',json={}).status_code==409
    monkeypatch.setattr(production_agent,'ACTIVE',{})
    monkeypatch.setattr(reference_analysis,'ACTIVE',{'fixture':object()})
    assert client.post('/api/studio/setup/runtime/framepack',json={}).status_code==409
