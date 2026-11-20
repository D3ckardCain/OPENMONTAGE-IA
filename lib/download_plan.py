"""Review-only missing-inventory plan, grouped for separate FDM downloads."""
from collections import Counter
from urllib.parse import urlsplit
from lib import production_studio as studio


def plan():
    catalog=studio.resource_catalog()
    inventories=catalog['inventories']
    if len({item['Serie'] for item in inventories})<2:
        raise ValueError('Importa al menos dos inventarios de discos distintos antes de preparar descargas')
    folders={};seen=set();excluded=Counter();needs_url=[]
    for group in catalog['groups']:
        for item in group['files']:
            if item['status']!='not_recorded':excluded[item['status']]+=1;continue
            url=item.get('download_url');parsed=urlsplit(url or '')
            if parsed.scheme!='https' or not parsed.netloc or parsed.username or parsed.password:
                needs_url.append({'family':group['id'],'filename':item['filename']});continue
            identity=(item['destination_folder'],item['filename'])
            if identity in seen:continue
            seen.add(identity)
            folders.setdefault(item['destination_folder'],[]).append({'family':group['id'],'filename':item['filename'],'url':url,'size_bytes':item.get('size_bytes')})
    names=Counter(item['filename'].casefold() for files in folders.values() for item in files)
    collisions=sorted(name for name,total in names.items() if total>1)
    return {'inventories':inventories,'folders':[{'destination_folder':folder,'files':files} for folder,files in sorted(folders.items())],
        'planned_files':sum(len(files) for files in folders.values()),'excluded':dict(excluded),'without_download_url':needs_url,
        'filename_collisions_across_folders':collisions,'downloads_started':0,
        'note':'No constan en los inventarios seleccionados por la app; esto no demuestra que falten ahora. Revisa fechas, discos y descargas posteriores del chat. Descarga cada carpeta por separado: FDM puede rechazar nombres repetidos entre carpetas.'}
