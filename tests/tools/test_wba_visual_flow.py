import runpy
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from tools.boxing import official_wba as wba
from tools.graphics.sports_card import render,SportsCard
from tools.graphics.sports_card_video import SportsCardVideo


def card(monkeypatch):
    page=runpy.run_path(str(Path(__file__).with_name('test_official_wba_live.py')))['page']()
    monkeypatch.setattr(wba,'fetch',lambda:(page,{'url':wba.URL,'retrieved_at':'2026-11-20T00:00:00Z'}))
    result=wba.OfficialWBA().execute({'action':'collectible_card','name':'Boxer 1'})
    assert result.success,result.error
    return result.data


def test_card_displays_month_division_and_rank_not_fight_record(monkeypatch,tmp_path):
    r=card(monkeypatch);root=ET.fromstring(render(r))
    text=[x.text for x in root.findall('{http://www.w3.org/2000/svg}text')]
    assert any('BOXEO' in value for value in text)
    assert any('2026-10' in value for value in text)
    assert 'HEAVYWEIGHT' in text and '1' in text
    assert r['records'][0]['fight_record'] is None
    assert r['records'][0]['knockouts'] is None
    assert SportsCard().execute({'report':r,'output_path':str(tmp_path/'wba.png')}).success


def test_wba_rejects_unverified_fight_metrics_or_missing_month(monkeypatch):
    r=card(monkeypatch);r['records'][0]['facts'][0]['metric']='knockouts'
    with pytest.raises(ValueError):render(r)
    r=card(monkeypatch);r['scope'].pop('as_of_month')
    with pytest.raises(ValueError):render(r)


def test_name_not_found_blocks_card(monkeypatch):
    card(monkeypatch)
    r=wba.OfficialWBA().execute({'action':'collectible_card','name':'Unknown'})
    assert r.success and not r.data['ready_for_script']
    with pytest.raises(ValueError):render(r.data)


def test_wba_synthetic_clip(monkeypatch,tmp_path):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):pytest.skip('FFmpeg not installed')
    report=card(monkeypatch)
    monkeypatch.setattr('tools.graphics.sports_card_video.require_media',shutil.which)
    result=SportsCardVideo().execute({'report':report,'output_path':str(tmp_path/'wba.mp4'),'duration_seconds':1})
    assert result.success,result.error
    assert result.data['full_decode_passed']
