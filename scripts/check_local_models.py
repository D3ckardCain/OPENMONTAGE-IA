"""Read-only, offline structural check of the bundled Wan model downloads.

Uses Python's standard library only, including ComfyUI's embedded Python.
Does not load tensors, allocate GPU memory, download, rename or delete files.
Structural checks are not a cryptographic checksum or an inference benchmark.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

WORKFLOWS = Path(__file__).resolve().parents[1] / 'tools' / '_comfyui' / 'workflows'
LOADERS = {
    'UNETLoader': ('diffusion_models', 'unet_name'),
    'CLIPLoader': ('text_encoders', 'clip_name'),
    'VAELoader': ('vae', 'vae_name'),
    'LoraLoaderModelOnly': ('loras', 'lora_name'),
}
MAX_HEADER = 16 * 1024 * 1024


def required_models(operation: str) -> list[Path]:
    """Read exact names from reviewed graphs, keeping I2V/T2V LoRAs separate."""
    variants = ('t2v', 'i2v') if operation == 'all' else (operation,)
    result = set()
    for variant in variants:
        graph = json.loads((WORKFLOWS / f'wan22-{variant}-4step.json').read_text(encoding='utf-8'))
        for node in graph.values():
            loader = LOADERS.get(node['class_type'])
            if loader:
                folder, field = loader
                result.add(Path(folder) / node['inputs'][field])
    return sorted(result)


def inspect_model(path: Path) -> tuple[str, str]:
    """Validate bounded header JSON and contiguous tensor payload offsets.

    Report header-readable rather than verified: wrong model contents and
    bit corruption inside tensor data require authoritative checksums.
    """
    try:
        with path.open('rb') as stream:
            size = path.stat().st_size
            prefix = stream.read(256)
            start = prefix.lstrip(b'\xef\xbb\xbf \t\r\n').lower()
            if start.startswith((b'<!doctype html', b'<html')):
                return 'INVALID', 'HTML page saved as a model; download the actual file'
            if start.startswith(b'version https://git-lfs.github.com/spec/v1'):
                return 'INVALID', 'Git LFS pointer, not downloaded model weights'
            if len(prefix) < 8:
                return 'INVALID', 'empty or truncated safetensors header'
            length = struct.unpack('<Q', prefix[:8])[0]
            if not 2 <= length <= MAX_HEADER:
                return 'INVALID', 'invalid or unsupported safetensors header length'
            if length > size - 8:
                return 'INVALID', 'truncated header; download may still be running'
            stream.seek(8)
            header = json.loads(stream.read(length))
            if not isinstance(header, dict):
                return 'INVALID', 'header must be a JSON object'
            payload = size - 8 - length
            offsets = []
            for name, tensor in header.items():
                if name == '__metadata__':
                    continue
                if not isinstance(tensor, dict):
                    return 'INVALID', f'invalid tensor entry: {name}'
                bounds = tensor.get('data_offsets')
                if (not isinstance(bounds, list) or len(bounds) != 2
                        or any(type(n) is not int for n in bounds)):
                    return 'INVALID', f'invalid tensor offsets: {name}'
                begin, end = bounds
                if not 0 <= begin <= end <= payload:
                    return 'INVALID', f'truncated or invalid tensor payload: {name}'
                offsets.append((begin, end))
            if not offsets:
                return 'INVALID', 'no tensors in header'
            position = 0
            for begin, end in sorted(offsets):
                if begin != position:
                    return 'INVALID', 'overlapping tensors or gaps in payload'
                position = end
            if position != payload:
                return 'INVALID', 'unexpected trailing data'
            return 'HEADER_OK', f'{size:,} bytes; structure readable, checksum not verified'
    except FileNotFoundError:
        return 'MISSING', 'required file not found in this folder'
    except (OSError, ValueError, UnicodeError, struct.error, RecursionError) as exc:
        return 'INVALID', f'cannot read model header: {exc}'


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models-dir', type=Path, required=True)
    parser.add_argument('--operation', choices=('t2v', 'i2v', 'all'), default='all')
    args = parser.parse_args(argv)
    if not args.models_dir.is_dir():
        parser.error('--models-dir must point to an existing ComfyUI models folder')
    failed = False
    for relative in required_models(args.operation):
        status, detail = inspect_model(args.models_dir / relative)
        print(f'{status}: {relative.as_posix()}\n  {detail}')
        failed |= status != 'HEADER_OK'
    print('Read-only structural check. Model identity, checksum, GPU speed and quality are not verified.')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
