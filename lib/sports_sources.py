"""Agent-facing source routing. This directory never impersonates a live query."""
from copy import deepcopy

# Entry points are source locations, not promises of API availability or coverage.
_ROWS = [
 ('uefa','football','europe','UEFA','https://www.uefa.com/','official_uefa_live'),
 ('fifa','football','world','FIFA','https://www.fifa.com/','official_fifa_live'),
 ('conmebol','football','americas','CONMEBOL','https://gol.conmebol.com/',''),
 ('concacaf','football','americas','CONCACAF','https://www.concacaf.com/',''),
 ('afc','football','asia','AFC','https://www.the-afc.com/',''),
 ('caf','football','africa','CAF','https://www.cafonline.com/',''),
 ('ofc','football','oceania','OFC','https://www.oceaniafootball.com/',''),
 ('premier','football','europe','Premier League','https://www.premierleague.com/',''),
 ('laliga','football','europe','LaLiga','https://www.laliga.com/',''),
 ('bundesliga','football','europe','Bundesliga','https://www.bundesliga.com/',''),
 ('serie_a','football','europe','Serie A','https://www.legaseriea.it/',''),
 ('ligue1','football','europe','Ligue 1','https://ligue1.com/',''),
 ('portugal','football','europe','Liga Portugal','https://www.ligaportugal.pt/',''),
 ('eredivisie','football','europe','Eredivisie','https://eredivisie.nl/',''),
 ('jleague','football','asia','J.League','https://www.jleague.jp/',''),
 ('kleague','football','asia','K League','https://www.kleague.com/',''),
 ('saudi','football','arab','Saudi Pro League','https://www.spl.com.sa/en/stats',''),
 ('uae','football','arab','UAE Pro League','https://www.uaeproleague.ae/',''),
 ('qatar','football','arab','Qatar Stars League','https://www.qsl.qa/',''),
 ('mls','football','americas','MLS','https://www.mlssoccer.com/',''),
 ('ligamx','football','americas','Liga MX','https://ligamx.net/',''),
 ('brasil','football','americas','CBF','https://www.cbf.com.br/',''),
 ('argentina','football','americas','Liga Profesional','https://www.ligaprofesional.ar/',''),
 ('south_africa','football','africa','PSL','https://www.psl.co.za/',''),
 ('morocco','football','africa','FRMF','https://frmf.ma/',''),
 ('egypt','football','africa','Egyptian Pro League','https://egyptianproleague.com/',''),
 ('mlb','baseball','americas','MLB','https://www.mlb.com/stats','official_mlb_live'),
 ('npb','baseball','asia','NPB','https://npb.jp/',''),
 ('kbo','baseball','asia','KBO','https://www.koreabaseball.com/',''),
 ('wbsc','baseball','world','WBSC','https://www.wbsc.org/',''),
 ('wbc','boxing','world','WBC','https://wbcboxing.com/en/ratings-en/',''),
 ('wba','boxing','world','WBA','https://www.wbaboxing.com/',''),
 ('ibf','boxing','world','IBF','https://www.ibf-usba-boxing.com/',''),
 ('wbo','boxing','world','WBO','https://wboboxing.com/',''),
]

def catalog(sport=None, region=None):
    if sport not in (None,'football','boxing','baseball'): raise ValueError('Deporte no admitido')
    if region not in (None,'world','europe','americas','asia','africa','arab','oceania'): raise ValueError('Región no admitida')
    rows=[]
    for ident,kind,area,label,url,tool in _ROWS:
        if sport and kind!=sport: continue
        if region and area not in (region,'world'): continue
        rows.append(dict(id=ident,sport=kind,region=area,name=label,url=url,
            connector=tool or None,status='implemented_requires_live_check' if tool else 'integration_pending',
            coverage_verified=False))
    return deepcopy(dict(sources=rows,complete_global_coverage=False,statistics_included=False,
        instruction='El agente resuelve nombres e IDs, consulta en el momento y conserva fuente, fecha y alcance. Un directorio no es un conector. No pedir al usuario que busque estadísticas. Si no hay acceso comprobado, declarar bloqueo; no inventar ni reutilizar datos antiguos.',
        output_contract={'formats':['player_comparison','collectible_card'],
            'required_scope':['sport','competition','season_or_period','phase','category'],
            'each_fact':['entity_id','metric','value','unit','source_url','retrieved_at','scope'],
            'rules':['Ausente es null, nunca cero.','No sumar club y selección ni mezclar temporadas sin indicación expresa.',
                     'Separar estadísticas de rankings y de estimaciones.','No inferir historial completo a partir de un ranking.',
                     'Las imágenes necesitan procedencia y permiso de uso independientes de las estadísticas.',
                     'Reconsultar antes de una nueva producción; el expediente de una producción es evidencia fechada.']}))
