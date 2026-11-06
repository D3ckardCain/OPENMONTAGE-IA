"""No provider calls, model downloads, GPU, or third-party test runner needed."""
import os
import unittest
from unittest.mock import patch

from tools.base_tool import BaseTool, ToolResult, ToolRuntime, ToolStatus
from tools.tool_registry import ToolRegistry


class LocalTool(BaseTool):
    name = "local_fixture"

    def execute(self, inputs):
        return ToolResult(success=True, data={"ran": True})


class RemoteTool(LocalTool):
    name = "remote_fixture"
    runtime = ToolRuntime.API
    dependencies = ["env:TEST_PAID_API_KEY"]
    install_instructions = "Set TEST_PAID_API_KEY to enable the API."

    def get_status(self):
        raise AssertionError("Blocked providers must not probe their endpoint")

    def estimate_cost(self, inputs):
        raise AssertionError("Blocked providers must not request a price quote")

    def execute(self, inputs):
        raise AssertionError("Paid provider body was reached")


class ZeroCostPolicyTests(unittest.TestCase):
    def test_local_and_gpu_work(self):
        for runtime in (ToolRuntime.LOCAL, ToolRuntime.LOCAL_GPU):
            tool = LocalTool()
            tool.runtime = runtime
            self.assertTrue(tool.execute({}).success)

    def test_api_blocked_with_credentials_and_cache_enabled(self):
        with patch.dict(os.environ, {"TEST_PAID_API_KEY": "dummy", "OPENMONTAGE_ASSET_CACHE": "1"}):
            result = RemoteTool().execute({"output_path": "unused.wav", "seed": 1})
        self.assertFalse(result.success)
        self.assertEqual(result.data["blocked_by"], "zero_cost_policy")
        self.assertEqual(result.cost_usd, 0)

    def test_api_cannot_claim_free_estimate(self):
        tool = LocalTool()
        tool.runtime = ToolRuntime.API
        self.assertFalse(tool.execute({}).success)

    def test_hybrid_and_unknown_backends_blocked(self):
        for runtime in (ToolRuntime.HYBRID, "new_remote_backend", None):
            tool = LocalTool()
            tool.runtime = runtime
            self.assertFalse(tool.execute({}).success)

    def test_comfyui_blocked_even_when_local(self):
        tool = LocalTool()
        tool.provider = "comfyui"
        tool.runtime = ToolRuntime.LOCAL_GPU
        self.assertFalse(tool.execute({"model_family": "seedance_2.5"}).success)
        self.assertEqual(tool.get_status(), ToolStatus.UNAVAILABLE)

    def test_custom_and_inherited_status_blocked(self):
        self.assertEqual(RemoteTool().get_status(), ToolStatus.UNAVAILABLE)
        tool = LocalTool()
        tool.runtime = ToolRuntime.API
        self.assertEqual(tool.get_status(), ToolStatus.UNAVAILABLE)

    def test_blocked_dry_run_never_quotes(self):
        report = RemoteTool().dry_run({})
        self.assertFalse(report["would_execute"])
        self.assertEqual(report["cost_status"], "blocked_by_policy")

    def test_overridden_dry_run_cannot_probe_blocked_provider(self):
        class CustomRemote(RemoteTool):
            def dry_run(self, inputs):
                raise AssertionError("blocked custom preflight was called")

        report = CustomRemote().dry_run({})
        self.assertFalse(report["would_execute"])
        self.assertEqual(report["cost_status"], "blocked_by_policy")

    def test_overridden_info_cannot_probe_blocked_provider(self):
        class CustomRemote(RemoteTool):
            def get_info(self):
                raise AssertionError("blocked metadata probe was called")

        info = CustomRemote().get_info()
        self.assertEqual(info["status"], "unavailable")
        self.assertTrue(info["cost_policy_block_reason"])

    def test_local_custom_metadata_and_preflight_still_work(self):
        class CustomLocal(LocalTool):
            def get_info(self):
                return {**super().get_info(), "local_metadata": True}

            def dry_run(self, inputs):
                return {"local_preflight": True}

        self.assertTrue(CustomLocal().get_info()["local_metadata"])
        self.assertTrue(CustomLocal().dry_run({})["local_preflight"])

    def test_local_preflight_does_not_offer_positive_or_unknown_cost(self):
        for value in (0.01, -1, float("nan"), float("inf"), None, "0", True):
            with self.subTest(value=value):
                tool = LocalTool()
                tool.estimate_cost = lambda inputs: value
                self.assertFalse(tool.dry_run({})["would_execute"])

    def test_failed_local_estimate_does_not_crash_preflight(self):
        tool = LocalTool()
        tool.estimate_cost = lambda inputs: 1 / 0
        self.assertFalse(tool.dry_run({})["would_execute"])

    def test_unknown_runtime_is_inspectable_but_blocked(self):
        tool = LocalTool()
        tool.runtime = "unknown_backend"
        info = tool.get_info()
        self.assertEqual(info["runtime"], "unknown_backend")
        self.assertEqual(info["status"], "unavailable")

    def test_positive_invalid_and_unknown_costs_blocked(self):
        for value in (0.01, -1, float("nan"), float("inf"), None, "0", True):
            with self.subTest(value=value):
                tool = LocalTool()
                tool.estimate_cost = lambda inputs: value
                self.assertFalse(tool.execute({}).success)

    def test_failed_estimate_blocks_body(self):
        tool = LocalTool()
        tool.estimate_cost = lambda inputs: 1 / 0
        self.assertFalse(tool.execute({}).success)

    def test_policy_precedes_cache(self):
        tool = LocalTool()
        tool.estimate_cost = lambda inputs: 1
        with patch("lib.asset_cache.asset_cache_enabled", side_effect=AssertionError("cache reached")):
            self.assertFalse(tool.execute({}).success)

    def test_selector_nested_paid_calls_stay_blocked_on_retries(self):
        class Selector(LocalTool):
            runtime = ToolRuntime.HYBRID
            provider = "selector"

            def execute(self, inputs):
                for _ in range(2):
                    result = RemoteTool().execute(inputs)
                    if result.success:
                        return result
                return result

        self.assertFalse(Selector().execute({}).success)

    def test_selector_can_delegate_to_local_provider(self):
        class Selector(LocalTool):
            runtime = ToolRuntime.HYBRID
            provider = "selector"

            def execute(self, inputs):
                return LocalTool().execute(inputs)

        self.assertTrue(Selector().execute({}).success)

    def test_registry_excludes_paid_fallback_and_setup_offer(self):
        registry = ToolRegistry()
        registry._discovered_packages.add("tools")
        source = LocalTool()
        source.fallback_tools = ["remote_fixture"]
        registry.register(source)
        registry.register(RemoteTool())
        self.assertIsNone(registry.find_fallback(source.name))
        self.assertEqual(registry.get_available(), [source])
        menu = registry.provider_menu()["generic"]
        self.assertEqual(menu["configured"], 1)
        self.assertTrue(menu["unavailable"][0]["cost_policy_block_reason"])
        self.assertEqual(registry.provider_menu_summary()["setup_offers"], [])

    def test_budget_defaults_and_repository_config(self):
        from lib.config_model import BudgetConfig, BudgetMode, OpenMontageConfig
        for budget in (BudgetConfig(), OpenMontageConfig.load().budget):
            self.assertEqual(budget.mode, BudgetMode.CAP)
            self.assertEqual(budget.total_usd, 0)
            self.assertEqual(budget.single_action_approval_usd, 0)


if __name__ == "__main__":
    unittest.main()
