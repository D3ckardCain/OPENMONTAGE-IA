from tools.base_tool import ToolStatus
from tools.graphics.sports_card import SportsCard
from tools.graphics.sports_card_video import SportsCardVideo
from lib import sports_export_requirements as requirements


def test_missing_media_is_reported_before_render(monkeypatch):
    monkeypatch.setattr(requirements,'png_requirements',lambda:{'available':True,'font':'fixture','missing':[]})
    def absent(name):raise ValueError('Configura la ruta de '+name)
    monkeypatch.setattr(requirements,'require_media',absent)
    tool=SportsCardVideo()
    assert tool.get_status()==ToolStatus.UNAVAILABLE
    info=tool.get_info()['export_readiness']
    assert not info['available'] and len(info['missing'])==2
    assert info['executables']=={'ffmpeg':None,'ffprobe':None}
    assert not info['downloads_started'] and not info['models_loaded']


def test_missing_font_does_not_disable_svg(monkeypatch):
    monkeypatch.setattr(requirements,'png_requirements',lambda:{'available':False,'font':None,'missing':['Fuente ausente']})
    monkeypatch.setattr(requirements,'require_media',lambda name:'/configured/'+name)
    image=SportsCard()
    assert image.get_status()==ToolStatus.AVAILABLE
    readiness=image.get_info()['output_readiness']
    assert readiness['svg']['available'] and not readiness['png']['available']
    assert SportsCardVideo().get_status()==ToolStatus.UNAVAILABLE


def test_configured_paths_and_font_make_video_available_without_running_binaries(monkeypatch):
    monkeypatch.setattr(requirements,'png_requirements',lambda:{'available':True,'font':'fixture','missing':[]})
    monkeypatch.setattr(requirements,'require_media',lambda name:'/configured/'+name)
    tool=SportsCardVideo()
    assert tool.get_status()==ToolStatus.AVAILABLE
    readiness=tool.get_info()['export_readiness']
    assert readiness['available'] and readiness['executables']['ffmpeg']=='/configured/ffmpeg'
