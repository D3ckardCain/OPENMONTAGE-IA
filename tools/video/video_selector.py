"""Capability-level video selector that routes between generation and stock providers.

Provider discovery is automatic — any BaseTool with capability="video_generation"
is picked up from the registry.  Adding a new video provider requires only creating
the tool file in tools/video/; no changes to this selector are needed.
"""

from __future__ import annotations

import os

from tools.base_tool import (
    BaseTool,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)


class VideoSelector(BaseTool):
    name = "video_selector"
    version = "0.3.1"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "selector"
    stability = ToolStability.BETA
    runtime = ToolRuntime.HYBRID
    agent_skills = [
        "ai-video-gen",
        "create-video",
        "ltx2",
        "gemini-omni",
        "atlas-cloud",
    ]

    # Operations that explicitly require motion. The fork's fallback catalog
    # excludes image-only tools for every video operation.
    MOTION_REQUIRED_OPERATIONS = frozenset(
        {"image_to_video", "reference_to_video", "video_edit"}
    )
    # Default score gap for the preferred_provider override (see input_schema).
    PREFERRED_PROVIDER_GAP = 0.15

    capabilities = [
        "text_to_video",
        "image_to_video",
        "reference_to_video",
        "video_edit",
        "stock_video",
        "provider_selection",
        "search_video",
        "download_video",
    ]
    supports = {
        "user_preference_routing": True,
        "offline_fallback": True,
        "reference_image": True,
        "stock_fallback": True,
    }
    best_for = [
        "preflight routing",
        "user-facing recommendation flows",
        "switching between cloud, local, and stock video tools",
    ]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "preferred_tool": {
                "type": "string",
                "description": "Exact tool name; never falls back.",
            },
            "hosting_provider": {
                "type": "string",
                "description": "Required API host, e.g. fal.ai, atlascloud, replicate.",
            },
            "prompt": {"type": "string"},
            "preferred_provider": {
                "type": "string",
                "description": "Provider name or 'auto'. Valid values are discovered at runtime from the registry.",
                "default": "auto",
            },
            "preferred_provider_gap": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "default": 0.15,
                "description": (
                    "Max weighted-score gap (0-1) within which an explicit preferred_provider "
                    "overrides the top-ranked provider. If the preferred provider's best score "
                    "falls more than this far below the overall top, the preference is ignored "
                    "and the top-ranked provider wins. Default 0.15 — honors a preference unless "
                    "it would drag selection to a drastically worse provider."
                ),
            },
            "allowed_providers": {"type": "array", "items": {"type": "string"}},
            "operation": {
                "type": "string",
                "enum": [
                    "text_to_video",
                    "image_to_video",
                    "reference_to_video",
                    "video_edit",
                    "rank",
                ],
                "default": "text_to_video",
            },
            "target_operation": {
                "type": "string",
                "enum": [
                    "text_to_video",
                    "image_to_video",
                    "reference_to_video",
                    "video_edit",
                ],
                "description": "Operation to score when operation='rank'.",
                "default": "text_to_video",
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["16:9", "9:16", "1:1"],
                "default": "16:9",
                "description": "Requested aspect ratio; adapted to native dimensions by local providers that expose an input adapter.",
            },
            "duration": {
                "type": "string",
                "description": "Duration in seconds (e.g., '5', '10'); Wan local also accepts '5s' and maps it to 4n+1 frames at 16 FPS.",
            },
            "width": {"type": "integer", "minimum": 1, "description": "Native frame width when supported by the selected local provider."},
            "height": {"type": "integer", "minimum": 1, "description": "Native frame height when supported by the selected local provider."},
            "num_frames": {"type": "integer", "minimum": 1, "description": "Native frame count; must agree with duration when both are supplied to Wan."},
            "seed": {"type": "integer", "minimum": 0, "description": "Reproducible seed, including zero, when supported by the provider."},
            "reference_image_path": {
                "type": "string",
                "description": "Local reference for image_to_video. No automatic upload to a cloud service is performed.",
            },
            "reference_image_url": {
                "type": "string",
                "description": "URL of a reference image for image_to_video.",
            },
            "reference_image_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Reference image URLs for providers that support reference-conditioned video.",
            },
            "reference_image_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Local reference image paths for providers that support reference-conditioned video.",
            },
            "reference_video_url": {
                "type": "string",
                "description": "Reference video URL for providers that support video-conditioned generation.",
            },
            "reference_video_path": {
                "type": "string",
                "description": "Local reference video path. Providers that require URLs should reject this clearly.",
            },
            "reference_video_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Reference video URLs for mixed-media generation.",
            },
            "reference_video_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Local reference video paths for mixed-media generation.",
            },
            "reference_audio_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Reference audio URLs for mixed-media generation.",
            },
            "reference_audio_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Local reference audio paths for mixed-media generation.",
            },
            "last_image_url": {
                "type": "string",
                "description": "Optional final frame for first/last-frame generation.",
            },
            "last_image_path": {
                "type": "string",
                "description": "Optional local final frame.",
            },
            "video_url": {
                "type": "string",
                "description": "Source video URL for video editing.",
            },
            "video_path": {
                "type": "string",
                "description": "Local source video for video editing.",
            },
            "video_clips": {"type": "array", "items": {"type": "object"}},
            "refers": {"type": "array", "items": {"type": "object"}},
            "image_list": {
                "type": "array",
                "description": "Provider-specific list of image references, e.g. Kling Official Video Omni.",
            },
            "video_list": {
                "type": "array",
                "description": "Provider-specific list of video references, e.g. Kling Official Video Omni.",
            },
            "element_list": {
                "type": "array",
                "description": "Provider-specific element references, e.g. Kling Official element_id objects.",
            },
            "multi_shot": {
                "type": "boolean",
                "description": "Provider-specific multi-shot mode.",
            },
            "shot_type": {
                "type": "string",
                "description": "Provider-specific multi-shot type.",
            },
            "multi_prompt": {
                "type": "array",
                "description": "Structured multi-shot prompts; not inferred from prose.",
            },
            "image_url": {
                "type": "string",
                "description": "Alias for reference_image_url (used by some providers like Kling via fal.ai).",
            },
            "resolution": {
                "type": "string",
                "description": "Resolution hint for providers that support named output resolutions.",
            },
            "api_family": {
                "type": "string",
                "description": "Provider-specific API family hint passed through when supported, e.g. classic/turbo/omni.",
            },
            "model_name": {
                "type": "string",
                "description": "Provider-specific model name passed through when supported.",
            },
            "model": {
                "type": "string",
                "description": "Exact provider model id, e.g. an Atlas Cloud live model route.",
            },
            "model_variant": {
                "type": "string",
                "description": "Provider route variant, e.g. standard or developer.",
            },
            "mode": {
                "type": "string",
                "description": "Provider-specific quality mode passed through when supported.",
            },
            "sound": {
                "type": "string",
                "description": "Provider-specific native audio toggle passed through when supported.",
            },
            "watermark": {
                "type": "boolean",
                "description": "Provider-specific watermark toggle passed through when supported.",
            },
            "callback_url": {
                "type": "string",
                "description": "Provider-specific callback URL. Current OpenMontage providers still poll by default.",
            },
            "external_task_id": {
                "type": "string",
                "description": "Provider-specific idempotency/provenance task id.",
            },
            "workflow_json": {
                "type": "string",
                "description": (
                    "Optional full ComfyUI workflow JSON. Routes to a custom-workflow-capable "
                    "provider (e.g. comfyui_video) based on server availability, not bundled "
                    "model readiness. Requires output_node."
                ),
            },
            "workflow_path": {
                "type": "string",
                "description": (
                    "Optional path to a ComfyUI workflow JSON file. Routes to a custom-workflow-"
                    "capable provider based on server availability. Requires output_node."
                ),
            },
            "output_node": {
                "type": "string",
                "description": "ComfyUI output node ID for a custom workflow_json/workflow_path.",
            },
            "workflow_name": {
                "type": "string",
                "description": "Optional human-readable provenance label for a custom workflow.",
            },
            "workflow_model": {
                "type": "string",
                "description": "Optional model/provenance label for a custom workflow.",
            },
            "workflow_model_stack": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Optional provenance metadata for custom workflow dependencies.",
            },
            "output_path": {"type": "string"},
        },
    }

    def _providers(self) -> list[BaseTool]:
        """Auto-discover video generation providers from the registry."""
        from tools.tool_registry import registry
        from tools.provider_routing import zero_cost_candidates

        registry.ensure_discovered()
        return zero_cost_candidates([
            t
            for t in registry.get_by_capability("video_generation")
            if t.name != self.name
        ])

    @property
    def fallback_tools(self) -> list[str]:
        """Policy-eligible video alternatives for external consumers."""
        return [t.name for t in self._providers()]

    def fallback_tools_for(self, inputs: dict[str, object]) -> list[str]:
        """List only policy-eligible video tools; never propose a still downgrade.

        These are alternatives to review, not authorization to auto-switch.
        """
        return [t.name for t in self._filter_candidates(inputs, self._providers())]

    @property
    def provider_matrix(self) -> dict[str, dict[str, str]]:
        """Built at runtime from each provider's best_for field."""
        matrix = {}
        for tool in self._providers():
            strength = ", ".join(tool.best_for) if tool.best_for else tool.name
            matrix[tool.provider] = {"tool": tool.name, "strength": strength}
        return matrix

    def get_status(self) -> ToolStatus:
        if any(tool.get_status() == ToolStatus.AVAILABLE for tool in self._providers()):
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, object]) -> float:
        candidates = self._filter_candidates(inputs, self._providers())
        if not candidates:
            return 0.0
        tool, _ = self._select_best_tool(
            inputs, candidates, self._prepare_task_context(inputs)
        )
        return tool.estimate_cost(inputs) if tool else 0.0

    def estimate_runtime(self, inputs: dict[str, object]) -> float:
        candidates = self._providers()
        if not candidates:
            return 0.0
        tool, _ = self._select_best_tool(
            inputs, candidates, self._prepare_task_context(inputs)
        )
        return tool.estimate_runtime(inputs) if tool else 0.0

    def execute(self, inputs: dict[str, object]) -> ToolResult:
        from lib.scoring import rank_providers

        candidates = self._providers()

        # Rank mode — return scored provider rankings without generating
        if inputs.get("operation") == "rank":
            rank_inputs = self._rank_inputs(inputs)
            task_context = self._prepare_task_context(rank_inputs)
            candidates = self._filter_candidates(rank_inputs, candidates)
            rankings = rank_providers(candidates, task_context)
            return ToolResult(
                success=True,
                data={
                    "rankings": self._serialize_rankings(candidates, rankings),
                    "explanation": "\n".join(r.explain() for r in rankings[:5]),
                    "normalized_task_context": task_context,
                },
            )

        # Normal generation — use scored selection
        task_context = self._prepare_task_context(inputs)
        tool, score = self._select_best_tool(inputs, candidates, task_context)
        if tool is None:
            return ToolResult(
                success=False, error="No video generation provider available."
            )

        # Adapt input keys: stock tools use 'query' while generators use 'prompt'
        from tools.provider_routing import provider_inputs
        adapted = provider_inputs(inputs)
        adapter = getattr(tool, "adapt_selector_inputs", None)
        if callable(adapter):
            try:
                adapted = adapter(adapted)
            except (ValueError, TypeError) as exc:
                return ToolResult(success=False, error=str(exc))
        if hasattr(tool, "input_schema"):
            required = tool.input_schema.get("properties", {})
            if "query" in required and "query" not in adapted:
                adapted["query"] = adapted.get("prompt", "")

        # Local references stay local. A URL-only adapter is not permission to
        # publish a user's image through a separate commercial upload service.
        if adapted.get("operation") == "image_to_video" and adapted.get(
            "reference_image_path"
        ):
            tool_props = getattr(tool, "input_schema", {}).get("properties", {})
            if ("image_url" in tool_props and "reference_image_path" not in tool_props
                    and "image_url" not in adapted):
                return ToolResult(
                    success=False,
                    error="ZERO_COST_POLICY: the selected provider cannot consume a local reference; automatic cloud upload is disabled.",
                    data={"blocked_by": "zero_cost_policy", "tool": tool.name},
                )

        result = tool.execute(adapted)
        if result.success:
            result.data.setdefault("selected_tool", tool.name)
            result.data["selected_provider"] = tool.provider
            result.data["selection_reason"] = (
                score.explain() if score else f"Selected {tool.provider} ({tool.name})"
            )
            if score:
                result.data["provider_score"] = score.to_dict()
            result.data.update(self._tool_context_payload(tool))
            result.data["alternatives_considered"] = [
                t.name
                for t in candidates
                if t.name != tool.name and t.get_status().value == "available"
            ]
            # Video alternatives only; never advertise an automatic still downgrade.
            result.data.setdefault("fallback_tools", self.fallback_tools_for(inputs))
        return result

    def _select_best_tool(
        self,
        inputs: dict[str, object],
        candidates: list[BaseTool],
        task_context: dict[str, object],
    ) -> tuple[BaseTool | None, object]:
        """Select the best provider using scored ranking.

        Respects preferred_provider and environment hints as tie-breakers,
        but the scoring engine drives the primary selection.
        """
        from lib.scoring import rank_providers

        preferred = inputs.get("preferred_provider", "auto")
        allowed = set(inputs.get("allowed_providers") or [])
        if allowed:
            candidates = [tool for tool in candidates if tool.provider in allowed]
        candidates = self._filter_candidates(inputs, candidates)

        env_hint = os.environ.get("VIDEO_GEN_LOCAL_MODEL", "").lower()
        env_map = {
            "wan2.2-ti2v-5b": "wan",
            "wan2.2-t2v-a14b": "wan",
            "wan2.2-i2v-a14b": "wan",
            "wan2.1-1.3b": "wan",
            "wan2.1-14b": "wan",
            "hunyuan-1.5": "hunyuan",
            "ltx2-local": "ltx",
            "cogvideo-5b": "cogvideo",
            "cogvideo-2b": "cogvideo",
        }
        if preferred == "auto" and env_hint in env_map:
            preferred = env_map[env_hint]

        rankings = rank_providers(candidates, task_context)

        # Selectable tools, keyed by NAME (not provider). Keying by provider
        # string shadowed one of two tools that legitimately share a provider —
        # e.g. seedance_video (fal) and seedance_replicate both have
        # provider="seedance", so only the first-registered was ever reachable.
        # Keying by name keeps every backend selectable; ranking picks the best.
        selectable_by_name: dict[str, BaseTool] = {
            tool.name: tool
            for tool in candidates
            if self._tool_selectable(tool, inputs)
        }

        def _tool_for(score: object) -> BaseTool | None:
            return selectable_by_name.get(getattr(score, "tool_name", None))

        # If a preferred provider is explicitly requested, honor it ONLY when its
        # best ranked tool is within a configurable score gap of the overall top.
        # The prior code returned the preferred provider on the first ranking
        # match regardless of how far below the top it scored (the comment
        # claimed "unless drastically worse" but no gate enforced it).
        if preferred != "auto" and rankings:
            try:
                gap = float(
                    inputs.get("preferred_provider_gap", self.PREFERRED_PROVIDER_GAP)
                )
            except (TypeError, ValueError):
                gap = self.PREFERRED_PROVIDER_GAP
            top_score = rankings[0].weighted_score
            preferred_score = next(
                (
                    s
                    for s in rankings
                    if s.provider == preferred and _tool_for(s) is not None
                ),
                None,
            )
            if (
                preferred_score is not None
                and preferred_score.weighted_score >= top_score - gap
            ):
                return _tool_for(preferred_score), preferred_score

        # Return the highest-scored selectable provider
        for score in rankings:
            tool = _tool_for(score)
            if tool is not None:
                return tool, score

        return None, None

    def _prepare_task_context(self, inputs: dict[str, object]) -> dict[str, object]:
        from lib.scoring import normalize_task_context

        return normalize_task_context(
            inputs.get("task_context", {}),
            prompt=str(inputs.get("prompt", "")),
            capability=self.capability,
            operation=str(inputs.get("operation", "text_to_video")),
        )

    @staticmethod
    def _rank_inputs(inputs: dict[str, object]) -> dict[str, object]:
        rank_inputs = dict(inputs)
        rank_inputs["operation"] = inputs.get("target_operation", "text_to_video")
        return rank_inputs

    @staticmethod
    def _tool_context_payload(tool: BaseTool) -> dict[str, object]:
        info = tool.get_info()
        return {
            "selected_tool_agent_skills": info.get("agent_skills", []),
            "required_agent_skills": info.get("agent_skills", []),
            "selected_tool_usage_location": info.get("usage_location"),
            "selected_tool_best_for": info.get("best_for", []),
        }

    def _serialize_rankings(
        self, candidates: list[BaseTool], rankings: list[object]
    ) -> list[dict[str, object]]:
        tool_by_name = {tool.name: tool for tool in candidates}
        serialized: list[dict[str, object]] = []
        for score in rankings:
            item = score.to_dict()
            tool = tool_by_name.get(score.tool_name)
            if tool:
                info = tool.get_info()
                item["agent_skills"] = info.get("agent_skills", [])
                item["usage_location"] = info.get("usage_location")
                item["best_for"] = info.get("best_for", [])
                item["supports"] = info.get("supports", {})
                item["status"] = str(tool.get_status())
            serialized.append(item)
        return serialized

    def _filter_candidates(
        self,
        inputs: dict[str, object],
        candidates: list[BaseTool],
    ) -> list[BaseTool]:
        from tools.provider_routing import filter_explicit_route

        candidates = filter_explicit_route(inputs, candidates)
        exact_model = inputs.get("model")
        if exact_model:
            model_matches = [
                tool
                for tool in candidates
                if exact_model
                in getattr(tool, "input_schema", {})
                .get("properties", {})
                .get("model", {})
                .get("enum", [])
                or exact_model in tool.get_info().get("model_catalog", {})
            ]
            candidates = model_matches

        # A caller-supplied custom workflow is provider-specific (ComfyUI graph
        # JSON). Route it only to custom-workflow-capable providers whose server
        # is reachable — bundled-model readiness is irrelevant in that case.
        if self._has_custom_workflow(inputs):
            return [t for t in candidates if self._custom_workflow_eligible(t, inputs)]

        operation = inputs.get("operation", "text_to_video")
        if operation == "rank":
            operation = inputs.get("target_operation", "text_to_video")

        filtered: list[BaseTool] = []
        for tool in candidates:
            supports = getattr(tool, "supports", {})
            props = getattr(tool, "input_schema", {}).get("properties", {})

            if operation == "image_to_video":
                if (
                    supports.get("image_to_video")
                    or "image_url" in props
                    or "reference_image_url" in props
                ):
                    if self._operation_ready(tool, "image_to_video"):
                        filtered.append(tool)
                continue

            if operation == "reference_to_video":
                if (
                    supports.get("reference_to_video")
                    or "reference_image_urls" in props
                ):
                    filtered.append(tool)
                continue

            if self._operation_ready(tool, str(operation)):
                filtered.append(tool)

        # No capability match is a blocker, not permission to send an I2V or
        # reference request to a text-only generator.
        return filtered

    @staticmethod
    def _operation_ready(tool: BaseTool, operation: str) -> bool:
        checker = getattr(tool, "is_operation_available", None)
        if not callable(checker):
            return True
        return bool(checker(operation))

    @staticmethod
    def _has_custom_workflow(inputs: dict[str, object]) -> bool:
        return bool(inputs.get("workflow_json") or inputs.get("workflow_path"))

    def _custom_workflow_eligible(
        self, tool: BaseTool, inputs: dict[str, object]
    ) -> bool:
        """Whether a tool can run the caller-supplied custom workflow.

        Eligibility is based on server availability, not bundled-model readiness:
        a provider qualifies when it advertises ``custom_workflow`` support, an
        ``output_node`` is supplied, and its backend is reachable (status is not
        UNAVAILABLE).
        """
        if not self._has_custom_workflow(inputs):
            return False
        if not inputs.get("output_node"):
            return False
        supports = getattr(tool, "supports", {})
        if not supports.get("custom_workflow"):
            return False
        return tool.get_status() != ToolStatus.UNAVAILABLE

    def _tool_selectable(self, tool: BaseTool, inputs: dict[str, object]) -> bool:
        """A provider is selectable if it is AVAILABLE, or if it can serve a
        caller-supplied custom workflow even while bundled models report DEGRADED."""
        if tool.get_status() == ToolStatus.AVAILABLE:
            return True
        return self._custom_workflow_eligible(tool, inputs)
