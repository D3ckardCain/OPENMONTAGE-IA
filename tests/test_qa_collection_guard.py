"""Manual production QA must not run during automatic pytest collection."""
from pathlib import Path
from tests.conftest import pytest_ignore_collect


def test_manual_qa_requires_explicit_opt_in(monkeypatch):
    monkeypatch.delenv('OPENMONTAGE_MANUAL_QA', raising=False)
    root = Path(__file__).resolve().parent
    assert pytest_ignore_collect(root / 'qa/test_04_audio_mix.py', None)
    assert pytest_ignore_collect(root / 'qa/test_08_end_to_end.py', None)


def test_automatic_and_separately_gated_tests_remain_collectable(monkeypatch):
    monkeypatch.delenv('OPENMONTAGE_MANUAL_QA', raising=False)
    root = Path(__file__).resolve().parent
    assert not pytest_ignore_collect(root / 'qa/test_09_hyperframes_compose.py', None)
    assert not pytest_ignore_collect(root / 'tools/test_rhubarb_integration.py', None)


def test_explicit_opt_in_preserves_manual_workflow(monkeypatch):
    monkeypatch.setenv('OPENMONTAGE_MANUAL_QA', '1')
    root = Path(__file__).resolve().parent
    assert not pytest_ignore_collect(root / 'qa/test_04_audio_mix.py', None)
