"""Agent-facing source routing. This directory never impersonates a live query."""
from copy import deepcopy

FOOTBALL_METRIC_GROUPS = {
    'participation': ('matches_played', 'starts', 'substitute_appearances', 'minutes_played'),
    'attack': ('goals', 'assists', 'shots', 'shots_on_target', 'shots_off_target', 'shots_blocked',
               'penalties_taken', 'penalty_goals', 'penalties_missed', 'offsides', 'big_chances_missed', 'expected_goals'),
    'creation_and_passing': ('chances_created', 'big_chances_created', 'key_passes', 'expected_assists',
                             'passes_attempted', 'passes_completed', 'pass_accuracy', 'crosses_attempted',
                             'crosses_completed', 'long_balls_attempted', 'long_balls_completed',
                             'touches', 'dribbles_attempted', 'dribbles_completed'),
    'defence_and_duels': ('duels_contested', 'duels_won', 'aerial_duels_contested', 'aerial_duels_won',
                          'tackles_attempted', 'tackles_won', 'interceptions', 'recoveries',
                          'clearances', 'blocks', 'own_goals'),
    'goalkeeping': ('clean_sheets', 'goals_conceded', 'saves', 'save_percentage', 'penalties_saved'),
    'discipline': ('fouls_committed', 'fouls_suffered', 'yellow_cards', 'second_yellow_cards', 'red_cards'),
    'physical': ('distance_covered', 'sprints', 'top_speed'),
}
FOOTBALL_STANDARD_METRICS = tuple(metric for group in FOOTBALL_METRIC_GROUPS.values() for metric in group)
FOOTBALL_METRIC_LABELS_ES = {
    'matches_played': 'Partidos jugados', 'starts': 'Titularidades',
    'substitute_appearances': 'Entradas como suplente', 'minutes_played': 'Minutos jugados',
    'goals': 'Goles', 'assists': 'Asistencias', 'shots': 'Tiros',
    'shots_on_target': 'Tiros a puerta', 'shots_off_target': 'Tiros fuera',
    'shots_blocked': 'Tiros bloqueados', 'penalties_taken': 'Penaltis lanzados',
    'penalty_goals': 'Goles de penalti', 'penalties_missed': 'Penaltis fallados',
    'offsides': 'Fueras de juego', 'big_chances_missed': 'Grandes ocasiones falladas',
    'expected_goals': 'Goles esperados (xG)', 'chances_created': 'Ocasiones creadas',
    'big_chances_created': 'Grandes ocasiones creadas', 'key_passes': 'Pases clave',
    'expected_assists': 'Asistencias esperadas (xA)', 'passes_attempted': 'Pases intentados',
    'passes_completed': 'Pases completados', 'pass_accuracy': 'Precisión de pase',
    'crosses_attempted': 'Centros intentados', 'crosses_completed': 'Centros completados',
    'long_balls_attempted': 'Pases largos intentados',
    'long_balls_completed': 'Pases largos completados', 'touches': 'Toques de balón',
    'dribbles_attempted': 'Regates intentados', 'dribbles_completed': 'Regates completados',
    'duels_contested': 'Duelos disputados', 'duels_won': 'Duelos ganados',
    'aerial_duels_contested': 'Duelos aéreos disputados',
    'aerial_duels_won': 'Duelos aéreos ganados', 'tackles_attempted': 'Entradas intentadas',
    'tackles_won': 'Entradas ganadas', 'interceptions': 'Intercepciones',
    'recoveries': 'Recuperaciones', 'clearances': 'Despejes', 'blocks': 'Bloqueos',
    'own_goals': 'Autogoles', 'clean_sheets': 'Porterías a cero',
    'goals_conceded': 'Goles recibidos', 'saves': 'Paradas',
    'save_percentage': 'Porcentaje de paradas', 'penalties_saved': 'Penaltis detenidos',
    'fouls_committed': 'Faltas cometidas', 'fouls_suffered': 'Faltas recibidas',
    'yellow_cards': 'Tarjetas amarillas', 'second_yellow_cards': 'Segundas amarillas',
    'red_cards': 'Tarjetas rojas', 'distance_covered': 'Distancia recorrida',
    'sprints': 'Sprints', 'top_speed': 'Velocidad máxima',
}


# Entry points are source locations, not promises of API availability or coverage.
_ROWS = [
 ('uefa','football','europe','UEFA','https://www.uefa.com/','official_uefa_live'),
 ('euro_2024','football','europe','Eurocopa 2024','https://www.uefa.com/euro2024/','as_competition_player_stats'),
 ('fifa','football','world','FIFA','https://www.fifa.com/','official_fifa_live'),
 ('world_cup_2022','football','world','Mundial Qatar 2022','https://www.fifa.com/','as_competition_player_stats'),
 ('conmebol','football','americas','CONMEBOL','https://gol.conmebol.com/',''),
 ('copa_america','football','americas','Copa América','https://copaamerica.com/','as_competition_player_stats'),
 ('libertadores','football','americas','Copa Libertadores','https://www.conmebol.com/conmebol-libertadores/','classificacao_league_player_stats'),
 ('sudamericana','football','americas','Copa Sudamericana','https://www.conmebol.com/conmebol-sudamericana/','classificacao_league_player_stats'),
 ('concacaf','football','americas','CONCACAF','https://www.concacaf.com/',''),
 ('gold_cup','football','americas','Copa Oro','https://www.concacaf.com/gold-cup/','as_competition_player_stats'),
 ('afc','football','asia','AFC','https://www.the-afc.com/',''),
 ('asian_cup','football','asia','Copa Asiática AFC','https://www.the-afc.com/en/national/afc_asian_cup.html','official_asian_cup_live'),
 ('caf','football','africa','CAF','https://www.cafonline.com/',''),
 ('afcon','football','africa','Copa Africana de Naciones','https://www.cafonline.com/afcon/','as_competition_player_stats'),
 ('ofc','football','oceania','OFC','https://www.oceaniafootball.com/',''),
 ('ofc_nations_cup','football','oceania','Copa de Naciones OFC','https://www.oceaniafootball.com/ofc-mens-nations-cup-2024/','official_ofc_nations_cup_live'),
 ('premier','football','europe','Premier League','https://www.premierleague.com/','official_premier_live'),
 ('laliga','football','europe','LaLiga','https://www.laliga.com/','classificacao_league_player_stats'),
 ('bundesliga','football','europe','Bundesliga','https://www.bundesliga.com/','official_bundesliga_live'),
 ('bundesliga_2','football','europe','2. Bundesliga','https://www.bundesliga.com/en/2bundesliga','official_bundesliga_live'),
 ('serie_a','football','europe','Serie A','https://www.legaseriea.it/','classificacao_league_player_stats'),
 ('ligue1','football','europe','Ligue 1','https://ligue1.com/','classificacao_league_player_stats'),
 ('portugal','football','europe','Liga Portugal','https://www.ligaportugal.pt/','classificacao_league_player_stats'),
 ('eredivisie','football','europe','Eredivisie','https://eredivisie.nl/','eredivisie_player_stats'),
 ('jleague','football','asia','J.League','https://www.jleague.jp/','official_jleague_live'),
 ('kleague','football','asia','K League','https://www.kleague.com/',''),
 ('saudi','football','arab','Saudi Pro League','https://www.spl.com.sa/en/stats','as_competition_player_stats'),
 ('uae','football','arab','UAE Pro League','https://www.uaeproleague.ae/',''),
 ('qatar','football','arab','Qatar Stars League','https://www.qsl.qa/',''),
 ('mls','football','americas','MLS','https://www.mlssoccer.com/','official_mls_live'),
 ('ligamx','football','americas','Liga MX','https://ligamx.net/','ligamx_player_stats'),
 ('brasil','football','americas','CBF','https://www.cbf.com.br/','brasileirao_player_stats'),
 ('argentina','football','americas','Liga Profesional','https://www.ligaprofesional.ar/','classificacao_league_player_stats'),
 ('south_africa','football','africa','PSL','https://www.psl.co.za/',''),
 ('morocco','football','africa','FRMF','https://frmf.ma/',''),
 ('egypt','football','africa','Egyptian Pro League','https://egyptianproleague.com/',''),
 ('mlb','baseball','americas','MLB','https://www.mlb.com/stats','official_mlb_live'),
 ('npb','baseball','asia','NPB','https://npb.jp/',''),
 ('kbo','baseball','asia','KBO','https://www.koreabaseball.com/',''),
 ('wbsc','baseball','world','WBSC','https://www.wbsc.org/',''),
 ('wbc','boxing','world','WBC','https://wbcboxing.com/en/ratings-en/',''),
 ('wba','boxing','world','WBA','https://www.wbaboxing.com/','official_wba_live'),
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
            connector=tool or None,status='source_inspection_only' if tool=='official_spl_source_status' else 'implemented_requires_live_check' if tool else 'integration_pending',
            coverage_verified=False))
    football_contract = {
        'metrics': list(FOOTBALL_STANDARD_METRICS),
        'missing_value': None,
        'metric_groups': {group: list(metrics) for group, metrics in FOOTBALL_METRIC_GROUPS.items()},
        'source_discovery': {
            'official_bundesliga_live': 'Consulta por nombre 19 rankings públicos de 2024/25 en ambas divisiones alemanas. Tres rankings de diez entradas y 16 vistas de cinco.',
            'official_premier_live': 'Líderes de 20 métricas hasta la jornada 29 de 2024/25. Busca el nombre publicado y añade el club entre paréntesis si hay ambigüedad.',
            'classificacao_league_player_stats': 'Nueve métricas en LaLiga, Premier League, Serie A italiana, Ligue 1 y Primeira Liga 2025/26, y Brasileirão, Primera División argentina, Libertadores y Sudamericana 2025. En Argentina y las copas usa la edición publicada sin atribuir cifras a fases separadas. Busca y reúne jugadores por bloques de tres páginas. Con search_by_name consulta cada nombre publicado por separado.',
            'brasileirao_player_stats': 'Brasileirão Série A 2025. Classificação Geral aporta nueve métricas. Busca por bloques de tres páginas y reúne los resultados. Usa max_blocks para ampliar la búsqueda y next_page como start_page para seguir desde otro bloque.',
            'eredivisie_player_stats': 'Rankings de goles, asistencias, amarillas y rojas de Eredivisie 2025/26 publicados por Voetbal International. Añade el club entre paréntesis si hay varias filas.',
            'ligamx_player_stats': 'Liga MX Apertura 2025 y Clausura 2026. Consulta rankings de AS por lotes de una a seis métricas. Cada cifra conserva su URL y temporada.',
            'as_competition_player_stats': 'AS publica rankings por métrica de Liga Saudí 2025/26 (saudi), Copa Africana 2025 (afcon), Copa Oro 2025 (gold_cup) y Copa América 2024 (copa_america). Se verificaron 25 rankings con filas por edición. En Copa América quedó vacío el ranking de goles en propia puerta. En las otras tres ediciones quedó vacío el de penaltis lanzados. También admite las fases finales de Eurocopa 2024 (euro_2024) y Mundial Qatar 2022 (world_cup_2022). Consulta hasta seis por solicitud. Si hay fallos, shared_metrics indica qué cifras comunes siguen disponibles para una selección explícita en la pieza visual.',
            'official_asian_cup_live': 'Informe oficial de líderes de la Copa Asiática Qatar 2023. Diez rankings de cinco filas; identifica al jugador por nombre publicado y selección.',
            'official_ofc_nations_cup_live': 'Goleadores de la Copa de Naciones OFC masculina 2024. Suma los goles atribuidos por la OFC en sus cinco tablas de fases.',
            'official_mls_live': 'Consulta por nombre las cifras de los goleadores por club de la temporada regular 2025. El catálogo de jugadores completo queda pendiente.',
            'official_uefa_live': 'Usa metrics=standard en consultas por nombre para solicitar las equivalencias comunes. Consulta definitions para detectar estadísticas oficiales adicionales de PLAYER.',
            'official_fifa_live': 'Omite metrics en player_statistics, compare_players o collectible_card para consultar el conjunto publicado.',
            'official_jleague_live': 'Usa metrics=all para consultar todos los rankings integrados; consulta tool_info para ver las métricas admitidas.',
        },
        'instruction': ('Para comparar jugadores usa football_comparison y presenta todas las cifras antes de seleccionar la postal o el video. '
                        'Usa competition para la competición sin eliminatorias y player para el historial por fases. '
                        'Usa el mismo conjunto de métricas para todas las ligas, copas y torneos de fútbol. '
                        'Relaciona los nombres del proveedor con las métricas comunes solo si su definición coincide. '
                        'Conserva toda métrica adicional publicada en el expediente con su clave original y procedencia. '
                        'Aplica cada métrica comparable nueva al mismo catálogo común de todas las competiciones. '
                        'Si falta una cifra o no aplica al jugador, conserva su campo con null. '
                        'Si el usuario pide una métrica concreta, puedes consultar ese subconjunto. '
                        'Si la pieza visual tiene un límite de espacio, muestra el mismo subconjunto para todos '
                        'los jugadores y conserva el expediente completo.'),
    }
    return deepcopy(dict(sources=rows,complete_global_coverage=False,statistics_included=False,
        football_standard=football_contract if sport in (None, 'football') else None,
        instruction='El agente resuelve nombres e IDs, consulta en el momento y conserva fuente, fecha y alcance. Un directorio no es un conector. No pedir al usuario que busque estadísticas. Si no hay acceso comprobado, declarar bloqueo; no inventar ni reutilizar datos antiguos.',
        output_contract={'formats':['player_comparison','collectible_card'],
            'required_scope':['sport','competition','season_or_period','phase','category'],
            'each_fact':['entity_id','metric','value','unit','source_url','retrieved_at','scope'],
            'rules':['Ausente es null, nunca cero.','No sumar club y selección ni mezclar temporadas sin indicación expresa.',
                     'Separar estadísticas de rankings y de estimaciones.','No inferir historial completo a partir de un ranking.',
                     'Las imágenes necesitan procedencia y permiso de uso independientes de las estadísticas.',
                     'Reconsultar antes de una nueva producción; el expediente de una producción es evidencia fechada.']}))
