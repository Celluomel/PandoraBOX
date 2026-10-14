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
        self.assertIn("#map[hidden]{display:none!important}", source)
        self.assertIn("sim?.resize(); buildSimulation(latestWorld); sim?.render()", source)
        self.assertIn("depth_gray_jpeg_base64", source)
        self.assertIn("no simulation object positions", source)

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
