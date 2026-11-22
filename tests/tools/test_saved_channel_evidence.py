from lib import production_studio as studio
from lib.channel_dossiers import save
from lib.channel_ideas import create
from tools.research.saved_channel_evidence import SavedChannelEvidence
from tools.tool_registry import ToolRegistry
from tools.research import saved_channel_evidence

CHANNEL='UC'+'a'*22


def test_agent_reads_verified_snapshot_in_parts(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path)
    report={'source':'YouTube Data API','channel_id':CHANNEL,'retrieved_at_utc':'2026-11-22T00:00:00Z',
            'since_utc':'2026-10-23T00:00:00Z','cutoff_at_utc':'2026-11-22T00:00:00Z',
            'complete_period':False,'analysis':{'median_views':100},
            'publications':[{'id':f'v{i:010d}','title':f'Video {i}','viewCount':100+i} for i in range(3)]}
    source=save(report)
    idea=create({'channel_id':CHANNEL,'snapshot_id':source['id'],'video_ids':['v0000000000'],
                 'title':'Una propuesta nueva para creadores','angle':'Un enfoque original con investigación de fuentes y producción local verificable.',
                 'audience':'Creadores','language':'es','format':'long'})
    tool=SavedChannelEvidence()
    assert tool.name in ToolRegistry().register_module(saved_channel_evidence)
    first=tool.execute({'channel_id':CHANNEL,'snapshot_id':source['id'],'idea_id':idea['id'],'limit':2})
    assert first.success and first.data['publication_total']==3 and first.data['next_offset']==2
    assert first.data['idea']['id']==idea['id'] and first.data['snapshot_sha256']==source['report_sha256']
    last=tool.execute({'channel_id':CHANNEL,'snapshot_id':source['id'],'offset':2,'limit':2})
    assert last.success and len(last.data['publications'])==1 and last.data['next_offset'] is None
    assert not tool.execute({'channel_id':CHANNEL,'snapshot_id':source['id'],'limit':51}).success
