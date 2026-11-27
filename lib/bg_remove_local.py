"""Local artifact checks for BgRemove. No provider imports, downloads or scans."""
from functools import lru_cache
import hashlib
import re
from pathlib import Path
from urllib.parse import urlsplit

MODELS = {'u2net': ('u2net', 'U2netSession'),
          'u2net_human_seg': ('u2net_human_seg', 'U2netHumanSegSession'),
          'isnet-general-use': ('dis_general_use', 'DisSession')}


class LocalModelError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def fail(code, message):
    raise LocalModelError(code, message)


def token(path):
    s = path.stat()
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns


@lru_cache(maxsize=64)
def _hash(path, identity):
    # Reuse the existing bounded reader; it rejects growth/truncation.
    from lib.studio_editor import digest
    value = digest(Path(path))
    if token(Path(path)) != identity:
        fail('artifact_changed', 'El archivo cambió durante su verificación')
    return value


def checksum(path):
    before = token(path)
    value = _hash(str(path.resolve()), before)
    if token(path) != before:
        fail('artifact_changed', 'El archivo cambió durante su verificación')
    return value


def review_license(review, expected):
    if not isinstance(review, dict) or review.get('status') != 'reviewed':
        fail('license_unreviewed', 'Falta revisión explícita de la licencia del peso/conversión')
    if review.get('commercial_use') != 'yes' or review.get('requires_paid_agreement') is not False:
        fail('license_ineligible', 'El artefacto no está declarado elegible para uso comercial sin acuerdo pagado')
    license_id = review.get('license_id')
    if (not isinstance(license_id, str) or not 1 <= len(license_id) <= 200
            or license_id.lower() in ('unknown', 'pending', 'unreviewed')
            or re.search(r'(?:^|[-_\s])NC(?:$|[-_\s])|NON.?COMMERCIAL', license_id, re.I)):
        fail('license_ineligible', 'Licencia desconocida o NC; no se habilita por MIT del wrapper')
    declared = review.get('model_sha256')
    if not isinstance(declared, str) or declared.lower() != expected:
        fail('license_wrong_artifact', 'La revisión de licencia no corresponde a esta huella del modelo')
    revision = review.get('revision')
    if not isinstance(revision, str) or not 1 <= len(revision) <= 200 or revision.lower() in ('main','master','latest','head'):
        fail('license_unreviewed', 'Fija revisión/versionado del artefacto revisado, no una rama flotante')
    for key in ('source_url', 'license_url'):
        value = review.get(key)
        if not isinstance(value, str) or len(value) > 2000:
            fail('license_unreviewed', 'Falta referencia de procedencia/licencia del artefacto')
        parsed = urlsplit(value)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
            fail('license_unreviewed', 'Usa referencias HTTPS sin credenciales para procedencia/licencia')
    return dict(review)


def preflight(inputs):
    from lib import production_studio as studio
    from lib.project_asset_sources import _asset
    allowed = {'project_id','input_path','output_path','model','model_path','model_sha256',
               'license_review','bg_color','alpha_matting'}
    if not isinstance(inputs, dict) or set(inputs) - allowed:
        fail('invalid_parameters', 'Parámetro desconocido en el contrato local de BgRemove')
    model = inputs.get('model')
    if model not in MODELS:
        fail('unsupported_model', 'Selecciona explícitamente u2net, u2net_human_seg o isnet-general-use; sin default/fallback')
    expected = inputs.get('model_sha256')
    if not isinstance(expected, str) or not re.fullmatch('[a-fA-F0-9]{64}', expected):
        fail('missing_model_hash', 'Se requiere SHA256 esperado del artefacto local')
    expected = expected.lower()
    review = review_license(inputs.get('license_review'), expected)
    project_id = inputs.get('project_id')
    if not isinstance(project_id, str) or not project_id:
        fail('missing_project', 'Indica el proyecto propietario del resultado')
    project = studio.project_path(project_id).resolve()
    paths = {}
    for key in ('input_path', 'output_path'):
        value = inputs.get(key)
        if not isinstance(value, str) or not value:
            fail('missing_path', 'Se requiere '+key+' explícito dentro del proyecto')
        path = Path(value)
        if not path.is_absolute():
            path = project / path
        if '..' in path.parts:
            fail('path_outside_project', 'No se admiten segmentos ..')
        try:
            relative = path.resolve().relative_to(project)
        except ValueError:
            fail('path_outside_project', 'Entrada y salida deben pertenecer al proyecto')
        if not relative.parts or relative.parts[0] not in ('assets','source_images','originales','thumbnails'):
            fail('path_outside_project', 'Usa originales, assets, source_images o thumbnails del proyecto')
        if any(project.joinpath(*relative.parts[:i]).is_symlink() for i in range(1,len(relative.parts)+1)):
            fail('symlink', 'No se admiten enlaces simbólicos para entrada/salida')
        paths[key] = project / relative
    source, output = paths['input_path'], paths['output_path']
    if source == output or output.exists() or output.is_symlink():
        fail('output_exists', 'La salida debe ser un archivo nuevo, separado del original')
    if output.suffix.lower() != '.png':
        fail('output_format', 'La salida local debe ser PNG')
    _asset(project, source.relative_to(project).as_posix())  # shared bounds/path rules
    if type(inputs.get('alpha_matting', False)) is not bool:
        fail('invalid_parameters', 'alpha_matting debe ser booleano')
    color = inputs.get('bg_color')
    if color is not None and (not isinstance(color, str) or not re.fullmatch('#?[a-fA-F0-9]{6}', color)):
        fail('invalid_parameters', 'bg_color requiere seis dígitos hexadecimales')
    value = inputs.get('model_path')
    if not isinstance(value, str) or not value:
        fail('missing_model', 'Indica el archivo ONNX local; no se busca ni descarga en caches')
    weight = Path(value).expanduser()
    if not weight.is_absolute() or weight.suffix.lower() != '.onnx' or weight.is_symlink() or not weight.is_file():
        fail('missing_model', 'Peso ONNX local ausente, no regular o enlace simbólico')
    if not weight.stat().st_size:
        fail('missing_model', 'Peso ONNX vacío')
    actual = checksum(weight)
    if actual != expected:
        fail('model_hash_mismatch', 'La huella local no coincide con el SHA256 esperado; no se carga el peso')
    return {'model':model,'model_path':weight.resolve(),'model_sha256':actual,
            'input_path':source,'output_path':output,'input_sha256':checksum(source),
            'license_review':review}


def local_session(model, path, expected):
    """Reuse rembg's preprocessing/predict; replace its download hook locally."""
    from importlib import import_module
    import onnxruntime as ort
    module, name = MODELS[model]
    cls = getattr(import_module('rembg.sessions.' + module), name)
    if cls.name() != model:
        fail('provider_incompatible', 'Clase de sesión incompatible; no se usa otra variante')

    class PreparedSession(cls):
        @classmethod
        def download_models(cls, *args, **kwargs):
            if checksum(path) != expected:
                fail('artifact_changed', 'Cambió el peso antes de crear la sesión local')
            return str(path)

    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    session = PreparedSession(model, options, providers=['CPUExecutionProvider'])
    active = session.inner_session.get_providers()
    if active != ['CPUExecutionProvider']:
        fail('provider_incompatible', 'Proveedor CPU explícito no respetado; no se permite fallback')
    return session

