import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nc_macro_visualizer.analyzer import analyze_text
from nc_macro_visualizer.flowchart import build_beginner_flow, structurize_beginner_flow
from nc_macro_visualizer.renderer import render_nassi_shneiderman, render_structured_text


class StructuredRendererTests(unittest.TestCase):
    def test_structurizer_preserves_if_then_as_nested_block(self):
        flow = build_beginner_flow(
            analyze_text("N10 IF [#100 EQ 1] THEN #101 = 5\nN20 M30\n", "structured.nc")
        )

        program = structurize_beginner_flow(flow)
        first = program.blocks[0]

        self.assertEqual(first.kind, "if")
        self.assertEqual(first.title, "条件が合うと処理する")
        self.assertEqual(len(first.children), 1)
        self.assertIn("#101 = 5", first.children[0].summary)

    def test_renders_nassi_shneiderman_html(self):
        flow = build_beginner_flow(analyze_text("N10 #100 = 1\nN20 M30\n", "nassi.nc"))
        program = structurize_beginner_flow(flow)

        html = render_nassi_shneiderman(program)

        self.assertIn('class="ns-diagram"', html)
        self.assertIn("nassi.nc", html)
        self.assertIn("値を入れる", html)

    def test_renders_structured_text(self):
        flow = build_beginner_flow(analyze_text("N10 M123\n", "text.nc"))
        program = structurize_beginner_flow(flow)

        text = render_structured_text(program)

        self.assertIn("# Structured View: text.nc", text)
        self.assertIn("意味の確認が必要なMコード", text)


if __name__ == "__main__":
    unittest.main()
