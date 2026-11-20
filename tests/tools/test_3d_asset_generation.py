"""Contracts for cloud mesh generation and Blender world rendering."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import jsonschema
import pytest

from tools.base_tool import ToolStatus
from tools.graphics import atlas_3d, fal_3d
from tools.graphics.atlas_3d import Atlas3D
from tools.graphics import blender_world
from tools.graphics.blender_world import BlenderWorld, first_missing_frame
from tools.graphics.fal_3d import Fal3D
from tools.tool_registry import ToolRegistry


def test_registry_discovers_separate_3d_capabilities():
    registry = ToolRegistry()
    registry.discover("tools")
    assert {tool.name for tool in registry.get_by_capability("3d_asset_generation")} >= {
        "atlas_3d", "fal_3d"
    }
    assert {tool.name for tool in registry.get_by_capability("3d_world_rendering")} >= {
        "blender_world"
    }


def test_atlas_cost_matrix_and_missing_key(monkeypatch, tmp_path):
    for key in ("ATLASCLOUD_API_KEY", "ATLAS_CLOUD_API_KEY", "ATLAS_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    tool = Atlas3D()
    assert tool.get_status() == ToolStatus.UNAVAILABLE
    assert tool.estimate_cost({"texture": False}) == 0.22
    assert tool.estimate_cost({"texture": True, "texture_quality": "standard"}) == 0.33
    assert tool.estimate_cost({"texture": True, "texture_quality": "detailed", "geometry_quality": "detailed"}) == 0.66
    result = tool.execute({"prompt": "a cottage", "output_path": str(tmp_path / "cottage.glb")})
    assert not result.success
    assert result.data["blocked_by"] == "zero_cost_policy"
    assert "ZERO_COST_POLICY" in result.error
    assert not (tmp_path / "cottage.glb").exists()


def test_fal_cost_matrix_and_input_validation(monkeypatch, tmp_path):
    monkeypatch.delenv("FAL_KEY", raising=False)
    monkeypatch.delenv("FAL_AI_API_KEY", raising=False)
    tool = Fal3D()
    assert tool.estimate_cost({"operation": "reconstruct_objects"}) == 0.02
    assert tool.estimate_cost({"operation": "image_to_3d", "enable_pbr": False}) == 0.225
    assert tool.estimate_cost({"operation": "image_to_3d", "enable_pbr": True}) == 0.375
    result = tool.execute({"operation": "text_to_3d", "output_path": str(tmp_path / "asset.glb")})
    assert not result.success


def test_blender_doctor_reports_detected_runtime(monkeypatch, tmp_path):
    executable = tmp_path / "blender"
    executable.write_bytes(b"")
    monkeypatch.setattr(blender_world, "find_blender", lambda: executable)
    monkeypatch.setattr(blender_world.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(
        args=args[0], returncode=0, stdout="OPENMONTAGE_BLENDER=4.5.10 LTS\n", stderr="",
    ))
    result = BlenderWorld().execute({"operation": "doctor"})
    assert result.success, result.error
    assert result.data["version_line"].startswith("OPENMONTAGE_BLENDER=4.5.10")


def test_blender_doctor_explains_missing_optional_runtime(monkeypatch):
    monkeypatch.setattr(blender_world, "find_blender", lambda: None)
    result = BlenderWorld().execute({"operation": "doctor"})
    assert not result.success
    assert "Blender not found" in (result.error or "")


def test_blender_resume_finds_first_missing_contiguous_frame(tmp_path):
    prefix = tmp_path / "frame-"
    for frame in (1, 2, 4):
        (tmp_path / f"frame-{frame:04d}.png").write_bytes(b"png")
    assert first_missing_frame(prefix, 1, 5) == 3
    (tmp_path / "frame-0003.png").write_bytes(b"png")
    assert first_missing_frame(prefix, 1, 4) is None


def test_asset_manifest_accepts_generated_mesh_type():
    schema = json.loads(Path("schemas/artifacts/asset_manifest.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate({
        "version": "1.0",
        "assets": [{
            "id": "hero-cottage",
            "type": "3d_asset",
            "path": "assets/3d/hero-cottage.glb",
            "source_tool": "atlas_3d",
            "scene_id": "village",
        }],
    }, schema)


@pytest.mark.parametrize("tool_cls,module,key", [
    (Atlas3D, atlas_3d, "ATLASCLOUD_API_KEY"),
    (Fal3D, fal_3d, "FAL_KEY"),
])
def test_cloud_mesh_credentials_never_enable_paid_generation(monkeypatch, tmp_path, tool_cls, module, key):
    monkeypatch.setenv(key, "dummy-test-key")

    def forbidden(*args, **kwargs):
        pytest.fail("Cloud mesh transport must not be reached under the zero-cost policy")

    monkeypatch.setattr(module.requests, "post", forbidden)
    monkeypatch.setattr(module.requests, "get", forbidden)
    output = tmp_path / "asset.glb"
    tool = tool_cls()
    assert tool.get_status() == ToolStatus.UNAVAILABLE
    result = tool.execute({
        "operation": "text_to_3d", "prompt": "a stone bridge", "output_path": str(output),
    })
    assert not result.success
    assert result.data["blocked_by"] == "zero_cost_policy"
    assert result.cost_usd == 0
    assert not output.exists()
    assert not output.with_suffix(".provenance.json").exists()
