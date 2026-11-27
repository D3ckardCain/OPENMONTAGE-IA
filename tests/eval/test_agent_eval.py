"""Offline tests for the agent-evaluation record contract; no model calls."""
import unittest
from pathlib import Path
from scripts.agent_eval import load_case_bank, summarize_records, validate_run_record

CASES = Path(__file__).with_name("agent_cases.json")


class AgentEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = load_case_bank(CASES)
        cls.cases = {case["id"]: case for case in cls.bank["cases"]}

    def record(self, case_id="available_tool_es", **extra):
        case = self.cases[case_id]
        value = {
            "schema_version": 1,
            "run_id": "synthetic-run-1",
            "case_id": case_id,
            "run_type": "synthetic_transport",
            "outcome": "blocked",
            "started_at": "2026-11-27T12:00:00Z",
            "model": None,
            "prompt_version": None,
            "checks": {name: True for name in case["expected_checks"]},
            "writes": [],
            "metrics": {"latency_ms": None, "prompt_tokens": None, "completion_tokens": None,
                        "ram_peak_mb": None, "vram_peak_mb": None},
            "redundant_call_count": 0,
        }
        value.update(extra)
        return value

    def test_case_bank_has_three_smokes_and_bilingual_held_out(self):
        self.assertEqual(len(self.bank["cases"]), 8)
        self.assertEqual(sum(c["phase"] == "smoke" for c in self.bank["cases"]), 3)
        self.assertEqual({c["language"] for c in self.bank["cases"]}, {"es", "en"})
        self.assertEqual(len(self.cases), 8)

    def test_real_model_pass_requires_model_runtime_quant_and_prompt_metadata(self):
        record = self.record(run_type="real_model", outcome="passed")
        self.assertIn("model metadata", " ".join(validate_run_record(record, self.cases)))
        record["model"] = {"name": "local-test", "quantization": "Q4", "runtime": "Ollama"}
        record["prompt_version"] = "synthetic-v1"
        self.assertEqual(validate_run_record(record, self.cases), [])

    def test_non_utc_timestamp_is_rejected(self):
        record = self.record(started_at="2026-11-27T12:00:00+03:00")
        self.assertIn("include a UTC timezone", " ".join(validate_run_record(record, self.cases)))

    def test_fixture_cannot_be_counted_as_real_model_pass(self):
        record = self.record(run_type="fixture", outcome="passed")
        self.assertIn("cannot be recorded as a real-model pass",
                      " ".join(validate_run_record(record, self.cases)))

    def test_required_verifiers_and_metric_types_are_checked(self):
        record = self.record()
        record["checks"] = {"one_dispatch": True}
        record["metrics"]["prompt_tokens"] = -1
        errors = " ".join(validate_run_record(record, self.cases))
        self.assertIn("missing expected checks", errors)
        self.assertIn("non-negative integer or null", errors)
        failed_pass = self.record(outcome="passed")
        failed_pass["checks"] = {name: False for name in self.cases["available_tool_es"]["expected_checks"]}
        self.assertIn("requires every expected check", " ".join(validate_run_record(failed_pass, self.cases)))

    def test_summary_separates_synthetic_and_detects_duplicate_effects(self):
        record = self.record(run_type="real_model", outcome="passed",
            model={"name": "local", "quantization": "Q4", "runtime": "Ollama"},
            prompt_version="prompt-a",
            metrics={"latency_ms": 250, "prompt_tokens": 12, "completion_tokens": 8,
                     "ram_peak_mb": 100, "vram_peak_mb": 200},
            writes=[{"idempotency_key": "edit-1", "effect_id": "effect-a"},
                    {"idempotency_key": "edit-1", "effect_id": "effect-b"}],
            redundant_call_count=1)
        other_run = dict(record, run_id="synthetic-run-2",
            writes=[{"idempotency_key": "edit-1", "effect_id": "effect-c"}])
        summary = summarize_records([record, other_run, self.record()])
        self.assertEqual(summary["real_model_passes"], 2)
        self.assertEqual(summary["synthetic_records"], 1)
        self.assertEqual(summary["measured_token_total"], 40)
        self.assertEqual(summary["duplicate_effects"], 1)
        self.assertEqual(summary["redundant_calls"], 2)
        self.assertEqual(summary["real_latency_ms"]["sample_size"], 2)


if __name__ == "__main__":
    unittest.main()
