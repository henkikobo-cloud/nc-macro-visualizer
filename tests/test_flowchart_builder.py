import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nc_macro_visualizer.analyzer import analyze_text
from nc_macro_visualizer.flowchart import build_beginner_flow
from nc_macro_visualizer.renderer import render_beginner_json


class FlowchartBuilderTests(unittest.TestCase):
    def test_translates_assignments_and_keeps_traceability(self):
        result = analyze_text("N10 #100 = 1\nN20 #500 = #100 + #101\n", "variables.nc")

        flow = build_beginner_flow(result)
        nodes = {node.id: node for node in flow.nodes}

        self.assertEqual(nodes["N10"].title, "値を入れる")
        self.assertEqual(nodes["N20"].title, "値を計算する")
        self.assertEqual(nodes["N20"].source_line_no, 2)
        self.assertEqual(nodes["N20"].source_label, "20")
        self.assertEqual(nodes["N20"].source_text, "N20 #500 = #100 + #101")

    def test_translates_if_goto_if_then_and_branch_edges(self):
        source = """N10 IF [#100 GT 10] GOTO 80
N20 M30
N80 M30
"""
        flow = build_beginner_flow(analyze_text(source, "branches.nc"))
        nodes = {node.id: node for node in flow.nodes}
        edges = {(edge.source, edge.target, edge.kind, edge.label) for edge in flow.edges}

        self.assertEqual(nodes["N10"].title, "条件で分かれる")
        self.assertIn(("N10", "N80", "branch_true", "はい"), edges)
        self.assertIn(("N10", "N20", "branch_false", "いいえ"), edges)

    def test_translates_if_then(self):
        flow = build_beginner_flow(analyze_text("N10 IF [#101 EQ 1] THEN #102 = 5\nN20 M30\n", "then.nc"))
        nodes = {node.id: node for node in flow.nodes}

        self.assertEqual(nodes["N10"].title, "条件が合うと処理する")
        self.assertIn("N10_THEN", nodes)

    def test_translates_calls_program_end_and_unknown_m_code(self):
        source = """N10 M98 P2000
N20 M123
N30 M30
"""
        flow = build_beginner_flow(analyze_text(source, "mcodes.nc"))
        nodes = {node.id: node for node in flow.nodes}

        self.assertEqual(nodes["N10"].kind, "call")
        self.assertEqual(nodes["N10"].title, "別のプログラムを呼び出す")
        self.assertEqual(nodes["N20"].kind, "needs_confirmation")
        self.assertEqual(nodes["N20"].title, "意味の確認が必要なMコード")
        self.assertIn("機械の説明書", nodes["N20"].summary)
        self.assertEqual(nodes["N30"].title, "プログラムを終了する")
        self.assertTrue(any("PMC" in warning.message for warning in flow.warnings))

    def test_renders_beginner_json_contract(self):
        flow = build_beginner_flow(analyze_text("N10 #100 = 1\n", "json.nc"))

        rendered = render_beginner_json(flow)

        self.assertIn('"schema_version": "beginner-flow/v0.2"', rendered)
        self.assertIn('"source_name": "json.nc"', rendered)
        self.assertIn('"kind": "process"', rendered)
        self.assertIn('"source_label": "10"', rendered)

    def test_long_if_goto_uses_connector_nodes_without_direct_edge(self):
        source = """N10 IF [#100 EQ 1] GOTO 90
N20 #101 = 1
N30 #102 = 1
N40 #103 = 1
N50 #104 = 1
N90 M30
"""
        flow = build_beginner_flow(analyze_text(source, "long_jump.nc"))
        nodes = {node.id: node for node in flow.nodes}
        edge_pairs = {(edge.source, edge.target) for edge in flow.edges}

        self.assertIn("N10_JUMP_OUT_N90", nodes)
        self.assertIn("N90_JUMP_IN_FROM_N10", nodes)
        self.assertEqual(nodes["N10_JUMP_OUT_N90"].kind, "jump_out")
        self.assertEqual(nodes["N10_JUMP_OUT_N90"].title, "指定した場所へ進む")
        self.assertIn("N90", nodes["N10_JUMP_OUT_N90"].summary)
        self.assertEqual(nodes["N90_JUMP_IN_FROM_N10"].kind, "jump_in")
        self.assertEqual(nodes["N90_JUMP_IN_FROM_N10"].title, "合流地点")
        self.assertIn("N10", nodes["N90_JUMP_IN_FROM_N10"].summary)
        self.assertNotIn(("N10", "N90"), edge_pairs)
        self.assertNotIn(("N10_JUMP_OUT_N90", "N90_JUMP_IN_FROM_N10"), edge_pairs)

    def test_merge_targets_have_at_most_one_labeled_incoming_edge(self):
        source = """N10 IF [#100 EQ 1] GOTO 50
N20 #101 = 1
N30 GOTO 50
N40 #102 = 1
N50 M30
"""
        flow = build_beginner_flow(analyze_text(source, "merge.nc"))
        incoming: dict[str, list[str]] = {}
        for edge in flow.edges:
            incoming.setdefault(edge.target, []).append(edge.label)

        for labels in incoming.values():
            non_empty = [label for label in labels if label]
            self.assertLessEqual(len(non_empty), 1)

    def test_decision_edges_emit_false_before_true(self):
        flow = build_beginner_flow(analyze_text("N10 IF [#100 EQ 1] GOTO 40\nN20 #101 = 1\nN40 M30\n", "order.nc"))
        decision_edges = [edge for edge in flow.edges if edge.source == "N10" and edge.kind.startswith("branch_")]

        self.assertEqual([edge.kind for edge in decision_edges], ["branch_false", "branch_true"])

    def test_if_then_merge_target_has_only_one_labeled_incoming_edge(self):
        source = "N10 IF [#102 EQ 1] THEN #103 = #<RESULT>\nN20 #104 = #103\nN30 M30\n"
        flow = build_beginner_flow(analyze_text(source, "if_then_merge.nc"))
        incoming_to_merge = [edge for edge in flow.edges if edge.target == "N20"]
        labeled = [edge for edge in incoming_to_merge if edge.label]

        self.assertEqual(len(labeled), 1)
        self.assertEqual(labeled[0].kind, "branch_false")
        self.assertEqual(labeled[0].label, "いいえ")
        self.assertIn(("N10_THEN", "N20", "sequential", ""), {
            (edge.source, edge.target, edge.kind, edge.label) for edge in incoming_to_merge
        })

    def test_decision_outgoing_labels_survive_merge_suppression(self):
        source = "N10 IF [#102 EQ 1] THEN #103 = #<RESULT>\nN20 #104 = #103\nN30 M30\n"
        flow = build_beginner_flow(analyze_text(source, "decision_labels.nc"))
        outgoing = {(edge.kind, edge.label) for edge in flow.edges if edge.source == "N10"}

        self.assertIn(("branch_false", "いいえ"), outgoing)
        self.assertIn(("branch_true", "はい"), outgoing)

    def test_three_incoming_merge_keeps_branch_false_label_only(self):
        source = """N10 IF [#100 EQ 1] THEN #101 = 1
N20 #102 = #101
N30 GOTO 20
N40 M30
"""
        flow = build_beginner_flow(analyze_text(source, "three_incoming.nc"))
        incoming_to_merge = [edge for edge in flow.edges if edge.target == "N20"]
        labeled = [(edge.kind, edge.label) for edge in incoming_to_merge if edge.label]

        self.assertEqual(labeled, [("branch_false", "いいえ")])


if __name__ == "__main__":
    unittest.main()
