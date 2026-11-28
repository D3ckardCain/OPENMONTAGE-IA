from pathlib import Path
import json

from lib.project_workspace import STANDARD_DIRS, create_project_folder, initialize_layout


def test_workspace_uses_readable_title_and_safe_collision_variant(tmp_path):
    root = tmp_path / "projects"
    root.mkdir()
    first_id, first = create_project_folder(root, "Video 1 para TikTok")
    second_id, second = create_project_folder(root, "Video 1 para TikTok")

    assert first_id == "video-1-para-tiktok"
    assert second_id == "video-1-para-tiktok-2"
    assert first != second
    assert first.is_dir() and second.is_dir()


def test_workspace_layout_is_uniform_and_confines_directories(tmp_path):
    root = tmp_path / "projects"
    root.mkdir()
    project_id, project = create_project_folder(root, "Edición local")
    initialize_layout(project, project_id, "Edición local")

    assert all((project / name).is_dir() for name in STANDARD_DIRS)
    assert all((project / name).resolve().is_relative_to(project.resolve()) for name in STANDARD_DIRS)
    manifest = json.loads((project / "datos" / "workspace.json").read_text(encoding="utf-8"))
    assert manifest["project_path"] == str(project.resolve())
    assert manifest["originals_policy"] == "copy_into_project; source_is_never_moved_or_deleted"


def test_workspace_creates_a_missing_local_root(tmp_path):
    root = tmp_path / "new" / "projects"
    project_id, project = create_project_folder(root, "Trabajo offline")

    assert root.is_dir()
    assert project_id == "trabajo-offline"
    assert project.is_dir()

