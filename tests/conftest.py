"""Offline automated suite: no paid endpoints or external CLI telemetry.

The guard starts before collection. Manual QA scripts historically rendered
videos while being imported, before session fixtures could protect the runner.
Those scripts are retained for explicit manual execution, not pytest discovery.
"""
from __future__ import annotations
import pytest
from tests.offline_guard import OfflineTestGuard

collect_ignore_glob = ["qa/test_*.py"]
_guard = OfflineTestGuard()

def pytest_sessionstart(session):
    _guard.install()

def pytest_sessionfinish(session, exitstatus):
    _guard.restore()

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "live_api: live provider test; never enabled by the offline suite",
    )

def pytest_collection_modifyitems(config, items):
    skip = pytest.mark.skip(reason="Live provider calls are outside the zero-cost offline suite")
    for item in items:
        if "live_api" in item.keywords:
            item.add_marker(skip)
