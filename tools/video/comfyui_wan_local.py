"""Local-only replacement for ComfyUI video Partner Nodes.

Reuses the existing bundled Wan builders, with a restricted input contract and
a transport that validates the complete graph before queueing it.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.base_tool import BaseTool, ResourceProfile, ToolResult, ToolRuntime
from tools._comfyui.client import ComfyUIClient
from tools._comfyui.metadata import BUNDLED_MODEL_STACKS
from tools.video.comfyui_video import ComfyUIVideo


class ComfyUIWanLocal(ComfyUIVideo):
    name = "comfyui_wan_local"
    version = "0.1.0"
    provider = "comfyui_wan_local"
    runtime = ToolRuntime.LOCAL_GPU
    agent_skills = ["comfyui", "ai-video-gen"]
    fallback = None
    fallback_tools = []
    # This adapter remains uncached until output/provenance behavior is verified
    # with real model runs. A cached result must not bypass graph validation.
    idempotency_key_fields = []
    resource_profile = ResourceProfile(
        cpu_cores=4, ram_mb=32000, vram_mb=16000, disk_mb=80000,
        network_required=False,
    )
    install_instructions = (
        "Run ComfyUI on localhost with the bundled Wan 2.2 14B FP8 models and "
        "LightX2V LoRAs. No account, credits, paid API or cloud endpoint is used. "
        "See docs/COMFYUI_WAN_LOCAL.md."
    )
    setup_offer = {
        "kind": "local_server",
        "fix_complexity": "local install and model downloads",
        "what_it_unlocks": ["local Wan text-to-video", "local Wan image-to-video"],
    }
    supports = {
        "seed": True, "reference_image": True, "offline": True,
        "custom_workflow": False, "native_audio": False,
    }
    best_for = ["local Wan generation without ComfyUI credits"]
    not_good_for = ["hosted Partner Nodes", "custom workflows", "CPU-only machines"]
    input_schema = {
        "type": "object", "required": ["prompt"], "additionalProperties": False,
        "properties": {
            "prompt": {"type": "string", "minLength": 1},
            "operation": {"type": "string", "enum": ["text_to_video", "image_to_video"]},
            "model_family": {"type": "string", "enum": ["wan2.2"]},
            "width": {"type": "integer", "minimum": 16, "maximum": 8192, "multipleOf": 16},
            "height": {"type": "integer", "minimum": 16, "maximum": 8192, "multipleOf": 16},
            "num_frames": {"type": "integer", "minimum": 1, "maximum": 4097},
            "seed": {"type": "integer", "minimum": 0, "maximum": 2**64 - 1},
            "reference_image_path": {"type": "string"},
            "output_path": {"type": "string"},
            "timeout_seconds": {"type": "integer", "minimum": 1},
            "project_dir": {"type": "string"},
            "scene_id": {"type": "string"},
        },
    }

    def __init__(self) -> None:
        self._client = ComfyUIClient(capability="video", local_wan_only=True)
        self._last_progress_log = 0.0

    def get_info(self) -> dict[str, Any]:
        info = BaseTool.get_info(self)
        info["operation_statuses"] = self.operation_statuses()
        info["setup_offer"] = self.setup_offer
        info["bundled_model_stacks"] = {
            operation: BUNDLED_MODEL_STACKS[key]
            for operation, key in (
                ("text_to_video", "wan22-t2v-4step"),
                ("image_to_video", "wan22-i2v-4step"),
            )
        }
        info["resource_profile_note"] = (
            "Use the bundled Wan 14B FP8 stack, not the generic 8GB provider floor. "
            "Actual quality, VRAM and speed require real GPU measurement."
        )
        info["execution_modes"] = {"wan2.2": {"hosted": False, "api_cost_usd": 0}}
        return info

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        from jsonschema import ValidationError, validate

        try:
            validate(inputs, self.input_schema)
            if inputs.get("num_frames", 81) % 4 != 1:
                raise ValueError("Wan frame count must be 4n+1.")
            if inputs.get("operation", "text_to_video") == "image_to_video":
                reference = inputs.get("reference_image_path")
                if not reference or not Path(reference).is_file():
                    raise ValueError("image_to_video requires an existing local image file.")
            output = Path(inputs.get("output_path", "wan_local.mp4"))
            if output.suffix.lower() != ".mp4":
                raise ValueError("Wan local output must use the .mp4 extension.")
        except (ValidationError, ValueError, TypeError) as exc:
            message = exc.message if isinstance(exc, ValidationError) else str(exc)
            return ToolResult(
                success=False, error=f"ZERO_COST_POLICY: {message}",
                data={"blocked_by": "zero_cost_policy", "tool": self.name},
            )
        result = super().execute(inputs)
        if result.success:
            result.data["provider"] = self.provider
        return result
