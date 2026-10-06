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

    def test_vr_scene_forward_axis_and_camera_arc_align_with_body_heading(self):
        source = (Path(__file__).resolve().parents[1] / "body_runtime_host" / "quest_vr.js").read_text(encoding="utf-8")

        self.assertIn("xrFollowTarget.copy(xrFollowHeadPosition).addScaledVector(xrFollowForward, 3.0)", source)
        self.assertIn("const sceneYaw = xrFollowYaw + Math.PI / 2 + xrSceneYawOffset", source)
        self.assertIn("applyAxisAngle(xrFollowYawAxis, sceneYaw)", source)
        self.assertIn("world.rotation.set(0, sceneYaw, 0)", source)
        self.assertIn("bodyMarker.rotation.y = yaw", source)
        self.assertIn("cameraArcRoot.rotation.set(0, -Math.PI / 2 - (Number(bodyPose.orientation) || 0), 0)", source)
        self.assertIn("It stays put as the Body turns", source)

    def test_navigation_brick_distinguishes_imu_attitude_heading_and_valid_gps_fix(self):
        source = (Path(__file__).resolve().parents[1] / "body_runtime_host" / "quest_vr_dashboard.js").read_text(encoding="utf-8")

        self.assertIn("drawNavigationInstruments(ctx, x, y, width, headingX, perception, fnk, headingDeg, speed)", source)
        self.assertIn("ATTITUDE · 3D HORIZON", source)
        self.assertIn("pitch_rad", source)
        self.assertIn("ctx.rotate(-roll * Math.PI / 180)", source)
        self.assertIn("HDG ${Number.isFinite(heading)", source)
        self.assertIn("gps.fix_quality", source)
        self.assertIn("NO VALID FIX", source)
        self.assertIn("GPS COG", source)
        self.assertIn("drawAzimuthRing(ctx, centerX, centerY, radius + 18, heading)", source)
        self.assertIn("indexY - 11", source)

    def test_2d_hud_preview_contains_live_imu_gps_navigation_brick(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "body_runtime_host" / "quest_hud_preview.html").read_text(encoding="utf-8")
        source = (root / "body_runtime_host" / "quest_hud_preview.js").read_text(encoding="utf-8")

        self.assertIn('id="nav-horizon"', html)
        self.assertIn('id="nav-gps"', html)
        self.assertIn('id="nav-heading-value"', html)
        self.assertIn("function drawNavigation(", source)
        self.assertIn("WAITING FOR FIX", html)
        self.assertIn("drawNavigation();", source)
        self.assertIn("const ring = radius + 15", source)
        self.assertIn("pointerY - 6", source)

    def test_vr_horizon_column_clears_robot_and_uses_sharp_canvas_filtering(self):
        source = (Path(__file__).resolve().parents[1] / "body_runtime_host" / "quest_vr_dashboard.js").read_text(encoding="utf-8")

        self.assertIn("this.texture.generateMipmaps = false", source)
        self.assertIn("this.texture.minFilter = THREE.LinearFilter", source)
        self.assertIn("this.robotVisual.group.position.set(-0.82, -0.5, -4.08)", source)
        self.assertIn("const centerX = x + width * .84", source)
        self.assertIn("ctx.ellipse(x + 267, y + 620", source)


if __name__ == "__main__":
    unittest.main()
