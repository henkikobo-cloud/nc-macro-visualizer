from __future__ import annotations

from dataclasses import dataclass, field

from nc_macro_visualizer.flowchart.builder import PROGRAM_END_CODES, is_program_line, node_id, then_summary
from nc_macro_visualizer.flowchart.models import validate_kind
from nc_macro_visualizer.models import AnalysisResult, ParsedLine
from nc_macro_visualizer.parser import find_calls, find_controls, find_loop_ends, find_m_codes


CFG_SCHEMA_VERSION = "cfg/v0.3"

CFG_NODE_KINDS = {
    "entry",
    "exit",
    "basic_block",
    "decision",
    "call_site",
    "jump_source",
    "unresolved",
}

CFG_EDGE_KINDS = {
    "forward",
    "back",
    "branch_true",
    "branch_false",
    "call",
    "return",
    "jump",
}


@dataclass(frozen=True)
class ControlFlowGraph:
    schema_version: str
    source_name: str
    nodes: list["CFGNode"]
    edges: list["CFGEdge"]
    entry_node_id: str
    exit_node_ids: list[str]


@dataclass(frozen=True)
class CFGNode:
    id: str
    kind: str
    source_line_no: int | None
    source_label: str | None
    source_text: str | None
    statements: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        validate_kind(self.kind, CFG_NODE_KINDS, "CFGNode.kind")


@dataclass(frozen=True)
class CFGEdge:
    source: str
    target: str
    kind: str
    condition: str | None

    def __post_init__(self) -> None:
        validate_kind(self.kind, CFG_EDGE_KINDS, "CFGEdge.kind")


def build_cfg(result: AnalysisResult) -> ControlFlowGraph:
    lines = [line for line in result.parsed_lines if is_program_line(line)]
    nodes = [CFGNode("ENTRY", "entry", None, None, None, ["開始"])]
    nodes.extend(build_cfg_nodes(lines))
    nodes.append(CFGNode("EXIT", "exit", None, None, None, ["終了"]))

    edges = build_cfg_edges(lines)
    exit_ids = ["EXIT"]
    return ControlFlowGraph(
        schema_version=CFG_SCHEMA_VERSION,
        source_name=result.source_name,
        nodes=nodes,
        edges=edges,
        entry_node_id="ENTRY",
        exit_node_ids=exit_ids,
    )


def build_cfg_nodes(lines: list[ParsedLine]) -> list[CFGNode]:
    nodes: list[CFGNode] = []
    labels = {line.label for line in lines if line.label is not None}
    unresolved_targets: set[str] = set()

    for line in lines:
        nodes.append(
            CFGNode(
                id=node_id(line),
                kind=cfg_node_kind(line),
                source_line_no=line.line_no,
                source_label=line.label,
                source_text=line.code,
                statements=[line.code],
            )
        )
        if any(control.kind == "IF_THEN" for control in find_controls(line)):
            nodes.append(
                CFGNode(
                    id=f"{node_id(line)}_THEN",
                    kind="basic_block",
                    source_line_no=line.line_no,
                    source_label=line.label,
                    source_text=line.code,
                    statements=[then_summary(line)],
                )
            )
        for control in find_controls(line):
            if control.kind in {"IF_GOTO", "GOTO"} and control.target and control.target not in labels:
                unresolved_targets.add(control.target)

    for target in sorted(unresolved_targets, key=int):
        nodes.append(
            CFGNode(
                id=unresolved_node_id(target),
                kind="unresolved",
                source_line_no=None,
                source_label=target,
                source_text=None,
                statements=[f"N{target} は見つかりません"],
            )
        )
    return nodes


def build_cfg_edges(lines: list[ParsedLine]) -> list[CFGEdge]:
    if not lines:
        return [CFGEdge("ENTRY", "EXIT", "forward", None)]

    labels = {line.label: node_id(line) for line in lines if line.label is not None}
    edges = [CFGEdge("ENTRY", node_id(lines[0]), "forward", None)]

    for index, line in enumerate(lines):
        current = node_id(line)
        next_line = lines[index + 1] if index + 1 < len(lines) else None
        next_id = node_id(next_line) if next_line is not None else "EXIT"

        loop_ends = find_loop_ends(line)
        if loop_ends:
            for loop_end in loop_ends:
                target = loop_header_id(loop_end.target, lines)
                if target is not None:
                    edges.append(CFGEdge(current, target, "back", None))
                else:
                    edges.append(CFGEdge(current, next_id, "forward", None))
            continue

        if is_program_end(line):
            edges.append(CFGEdge(current, "EXIT", "forward", None))
            continue

        controls = find_controls(line)
        if not controls:
            for call in find_calls(line):
                edges.append(CFGEdge(current, next_id, "call", call.target))
            edges.append(CFGEdge(current, next_id, "forward", None))
            continue

        control = controls[0]
        if control.kind == "WHILE":
            edges.append(CFGEdge(current, next_id, "branch_true", control.condition))
            edges.append(CFGEdge(current, loop_exit_id(control.target, lines) or "EXIT", "branch_false", control.condition))
        elif control.kind == "IF_GOTO" and control.target is not None:
            edges.append(CFGEdge(current, next_id, "branch_false", control.condition))
            edges.append(CFGEdge(current, labels.get(control.target, unresolved_node_id(control.target)), "branch_true", control.condition))
        elif control.kind == "IF_THEN":
            then_id = f"{current}_THEN"
            edges.append(CFGEdge(current, then_id, "branch_true", control.condition))
            edges.append(CFGEdge(current, next_id, "branch_false", control.condition))
            edges.append(CFGEdge(then_id, next_id, "forward", None))
        elif control.kind == "GOTO" and control.target is not None:
            edges.append(CFGEdge(current, labels.get(control.target, unresolved_node_id(control.target)), "jump", None))

    return dedupe_cfg_edges(edges)


def cfg_node_kind(line: ParsedLine) -> str:
    controls = find_controls(line)
    if controls:
        if controls[0].kind == "GOTO":
            return "jump_source"
        return "decision"
    if find_calls(line):
        return "call_site"
    return "basic_block"


def is_program_end(line: ParsedLine) -> bool:
    return any(hit.code in PROGRAM_END_CODES for hit in find_m_codes(line))


def loop_header_id(target: str | None, lines: list[ParsedLine]) -> str | None:
    if target is None:
        return None
    for line in lines:
        for control in find_controls(line):
            if control.kind == "WHILE" and control.target == target:
                return node_id(line)
    return None


def loop_exit_id(target: str | None, lines: list[ParsedLine]) -> str | None:
    if target is None:
        return None
    for index, line in enumerate(lines):
        if any(loop_end.target == target for loop_end in find_loop_ends(line)):
            next_line = lines[index + 1] if index + 1 < len(lines) else None
            return node_id(next_line) if next_line is not None else "EXIT"
    return None


def unresolved_node_id(target: str) -> str:
    return f"N{target}_UNRESOLVED"


def dedupe_cfg_edges(edges: list[CFGEdge]) -> list[CFGEdge]:
    seen: set[tuple[str, str, str, str | None]] = set()
    result: list[CFGEdge] = []
    for edge in edges:
        key = (edge.source, edge.target, edge.kind, edge.condition)
        if key in seen:
            continue
        seen.add(key)
        result.append(edge)
    return result
