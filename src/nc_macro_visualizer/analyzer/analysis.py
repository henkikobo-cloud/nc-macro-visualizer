from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from nc_macro_visualizer.models import (
    AnalysisWarning,
    AnalysisResult,
    FlowEdge,
    LabelHit,
    ParsedLine,
    VariableHit,
    VariableSummary,
)
from nc_macro_visualizer.parser import (
    find_calls,
    find_controls,
    find_loop_ends,
    find_m_codes,
    find_variable_dependencies,
    find_variables,
    parse_lines,
)


SUPPORTED_EXTENSIONS = {".nc", ".min", ".txt"}


def analyze_file(path: Path) -> AnalysisResult:
    return analyze_text(path.read_text(encoding="utf-8"), source_name=path.name)


def analyze_text(text: str, source_name: str = "<memory>") -> AnalysisResult:
    parsed_lines = parse_lines(text)
    executable_lines = [line for line in parsed_lines if is_program_line(line)]
    variables = [hit for line in executable_lines for hit in find_variables(line)]
    controls = [hit for line in executable_lines for hit in find_controls(line)]
    m_codes = [hit for line in executable_lines for hit in find_m_codes(line)]
    labels = [LabelHit(line.line_no, line.label, line.code) for line in executable_lines if line.label is not None]
    calls = [hit for line in executable_lines for hit in find_calls(line)]
    loop_ends = [hit for line in executable_lines for hit in find_loop_ends(line)]
    variable_dependencies = [hit for line in executable_lines for hit in find_variable_dependencies(line)]

    return AnalysisResult(
        source_name=source_name,
        line_count=len(parsed_lines),
        parsed_lines=parsed_lines,
        variables=variables,
        variable_summary=summarize_variables(variables),
        controls=controls,
        m_codes=m_codes,
        labels=labels,
        calls=calls,
        loop_ends=loop_ends,
        variable_dependencies=variable_dependencies,
        warnings=validate_program(source_name, labels, controls, loop_ends),
        flow_edges=build_flow_edges(executable_lines),
    )


def summarize_variables(variables: list[VariableHit]) -> list[VariableSummary]:
    assignments: dict[str, list[int]] = defaultdict(list)
    references: dict[str, list[int]] = defaultdict(list)

    for hit in variables:
        if hit.kind == "assignment":
            assignments[hit.name].append(hit.line_no)
        else:
            references[hit.name].append(hit.line_no)

    names = sorted(set(assignments) | set(references), key=variable_sort_key)
    return [VariableSummary(name, assignments[name], references[name]) for name in names]


def build_flow_edges(lines: list[ParsedLine]) -> list[FlowEdge]:
    if not lines:
        return []

    node_names = {line.line_no: node_name(line) for line in lines}
    edges = [FlowEdge("START", node_names[lines[0].line_no], "")]

    for index, line in enumerate(lines):
        next_line = lines[index + 1] if index + 1 < len(lines) else None
        controls = find_controls(line)
        loop_ends = find_loop_ends(line)
        if loop_ends:
            for loop_end in loop_ends:
                target = loop_start_node(loop_end.target, lines)
                if target is not None:
                    edges.append(FlowEdge(node_names[line.line_no], target, "END"))
            continue

        if not controls:
            if next_line is not None:
                edges.append(FlowEdge(node_names[line.line_no], node_names[next_line.line_no], "next"))
            continue

        for control in controls:
            if control.kind == "IF_GOTO" and control.target is not None:
                edges.append(FlowEdge(node_names[line.line_no], label_node(control.target), "YES"))
                if next_line is not None:
                    edges.append(FlowEdge(node_names[line.line_no], node_names[next_line.line_no], "NO"))
            elif control.kind == "GOTO" and control.target is not None:
                edges.append(FlowEdge(node_names[line.line_no], label_node(control.target), "GOTO"))
            elif control.kind in {"IF_THEN", "WHILE"}:
                if next_line is not None:
                    edges.append(FlowEdge(node_names[line.line_no], node_names[next_line.line_no], control.kind))

    edges.append(FlowEdge(node_names[lines[-1].line_no], "END", ""))
    return edges


def node_name(line: ParsedLine) -> str:
    if line.label is not None:
        return label_node(line.label)
    return f"L{line.line_no}"


def label_node(label: str) -> str:
    return f"N{label}"


def loop_start_node(target: str | None, lines: list[ParsedLine]) -> str | None:
    if target is None:
        return None
    for line in lines:
        for control in find_controls(line):
            if control.kind == "WHILE" and control.target == target:
                return node_name(line)
    return None


def validate_program(
    source_name: str,
    labels: list[LabelHit],
    controls,
    loop_ends,
) -> list[AnalysisWarning]:
    warnings: list[AnalysisWarning] = []
    suffix = Path(source_name).suffix.lower()
    if suffix and suffix not in SUPPORTED_EXTENSIONS and source_name != "<memory>":
        warnings.append(
            AnalysisWarning(
                line_no=None,
                code="unsupported_extension",
                message=f"Input extension '{suffix}' is outside the documented set: .nc, .min, .txt.",
            )
        )

    label_lines: dict[str, list[int]] = defaultdict(list)
    for label in labels:
        label_lines[label.label].append(label.line_no)

    for label, line_numbers in sorted(label_lines.items(), key=lambda item: int(item[0])):
        if len(line_numbers) > 1:
            warnings.append(
                AnalysisWarning(
                    line_no=line_numbers[0],
                    code="duplicate_label",
                    message=f"N{label} appears on multiple lines: {format_line_numbers(line_numbers)}.",
                )
            )

    label_names = set(label_lines)
    for control in controls:
        if control.kind in {"IF_GOTO", "GOTO"} and control.target is not None and control.target not in label_names:
            warnings.append(
                AnalysisWarning(
                    line_no=control.line_no,
                    code="unresolved_goto",
                    message=f"{control.kind} target N{control.target} does not exist in this file.",
                )
            )

    while_ids = {
        control.target
        for control in controls
        if control.kind == "WHILE" and control.target is not None
    }
    for loop_end in loop_ends:
        if loop_end.target is not None and loop_end.target not in while_ids:
            warnings.append(
                AnalysisWarning(
                    line_no=loop_end.line_no,
                    code="unmatched_loop_end",
                    message=f"END{loop_end.target} has no matching WHILE ... DO{loop_end.target}.",
                )
            )

    return warnings


def format_line_numbers(line_numbers: list[int]) -> str:
    return ", ".join(str(line_no) for line_no in line_numbers)


def variable_sort_key(name: str) -> tuple[int, str]:
    if name.startswith("#") and name[1:].isdigit():
        return (0, f"{int(name[1:]):08d}")
    return (1, name)


def is_program_line(line: ParsedLine) -> bool:
    if not line.code:
        return False
    upper_code = line.code.upper()
    return upper_code != "%" and not upper_code.startswith("O")
