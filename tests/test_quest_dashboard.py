import unittest
from pathlib import Path


class QuestDashboardTests(unittest.TestCase):
    def test_panel_mesh_does_not_shadow_canvas_panel_renderer(self):
        source = (Path(__file__).resolve().parents[1] / "body_runtime_host" / "quest_vr_dashboard.js").read_text(encoding="utf-8")

        self.assertIn("this.panel = panel;", source)
        self.assertIn("drawPanel(ctx, x, y, width, height, title, meta = '')", source)
        self.assertEqual(source.count("this.drawPanel(ctx,"), 4)
        self.assertNotIn("this.panel(ctx,", source)

    def test_simulation_controls_are_visible_before_entering_vr(self):
        root = Path(__file__).resolve().parents[1]
        gui_source = (root / "body_runtime_host" / "body_gui.py").read_text(encoding="utf-8")
        quest_html = (root / "body_runtime_host" / "quest_vr.html").read_text(encoding="utf-8")
        quest_source = (root / "body_runtime_host" / "quest_vr.js").read_text(encoding="utf-8")

        self.assertIn("wm-simulation-toggle", gui_source)
        self.assertIn('id="quest-simulation"', quest_html)
        self.assertIn("#quest-simulation').addEventListener('click', () => toggleSimulationFromHud())", quest_source)
        self.assertIn("syncSimulationControl(frame)", quest_source)

    def test_hud_arc_tilts_its_top_toward_the_viewer(self):
        source = (Path(__file__).resolve().parents[1] / "body_runtime_host" / "quest_vr_dashboard.js").read_text(encoding="utf-8")

        self.assertIn("createArcGeometry(8.4, 0.5, 64)", source)
        self.assertIn("const topForwardTilt = row === 0 ? depth / 2 : -depth / 2", source)
        self.assertIn("+ topForwardTilt", source)
        self.assertIn("radius * (Math.cos(theta) - 1)", source)
        self.assertNotIn("radius * (1 - Math.cos(theta))", source)

    def test_hud_faces_the_headset_when_moved_and_sensor_labels_are_legible(self):
        source = (Path(__file__).resolve().parents[1] / "body_runtime_host" / "quest_vr_dashboard.js").read_text(encoding="utf-8")

        self.assertIn("this.facingMatrix.lookAt(this.scratchPosition, this.root.position, this.headUp)", source)
        self.assertIn("this.root.position.copy(this.headOffsetPosition).applyQuaternion(this.scratchQuaternion).add(this.scratchPosition)", source)
        self.assertIn("ctx.font = '16px ui-monospace, monospace'", source)
        self.assertIn("ctx.font = '15px ui-monospace, monospace'", source)


if __name__ == "__main__":
    unittest.main()
