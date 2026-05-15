from __future__ import annotations

from nc_macro_visualizer.models import (
    AnalysisResult,
    AnalysisWarning,
    CallHit,
    ControlHit,
    MCodeHit,
    VariableDependency,
    VariableHit,
    VariableSummary,
)


def render_markdown(result: AnalysisResult) -> str:
    lines = [
        f"# NC Macro Visualizer Report: {result.source_name}",
        "",
        "## Summary",
        "",
        f"- Lines: {result.line_count}",
        f"- Labels: {len(result.labels)}",
        f"- Variables: {len(result.variables)}",
        f"- IF/GOTO/WHILE/THEN: {len(result.controls)}",
        f"- M codes: {len(result.m_codes)}",
        f"- Calls: {len(result.calls)}",
        f"- Warnings: {len(result.warnings)}",
        "",
        "> This report is for understanding NC macro assets. It does not guarantee real machine behavior.",
        "",
    ]
    lines.extend(render_warnings(result.warnings))
    lines.extend(render_variable_summary(result.variable_summary))
    lines.extend(render_variable_dependencies(result.variable_dependencies))
    lines.extend(render_variables(result.variables))
    lines.extend(render_controls(result.controls))
    lines.extend(render_m_codes(result.m_codes))
    lines.extend(render_calls(result.calls))
    return "\n".join(lines).rstrip() + "\n"


def render_warnings(warnings: list[AnalysisWarning]) -> list[str]:
    lines = ["## Warnings", ""]
    if not warnings:
        return lines + ["No warnings found.", ""]

    lines.extend(["| Line | Code | Message |", "| ---: | --- | --- |"])
    for warning in warnings:
        line_no = str(warning.line_no) if warning.line_no is not None else "-"
        lines.append(f"| {line_no} | `{warning.code}` | {escape_table(warning.message)} |")
    lines.append("")
    return lines


def render_variable_summary(summaries: list[VariableSummary]) -> list[str]:
    lines = ["## Variable Summary", ""]
    if not summaries:
        return lines + ["No variables found.", ""]

    lines.extend(["| Variable | Count | Assignments | References |", "| --- | ---: | --- | --- |"])
    for item in summaries:
        lines.append(
            f"| `{item.name}` | {item.count} | {format_lines(item.assignments)} | {format_lines(item.references)} |"
        )
    lines.append("")
    return lines


def render_variable_dependencies(dependencies: list[VariableDependency]) -> list[str]:
    lines = ["## Variable Dependencies", ""]
    if not dependencies:
        return lines + ["No variable dependencies found.", ""]

    lines.extend(["| Line | Target | Sources | Code |", "| ---: | --- | --- | --- |"])
    for hit in dependencies:
        sources = ", ".join(f"`{source}`" for source in hit.sources)
        lines.append(f"| {hit.line_no} | `{hit.target}` | {sources} | `{escape_table(hit.text)}` |")
    lines.append("")
    return lines


def render_variables(variables: list[VariableHit]) -> list[str]:
    lines = ["## Variable Occurrences", ""]
    if not variables:
        return lines + ["No variables found.", ""]

    lines.extend(["| Line | Variable | Kind | Code |", "| ---: | --- | --- | --- |"])
    for hit in variables:
        lines.append(f"| {hit.line_no} | `{hit.name}` | {hit.kind} | `{escape_table(hit.text)}` |")
    lines.append("")
    return lines


def render_controls(controls: list[ControlHit]) -> list[str]:
    lines = ["## Flow Controls", ""]
    if not controls:
        return lines + ["No flow controls found.", ""]

    lines.extend(["| Line | Type | Target | Condition | Code |", "| ---: | --- | --- | --- | --- |"])
    for hit in controls:
        target = f"N{hit.target}" if hit.target else "-"
        condition = hit.condition if hit.condition else "-"
        lines.append(
            f"| {hit.line_no} | {hit.kind} | {target} | `{escape_table(condition)}` | `{escape_table(hit.text)}` |"
        )
    lines.append("")
    return lines


def render_m_codes(m_codes: list[MCodeHit]) -> list[str]:
    lines = ["## M Codes", ""]
    if not m_codes:
        return lines + ["No M codes found.", ""]

    lines.extend(["| Line | M Code | Description | Category | Code |", "| ---: | --- | --- | --- | --- |"])
    for hit in m_codes:
        lines.append(
            f"| {hit.line_no} | `{hit.code}` | {hit.description} | {hit.category} | `{escape_table(hit.text)}` |"
        )
    lines.append("")
    return lines


def render_calls(calls: list[CallHit]) -> list[str]:
    lines = ["## Subprogram / Macro Calls", ""]
    if not calls:
        return lines + ["No M98 or G65 calls found.", ""]

    lines.extend(["| Line | Type | Target | Code |", "| ---: | --- | --- | --- |"])
    for hit in calls:
        target = hit.target if hit.target else "undefined"
        lines.append(f"| {hit.line_no} | {hit.kind} | `{target}` | `{escape_table(hit.text)}` |")
    lines.append("")
    return lines


def format_lines(lines: list[int]) -> str:
    if not lines:
        return "-"
    return ", ".join(str(line) for line in lines)


def escape_table(value: str) -> str:
    return value.replace("|", r"\|")
