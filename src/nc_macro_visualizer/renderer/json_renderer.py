from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from typing import Any

from nc_macro_visualizer.models import AnalysisResult, VariableSummary


def render_json(result: AnalysisResult) -> str:
    return json.dumps(to_jsonable(result), ensure_ascii=False, indent=2) + "\n"


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
