import pytest
from lib.config_model import OpenMontageConfig
from tools.cost_tracker import CostTracker, BudgetExceededError

@pytest.mark.parametrize("config", [OpenMontageConfig(), OpenMontageConfig.load()])
def test_local_default_rejects_paid_reservation_even_after_tool_approval(config):
    tracker = CostTracker(
        budget_total_usd=config.budget.total_usd, mode=config.budget.mode,
        require_approval_for_new_paid_tool=config.budget.require_approval_for_new_paid_tool)
    assert config.llm.provider == "ollama"
    tracker.approve_tool("paid-fixture")
    entry = tracker.estimate("paid-fixture", "fixture", 0.01)
    with pytest.raises(BudgetExceededError):
        tracker.reserve(entry)
    free = tracker.estimate("ffmpeg", "fixture", 0)
    tracker.reserve(free)
    assert tracker.budget_reserved_usd == 0
