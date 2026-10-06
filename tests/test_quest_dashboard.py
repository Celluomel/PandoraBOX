import unittest
from pathlib import Path


class QuestDashboardTests(unittest.TestCase):
    def test_panel_mesh_does_not_shadow_canvas_panel_renderer(self):
        source = (Path(__file__).resolve().parents[1] / "body_runtime_host" / "quest_vr_dashboard.js").read_text(encoding="utf-8")

        self.assertIn("this.panel = panel;", source)
        self.assertIn("drawPanel(ctx, x, y, width, height, title, meta = '')", source)
        self.assertEqual(source.count("this.drawPanel(ctx,"), 4)
        self.assertNotIn("this.panel(ctx,", source)


if __name__ == "__main__":
    unittest.main()
