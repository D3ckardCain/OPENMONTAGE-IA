from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backlot.server import create_app
from lib import production_studio as studio, studio_editor as editor
from lib import studio_text_to_video as jobs
from lib.wan_presets import config as wan_config


class FakeClient:
    available = True
    missing = []

    def is_available(self):
        return self.available

    def unavailable_reason(self):
        return "ComfyUI simulado fuera de línea"

    def check_models(self, names):
        self.checked = tuple(names)
        return [], list(self.missing)


class FakeComfyUIVideo:
    mode = "complete"
    calls = 0
    last_inputs = None

    def __init__(self):
        self._client = FakeClient()

    def execute(self, inputs):
        type(self).calls += 1
        type(self).last_inputs = inputs
        if self.mode == "complete":
            output = __import__("pathlib").Path(inputs["output_path"])
            output.write_bytes(b"simulated mp4 bytes")
            return SimpleNamespace(success=True, data={"output": str(output), "model": "fake-wan"}, error=None)
        if self.mode == "uncertain":
            return SimpleNamespace(success=False, data={"prompt_id": "comfy-prompt-123"}, error="poll timeout")
        return SimpleNamespace(success=False, data={}, error="node validation error")


@pytest.fixture
def text_video(monkeypatch, tmp_path):
    monkeypatch.setattr(studio, "PROJECTS_DIR", tmp_path / "projects")
    monkeypatch.setattr(jobs, "ACTIVE", {})
    FakeComfyUIVideo.calls = 0
    FakeComfyUIVideo.last_inputs = None
    FakeComfyUIVideo.mode = "complete"
    fake = FakeClient()
    monkeypatch.setattr(FakeComfyUIVideo, "__init__", lambda self: setattr(self, "_client", fake))
    monkeypatch.setattr("tools.video.comfyui_video.ComfyUIVideo", FakeComfyUIVideo)
    expected = wan_config(jobs.PROFILE)
    monkeypatch.setattr("lib.model_adapters.configuration", lambda family: {**expected, "preset": jobs.PROFILE})
    pid = editor.create("T2V de prueba")['project_id']
    return TestClient(create_app()), pid, fake


def post(client, pid, request_id="a" * 32, prompt="Nubes moviéndose lentamente"):
    return client.post(f"/api/studio/editor/{pid}/text-to-video", json={"prompt": prompt, "request_id": request_id})


def wait_for(client, pid, request_id, expected):
    for _ in range(100):
        response = client.get(f"/api/studio/editor/{pid}/text-to-video/requests/{request_id}")
        if response.status_code == 200 and response.json()["state"] == expected:
            return response.json()
        time.sleep(0.01)
    pytest.fail(f"El trabajo no llegó a {expected}: {response.text}")


def test_local_flow_saves_mp4_in_active_project(text_video):
    client, pid, fake = text_video
    response = post(client, pid)
    assert response.status_code == 202
    assert tuple(fake.checked)
    completed = wait_for(client, pid, "a" * 32, "completed")
    assert completed["profile"] == jobs.PROFILE
    assert "relative_path" not in completed
    assert FakeComfyUIVideo.last_inputs["operation"] == "text_to_video"
    assert FakeComfyUIVideo.last_inputs["model_family"] == "wan2.2"
    assert FakeComfyUIVideo.last_inputs["wan_workflow_path"] == wan_config(jobs.PROFILE)["workflow_path"]
    assert completed["bytes"] == len(b"simulated mp4 bytes")
    assert completed["video_url"].endswith("/video")
    output = studio.project_path(pid) / "medios_generados" / f"wan-t2v-{'a' * 32}.mp4"
    assert output.read_bytes() == b"simulated mp4 bytes"
    downloaded = client.get(completed["video_url"])
    assert downloaded.status_code == 200
    assert downloaded.content == b"simulated mp4 bytes"
    assert downloaded.headers["content-type"].startswith("video/mp4")


def test_completed_receipt_is_listed_after_reopening_project(text_video):
    client, pid, _ = text_video
    assert post(client, pid).status_code == 202
    completed = wait_for(client, pid, "a" * 32, "completed")

    # Re-open the editable project as Studio does on project selection/reload.
    reopened = client.get(f"/api/studio/editor/{pid}")
    assert reopened.status_code == 200
    assert reopened.json()["revision"] == 0

    results = client.get(f"/api/studio/editor/{pid}/text-to-video/results")
    assert results.status_code == 200
    assert len(results.json()) == 1
    media = results.json()[0]
    assert media["request_id"] == "a" * 32
    assert media["video_url"] == completed["video_url"]
    assert media["bytes"] == len(b"simulated mp4 bytes")
    assert "relative_path" not in media
    assert str(studio.project_path(pid)) not in media.values()


def test_read_only_availability_requires_wan_preflight_without_submission(text_video):
    client, pid, fake = text_video
    ready = client.get(f"/api/studio/editor/{pid}/text-to-video/availability")
    assert ready.status_code == 200
    assert ready.json() == {
        "available": True,
        "profile": jobs.PROFILE,
        "workflow": "wan22-t2v-4step.json",
        "required_models": 6,
    }
    assert tuple(fake.checked)
    assert FakeComfyUIVideo.calls == 0

    fake.available = False
    unavailable = client.get(f"/api/studio/editor/{pid}/text-to-video/availability")
    assert unavailable.status_code == 200
    assert unavailable.json()["available"] is False
    assert "fuera de línea" in unavailable.json()["reason"]
    assert FakeComfyUIVideo.calls == 0


def test_read_only_availability_reports_missing_wan_weights(text_video):
    client, pid, fake = text_video
    fake.missing = ["wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors"]
    response = client.get(f"/api/studio/editor/{pid}/text-to-video/availability")
    assert response.status_code == 200
    assert response.json()["available"] is False
    assert fake.missing[0] in response.json()["reason"]
    assert FakeComfyUIVideo.calls == 0


def test_completed_result_adds_to_timeline_without_browser_path(text_video, monkeypatch):
    client, pid, _ = text_video
    assert post(client, pid).status_code == 202
    wait_for(client, pid, "a" * 32, "completed")
    monkeypatch.setattr(editor, "probe", lambda path: {
        "duration": 1.0, "kind": "video", "audio": False, "width": 16, "height": 9,
    })
    monkeypatch.setattr(editor, "digest", lambda path: "a" * 64)

    rejected = client.post(
        f"/api/studio/editor/{pid}/text-to-video/requests/{'a' * 32}/add",
        json={"revision": 0, "relative_path": "medios_generados/otro.mp4"},
    )
    assert rejected.status_code == 400

    added = client.post(
        f"/api/studio/editor/{pid}/text-to-video/requests/{'a' * 32}/add",
        json={"revision": 0},
    )
    assert added.status_code == 200
    result = added.json()
    assert result["edit"]["edit_decisions"]["cuts"][0]["source"] == (
        f"medios_generados/wan-t2v-{'a' * 32}.mp4"
    )
    assert result["edit"]["events"][-1]["operation"] == "add_generated_video"
    assert result["edit"]["undo"]
    assert editor.source(pid, result["source_id"]).name == f"wan-t2v-{'a' * 32}.mp4"
    reopened = client.get(f"/api/studio/editor/{pid}")
    assert reopened.status_code == 200
    media = client.get(f"/api/studio/editor/{pid}/source/{result['source_id']}")
    assert media.status_code == 200
    assert media.content == b"simulated mp4 bytes"
    assert client.get(f"/api/studio/editor/{pid}/text-to-video/results").json() == []


@pytest.mark.parametrize("prompt", ["", "  ", "x" * (jobs.MAX_PROMPT_CHARS + 1)])
def test_prompt_is_validated_before_comfyui(text_video, prompt):
    client, pid, _ = text_video
    response = post(client, pid, prompt=prompt)
    assert response.status_code == 400
    assert FakeComfyUIVideo.calls == 0


def test_service_unavailable_is_reported_without_job(text_video):
    client, pid, fake = text_video
    fake.available = False
    response = post(client, pid)
    assert response.status_code == 503
    assert "fuera de línea" in response.json()["detail"]
    assert FakeComfyUIVideo.calls == 0
    assert not (studio.project_path(pid) / "artifacts" / "text_to_video" / ("a" * 32 + ".json")).exists()


def test_missing_wan_models_are_reported_without_submission(text_video):
    client, pid, fake = text_video
    fake.missing = ["wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors"]
    response = post(client, pid)
    assert response.status_code == 503
    assert fake.missing[0] in response.json()["detail"]
    assert FakeComfyUIVideo.calls == 0


def test_nonmatching_profile_workflow_is_not_sent(text_video, monkeypatch):
    client, pid, _ = text_video
    monkeypatch.setattr("lib.model_adapters.configuration", lambda family: {
        **wan_config(jobs.PROFILE), "preset": jobs.PROFILE,
        "workflow_path": str(studio.REPO_ROOT / "another-workflow.json"),
    })
    response = post(client, pid)
    assert response.status_code == 503
    assert "no coincide" in response.json()["detail"]
    assert FakeComfyUIVideo.calls == 0


def test_uncertain_comfyui_result_is_recoverable_without_resubmit(text_video):
    client, pid, _ = text_video
    FakeComfyUIVideo.mode = "uncertain"
    first = post(client, pid)
    assert first.status_code == 202
    uncertain = wait_for(client, pid, "a" * 32, "uncertain")
    assert uncertain["prompt_id"] == "comfy-prompt-123"
    retry = post(client, pid)
    assert retry.status_code == 202
    assert retry.json()["reused_request"] is True
    assert retry.json()["state"] == "uncertain"
    assert FakeComfyUIVideo.calls == 1


def test_tool_failure_and_unknown_request_have_clear_states(text_video):
    client, pid, _ = text_video
    FakeComfyUIVideo.mode = "failed"
    response = post(client, pid)
    assert response.status_code == 202
    failed = wait_for(client, pid, "a" * 32, "failed")
    assert "validation error" in failed["error"]
    missing = client.get(f"/api/studio/editor/{pid}/text-to-video/requests/{'b' * 32}")
    assert missing.status_code == 404
