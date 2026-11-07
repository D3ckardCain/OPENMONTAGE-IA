"""Transport/graph tests with an emulated localhost server, NOT model inference.

The returned artifact is an explicit byte fixture, not an AI-generated video.
No GPU, model weights, external endpoints or credit-consuming nodes are used.
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import Mock, patch

import pytest

from tools._comfyui.client import ComfyUIClient, ComfyUIError
from tools._comfyui.zero_cost import (
    LocalWorkflowPolicyError, local_server_url, validate_wan_workflow,
)
from tools.video.comfyui_video import _REQUIRED_MODELS_T2V, _REQUIRED_MODELS_I2V
from tools.video.comfyui_wan_local import ComfyUIWanLocal

_FIXTURE = b"HTTP contract fixture, not an AI-generated MP4"


@pytest.fixture
def server(monkeypatch):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, data):
            content = data if isinstance(data, bytes) else json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self):
            self.server.calls.append(("GET", self.path))
            if self.path == "/system_stats":
                self.reply({"devices": []})
            elif self.path.startswith("/object_info/"):
                node = self.path.rsplit("/", 1)[-1]
                if node in self.server.missing_nodes:
                    self.reply({})
                    return
                field = {
                    "CheckpointLoaderSimple": "ckpt_name", "UNETLoader": "unet_name",
                    "VAELoader": "vae_name", "CLIPLoader": "clip_name",
                    "LoraLoaderModelOnly": "lora_name",
                }.get(node)
                required = {field: [list(set(_REQUIRED_MODELS_T2V + _REQUIRED_MODELS_I2V))]} if field else {}
                self.reply({node: {"input": {"required": required}}})
            elif self.path.startswith("/history/"):
                output = "108" if "108" in self.server.graph else "16"
                self.reply({"test-job": {
                    "status": {"status_str": "success"},
                    "outputs": {output: {"video": [{"filename": "fixture.mp4"}]}},
                }})
            elif self.path.startswith("/view?"):
                self.reply(_FIXTURE)
            else:
                self.send_error(404)

        def do_POST(self):
            self.server.calls.append(("POST", self.path))
            content = self.rfile.read(int(self.headers["Content-Length"]))
            if self.path == "/prompt":
                self.server.graph = json.loads(content)["prompt"]
                self.reply({"prompt_id": "test-job"})
            elif self.path == "/upload/image":
                self.reply({"name": "uploaded-reference.png"})
            else:
                self.send_error(404)

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    http.calls = []
    http.missing_nodes = set()
    http.graph = {}
    thread = Thread(target=http.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("COMFYUI_VIDEO_SERVER_URL", f"http://127.0.0.1:{http.server_port}")
    monkeypatch.delenv("OPENMONTAGE_ASSET_CACHE", raising=False)
    try:
        yield http
    finally:
        http.shutdown()
        http.server_close()
        thread.join(timeout=2)


def test_text_to_video_contract_on_real_loopback_transport(server, tmp_path, monkeypatch):
    # A proxy must not redirect the local request to a billable hosted service.
    monkeypatch.setenv("HTTP_PROXY", "http://unreachable.invalid:1")
    monkeypatch.setenv("NO_PROXY", "")
    tool = ComfyUIWanLocal()
    target = tmp_path / "contract.mp4"
    result = tool.execute({
        "prompt": "A red ball rolling across a table", "seed": 0,
        "width": 512, "height": 320, "num_frames": 17, "output_path": str(target),
    })
    assert result.success, result.error
    assert target.read_bytes() == _FIXTURE
    assert result.cost_usd == 0
    assert result.seed == 0
    assert result.data["provider"] == "comfyui_wan_local"
    assert result.data["hosted"] is False
    assert server.graph["12"]["inputs"]["noise_seed"] == 0
    assert server.graph["11"]["inputs"]["batch_size"] == 1
    assert validate_wan_workflow(server.graph) == "wan22-t2v-4step.json"
    assert server.calls.count(("POST", "/prompt")) == 1
    assert tool._client._local_session.trust_env is False


def test_image_to_video_contract_uses_local_upload(server, tmp_path):
    reference = tmp_path / "reference.png"
    reference.write_bytes(b"image-upload-contract-fixture")
    tool = ComfyUIWanLocal()
    result = tool.execute({
        "prompt": "The camera moves around the product", "operation": "image_to_video",
        "reference_image_path": str(reference), "seed": 7,
        "output_path": str(tmp_path / "i2v.mp4"),
    })
    assert result.success, result.error
    assert server.calls.count(("POST", "/upload/image")) == 1
    assert server.graph["97"]["inputs"]["image"] == "uploaded-reference.png"
    assert validate_wan_workflow(server.graph, "108") == "wan22-i2v-4step.json"


@pytest.mark.parametrize("overrides", [
    {"model_family": "gemini_omni_flash"}, {"model_family": "seedance_2.5"},
    {"model_family": "minimax_h3_api"}, {"model_family": "unknown"},
    {"workflow_json": "{}"}, {"workflow_path": "custom.json"},
    {"resume_prompt_id": "paid-job"}, {"reference_image_url": "https://example.com/image"},
    {"width": 513}, {"num_frames": 16}, {"seed": -1}, {"output_path": "out.wav"},
])
def test_rejects_unreviewed_paths_before_any_connection(overrides):
    tool = ComfyUIWanLocal()
    with patch.object(tool._client, "is_available", side_effect=AssertionError("network reached")):
        result = tool.execute({"prompt": "test", **overrides})
    assert not result.success
    assert "ZERO_COST_POLICY" in result.error


@pytest.mark.parametrize("url", [
    "https://hosted.example", "http://192.168.1.1:8188", "http://127.0.0.1.example:8188",
    "http://user:password@127.0.0.1:8188", "http://127.0.0.1:8188/path",
    "http://127.0.0.1:8188?host=cloud", "file:///tmp/socket",
])
def test_remote_server_rejected_before_transport(url):
    client = ComfyUIClient(server_url=url, local_wan_only=True)
    with patch("requests.Session", side_effect=AssertionError("transport reached")):
        assert client.is_available() is False
    assert "ZERO_COST_POLICY" in client.unavailable_reason()


def test_loopback_normalization_has_no_dns_dependency():
    assert local_server_url("http://localhost:8188") == "http://127.0.0.1:8188"
    assert local_server_url("http://[::1]:8190") == "http://[::1]:8190"


def test_redirect_is_not_followed():
    client = ComfyUIClient(local_wan_only=True)
    response = Mock(status_code=302)
    with patch("requests.Session") as factory:
        factory.return_value.request.return_value = response
        with pytest.raises(ComfyUIError, match="redirects"):
            client._get(f"{client.server_url}/system_stats")
        assert factory.return_value.request.call_args.kwargs["allow_redirects"] is False
        assert factory.return_value.trust_env is False


@pytest.mark.parametrize("mutation", ["partner", "model", "link", "input", "metadata"])
def test_graph_mutation_rejected_before_queueing(mutation, tmp_path):
    tool = ComfyUIWanLocal()
    graph, _ = tool._build_t2v({"prompt": "test"}, 0, tmp_path / "out.mp4")
    if mutation == "partner":
        graph["1"]["class_type"] = "ByteDance2TextToVideoNode"
    elif mutation == "model":
        graph["5"]["inputs"]["unet_name"] = "unreviewed-model.safetensors"
    elif mutation == "link":
        graph["14"]["inputs"]["samples"] = ["5", 0]
    elif mutation == "input":
        graph["5"]["inputs"]["api_key"] = "not-allowed"
    else:
        graph["5"]["_meta"] = {"extra": True}
    with patch.object(tool._client, "_post", side_effect=AssertionError("queued")):
        with pytest.raises(LocalWorkflowPolicyError):
            tool._client.submit(graph)


def test_missing_models_are_reported_without_fallback(server, tmp_path):
    tool = ComfyUIWanLocal()
    with patch.object(tool._client, "check_models", return_value=([], ["missing.safetensors"])):
        result = tool.execute({"prompt": "test", "output_path": str(tmp_path / "out.mp4")})
    assert not result.success
    assert "missing models" in result.error
    assert not any(method == "POST" for method, _ in server.calls)
    assert tool.fallback_tools == []


def test_generic_comfyui_adapter_remains_blocked():
    from tools.video.comfyui_video import ComfyUIVideo
    result = ComfyUIVideo().execute({"prompt": "test"})
    assert not result.success
    assert result.data["blocked_by"] == "zero_cost_policy"


@pytest.mark.parametrize('operation', [None, 'text_to_video'])
def test_reference_never_silently_ignored_in_text_mode(operation, tmp_path):
    tool = ComfyUIWanLocal()
    image = tmp_path / 'reference.png'
    image.write_bytes(b'local reference fixture')
    inputs = {'prompt': 'Move this product', 'reference_image_path': str(image)}
    if operation is not None:
        inputs['operation'] = operation
    with patch.object(tool._client, 'is_available', side_effect=AssertionError('transport reached')):
        result = tool.execute(inputs)
    assert not result.success
    assert 'operation=image_to_video' in result.error


@pytest.mark.parametrize('prompt', [' ', '\n\t'])
def test_blank_prompt_rejected_before_transport(prompt):
    tool = ComfyUIWanLocal()
    with patch.object(tool._client, 'is_available', side_effect=AssertionError('transport reached')):
        result = tool.execute({'prompt': prompt})
    assert not result.success
    assert 'non-whitespace' in result.error


def test_queued_job_failure_does_not_recommend_unsupported_resume(server, tmp_path):
    tool = ComfyUIWanLocal()
    with patch.object(tool._client, 'generate', side_effect=ComfyUIError('Timed out', prompt_id='queued-wan-job')) as generate:
        result = tool.execute({'prompt': 'A ball rolling', 'output_path': str(tmp_path / 'out.mp4')})
    assert not result.success
    assert generate.call_count == 1
    assert result.data['prompt_id'] == 'queued-wan-job'
    assert result.data['resume_supported'] is False
    assert result.data['resubmit_requires_job_check'] is True
    assert 'resume_prompt_id=' not in result.error
    assert 'queue/history' in result.error
    assert not (tmp_path / 'out.mp4').exists()


def test_dry_run_offline_is_not_ready():
    tool = ComfyUIWanLocal()
    with patch.object(tool._client, "is_available", return_value=False):
        result = tool.dry_run({"prompt": "A moving ball"})
    assert result["would_execute"] is False
    assert result["status"] == "unavailable"
    assert result["estimated_runtime_seconds"] is None


@pytest.mark.parametrize("inputs", [
    {"prompt": "   "},
    {"prompt": "A ball", "num_frames": 18},
    {"prompt": "A ball", "reference_image_path": "ignored.png"},
])
def test_invalid_dry_run_does_not_contact_server(inputs):
    tool = ComfyUIWanLocal()
    with patch.object(tool._client, "is_available") as available:
        result = tool.dry_run(inputs)
    assert result["would_execute"] is False
    assert result["input_error"]
    available.assert_not_called()


def test_missing_node_blocks_submission_and_dry_run(server):
    server.missing_nodes.add("EmptyHunyuanLatentVideo")
    tool = ComfyUIWanLocal()
    inputs = {"prompt": "A moving ball"}
    preview = tool.dry_run(inputs)
    assert preview["status"] == "degraded"
    assert preview["would_execute"] is False
    result = tool.execute(inputs)
    assert not result.success
    assert result.data["missing_nodes"] == ["EmptyHunyuanLatentVideo"]
    assert not any(method == "POST" for method, _ in server.calls)


def test_node_readiness_is_operation_specific(server):
    server.missing_nodes.add("WanImageToVideo")
    statuses = ComfyUIWanLocal().operation_statuses()
    assert statuses == {"text_to_video": "available", "image_to_video": "degraded"}


def test_dry_run_missing_models_is_not_ready(server):
    tool = ComfyUIWanLocal()
    with patch.object(tool._client, "check_models", return_value=([], ["missing.safetensors"])):
        result = tool.dry_run({"prompt": "A moving ball"})
    assert result["would_execute"] is False
    assert result["status"] == "degraded"


def test_ready_dry_run_does_not_submit_or_write(server, tmp_path):
    target = tmp_path / "preview.mp4"
    result = ComfyUIWanLocal().dry_run({"prompt": "A moving ball", "output_path": str(target)})
    assert result["would_execute"] is True
    assert result["estimated_runtime_seconds"] is None
    assert result["runtime_status"] == "unmeasured_on_target_gpu"
    assert not target.exists()
    assert not any(method == "POST" for method, _ in server.calls)
