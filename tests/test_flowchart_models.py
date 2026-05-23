import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nc_macro_visualizer.flowchart.models import BeginnerEdge, BeginnerFlow, BeginnerNode
from nc_macro_visualizer.flowchart.terminology import (
    CALCULATION_TITLE,
    EDGE_LABELS,
    SCHEMA_VERSION,
    UNKNOWN_M_CODE_MESSAGE,
    UNKNOWN_M_CODE_TITLE,
)


class FlowchartModelTests(unittest.TestCase):
    def test_beginner_flow_defaults_to_v02_schema(self):
        flow = BeginnerFlow(source_name="sample.nc")

        self.assertEqual(flow.schema_version, SCHEMA_VERSION)
        self.assertEqual(flow.nodes, [])
        self.assertEqual(flow.edges, [])
        self.assertEqual(flow.warnings, [])

    def test_node_and_edge_kind_values_are_validated(self):
        BeginnerNode("START", "start", "開始", "確認を始めます", None, None, None)
        BeginnerEdge("START", "END", "次へ", "sequential")

        with self.assertRaises(ValueError):
            BeginnerNode("BAD", "unsupported", "", "", None, None, None)

        with self.assertRaises(ValueError):
            BeginnerEdge("START", "END", "", "unsupported")

    def test_terminology_contains_required_beginner_wording(self):
        self.assertEqual(CALCULATION_TITLE, "値を計算する")
        self.assertEqual(UNKNOWN_M_CODE_TITLE, "意味の確認が必要なMコード")
        self.assertIn("機械の説明書", UNKNOWN_M_CODE_MESSAGE)
        self.assertEqual(EDGE_LABELS["branch_true"], "はい")
        self.assertEqual(EDGE_LABELS["branch_false"], "いいえ")


if __name__ == "__main__":
    unittest.main()
