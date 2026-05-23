from __future__ import annotations

from html import escape

from nc_macro_visualizer.flowchart.models import StructuredBlock, StructuredProgram


def render_nassi_shneiderman(program: StructuredProgram) -> str:
    lines = [
        '<section class="ns-diagram" data-view="nassi-shneiderman">',
        f'  <h1>{escape(program.source_name)}</h1>',
        '  <div class="ns-stack">',
    ]
    for block in program.blocks:
        lines.extend(render_block(block, indent=2))
    lines.extend([
        "  </div>",
        "</section>",
        "",
    ])
    return "\n".join(lines)


def render_block(block: StructuredBlock, indent: int) -> list[str]:
    pad = "  " * indent
    classes = f"ns-block ns-{escape(block.kind)}"
    lines = [
        f'{pad}<div class="{classes}">',
        f'{pad}  <div class="ns-title">{escape(block.title)}</div>',
    ]
    if block.summary:
        lines.append(f'{pad}  <div class="ns-summary">{escape(block.summary)}</div>')
    if block.source_text:
        lines.append(f'{pad}  <div class="ns-source">{escape(block.source_text)}</div>')
    if block.note:
        lines.append(f'{pad}  <div class="ns-note">{escape(block.note)}</div>')

    if block.children or block.false_children:
        lines.append(f'{pad}  <div class="ns-branches">')
        lines.append(f'{pad}    <div class="ns-branch">')
        lines.append(f'{pad}      <div class="ns-branch-label">はい</div>')
        if block.children:
            for child in block.children:
                lines.extend(render_block(child, indent + 4))
        else:
            lines.append(f'{pad}      <div class="ns-empty">処理なし</div>')
        lines.append(f'{pad}    </div>')
        lines.append(f'{pad}    <div class="ns-branch">')
        lines.append(f'{pad}      <div class="ns-branch-label">いいえ</div>')
        if block.false_children:
            for child in block.false_children:
                lines.extend(render_block(child, indent + 4))
        else:
            lines.append(f'{pad}      <div class="ns-empty">そのまま次へ</div>')
        lines.append(f'{pad}    </div>')
        lines.append(f'{pad}  </div>')

    lines.append(f"{pad}</div>")
    return lines
