from __future__ import annotations

import re
from html import escape

from nc_macro_visualizer.flowchart.models import StructuredNode, StructuredTree
from nc_macro_visualizer.flowchart.terminology import (
    CONDITIONAL_SUMMARY,
    LOOP_SUMMARY,
    MACHINE_BEHAVIOR_DISCLAIMER,
    PROGRAM_END_LABEL,
    PROGRAM_END_MARK,
    PROGRAM_START_LABEL,
    PROGRAM_START_MARK,
    UNKNOWN_M_CODE_CONFIRMATION_SUMMARY,
)


def render_pad_html(tree: StructuredTree) -> str:
    body = render_sequence(tree.root.children, depth=0, root=True)
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="ja">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            f"  <title>PAD-Inspired View | {escape(tree.source_name)}</title>",
            '  <link rel="stylesheet" href="pad.css">',
            "</head>",
            "<body>",
            '  <main class="pad-page">',
            f'    <p class="pad-disclaimer">{escape(MACHINE_BEHAVIOR_DISCLAIMER)}</p>',
            f"    <h1>{escape(tree.source_name)}</h1>",
            body,
            "  </main>",
            "</body>",
            "</html>",
            "",
        ]
    )


def render_sequence(nodes: list[StructuredNode], *, depth: int, root: bool = False) -> str:
    classes = "pad-sequence pad-root" if root else "pad-sequence"
    lines = [f'<div class="{classes}" style="--depth: {depth}">']
    lines.append('  <div class="pad-sequence-line" aria-hidden="true"></div>')
    lines.append('  <div class="pad-sequence-items">')
    if nodes:
        if root:
            lines.append(indent(render_terminal_marker("start", depth=depth + 1), 4))
        for node in nodes:
            lines.append(indent(render_node(node, depth=depth + 1), 4))
        if root:
            lines.append(indent(render_terminal_marker("end", depth=depth + 1), 4))
    else:
        lines.append('    <div class="pad-empty"></div>')
    lines.append("  </div>")
    lines.append("</div>")
    return "\n".join(lines)


def render_node(node: StructuredNode, *, depth: int) -> str:
    if node.kind == "sequence":
        return render_sequence(node.children, depth=depth)
    if node.kind in {"if_then", "if_then_else"}:
        return render_selection(node, depth=depth)
    if node.kind == "while_loop":
        return render_loop(node, depth=depth)
    return render_terminal_or_process(node, depth=depth)


def render_terminal_or_process(node: StructuredNode, *, depth: int) -> str:
    class_name = node.kind.replace("_", "-")
    shape = "process"
    if node.kind == "call":
        shape = "call"
    classes = unique_classes(["pad-element", f"pad-{shape}", f"pad-{class_name}"])
    lines = [f'<div class="{classes}" style="--depth: {depth}">']
    lines.append('  <div class="pad-box">')
    lines.extend(render_content(node, title=node.title, indent_spaces=4))
    lines.append("  </div>")
    lines.append("</div>")
    return "\n".join(lines)


def render_terminal_marker(kind: str, *, depth: int) -> str:
    if kind == "start":
        mark = PROGRAM_START_MARK
        label = PROGRAM_START_LABEL
        class_name = "pad-start"
    else:
        mark = PROGRAM_END_MARK
        label = PROGRAM_END_LABEL
        class_name = "pad-program-end"
    return "\n".join(
        [
            f'<div class="pad-element pad-terminal {class_name}" style="--depth: {depth}">',
            '  <div class="pad-terminal-box">',
            f'    <span class="pad-terminal-mark">{escape(mark)}</span>',
            f'    <span class="pad-terminal-label">{escape(label)}</span>',
            "  </div>",
            "</div>",
        ]
    )


def render_selection(node: StructuredNode, *, depth: int) -> str:
    class_name = node.kind.replace("_", "-")
    true_children, false_children = selection_children(node)
    lines = [f'<div class="pad-element pad-selection pad-{class_name}" style="--depth: {depth}">']
    lines.append('  <div class="pad-selection-condition">')
    lines.append('    <div class="pad-box pad-condition-box">')
    lines.extend(render_content(node, title=selection_title(node), summary=CONDITIONAL_SUMMARY, indent_spaces=6))
    lines.append("    </div>")
    lines.append("  </div>")
    if node.kind == "if_then_else":
        lines.append('  <div class="pad-selection-branches">')
        lines.append('    <div class="pad-selection-then">')
        lines.append(indent(render_sequence(true_children, depth=depth + 1), 6))
        lines.append("    </div>")
        lines.append('    <div class="pad-selection-else">')
        lines.append('      <div class="pad-branch-divider">そうでなければ</div>')
        lines.append(indent(render_sequence(false_children, depth=depth + 1), 6))
        lines.append("    </div>")
        lines.append("  </div>")
    else:
        lines.append('  <div class="pad-selection-then">')
        lines.append(indent(render_sequence(true_children, depth=depth + 1), 4))
        lines.append("  </div>")
    lines.append("</div>")
    return "\n".join(lines)


def render_loop(node: StructuredNode, *, depth: int) -> str:
    lines = [f'<div class="pad-element pad-loop pad-while-loop" style="--depth: {depth}">']
    lines.append('  <div class="pad-while-condition">')
    lines.append('    <div class="pad-box pad-condition-box">')
    lines.extend(render_content(node, title=loop_title(node), summary=LOOP_SUMMARY, indent_spaces=6))
    lines.append("    </div>")
    lines.append("  </div>")
    lines.append('  <div class="pad-while-body">')
    lines.append(indent(render_sequence(node.children, depth=depth + 1), 4))
    lines.append("  </div>")
    lines.append("</div>")
    return "\n".join(lines)


def render_content(node: StructuredNode, *, title: str, indent_spaces: int, summary: str | None = None) -> list[str]:
    prefix = " " * indent_spaces
    lines = [
        f'{prefix}<div class="pad-box-header">',
        f'{prefix}  {render_title(node, title)}',
    ]
    line_trace = render_line_trace(node)
    if line_trace:
        lines.append(f"{prefix}  {line_trace}")
    lines.append(f"{prefix}</div>")
    display_summary = summary if summary is not None else natural_summary(node)
    if display_summary:
        lines.append(f'{prefix}<div class="pad-summary">{escape(display_summary)}</div>')
    if node.source_text:
        lines.append(f'{prefix}<div class="pad-source"><span>{escape(node.source_text)}</span></div>')
    if node.note:
        lines.append(f'{prefix}<div class="pad-note">{escape(node.note)}</div>')
    return lines


def render_title(node: StructuredNode, title: str) -> str:
    seq = sequence_label(node)
    if seq is None:
        return f'<div class="pad-title"><span class="pad-title-text">{escape(title)}</span></div>'
    line_class = " pad-seq-line" if node.source_label is None else ""
    return (
        '<div class="pad-title">'
        f'<span class="pad-seq-number{line_class}">{escape(seq)}</span>'
        '<span class="pad-title-separator">:</span>'
        f'<span class="pad-title-text">{escape(title)}</span>'
        "</div>"
    )


def sequence_label(node: StructuredNode) -> str | None:
    if node.source_label:
        return f"N{node.source_label}"
    if node.source_line_no is not None:
        return f"line {node.source_line_no}"
    return None


def render_line_trace(node: StructuredNode) -> str:
    if node.source_label and node.source_line_no is not None:
        return f'<div class="pad-line-trace">line {node.source_line_no}</div>'
    return ""


def selection_children(node: StructuredNode) -> tuple[list[StructuredNode], list[StructuredNode]]:
    if node.kind == "if_then_else" and len(node.children) >= 2:
        return node.children[0].children, node.children[1].children
    return node.children, []


def selection_title(node: StructuredNode) -> str:
    condition = node.condition or node.summary or node.title
    return f"もし {condition} なら"


def loop_title(node: StructuredNode) -> str:
    condition = node.condition or node.summary or node.title
    return f"{condition} の間くり返す"


def natural_summary(node: StructuredNode) -> str:
    if node.kind == "end":
        return ""
    if node.kind == "call":
        target = call_target(node.source_text or "")
        return f"別のプログラム P{target} を呼び出します" if target else "別のプログラムを呼び出します"
    if node.kind == "needs_confirmation":
        return UNKNOWN_M_CODE_CONFIRMATION_SUMMARY
    if node.kind == "machine_action":
        return "" if node.summary == node.source_text else node.summary

    assignment = assignment_summary(node.source_text or node.summary)
    if assignment:
        return assignment
    if node.summary and node.summary != node.source_text and node.summary != node.title:
        return node.summary
    return ""


ASSIGNMENT_RE = re.compile(r"(#(?:<[^>\s]+>|\d+))\s*=\s*(.+)$")
BINARY_RE = re.compile(r"^(#(?:<[^>\s]+>|\d+)|[-+]?\d+(?:\.\d+)?)\s*([+\-*/])\s*(#(?:<[^>\s]+>|\d+)|[-+]?\d+(?:\.\d+)?)$")


def assignment_summary(text: str | None) -> str:
    if not text:
        return ""
    match = ASSIGNMENT_RE.search(strip_label(text))
    if not match:
        return ""
    target = match.group(1)
    expression = match.group(2).strip()
    binary = BINARY_RE.match(expression)
    if binary:
        left, operator, right = binary.groups()
        if operator == "+":
            return f"{left} と {right} を足して {target} に入れます"
        if operator == "-":
            return f"{left} から {right} を引いて {target} に入れます"
        if operator == "*":
            return f"{left} と {right} をかけて {target} に入れます"
        if operator == "/":
            return f"{left} を {right} で割って {target} に入れます"
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", expression):
        return f"{target} に {expression} を入れます"
    if re.fullmatch(r"#(?:<[^>\s]+>|\d+)", expression):
        return f"{target} に {expression} の値を入れます"
    return f"{target} を計算して入れます"


def strip_label(text: str) -> str:
    return re.sub(r"^\s*N\s*\d+\s+", "", text, count=1, flags=re.IGNORECASE)


def call_target(text: str) -> str | None:
    match = re.search(r"\b[MG]\s*0*(?:98|65)\b.*?\bP\s*(\d+)", text, re.IGNORECASE)
    return match.group(1) if match else None


def indent(text: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line for line in text.splitlines())


def unique_classes(values: list[str]) -> str:
    seen: set[str] = set()
    classes: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        classes.append(value)
    return " ".join(classes)
