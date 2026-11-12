"""Apply the fork policy to every disabled production adapter, not just fixtures.

No API payload is submitted. Availability, metadata, preflight and execution
must stop before a cost estimator, asset cache or HTTP transport is reached.
"""
import pytest
import requests

from tools.base_tool import ToolStatus, zero_cost_block_reason
from tools.tool_registry import ToolRegistry


def _blocked_adapters():
    catalog = ToolRegistry()
    catalog.discover("tools")
    return [catalog.get(name) for name in sorted(catalog.list_all())
            if zero_cost_block_reason(catalog.get(name)) is not None]


@pytest.mark.parametrize("tool", _blocked_adapters(), ids=lambda tool: tool.name)
def test_production_adapter_cannot_cross_zero_cost_boundary(tool, monkeypatch, tmp_path):
    def forbidden(*args, **kwargs):
        pytest.fail(f"Blocked adapter {tool.name} reached pricing, cache or transport")

    # Simulate installed credentials without depending on the user's real env.
    for dependency in tool.dependencies:
        if dependency.startswith("env:"):
            monkeypatch.setenv(dependency[4:], "dummy-test-key")
    monkeypatch.setenv("OPENMONTAGE_ASSET_CACHE", "1")
    monkeypatch.setattr(tool, "estimate_cost", forbidden)
    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)
    monkeypatch.setattr("lib.asset_cache.asset_cache_enabled", forbidden)

    assert tool.get_status() == ToolStatus.UNAVAILABLE
    info = tool.get_info()
    assert info["status"] == "unavailable"
    assert info["cost_policy_block_reason"]
    report = tool.dry_run({"prompt": "test"})
    assert report["would_execute"] is False
    assert report["cost_status"] == "blocked_by_policy"

    output = tmp_path / "not-generated.bin"
    result = tool.execute({"prompt": "test", "output_path": str(output), "seed": 1})
    assert not result.success
    assert result.data["blocked_by"] == "zero_cost_policy"
    assert result.cost_usd == 0
    assert result.from_cache is False
    assert not output.exists()
