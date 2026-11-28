"""Deterministic validation of agent-authored audio review evidence.
This module does not listen to audio or decide cultural suitability.
Overlapping segments are permitted for simultaneous tracks.
"""
import math
from schemas.artifacts import validate_artifact

def validate_cultural_audio(audit):
    validate_artifact("cultural_audio_audit", audit)
    duration = audit["duration_seconds"]
    if not math.isfinite(duration):
        raise ValueError("Non-finite duration")
    seen = set()
    coverage = 0.0
    for item in sorted(audit["segments"], key=lambda s: s["start"]):
        start, end = item["start"], item["end"]
        if not all(math.isfinite(t) for t in (start,end)) or not 0 <= start < end <= duration:
            raise ValueError("Invalid audio interval")
        if item["id"] in seen:
            raise ValueError("Duplicate segment ID")
        seen.add(item["id"])
        if start > coverage + 0.001:
            raise ValueError("Unreviewed audio gap")
        coverage = max(coverage,end)
        if item["kind"] == "unknown" or item["action"] == "review" or not item["resolved"]:
            raise ValueError("Unresolved audio review")
        if item["language"] == "unknown" and item["kind"] in {"speech","song","mixed"}:
            raise ValueError("Unresolved language")
        if item["action"] != "remove" and not item["rights_cleared"]:
            raise ValueError("Audio rights unresolved")
    if coverage < duration - 0.001:
        raise ValueError("Unreviewed audio tail")
