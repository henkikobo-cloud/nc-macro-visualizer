from __future__ import annotations

from nc_macro_visualizer.flowchart.models import StructuredBlock, StructuredProgram


def render_structured_text(program: StructuredProgram) -> str:
    lines = [f"# Structured View: {program.source_name}", ""]
    for block in program.blocks:
        lines.extend(render_block(block, depth=0))
    return "\n".join(lines).rstrip() + "\n"


def render_block(block: StructuredBlock, depth: int) -> list[str]:
    prefix = "  " * depth
    label = f"N{block.source_label}: " if block.source_label else ""
    lines = [f"{prefix}- {label}{block.title}"]
    if block.summary and block.summary != block.title:
        lines.append(f"{prefix}  {block.summary}")
    if block.note:
        lines.append(f"{prefix}  {block.note}")
    if block.source_text:
        lines.append(f"{prefix}  code: {block.source_text}")

    if block.children:
        lines.append(f"{prefix}  はい:")
        for child in block.children:
            lines.extend(render_block(child, depth + 2))
    if block.false_children:
        lines.append(f"{prefix}  いいえ:")
        for child in block.false_children:
            lines.extend(render_block(child, depth + 2))
    elif block.kind == "if":
        lines.append(f"{prefix}  いいえ: そのまま次へ")

    return lines
