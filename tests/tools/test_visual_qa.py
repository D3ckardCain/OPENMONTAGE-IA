"""Non-destructive frame extraction contract for visual QA."""
from pathlib import Path
from types import SimpleNamespace

from tools.analysis.visual_qa import VisualQA


def test_review_preserves_existing_capture_without_running_ffmpeg(tmp_path, monkeypatch):
    source = tmp_path / "input.mp4"
    source.write_bytes(b"synthetic input fixture")
    output = tmp_path / "review"
    output.mkdir()
    existing = output / "frame_1_0s.jpg"
    existing.write_bytes(b"keep this prior capture")

    tool = VisualQA()
    monkeypatch.setattr(tool, "run_command", lambda command: (_ for _ in ()).throw(
        AssertionError("FFmpeg must not run for an existing target")))

    result = tool.execute({
        "operation": "review",
        "input_path": str(source),
        "timestamps": [1.0],
        "output_dir": str(output),
    })

    assert result.success is True
    assert result.data["frame_count"] == 0
    assert result.data["frames"][0]["overwritten"] is False
    assert "no se sobrescribió" in result.data["frames"][0]["error"]
    assert existing.read_bytes() == b"keep this prior capture"


def test_review_uses_no_overwrite_flag_and_unique_names_for_rounded_collisions(tmp_path, monkeypatch):
    source = tmp_path / "input.mp4"
    source.write_bytes(b"synthetic input fixture")
    output = tmp_path / "review"
    commands = []

    def run_command(command):
        commands.append(command)
        Path(command[-1]).write_bytes(b"synthetic frame fixture")
        return SimpleNamespace(stdout="", stderr="", returncode=0)

    tool = VisualQA()
    monkeypatch.setattr(tool, "run_command", run_command)
    result = tool.execute({
        "operation": "review",
        "input_path": str(source),
        "timestamps": [1.01, 1.04],
        "output_dir": str(output),
    })

    assert result.success is True
    assert result.data["frame_count"] == 2
    assert len({frame["path"] for frame in result.data["frames"]}) == 2
    assert len({command[-1] for command in commands}) == 2
    assert all("-n" in command and "-y" not in command for command in commands)
    assert all(Path(frame["path"]).read_bytes() == b"synthetic frame fixture"
               for frame in result.data["frames"])
