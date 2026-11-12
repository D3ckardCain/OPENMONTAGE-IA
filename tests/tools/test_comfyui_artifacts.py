"""Container validation uses synthetic bytes, not model-generated videos."""
import pytest
from tools._comfyui.artifacts import validate_mp4_container


def box(kind, payload=b'x'):
    return (8 + len(payload)).to_bytes(4, 'big') + kind + payload


FTYP = box(b'ftyp', b'isom\x00\x00\x00\x00')
MOVIE = box(b'moov')
MEDIA = box(b'mdat')


@pytest.mark.parametrize('data', [
    b'', b'<html>not a video</html>', FTYP, FTYP + MOVIE,
    FTYP + MEDIA, FTYP + MOVIE + MEDIA[:-1],
    FTYP + MOVIE + MEDIA + b'x', box(b'ftyp') + MOVIE + MEDIA,
    FTYP + box(b'moov', b'') + MEDIA, FTYP + MOVIE + box(b'mdat', b''),
    FTYP + MOVIE + b'\x00\x00\x00\x01mdat',
    FTYP + MOVIE + b'\x00\x00\x00\x04mdat',
])
def test_invalid_containers_rejected(data):
    with pytest.raises(ValueError): validate_mp4_container(data)


@pytest.mark.parametrize('media', [
    MEDIA,
    b'\x00\x00\x00\x00mdatx',
    b'\x00\x00\x00\x01mdat' + (17).to_bytes(8, 'big') + b'x',
])
def test_supported_box_sizes(media):
    validate_mp4_container(FTYP + MOVIE + media)


def test_ffmpeg_generated_mp4_passes_container_check(tmp_path):
    import shutil
    import subprocess
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        pytest.skip('ffmpeg is not installed')
    target = tmp_path / 'synthetic.mp4'
    subprocess.run([
        ffmpeg, '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=32x32:r=4',
        '-frames:v', '2', '-c:v', 'mpeg4', '-y', str(target),
    ], check=True, timeout=30, capture_output=True)
    validate_mp4_container(target.read_bytes())
