"""Read tiny file prefixes to identify common failed downloads, not certify weights."""
from pathlib import Path

SUFFIXES={'.safetensors','.bin','.pt','.pth','.onnx','.model','.pdiparams','.json'}


def download_problem(path):
    path=Path(path)
    if path.suffix.lower() not in SUFFIXES:return None
    try:
        with path.open('rb') as stream:prefix=stream.read(512)
    except OSError:return 'No se puede leer el archivo'
    text=prefix.decode('utf-8-sig',errors='ignore').lstrip().lower()
    if text.startswith('version https://git-lfs.github.com/spec/v1'):
        return 'Puntero Git LFS; no contiene los pesos reales'
    if text.startswith(('<!doctype html','<html','<head','<body')):
        return 'Página HTML guardada en lugar del archivo del modelo'
    if text.startswith(('<?xml','<error>','<error ')):
        return 'Respuesta XML de descarga; revisar el archivo'
    return None
