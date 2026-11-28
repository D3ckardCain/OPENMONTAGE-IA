"""Local-only publication planning.

This tool persists a versioned draft bound to a project media hash. It never
authenticates, uploads, schedules remotely, or claims a platform accepted it.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from tools.base_tool import (
    BaseTool, Determinism, ExecutionMode, ResourceProfile, ToolResult,
    ToolRuntime, ToolStability, ToolTier,
)


_PLAN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_PLATFORMS = {"youtube", "facebook_page", "instagram_professional"}
_VISIBILITIES = {"public", "private", "unlisted"}
_SECRET_KEYS = {"token", "access_token", "refresh_token", "client_secret", "password", "cookie", "authorization"}
_INPUT_KEYS = {"project_dir", "plan_id", "revision", "media_path", "targets", "created_at"}


def _iso_datetime(value: str, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} debe ser texto ISO-8601.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} debe ser una fecha ISO-8601 con zona horaria.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} debe incluir un offset explícito.")
    return parsed


def _target_schedule(target: dict[str, Any], now: datetime) -> tuple[str | None, str]:
    timezone_name = target.get("timezone")
    scheduled_for = target.get("scheduled_for")
    if not isinstance(timezone_name, str) or not timezone_name.strip():
        raise ValueError("Cada destino requiere su zona IANA explícita.")
    try:
        zone = timezone.utc if timezone_name in {"UTC", "Etc/UTC", "Etc/GMT"} else ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"Zona IANA desconocida: {timezone_name}") from exc

    if scheduled_for is None:
        return None, timezone_name
    scheduled = _iso_datetime(scheduled_for, "scheduled_for")
    local = scheduled.astimezone(zone)
    # An explicit offset must round-trip through the chosen IANA zone. This
    # rejects nonexistent wall times and offsets that disagree with DST.
    if local.replace(tzinfo=None) != scheduled.replace(tzinfo=None) or local.utcoffset() != scheduled.utcoffset():
        raise ValueError("scheduled_for no coincide con la zona IANA indicada (revisa DST y offset).")
    if scheduled.astimezone(timezone.utc) <= now.astimezone(timezone.utc):
        raise ValueError("No se aceptan fechas pasadas; define una fecha futura para evitar publicación inmediata.")
    return scheduled.isoformat(), timezone_name


class LocalPublishPlan(BaseTool):
    name = "local_publish_plan"
    version = "0.1.0"
    tier = ToolTier.PUBLISH
    capability = "publish"
    provider = "local"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL
    dependencies: list[str] = []
    install_instructions = "No requiere instalación; usa la biblioteca estándar de Python."
    agent_skills: list[str] = []
    capabilities = ["plan_local_publication", "persist_publication_draft"]
    supports = {"local_offline": True, "free": True, "uploads": False, "remote_scheduling": False}
    best_for = ["guardar un plan de publicación por proyecto y destino sin iniciar sesión ni transferir medios"]
    not_good_for = ["autenticación, carga de medios, programación remota o confirmación de publicación"]
    input_schema = {
        "type": "object",
        "required": ["project_dir", "plan_id", "revision", "media_path", "targets"],
        "additionalProperties": False,
        "properties": {
            "project_dir": {"type": "string"},
            "plan_id": {"type": "string"},
            "revision": {"type": "integer", "minimum": 1},
            "media_path": {"type": "string", "description": "Ruta relativa al proyecto; el medio no se copia ni transmite."},
            "targets": {
                "type": "array", "minItems": 1,
                "items": {"type": "object"},
                "description": "Destino explícito, privacidad solicitada, zona IANA, horario opcional y metadatos.",
            },
            "created_at": {"type": "string", "description": "ISO-8601 con offset; opcional, por defecto hora UTC local."},
        },
    }
    output_schema = {"type": "object", "properties": {"plan": {"type": "object"}, "plan_path": {"type": "string"}}}
    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=64, vram_mb=0, disk_mb=1, network_required=False)
    side_effects = ["writes a versioned draft JSON under the existing project"]
    user_visible_verification = ["Open publication/plans/<plan_id>-v<revision>.json and confirm status is draft and no credentials are present"]

    @staticmethod
    def _project_media(project_dir: Path, relative_path: str) -> tuple[Path, str]:
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ValueError("media_path relativa requerida.")
        rel = Path(relative_path)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("media_path debe permanecer dentro del proyecto.")
        project = project_dir.resolve(strict=True)
        candidate = (project / rel).resolve(strict=True)
        if not candidate.is_relative_to(project) or not candidate.is_file():
            raise ValueError("media_path debe ser un archivo dentro del proyecto.")
        digest = hashlib.sha256()
        with candidate.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return candidate, digest.hexdigest()

    @staticmethod
    def _validate_target(target: Any, now: datetime, plan_id: str, revision: int, media_sha256: str, index: int) -> dict[str, Any]:
        if not isinstance(target, dict):
            raise ValueError("Cada destino debe ser un objeto.")
        if any(str(key).lower() in _SECRET_KEYS for key in target):
            raise ValueError("No incluyas tokens, contraseñas, cookies ni credenciales en el plan.")
        allowed = {"platform", "destination_id", "visibility", "timezone", "scheduled_for", "title", "description", "tags"}
        if set(target) - allowed:
            raise ValueError("El destino contiene campos no admitidos; no guardes secretos ni estado remoto aquí.")
        platform = target.get("platform")
        if platform not in _PLATFORMS:
            raise ValueError("Plataforma no admitida por el borrador local.")
        destination_id = target.get("destination_id")
        if not isinstance(destination_id, str) or not destination_id.strip() or len(destination_id) > 200:
            raise ValueError("Cada destino requiere un ID remoto explícito; no se infiere por nombre.")
        visibility = target.get("visibility")
        if visibility not in _VISIBILITIES:
            raise ValueError("Indica explícitamente public, private o unlisted.")
        title = target.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Cada destino requiere título explícito.")
        description = target.get("description", "")
        tags = target.get("tags", [])
        if not isinstance(description, str) or not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise ValueError("Descripción y etiquetas deben ser texto.")
        scheduled_for, timezone_name = _target_schedule(target, now)
        request_material = json.dumps(
            [plan_id, revision, index, platform, destination_id, media_sha256, visibility, scheduled_for, timezone_name, title, description, tags],
            ensure_ascii=False, separators=(",", ":"), sort_keys=True,
        ).encode("utf-8")
        return {
            "platform": platform,
            "destination_id": destination_id.strip(),
            "visibility": visibility,
            "timezone": timezone_name,
            "scheduled_for": scheduled_for,
            "title": title.strip(),
            "description": description,
            "tags": tags,
            "request_id": hashlib.sha256(request_material).hexdigest(),
            "remote_status": "not_submitted",
        }

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        try:
            if set(inputs) - _INPUT_KEYS:
                raise ValueError("La solicitud contiene campos no admitidos; el plan no admite credenciales.")
            project_dir = Path(inputs["project_dir"]).expanduser().resolve(strict=True)
            if not project_dir.is_dir():
                raise ValueError("project_dir debe ser un proyecto existente.")
            plan_id = inputs["plan_id"]
            revision = inputs["revision"]
            if not isinstance(plan_id, str) or not _PLAN_ID.fullmatch(plan_id):
                raise ValueError("plan_id debe ser un identificador simple de hasta 64 caracteres.")
            if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
                raise ValueError("revision debe ser un entero positivo.")
            media_path, media_sha256 = self._project_media(project_dir, inputs["media_path"])
            now = _iso_datetime(inputs["created_at"], "created_at") if inputs.get("created_at") else datetime.now(timezone.utc)
            targets = inputs["targets"]
            if not isinstance(targets, list) or not targets:
                raise ValueError("Incluye al menos un destino explícito.")
            clean_targets = [self._validate_target(t, now, plan_id, revision, media_sha256, i) for i, t in enumerate(targets)]
            identity = [(t["platform"], t["destination_id"]) for t in clean_targets]
            if len(set(identity)) != len(identity):
                raise ValueError("No repitas el mismo destino dentro del plan.")

            plan = {
                "schema_version": "1.0",
                "plan_id": plan_id,
                "revision": revision,
                "status": "draft",
                "execution": "local_plan_only",
                "created_at": now.isoformat(),
                "media": {
                    "project_relative_path": media_path.relative_to(project_dir).as_posix(),
                    "sha256": media_sha256,
                },
                "targets": clean_targets,
                "remote_submission": False,
            }
            payload = (json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")

            parent = project_dir / "publication"
            plans_dir = parent / "plans"
            if parent.is_symlink() or plans_dir.is_symlink():
                raise ValueError("No se permiten enlaces simbólicos en la ruta del plan.")
            plans_dir.mkdir(parents=True, exist_ok=True)
            output = plans_dir / f"{plan_id}-v{revision}.json"
            temp_path: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(dir=plans_dir, prefix=".plan-", suffix=".tmp", delete=False) as stream:
                    temp_path = Path(stream.name)
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                # Same-volume hard link atomically creates without overwriting.
                os.link(temp_path, output)
            except FileExistsError:
                existing = json.loads(output.read_text(encoding="utf-8"))
                comparable_existing = dict(existing)
                comparable_plan = dict(plan)
                comparable_existing.pop("created_at", None)
                comparable_plan.pop("created_at", None)
                if comparable_existing != comparable_plan:
                    raise ValueError("Conflicto: el plan/version ya existe con contenido diferente; crea otra revisión.")
                return ToolResult(success=True, data={"plan": existing, "plan_path": str(output), "idempotent_reuse": True})
            finally:
                if temp_path is not None:
                    temp_path.unlink(missing_ok=True)
            return ToolResult(success=True, data={"plan": plan, "plan_path": str(output), "idempotent_reuse": False})
        except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return ToolResult(success=False, error=str(exc), data={"remote_submission": False})
