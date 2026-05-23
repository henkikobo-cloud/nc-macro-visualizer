from __future__ import annotations

from nc_macro_visualizer.flowchart.models import StructuredNode, StructuredTree
from nc_macro_visualizer.flowchart.terminology import (
    PROGRAM_END_LABEL,
    PROGRAM_END_MARK,
    PROGRAM_START_LABEL,
    PROGRAM_START_MARK,
)
from nc_macro_visualizer.renderers.pad_html import natural_summary, sequence_label


def render_pad_text(tree: StructuredTree) -> str:
    lines: list[str] = [f"{PROGRAM_START_MARK} {PROGRAM_START_LABEL}"]
    for child in tree.root.children:
        lines.extend(render_node(child, depth=0))
    lines.append(f"{PROGRAM_END_MARK} {PROGRAM_END_LABEL}")
    return "\n".join(lines) + ("\n" if lines else "")


def render_node(node: StructuredNode, *, depth: int) -> list[str]:
    if node.kind == "sequence":
        lines: list[str] = []
        for child in node.children:
            lines.extend(render_node(child, depth=depth))
        return lines

    prefix = "  " * depth
    title = text_title(node)
    summary = "" if node.kind in {"if_then", "if_then_else", "while_loop"} else natural_summary(node)
    summary_text = f"  ({summary})" if summary else ""
    line = f"{prefix}{title}{summary_text}".rstrip()
    lines = [line]
    if node.note:
        lines.append(f"{prefix}  補足: {node.note}")
    for child in node.children:
        lines.extend(render_node(child, depth=depth + 1))
    return lines


def text_title(node: StructuredNode) -> str:
    label = sequence_label(node)
    title = node.title
    if node.kind in {"if_then", "if_then_else"}:
        condition = node.condition or node.summary or node.title
        title = f"もし {condition} なら"
    elif node.kind == "while_loop":
        condition = node.condition or node.summary or node.title
        title = f"{condition} の間くり返す"
    return f"{label}: {title}" if label else title
