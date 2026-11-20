import pytest
from lib import production_studio as studio

@pytest.fixture
def setup(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'REPO_ROOT',tmp_path)
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    paths=['C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/model/'+name for name in ('known.bin','unknown.bin','different.bin','missing.bin')]
    studio.save_json(tmp_path/'docs/models/fixture.json',{'groups':[{'id':'fixture','files':paths}],'files':[{'destination':path,'path':path.rsplit('/',1)[-1],'size_bytes':None if 'unknown' in path else 10,'url':'https://example.org/file'} for path in paths]})
    for serial in ('ADATA','SEAGATE'):
        studio.import_inventory({'Serie':serial,'Fecha':'fixture-date','Ficheros':[{'FullName':path.replace('C:','D:'),'Length':20 if 'different' in path else 10} for path in paths[:3]]})
    return tmp_path


def test_unknown_sizes_remain_registered_in_both_inventories(setup):
    files=studio.resource_catalog()['groups'][0]['files']
    assert [item['status'] for item in files]==['recorded_size_match','recorded_path_size_unknown','recorded_size_mismatch','not_recorded']
    assert files[1]['size_verified'] is False
    assert {match['serial'] for match in files[1]['inventory_path_matches']}=={'ADATA','SEAGATE'}
    assert files[1]['inventory_matches']==[]
    assert files[0]['size_verified'] is True and len(files[0]['inventory_matches'])==2
    assert files[3]['inventory_path_matches']==[]
    assert all(not item['inference_verified'] for item in files)


def test_other_locations_require_known_positive_size_and_do_not_claim_identity(setup):
    studio.import_inventory({'Serie':'OTHER','Ficheros':[{'FullName':'E:/Downloads/missing.bin','Length':10},{'FullName':'E:/Downloads/unknown.bin','Length':10}]})
    files=studio.resource_catalog()['groups'][0]['files']
    candidate=files[3]
    assert candidate['status']=='possible_elsewhere_size_match'
    assert candidate['inventory_other_locations'][0]['path']=='E:/Downloads/missing.bin'
    assert candidate['size_verified'] is False and candidate['inventory_matches']==[]
    assert files[1]['inventory_other_locations']==[]


def test_candidate_limit_and_case_insensitive_expected_path(setup):
    studio.import_inventory({'Serie':'MANY','Ficheros':[{'FullName':f'E:/folder-{i}/missing.bin','Length':10} for i in range(25)]+[{'FullName':'E:/openmontaje-ia/descargas_modelos/model/KNOWN.BIN','Length':10}]})
    files=studio.resource_catalog()['groups'][0]['files']
    assert len(files[3]['inventory_other_locations'])==20
    assert files[3]['other_locations_count']==25 and files[3]['other_locations_partial'] is True
    assert any(match['serial']=='MANY' for match in files[0]['inventory_matches'])
