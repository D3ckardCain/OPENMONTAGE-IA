"""Validation for opt-in, executable production-plan DAGs.

Legacy proposal packets remain readable. The DAG contract is activated only by
metadata.executable_plan_contract=studio-plan-dag-v1.
"""
from __future__ import annotations

import re

CONTRACT = "studio-plan-dag-v1"
_NODE_ID = re.compile(r"^[a-z][a-z0-9_.-]{0,79}$")


def validate_executable_plan(packet: dict) -> dict:
    """Validate explicit stage I/O, acceptance criteria, and acyclic dependencies."""
    metadata = packet.get("metadata") or {}
    contract = metadata.get("executable_plan_contract")
    if contract is None:
        return {"enabled": False, "order": []}
    if contract != CONTRACT:
        raise ValueError("Contrato de plan ejecutable desconocido")

    concepts = packet.get("concept_options") or []
    selected = (packet.get("selected_concept") or {}).get("concept_id")
    if selected not in {item.get("id") for item in concepts}:
        raise ValueError("El concepto seleccionado debe pertenecer a las propuestas")

    stages = (packet.get("production_plan") or {}).get("stages")
    if not isinstance(stages, list) or not 1 <= len(stages) <= 100:
        raise ValueError("Plan ejecutable limitado a 1–100 etapas")

    by_id = {}
    for stage in stages:
        node_id = stage.get("id")
        if not isinstance(node_id, str) or not _NODE_ID.fullmatch(node_id):
            raise ValueError("Cada etapa requiere un ID estable")
        if node_id in by_id:
            raise ValueError("ID de etapa duplicado: " + node_id)
        by_id[node_id] = stage
        for field in ("inputs", "outputs", "acceptance_criteria", "depends_on"):
            value = stage.get(field)
            if not isinstance(value, list):
                raise ValueError("La etapa " + node_id + " requiere " + field)
            if field != "depends_on" and any(not isinstance(x, str) or not x.strip() for x in value):
                raise ValueError(field + " contiene un valor vacío")
        if not stage["outputs"] or not stage["acceptance_criteria"]:
            raise ValueError("Cada etapa requiere salidas y criterios de aceptación")

    indegree = {node_id: 0 for node_id in by_id}
    children = {node_id: [] for node_id in by_id}
    for node_id, stage in by_id.items():
        deps = stage["depends_on"]
        if len(set(deps)) != len(deps):
            raise ValueError("Dependencias duplicadas en " + node_id)
        for dep in deps:
            if dep not in by_id:
                raise ValueError("Dependencia desconocida " + dep + " en " + node_id)
            if dep == node_id:
                raise ValueError("Una etapa no puede depender de sí misma: " + node_id)
            indegree[node_id] += 1
            children[dep].append(node_id)

    ready = [stage["id"] for stage in stages if indegree[stage["id"]] == 0]
    order = []
    while ready:
        node_id = ready.pop(0)
        order.append(node_id)
        for child in children[node_id]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if len(order) != len(stages):
        raise ValueError("El plan contiene una dependencia cíclica")
    return {"enabled": True, "contract": CONTRACT, "order": order}
