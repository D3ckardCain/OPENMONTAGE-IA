"""Exercise actual selector boundaries; generated outputs are test fixtures only."""
import jsonschema
import pytest

from tools.base_tool import BaseTool, ToolResult, ToolRuntime, ToolStatus
from tools.audio.tts_selector import TTSSelector
from tools.graphics.image_selector import ImageSelector
from tools.video.video_selector import VideoSelector
from tools.video.comfyui_wan_local import ComfyUIWanLocal
from tools.tool_registry import ToolRegistry
from tests.tools.test_comfyui_wan_local import server  # noqa: F401 -- shared HTTP fixture


class LocalFixture(BaseTool):
    provider = "local_fixture"
    runtime = ToolRuntime.LOCAL
    quality_score = 0.5
    supports = {"text_to_video": True, "image_to_video": True, "offline": True}

    def __init__(self, capability):
        self.capability = capability
        self.name = f"local_{capability}"
        field = "text" if capability == "tts" else "prompt"
        self.input_schema = {
            "type": "object", "required": [field], "additionalProperties": False,
            "properties": {field: {"type": "string"}, "output_path": {"type": "string"}},
        }
        self.calls = 0
        self.succeed = True
        self.ready = True

    def get_status(self):
        return ToolStatus.AVAILABLE if self.ready else ToolStatus.UNAVAILABLE

    def execute(self, inputs):
        jsonschema.validate(inputs, self.input_schema)
        self.calls += 1
        return ToolResult(success=self.succeed, error=None if self.succeed else "local failure")


class CloudFixture(LocalFixture):
    provider = "paid_fixture"
    runtime = ToolRuntime.API
    quality_score = 1.0

    def __init__(self, capability):
        super().__init__(capability)
        self.name = f"paid_{capability}"

    def get_status(self):
        pytest.fail("Disabled provider readiness must not be probed by a selector")

    def estimate_cost(self, inputs):
        pytest.fail("Disabled provider pricing must not be probed by a selector")

    def is_operation_available(self, operation):
        pytest.fail("Disabled provider operation readiness must not be probed")

    def execute(self, inputs):
        pytest.fail("Disabled provider implementation must not be executed")


SELECTORS = [
    (TTSSelector, "tts", {"text": "prueba"}),
    (ImageSelector, "image_generation", {"prompt": "test"}),
    (VideoSelector, "video_generation", {"prompt": "test"}),
]


def install_catalog(monkeypatch, *providers):
    catalog = ToolRegistry()
    catalog._discovered_packages.add("tools")
    for provider in providers:
        catalog.register(provider)
    monkeypatch.setattr("tools.tool_registry.registry", catalog)
    return catalog


@pytest.fixture(params=SELECTORS, ids=lambda item: item[0].__name__)
def route(request, monkeypatch):
    selector_cls, capability, inputs = request.param
    local = LocalFixture(capability)
    cloud = CloudFixture(capability)
    install_catalog(monkeypatch, cloud, local)
    return selector_cls(), local, cloud, inputs


def test_disabled_providers_absent_from_discovery_metadata_and_fallbacks(route):
    selector, local, cloud, _ = route
    assert [tool.name for tool in selector._providers()] == [local.name]
    assert cloud.name not in selector.fallback_tools
    assert cloud.provider not in selector.provider_matrix


def test_selects_local_and_strips_routing_controls_for_strict_provider(route):
    selector, local, cloud, inputs = route
    result = selector.execute({
        **inputs, "preferred_tool": local.name, "preferred_provider": local.provider,
        "allowed_providers": [local.provider], "preferred_provider_gap": 0.15,
        "task_context": {"intent": "test"},
    })
    assert result.success, result.error
    assert result.data["selected_tool"] == local.name
    assert local.calls == 1
    assert cloud.calls == 0


def test_failed_local_does_not_retry_paid_or_switch_provider(route):
    selector, local, cloud, inputs = route
    local.succeed = False
    result = selector.execute(inputs)
    assert not result.success
    assert result.error == "local failure"
    assert local.calls == 1
    assert cloud.calls == 0


def test_unavailable_local_never_unlocks_paid_provider(route):
    selector, local, cloud, inputs = route
    local.ready = False
    result = selector.execute(inputs)
    assert not result.success
    assert local.calls == cloud.calls == 0


def test_explicit_paid_tool_does_not_silently_fall_back_to_local(route):
    selector, local, cloud, inputs = route
    result = selector.execute({**inputs, "preferred_tool": cloud.name})
    assert not result.success
    assert local.calls == cloud.calls == 0


def test_url_only_provider_does_not_trigger_cloud_upload(monkeypatch, tmp_path):
    local = LocalFixture("video_generation")
    local.input_schema["properties"]["image_url"] = {"type": "string"}
    install_catalog(monkeypatch, local)
    def forbidden(*args, **kwargs):
        pytest.fail("A local reference was uploaded to a commercial service")
    monkeypatch.setattr("tools.video._shared.upload_image_fal", forbidden)
    reference = tmp_path / "private.png"
    reference.write_bytes(b"test fixture")
    result = VideoSelector().execute({
        "prompt": "test", "operation": "image_to_video",
        "reference_image_path": str(reference),
    })
    assert not result.success
    assert result.data["blocked_by"] == "zero_cost_policy"
    assert local.calls == 0


def test_rank_mode_lists_only_eligible_local_tools(route):
    selector, local, cloud, inputs = route
    result = selector.execute({**inputs, "operation": "rank"})
    assert result.success, result.error
    assert [entry["tool_name"] for entry in result.data["rankings"]] == [local.name]
    assert local.calls == cloud.calls == 0


@pytest.mark.parametrize("operation,eligible", [
    ("text_to_video", True), ("image_to_video", True), ("reference_to_video", False),
])
def test_video_alternatives_never_advertise_paid_or_still_downgrades(monkeypatch, operation, eligible):
    local = LocalFixture("video_generation")
    cloud = CloudFixture("video_generation")
    install_catalog(monkeypatch, cloud, local)
    expected = [local.name] if eligible else []
    assert VideoSelector().fallback_tools_for({"operation": operation}) == expected


@pytest.mark.parametrize("operation", ["image_to_video", "reference_to_video"])
def test_unsupported_motion_operation_never_reaches_text_only_tool(monkeypatch, operation):
    local = LocalFixture("video_generation")
    local.supports = {"text_to_video": True}
    install_catalog(monkeypatch, local)
    result = VideoSelector().execute({"prompt": "test", "operation": operation})
    assert not result.success
    assert local.calls == 0


@pytest.mark.parametrize("with_local", [True, False])
def test_registry_video_fallback_skips_paid_and_image_only_tools(monkeypatch, with_local):
    source = LocalFixture("video_generation")
    source.name = "source_video"
    image = LocalFixture("image_generation")
    cloud = CloudFixture("video_generation")
    local = LocalFixture("video_generation")
    source.fallback_tools = [image.name, cloud.name, local.name]
    providers = [source, image, cloud] + ([local] if with_local else [])
    catalog = install_catalog(monkeypatch, *providers)
    assert catalog.find_fallback(source.name) is (local if with_local else None)


@pytest.mark.parametrize("operation,ratio,size", [
    ("text_to_video", "16:9", (832, 480)),
    ("image_to_video", "1:1", (640, 640)),
])
def test_selector_to_real_wan_adapter_over_emulated_http(server, monkeypatch, tmp_path, operation, ratio, size):
    # This server returns an explicit byte fixture, not model-generated video.
    wan = ComfyUIWanLocal()
    cloud = CloudFixture("video_generation")
    install_catalog(monkeypatch, cloud, wan)
    output = tmp_path / "http-contract.mp4"
    inputs = {
        "prompt": "test motion", "preferred_tool": wan.name,
        "operation": operation, "duration": "5s", "aspect_ratio": ratio,
        "seed": 0, "output_path": str(output),
    }
    if operation == "image_to_video":
        reference = tmp_path / "reference.png"
        reference.write_bytes(b"upload fixture, not a generated image")
        inputs["reference_image_path"] = str(reference)
    result = VideoSelector().execute(inputs)
    assert result.success, result.error
    assert result.data["selected_tool"] == wan.name
    assert result.data["num_frames"] == 81
    assert (result.data["width"], result.data["height"]) == size
    assert result.seed == 0
    assert result.cost_usd == 0
    assert server.calls.count(("POST", "/prompt")) == 1
    assert cloud.calls == 0


@pytest.mark.parametrize("extra", [
    {"duration": "NaN"}, {"duration": -1}, {"duration": True},
    {"duration": "5", "num_frames": 17},
    {"aspect_ratio": "1:1", "width": 832, "height": 480},
])
def test_invalid_shared_wan_controls_stop_before_connection(monkeypatch, extra):
    wan = ComfyUIWanLocal()
    install_catalog(monkeypatch, wan)
    monkeypatch.setattr(wan, "get_status", lambda: ToolStatus.AVAILABLE)
    monkeypatch.setattr(wan, "is_operation_available", lambda operation: True)
    # Selection metadata should not probe the actual server in this test.
    monkeypatch.setattr(wan, "get_info", lambda: BaseTool.get_info(wan))
    def forbidden(*args, **kwargs):
        pytest.fail("Invalid controls reached the ComfyUI transport")
    monkeypatch.setattr(wan._client, "is_available", forbidden)
    result = VideoSelector().execute({
        "prompt": "test", "preferred_tool": wan.name, **extra,
    })
    assert not result.success
