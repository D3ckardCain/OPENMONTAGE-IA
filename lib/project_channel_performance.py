"""Verify the private performance CSV snapshot copied into a production."""
from lib import production_studio as studio
from lib.channel_dossiers import _digest
from lib.channel_performance import summary


def verified(path, request):
    identifier = request.get('performance_import_id')
    if identifier is None:
        return None
    record = studio.read_json(path/'artifacts/channel_performance_snapshot.json')
    if (not isinstance(record, dict) or record.get('id') != identifier
            or record.get('sha256') != request.get('performance_import_sha256')
            or not isinstance(record.get('rows'), list)
            or _digest({key: value for key, value in record.items() if key != 'sha256'}) != record['sha256']):
        raise ValueError('Rendimiento del proyecto ausente o alterado')
    return record


def page(path, request, offset=0, limit=20):
    record = verified(path, request)
    if record is None:
        return {'status': 'not_copied', 'rows': [], 'message': 'El proyecto no tiene un CSV de rendimiento vinculado.'}
    return {'status': 'verified', **summary(record, offset, limit)}
