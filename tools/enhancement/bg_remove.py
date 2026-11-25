"""Background removal tool wrapping rembg.

Removes backgrounds from images using the rembg library (U2Net models).
Outputs transparent PNGs or composites onto a custom background color.
Requires explicitly prepared local weights and artifact-bound license review.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)


class BgRemove(BaseTool):
    name = "bg_remove"
    version = "0.2.0"
    tier = ToolTier.ENHANCE
    capability = "enhancement"
    provider = "rembg"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = ["python:rembg", "python:PIL"]
    install_instructions = (
        "pip install rembg       # CPU mode\n"
        "pip install rembg[gpu]  # GPU mode (requires CUDA + onnxruntime-gpu)"
    )
    agent_skills = ["ffmpeg"]

    capabilities = [
        "background_removal",
        "alpha_matte",
        "custom_background",
        "explicit_local_weights",
        "artifact_provenance",
    ]

    input_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["project_id", "input_path", "output_path", "model", "model_path", "model_sha256", "license_review"],
        "properties": {
            "project_id": {"type": "string", "description": "Owning existing project"},
            "model_path": {"type": "string", "description": "Explicit local ONNX path; no cache scan/download"},
            "model_sha256": {"type": "string", "pattern": "^[a-fA-F0-9]{64}$"},
            "license_review": {"type": "object", "description": "Reviewed artifact SHA/license/source/revision, commercial_use yes, requires_paid_agreement false"},
            "input_path": {
                "type": "string",
                "description": "Path to image or video frame",
            },
            "output_path": {
                "type": "string",
                "description": "New PNG inside the owning project; never overwrite an existing file",
            },
            "model": {
                "type": "string",
                "enum": ["u2net", "u2net_human_seg", "isnet-general-use"],
            },
            "bg_color": {
                "type": "string",
                "description": "Replacement background color hex (e.g. #00FF00). Transparent if not set.",
            },
            "alpha_matting": {
                "type": "boolean",
                "default": False,
                "description": "Use alpha matting for finer edges",
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=2, ram_mb=2048, vram_mb=0, disk_mb=500
    )

    idempotency_key_fields = ["project_id", "input_path", "output_path", "model", "model_sha256", "license_review", "bg_color", "alpha_matting"]
    side_effects = ["writes a new project PNG; no model downloads or cloud fallback"]
    user_visible_verification = [
        "Inspect output for clean edges around the subject",
        "Verify transparency or background color is applied correctly",
    ]

    def get_status(self) -> ToolStatus:
        from importlib.util import find_spec
        try:
            if find_spec('rembg') and find_spec('PIL'):
                return ToolStatus.DEGRADED  # artifact/license preflight still required
        except (ImportError, ValueError):
            pass
        return ToolStatus.UNAVAILABLE

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        from io import BytesIO
        from importlib.metadata import version, PackageNotFoundError
        from lib.bg_remove_local import preflight, local_session, checksum, LocalModelError
        started = time.time()
        output_created = False
        prepared = None
        try:
            prepared = preflight(inputs)
            try:
                import rembg
                from PIL import Image
            except ImportError as exc:
                return ToolResult(success=False, error='Proveedor local no disponible; prepara un entorno compatible sin descargar pesos: '+str(exc),
                                  data={'error_code':'provider_unavailable'})
            session = local_session(prepared['model'], prepared['model_path'], prepared['model_sha256'])
            with Image.open(prepared['input_path']) as image:
                image.load()
                result_image = rembg.remove(image.copy(), session=session,
                                           alpha_matting=inputs.get('alpha_matting', False))
            if not isinstance(result_image, Image.Image) or 'A' not in result_image.getbands():
                raise ValueError('El proveedor no devolvió una imagen con alpha; no se fabrica una máscara')
            color = inputs.get('bg_color')
            if color:
                value = color.lstrip('#')
                rgb = tuple(int(value[i:i+2], 16) for i in (0,2,4))
                background = Image.new('RGBA', result_image.size, (*rgb,255))
                result_image = Image.alpha_composite(background, result_image.convert('RGBA')).convert('RGB')
            rechecked = preflight(inputs)  # cached hashes, revalidate paths and ownership
            if rechecked['input_sha256'] != prepared['input_sha256'] or rechecked['model_sha256'] != prepared['model_sha256']:
                raise ValueError('La entrada o el modelo cambió durante el procesamiento; resultado no publicado')
            encoded = BytesIO()
            result_image.save(encoded, format='PNG')
            output = prepared['output_path']
            output.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation also protects against a file appearing after preflight.
            with output.open('xb') as stream:
                output_created = True
                stream.write(encoded.getvalue())
            try:
                provider_version = version('rembg')
            except PackageNotFoundError:
                provider_version = 'unknown'
            return ToolResult(success=True, artifacts=[str(output)], duration_seconds=time.time()-started,
                data={'input':str(prepared['input_path']),'output':str(output),'model':prepared['model'],
                      'alpha_matting':inputs.get('alpha_matting',False),'bg_color':color,
                      'width':result_image.width,'height':result_image.height,'mode':result_image.mode,
                      'local_only':True,'provider':'CPUExecutionProvider','rembg_version':provider_version,
                      'provenance':{'input_sha256':prepared['input_sha256'],'output_sha256':checksum(output),
                          'model_path':str(prepared['model_path']),'model_sha256':prepared['model_sha256'],
                          'license_review':prepared['license_review'],
                          'license_status':'operator_declared_not_independently_verified'}})
        except Exception as exc:
            data={'error_code':exc.code if isinstance(exc,LocalModelError) else 'local_processing_failed'}
            if output_created and prepared:
                # Never promote a partial/error as a successful artifact or delete originals.
                data['unapproved_output']=str(prepared['output_path'])
            return ToolResult(success=False,error=str(exc),data=data,duration_seconds=time.time()-started)
