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
