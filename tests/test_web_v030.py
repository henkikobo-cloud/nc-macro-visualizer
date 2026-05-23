import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WebV030Tests(unittest.TestCase):
    def test_index_has_three_view_tabs(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")

        self.assertIn('data-view="pad-output"', html)
        self.assertIn("初心者向け表示", html)
        self.assertIn('data-view="text-output"', html)
        self.assertIn("テキスト版", html)
        self.assertIn('data-view="flow-output"', html)
        self.assertIn("詳細表示（専門家向け）", html)
        self.assertIn("本ツールは機械動作を保証しません", html)

    def test_tab_logic_uses_session_storage(self):
        script = (ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("function activateView", script)
        self.assertIn("sessionStorage.setItem", script)
        self.assertIn("sessionStorage?.getItem", script)
        self.assertIn("restoreActiveView()", script)


if __name__ == "__main__":
    unittest.main()
