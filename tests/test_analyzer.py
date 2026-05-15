import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nc_macro_visualizer.analyzer import analyze_text


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


class AnalyzerTests(unittest.TestCase):
    def test_extracts_variables_controls_and_m_codes(self):
        result = analyze_text(SAMPLE, "sample.nc")

        self.assertEqual([(hit.line_no, hit.name, hit.kind) for hit in result.variables], [
            (3, "#100", "assignment"),
            (4, "#100", "reference"),
        ])
        self.assertEqual([(hit.line_no, hit.kind, hit.target) for hit in result.controls], [
            (4, "IF_GOTO", "80"),
            (6, "GOTO", "90"),
        ])
        self.assertEqual([(hit.line_no, hit.code) for hit in result.m_codes], [
            (5, "M3"),
            (7, "M8"),
            (8, "M30"),
        ])

    def test_machine_specific_m_code_is_unknown(self):
        result = analyze_text("N10 M50\n", "machine.nc")

        self.assertEqual(result.m_codes[0].description, "unknown")
        self.assertEqual(result.m_codes[0].category, "machine_specific")

    def test_extracts_m98_and_g65_calls(self):
        result = analyze_text("N10 M98 P2000\nN20 G65 P3000 A1.0\n", "calls.nc")

        self.assertEqual([(hit.kind, hit.target) for hit in result.calls], [("M98", "2000"), ("G65", "3000")])

    def test_emits_validation_warnings(self):
        source = "N10 GOTO 999\nN20 M30\nN20 M99\n"

        result = analyze_text(source, "program.csv")

        self.assertEqual(
            [(warning.line_no, warning.code) for warning in result.warnings],
            [(None, "unsupported_extension"), (2, "duplicate_label"), (1, "unresolved_goto")],
        )

    def test_records_variable_dependencies(self):
        result = analyze_text("N10 #500 = #100 + #101\nN20 #<RESULT> = #500\n", "variables.nc")

        self.assertEqual(
            [(hit.line_no, hit.target, hit.sources) for hit in result.variable_dependencies],
            [(1, "#500", ["#100", "#101"]), (2, "#<RESULT>", ["#500"])],
        )


if __name__ == "__main__":
    unittest.main()
