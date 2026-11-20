"""Local-only replacement for ComfyUI video Partner Nodes.

Reuses the existing bundled Wan builders, with a restricted input contract and
a transport that validates the complete graph before queueing it.
"""
from __future__ import annotations

from pathlib import Path
import math
import json
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
        "text_to_video": True, "image_to_video": True,
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

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        # This adapter cannot select any paid family. Creative controls are
        # validated during adaptation/execution, not parsed by a cloud estimator.
        return 0.0

    @staticmethod
    def adapt_selector_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
        """Translate shared duration/ratio controls into the reviewed Wan graph.

        Wan uses 16 FPS with 4n+1 frames. Composition can trim that native clip
        to the requested final duration; the provider reports the actual frames.
        """
        adapted = dict(inputs)
        duration = adapted.pop("duration", None)
        if duration is not None:
            if isinstance(duration, bool):
                raise ValueError("Wan duration must be a finite number of seconds.")
            try:
                seconds = float(str(duration).strip().lower().removesuffix("s"))
            except (ValueError, TypeError):
                raise ValueError("Wan duration must be a finite number of seconds.") from None
            if not math.isfinite(seconds) or not 0.25 <= seconds <= 256:
                raise ValueError("Wan duration must be between 0.25 and 256 seconds.")
            frames = 4 * round(seconds * 16 / 4) + 1
            if "num_frames" in adapted and adapted["num_frames"] != frames:
                raise ValueError("duration conflicts with num_frames for Wan at 16 FPS.")
            adapted["num_frames"] = frames

        ratio = adapted.pop("aspect_ratio", None)
        if ratio is not None:
            ratios = {"16:9": (832, 480), "9:16": (480, 832), "1:1": (640, 640)}
            if ratio not in ratios:
                raise ValueError("Wan aspect_ratio must be 16:9, 9:16 or 1:1.")
            width = adapted.get("width")
            height = adapted.get("height")
            for value in (width, height):
                if value is not None and (type(value) is not int or value <= 0 or value % 16):
                    raise ValueError("Wan dimensions must be positive integer multiples of 16.")
            numerator, denominator = map(int, ratio.split(":"))
            factor = numerator / denominator
            if width is None and height is None:
                width, height = ratios[ratio]
            elif height is None:
                height = max(16, 16 * round(width / factor / 16))
            elif width is None:
                width = max(16, 16 * round(height * factor / 16))
            if not math.isclose(width / height, factor, rel_tol=0.03):
                raise ValueError("aspect_ratio conflicts with width/height for Wan.")
            adapted.update(width=width, height=height)
        return adapted

    def _missing_nodes(self, operation: str) -> list[str]:
        variant = "i2v" if operation == "image_to_video" else "t2v"
        path = Path(__file__).parents[1] / "_comfyui" / "workflows" / f"wan22-{variant}-4step.json"
        graph = json.loads(path.read_text(encoding="utf-8"))
        return [name for name in sorted({node["class_type"] for node in graph.values()})
                if not self._client.has_node(name)]

    def operation_statuses(self) -> dict[str, str]:
        statuses = super().operation_statuses()
        for operation, status in statuses.items():
            if status == "available" and self._missing_nodes(operation):
                statuses[operation] = "degraded"
        return statuses

    def dry_run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        # Reuse the same contract as execute; no queueing, uploads or output files.
        from jsonschema import ValidationError
        try:
            self._validate_inputs(inputs)
        except (ValidationError, ValueError, TypeError) as exc:
            message = exc.message if isinstance(exc, ValidationError) else str(exc)
            return {"tool": self.name, "estimated_cost_usd": 0,
                    "would_execute": False, "status": "unavailable",
                    "input_error": message}
        operation = inputs.get("operation", "text_to_video")
        status = self.operation_statuses()[operation]
        return {"tool": self.name, "operation": operation,
                "estimated_cost_usd": 0, "estimated_runtime_seconds": None,
                "runtime_status": "unmeasured_on_target_gpu",
                "status": status, "would_execute": status == "available"}

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

    def _validate_inputs(self, inputs: dict[str, Any]) -> None:
        from jsonschema import validate

        validate(inputs, self.input_schema)
        if not inputs["prompt"].strip():
            raise ValueError("Wan prompt must contain non-whitespace text.")
        operation = inputs.get("operation", "text_to_video")
        if "reference_image_path" in inputs and operation != "image_to_video":
            raise ValueError(
                "A reference image requires operation=image_to_video; "
                "text_to_video cannot silently ignore it."
            )
        if inputs.get("num_frames", 81) % 4 != 1:
            raise ValueError("Wan frame count must be 4n+1.")
        if inputs.get("operation", "text_to_video") == "image_to_video":
            reference = inputs.get("reference_image_path")
            if not reference or not Path(reference).is_file():
                raise ValueError("image_to_video requires an existing local image file.")
        output = Path(inputs.get("output_path", "wan_local.mp4"))
        if output.suffix.lower() != ".mp4":
            raise ValueError("Wan local output must use the .mp4 extension.")

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        from jsonschema import ValidationError

        try:
            self._validate_inputs(inputs)
        except (ValidationError, ValueError, TypeError) as exc:
            message = exc.message if isinstance(exc, ValidationError) else str(exc)
            return ToolResult(
                success=False, error=f"ZERO_COST_POLICY: {message}",
                data={"blocked_by": "zero_cost_policy", "tool": self.name},
            )
        if self._client.is_available():
            missing_nodes = self._missing_nodes(inputs.get("operation", "text_to_video"))
            if missing_nodes:
                return ToolResult(
                    success=False, error="ComfyUI is missing required Wan nodes: " + ", ".join(missing_nodes),
                    data={"missing_nodes": missing_nodes, "setup_required": True},
                )
        result = super().execute(inputs)
        if result.success:
            result.data["provider"] = self.provider
        elif result.data.get("missing_models"):
            result.data["provider"] = self.provider
            result.data["setup_offer"] = dict(self.setup_offer)
        elif result.data.get("prompt_id"):
            # The generic adapter recommends resume_prompt_id, but this
            # reviewed local-only adapter deliberately rejects unverified jobs.
            # Preserve the ID for inspection without telling users to resubmit.
            message = (result.error or "ComfyUI job failed").partition(
                "\n\nThis job was NOT cancelled"
            )[0]
            result.error = (
                message + "\n\nInspect this job in the local ComfyUI queue/history "
                "before submitting again; it may still be running. This adapter "
                "does not support resuming jobs."
            )
            result.data.update(
                job_state="unknown_check_local_queue",
                resume_supported=False,
                resubmit_requires_job_check=True,
            )
        return result
