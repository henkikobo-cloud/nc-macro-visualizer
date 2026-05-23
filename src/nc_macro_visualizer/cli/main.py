from __future__ import annotations

import argparse
from pathlib import Path

from nc_macro_visualizer.analyzer import analyze_file
from nc_macro_visualizer.flowchart import build_beginner_flow, build_cfg, structurize_beginner_flow, structurize_cfg
from nc_macro_visualizer.renderer import (
    render_beginner_json,
    render_cfg_json,
    render_json,
    render_markdown,
    render_mermaid,
    render_nassi_shneiderman,
    render_structured_text,
)
from nc_macro_visualizer.renderers import render_pad_html, render_pad_text


REPORT_FILE = "report.md"
JSON_FILE = "analysis.json"
MERMAID_FILE = "flow.mmd"
BEGINNER_FLOW_FILE = "beginner_flow.json"
NASSI_FILE = "nassi_shneiderman.html"
STRUCTURED_TEXT_FILE = "structured_text.md"
PAD_HTML_FILE = "pad.html"
PAD_TEXT_FILE = "pad.txt"
CFG_FILE = "cfg.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze FANUC-style NC macro files for human understanding.")
    parser.add_argument("input", type=Path, help="Input NC, MIN, or TXT file")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("output"), help="Output directory")
    parser.add_argument("--beginner", action="store_true", help="Also write beginner_flow.json for Web-first reading support")
    parser.add_argument("--nassi", action="store_true", help="Also write nassi_shneiderman.html")
    parser.add_argument("--text", action="store_true", help="Also write structured_text.md")
    parser.add_argument("--pad-html", action="store_true", help="Also write pad.html")
    parser.add_argument("--pad-text", action="store_true", help="Also write pad.txt")
    parser.add_argument("--cfg", action="store_true", help="Also write cfg.json")
    parser.add_argument("--all-views", action="store_true", help="Write all default, beginner, PAD, CFG, and structured outputs")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = analyze_file(args.input)
    write_outputs(result, args.output_dir)
    if args.beginner or args.all_views:
        write_beginner_output(result, args.output_dir)
    if args.nassi or args.text or args.all_views:
        write_structured_outputs(result, args.output_dir, write_nassi=args.nassi or args.all_views, write_text=args.text or args.all_views)
    if args.pad_html or args.pad_text or args.cfg or args.all_views:
        write_v030_outputs(
            result,
            args.output_dir,
            write_pad_html=args.pad_html or args.all_views,
            write_pad_text=args.pad_text or args.all_views,
            write_cfg=args.cfg or args.all_views,
        )
    return 0


def write_outputs(result, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / REPORT_FILE).write_text(render_markdown(result), encoding="utf-8")
    (output_dir / JSON_FILE).write_text(render_json(result), encoding="utf-8")
    (output_dir / MERMAID_FILE).write_text(render_mermaid(result), encoding="utf-8")


def write_beginner_output(result, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    flow = build_beginner_flow(result)
    (output_dir / BEGINNER_FLOW_FILE).write_text(render_beginner_json(flow), encoding="utf-8")


def write_structured_outputs(result, output_dir: Path, *, write_nassi: bool, write_text: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    flow = build_beginner_flow(result)
    program = structurize_beginner_flow(flow)
    if write_nassi:
        (output_dir / NASSI_FILE).write_text(render_nassi_shneiderman(program), encoding="utf-8")
    if write_text:
        (output_dir / STRUCTURED_TEXT_FILE).write_text(render_structured_text(program), encoding="utf-8")


def write_v030_outputs(result, output_dir: Path, *, write_pad_html: bool, write_pad_text: bool, write_cfg: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    cfg = build_cfg(result)
    tree = structurize_cfg(cfg)
    if write_pad_html:
        (output_dir / PAD_HTML_FILE).write_text(render_pad_html(tree), encoding="utf-8")
    if write_pad_text:
        (output_dir / PAD_TEXT_FILE).write_text(render_pad_text(tree), encoding="utf-8")
    if write_cfg:
        (output_dir / CFG_FILE).write_text(render_cfg_json(cfg), encoding="utf-8")
