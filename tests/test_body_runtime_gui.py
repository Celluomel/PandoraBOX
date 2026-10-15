import unittest


class BodyRuntimeGuiTests(unittest.TestCase):
    def test_world_map_switches_between_simulation_and_sensor_only_renderings(self):
        from body_runtime_host.body_gui import BODY_GUI_HTML

        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        source = (root / "body_runtime_host" / "world_map_3d.js").read_text(encoding="utf-8")
        self.assertIn('src="/world-map-3d.js"', BODY_GUI_HTML)
        self.assertIn('data-source="simulation"', source)
        self.assertIn('data-source="sensors"', source)
        self.assertIn('data-render="2d"', source)
        self.assertIn('data-render="3d"', source)
        self.assertIn(".map-layout>.map-wrap[hidden]", source)
        self.assertIn("sim?.resize(); buildSimulation(latestWorld); sim?.render()", source)
        self.assertIn("depth_gray_jpeg_base64", source)
        self.assertIn("no simulation object positions", source)
        self.assertIn("performance.now() - lastSensorDepthAt < 250", source)
        self.assertIn("age <= 2.5", source)
        self.assertIn("currentCamera.image_base64", source)
        self.assertIn("async function refreshSensorDepth()", source)
        self.assertIn("sensorDepthBusy", source)
        self.assertIn("depth.device", source)
        self.assertIn("s old", source)
        self.assertIn("activeRender === '3d'", source)
        self.assertIn("function drawDepthDetections(image, detections)", source)
        self.assertIn("makeLabel(`${item.label || item.class_name", source)
        self.assertIn("yolo.frame_id !== cloudYoloFrameId", source)
        self.assertIn("depth.depth_jpeg_base64 ? await loadGrayDepth(depth.depth_jpeg_base64)", source)
        self.assertIn("function semanticColor(classId)", source)
        self.assertIn("[0, '#ef8354']", source)
        self.assertIn("[89, '#3a86ff']", source)
        self.assertIn("[130, '#c77dff']", source)
        self.assertIn("[22, '#e76f51']", source)
        self.assertIn("padding:9px 0;color:#40574a", source)
        self.assertIn("padding:8px 10px;color:#33483d", source)
        self.assertIn("function segmentationMatchesDepth(segmentation, depth)", source)
        self.assertIn("Math.abs(segmentationTime - depthTime) <= 0.25", source)
        self.assertIn("Color MiDaS 3D points by semantic class", BODY_GUI_HTML)
        self.assertIn("camera-setting-segmentation-runtime", BODY_GUI_HTML)
        self.assertIn("/body/camera/segmentation", BODY_GUI_HTML)
        self.assertIn("world-map-segmentation-state", source)
        self.assertIn("async function renderSemanticMask(segmentation, cameraFrame)", source)
        self.assertIn("segmentationMatchesFrame(segmentation, cameraFrame)", source)
        self.assertIn("maskAge <= 2.5", source)
        self.assertIn("s lag", source)
        self.assertIn("world-map-segmentation-overlay", source)
        self.assertIn("CAMERA · YOLOX + SEGFORMER", source)
        self.assertNotIn("image-rendering:pixelated", source)
        self.assertIn("fetch('/body/camera/segmentation'", source)
        camera_refresh = source.split("async function refreshSensors()", 1)[1].split("async function refreshSensorSegmentation()", 1)[0]
        segmentation_refresh = source.split("async function refreshSensorSegmentation()", 1)[1].split("async function refreshSensorDepth()", 1)[0]
        self.assertNotIn("/body/camera/segmentation", camera_refresh)
        self.assertIn("!byId('world-map-segmentation-toggle')?.checked", segmentation_refresh)
        self.assertIn("}, 500);", source)
        quest = (root / "body_runtime_host" / "quest_vr.js").read_text(encoding="utf-8")
        self.assertNotIn("pollSensorSegmentation", quest)
        self.assertNotIn("sensorSemanticColor", quest)
        self.assertNotIn("fetch('/body/camera/segmentation'", quest)
        self.assertNotIn("latestSensorYolo?.frame_id === depthFrameId", source)
        self.assertIn("age <= 2.5", source)
        self.assertIn("}, 150);", source)

    def test_modulino_movement_controls_expose_persistent_body_setting_and_live_sample(self):
        from body_runtime_host.body_gui import BODY_GUI_HTML

        self.assertIn("VENTUNO Q · Modulino Movement", BODY_GUI_HTML)
        self.assertIn("Use physical IMU in Body and Quest HUD", BODY_GUI_HTML)
        self.assertIn("/plugins/imu/status", BODY_GUI_HTML)
        self.assertIn("Save IMU setting", BODY_GUI_HTML)

    def test_ld2450_settings_expose_ventuno_bridge_and_live_frame_state(self):
        from body_runtime_host.body_gui import BODY_GUI_HTML

        self.assertIn("Ventuno STM32 UART · local Bridge", BODY_GUI_HTML)
        self.assertIn("Ventuno UART7 online", BODY_GUI_HTML)
        self.assertIn("bridge_status", BODY_GUI_HTML)
        self.assertIn("void refreshSensorDevices()", BODY_GUI_HTML)

    def test_brain_bridge_settings_are_mounted_in_runtime_view(self):
        from body_runtime_host.body_gui import BODY_GUI_HTML

        self.assertIn("const page=document.getElementById('view-runtime')", BODY_GUI_HTML)
        self.assertIn("Persistent Body → Brain bridge settings.", BODY_GUI_HTML)
        self.assertIn("void refreshBrainBridgeSettings()", BODY_GUI_HTML)
        self.assertIn("document.getElementById('brain-bridge-save')", BODY_GUI_HTML)

    def test_world_model_exposes_grounded_vlm_scene_visually(self):
        from body_runtime_host.body_gui import BODY_GUI_HTML

        self.assertIn("VLM-grounded spatial scene", BODY_GUI_HTML)
        self.assertIn("semantic-scene-view", BODY_GUI_HTML)
        self.assertIn("semantic-scene-vlm-status", BODY_GUI_HTML)
        self.assertIn("Interpret current scene", BODY_GUI_HTML)
        self.assertIn("renderSemanticScene(w?.perception,w?.sim)", BODY_GUI_HTML)
        self.assertIn("not photogrammetric reconstruction", BODY_GUI_HTML)

    def test_sensorimotor_benchmark_exposes_blind_scene_count_and_paired_metrics(self):
        from body_runtime_host.body_gui import BODY_GUI_HTML

        self.assertIn("sensorimotor-scene-count", BODY_GUI_HTML)
        self.assertIn("new Option(`${count} scene${count===1?'':'s'}`,String(count))", BODY_GUI_HTML)
        self.assertIn("camera_only", BODY_GUI_HTML)
        self.assertIn("camera_plus_sensors", BODY_GUI_HTML)
        self.assertIn("paired_scene_count", BODY_GUI_HTML)

    def test_hardware_inventory_updates_without_replacing_unchanged_rows(self):
        from body_runtime_host.body_gui import BODY_GUI_HTML

        self.assertIn("function setStableHtml(node,html)", BODY_GUI_HTML)
        self.assertIn("fnk-serial-devices", BODY_GUI_HTML)
        self.assertIn("No USB serial adapters detected by this Body host.", BODY_GUI_HTML)
        self.assertIn("(data.modules||[]).filter(m=>m.detected||m.enabled)", BODY_GUI_HTML)


if __name__ == "__main__":
    unittest.main()
