import xml.etree.ElementTree as ET
from copy import deepcopy
import pytest
from tools.graphics.sports_card import render, SportsCard


def report():
    scope={'season_id':'22','competition_id':'17'}
    q={'url':'https://fdh-api.fifa.com/v1/stats/season/22/players.json','retrieved_at':'2026-11-20T00:00:00Z'}
    return {'source':'FIFA','type':'collectible_card','ready_for_script':True,'scope':scope,'queries':[q],
            'records':[{'identity':{'name':'A <script> B','player_id':'1','fdh_player_id':'10'},
                        'facts':[{'metric':'Goals','value':0,'entity_id':'10','scope':scope,'source_url':q['url'],'retrieved_at':q['retrieved_at']}]}]}


def test_svg_escapes_text_preserves_zero_and_evidence():
    svg=render(report());root=ET.fromstring(svg)
    assert '<script>' not in svg
    assert any(x.text=='0' for x in root.findall('{http://www.w3.org/2000/svg}text'))
    assert 'source_url' in root.find('{http://www.w3.org/2000/svg}metadata').text


@pytest.mark.parametrize('change',[
    lambda r:r.update(ready_for_script=False),
    lambda r:r['records'][0]['facts'][0].update(value=None),
    lambda r:r['records'][0]['facts'][0].update(entity_id='20'),
    lambda r:r['records'][0]['facts'][0].update(scope={'season_id':'23'}),
    lambda r:r['records'][0]['facts'][0].update(source_url='https://evil.test/'),
    lambda r:r['records'][0]['facts'][0].update(retrieved_at='yesterday'),
])
def test_invalid_evidence_blocked(change):
    r=report();change(r)
    with pytest.raises(ValueError):render(r)


def test_tool_writes_only_after_validation(tmp_path):
    p=tmp_path/'card.svg';tool=SportsCard()
    assert tool.execute({'report':report(),'output_path':str(p)}).success
    ET.parse(p)
    p=tmp_path/'invalid.svg';r=report();r['ready_for_script']=False
    assert not tool.execute({'report':r,'output_path':str(p)}).success
    assert not p.exists()


def test_comparison_requires_same_metrics():
    r=report();r['type']='player_comparison'
    r['records']=[{'identity':{'name':'One','player_id':'1','fdh_player_id':'10'},'entity_id':'10','statistics':{'Goals':{'value':1}}},
                  {'identity':{'name':'Two','player_id':'2','fdh_player_id':'20'},'entity_id':'20','statistics':{'Goals':{'value':0}}}]
    ET.fromstring(render(r))
    r['records'][1]['statistics']={'Assists':{'value':0}}
    with pytest.raises(ValueError):render(r)


def test_png_export_has_dimensions_and_embedded_evidence(tmp_path):
    from PIL import Image
    import json
    p=tmp_path/'card.png'
    r=SportsCard().execute({'report':report(),'output_path':str(p)})
    assert r.success,r.error
    with Image.open(p) as im:
        assert im.size==(1080,1350) and im.format=='PNG'
        evidence=json.loads(im.info['openmontage_evidence'])
        assert evidence['records'][0]['facts'][0]['value']==0
        assert len(im.getcolors(1080*1350))>20


def test_png_comparison_export(tmp_path):
    from PIL import Image
    r=report();r['type']='player_comparison'
    r['records']=[{'identity':{'name':name,'player_id':pid,'fdh_player_id':fdh},'entity_id':fdh,'statistics':{'Goals':{'value':value}}}
                  for name,pid,fdh,value in [('Jugador Uno','1','10',2),('Jugador Dos','2','20',0)]]
    path=tmp_path/'comparison.png'
    out=SportsCard().execute({'report':r,'output_path':str(path)})
    assert out.success,out.error
    with Image.open(path) as im:assert im.size==(1080,1350)
