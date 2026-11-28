"""New subtitle-language cases only; no approved PT sample or ASR repeated."""
import json
from pathlib import Path
import subprocess
import uuid

import pytest
from fastapi.testclient import TestClient

from backlot.server import create_app
from lib import studio_editor as edit, studio_editor_render as render, production_studio as studio
from lib.media_executables import find_media
from lib.studio_subtitle_language import metadata_args
from tests.backlot.test_studio_editor import project, command, add


def test_explicit_language_is_shared_persistent_reversible_and_not_translation(project):
    pid, key, _ = project
    add(pid, key)
    command(pid, 'subtitles', srt='1\n00:00:00,000 --> 00:00:01,000\nTexto intacto.\n')
    before = edit.state(pid)
    assert before['edit_decisions']['subtitle_style']['language'] == 'und'
    client = TestClient(create_app(), base_url='http://127.0.0.1')
    response = client.post(f'/api/studio/editor/{pid}/agent-command', json={
        'operation': 'subtitle_style', 'revision': before['revision'],
        'size': 32, 'position': 'bottom', 'mode': 'soft', 'language': 'por'})
    assert response.status_code == 200
    value = response.json()
    assert value['edit_decisions']['subtitle_style']['language'] == 'por'
    assert value['edit_decisions']['cues'] == before['edit_decisions']['cues']
    assert value['render_sha256'] != before['render_sha256']
    command(pid, 'save')
    assert studio.read_json(studio.project_path(pid) / edit.ARTIFACT)['edit_decisions']['subtitle_style']['language'] == 'por'
    command(pid, 'undo')
    assert edit.state(pid)['edit_decisions']['subtitle_style']['language'] == 'und'
    command(pid, 'redo')
    assert edit.state(pid)['edit_decisions']['subtitle_style']['language'] == 'por'
    command(pid, 'subtitle_style', size=40, position='top', mode='burn')
    assert edit.state(pid)['edit_decisions']['subtitle_style']['language'] == 'por'


@pytest.mark.parametrize('language', ['pt', 'zzz', 'por -f x', 'POR', '', None, True])
def test_unknown_or_unsafe_language_fails_without_project_mutation(project, language):
    pid, _, _ = project
    before = edit.state(pid)
    with pytest.raises(ValueError, match='Idioma'):
        command(pid, 'subtitle_style', size=32, position='bottom', mode='soft', language=language)
    assert edit.state(pid) == before


@pytest.mark.parametrize('language,expected', [('por','por'), ('eng','eng'), ('und','und'), (None,'spa')])
def test_actual_worker_command_uses_declared_tag_and_preserves_legacy(project, monkeypatch, language, expected):
    pid, key, _ = project
    add(pid, key)
    command(pid, 'subtitles', srt='1\n00:00:00,000 --> 00:00:01,000\nSynthetic caption\n')
    if language is not None:
        command(pid, 'subtitle_style', size=32, position='bottom', mode='soft', language=language)
    else:
        path = studio.project_path(pid) / edit.ARTIFACT
        saved = studio.read_json(path)
        saved['edit_decisions']['subtitle_style'].pop('language')
        studio.save_json(path, saved)
    value = edit.state(pid);before = value['edit_decisions']
    captured = []
    def execute(args, work, control, timeout):
        captured.extend(args)
        Path(args[-1]).write_bytes(b'SYNTHETIC MUX STUB: NOT REAL AV')
        return subprocess.CompletedProcess(args, 0, b'', b'')
    monkeypatch.setattr(render, 'execute', execute)
    monkeypatch.setattr(render, 'require_media', lambda _: 'mock-ffmpeg')
    args, filters, width, height = render.plan(pid, before)
    job = {'status':'running','attempt':uuid.uuid4().hex,'revision':value['revision'],
           'width':width,'height':height,'preview':False}
    render._worker(pid, before, job, args, filters)
    assert job['status'] == 'completed'
    assert captured[captured.index('-metadata:s:s:0')+1] == 'language='+expected
    assert edit.state(pid)['edit_decisions'] == before  # no automatic migration


@pytest.mark.parametrize('language', ['por', 'eng', 'und'])
def test_ffmpeg_synthetic_container_reports_language(tmp_path, language):
    ffmpeg, ffprobe = find_media('ffmpeg'), find_media('ffprobe')
    if not ffmpeg or not ffprobe:
        pytest.skip('Prepared media binaries unavailable; no download allowed')
    srt = tmp_path / 'synthetic.srt'
    srt.write_text('1\n00:00:00,000 --> 00:00:00,400\nSynthetic metadata test\n', encoding='utf-8')
    output = tmp_path / 'synthetic.mp4'
    result = subprocess.run([ffmpeg,'-nostdin','-v','error','-n','-f','lavfi','-i',
        'color=c=black:s=64x64:r=5:d=0.4','-i',str(srt),'-map','0:v:0','-map','1:s:0',
        '-c:v','libx264','-c:s','mov_text',*metadata_args({'language':language}),str(output)],
        capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr.decode('utf-8','replace')
    result = subprocess.run([ffprobe,'-v','error','-select_streams','s:0',
        '-show_entries','stream_tags=language','-of','json',str(output)],capture_output=True,timeout=10)
    assert result.returncode == 0
    assert json.loads(result.stdout)['streams'][0]['tags']['language'] == language
