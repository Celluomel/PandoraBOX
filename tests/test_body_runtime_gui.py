import unittest


class BodyRuntimeGuiTests(unittest.TestCase):
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
