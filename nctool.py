#!/usr/bin/env python3
"""CLI entry point for NC Macro Visualizer."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nc_macro_visualizer.cli.main import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
