"""Deterministic ledger for the local-agent evaluation bank.

This module validates recorded runs; it never calls a model, a tool, or a renderer.
Synthetic/fixture runs are reported separately and cannot count as a real-model pass.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = 1
RUN_TYPES = {"real_model", "synthetic_transport", "fixture"}
OUTCOMES = {"passed", "failed", "blocked"}
METRICS = ("latency_ms", "prompt_tokens", "completion_tokens", "ram_peak_mb", "vram_peak_mb")


def load_case_bank(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("agent case bank schema_version must be 1")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("agent case bank must contain cases")
    ids = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("case must be an object")
        required = ("id", "language", "phase", "objective", "expected_checks")
        if any(not isinstance(case.get(key), str) or not case[key].strip() for key in required[:4]):
            raise ValueError("case requires non-empty id, language, phase, and objective")
        if case["language"] not in {"es", "en"} or case["phase"] not in {"smoke", "held_out"}:
            raise ValueError(f"invalid language/phase for case {case['id']}")
        if case["id"] in ids:
            raise ValueError(f"duplicate case id: {case['id']}")
        ids.add(case["id"])
        checks = case["expected_checks"]
        if not isinstance(checks, list) or not checks or any(not isinstance(x, str) or not x for x in checks):
            raise ValueError(f"case {case['id']} needs expected_checks")
    if sum(case["phase"] == "smoke" for case in cases) != 3:
        raise ValueError("initial bank must have exactly three smoke cases")
    if {case["language"] for case in cases} != {"es", "en"}:
        raise ValueError("initial bank must cover Spanish and English")
    return data


def validate_run_record(record: object, cases: dict) -> list[str]:
    errors = []
    if not isinstance(record, dict):
        return ["record must be an object"]
    required = ("schema_version", "run_id", "case_id", "run_type", "outcome", "started_at",
                "model", "prompt_version", "checks", "writes", "metrics")
    missing = [key for key in required if key not in record]
    if missing:
        return ["missing fields: " + ", ".join(missing)]
    if record["schema_version"] != SCHEMA_VERSION:
        errors.append("unsupported schema_version")
    if not isinstance(record["run_id"], str) or not record["run_id"].strip():
        errors.append("run_id must be non-empty")
    case = cases.get(record["case_id"])
    if case is None:
        errors.append("unknown case_id")
    if record["run_type"] not in RUN_TYPES:
        errors.append("invalid run_type")
    if record["outcome"] not in OUTCOMES:
        errors.append("invalid outcome")
    if record["outcome"] == "passed" and record["run_type"] != "real_model":
        errors.append("synthetic/fixture outcome cannot be recorded as a real-model pass")
    if not isinstance(record["started_at"], str):
        errors.append("started_at must be an ISO-8601 string")
    else:
        try:
            timestamp = datetime.fromisoformat(record["started_at"].replace("Z", "+00:00"))
            if timestamp.tzinfo is None or timestamp.utcoffset().total_seconds() != 0:
                errors.append("started_at must include a UTC timezone")
        except ValueError:
            errors.append("started_at must be an ISO-8601 timestamp in UTC")
    model = record["model"]
    if record["run_type"] == "real_model":
        if not isinstance(model, dict):
            errors.append("real_model requires model metadata")
        else:
            for key in ("name", "quantization", "runtime"):
                if not isinstance(model.get(key), str) or not model[key].strip():
                    errors.append(f"real_model requires model.{key}")
        if not isinstance(record["prompt_version"], str) or not record["prompt_version"].strip():
            errors.append("real_model requires prompt_version")
    checks = record["checks"]
    if not isinstance(checks, dict) or any(v is not None and type(v) is not bool for v in checks.values()):
        errors.append("checks must map check names to booleans or null when unmeasured")
    elif case:
        missing_checks = sorted(set(case["expected_checks"]) - set(checks))
        if missing_checks:
            errors.append("missing expected checks: " + ", ".join(missing_checks))
        elif record["outcome"] == "passed" and any(checks[name] is not True for name in case["expected_checks"]):
            errors.append("passed outcome requires every expected check to be true")
    writes = record["writes"]
    if not isinstance(writes, list):
        errors.append("writes must be a list")
    else:
        for index, write in enumerate(writes):
            if not isinstance(write, dict) or not isinstance(write.get("idempotency_key"), str):
                errors.append(f"writes[{index}] requires idempotency_key")
            elif write.get("effect_id") is not None and not isinstance(write.get("effect_id"), str):
                errors.append(f"writes[{index}].effect_id must be a string or null")
    metrics = record["metrics"]
    if not isinstance(metrics, dict):
        errors.append("metrics must be an object")
    else:
        for key in METRICS:
            value = metrics.get(key)
            if value is not None and (type(value) is not int or value < 0):
                errors.append(f"metrics.{key} must be a non-negative integer or null")
    redundant = record.get("redundant_call_count", 0)
    if type(redundant) is not int or redundant < 0:
        errors.append("redundant_call_count must be a non-negative integer")
    return errors


def summarize_records(records: list[dict]) -> dict:
    duplicate_effects = 0
    by_key = defaultdict(set)
    for record in records:
        for write in record.get("writes", []):
            key, effect = write.get("idempotency_key"), write.get("effect_id")
            if key and effect:
                by_key[(record.get("run_id"), key)].add(effect)
    duplicate_effects = sum(max(0, len(effects) - 1) for effects in by_key.values())
    real = [r for r in records if r.get("run_type") == "real_model"]
    latencies = [r["metrics"]["latency_ms"] for r in real
                 if isinstance(r.get("metrics"), dict) and type(r["metrics"].get("latency_ms")) is int]
    measured_tokens = sum((r["metrics"].get("prompt_tokens") or 0)
                          + (r["metrics"].get("completion_tokens") or 0) for r in real
                          if isinstance(r.get("metrics"), dict))
    return {
        "records": len(records),
        "real_model_passes": sum(r.get("run_type") == "real_model" and r.get("outcome") == "passed" for r in records),
        "synthetic_records": sum(r.get("run_type") != "real_model" for r in records),
        "failed": sum(r.get("outcome") == "failed" for r in records),
        "blocked": sum(r.get("outcome") == "blocked" for r in records),
        "measured_real_runs": len(real),
        "measured_token_total": measured_tokens,
        "real_latency_ms": {
            "sample_size": len(latencies),
            "p50": statistics.median(latencies) if latencies else None,
            "p95_nearest_rank": sorted(latencies)[max(0, math.ceil(.95 * len(latencies)) - 1)] if latencies else None,
        },
        "duplicate_effects": duplicate_effects,
        "redundant_calls": sum(r.get("redundant_call_count", 0) for r in records),
        "resource_peak_mb": {
            "ram": max((r["metrics"]["ram_peak_mb"] for r in real if r.get("metrics", {}).get("ram_peak_mb") is not None), default=None),
            "vram": max((r["metrics"]["vram_peak_mb"] for r in real if r.get("metrics", {}).get("vram_peak_mb") is not None), default=None),
        },
        "note": "Synthetic/fixture records are not real-model evidence; null metrics remain unmeasured.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path("tests/eval/agent_cases.json"))
    parser.add_argument("records", nargs="*", type=Path)
    args = parser.parse_args(argv)
    bank = load_case_bank(args.cases)
    case_map = {case["id"]: case for case in bank["cases"]}
    records = []
    seen_run_ids = set()
    for path in args.records:
        record = json.loads(path.read_text(encoding="utf-8"))
        errors = validate_run_record(record, case_map)
        if errors:
            print(json.dumps({"path": str(path), "errors": errors}, ensure_ascii=False), file=sys.stderr)
            return 2
        if record["run_id"] in seen_run_ids:
            print(json.dumps({"path": str(path), "errors": ["duplicate run_id"]}, ensure_ascii=False), file=sys.stderr)
            return 2
        seen_run_ids.add(record["run_id"])
        records.append(record)
    if not records:
        print(json.dumps({"cases": len(case_map), "smoke": sum(c["phase"] == "smoke" for c in case_map.values()),
                          "held_out": sum(c["phase"] == "held_out" for c in case_map.values()),
                          "runs": 0, "note": "No model runs were executed."}, ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(summarize_records(records), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
