import pytest
from lib import production_studio as studio
from lib.language_versions import create_versions


@pytest.fixture
def source(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    studio.save_json(tmp_path/'base/production_request.json',{'title':'Tema original','brief':'Investigar el tema','pipeline':'animated-explainer','language':'es','reference':'https://example.org','automatic':True})
    captured=[]
    def create(data):
        pid='version-'+str(len(captured));captured.append(data)
        studio.save_json(tmp_path/pid/'production_request.json',data)
        return {'project_id':pid}
    monkeypatch.setattr(studio,'create_production',create)
    return captured


def test_versions_are_independent_guided_requests_and_repeat_is_reused(source):
    report=create_versions('base',['en','ko'])
    assert [item['status'] for item in report['versions']]==['created','created']
    assert all(item['automatic'] is False for item in source)
    assert source[1]['language']=='ko' and 'canciones' in source[1]['brief']
    assert source[0]['reference']=='https://example.org'
    assert report['generation_started'] is False and report['media_copied'] is False
    assert create_versions('base',['en'])['versions'][0]['status']=='existing'
    assert len(source)==2


def test_without_football_selection_keeps_original_version_fingerprint(source):
    import hashlib
    import json
    request=studio.read_json(studio.project_path('base')/'production_request.json')
    original={key:request.get(key) for key in ('title','brief','pipeline','reference','language')}
    fingerprint=hashlib.sha256(json.dumps(original,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    created=create_versions('base',['en'])['versions'][0]
    ledger=studio.read_json(studio.project_path('base')/'language_versions.json')
    assert ledger['versions'][fingerprint+':en']['project_id']==created['project_id']


def test_localized_version_preserves_channel_evidence_without_global_registry(source):
    import shutil
    from lib.channel_dossiers import save,read,_digest
    from lib.channel_ideas import create
    from lib.video_observations import add
    from lib.project_channel_evidence import verified
    from lib.project_video_observations import verified_rows
    from lib.language_versions import list_versions
    channel='UC'+'v'*22
    report={'source':'YouTube Data API','channel_id':channel,'retrieved_at_utc':'2026-11-22T00:00:00Z',
            'since_utc':'2026-10-23T00:00:00Z','cutoff_at_utc':'2026-11-22T00:00:00Z',
            'complete_period':True,'publications':[{'id':'abcdefghijk','title':'Video fuente','viewCount':100}]}
    saved=save(report);snapshot=read(channel,saved['id'])
    idea=create({'channel_id':channel,'snapshot_id':saved['id'],'video_ids':['abcdefghijk'],
                 'title':'Tema propio documentado','angle':'Investigar un enfoque nuevo y comprobar las fuentes del tema.',
                 'audience':'Creadores','language':'es','format':'long'})
    rows=[add({'video_url':'https://www.youtube.com/watch?v=abcdefghijk','views':100,'vph':2,
               'engagement_percent':None,'outlier_ratio':None,'seo_score':None,'notes':''})]
    base=studio.project_path('base');request=studio.read_json(base/'production_request.json')
    request.update(reference='https://www.youtube.com/watch?v=abcdefghijk',
                   research_idea={'channel_id':channel,'snapshot_id':saved['id'],'idea_id':idea['id']},
                   research_idea_sha256=_digest(idea),research_observations_sha256=_digest(rows))
    studio.save_json(base/'production_request.json',request)
    studio.save_json(base/'artifacts/channel_research_snapshot.json',snapshot)
    studio.save_json(base/'artifacts/channel_idea_source.json',idea)
    studio.save_json(base/'artifacts/video_observations_snapshot.json',rows)
    shutil.rmtree(studio.CONFIG_DIR/'research')
    entry=create_versions('base',['en'])['versions'][0]
    assert entry['status']=='created' and 'source_channel_research' in entry
    child=studio.project_path(entry['project_id']);child_request=studio.read_json(child/'production_request.json')
    assert child_request['language']=='en' and child_request['research_idea']==request['research_idea']
    assert verified(child,child_request)[0]==snapshot
    assert verified_rows(child,child_request)==rows
    from lib.language_versions import selection_provenance_problem
    assert selection_provenance_problem(child) is None
    assert create_versions('base',['en'])['versions'][0]['status']=='existing'
    tampered=studio.read_json(child/'artifacts/video_observations_snapshot.json')
    tampered[0]['vph']=999
    studio.save_json(child/'artifacts/video_observations_snapshot.json',tampered)
    assert list_versions('base')['versions'][0]['status']=='research_changed'
    assert list_versions('base')['versions'][0]['can_enqueue'] is False
    assert create_versions('base',['en'])['versions'][0]['status']=='research_changed'
    assert selection_provenance_problem(child)
    from lib import production_agent as agent
    with pytest.raises(ValueError,match='investigación'):
        agent.start(entry['project_id'])


def test_localized_version_inherits_selected_evidence_and_new_selection_gets_new_version(source,monkeypatch):
    from lib.football_comparison_dossier import latest_for_agent, save_to_project
    from tools.football.ligamx import ranking_urls, tournament_scope
    scope=tournament_scope(('world_cup_2022',2022,'final_tournament'))
    urls=ranking_urls(('world_cup_2022',2022,'final_tournament'))
    queries=[{'url':urls[metric],'retrieved_at':'2026-11-22'} for metric in ('goals','shots')]
    records=[]
    for name in ('A','B'):
        facts=[{'metric':metric,'value':value,'entity_id':name,'scope':scope,
                'source_url':query['url'],'retrieved_at':query['retrieved_at']}
               for (metric,value),query in zip((('goals',2),('shots',4)),queries)]
        records.append({'entity_id':name,'identity':{'entity_id':name,'name':name},
                        'statistics':{'goals':2,'shots':4},'facts':facts})
    report={'source':'AS','type':'player_comparison','scope':scope,'queries':queries,
            'records':records,'ready_for_script':True,'failed_metrics':{},'unresolved':[]}
    first=save_to_project('base',report,['goals'])['selection']
    en=create_versions('base',['en'])['versions'][0]
    assert en['source_football_selection']['selection_id']==first['selection_id']
    inherited=latest_for_agent(en['project_id'],include_report=True)
    assert inherited['report']==report and inherited['selected_metrics']==['goals']
    from lib.language_versions import list_versions
    assert list_versions('base')['versions'][0]['status']=='existing'
    assert create_versions('base',['en'])['versions'][0]['status']=='existing'
    second=save_to_project('base',report,['shots'])['selection']
    new=create_versions('base',['en'])['versions'][0]
    assert new['status']=='created' and new['project_id']!=en['project_id']
    assert new['source_football_selection']['selection_id']==second['selection_id']
    assert latest_for_agent(en['project_id'])['selected_metrics']==['goals']
    assert latest_for_agent(new['project_id'])['selected_metrics']==['shots']
    save_to_project(en['project_id'],report,['shots'])
    changed=next(row for row in list_versions('base')['versions'] if row['project_id']==en['project_id'])
    assert changed['status']=='selection_changed' and changed['can_enqueue'] is False
    from lib import production_queue as queue
    monkeypatch.setattr(queue,'WORKER',None)
    queue.enqueue(en['project_id'])
    inspected=queue.inspect()
    assert any('selección deportiva' in problem for problem in inspected['items'][0]['problems'])
    with pytest.raises(ValueError,match='selección deportiva'):
        queue.start()
    from lib import production_agent as agent
    with pytest.raises(ValueError,match='selección deportiva'):
        agent.start(en['project_id'])
    with pytest.raises(ValueError,match='selección deportiva'):
        agent.approve(en['project_id'])
    assert create_versions('base',['en'])['versions'][0]['project_id']==new['project_id']
    save_to_project('base',report,['goals'])
    assert create_versions('base',['en'])['versions'][0]['status']=='selection_changed'


@pytest.mark.parametrize('languages',[[],['es'],['en','EN'],['../../bad'],['en']*11,'en'])
def test_invalid_versions_create_nothing(source,languages):
    with pytest.raises(ValueError):create_versions('base',languages)
    assert source==[]


def test_missing_existing_version_is_reported_without_duplicate(source):
    result=create_versions('base',['en'])
    project=studio.project_path(result['versions'][0]['project_id'])
    (project/'production_request.json').unlink()
    assert create_versions('base',['en'])['versions'][0]['status']=='unavailable'
    assert len(source)==1


def test_api_only_accepts_languages(source):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    assert client.post('/api/studio/language-versions/base',json={'languages':['en'],'automatic':True}).status_code==400
    assert client.post('/api/studio/language-versions/base',json={'languages':['en']}).json()['generation_started'] is False


def test_partial_failure_keeps_prepared_version_registered(source,monkeypatch):
    original=studio.create_production
    def create(data):
        if data['language']=='ko':raise ValueError('Fixture failure')
        return original(data)
    monkeypatch.setattr(studio,'create_production',create)
    result=create_versions('base',['en','ko','de'])
    assert [entry['status'] for entry in result['versions']]==['created','failed']
    assert create_versions('base',['en'])['versions'][0]['status']=='existing'
    assert len(source)==1


def test_list_versions_survives_reopening_and_marks_unavailable(source):
    from lib.language_versions import list_versions
    result=create_versions('base',['en','ko'])
    assert len(list_versions('base')['versions'])==2
    (studio.project_path(result['versions'][0]['project_id'])/'production_request.json').unlink()
    report=list_versions('base')
    assert [entry['status'] for entry in report['versions']]==['unavailable','existing']
    assert report['generation_started'] is False
    assert len(source)==2


def test_requirements_do_not_probe_runtimes_or_certify_languages(source,monkeypatch):
    from lib import model_adapters
    from lib.language_versions import local_requirements
    monkeypatch.setattr(model_adapters,'CATALOG',{'voice':{},'translator':{},'video':{}})
    monkeypatch.setattr(model_adapters,'spec',lambda family:{'capability':{'voice':'tts','translator':'translation','video':'video_generation'}[family]})
    calls=[]
    def diagnostics(family,probe):
        assert probe is False
        calls.append(family)
        return {'ready':True,'model_dir':'/fixture','problems':[],'required_modules':['fixture']}
    monkeypatch.setattr(model_adapters,'diagnostics',diagnostics)
    report=local_requirements('base')
    assert calls==['voice','translator']
    assert report['generation_started'] is False and report['network_requests_started']==0
    assert all(not item['language_support_verified'] and not item['runtime_checked'] for item in report['candidates'])


def test_version_status_summary_preserves_evidence_without_starting_work(source):
    from lib.language_versions import list_versions
    result=create_versions('base',['en','ko','de'])
    en,ko,de=[studio.project_path(entry['project_id']) for entry in result['versions']]
    studio.save_json(en/'job.json',{'status':'rendered','message':'Terminado','updated_at':'fixture-time'})
    studio.save_json(en/'render_verification.json',{'status':'passed'})
    studio.save_json(en/'final_delivery.json',{'copied':True})
    studio.save_json(ko/'job.json',{'status':'awaiting_human','message':'Revisa voz'})
    studio.save_json(de/'job.json',{'status':'blocked','message':'Falta modelo'})
    ledger=studio.project_path('base')/'language_versions.json';before=ledger.read_bytes()
    report=list_versions('base')
    assert report['summary']=={'total':3,'rendered':1,'awaiting_human':1,'blocked':1,'unavailable':0}
    assert report['versions'][0]['can_enqueue'] is False
    assert report['versions'][0]['verification_status']=='passed'
    assert report['versions'][0]['final_copy_registered'] is True
    assert report['versions'][1]['can_enqueue'] is True
    assert report['versions'][1]['message']=='Revisa voz'
    assert ledger.read_bytes()==before and len(source)==3


def test_corrupt_version_does_not_hide_other_versions(source):
    from lib.language_versions import list_versions
    result=create_versions('base',['en','ko'])
    (studio.project_path(result['versions'][0]['project_id'])/'job.json').write_text('{broken')
    report=list_versions('base')
    assert report['summary']['unavailable']==1
    assert report['versions'][0]['can_enqueue'] is False
    assert report['versions'][1]['status']=='existing'


def test_confirmed_original_language_is_excluded_including_regional_variants(source):
    from lib.reference_language import confirm
    confirm('base','en')
    with pytest.raises(ValueError,match='original confirmado'):create_versions('base',['ko','en-US'])
    assert source==[]
    assert create_versions('base',['ko'])['versions'][0]['status']=='created'
