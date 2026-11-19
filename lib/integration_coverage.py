"""Preparation matrix; never turns catalog presence into compatibility evidence."""
from pathlib import Path
import json
from lib import model_adapters as adapters
from lib import production_studio as studio


def coverage():
    template_dir=Path(__file__).resolve().parents[1]/'tools/_comfyui/reference_templates'
    manifest=json.loads((template_dir/'manifest.json').read_text(encoding='utf-8'))
    templates={row['family']:row for row in manifest['templates']}
    rows=[]
    for family,group in adapters.CATALOG.items():
        spec=adapters.spec(family);cfg=adapters.configuration(family)
        workflow=Path(cfg['workflow_path']) if cfg.get('workflow_path') else None
        native=spec['backend']=='native';bound=bool(workflow and workflow.is_file())
        reference=templates.get(family)
        rows.append({'family':family,'title':group.get('title',family),'capability':spec['capability'],
            'adapter':spec['backend'],'implementation':'native_worker' if native else 'comfyui_api_bridge',
            'workflow_path':str(workflow) if workflow else None,'workflow_bound':bound,
            'reference_template':reference,
            'reference_template_available':bool(reference and (template_dir/reference['file']).is_file()),
            'preparation_state':'awaiting_hardware_test' if native or bound else 'workflow_binding_required',
            'inference_verified':False,'required_modules':spec['dependencies'],
            'catalogued_files':len(group['entries']),
            'next_step':'Comprobar pesos, dependencias y resultado real' if native or bound else 'Preparar o importar el workflow API compatible y sus nodos antes de probar',
            'manual':'docs/ADAPTADORES_MODELOS_ES.md'})
    return {'models':rows,'total':len(rows),'native_workers':sum(r['adapter']=='native' for r in rows),
        'bound_workflows':sum(r['workflow_bound'] for r in rows),
        'reference_templates':sum(r['reference_template_available'] for r in rows),
        'scope':'static_preparation_no_runtime_probes'}
