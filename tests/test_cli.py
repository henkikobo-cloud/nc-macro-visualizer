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


if __name__ == "__main__":
    unittest.main()
