"""Safe, uniform on-disk layout for local Studio projects."""
from __future__ import annotations

import re
import json
import unicodedata
from pathlib import Path


STANDARD_DIRS = (
    "datos",
    "originales",
    "medios_generados",
    "audio",
    "subtitulos",
    "miniaturas",
    "edicion",
    "cache",
    "exportaciones",
    # Existing engines still address these stable project-relative contracts.
    "artifacts",
    "assets/images",
    "assets/video",
    "assets/audio",
    "assets/music",
    "renders",
)


def folder_slug(title: str) -> str:
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Indica un nombre de proyecto")
    normalized = unicodedata.normalize("NFKD", title.strip())
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title).strip("-")
    if not slug:
        slug = "proyecto"
    return slug[:90].rstrip("-") or "proyecto"


def create_project_folder(root: Path, title: str) -> tuple[str, Path]:
    """Atomically reserve a readable, never-overwritten project directory.

    Existing names produce a safe numbered variant (``-2``, ``-3``, ...).
    ``mkdir(exist_ok=False)`` is the final collision check, including races
    with another Studio process.
    """
    root = Path(root).expanduser().resolve()
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ValueError(f"La carpeta raíz de proyectos no está disponible: {exc}") from exc
    if not root.is_dir():
        raise ValueError("La ruta raíz de proyectos no es una carpeta")
    base = folder_slug(title)
    for number in range(1, 10000):
        project_id = base if number == 1 else f"{base}-{number}"
        candidate = root / project_id
        try:
            candidate.mkdir(exist_ok=False)
        except FileExistsError:
            continue
        except OSError as exc:
            raise ValueError(f"No se pudo crear la carpeta del proyecto: {exc}") from exc
        return project_id, candidate
    raise ValueError("No se encontró un nombre de carpeta libre para el proyecto")


def initialize_layout(project: Path, project_id: str | None = None, title: str | None = None) -> None:
    project = Path(project).resolve()
    for relative in STANDARD_DIRS:
        target = project / relative
        target.resolve().relative_to(project)
        target.mkdir(parents=True, exist_ok=True)
    if project_id is not None and title is not None:
        manifest = project / "datos" / "workspace.json"
        record = {
            "schema_version": 1,
            "project_id": project_id,
            "title": title,
            "project_root": str(project.parent),
            "project_path": str(project),
            "directories": list(STANDARD_DIRS[:10]),
            "originals_policy": "copy_into_project; source_is_never_moved_or_deleted",
            "shared_models_policy": "models_remain_in_shared_application_locations",
        }
        with manifest.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2)
            stream.write("\n")


def describe(project: Path) -> dict:
    project = Path(project).resolve()
    return {
        "project_path": str(project),
        "directories": {name: str(project / name) for name in STANDARD_DIRS[:10]},
        "originals_policy": "copy_into_project; source_is_never_moved_or_deleted",
        "shared_models_policy": "models_remain_in_shared_application_locations",
    }

