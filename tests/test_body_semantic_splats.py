import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class BodySemanticSplatsTest(unittest.TestCase):
    def test_vlm_semantics_are_sanitized_and_grounded_to_observed_objects(self):
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter
        from body_runtime_host.worldmodel.semantic_splats import build_semantic_splat_scene

        packet = {
            "frame_id": "camera-42",
            "timestamp": 42.0,
            "objects": [
                {"id": "cup-1", "label": "cup", "kind": "target", "position": [1.2, 2.3, 0.0], "size": 0.4},
                {"id": "table-1", "label": "table", "kind": "table", "position": [2.0, 2.0, 0.0], "size": 0.8},
            ],
        }
        semantic = BodySceneInterpreter._ground_interpretation({
            "primary_objects": ["cup"],
            "object_descriptions": [{
                "id": "cup-1",
                "description": "small ceramic drinking vessel",
                "role": "graspable object",
                "confidence": 0.91,
                "image_region": {"x": 0.4, "y": 0.5, "width": 0.1, "height": 0.2},
                "attributes": {"material": "ceramic", "color": "white", "x": 999, "nested": {"bad": True}},
                "relations": [{"type": "on", "target_id": "table-1"}, {"type": "near", "target_id": "invented"}],
            }],
        }, packet)
        semantic["grounding"].update({"accepted_for_context": True, "geometry_authoritative": True})

        result = build_semantic_splat_scene(packet["objects"], semantic, frame_id="camera-42", simulated=True)
        self.assertEqual(result["status"], "ready")
        self.assertTrue(result["preview_only"])
        self.assertFalse(result["safety_authoritative"])
        self.assertEqual(len(result["groups"]), 1)
        group = result["groups"][0]
        self.assertEqual(group["center_m"], [1.2, 2.3, 0.0])
        self.assertEqual(group["attributes"], {"material": "ceramic", "color": "white"})
        self.assertEqual(group["image_region"], {"x": 0.4, "y": 0.5, "width": 0.1, "height": 0.2})
        self.assertEqual(group["relations"], [{"type": "on", "target_id": "table-1"}])
        self.assertEqual(group["confidence"], 0.91)

    def test_stale_or_rejected_semantics_never_create_splats(self):
        from body_runtime_host.worldmodel.semantic_splats import build_semantic_splat_scene

        objects = [{"id": "mug", "position": [0, 0, 0], "size": 0.4}]
        scene = {"frame_id": "old", "grounding": {
            "accepted_for_context": True, "geometry_authoritative": True,
        }, "entities": [{"id": "mug", "description": "mug"}]}
        stale = build_semantic_splat_scene(objects, scene, frame_id="new")
        self.assertEqual(stale["status"], "stale_semantic_frame")
        self.assertEqual(stale["groups"], [])

        scene["frame_id"] = "new"
        scene["grounding"]["accepted_for_context"] = False
        rejected = build_semantic_splat_scene(objects, scene, frame_id="new")
        self.assertEqual(rejected["status"], "grounding_rejected")
        self.assertEqual(rejected["groups"], [])

    def test_malformed_semantic_shapes_are_bounded_and_do_not_raise(self):
        from body_runtime_host.worldmodel.semantic_splats import build_semantic_splat_scene, bind_gaussian_primitives

        malformed = build_semantic_splat_scene(
            None,
            {"frame_id": "f", "grounding": {"accepted_for_context": True,
             "geometry_authoritative": True}, "entities": 7, "primary_object_ids": "cup"},
            frame_id="f",
        )
        self.assertEqual(malformed["status"], "no_grounded_render_groups")
        bindings = bind_gaussian_primitives(
            [{"center_m": [0, 0, 0]}],
            {"groups": [{"center_m": ["bad", 0, 0]}]},
        )
        self.assertEqual(bindings["unbound_count"], 1)

    def test_rebound_geometry_keeps_semantic_provenance_and_drops_stale_image_box(self):
        from body_runtime_host.worldmodel.semantic_splats import build_semantic_splat_scene

        scene = {
            "frame_id": "current-frame",
            "primary_object_ids": ["cup"],
            "grounding": {
                "accepted_for_context": True,
                "geometry_authoritative": True,
                "source_frame_id": "vlm-frame",
                "current_frame_id": "current-frame",
                "same_frame": False,
                "geometry_rebound_to_current_frame": True,
                "semantic_age_seconds": 1.4,
            },
            "entities": [{"id": "cup", "description": "ceramic cup",
                          "image_region": {"x": 0.2, "y": 0.2, "width": 0.1, "height": 0.1}}],
        }
        result = build_semantic_splat_scene(
            [{"id": "cup", "position": [3, 4, 0], "size": 0.4}], scene,
            frame_id="current-frame",
        )
        group = result["groups"][0]
        self.assertIsNone(group["image_region"])
        self.assertEqual(group["semantic_evidence"]["frame_id"], "vlm-frame")
        self.assertEqual(group["geometry_evidence"]["frame_id"], "current-frame")
        self.assertEqual(group["semantic_evidence"]["age_seconds"], 1.4)

    def test_gaussian_primitives_receive_nearest_grounded_semantic_group(self):
        from body_runtime_host.worldmodel.semantic_splats import bind_gaussian_primitives

        bindings = bind_gaussian_primitives([
            {"id": "g1", "center_m": [1.1, 2.0, 0]},
            {"id": "g2", "center_m": [9, 9, 0]},
        ], {"groups": [{
            "group_id": "semantic:cup", "entity_id": "cup", "label": "cup", "kind": "target",
            "center_m": [1, 2, 0], "extent_m": 0.5, "confidence": 0.8,
            "semantic_evidence": {"frame_id": "frame-9"},
        }]})
        self.assertEqual(bindings["bound_count"], 1)
        self.assertEqual(bindings["bound"][0]["semantic_label"], "cup")
        self.assertEqual(bindings["unbound_count"], 1)


if __name__ == "__main__":
    unittest.main()
