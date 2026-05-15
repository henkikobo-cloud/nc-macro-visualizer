from __future__ import annotations

import re

from nc_macro_visualizer.models import AnalysisResult, ParsedLine
from nc_macro_visualizer.parser import find_calls, find_controls, find_loop_ends, find_m_codes


NODE_RE = re.compile(r"[^A-Za-z0-9_]")
IF_THEN_BODY_RE = re.compile(r"\bTHEN\b(?P<body>.*)", re.IGNORECASE)
PROGRAM_END_CODES = {"M30", "M99"}


def render_mermaid(result: AnalysisResult) -> str:
    lines = program_lines(result)
    if not lines:
        return "flowchart TD\n    START([\"START\"]) --> END([\"END\"])\n"

    label_nodes = {line.label: node_id(line) for line in lines if line.label is not None}
    loop_starts = loop_start_nodes(lines)
    loop_ends = loop_end_nodes(lines)
    node_defs: dict[str, str] = {
        "START": 'START(["START"])',
        "END": 'END(["END"])',
    }
    edges: list[str] = []

    for line in lines:
        node_defs[node_id(line)] = render_node(line)

    edges.append(f"START --> {node_id(lines[0])}")
    for index, line in enumerate(lines):
        next_line = lines[index + 1] if index + 1 < len(lines) else None
        current = node_id(line)

        if is_program_end(line):
            edges.append(f"{current} --> END")
            continue

        line_loop_ends = find_loop_ends(line)
        if line_loop_ends:
            for loop_end in line_loop_ends:
                target = loop_starts.get(loop_end.target)
                if target is not None:
                    edges.append(f"{current} -->|LOOP| {target}")
            continue

        calls = find_calls(line)
        for call in calls:
            if call.target is None:
                continue
            target = target_node(call.target, label_nodes, node_defs)
            edges.append(f"{current} -.->|CALL {call.kind}| {target}")

        controls = find_controls(line)
        if not controls:
            if next_line is not None:
                edges.append(f"{current} -->|next| {node_id(next_line)}")
            continue

        for control in controls:
            if control.kind == "IF_GOTO" and control.target is not None:
                target = target_node(control.target, label_nodes, node_defs)
                edges.append(f"{current} -->|YES| {target}")
                if next_line is not None:
                    edges.append(f"{current} -->|NO| {node_id(next_line)}")
            elif control.kind == "GOTO" and control.target is not None:
                target = target_node(control.target, label_nodes, node_defs)
                edges.append(f"{current} -->|GOTO| {target}")
            elif control.kind == "IF_THEN":
                then_node = f"{current}_THEN"
                node_defs[then_node] = render_then_node(then_node, line)
                edges.append(f"{current} -->|THEN| {then_node}")
                if next_line is not None:
                    edges.append(f"{then_node} --> {node_id(next_line)}")
                    edges.append(f"{current} -->|NO| {node_id(next_line)}")
            elif control.kind == "WHILE":
                if next_line is not None:
                    edges.append(f"{current} -->|DO| {node_id(next_line)}")
                loop_exit = loop_ends.get(control.target)
                if loop_exit is not None:
                    after_loop = next_program_line(lines, loop_exit)
                    if after_loop is not None:
                        edges.append(f"{current} -->|END| {node_id(after_loop)}")
                    else:
                        edges.append(f"{current} -->|END| END")

    mermaid = ["flowchart TD"]
    mermaid.extend(f"    {definition}" for definition in node_defs.values())
    mermaid.extend(f"    {edge}" for edge in dedupe(edges))
    return "\n".join(mermaid) + "\n"


def program_lines(result: AnalysisResult) -> list[ParsedLine]:
    return [line for line in result.parsed_lines if is_program_line(line)]


def is_program_line(line: ParsedLine) -> bool:
    if not line.code:
        return False
    upper_code = line.code.upper()
    return upper_code != "%" and not upper_code.startswith("O")


def node_id(line: ParsedLine) -> str:
    base = f"N{line.label}" if line.label is not None else f"L{line.line_no}"
    if is_program_end(line):
        return f"END_{base}"
    return sanitize_node(base)


def target_node(target: str, label_nodes: dict[str, str], node_defs: dict[str, str]) -> str:
    node = label_nodes.get(target)
    if node is not None:
        return node

    unresolved = sanitize_node(f"N{target}_UNRESOLVED")
    node_defs.setdefault(unresolved, f'{unresolved}["N{target}<br/>unresolved"]')
    return unresolved


def render_node(line: ParsedLine) -> str:
    current = node_id(line)
    label = node_label(line)
    controls = find_controls(line)
    calls = find_calls(line)

    if is_program_end(line):
        return f'{current}(["{escape_label(label)}<br/>END"])'
    if controls and controls[0].kind in {"IF_GOTO", "IF_THEN", "WHILE"}:
        return f'{current}{{"{escape_label(label)}"}}'
    if calls:
        call_text = ", ".join(format_call(call) for call in calls)
        return f'{current}[["{escape_label(label)}<br/>{escape_label(call_text)}"]]'
    return f'{current}["{escape_label(label)}"]'


def loop_start_nodes(lines: list[ParsedLine]) -> dict[str | None, str]:
    starts: dict[str | None, str] = {}
    for line in lines:
        for control in find_controls(line):
            if control.kind == "WHILE" and control.target is not None:
                starts[control.target] = node_id(line)
    return starts


def loop_end_nodes(lines: list[ParsedLine]) -> dict[str | None, ParsedLine]:
    ends: dict[str | None, ParsedLine] = {}
    for line in lines:
        for loop_end in find_loop_ends(line):
            if loop_end.target is not None:
                ends[loop_end.target] = line
    return ends


def next_program_line(lines: list[ParsedLine], current: ParsedLine) -> ParsedLine | None:
    for index, line in enumerate(lines):
        if line.line_no == current.line_no:
            return lines[index + 1] if index + 1 < len(lines) else None
    return None


def render_then_node(node: str, line: ParsedLine) -> str:
    match = IF_THEN_BODY_RE.search(line.code)
    body = match.group("body").strip() if match else "THEN"
    label = f"THEN {body}" if body else "THEN"
    return f'{node}["{escape_label(label)}"]'


def node_label(line: ParsedLine) -> str:
    return line.code


def format_call(call) -> str:
    if call.target is None:
        return f"CALL {call.kind}"
    return f"CALL {call.kind} P{call.target}"


def is_program_end(line: ParsedLine) -> bool:
    return any(hit.code in PROGRAM_END_CODES for hit in find_m_codes(line))


def sanitize_node(name: str) -> str:
    return NODE_RE.sub("_", name)


def escape_label(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', r"\"")


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
