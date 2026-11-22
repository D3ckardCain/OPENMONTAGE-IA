"""Configured field names per adapter; never a claim of live player coverage."""


def configured_fields():
    from lib.football_statistics import FIFA_NAMES, UEFA_NAMES
    from tools.football.brasileirao import FIELDS
    from tools.football.eredivisie import RANKINGS as VI_RANKINGS
    from tools.football.ligamx import RANKINGS as AS_RANKINGS
    from tools.football.official_asian_cup import SECTIONS
    from tools.football.official_bundesliga import ALL_METRICS
    from tools.football.official_jleague import METRICS as JLEAGUE_METRICS
    from tools.football.official_mls import METRICS as MLS_METRICS
    from tools.football.official_premier import METRICS as PREMIER_METRICS

    return {
        'official_uefa_live': (set(UEFA_NAMES.values()), True),
        'official_fifa_live': (set(FIFA_NAMES.values()), True),
        'official_jleague_live': (set(JLEAGUE_METRICS), False),
        'official_mls_live': (set(MLS_METRICS), False),
        'official_bundesliga_live': (set(ALL_METRICS), False),
        'official_premier_live': (set(PREMIER_METRICS), False),
        'brasileirao_player_stats': (set(FIELDS), False),
        'classificacao_league_player_stats': (set(FIELDS), False),
        'eredivisie_player_stats': (set(VI_RANKINGS), False),
        'ligamx_player_stats': (set(AS_RANKINGS), False),
        'as_competition_player_stats': (set(AS_RANKINGS), False),
        'official_asian_cup_live': (set(SECTIONS.values()), False),
        'official_ofc_nations_cup_live': ({'goals'}, False),
    }
