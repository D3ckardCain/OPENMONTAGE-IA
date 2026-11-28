import copy
import pytest
from lib.cultural_audio import validate_cultural_audio
from lib.checkpoint import validate_checkpoint, CheckpointValidationError

def audit():
    return dict(source_id='sha256:fixture',duration_seconds=10,target_locale='ko-KR',source_review_complete=True,segments=[dict(id='1',start=0,end=10,kind='song',language='ko',evidence='Final mix listened at 0-10s',action='replace',rationale='Licensed Korean song fits the intended scene',resolved=True,rights_cleared=True)])

def test_complete_review():
    validate_cultural_audio(audit())

@pytest.mark.parametrize('change', [dict(start=1),dict(end=9),dict(end=11),dict(end=0),dict(kind='unknown'),dict(language='unknown'),dict(action='review'),dict(resolved=False),dict(rights_cleared=False),dict(end=float('nan'))])
def test_incomplete_review_rejected(change):
    value=audit();value['segments'][0].update(change)
    with pytest.raises(Exception):validate_cultural_audio(value)

def test_simultaneous_tracks_allowed_but_duplicate_ids_rejected():
    value=audit();item=copy.deepcopy(value['segments'][0]);item['id']='2';value['segments'].append(item)
    validate_cultural_audio(value)
    item['id']='1'
    with pytest.raises(ValueError,match='Duplicate'):validate_cultural_audio(value)

@pytest.mark.parametrize("stage,canonical", [("assets","asset_manifest"),("edit","edit_decisions"),("compose","render_report"),("publish","publish_log")])
def test_real_checkpoint_requires_resolved_audio(stage, canonical):
    import json
    from pathlib import Path
    samples = json.loads((Path(__file__).parents[1] / "fixtures/localization_checkpoint_artifacts.json").read_text())
    value = dict(version="1.0", project_id="locale-fixture", stage=stage,
        status="completed", timestamp="2026-11-14T00:00:00Z",
        pipeline_type="localization-dub", artifacts={canonical:samples[canonical]})
    with pytest.raises(CheckpointValidationError,match="requires cultural_audio_audit"):
        validate_checkpoint(value)
    value["artifacts"]["cultural_audio_audit"] = audit()
    validate_checkpoint(value)
    value["artifacts"]["cultural_audio_audit"]["segments"][0]["resolved"] = False
    with pytest.raises(CheckpointValidationError, match="blocked"):
        validate_checkpoint(value)


def test_manifest_requires_audit_at_each_downstream_stage():
    from lib.pipeline_loader import load_pipeline_readonly
    manifest = load_pipeline_readonly("localization-dub")
    assert manifest["orchestration"]["budget_default_usd"] == 0
    stages = {stage["name"]: stage for stage in manifest["stages"]}
    assert "cultural_audio_audit" in stages["assets"]["produces"]
    for name in ("edit", "compose", "publish"):
        assert "cultural_audio_audit" in stages[name]["required_artifacts_in"]
