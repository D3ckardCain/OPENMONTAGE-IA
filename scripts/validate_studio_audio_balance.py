"""Opt-in 40 ms synthetic PCM checks. No voice, video, model or downloads.

Run from the repository: python -m scripts.validate_studio_audio_balance
Uses the existing configured FFmpeg and emits JSON to stdout.
"""
import array
import json
import subprocess

from lib.media_executables import require_media
from lib.studio_audio_balance import filter_suffix


def main():
    executable = require_media('ffmpeg')
    results = {}
    baseline = None
    for balance in (0, -1, 1, .5):
        audio_filter = 'aformat=sample_fmts=fltp:channel_layouts=stereo' + filter_suffix({'stereo_balance': balance})
        process = subprocess.run([
            executable, '-v', 'error', '-f', 'lavfi', '-i',
            'aevalsrc=0.2*sin(2*PI*440*t)|0.1*sin(2*PI*880*t):s=48000:d=0.04',
            '-af', audio_filter, '-f', 'f32le', '-c:a', 'pcm_f32le', 'pipe:1',
        ], capture_output=True, timeout=10, check=True)
        samples = array.array('f')
        samples.frombytes(process.stdout)
        assert len(samples) == 3840
        if baseline is None:
            baseline = samples
        gains = (1 - max(0, balance), 1 + min(0, balance))
        error = max(abs(samples[i] - baseline[i] * gains[i % 2]) for i in range(len(samples)))
        assert error < 2e-7
        results[str(balance)] = {'samples_per_channel': 1920, 'left_gain': gains[0],
                                 'right_gain': gains[1], 'maximum_error': error}
    print(json.dumps({'scenario': 'Synthetic PCM only; no human listening', 'ffmpeg': executable,
                      'results': results}, indent=2))


if __name__ == '__main__':
    main()
