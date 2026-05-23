from __future__ import annotations

import re
from dataclasses import dataclass

from nc_macro_visualizer.flowchart.models import (
    BeginnerEdge,
    BeginnerFlow,
    BeginnerNode,
    BeginnerWarning,
)
from nc_macro_visualizer.flowchart.terminology import (
    ASSIGNMENT_TITLE,
    CALCULATION_TITLE,
    CALL_TITLE,
    EDGE_LABELS,
    END_TITLE,
    GOTO_TITLE,
    IF_GOTO_TITLE,
    IF_THEN_TITLE,
    JUMP_IN_TITLE,
    MACHINE_ACTION_TITLE,
    PROCESS_TITLE,
    PROGRAM_END_TITLE,
    START_TITLE,
    UNKNOWN_M_CODE_MESSAGE,
    UNKNOWN_M_CODE_TITLE,
    WHILE_TITLE,
)
from nc_macro_visualizer.models import AnalysisResult, ParsedLine
from nc_macro_visualizer.parser import (
    find_calls,
    find_controls,
    find_loop_ends,
    find_m_codes,
    find_variable_dependencies,
)


PROGRAM_END_CODES = {"M30", "M99"}


@dataclass(frozen=True)
class JumpConnectorPair:
    source_line: ParsedLine
    target_line: ParsedLine
    target_label: str
    jump_out_id: str
    jump_in_id: str

    @property
    def source_line_no(self) -> int:
        return self.source_line.line_no

    @property
    def target_line_no(self) -> int:
        return self.target_line.line_no


def build_beginner_flow(result: AnalysisResult) -> BeginnerFlow:
    program_lines = [line for line in result.parsed_lines if is_program_line(line)]
    connector_pairs = build_connector_pairs(program_lines)
    nodes = [
        BeginnerNode("START", "start", START_TITLE, "確認を始めます", None, None, None),
    ]
    nodes.extend(build_nodes(program_lines, connector_pairs))
    nodes.append(BeginnerNode("END", "end", END_TITLE, "確認を終えます", None, None, None))

    warnings = [
        BeginnerWarning(warning.line_no, warning.code, warning.message)
        for warning in result.warnings
    ]
    warnings.extend(unknown_m_code_warnings(result))

    return BeginnerFlow(
        source_name=result.source_name,
        nodes=nodes,
        edges=build_edges(program_lines, connector_pairs),
        warnings=warnings,
    )


def build_nodes(lines: list[ParsedLine], connector_pairs: list[JumpConnectorPair]) -> list[BeginnerNode]:
    jump_in_by_target = group_connectors(connector_pairs, "target_line_no")
    jump_out_by_source = group_connectors(connector_pairs, "source_line_no")
    nodes: list[BeginnerNode] = []

    for line in lines:
        for pair in jump_in_by_target.get(line.line_no, []):
            nodes.append(
                BeginnerNode(
                    id=pair.jump_in_id,
                    kind="jump_in",
                    title=JUMP_IN_TITLE,
                    summary=f"{node_id(pair.source_line)} からの合流",
                    source_line_no=line.line_no,
                    source_label=line.label,
                    source_text=line.code,
                )
            )
        nodes.append(build_node(line))
        if has_if_then(line):
            nodes.append(build_then_node(line))
        for pair in jump_out_by_source.get(line.line_no, []):
            nodes.append(
                BeginnerNode(
                    id=pair.jump_out_id,
                    kind="jump_out",
                    title=GOTO_TITLE,
                    summary=f"{node_id(pair.target_line)} へジャンプします",
                    source_line_no=line.line_no,
                    source_label=line.label,
                    source_text=line.code,
                )
            )
    return nodes


def build_node(line: ParsedLine) -> BeginnerNode:
    return BeginnerNode(
        id=node_id(line),
        kind=node_kind(line),
        title=node_title(line),
        summary=node_summary(line),
        source_line_no=line.line_no,
        source_label=line.label,
        source_text=line.code,
    )


def build_then_node(line: ParsedLine) -> BeginnerNode:
    return BeginnerNode(
        id=then_node_id(line),
        kind="process",
        title=then_title(line),
        summary=then_summary(line),
        source_line_no=line.line_no,
        source_label=line.label,
        source_text=line.code,
    )


def build_edges(lines: list[ParsedLine], connector_pairs: list[JumpConnectorPair] | None = None) -> list[BeginnerEdge]:
    if not lines:
        return [BeginnerEdge("START", "END", EDGE_LABELS["sequential"], "sequential")]

    connector_pairs = connector_pairs or []
    connectors_by_jump = {(pair.source_line_no, pair.target_label): pair for pair in connector_pairs}
    node_ids = {line.line_no: node_id(line) for line in lines}
    label_nodes = {line.label: node_id(line) for line in lines if line.label is not None}
    edges = [BeginnerEdge("START", node_id(lines[0]), EDGE_LABELS["sequential"], "sequential")]

    for pair in connector_pairs:
        target = label_nodes.get(pair.target_label, unresolved_node_id(pair.target_label))
        edges.append(BeginnerEdge(pair.jump_in_id, target, "", "jump"))

    for index, line in enumerate(lines):
        current = node_id(line)
        next_line = lines[index + 1] if index + 1 < len(lines) else None

        if is_program_end(line):
            edges.append(BeginnerEdge(current, "END", EDGE_LABELS["sequential"], "sequential"))
            continue

        loop_ends = find_loop_ends(line)
        if loop_ends:
            for loop_end in loop_ends:
                target = loop_start_node(loop_end.target, lines)
                if target is not None:
                    edges.append(BeginnerEdge(current, target, EDGE_LABELS["loop_body"], "loop_body"))
            continue

        controls = find_controls(line)
        if not controls:
            if next_line is not None:
                edges.append(BeginnerEdge(current, node_ids[next_line.line_no], EDGE_LABELS["sequential"], "sequential"))
            else:
                edges.append(BeginnerEdge(current, "END", EDGE_LABELS["sequential"], "sequential"))
            continue

        for control in controls:
            if control.kind == "IF_GOTO" and control.target is not None:
                if next_line is not None:
                    edges.append(BeginnerEdge(current, node_ids[next_line.line_no], EDGE_LABELS["branch_false"], "branch_false"))
                connector = connectors_by_jump.get((line.line_no, control.target))
                target = connector.jump_out_id if connector is not None else label_nodes.get(control.target, unresolved_node_id(control.target))
                edges.append(BeginnerEdge(current, target, EDGE_LABELS["branch_true"], "branch_true"))
            elif control.kind == "GOTO" and control.target is not None:
                connector = connectors_by_jump.get((line.line_no, control.target))
                target = connector.jump_out_id if connector is not None else label_nodes.get(control.target, unresolved_node_id(control.target))
                edges.append(BeginnerEdge(current, target, EDGE_LABELS["jump"], "jump"))
            elif control.kind == "IF_THEN":
                if next_line is not None:
                    edges.append(BeginnerEdge(current, node_ids[next_line.line_no], EDGE_LABELS["branch_false"], "branch_false"))
                    then_node = then_node_id(line)
                    edges.append(BeginnerEdge(current, then_node, EDGE_LABELS["branch_true"], "branch_true"))
                    edges.append(BeginnerEdge(then_node, node_ids[next_line.line_no], EDGE_LABELS["sequential"], "sequential"))
            elif control.kind == "WHILE":
                if next_line is not None:
                    edges.append(BeginnerEdge(current, node_ids[next_line.line_no], EDGE_LABELS["loop_body"], "loop_body"))
                exit_target = loop_exit_node(control.target, lines)
                edges.append(BeginnerEdge(current, exit_target or "END", EDGE_LABELS["loop_exit"], "loop_exit"))

    return consolidate_merge_labels(dedupe_edges(edges))


def node_kind(line: ParsedLine) -> str:
    controls = find_controls(line)
    if controls:
        if controls[0].kind in {"IF_GOTO", "IF_THEN", "WHILE"}:
            return "decision"
        return "process"

    if find_calls(line):
        return "call"

    m_codes = find_m_codes(line)
    if any(hit.description == "unknown" for hit in m_codes):
        return "needs_confirmation"
    if m_codes:
        return "machine_action"

    return "process"


def node_title(line: ParsedLine) -> str:
    controls = find_controls(line)
    if controls:
        kind = controls[0].kind
        if kind == "IF_GOTO":
            return IF_GOTO_TITLE
        if kind == "IF_THEN":
            return IF_THEN_TITLE
        if kind == "GOTO":
            return GOTO_TITLE
        if kind == "WHILE":
            return WHILE_TITLE

    if find_calls(line):
        return CALL_TITLE

    m_codes = find_m_codes(line)
    if any(hit.description == "unknown" for hit in m_codes):
        return UNKNOWN_M_CODE_TITLE
    if any(hit.code in PROGRAM_END_CODES for hit in m_codes):
        return PROGRAM_END_TITLE
    if m_codes:
        return MACHINE_ACTION_TITLE

    dependencies = find_variable_dependencies(line)
    if dependencies:
        return CALCULATION_TITLE
    if "=" in line.code:
        return ASSIGNMENT_TITLE
    return PROCESS_TITLE


def node_summary(line: ParsedLine) -> str:
    title = node_title(line)
    if title == UNKNOWN_M_CODE_TITLE:
        return UNKNOWN_M_CODE_MESSAGE
    return title


def then_summary(line: ParsedLine) -> str:
    parts = re.split(r"\bTHEN\b", line.code, maxsplit=1, flags=re.IGNORECASE)
    return parts[1].strip() if len(parts) == 2 and parts[1].strip() else IF_THEN_TITLE


def then_title(line: ParsedLine) -> str:
    summary = then_summary(line)
    if "=" not in summary:
        return IF_THEN_TITLE
    return CALCULATION_TITLE if re.search(r"#(?:<[^>\s]+>|\d+)", summary.split("=", 1)[1]) else ASSIGNMENT_TITLE


def unknown_m_code_warnings(result: AnalysisResult) -> list[BeginnerWarning]:
    return [
        BeginnerWarning(
            source_line_no=hit.line_no,
            code="machine_specific_m_code",
            message=f"{hit.code} は{UNKNOWN_M_CODE_TITLE}です。{UNKNOWN_M_CODE_MESSAGE}",
        )
        for hit in result.m_codes
        if hit.description == "unknown"
    ]


def build_connector_pairs(lines: list[ParsedLine]) -> list[JumpConnectorPair]:
    line_indexes = {line.line_no: index for index, line in enumerate(lines)}
    labels = {line.label: line for line in lines if line.label is not None}
    pairs: list[JumpConnectorPair] = []

    for line in lines:
        source_index = line_indexes[line.line_no]
        for control in find_controls(line):
            if control.kind not in {"IF_GOTO", "GOTO"} or control.target is None:
                continue
            target_line = labels.get(control.target)
            if target_line is None:
                continue
            target_index = line_indexes[target_line.line_no]
            if not is_long_distance_jump(source_index, target_index):
                continue
            pairs.append(
                JumpConnectorPair(
                    source_line=line,
                    target_line=target_line,
                    target_label=control.target,
                    jump_out_id=f"{node_id(line)}_JUMP_OUT_{node_id(target_line)}",
                    jump_in_id=f"{node_id(target_line)}_JUMP_IN_FROM_{node_id(line)}",
                )
            )
    return pairs


def is_long_distance_jump(source_index: int, target_index: int) -> bool:
    crossed_siblings = abs(target_index - source_index) - 1
    return crossed_siblings > 2


def group_connectors(pairs: list[JumpConnectorPair], key: str) -> dict[int, list[JumpConnectorPair]]:
    grouped: dict[int, list[JumpConnectorPair]] = {}
    for pair in pairs:
        grouped.setdefault(getattr(pair, key), []).append(pair)
    return grouped


def node_id(line: ParsedLine) -> str:
    if line.label is not None:
        return f"N{line.label}"
    return f"L{line.line_no}"


def then_node_id(line: ParsedLine) -> str:
    return f"{node_id(line)}_THEN"


def has_if_then(line: ParsedLine) -> bool:
    return any(control.kind == "IF_THEN" for control in find_controls(line))


def unresolved_node_id(target: str) -> str:
    return f"N{target}_UNRESOLVED"


def loop_start_node(target: str | None, lines: list[ParsedLine]) -> str | None:
    if target is None:
        return None
    for line in lines:
        for control in find_controls(line):
            if control.kind == "WHILE" and control.target == target:
                return node_id(line)
    return None


def loop_exit_node(target: str | None, lines: list[ParsedLine]) -> str | None:
    if target is None:
        return None
    for index, line in enumerate(lines):
        for loop_end in find_loop_ends(line):
            if loop_end.target == target:
                next_line = lines[index + 1] if index + 1 < len(lines) else None
                return node_id(next_line) if next_line is not None else "END"
    return None


def is_program_line(line: ParsedLine) -> bool:
    if not line.code:
        return False
    upper_code = line.code.upper()
    return upper_code != "%" and not upper_code.startswith("O")


def is_program_end(line: ParsedLine) -> bool:
    return any(hit.code in PROGRAM_END_CODES for hit in find_m_codes(line))


def dedupe_edges(edges: list[BeginnerEdge]) -> list[BeginnerEdge]:
    seen: set[tuple[str, str, str, str]] = set()
    result: list[BeginnerEdge] = []
    for edge in edges:
        key = (edge.source, edge.target, edge.label, edge.kind)
        if key in seen:
            continue
        seen.add(key)
        result.append(edge)
    return result


def consolidate_merge_labels(edges: list[BeginnerEdge]) -> list[BeginnerEdge]:
    incoming: dict[str, list[int]] = {}
    for index, edge in enumerate(edges):
        incoming.setdefault(edge.target, []).append(index)

    result = list(edges)
    for indexes in incoming.values():
        if len(indexes) < 2:
            continue
        keep_index = choose_labeled_merge_edge(result, indexes)
        for index in indexes:
            if index == keep_index or not result[index].label:
                continue
            edge = result[index]
            result[index] = BeginnerEdge(edge.source, edge.target, "", edge.kind)
    return result


def choose_labeled_merge_edge(edges: list[BeginnerEdge], indexes: list[int]) -> int:
    for preferred_kind in ("branch_false", "branch_true", "sequential"):
        for index in indexes:
            if edges[index].kind == preferred_kind and edges[index].label:
                return index
    for index in indexes:
        if edges[index].label:
            return index
    return indexes[0]
