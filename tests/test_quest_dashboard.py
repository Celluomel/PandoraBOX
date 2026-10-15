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

    def test_quest_can_replace_simulation_objects_with_live_sensor_scene(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "body_runtime_host" / "quest_vr.html").read_text(encoding="utf-8")
        source = (root / "body_runtime_host" / "quest_vr.js").read_text(encoding="utf-8")

        self.assertIn('id="scene-mode-sensors"', html)
        self.assertIn("selectSceneMode('sensors')", source)
        self.assertIn("objectsGroup.visible = false", source)
        self.assertIn("sensorSceneGroup.visible = true", source)
        self.assertIn("/body/camera/depth", source)
        self.assertIn("/body/camera/yolo/status", source)
        self.assertIn("/body/camera/image", source)
        self.assertIn("function pollSensorDepth()", source)
        self.assertIn("function pollSensorRadar()", source)
        self.assertNotIn("pollSensorSegmentation", source)
        self.assertNotIn("/body/camera/segmentation", source)
        self.assertNotIn("drawCameraYoloOverlay", (root / "body_runtime_host" / "quest_vr_dashboard.js").read_text(encoding="utf-8"))
        self.assertNotIn("LIVE · ${this.cameraDetectionCount} YOLO", (root / "body_runtime_host" / "quest_vr_dashboard.js").read_text(encoding="utf-8"))
        self.assertIn("/worldmodel/status", source)
        self.assertIn("/plugins/mmwave_radar/status", source)
        self.assertIn("updateSensorRadar(perception)", source)
        self.assertIn("calibratedSensorDistance(z)", source)
        self.assertIn("/body/camera/depth-calibration", source)
        self.assertIn("calibrated YOLOX ranges", source)
        self.assertIn("const z = calibratedSensorDistance(relative) ?? relative", source)
        self.assertIn("matchRadarTargetToYolo(rawPosition)", source)
        self.assertIn("const rangeTolerance = Math.max(0.65, radarRange * 0.3)", source)
        self.assertIn("yoloAge > 2.5", source)
        self.assertIn("new THREE.CylinderGeometry(0.12, 0.14, 0.14, 24)", source)
        self.assertIn("new THREE.PlaneGeometry(4.2, 4.2)", source)
        self.assertIn("new THREE.GridHelper(4.2, 14", source)
        self.assertIn("Math.min(5, calibratedFarRange + 0.5)", source)
        self.assertIn("floor.visible = false", source)
        self.assertIn("sensorGround.visible = true", source)
        dashboard = (root / "body_runtime_host" / "quest_vr_dashboard.js").read_text(encoding="utf-8")
        self.assertIn("drawButton('sensor-mode'", dashboard)
        self.assertIn("this.sceneMode === 'sensors'", dashboard)
        self.assertIn("hudAction === 'sensor-mode'", source)

    def test_world_model_has_persistent_radar_anchored_midas_calibration(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "body_runtime_host" / "world_map_3d.js").read_text(encoding="utf-8")
        runtime = (root / "body_runtime_host" / "runtime.py").read_text(encoding="utf-8")
        self.assertIn('id="world-map-midas-calibrate"', source)
        self.assertIn("Applied to all YOLOX objects", source)
        self.assertIn("relativeDepthToMeters", source)
        self.assertIn("nearest_to=", source)
        self.assertIn('query.get("nearest_to")', runtime)
        self.assertIn("performance.now() + 60000", source)
        self.assertIn("frameDelta <= 0.75", source)
        self.assertLess(source.index("radarHistory.push(latestRadar)"), source.index("nearest_to=${encodeURIComponent(depth.captured_at)}"))
        self.assertIn("diagnostics.bearing", source)
        self.assertIn("frames ${diagnostics.depth}, YOLO ${diagnostics.yolo}, radar ${diagnostics.radar}, bearing ${diagnostics.bearing}", source)
        self.assertIn("time-matched camera, YOLOX, MiDaS and LD2450", source)
        self.assertIn("/body/camera/depth-calibration", runtime)
        self.assertIn("midas_metric_calibration.json", runtime)

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
        self.assertIn("yaw_rate_dps", source)
        self.assertIn("NO MAGNETOMETER", source)
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
        self.assertIn("fetch('/plugins/imu/status'", source)
        self.assertIn("setInterval(pollImu, 1000)", source)
        self.assertIn("No local Arduino Bridge", source)
        self.assertIn("ACQUIRING ATTITUDE", source)
        self.assertIn("LAST VALID ·", source)
        self.assertIn("lastValidImuAt", source)
        self.assertIn("const ring = radius + 15", source)
        self.assertIn("pointerY - 6", source)

    def test_live_ld2450_targets_use_forward_lateral_axes_in_hud(self):
        root = Path(__file__).resolve().parents[1]
        preview = (root / "body_runtime_host" / "quest_hud_preview.js").read_text(encoding="utf-8")
        quest = (root / "body_runtime_host" / "quest_vr_dashboard.js").read_text(encoding="utf-8")

        self.assertIn("function radarTargetToHud(target, radar)", preview)
        self.assertIn("/^hlk_ld2450/i", preview)
        self.assertIn("[Number(position[1]), -Number(position[0])", preview)
        self.assertIn("worldLocal(hudTarget.position, perception, radar.frame)", preview)
        self.assertIn("const isLd2450 = /^hlk_ld2450/i", quest)
        self.assertIn("this.sensorLocal(radarPosition, radarFrame, bodyPosition, yaw)", quest)
        self.assertIn("const lateralLimit = Math.tan(Math.PI / 3) * 6", preview)
        draw_map = preview.split("function drawMap(canvas, mode) {", 1)[1].split("function drawTofRangeBar", 1)[0]
        self.assertLess(draw_map.index("const lateralLimit ="), draw_map.index("if (lidarMode) {"))
        self.assertIn("target.radial_speed_mps", preview)
        self.assertIn("const speedFont = Math.max(14 * ratio", preview)
        self.assertIn("const labelPadding = 4 * ratio", preview)
        self.assertIn("const preferredX = x > cx ? x - labelGap - labelWidth : x + labelGap", preview)
        self.assertIn("/moving|mobile/.test(classification)", preview)
        self.assertIn("const color = isMoving ? '#ed91c5' : '#efcb76'", preview)
        self.assertIn("target.radial_speed_mps", quest)
        self.assertIn("const preferredX = mapped.x > cx ? mapped.x - labelGap - labelWidth : mapped.x + labelGap", quest)
        self.assertIn("const color = isMoving ? '#ef91c5' : '#f2ce73'", quest)

    def test_vr_horizon_column_clears_robot_and_uses_sharp_canvas_filtering(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "body_runtime_host" / "quest_vr_dashboard.js").read_text(encoding="utf-8")
        quest_source = (root / "body_runtime_host" / "quest_vr.js").read_text(encoding="utf-8")

        self.assertIn("this.texture.generateMipmaps = true", source)
        self.assertIn("this.texture.minFilter = THREE.LinearMipmapLinearFilter", source)
        self.assertIn("this.robotVisual.group.position.set(-0.82, -0.5, -4.08)", source)
        self.assertIn("const centerX = x + width * .84", source)
        self.assertIn("ctx.ellipse(x + 267, y + 620", source)
        self.assertIn("700 30px system-ui", source)
        self.assertIn("HDG ${Number.isFinite(heading)", source)
        self.assertIn("updateImuStatus(status)", source)
        self.assertIn("fetch('/plugins/imu/status'", quest_source)


if __name__ == "__main__":
    unittest.main()
