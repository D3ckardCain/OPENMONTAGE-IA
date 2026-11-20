import xml.etree.ElementTree as ET
from copy import deepcopy
import pytest
from tools.graphics.sports_card import render


def example():
    sources=[{'url':f'https://compstats.uefa.com/v2/player-ranking?offset={n}','consultado_utc':'2026-11-20T00:00:00Z'} for n in (0,50)]
    return {'fuente':'UEFA','tipo':'comparativa_jugadores','ready_for_script':True,'competicion':'champions',
            'alcance':{'competitionId':'1','seasonYear':2024,'phase':'TOURNAMENT'},'consultas':sources,
            'registros':[{'id':pid,'nombre':name,'estadisticas':{'goals':value},'fuente_estadisticas':deepcopy(source)}
                         for pid,name,value,source in [('1','Jugador Uno','8',sources[0]),('2','Jugador Dos','0',sources[1])]]}


def test_uefa_comparison_uses_exact_row_sources_and_preserves_string_zero():
    root=ET.fromstring(render(example()))
    texts=[x.text for x in root.findall('{http://www.w3.org/2000/svg}text')]
    assert '0' in texts and '8' in texts
    assert any('UEFA' in text and '2024' in text for text in texts)
    metadata=root.find('{http://www.w3.org/2000/svg}metadata').text
    assert 'offset=0' in metadata and 'offset=50' in metadata


def test_missing_page_or_ambiguous_scope_blocks_visual():
    r=example();r['registros'][0].pop('fuente_estadisticas')
    with pytest.raises(ValueError):render(r)
    r=example();r['alcance']['phase']=None
    with pytest.raises(ValueError):render(r)
    r=example();r['ready_for_script']=False
    with pytest.raises(ValueError):render(r)
