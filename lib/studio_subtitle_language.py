"""Explicit MP4 subtitle language tags; no detection, translation or downloads."""

SUPPORTED = frozenset({'und', 'spa', 'por', 'eng', 'fra', 'deu', 'ita',
                       'jpn', 'kor', 'zho', 'rus', 'ara', 'hin'})


def validate_language(value):
    if not isinstance(value, str) or value not in SUPPORTED:
        raise ValueError('Idioma de subtítulos no admitido; usa un código explícito del selector o und')
    return value


def stream_language(style):
    # Compatibility only: pre-language EDLs historically exported spa. Never
    # write that assumption into their project or claim it was detected.
    return validate_language(style['language']) if 'language' in style else 'spa'


def metadata_args(style):
    return ['-metadata:s:s:0', 'language=' + stream_language(style)]
