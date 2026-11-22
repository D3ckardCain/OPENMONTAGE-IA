"""Portable, read-only evidence for a reviewed football comparison selection."""
import hashlib
import json
from datetime import datetime, timezone

from lib.football_comparisons import metric_matrix
from tools.graphics.sports_card import render


def build(report, metrics):
    # The same verifier used by the SVG rejects missing values, wrong identities,
    # mixed phases and URLs outside the signed source report.
    render(report, metrics)
    matrix = metric_matrix(report.get('original_report') or report)
    rows = report['records']
    source = report.get('source')
    queries = report.get('queries') or []
    evidence = []
    for row in rows:
        if source == 'FIFA':
            origin = queries[-1]
            facts = [{'metric': metric, 'value': row['statistics'][metric]['value'],
                      'unit': row['statistics'][metric].get('unit'),
                      'source_url': origin['url'], 'retrieved_at': origin['retrieved_at']}
                     for metric in metrics]
        else:
            by_metric = {fact['metric']: fact for fact in row['facts']}
            facts = [by_metric[metric] for metric in metrics]
        evidence.append({'entity_id': row['entity_id'], 'name': row['identity']['name'],
                         'selected_facts': facts})
    dossier = {'version': 1, 'status': 'selection_previewed',
               'created_at': datetime.now(timezone.utc).isoformat(),
               'source': source, 'scope': report['scope'], 'selected_metrics': metrics,
               'selected_evidence': evidence, 'metric_matrix': matrix,
               'report': report}
    canonical = json.dumps(dossier, sort_keys=True, separators=(',', ':'),
                           ensure_ascii=False, allow_nan=False).encode('utf-8')
    dossier['sha256'] = hashlib.sha256(canonical).hexdigest()
    return dossier


def save_to_project(project_id, report, metrics):
    from lib import production_studio as studio

    dossier = build(report, metrics)
    selection = json.dumps({'report': report, 'metrics': metrics}, sort_keys=True,
                           separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')
    selection_id = hashlib.sha256(selection).hexdigest()
    serialized = json.dumps(dossier, ensure_ascii=False, indent=2).encode('utf-8')
    if len(serialized) > 500_000:
        raise ValueError('El expediente supera 500 KB; reduce el alcance antes de guardarlo')
    project = studio.project_path(project_id)
    folder = project / 'artifacts' / 'football_comparisons'
    path = folder / (selection_id + '.json')
    index_path = project / 'artifacts' / 'football_comparison_selection.json'
    with studio.LOCK:
        folder.mkdir(parents=True, exist_ok=True)
        if folder.is_symlink() or path.is_symlink() or index_path.is_symlink():
            raise ValueError('La carpeta de comparativas contiene un enlace no admitido')
        duplicate = path.is_file()
        if duplicate:
            stored = studio.read_json(path)
            unsigned = {key: value for key, value in stored.items() if key != 'sha256'}
            canonical = json.dumps(unsigned, sort_keys=True, separators=(',', ':'),
                                   ensure_ascii=False, allow_nan=False).encode('utf-8')
            if (stored.get('sha256') != hashlib.sha256(canonical).hexdigest()
                    or stored.get('report') != report or stored.get('selected_metrics') != metrics):
                raise ValueError('El expediente guardado cambió; revisa el archivo antes de continuar')
        else:
            if sum(1 for item in folder.glob('*.json') if item.is_file()) >= 100:
                raise ValueError('El proyecto alcanzó el límite de 100 comparativas guardadas')
            studio.save_json(path, dossier)
            stored = dossier
        index = {'project_id': project_id, 'selection_id': selection_id,
                 'dossier_path': path.relative_to(project).as_posix(),
                 'sha256': stored['sha256'],
                 'selected_metrics': metrics, 'source': report.get('source'),
                 'scope': report['scope'], 'saved_at': studio.now(),
                 'status': 'selection_previewed'}
        studio.save_json(index_path, index)
    return {'selection': index, 'duplicate': duplicate}


def latest_for_agent(project_id):
    from lib import production_studio as studio

    project = studio.project_path(project_id)
    index_path = project / 'artifacts' / 'football_comparison_selection.json'
    if index_path.is_symlink():
        raise ValueError('Índice de comparativa inválido')
    index = studio.read_json(index_path)
    if not index:
        return {'available': False}
    selection_id = index.get('selection_id', '')
    if (not isinstance(selection_id, str) or len(selection_id) != 64
            or any(char not in '0123456789abcdef' for char in selection_id)):
        raise ValueError('Índice de comparativa inválido')
    relative = f'artifacts/football_comparisons/{selection_id}.json'
    if index.get('project_id') != project_id or index.get('dossier_path') != relative:
        raise ValueError('El índice apunta a otro expediente')
    path = project / relative
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 500_000:
        raise ValueError('El expediente seleccionado no está disponible')
    dossier = studio.read_json(path)
    unsigned = {key: value for key, value in dossier.items() if key != 'sha256'}
    canonical = json.dumps(unsigned, sort_keys=True, separators=(',', ':'),
                           ensure_ascii=False, allow_nan=False).encode('utf-8')
    if (hashlib.sha256(canonical).hexdigest() != dossier.get('sha256')
            or dossier['sha256'] != index.get('sha256')):
        raise ValueError('El expediente seleccionado cambió')
    return {'available': True, 'status': dossier['status'], 'project_id': project_id,
            'selection_id': selection_id, 'dossier_path': relative,
            'selected_metrics': dossier['selected_metrics'],
            'selected_evidence': dossier['selected_evidence'], 'scope': dossier['scope'],
            'source': dossier['source'], 'sha256': dossier['sha256']}
