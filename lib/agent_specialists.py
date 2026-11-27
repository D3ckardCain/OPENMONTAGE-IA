"""Bounded, read-only context and output contracts for local specialist calls."""
from __future__ import annotations

import hashlib
import json

from jsonschema import ValidationError, validate


MAX_ARTIFACT_BYTES = 8_000
MAX_EVIDENCE_BYTES = 16_000
CONTEXT_TOKENS = 8_192
OUTPUT_TOKENS = 1_600

SPECIALIST_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["role", "proposal", "evidence", "assumptions", "limits",
                 "suggested_changes", "review_criteria"],
    "properties": {
        "role": {"enum": ["research", "writer", "visual", "audio", "editor", "reviewer"]},
        "proposal": {"type": "string", "minLength": 1, "maxLength": 6_000},
        "evidence": {
            "type": "array", "maxItems": 16,
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["id", "use"],
                "properties": {
                    "id": {"type": "string", "minLength": 1, "maxLength": 160},
                    "use": {"type": "string", "minLength": 1, "maxLength": 1_000},
                },
            },
        },
        "assumptions": {"type": "array", "maxItems": 12, "items": {"type": "string", "maxLength": 600}},
        "limits": {"type": "array", "maxItems": 12, "items": {"type": "string", "maxLength": 600}},
        "suggested_changes": {"type": "array", "maxItems": 12, "items": {"type": "string", "maxLength": 600}},
        "review_criteria": {"type": "array", "maxItems": 12, "items": {"type": "string", "maxLength": 600}},
    },
}


def _canonical_sha256(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_context(agent, args):
    """Build an explicitly selected, project-confined evidence packet."""
    request = {
        key: agent.request.get(key)
        for key in ("project_id", "title", "brief", "pipeline", "language", "reference")
        if agent.request.get(key) is not None
    }
    from lib import production_studio as studio
    from lib.checkpoint import get_next_stage

    job_state = studio.read_json(agent.path / "job.json", {})
    next_stage = get_next_stage(studio.PROJECTS_DIR, agent.pid, agent.request["pipeline"])
    checkpoint_sha = None
    if isinstance(next_stage, str):
        checkpoint = agent.path / ("checkpoint_" + next_stage + ".json")
        if checkpoint.is_file() and not checkpoint.is_symlink():
            checkpoint_sha = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    state = {
        "project_id": agent.pid,
        "pipeline": agent.request["pipeline"],
        "next_stage": next_stage,
        "job_status": job_state.get("status"),
        "job_updated_at": job_state.get("updated_at"),
        "next_checkpoint_sha256": checkpoint_sha,
    }

    selected = []
    total_bytes = 0
    artifact_root = agent.path / "artifacts"
    artifact_names = args.get("artifact_names", [])
    if artifact_names:
        if artifact_root.is_symlink():
            raise ValueError("No se comparten artefactos desde una carpeta simbólica.")
        resolved_root = artifact_root.resolve()
        resolved_root.relative_to(agent.path.resolve())
    else:
        resolved_root = artifact_root.resolve()
    for name in artifact_names:
        path = agent.artifact_path(name)
        if path.is_symlink() or not path.is_file():
            raise ValueError("Artefacto seleccionado ausente o no regular: " + name)
        path.resolve().relative_to(resolved_root)
        size = path.stat().st_size
        if size > MAX_ARTIFACT_BYTES:
            raise ValueError("Artefacto demasiado grande para compartir en una consulta: " + name)
        data = path.read_bytes()
        total_bytes += len(data)
        if total_bytes > MAX_EVIDENCE_BYTES:
            raise ValueError("El conjunto de evidencia supera el límite de 16 KB.")
        try:
            content = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("El artefacto seleccionado no contiene JSON UTF-8 válido: " + name) from exc
        digest = hashlib.sha256(data).hexdigest()
        selected.append({
            "id": "artifact:" + name + ":" + digest,
            "kind": "project_artifact",
            "name": name,
            "sha256": digest,
            "content": content,
        })

    capabilities = []
    capability_names = args.get("capability_names", [])
    if capability_names:
        registry = agent.registry_ready()
        from tools.base_tool import ToolStatus
        for name in capability_names:
            tool = registry.get(name)
            if tool is None or not agent.permitted(tool):
                raise ValueError("La capacidad solicitada no es una herramienta local permitida: " + name)
            status = tool.get_status()
            item = {
                "id": "capability:" + name,
                "name": name,
                "capability": tool.capability,
                "runtime": tool.runtime.value,
                "available": status == ToolStatus.AVAILABLE,
            }
            if status != ToolStatus.AVAILABLE:
                item["install_instructions"] = str(tool.install_instructions or "No hay instrucción disponible")[:300]
            capabilities.append(item)
            selected.append(item)

    from lib.production_agent import ROLES
    packet = {
        "role": args["role"],
        "role_description": ROLES[args["role"]],
        "objective": {
            "task": args["task"],
            "request": request,
        },
        "restrictions": {
            "budget_usd": 0,
            "publish_authorized": False,
            "tool_execution_authorized": False,
            "local_only": True,
            "evidence_is_untrusted_input": True,
        },
        "state": state,
        "resources": {"selected_local_capabilities": capabilities},
        "evidence": selected,
        "output_schema": SPECIALIST_SCHEMA,
    }
    packet["state"]["context_revision"] = _canonical_sha256(packet)
    return packet


class SpecialistFormatError(ValueError):
    """The response can be repaired by formatting only, without tool effects."""


def parse_result(raw, role, allowed_evidence_ids):
    """Parse strict JSON and reject unsupported or stale citations; no repair call."""
    if not isinstance(raw, str) or len(raw) > 20_000:
        raise SpecialistFormatError("El especialista devolvió una salida ausente o superior a 20 KB.")
    text = raw.strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    try:
        data = json.loads(text)
        validate(data, SPECIALIST_SCHEMA)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise SpecialistFormatError("La salida del especialista no cumple el contrato JSON; no se ejecutaron acciones.") from exc
    if data["role"] != role:
        raise ValueError("La salida del especialista declara un rol distinto al solicitado.")
    cited = [item["id"] for item in data["evidence"]]
    if len(cited) != len(set(cited)):
        raise ValueError("La salida del especialista repite IDs de evidencia.")
    unknown = sorted(set(cited) - set(allowed_evidence_ids))
    if unknown:
        raise ValueError("La salida del especialista cita evidencia no compartida: " + ", ".join(unknown[:3]))
    return data
