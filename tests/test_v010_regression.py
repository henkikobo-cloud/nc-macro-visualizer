import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nc_macro_visualizer.analyzer import analyze_text
from nc_macro_visualizer.cli.main import main
from nc_macro_visualizer.profiles.fanuc import describe_m_code
from nc_macro_visualizer.renderer import render_json, render_markdown, render_mermaid


class V010RegressionTests(unittest.TestCase):
    def test_cli_processes_all_samples(self):
        samples = sorted((ROOT / "samples").glob("*.nc"))
        self.assertGreaterEqual(len(samples), 5)

        for sample in samples:
            with self.subTest(sample=sample.name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    exit_code = main([str(sample), "-o", tmpdir])

                    self.assertEqual(exit_code, 0)
                    self.assertTrue((Path(tmpdir) / "report.md").exists())
                    self.assertTrue((Path(tmpdir) / "analysis.json").exists())
                    self.assertTrue((Path(tmpdir) / "flow.mmd").exists())

                    analysis = json.loads((Path(tmpdir) / "analysis.json").read_text(encoding="utf-8"))
                    self.assertEqual(analysis["source_name"], sample.name)
                    self.assertIn("warnings", analysis)

    def test_unknown_m_code_profile_stays_machine_specific(self):
        profile = describe_m_code("M123")

        self.assertEqual(profile["description"], "unknown")
        self.assertEqual(profile["category"], "machine_specific")

    def test_existing_outputs_keep_stable_contract(self):
        source = """%
O1000
N10 #100 = 12
N20 IF [#100 GT 10] GOTO 80
N30 M03 S1200
N40 GOTO 90
N80 M08
N90 M30
%
"""
        result = analyze_text(source, "stable.nc")

        report = render_markdown(result)
        analysis_json = render_json(result)
        flow = render_mermaid(result)
        analysis = json.loads(analysis_json)

        self.assertIn("# NC Macro Visualizer Report: stable.nc", report)
        self.assertIn("| 4 | IF_GOTO | N80 | `[#100 GT 10]`", report)
        self.assertEqual(analysis["source_name"], "stable.nc")
        self.assertEqual(analysis["variable_summary"][0]["name"], "#100")
        self.assertEqual(analysis["variable_summary"][0]["count"], 2)
        self.assertEqual(analysis["warnings"], [])
        self.assertIn('N20{"N20 IF [#100 GT 10] GOTO 80"}', flow)
        self.assertIn("N20 -->|YES| N80", flow)
        self.assertIn("N20 -->|NO| N30", flow)
        self.assertIn("N40 -->|GOTO| END_N90", flow)


if __name__ == "__main__":
    unittest.main()
