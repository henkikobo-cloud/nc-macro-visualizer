import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nc_macro_visualizer.analyzer import analyze_file, analyze_text
from nc_macro_visualizer.flowchart import build_cfg, structurize_cfg
from nc_macro_visualizer.flowchart.cfg import CFGEdge, CFGNode, ControlFlowGraph
from nc_macro_visualizer.renderers import render_pad_html, render_pad_text


class CFGV030Tests(unittest.TestCase):
    def test_builds_cfg_for_samples_with_entry_and_exit(self):
        for sample in (ROOT / "samples").glob("*.nc"):
            with self.subTest(sample=sample.name):
                cfg = build_cfg(analyze_file(sample))

                self.assertEqual(cfg.schema_version, "cfg/v0.3")
                self.assertEqual(cfg.entry_node_id, "ENTRY")
                self.assertEqual(cfg.exit_node_ids, ["EXIT"])
                self.assertTrue(cfg.nodes)
                self.assertTrue(cfg.edges)

    def test_if_goto_emits_true_and_false_edges(self):
        cfg = build_cfg(analyze_text("N10 IF [#100 EQ 1] GOTO 30\nN20 M05\nN30 M30\n", "if.nc"))
        edges = {(edge.source, edge.target, edge.kind, edge.condition) for edge in cfg.edges}

        self.assertIn(("N10", "N30", "branch_true", "[#100 EQ 1]"), edges)
        self.assertIn(("N10", "N20", "branch_false", "[#100 EQ 1]"), edges)

    def test_while_loop_emits_back_edge(self):
        cfg = build_cfg(
            analyze_text("N10 WHILE [#1 LT 3] DO 1\nN20 #1 = #1 + 1\nN30 END1\nN40 M30\n", "while.nc")
        )

        self.assertIn(("N30", "N10", "back"), {(edge.source, edge.target, edge.kind) for edge in cfg.edges})

    def test_unresolved_jump_uses_unresolved_node_and_jump_edge(self):
        cfg = build_cfg(analyze_text("N10 GOTO 999\nN20 M30\n", "missing.nc"))
        nodes = {node.id: node for node in cfg.nodes}

        self.assertEqual(nodes["N999_UNRESOLVED"].kind, "unresolved")
        self.assertIn(("N10", "N999_UNRESOLVED", "jump"), {(edge.source, edge.target, edge.kind) for edge in cfg.edges})

    def test_call_site_emits_call_edge(self):
        cfg = build_cfg(analyze_text("N10 M98 P2000\nN20 M30\n", "call.nc"))

        self.assertIn(("N10", "N20", "call", "2000"), {(edge.source, edge.target, edge.kind, edge.condition) for edge in cfg.edges})


class StructurizerV030Tests(unittest.TestCase):
    def test_while_loop_pattern(self):
        cfg = build_cfg(
            analyze_text("N10 WHILE [#1 LT 3] DO 1\nN20 #1 = #1 + 1\nN30 END1\nN40 M30\n", "while.nc")
        )
        tree = structurize_cfg(cfg)

        self.assertEqual(tree.root.children[0].kind, "while_loop")
        self.assertEqual(tree.root.children[0].children[0].kind, "process")

    def test_if_then_pattern(self):
        cfg = build_cfg(analyze_text("N10 IF [#1 EQ 1] THEN #2 = 1\nN20 M30\n", "then.nc"))
        tree = structurize_cfg(cfg)

        self.assertEqual(tree.root.children[0].kind, "if_then")
        self.assertEqual(tree.root.children[0].children[0].kind, "process")

    def test_if_then_else_pattern_from_cfg(self):
        cfg = ControlFlowGraph(
            "cfg/v0.3",
            "else.nc",
            [
                CFGNode("ENTRY", "entry", None, None, None, []),
                CFGNode("D", "decision", 1, "10", "N10 IF ...", ["N10 IF ..."]),
                CFGNode("T", "basic_block", 2, "20", "N20 #1=1", ["N20 #1=1"]),
                CFGNode("F", "basic_block", 3, "30", "N30 #1=0", ["N30 #1=0"]),
                CFGNode("E", "basic_block", 4, "40", "N40 M30", ["N40 M30"]),
                CFGNode("EXIT", "exit", None, None, None, []),
            ],
            [
                CFGEdge("ENTRY", "D", "forward", None),
                CFGEdge("D", "T", "branch_true", "[#1 EQ 1]"),
                CFGEdge("D", "F", "branch_false", "[#1 EQ 1]"),
                CFGEdge("T", "E", "forward", None),
                CFGEdge("F", "E", "forward", None),
                CFGEdge("E", "EXIT", "forward", None),
            ],
            "ENTRY",
            ["EXIT"],
        )
        tree = structurize_cfg(cfg)

        self.assertEqual(tree.root.children[0].kind, "if_then_else")
        self.assertEqual(len(tree.root.children[0].children), 2)

    def test_unstructured_jump_has_note(self):
        cfg = build_cfg(analyze_text("N10 GOTO 999\nN20 M30\n", "jump.nc"))
        tree = structurize_cfg(cfg)

        self.assertEqual(tree.root.children[0].kind, "unstructured_jump")
        self.assertIn("構造化できない", tree.root.children[0].note)

    def test_pad_renderers_include_traceability_and_disclaimer(self):
        cfg = build_cfg(analyze_text("N10 IF [#1 EQ 1] THEN #2 = 1\nN20 M30\n", "pad.nc"))
        tree = structurize_cfg(cfg)

        html = render_pad_html(tree)
        text = render_pad_text(tree)

        self.assertIn("<!doctype html>", html)
        self.assertIn("本ツールは機械動作を保証しません", html)
        self.assertIn("pad-root", html)
        self.assertIn("pad-sequence-line", html)
        self.assertIn("pad-selection", html)
        self.assertIn("pad-condition-box", html)
        self.assertIn("pad-selection-then", html)
        self.assertIn("pad-terminal pad-start", html)
        self.assertIn("pad-terminal pad-program-end", html)
        self.assertIn("pad-terminal-box", html)
        self.assertIn("pad-terminal-mark", html)
        self.assertIn("▶", html)
        self.assertIn("■", html)
        self.assertIn("プログラム開始", html)
        self.assertIn("プログラム終了", html)
        start_marker = html[html.index("pad-terminal pad-start") : html.index("pad-terminal pad-start") + 260]
        end_marker = html[html.index("pad-terminal pad-program-end") : html.index("pad-terminal pad-program-end") + 260]
        self.assertNotIn("pad-seq-number", start_marker)
        self.assertNotIn("line", start_marker)
        self.assertNotIn("pad-seq-number", end_marker)
        self.assertNotIn("line", end_marker)
        self.assertIn("pad-box-header", html)
        self.assertIn("pad-seq-number", html)
        self.assertIn(">N10<", html)
        self.assertIn("pad-title-separator", html)
        self.assertIn("pad-title-text", html)
        self.assertIn("pad-line-trace", html)
        self.assertIn(">line 1<", html)
        self.assertIn("#2 に 1 を入れます", html)
        self.assertNotIn("pad-selection-else", html)
        self.assertNotIn("pad-control-kind", html)
        self.assertNotIn("pad-branch-mark", html)
        self.assertNotIn("pad-branch-label", html)
        self.assertNotIn("処理はありません", html)
        self.assertNotIn(">選択<", html)
        self.assertNotIn(">反復<", html)
        self.assertIn('style="--depth: 1"', html)
        self.assertEqual(text.splitlines()[0], "▶ プログラム開始")
        self.assertEqual(text.splitlines()[-1], "■ プログラム終了")
        self.assertIn("N10: もし [#1 EQ 1] なら\n", text)
        self.assertIn("  N10: 値を入れる  (#2 に 1 を入れます)", text)
        self.assertIn("N20: プログラムを終了する", text)
        self.assertNotIn("# N10", text)

    def test_pad_line_number_fallback_when_source_label_is_absent(self):
        cfg = build_cfg(analyze_text("#100 = 1\nM30\n", "line_fallback.nc"))
        html = render_pad_html(structurize_cfg(cfg))
        text = render_pad_text(structurize_cfg(cfg))

        self.assertIn("pad-seq-number pad-seq-line", html)
        self.assertIn(">line 1<", html)
        self.assertNotIn("pad-line-trace", html)
        self.assertIn("\nline 1:", text)

    def test_pad_natural_language_assignment_summaries(self):
        cfg = build_cfg(
            analyze_text(
                "N10 #102 = 1\nN20 #500 = #100 + #101\nN30 #501 = #100 + #101 + #102\nN40 M30\n",
                "summaries.nc",
            )
        )
        html = render_pad_html(structurize_cfg(cfg))
        text = render_pad_text(structurize_cfg(cfg))

        self.assertIn("#102 に 1 を入れます", html)
        self.assertIn("#100 と #101 を足して #500 に入れます", html)
        self.assertIn("#501 を計算して入れます", html)
        self.assertIn("N20: 値を計算する  (#100 と #101 を足して #500 に入れます)", text)
        self.assertNotIn("N20: 値を計算する  N20 #500", text)

    def test_pad_if_then_else_and_while_layout_contract(self):
        cfg = ControlFlowGraph(
            "cfg/v0.3",
            "layout.nc",
            [
                CFGNode("ENTRY", "entry", None, None, None, []),
                CFGNode("D", "decision", 1, "10", "N10 IF ...", ["N10 IF ..."]),
                CFGNode("T", "basic_block", 2, "20", "N20 #1=1", ["N20 #1=1"]),
                CFGNode("F", "basic_block", 3, "30", "N30 #1=0", ["N30 #1=0"]),
                CFGNode("E", "basic_block", 4, "40", "N40 M30", ["N40 M30"]),
                CFGNode("EXIT", "exit", None, None, None, []),
            ],
            [
                CFGEdge("ENTRY", "D", "forward", None),
                CFGEdge("D", "T", "branch_true", "[#1 EQ 1]"),
                CFGEdge("D", "F", "branch_false", "[#1 EQ 1]"),
                CFGEdge("T", "E", "forward", None),
                CFGEdge("F", "E", "forward", None),
                CFGEdge("E", "EXIT", "forward", None),
            ],
            "ENTRY",
            ["EXIT"],
        )
        html = render_pad_html(structurize_cfg(cfg))

        self.assertIn("pad-selection-then", html)
        self.assertIn("pad-selection-else", html)
        self.assertIn("そうでなければ", html)

        while_cfg = build_cfg(
            analyze_text("N10 WHILE [#1 LT 3] DO 1\nN20 #1 = #1 + 1\nN30 END1\nN40 M30\n", "while.nc")
        )
        while_html = render_pad_html(structurize_cfg(while_cfg))
        css = (ROOT / "web" / "pad.css").read_text(encoding="utf-8")

        self.assertIn("pad-while-body", while_html)
        self.assertIn("の間くり返す", while_html)
        self.assertIn("border-left: 4px double var(--pad-accent)", css)
        self.assertIn("word-break: break-all", css)
        self.assertIn("--pad-seq-color", css)
        self.assertIn("--pad-terminal-bg", css)
        self.assertIn("--pad-start-color", css)
        self.assertIn("--pad-end-color", css)


if __name__ == "__main__":
    unittest.main()
