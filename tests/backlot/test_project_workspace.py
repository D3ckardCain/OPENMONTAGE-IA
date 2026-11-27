from pathlib import Path

import pytest

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
    _, project = create_project_folder(root, "Edición local")
    initialize_layout(project)

    assert all((project / name).is_dir() for name in STANDARD_DIRS)
    assert all((project / name).resolve().is_relative_to(project.resolve()) for name in STANDARD_DIRS)


def test_workspace_requires_existing_selected_root(tmp_path):
    with pytest.raises(ValueError, match="carpeta raíz"):
        create_project_folder(tmp_path / "missing", "Sin disco")

