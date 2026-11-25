"""Piper local text-to-speech provider tool."""

from __future__ import annotations

import time
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)


class PiperTTS(BaseTool):
    name = "piper_tts"
    version = "0.2.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "piper"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = []
    install_instructions = "Configure an isolated Piper >=1.5 runtime and verified local bundles; see docs/piper-studio.md. No automatic downloads."
    agent_skills = []

    capabilities = [
        "text_to_speech",
        "offline_generation",
    ]
    supports = {
        "voice_cloning": False,
        "multilingual": False,
        "offline": True,
        "native_audio": True,
    }
    best_for = [
        "offline narration fallback",
        "privacy-sensitive local-only workflows",
    ]
    not_good_for = [
        "best-in-class expressive voice quality",
        "voice clone matching",
    ]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string"},
            "model": {
                "type": "string",
                "default": "es_ES-davefx-medium",
            },
            "speaker_id": {
                "type": "integer",
                "default": 0,
            },
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=2, ram_mb=512, vram_mb=0, disk_mb=200, network_required=False
    )
    retry_policy = RetryPolicy(max_retries=1, retryable_errors=[])
    idempotency_key_fields = ["text", "model", "speaker_id", "output_path"]
    side_effects = ["writes audio file to output_path"]
    user_visible_verification = ["Listen to generated audio for intelligibility"]

    def get_status(self) -> ToolStatus:
        from lib.studio_piper import catalog
        return ToolStatus.AVAILABLE if any(v['available'] and not v['blocked'] for v in catalog()) else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        if self.get_status() != ToolStatus.AVAILABLE:
            return ToolResult(success=False, error="Piper TTS not available. " + self.install_instructions)

        start = time.time()
        try:
            result = self._generate(inputs)
        except Exception as exc:
            return ToolResult(success=False, error=f"Local TTS generation failed: {exc}")

        result.duration_seconds = round(time.time() - start, 2)
        return result

    def _generate(self, inputs: dict[str, Any]) -> ToolResult:
        from lib.studio_piper import synthesize
        result = synthesize(inputs['text'], inputs.get('model', 'es_ES-davefx-medium'),
                            inputs.get('speaker_id', 0), inputs.get('output_path', 'tts_output.wav'))
        return ToolResult(success=True, data=result, artifacts=[result['output']],
                          model=inputs.get('model', 'es_ES-davefx-medium'))
