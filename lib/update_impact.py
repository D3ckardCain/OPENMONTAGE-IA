"""Local catalogue relationships for an update; no runtime or compatibility claims."""
from lib import production_studio as studio
from lib import update_center as updates


def inspect(identifier,index):
    if type(index) is not int or index<0:raise ValueError('Índice inválido')
    records=updates._files(identifier)
    if index>=len(records):raise ValueError('Archivo fuera del catálogo')
    selected=records[index]
    related={}
    for path in sorted((studio.REPO_ROOT/'docs/models').glob('*.json')):
        manifest=studio.read_json(path,{})
        entries={item['destination']:item for item in manifest.get('files',[]) if isinstance(item,dict) and isinstance(item.get('destination'),str)}
        for group in manifest.get('groups',[]):
            members=[entries[dest] for dest in group.get('files',[]) if dest in entries]
            matches=[]
            for item in members:
                source=updates._model_source(item.get('url'))
                if source and (source[0],source[3])==(identifier,selected['filename']):
                    matches.append({'destination':item['destination'],'catalog_revision':source[2]})
            if not matches:continue
            family=group['id']
            if family in related:raise ValueError('Familia duplicada en el catálogo; revisa el manifiesto')
            from lib import model_adapters as adapters
            spec=adapters.spec(family);cfg=adapters.configuration(family)
            companions=[{'destination':item['destination'],'source_url':item.get('url')} for item in members
                        if item['destination'] not in {match['destination'] for match in matches}]
            related[family]={'family':family,'title':group.get('title',family),
                             'backend':spec['backend'],'capability':spec['capability'],
                             'required_modules':spec['dependencies'],
                             'matched_catalog_locations':matches,
                             'declared_configuration':{key:cfg[key] for key in ('model_dir','workflow_path','output_node','preset') if key in cfg},
                             'companion_file_count':len(companions),'companion_files':companions[:20],
                             'runtime_verified':False}
    return {'id':identifier,'index':index,'filename':selected['filename'],
            'original_destination':selected['destination'],'families':sorted(related.values(),key=lambda row:row['family']),
            'family_count':len(related),'status':'catalog_relationships_found' if related else 'no_catalog_relationships',
            'network_checked':False,'inference_started':False,'configuration_changed':False,'update_allowed':False,
            'checked_at':studio.now(),
            'note':'Relaciones por repositorio y ruta remota exactos del catálogo, no un análisis del uso real de cada workflow. No lee pesos, importa dependencias del motor, consulta servidores ni ejecuta pruebas. Revisa archivos acompañantes, formato, dependencias y una muestra real antes de activar el candidato.'}
