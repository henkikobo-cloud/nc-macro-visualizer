from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from typing import Any

from nc_macro_visualizer.flowchart.cfg import ControlFlowGraph
from nc_macro_visualizer.flowchart.models import BeginnerFlow, StructuredTree
from nc_macro_visualizer.models import AnalysisResult, VariableSummary


def render_json(result: AnalysisResult) -> str:
    return json.dumps(to_jsonable(result), ensure_ascii=False, indent=2) + "\n"


def render_beginner_json(flow: BeginnerFlow) -> str:
    return json.dumps(to_beginner_jsonable(flow), ensure_ascii=False, indent=2) + "\n"


def render_cfg_json(cfg: ControlFlowGraph) -> str:
    return json.dumps(to_jsonable(cfg), ensure_ascii=False, indent=2) + "\n"


def render_structured_tree_json(tree: StructuredTree) -> str:
    return json.dumps(to_jsonable(tree), ensure_ascii=False, indent=2) + "\n"


def to_beginner_jsonable(flow: BeginnerFlow) -> dict[str, Any]:
    return {
        "schema_version": flow.schema_version,
        "source_name": flow.source_name,
        "nodes": to_jsonable(flow.nodes),
        "edges": to_jsonable(flow.edges),
        "warnings": to_jsonable(flow.warnings),
    }


def to_jsonable(value: Any) -> Any:
    if isinstance(value, VariableSummary):
        data = {
            "name": value.name,
            "assignments": value.assignments,
            "references": value.references,
        }
        data["count"] = value.count
        return data
    if is_dataclass(value):
        return {field.name: to_jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value
