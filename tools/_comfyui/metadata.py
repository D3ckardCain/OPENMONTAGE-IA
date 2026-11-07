"""Shared metadata helpers for ComfyUI provider tools."""

from __future__ import annotations

import hashlib
import json
from typing import Any


COMFYUI_SETUP_OFFER: dict[str, Any] = {
    "kind": "local_server",
    "fix_complexity": "1-minute env-var if ComfyUI is already running; otherwise local install",
    "env_var": "COMFYUI_SERVER_URL",
    "default_url": "http://localhost:8188",
    "health_check": "GET /system_stats",
    "what_it_unlocks": [
        "free local image generation through ComfyUI workflows",
        "free local video generation through ComfyUI workflows",
        "community workflow_json/workflow_path execution",
    ],
    # Optional: point image/video generation at separate ComfyUI instances
    # (e.g. different GPUs). Each overrides COMFYUI_SERVER_URL for its own
    # tool only; single-server setups can ignore this entirely.
    "per_capability_env_var_overrides": {
        "comfyui_image": "COMFYUI_IMAGE_SERVER_URL",
        "comfyui_video": "COMFYUI_VIDEO_SERVER_URL",
        "comfyui_music": "COMFYUI_MUSIC_SERVER_URL",
    },
}


BUNDLED_MODEL_STACKS: dict[str, list[dict[str, Any]]] = {
    "minimax-h3-local": [
        {
            "role": "diffusion_model",
            "name": "minimax_h3_fl2va_pruned_int8_convrot.safetensors",
            "quantization": "INT8 ConvRot",
            "destination_hint": "ComfyUI/models/diffusion_models/",
            "download_url": "https://huggingface.co/Comfy-Org/MiniMax-H3/tree/main/diffusion_models",
        },
        {
            "role": "text_encoder",
            "name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
            "quantization": "NVFP4 AWQ",
            "destination_hint": "ComfyUI/models/text_encoders/",
            "download_url": "https://huggingface.co/Comfy-Org/MiniMax-H3/tree/main/text_encoders",
        },
        {
            "role": "video_vae",
            "name": "minimax_h3_video_vae_fp16.safetensors",
            "destination_hint": "ComfyUI/models/vae/",
            "download_url": "https://huggingface.co/Comfy-Org/MiniMax-H3/tree/main/vae",
        },
        {
            "role": "audio_vae",
            "name": "minimax_h3_audio_vae_fp32.safetensors",
            "destination_hint": "ComfyUI/models/vae/",
            "download_url": "https://huggingface.co/Comfy-Org/MiniMax-H3/tree/main/vae",
        },
    ],
    "flux2-txt2img": [
        {
            "role": "diffusion_model",
            "name": "flux2-dev-nvfp4.safetensors",
            "quantization": "NVFP4",
            "destination_hint": "ComfyUI/models/diffusion_models/",
            "download_url": (
                "https://huggingface.co/black-forest-labs/FLUX.2-dev-NVFP4"
            ),
        },
        {
            "role": "text_encoder",
            "name": "mistral_3_small_flux2_fp4_mixed.safetensors",
            "quantization": "FP4 mixed",
            "destination_hint": "ComfyUI/models/text_encoders/",
            "download_url": (
                "https://huggingface.co/Comfy-Org/flux2-dev/tree/main/"
                "split_files/text_encoders"
            ),
        },
        {
            "role": "vae",
            "name": "flux2-vae.safetensors",
            "destination_hint": "ComfyUI/models/vae/",
            "download_url": (
                "https://huggingface.co/Comfy-Org/flux2-dev/blob/main/"
                "split_files/vae/flux2-vae.safetensors"
            ),
        },
    ],
    "wan22-t2v-4step": [
        {
            "role": "text_encoder",
            "name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
            "quantization": "FP8",
            "destination_hint": "ComfyUI/models/text_encoders/",
            "download_url": 'https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors?download=true',
            "download_revision": 'ee6f4a40737a995bf5818954cfce6d59443b0f04',
            "expected_size_bytes": 6735906897,
            "sha256": 'c3355d30191f1f066b26d93fba017ae9809dce6c627dda5f6a66eaa651204f68'
        },
        {
            "role": "diffusion_model_high_noise",
            "name": "wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors",
            "quantization": "FP8",
            "destination_hint": "ComfyUI/models/diffusion_models/",
            "download_url": 'https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors?download=true',
            "download_revision": 'ee6f4a40737a995bf5818954cfce6d59443b0f04',
            "expected_size_bytes": 14293923632,
            "sha256": 'cad711ae211c8b23455ec68cd6a190a33a3d874234a77eb57266d73f8f0e6c9f'
        },
        {
            "role": "diffusion_model_low_noise",
            "name": "wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors",
            "quantization": "FP8",
            "destination_hint": "ComfyUI/models/diffusion_models/",
            "download_url": 'https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors?download=true',
            "download_revision": 'ee6f4a40737a995bf5818954cfce6d59443b0f04',
            "expected_size_bytes": 14293923632,
            "sha256": 'e71b96d7c82e638694c5e7fb98fac4bfb0e4ddc5fbbb4b1df40da8f0f1278a97'
        },
        {
            "role": "vae",
            "name": "wan_2.1_vae.safetensors",
            "destination_hint": "ComfyUI/models/vae/",
            "download_url": 'https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/vae/wan_2.1_vae.safetensors?download=true',
            "download_revision": 'ee6f4a40737a995bf5818954cfce6d59443b0f04',
            "expected_size_bytes": 253815318,
            "sha256": '2fc39d31359a4b0a64f55876d8ff7fa8d780956ae2cb13463b0223e15148976b'
        },
        {
            "role": "lora",
            "name": "wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors",
            "strength_model": 1.0,
            "destination_hint": "ComfyUI/models/loras/",
            "download_url": 'https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors?download=true',
            "download_revision": 'ee6f4a40737a995bf5818954cfce6d59443b0f04',
            "expected_size_bytes": 1226977424,
            "sha256": '698321cb86bd30c4af06c9b84e656a1048c8cb54e06d50694536fb5de37fde41'
        },
        {
            "role": "lora",
            "name": "wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors",
            "strength_model": 1.0,
            "destination_hint": "ComfyUI/models/loras/",
            "download_url": 'https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors?download=true',
            "download_revision": 'ee6f4a40737a995bf5818954cfce6d59443b0f04',
            "expected_size_bytes": 1226977424,
            "sha256": 'ec95216e614b3c132c11bfb387b11feedf62163150ccc9068bca8a189771e75a'
        },
    ],
    "wan22-i2v-4step": [
        {
            "role": "text_encoder",
            "name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
            "quantization": "FP8",
            "destination_hint": "ComfyUI/models/text_encoders/",
            "download_url": 'https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors?download=true',
            "download_revision": 'ee6f4a40737a995bf5818954cfce6d59443b0f04',
            "expected_size_bytes": 6735906897,
            "sha256": 'c3355d30191f1f066b26d93fba017ae9809dce6c627dda5f6a66eaa651204f68'
        },
        {
            "role": "diffusion_model_high_noise",
            "name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
            "quantization": "FP8",
            "destination_hint": "ComfyUI/models/diffusion_models/",
            "download_url": 'https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors?download=true',
            "download_revision": 'ee6f4a40737a995bf5818954cfce6d59443b0f04',
            "expected_size_bytes": 14294742832,
            "sha256": '6122e79d55e0f235698d11d657f3b196c5273c830da00b2b013c5a048d5e6a42'
        },
        {
            "role": "diffusion_model_low_noise",
            "name": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
            "quantization": "FP8",
            "destination_hint": "ComfyUI/models/diffusion_models/",
            "download_url": 'https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors?download=true',
            "download_revision": 'ee6f4a40737a995bf5818954cfce6d59443b0f04',
            "expected_size_bytes": 14294742832,
            "sha256": '5471a457b6ac404202a5fbe6c11595a3d5641fc766b00f38763f72303fffc21e'
        },
        {
            "role": "vae",
            "name": "wan_2.1_vae.safetensors",
            "destination_hint": "ComfyUI/models/vae/",
            "download_url": 'https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/vae/wan_2.1_vae.safetensors?download=true',
            "download_revision": 'ee6f4a40737a995bf5818954cfce6d59443b0f04',
            "expected_size_bytes": 253815318,
            "sha256": '2fc39d31359a4b0a64f55876d8ff7fa8d780956ae2cb13463b0223e15148976b'
        },
        {
            "role": "lora",
            "name": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors",
            "strength_model": 1.0,
            "destination_hint": "ComfyUI/models/loras/",
            "download_url": 'https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors?download=true',
            "download_revision": 'ee6f4a40737a995bf5818954cfce6d59443b0f04',
            "expected_size_bytes": 1226977424,
            "sha256": 'd176c808d6fc461999b68e321efcb7501b20b8c3797523ed0df14f7d1deff11e'
        },
        {
            "role": "lora",
            "name": "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors",
            "strength_model": 1.0,
            "destination_hint": "ComfyUI/models/loras/",
            "download_url": 'https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors?download=true',
            "download_revision": 'ee6f4a40737a995bf5818954cfce6d59443b0f04',
            "expected_size_bytes": 1226977424,
            "sha256": '024f21de095bc8fad9809ded3e9e49a2e170dcf27075da8145ba7d60d8aab7f9'
        },
    ],
    "ace-step-1-t2a": [
        {
            "role": "checkpoint",
            "name": "ace_step_v1_3.5b.safetensors",
            "destination_hint": "ComfyUI/models/checkpoints/",
            "download_url": (
                "https://huggingface.co/Comfy-Org/ACE-Step_ComfyUI_repackaged/"
                "blob/main/all_in_one/ace_step_v1_3.5b.safetensors"
            ),
        },
    ],
}


def workflow_hash(workflow: dict[str, Any]) -> str:
    """Return a stable hash of the final workflow JSON submitted to ComfyUI."""
    payload = json.dumps(workflow, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def model_stack(
    workflow_key: str | None, inputs: dict[str, Any]
) -> list[dict[str, Any]]:
    """Return bundled or caller-supplied model stack metadata."""
    if workflow_key:
        return [dict(item) for item in BUNDLED_MODEL_STACKS[workflow_key]]
    stack = inputs.get("workflow_model_stack")
    return stack if isinstance(stack, list) else []


def missing_models_payload(
    missing: list[str],
    *,
    workflow_key: str,
    workflow_name: str,
    operation: str | None = None,
) -> dict[str, Any]:
    """Build a machine-readable missing-model error payload."""
    stack_by_name = {
        item["name"]: item for item in BUNDLED_MODEL_STACKS.get(workflow_key, [])
    }
    items = []
    for name in missing:
        meta = dict(stack_by_name.get(name, {}))
        meta.setdefault("name", name)
        meta.setdefault("role", "unknown")
        meta.setdefault(
            "destination_hint", "ComfyUI/models/ matching the workflow node"
        )
        meta.setdefault("download_url", None)
        items.append(meta)

    return {
        "provider": "comfyui",
        "workflow": workflow_name,
        "operation": operation,
        "missing_models": items,
        "setup_offer": COMFYUI_SETUP_OFFER,
    }
