import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nc_macro_visualizer.analyzer import analyze_text
from nc_macro_visualizer.renderer import render_json, render_markdown, render_mermaid


SAMPLE = """%
O1000 (sample)
N10 #100 = 12
N20 IF [#100 GT 10] GOTO 80
N30 M03 S1200
N40 GOTO 90
N80 M08
N90 M30
%
"""


class RendererTests(unittest.TestCase):
    def test_markdown_report_contains_sections(self):
        report = render_markdown(analyze_text(SAMPLE, "sample.nc"))

        self.assertIn("# NC Macro Visualizer Report: sample.nc", report)
        self.assertIn("## Warnings", report)
        self.assertIn("## Variable Summary", report)
        self.assertIn("## Variable Dependencies", report)
        self.assertIn("## Flow Controls", report)
        self.assertIn("## M Codes", report)
        self.assertIn("| 4 | IF_GOTO | N80 | `[#100 GT 10]`", report)

    def test_json_report_contains_variable_counts_and_warnings(self):
        report = render_json(analyze_text(SAMPLE, "sample.nc"))

        self.assertIn('"name": "#100"', report)
        self.assertIn('"count": 2', report)
        self.assertIn('"warnings": []', report)

    def test_mermaid_report_contains_flow_edges(self):
        report = render_mermaid(analyze_text(SAMPLE, "sample.nc"))

        self.assertIn("flowchart TD", report)
        self.assertIn('N20{"N20 IF [#100 GT 10] GOTO 80"}', report)
        self.assertIn("N20 -->|YES| N80", report)
        self.assertIn("N20 -->|NO| N30", report)
        self.assertIn("N40 -->|GOTO| END_N90", report)
        self.assertIn('END_N90(["N90 M30<br/>END"])', report)
        self.assertNotIn("L1", report)

    def test_mermaid_renders_calls_if_then_and_m99_end(self):
        source = """N10 M98 P2000
N20 IF [#<RESULT> GT 0] THEN #102 = 1
N30 M99
"""
        report = render_mermaid(analyze_text(source, "flow.nc"))

        self.assertIn('N10[["N10 M98 P2000<br/>CALL M98 P2000"]]', report)
        self.assertIn("N10 -.->|CALL M98| N2000_UNRESOLVED", report)
        self.assertIn('N20{"N20 IF [#&lt;RESULT&gt; GT 0] THEN #102 = 1"}', report)
        self.assertIn('N20_THEN["THEN #102 = 1"]', report)
        self.assertIn("N20 -->|THEN| N20_THEN", report)
        self.assertIn('END_N30(["N30 M99<br/>END"])', report)

    def test_mermaid_renders_while_end_loop(self):
        source = """N10 #100 = 0
N20 WHILE [#100 LT 3] DO1
N30 #100 = #100 + 1
N40 END1
N50 M30
"""
        report = render_mermaid(analyze_text(source, "loop.nc"))

        self.assertIn("N20 -->|DO| N30", report)
        self.assertIn("N20 -->|END| END_N50", report)
        self.assertIn("N40 -->|LOOP| N20", report)


if __name__ == "__main__":
    unittest.main()
