"""Synthetic validation of the opt-in proposal-plan DAG; no tools or media run."""
from copy import deepcopy

import pytest

from lib import production_plan
from lib import production_agent as agent
from lib import production_studio as studio


def stage(node_id, depends_on=()):
    return {
        "id": node_id,
        "stage": node_id,
        "tools": [],
        "approach": "Synthetic stage",
        "depends_on": list(depends_on),
        "inputs": [],
        "outputs": [node_id + "_artifact"],
        "acceptance_criteria": ["Synthetic criterion"],
    }


def packet():
    return {
        "version": "1.0",
        "concept_options": [
            {"id": "c1", "title": "A", "hook": "h", "narrative_structure": "story",
             "visual_approach": "visual A", "target_duration_seconds": 15, "why_this_works": "fixture"},
            {"id": "c2", "title": "B", "hook": "h", "narrative_structure": "tutorial",
             "visual_approach": "visual B", "target_duration_seconds": 15, "why_this_works": "fixture"},
            {"id": "c3", "title": "C", "hook": "h", "narrative_structure": "timeline",
             "visual_approach": "visual C", "target_duration_seconds": 15, "why_this_works": "fixture"},
        ],
        "selected_concept": {"concept_id": "c1", "rationale": "Synthetic selection"},
        "production_plan": {
            "pipeline": "animated-explainer",
            "render_runtime": "local",
            "stages": [stage("script"), stage("edit", ["script"])],
        },
        "cost_estimate": {"total_estimated_usd": 0, "line_items": [], "budget_verdict": "within_budget"},
        "approval": {"status": "pending"},
        "metadata": {"executable_plan_contract": production_plan.CONTRACT},
    }


def test_legacy_proposal_packet_does_not_require_new_dag_fields():
    value = packet()
    value.pop("metadata")
    for item in value["production_plan"]["stages"]:
        for field in ("id", "depends_on", "inputs", "outputs", "acceptance_criteria"):
            item.pop(field, None)
    assert production_plan.validate_executable_plan(value) == {"enabled": False, "order": []}


def test_executable_dag_returns_dependency_order():
    value = packet()
    value["production_plan"]["stages"] = [stage("export", ["edit"]), stage("script"), stage("edit", ["script"])]
    result = production_plan.validate_executable_plan(value)
    assert result["enabled"] is True
    assert result["order"].index("script") < result["order"].index("edit") < result["order"].index("export")


@pytest.mark.parametrize("stages,message", [
    ([stage("script", ["missing"])], "Dependencia desconocida"),
    ([stage("script", ["script"])], "no puede depender de sí misma"),
    ([stage("script", ["edit"]), stage("edit", ["script"])], "cíclica"),
    ([stage("script"), stage("script")], "duplicado"),
])
def test_invalid_dag_is_rejected(stages, message):
    value = packet()
    value["production_plan"]["stages"] = stages
    with pytest.raises(ValueError, match=message):
        production_plan.validate_executable_plan(value)


def test_agent_persists_only_valid_executable_proposal(tmp_path, monkeypatch):
    monkeypatch.setattr(studio, "PROJECTS_DIR", tmp_path / "projects")
    monkeypatch.setattr(studio, "CONFIG_DIR", tmp_path / "config")
    created = studio.create_production({
        "title": "Synthetic proposal contract", "brief": "Fixture only",
        "pipeline": "animated-explainer", "language": "es", "automatic": False,
    })
    worker = agent.LocalAgent(created["project_id"])
    valid = packet()
    result = worker.dispatch("write_artifact", {"name": "proposal_packet", "data": valid})
    saved = studio.read_json(worker.artifact_path("proposal_packet"))
    assert result["saved"]
    assert saved == valid

    invalid = deepcopy(valid)
    invalid["production_plan"]["stages"][0]["depends_on"] = ["edit"]
    with pytest.raises(ValueError, match="cíclica"):
        worker.dispatch("write_artifact", {"name": "proposal_packet", "data": invalid})
    assert studio.read_json(worker.artifact_path("proposal_packet")) == valid
