import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nc_macro_visualizer.parser import find_variable_dependencies, parse_lines, strip_comments


class ParserTests(unittest.TestCase):
    def test_strip_comments(self):
        self.assertEqual(strip_comments("N10 G0 X0 (move) M03 ; end"), "N10 G0 X0 M03")

    def test_extracts_variable_dependencies(self):
        line = parse_lines("N10 #500 = #100 + #101 + #100")[0]

        dependencies = find_variable_dependencies(line)

        self.assertEqual(len(dependencies), 1)
        self.assertEqual(dependencies[0].target, "#500")
        self.assertEqual(dependencies[0].sources, ["#100", "#101"])


if __name__ == "__main__":
    unittest.main()
