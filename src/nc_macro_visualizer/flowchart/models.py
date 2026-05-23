from __future__ import annotations

from dataclasses import dataclass, field

from nc_macro_visualizer.flowchart.terminology import SCHEMA_VERSION


NODE_KINDS = {
    "start",
    "end",
    "process",
    "decision",
    "call",
    "machine_action",
    "needs_confirmation",
    "warning",
    "jump_out",
    "jump_in",
}

EDGE_KINDS = {
    "sequential",
    "branch_true",
    "branch_false",
    "jump",
    "loop_body",
    "loop_exit",
    "call",
}

STRUCTURED_TREE_SCHEMA_VERSION = "structured-tree/v0.3"

STRUCTURED_NODE_KINDS = {
    "sequence",
    "process",
    "if_then",
    "if_then_else",
    "while_loop",
    "call",
    "machine_action",
    "needs_confirmation",
    "unstructured_jump",
    "end",
}


@dataclass(frozen=True)
class BeginnerFlow:
    source_name: str
    nodes: list[BeginnerNode] = field(default_factory=list)
    edges: list[BeginnerEdge] = field(default_factory=list)
    warnings: list[BeginnerWarning] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class BeginnerNode:
    id: str
    kind: str
    title: str
    summary: str
    source_line_no: int | None
    source_label: str | None
    source_text: str | None

    def __post_init__(self) -> None:
        validate_kind(self.kind, NODE_KINDS, "BeginnerNode.kind")


@dataclass(frozen=True)
class BeginnerEdge:
    source: str
    target: str
    label: str
    kind: str

    def __post_init__(self) -> None:
        validate_kind(self.kind, EDGE_KINDS, "BeginnerEdge.kind")


@dataclass(frozen=True)
class BeginnerWarning:
    source_line_no: int | None
    code: str
    message: str


@dataclass(frozen=True)
class StructuredProgram:
    source_name: str
    blocks: list[StructuredBlock] = field(default_factory=list)


@dataclass(frozen=True)
class StructuredBlock:
    kind: str
    title: str
    summary: str
    source_line_no: int | None = None
    source_label: str | None = None
    source_text: str | None = None
    children: list["StructuredBlock"] = field(default_factory=list)
    false_children: list["StructuredBlock"] = field(default_factory=list)
    note: str = ""


@dataclass(frozen=True)
class StructuredTree:
    source_name: str
    root: "StructuredNode"
    schema_version: str = STRUCTURED_TREE_SCHEMA_VERSION


@dataclass(frozen=True)
class StructuredNode:
    id: str
    kind: str
    title: str
    summary: str
    source_line_no: int | None
    source_label: str | None
    source_text: str | None
    children: list["StructuredNode"] = field(default_factory=list)
    condition: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        validate_kind(self.kind, STRUCTURED_NODE_KINDS, "StructuredNode.kind")


def validate_kind(value: str, allowed: set[str], field_name: str) -> None:
    if value not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise ValueError(f"{field_name} must be one of: {allowed_values}. Got: {value!r}.")
