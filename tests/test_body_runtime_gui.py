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
        self.assertIn("Interpret current scene", BODY_GUI_HTML)
        self.assertIn("renderSemanticScene(w?.perception,w?.sim)", BODY_GUI_HTML)
        self.assertIn("not photogrammetric reconstruction", BODY_GUI_HTML)


if __name__ == "__main__":
    unittest.main()
