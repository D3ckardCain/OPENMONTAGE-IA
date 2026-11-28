"""Project-scoped Wan 2.2 T2V jobs through the existing local ComfyUI tool."""
from __future__ import annotations

import hashlib
import json
import re
import threading
import uuid
from pathlib import Path

from lib import production_studio as studio, studio_editor as editor

ACTIVE: dict[tuple[str, str], threading.Thread] = {}
MAX_PROMPT_CHARS = 2000
PROFILE = "wan22-14b-t2v-4step"


class GenerationUnavailable(RuntimeError):
    """Local ComfyUI or its Wan T2V model stack is not available."""


def _request_id(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{32}", value):
        raise ValueError("request_id debe ser un UUID hexadecimal de 32 caracteres")
    return value


def _paths(pid: str, request_id: str):
    project = studio.project_path(pid)
    folder = project / "artifacts" / "text_to_video"
    folder.resolve().relative_to(project.resolve())
    output_dir = project / "medios_generados"
    output_dir.resolve().relative_to(project.resolve())
    if folder.is_symlink() or output_dir.is_symlink():
        raise ValueError("No se permiten carpetas enlazadas para trabajos de vídeo")
    record = folder / f"{request_id}.json"
    claim = folder / f"{request_id}.claim"
    output = output_dir / f"wan-t2v-{request_id}.mp4"
    if record.is_symlink() or claim.is_symlink() or output.is_symlink():
        raise ValueError("No se permiten archivos enlazados en el trabajo")
    output.resolve().relative_to(project.resolve())
    return project, folder, record, claim, output


def _public(record: dict) -> dict:
    result = {key: record.get(key) for key in (
        "request_id", "project_id", "state", "profile", "prompt_chars",
        "created_at", "updated_at", "completed_at", "error", "prompt_id",
    )}
    if record.get("state") == "completed":
        result["video_url"] = f"/api/studio/editor/{record['project_id']}/text-to-video/requests/{record['request_id']}/video"
        result["bytes"] = record.get("bytes")
        result["model"] = record.get("model")
    return result


def _read_record(project: Path, record_path: Path) -> dict:
    try:
        value = studio.read_json(record_path)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Registro de generación ilegible; no se reenvía el trabajo") from exc
    if not isinstance(value, dict) or value.get("project_id") != project.name:
        raise ValueError("Registro de generación inválido")
    return value


def status(pid: str, request_id: str) -> dict:
    key = _request_id(request_id)
    project, _, record_path, claim, output = _paths(pid, key)
    with studio.LOCK:
        if not record_path.is_file():
            if claim.exists():
                return {"request_id": key, "project_id": pid, "state": "interrupted",
                        "error": "Hay una reserva sin recibo; consulta ComfyUI antes de reintentar."}
            raise FileNotFoundError("Trabajo de texto a vídeo no encontrado")
        record = _read_record(project, record_path)
        if record.get("request_id") != key:
            raise ValueError("El registro no corresponde al request_id")
        if record.get("state") in ("queued", "running") and (pid, key) not in ACTIVE:
            record.update(state="interrupted", updated_at=studio.now(),
                          error="Studio dejó de informar este trabajo; no se reenvía automáticamente.")
            studio.save_json(record_path, record)
        if record.get("state") == "completed":
            relative = record.get("relative_path")
            if relative != f"medios_generados/wan-t2v-{key}.mp4" or output.is_symlink() or not output.is_file():
                record.update(state="invalid", error="No se encontró el MP4 registrado dentro del proyecto.")
                studio.save_json(record_path, record)
            elif output.stat().st_size != record.get("bytes") or output.stat().st_size <= 0:
                record.update(state="invalid", error="El MP4 cambió desde que se completó el trabajo.")
                studio.save_json(record_path, record)
        return _public(record)


def video_path(pid: str, request_id: str) -> Path:
    value = status(pid, request_id)
    if value.get("state") != "completed":
        raise editor.Conflict("El vídeo no está completado")
    _, _, _, _, output = _paths(pid, request_id)
    return output


def completed_results(pid: str) -> list[dict]:
    """List only validated completed receipts for this project, excluding registered media."""
    project = studio.project_path(pid)
    current = editor.state(pid)
    registered = {
        source.get("path") for source in current.get("edit_decisions", {}).get("sources", {}).values()
    }
    folder = project / "artifacts" / "text_to_video"
    if folder.is_symlink():
        raise ValueError("No se permite una carpeta de recibos enlazada")
    if not folder.is_dir():
        return []
    results = []
    for record_path in sorted(folder.glob("*.json"), key=lambda item: item.name, reverse=True)[:200]:
        if record_path.is_symlink() or not re.fullmatch(r"[a-f0-9]{32}\.json", record_path.name):
            continue
        request_id = record_path.stem
        try:
            receipt = _read_record(project, record_path)
            if receipt.get("request_id") != request_id or receipt.get("project_id") != pid:
                continue
            result = status(pid, request_id)
        except (OSError, ValueError, FileNotFoundError):
            continue
        if result.get("state") != "completed":
            continue
        expected_relative = f"medios_generados/wan-t2v-{request_id}.mp4"
        if receipt.get("relative_path") != expected_relative or expected_relative in registered:
            continue
        results.append({
            "request_id": request_id,
            "label": "Vídeo generado · Wan 2.2",
            "model": result.get("model"),
            "bytes": result.get("bytes"),
            "completed_at": result.get("completed_at"),
            "video_url": result["video_url"],
        })
    return results


def add_to_timeline(pid: str, request_id: str, expected_revision: int) -> dict:
    """Resolve the media path from the validated receipt; accept no browser-supplied path."""
    result = status(pid, request_id)
    if result.get("state") != "completed":
        raise editor.Conflict("El recibo no tiene un MP4 completado válido")
    project, _, _, _, output = _paths(pid, request_id)
    relative = output.relative_to(project).as_posix()
    edit = editor.register_generated_and_add(pid, relative, expected_revision)
    return {"source_id": edit["source_id"], "clip_id": edit["clip_id"], "edit": edit}


def _preflight(tool):
    from lib.model_adapters import configuration
    from lib.wan_presets import config as wan_config
    from tools.video.comfyui_video import _REQUIRED_MODELS_T2V

    configured = configuration("wan")
    if configured.get("preset") != PROFILE:
        raise GenerationUnavailable("El perfil local Wan 2.2 T2V 14B de 4 pasos no está seleccionado")
    expected = wan_config(PROFILE)
    workflow_path = configured.get("workflow_path")
    if (not isinstance(workflow_path, str) or
            Path(workflow_path).resolve() != Path(expected["workflow_path"]).resolve() or
            configured.get("output_node") != expected["output_node"] or
            not Path(workflow_path).is_file()):
        raise GenerationUnavailable("El workflow Wan 2.2 T2V configurado no coincide con el perfil local o no está disponible")
    try:
        available = tool._client.is_available()
    except Exception as exc:
        raise GenerationUnavailable(f"No se pudo consultar ComfyUI local: {exc}") from exc
    if not available:
        raise GenerationUnavailable(tool._client.unavailable_reason())
    try:
        _, missing = tool._client.check_models(_REQUIRED_MODELS_T2V)
    except Exception as exc:
        raise GenerationUnavailable(f"ComfyUI respondió al estado, pero no se pudieron consultar los modelos: {exc}") from exc
    if missing:
        raise GenerationUnavailable("ComfyUI no informa estos modelos Wan T2V: " + ", ".join(missing))
    return str(Path(workflow_path).resolve())


def availability(pid: str, tool=None) -> dict:
    """Read-only, project-scoped readiness check; it never queues a ComfyUI prompt."""
    editor.state(pid)
    try:
        if tool is None:
            from tools.video.comfyui_video import ComfyUIVideo
            tool = ComfyUIVideo()
        workflow_path = _preflight(tool)
    except GenerationUnavailable as exc:
        return {"available": False, "profile": PROFILE, "reason": str(exc)}
    return {
        "available": True,
        "profile": PROFILE,
        "workflow": Path(workflow_path).name,
        "required_models": 6,
    }


def _run(pid: str, request_id: str, prompt: str, tool, record_path: Path, output: Path):
    key = (pid, request_id)
    try:
        with studio.LOCK:
            record = _read_record(studio.project_path(pid), record_path)
            record.update(state="running", updated_at=studio.now())
            studio.save_json(record_path, record)
        result = tool.execute({
            "operation": "text_to_video",
            "model_family": "wan2.2",
            "prompt": prompt,
            "output_path": str(output),
            "wan_workflow_path": record.get("workflow_path"),
        })
        data = getattr(result, "data", {}) or {}
        if not getattr(result, "success", False):
            prompt_id = data.get("prompt_id")
            state = "uncertain" if prompt_id else "failed"
            error = str(getattr(result, "error", None) or "ComfyUI no completó el trabajo")[:2000]
            with studio.LOCK:
                record = _read_record(studio.project_path(pid), record_path)
                record.update(state=state, updated_at=studio.now(), completed_at=studio.now(),
                              error=error, prompt_id=prompt_id)
                studio.save_json(record_path, record)
            return
        actual = Path(str(data.get("output") or "")).resolve()
        if actual != output.resolve() or output.is_symlink() or not output.is_file() or output.stat().st_size <= 0:
            raise ValueError("El adaptador no entregó el MP4 esperado dentro del proyecto")
        with studio.LOCK:
            record = _read_record(studio.project_path(pid), record_path)
            record.update(
                state="completed", updated_at=studio.now(), completed_at=studio.now(),
                relative_path=f"medios_generados/{output.name}", bytes=output.stat().st_size,
                model=data.get("model", "Wan 2.2 T2V local"),
                workflow_provenance=data.get("workflow_provenance"),
            )
            studio.save_json(record_path, record)
    except Exception as exc:
        with studio.LOCK:
            record = _read_record(studio.project_path(pid), record_path)
            prompt_id = getattr(exc, "prompt_id", None)
            record.update(state="uncertain" if prompt_id else "failed", updated_at=studio.now(),
                          completed_at=studio.now(), error=str(exc)[:2000], prompt_id=prompt_id)
            studio.save_json(record_path, record)
    finally:
        with studio.LOCK:
            ACTIVE.pop(key, None)
            claim = record_path.with_suffix(".claim")
            try:
                latest = _read_record(studio.project_path(pid), record_path)
                if latest.get("state") != "uncertain":
                    claim.unlink(missing_ok=True)
            except (OSError, ValueError):
                pass


def start(pid: str, data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Se requiere un objeto JSON")
    prompt = data.get("prompt")
    if not isinstance(prompt, str):
        raise ValueError("Escribe un prompt de texto para Wan")
    prompt = prompt.strip()
    if not prompt or len(prompt) > MAX_PROMPT_CHARS or "\x00" in prompt:
        raise ValueError(f"El prompt debe tener entre 1 y {MAX_PROMPT_CHARS} caracteres")
    if set(data) - {"prompt", "request_id"}:
        raise ValueError("La solicitud solo admite prompt y request_id")
    request_id = _request_id(data.get("request_id"))
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    project, folder, record_path, claim, output = _paths(pid, request_id)
    editor.state(pid)  # Require an editable project before any ComfyUI request.
    with studio.LOCK:
        if record_path.exists():
            record = _read_record(project, record_path)
            if record.get("prompt_sha256") != prompt_hash:
                raise editor.Conflict("request_id ya corresponde a otro prompt")
            return {**status(pid, request_id), "reused_request": True}
        if claim.exists():
            raise editor.Conflict("Este trabajo tiene una reserva previa; consulta su estado antes de reintentar")
        if output.exists():
            raise editor.Conflict("La ruta del MP4 ya existe; no se sobrescribe")

    from tools.video.comfyui_video import ComfyUIVideo
    tool = ComfyUIVideo()
    workflow_path = _preflight(tool)

    with editor.guard(pid):
        editor.state(pid)
        with studio.LOCK:
            if record_path.exists() or claim.exists() or output.exists():
                raise editor.Conflict("La solicitud o su salida cambió durante la validación")
            folder.mkdir(parents=True, exist_ok=True)
            output.parent.mkdir(parents=True, exist_ok=True)
            try:
                with claim.open("x", encoding="utf-8") as stream:
                    json.dump({"request_id": request_id, "project_id": pid}, stream)
            except FileExistsError as exc:
                raise editor.Conflict("Otra solicitud reservó este trabajo") from exc
            now = studio.now()
            record = {
                "request_id": request_id, "project_id": pid, "state": "queued",
                "profile": PROFILE, "prompt_sha256": prompt_hash, "prompt_chars": len(prompt),
                "workflow_path": workflow_path,
                "relative_path": f"medios_generados/{output.name}",
                "created_at": now, "updated_at": now,
            }
            studio.save_json(record_path, record)
            thread = threading.Thread(
                target=_run, args=(pid, request_id, prompt, tool, record_path, output),
                name=f"wan-t2v-{request_id[:8]}", daemon=True,
            )
            ACTIVE[(pid, request_id)] = thread
            try:
                thread.start()
            except Exception:
                ACTIVE.pop((pid, request_id), None)
                claim.unlink(missing_ok=True)
                record.update(state="failed", error="No se pudo iniciar el trabajador local", updated_at=studio.now())
                studio.save_json(record_path, record)
                raise
    return {**status(pid, request_id), "reused_request": False}
