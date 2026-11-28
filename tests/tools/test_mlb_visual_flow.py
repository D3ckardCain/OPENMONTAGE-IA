import runpy
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from tools.baseball.official_mlb import MLB,OfficialMLB
from tools.graphics.sports_card import render,SportsCard
from tools.graphics.sports_card_video import SportsCardVideo


def client():
    fake=runpy.run_path(str(Path(__file__).with_name('test_official_mlb_live.py')))['Feed']()
    return MLB(fake)


def test_card_keeps_original_rates_and_innings_and_renders_png(tmp_path):
    r=client().collectible_card('One',2024,'pitching',['inningsPitched','avg'])
    assert r['ready_for_script']
    assert [f['value'] for f in r['records'][0]['facts']]==['4.1','.310']
    svg=render(r);root=ET.fromstring(svg)
    texts=[node.text for node in root.findall('{http://www.w3.org/2000/svg}text')]
    assert '4.1' in texts and '.310' in texts
    assert any('BÉISBOL' in value for value in texts)
    assert any('Pitcheo' in value for value in texts)
    assert SportsCard().execute({'report':r,'output_path':str(tmp_path/'mlb.png')}).success


def test_comparison_keeps_each_players_own_statistics_source():
    r=client().compare_players(['One','Two'],2024,'hitting',['homeRuns','avg'])
    assert r['records'][0]['statistics_source']['url']!=r['records'][1]['statistics_source']['url']
    ET.fromstring(render(r))
    r['records'][0]['statistics_source']['url']='https://statsapi.mlb.com/unqueried'
    with pytest.raises(ValueError):render(r)


def test_missing_metric_blocks_design():
    r=client().collectible_card('One',2024,'hitting',['unknown'])
    assert not r['ready_for_script']
    with pytest.raises(ValueError):render(r)


def test_registered_card_dispatch_and_real_synthetic_video(tmp_path,monkeypatch):
    tool=OfficialMLB();tool.client=client()
    result=tool.execute({'action':'collectible_card','name':'One','season':2024,'group':'hitting','metrics':['homeRuns','avg']})
    assert result.success,result.error
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):pytest.skip('FFmpeg not installed')
    monkeypatch.setattr('tools.graphics.sports_card_video.require_media',shutil.which)
    r=SportsCardVideo().execute({'report':result.data,'output_path':str(tmp_path/'mlb.mp4'),'duration_seconds':1})
    assert r.success,r.error
    assert r.data['full_decode_passed']
