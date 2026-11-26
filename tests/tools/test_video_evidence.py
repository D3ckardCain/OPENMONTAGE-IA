"""Only new bounded evidence behavior; no old sampling suites or media renders."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image
from lib import video_evidence as evidence


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    source=tmp_path/'source.mp4';source.write_bytes(b'fixture-local-video')
    exe=tmp_path/'ffmpeg.exe';exe.write_bytes(b'fixture-executable')
    monkeypatch.setattr(evidence,'require_media',lambda name:str(exe))
    calls=[]
    def run(command):
        calls.append(command)
        if '-show_frames' in command:
            return SimpleNamespace(stdout=json.dumps({'frames':[{'best_effort_timestamp':i} for i in [0,400,900]]}),stderr='')
        if '-show_entries' in command:
            return SimpleNamespace(stdout=json.dumps({'streams':[{'time_base':'1/1000','duration':'1'}],'format':{'duration':'1'}}),stderr='')
        pattern=Path(command[-1]);pattern.parent.mkdir(exist_ok=True)
        for i in [1,2]:Image.new('RGB',(128,72),(i*80,20,40)).save(str(pattern).replace('%02d',f'{i:02d}'))
        return SimpleNamespace(stdout='',stderr='pts_time:0.4\npts_time:0.9\n')
    monkeypatch.setattr(evidence,'_run',run)
    inputs=dict(input_path=str(source),output_dir=str(tmp_path/'evidence'),start_seconds=0,end_seconds=1,max_frames=2,thumbnail_width=128)
    return inputs,calls


def test_real_pts_contract_and_cache_do_not_repeat_decode_or_source_hash(fixture,monkeypatch):
    inputs,calls=fixture;first=evidence.inspect(inputs)
    assert [f['pts_seconds'] for f in first['frames']]==[.4,.9] # Not requested uniform targets .25/.75.
    assert first['coverage']=='partial_sampled_images_only' and not first['inference_executed']
    count=len(calls)
    again=evidence.inspect(inputs)
    assert again['cache_reused'] and again['source_hash_reused'] and len(calls)==count
    assert Path(again['contact_sheet']).is_file()


def test_changed_cached_image_is_not_silently_reused(fixture):
    inputs,_=fixture;report=evidence.inspect(inputs);path=Path(report['frames'][0]['path'])
    path.write_bytes(b'changed')
    with pytest.raises(ValueError,match='Cached evidence changed'):evidence.inspect(inputs)
    assert path.read_bytes()==b'changed'


def test_changed_receipt_not_trusted(fixture):
    inputs,_=fixture;report=evidence.inspect(inputs);receipt=Path(report['contact_sheet']).parent/'receipt.json'
    receipt.write_text('{}')
    with pytest.raises(ValueError,match='receipt changed'):evidence.inspect(inputs)


@pytest.mark.parametrize('change',[{'max_frames':True},{'max_frames':13},{'end_seconds':float('nan')},{'end_seconds':121},{'thumbnail_width':1000}])
def test_budget_and_range_fail_before_process_or_output(fixture,change):
    inputs,calls=fixture;inputs.update(change)
    with pytest.raises(ValueError):evidence.inspect(inputs)
    assert not calls and not Path(inputs['output_dir']).exists()


def test_transcript_reused_only_for_matching_content_and_interval(fixture):
    inputs,_=fixture;sha=hashlib.sha256(Path(inputs['input_path']).read_bytes()).hexdigest()
    inputs['stored_transcript']=dict(source_sha256=sha,words=[{'word':'No','start':.1,'end':.2},{'word':'fin','start':2,'end':3}],coverage={'processed_ranges':[[0,1]]})
    result=evidence.inspect(inputs);assert [w['text'] for w in result['transcript']['words']]==['No']
    assert not result['transcript']['asr_executed']
    inputs['stored_transcript']['source_sha256']='0'*64
    with pytest.raises(ValueError,match='transcript does not match'):evidence.inspect(inputs)
