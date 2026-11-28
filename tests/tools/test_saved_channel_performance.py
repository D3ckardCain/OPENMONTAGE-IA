from lib import production_studio as studio
from lib.channel_performance import FIELDS, import_csv
from tools.research.saved_channel_performance import SavedChannelPerformance
from tools.research import saved_channel_performance
from tools.tool_registry import ToolRegistry


def test_agent_reads_periods_in_parts_and_rejects_altered_record(tmp_path, monkeypatch):
    monkeypatch.setattr(studio, 'CONFIG_DIR', tmp_path)
    header = ','.join(FIELDS)
    rows = [f'https://www.youtube.com/watch?v=abcdefghijk,2026-11-{day:02d},2026-11-{day:02d},100,4,20,10,20'
            for day in (1, 2, 3)]
    record = import_csv(header + '\n' + '\n'.join(rows) + '\n')
    tool = SavedChannelPerformance()
    assert tool.name in ToolRegistry().register_module(saved_channel_performance)
    first = tool.execute({'import_id': record['id'], 'limit': 2})
    assert first.success and first.data['row_total'] == 3 and first.data['next_offset'] == 2
    assert first.data['source'].startswith('CSV aportado')
    assert first.data['rows'][0]['clicks_per_impression_percent'] == 4
    last = tool.execute({'import_id': record['id'], 'offset': 2, 'limit': 2})
    assert last.success and len(last.data['rows']) == 1 and last.data['next_offset'] is None
    assert not tool.execute({'import_id': record['id'], 'limit': 51}).success
    assert not tool.execute({'import_id': record['id'], 'unexpected': 1}).success

    path = tmp_path / 'research/channel_performance' / (record['id'] + '.json')
    path.write_text(path.read_text().replace('"views": 20', '"views": 999'), encoding='utf-8')
    assert not tool.execute({'import_id': record['id']}).success
