from __future__ import annotations

import argparse
from pathlib import Path

from nc_macro_visualizer.analyzer import analyze_file
from nc_macro_visualizer.renderer import render_json, render_markdown, render_mermaid


REPORT_FILE = "report.md"
JSON_FILE = "analysis.json"
MERMAID_FILE = "flow.mmd"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze FANUC-style NC macro files for human understanding.")
    parser.add_argument("input", type=Path, help="Input NC, MIN, or TXT file")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("output"), help="Output directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = analyze_file(args.input)
    write_outputs(result, args.output_dir)
    return 0


def write_outputs(result, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / REPORT_FILE).write_text(render_markdown(result), encoding="utf-8")
    (output_dir / JSON_FILE).write_text(render_json(result), encoding="utf-8")
    (output_dir / MERMAID_FILE).write_text(render_mermaid(result), encoding="utf-8")
