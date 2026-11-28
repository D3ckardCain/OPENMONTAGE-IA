from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_studio as studio


def test_script_diagnostic_is_read_only_and_flags_missing_cues(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    pid=studio.create_production({'title':'Guion','brief':'Video nuevo','pipeline':'animated-explainer',
        'language':'es'})['project_id']
    path=studio.project_path(pid)/'artifacts/script.json'
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    base='/api/studio/script-diagnostic/'+pid
    assert client.get(base).json()['status']=='missing'
    script={'version':'1.0','title':'Guion original','total_duration_seconds':20,
        'sections':[{'id':'s1','label':'Apertura','text':'Una dos tres cuatro cinco seis siete ocho nueve diez',
            'start_seconds':0,'end_seconds':3,'speaker_directions':'Pausa antes de la idea',
            'source_ref':'Expediente local','enhancement_cues':[{'type':'diagram','description':'Esquema'}]},
            {'id':'s2','label':'Cierre','text':'Una idea para terminar','start_seconds':5,'end_seconds':10}]}
    studio.save_json(path,script)
    before=path.read_bytes()
    report=client.get(base+'?words_per_minute=120').json()
    assert report['status']=='review' and report['word_count']==14
    assert report['sections'][0]['speech_overrun_seconds']==2
    assert report['sections'][1]['gap_before_seconds']==2
    assert report['trailing_gap_seconds']==10
    assert report['source_ref_missing']==1 and report['voice_directions_missing']==1
    assert report['visual_cues_missing']==1 and path.read_bytes()==before
    assert client.get(base+'?words_per_minute=221').status_code==422
    script['sections'][1]['start_seconds']=2
    studio.save_json(path,script)
    assert client.get(base).status_code==400
