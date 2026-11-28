import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from schemas.artifacts import validate_artifact
from tools.publishers.local_plan import LocalPublishPlan
from tools.tool_registry import ToolRegistry


CREATED = "2026-11-28T15:00:00+00:00"
TARGET = {
    "platform": "youtube",
    "destination_id": "UC-synthetic-channel",
    "visibility": "private",
    "timezone": "UTC",
    "scheduled_for": "2026-12-01T10:00:00+00:00",
    "title": "Synthetic QA",
    "description": "Fixture only",
    "tags": ["qa"],
}


def setup_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    media = project / "export.mp4"
    media.write_bytes(b"synthetic-fixture-not-a-video")
    return project, media


def call(project, **overrides):
    inputs = {
        "project_dir": str(project),
        "plan_id": "qa-plan",
        "revision": 1,
        "media_path": "export.mp4",
        "created_at": CREATED,
        "targets": [dict(TARGET)],
    }
    inputs.update(overrides)
    return LocalPublishPlan().execute(inputs)


def test_persists_local_draft_bound_to_media_and_explicit_destination(tmp_path):
    project, media = setup_project(tmp_path)
    result = call(project)
    assert result.success
    saved = json.loads(Path(result.data["plan_path"]).read_text(encoding="utf-8"))
    validate_artifact("local_publish_plan", saved)
    assert saved["status"] == "draft"
    assert saved["execution"] == "local_plan_only"
    assert saved["remote_submission"] is False
    assert saved["media"]["project_relative_path"] == "export.mp4"
    assert saved["media"]["sha256"]
    target = saved["targets"][0]
    assert target["destination_id"] == "UC-synthetic-channel"
    assert target["visibility"] == "private"
    assert target["remote_status"] == "not_submitted"
    assert target["request_id"]
    assert media.read_bytes() == b"synthetic-fixture-not-a-video"


def test_same_revision_is_idempotent_but_changed_payload_cannot_overwrite(tmp_path):
    project, _ = setup_project(tmp_path)
    first = call(project)
    again = call(project, created_at="2026-11-28T16:00:00+00:00")
    assert first.success and again.success
    assert again.data["idempotent_reuse"] is True
    original = Path(first.data["plan_path"]).read_bytes()
    changed = dict(TARGET, title="changed")
    conflict = call(project, targets=[changed])
    assert not conflict.success and "Conflicto" in conflict.error
    assert Path(first.data["plan_path"]).read_bytes() == original


def test_target_requires_explicit_visibility_and_destination(tmp_path):
    project, _ = setup_project(tmp_path)
    assert not call(project, targets=[dict(TARGET, visibility=None)]).success
    assert not call(project, targets=[dict(TARGET, destination_id="")]).success
    assert not call(project, targets=[{k: v for k, v in TARGET.items() if k != "destination_id"}]).success


def test_rejects_credentials_unknown_fields_and_duplicate_destinations(tmp_path):
    project, _ = setup_project(tmp_path)
    assert not call(project, access_token="must-not-be-accepted").success
    assert not call(project, targets=[dict(TARGET, access_token="secret")]).success
    assert not call(project, targets=[dict(TARGET, unexpected="value")]).success
    assert not call(project, targets=[dict(TARGET), dict(TARGET)]).success


def test_rejects_paths_outside_project_and_bad_identifiers(tmp_path):
    project, _ = setup_project(tmp_path)
    assert not call(project, media_path="../outside.mp4").success
    assert not call(project, plan_id="../bad").success
    assert not call(project, revision=True).success


def test_rejects_past_schedule_unknown_zone_and_dst_offset_mismatch(tmp_path):
    project, _ = setup_project(tmp_path)
    past = dict(TARGET, scheduled_for="2026-11-27T10:00:00+00:00")
    unknown = dict(TARGET, timezone="Unknown/Zone")
    wrong_offset = dict(TARGET, scheduled_for="2026-12-01T10:00:00+01:00")
    assert not call(project, targets=[past]).success
    assert not call(project, targets=[unknown]).success
    assert not call(project, targets=[wrong_offset]).success


def test_schedule_is_optional_for_an_unscheduled_local_draft(tmp_path):
    project, _ = setup_project(tmp_path)
    target = dict(TARGET)
    target.pop("scheduled_for")
    result = call(project, targets=[target])
    assert result.success
    assert result.data["plan"]["targets"][0]["scheduled_for"] is None


def test_registry_discovers_local_plan_tool():
    registry = ToolRegistry()
    registry.discover()
    tool = registry.get("local_publish_plan")
    assert tool is not None
    assert tool.supports["uploads"] is False
    assert tool.supports["remote_scheduling"] is False


def test_rejects_nonexistent_dst_wall_time_when_iana_database_is_available(tmp_path):
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    try:
        ZoneInfo("America/New_York")
    except ZoneInfoNotFoundError:
        pytest.skip("La base IANA no está disponible en este runner; no se instaló tzdata.")
    project, _ = setup_project(tmp_path)
    target = dict(TARGET, timezone="America/New_York", scheduled_for="2027-03-14T02:30:00-05:00")
    result = call(project, targets=[target])
    assert not result.success
    assert "DST" in result.error
