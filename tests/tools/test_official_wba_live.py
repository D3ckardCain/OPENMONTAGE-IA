import pytest
from tools.boxing import official_wba as wba
from tools.base_tool import _is_cacheable
from tools.tool_registry import ToolRegistry


def page():
    rows=''.join(f'<tr><td>{i}</td><td><a href="https://www.wbaboxing.com/wba-boxer-profile/?id={i}">BOXER {i}</a></td><td></td><td>CUB</td></tr>' for i in range(1,16))
    return '<h2>World Boxing Association Ranking as of OCTOBER 2026</h2><a href="#division1">HEAVYWEIGHT</a><div id="division1"><table><tr><td>Champion</td><td>NOT A RANKED BOXER</td></tr>'+rows+'</table></div>'


def test_parser_keeps_publication_month_distinct_and_excludes_champions():
    r=wba.parse(page(),{'url':wba.URL,'retrieved_at':'2026-11-20'})
    assert r['scope']['as_of_month']=='2026-10'
    assert len(r['records'])==15 and r['records'][0]['rank']==1
    assert r['records'][0]['country']=='CUB'
    assert not r['champions_included'] and not r['fight_record_included']
    assert r['queries'][0]['retrieved_at']=='2026-11-20'


@pytest.mark.parametrize('change',[
    lambda s:s.replace('OCTOBER','UNKNOWN'),
    lambda s:s.replace('<td>15</td>','<td>14</td>'),
    lambda s:s.replace('https://www.wbaboxing.com/wba-boxer-profile/?id=1"','https://evil.test/wba-boxer-profile/?id=1"'),
    lambda s:s.replace('as of OCTOBER 2026','not dated'),
])
def test_changed_schemas_rejected(change):
    with pytest.raises(ValueError):wba.parse(change(page()),{'url':wba.URL,'retrieved_at':'2026-11-20'})


def test_tool_resolves_names_queries_fresh_and_never_returns_old_data(monkeypatch):
    calls=[]
    def fetch():calls.append(1);return page(),{'url':wba.URL,'retrieved_at':str(len(calls))}
    monkeypatch.setattr(wba,'fetch',fetch)
    tool=wba.OfficialWBA()
    for _ in range(2):
        r=tool.execute({'action':'resolve_boxer','name':'Boxer 1'})
        assert r.success and r.data['records'][0]['status']=='resolved'
    assert len(calls)==2
    assert not _is_cacheable(tool,{'output_path':'x.json'})
    def fail():raise OSError('offline')
    monkeypatch.setattr(wba,'fetch',fail)
    r=tool.execute({'action':'rankings'})
    assert not r.success and not r.data['stale_fallback']


def test_discovery_and_inapplicable_inputs_rejected(monkeypatch):
    assert 'official_wba_live' in ToolRegistry().register_module(wba)
    monkeypatch.setattr(wba,'fetch',lambda:pytest.fail('Must reject before network'))
    t=wba.OfficialWBA()
    assert not t.execute({'action':'rankings','name':'One'}).success
    assert not t.execute({'action':'rankings','output_path':'stats.json'}).success
    assert not t.execute({'action':'resolve_boxer'}).success
