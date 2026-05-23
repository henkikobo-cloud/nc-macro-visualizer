import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nc_macro_visualizer.cli.main import main


class CLITests(unittest.TestCase):
    def test_cli_writes_expected_outputs(self):
        sample = ROOT / "samples" / "01_simple_if.nc"
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = main([str(sample), "-o", tmpdir])

            self.assertEqual(exit_code, 0)
            self.assertTrue((Path(tmpdir) / "report.md").exists())
            self.assertTrue((Path(tmpdir) / "analysis.json").exists())
            self.assertTrue((Path(tmpdir) / "flow.mmd").exists())
            self.assertFalse((Path(tmpdir) / "beginner_flow.json").exists())

    def test_cli_writes_beginner_flow_when_requested(self):
        sample = ROOT / "samples" / "04_variables.nc"
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = main([str(sample), "-o", tmpdir, "--beginner"])

            self.assertEqual(exit_code, 0)
            output = Path(tmpdir) / "beginner_flow.json"
            self.assertTrue(output.exists())
            text = output.read_text(encoding="utf-8")
            self.assertIn('"schema_version": "beginner-flow/v0.2"', text)
            self.assertIn('"source_name": "04_variables.nc"', text)

    def test_cli_writes_structured_outputs_when_requested(self):
        sample = ROOT / "samples" / "04_variables.nc"
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = main([str(sample), "-o", tmpdir, "--nassi", "--text"])

            self.assertEqual(exit_code, 0)
            nassi = Path(tmpdir) / "nassi_shneiderman.html"
            text = Path(tmpdir) / "structured_text.md"
            self.assertTrue(nassi.exists())
            self.assertTrue(text.exists())
            self.assertIn('class="ns-diagram"', nassi.read_text(encoding="utf-8"))
            self.assertIn("# Structured View: 04_variables.nc", text.read_text(encoding="utf-8"))

    def test_cli_writes_v030_outputs_when_requested(self):
        sample = ROOT / "samples" / "04_variables.nc"
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = main([str(sample), "-o", tmpdir, "--pad-html", "--pad-text", "--cfg"])

            self.assertEqual(exit_code, 0)
            self.assertIn("pad.css", (Path(tmpdir) / "pad.html").read_text(encoding="utf-8"))
            self.assertIn("N30: もし [#<RESULT> GT 0] なら", (Path(tmpdir) / "pad.txt").read_text(encoding="utf-8"))
            self.assertIn('"schema_version": "cfg/v0.3"', (Path(tmpdir) / "cfg.json").read_text(encoding="utf-8"))

    def test_cli_all_views_includes_existing_and_v030_outputs(self):
        sample = ROOT / "samples" / "04_variables.nc"
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = main([str(sample), "-o", tmpdir, "--all-views"])

            self.assertEqual(exit_code, 0)
            for name in [
                "report.md",
                "analysis.json",
                "flow.mmd",
                "beginner_flow.json",
                "nassi_shneiderman.html",
                "structured_text.md",
                "pad.html",
                "pad.txt",
                "cfg.json",
            ]:
                self.assertTrue((Path(tmpdir) / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
