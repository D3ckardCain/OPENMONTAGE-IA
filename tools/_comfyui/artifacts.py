"""Small container checks; these do not decode video or certify playable media."""
from __future__ import annotations


def validate_mp4_container(content: bytes) -> None:
    """Reject empty, textual and truncated MP4 downloads before replacement.

    Walk top-level ISO BMFF boxes, including extended sizes and final size-zero
    boxes. A generated self-contained MP4 needs ftyp, moov and media data.
    This deliberately does not interpret codecs, tracks or nested boxes.
    """
    offset = 0
    boxes = set()
    while offset < len(content):
        if len(content) - offset < 8:
            raise ValueError('Truncated MP4 box header')
        size = int.from_bytes(content[offset:offset + 4], 'big')
        kind = content[offset + 4:offset + 8]
        header = 8
        if size == 1:
            if len(content) - offset < 16:
                raise ValueError('Truncated extended MP4 box header')
            size = int.from_bytes(content[offset + 8:offset + 16], 'big')
            header = 16
        elif size == 0:
            size = len(content) - offset
        if size < header or size > len(content) - offset:
            raise ValueError('Invalid or truncated MP4 box size')
        payload_size = size - header
        if kind == b'ftyp' and payload_size < 8:
            raise ValueError('Invalid MP4 file type box')
        if kind in {b'moov', b'mdat'} and payload_size == 0:
            raise ValueError('Empty MP4 movie or media data box')
        boxes.add(kind)
        offset += size
    if not {b'ftyp', b'moov', b'mdat'}.issubset(boxes):
        raise ValueError('Expected a self-contained MP4 with ftyp, moov and mdat boxes')
