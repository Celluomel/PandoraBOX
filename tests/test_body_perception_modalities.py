"""Tests for the native camera/LiDAR perception boundary."""
import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class BodyPerceptionModalitiesTest(unittest.TestCase):
    def test_native_modalities_are_preferred_and_provenanced(self):
        from body_runtime_host.worldmodel.perception import sensor_projections
        from body_runtime_host.worldmodel.types import BodyState, SceneObject

        body = BodyState(position=[1, 2, 0], timestamp=100.0)
        projections = sensor_projections(
            body,
            [SceneObject(id="fallback", label="fallback", position=[9, 9, 0])],
            modalities={
                "frame_id": "camera-lidar-7",
                "camera": {"objects": [{
                    "id": "cup", "label": "cup", "kind": "target",
                    "position": [2, 3, 0], "size": 0.4,
                }]},
                "lidar": {"points": [{"x": 1.0, "y": 2.0, "z": 0.4,
                                           "intensity": 0.9, "object_id": "cup"}]},
            },
        )

        self.assertEqual(projections["frame"]["frame_id"], "camera-lidar-7")
        self.assertEqual(projections["quality"], {
            "camera": "native", "lidar": "native", "authoritative_geometry": "world_model",
        })
        self.assertEqual(projections["vision_projection"]["source"], "native_camera")
        self.assertEqual(projections["vision_projection"]["objects"][0]["id"], "cup")
        self.assertEqual(projections["lidar"]["source"], "native_lidar")
        self.assertEqual(projections["lidar"]["returns"], 1)

    def test_simulation_is_explicitly_marked_derived(self):
        from body_runtime_host.worldmodel.perception import sensor_projections
        from body_runtime_host.worldmodel.types import BodyState, SceneObject

        projections = sensor_projections(
            BodyState(position=[0, 0, 0]),
            [SceneObject(id="table", label="table", kind="table", position=[2, 0, 0])],
        )
        self.assertEqual(projections["quality"]["camera"], "derived")
        self.assertEqual(projections["quality"]["lidar"], "derived")
        self.assertFalse(projections["vision_projection"]["native"])
        self.assertFalse(projections["lidar"]["native"])

    def test_camera_and_lidar_are_fused_by_category_and_geometry(self):
        from body_runtime_host.worldmodel.perception import sensor_projections
        from body_runtime_host.worldmodel.types import BodyState, SceneObject

        projections = sensor_projections(
            BodyState(position=[0, 0, 0], orientation=0.0),
            [],
            modalities={
                "camera": {"objects": [{
                    "id": "visual-mug", "label": "mug", "kind": "object",
                    "position": [2.0, 0.05, 0], "size": 0.4,
                }]},
                "lidar": {
                    "frame": "body_world",
                    "points": [
                        {"x": 2.0, "y": 0.05, "z": 0.3, "object_id": "cup"},
                        {"x": 6.0, "y": 4.0, "z": 0.2, "object_id": "table"},
                    ],
                },
            },
        )

        fusion = projections["fusion"]
        self.assertEqual(fusion["matched"], 1)
        self.assertEqual(fusion["associations"][0]["category"], "cup")
        self.assertEqual(fusion["associations"][0]["lidar_point_indices"], [0])
        self.assertEqual(fusion["unmatched_lidar_point_indices"], [1])
        self.assertEqual(projections["lidar"]["vertical_layers"], 2)

    def test_body_perception_frame_v2_keeps_modalities_synchronized(self):
        from body_runtime_host.worldmodel.perception import build_body_perception_frame
        from body_runtime_host.worldmodel.types import BodyState, Observation, SceneObject

        body = BodyState(
            position=[1.0, 2.0, 0.0], orientation=0.25, timestamp=100.0,
            coordinate_frame="local_map", position_source="odometry",
        )
        observation = Observation(
            timestamp=100.0,
            scene=[SceneObject(id="cup", label="cup", kind="target", position=[2.0, 3.0, 0.0])],
            modalities={
                "frame_id": "frame-v2",
                "camera": {
                    "image_base64": "aGVsbG8=", "mime_type": "image/png",
                    "timestamp": 100.0,
                    "calibration": {"profile": "level_body_front"},
                },
                "lidar": {
                    "timestamp": 100.0, "frame": "body_world",
                    "points": [{"x": 2.0, "y": 3.0, "z": 0.3, "object_id": "cup"}],
                },
            },
        )
        frame = build_body_perception_frame(
            body, observation,
            motion={"speed": 0.4, "relative_speed": 0.5, "angular_speed": 0.1},
        )

        self.assertEqual(frame["contract"], "body_perception_frame.v2")
        self.assertEqual(frame["frame_id"], "frame-v2")
        self.assertTrue(frame["synchronization"]["synchronized"])
        self.assertEqual(frame["camera"]["image_base64"], "aGVsbG8=")
        self.assertEqual(frame["lidar"]["quality"]["returns"], 1)
        self.assertIn("position_m", frame["body"]["pose"])
        self.assertEqual(frame["metric_frame"]["length_unit"], "m")
        self.assertIn("items", frame["associations"])
        self.assertIn("camera", frame["uncertainty"])

    def test_fusion_reports_visual_detection_without_inventing_geometry(self):
        from body_runtime_host.worldmodel.perception import sensor_projections
        from body_runtime_host.worldmodel.types import BodyState

        projections = sensor_projections(
            BodyState(position=[0, 0, 0], orientation=0.0), [],
            modalities={
                "camera": {"objects": [{
                    "id": "chair", "label": "chair", "kind": "chair",
                    "position": [2.0, 0.0, 0], "size": 0.8,
                }]},
                "lidar": {"frame": "body_world", "points": [
                    {"x": 8.0, "y": 4.0, "z": 0.2, "object_id": "table"},
                ]},
            },
        )

        fusion = projections["fusion"]
        self.assertEqual(fusion["matched"], 0)
        self.assertEqual(fusion["unmatched_vision"], ["chair"])
        self.assertEqual(fusion["unmatched_lidar_point_indices"], [0])

    def test_virtual_camera_emits_real_image_payload(self):
        from body_runtime_host.worldmodel.sim_world import SimulatedRoom

        observation = SimulatedRoom().observe()
        camera = observation.modalities["camera"]
        self.assertEqual(camera["source"], "virtual_camera")
        self.assertEqual(camera["mime_type"], "image/png")
        self.assertEqual(camera["depth_mime_type"], "image/png")
        self.assertEqual(camera["calibration"]["projection"], "pinhole_egocentric")
        self.assertEqual(camera["calibration"]["mount"], "low_body_front")
        self.assertTrue(camera["calibration"]["floor_biased_view"])
        self.assertGreater(len(camera["image_base64"]), 200)
        self.assertGreater(len(camera["depth_base64"]), 200)
        self.assertTrue(camera["image_base64"].startswith("iVBOR"))

    def test_virtual_camera_supports_calibrated_view_profiles(self):
        from body_runtime_host.worldmodel.sim_world import SimulatedRoom
        from body_runtime_host.worldmodel.virtual_camera import render_camera

        room = SimulatedRoom()
        body = room.body_state()
        low = render_camera(body, room._scene(), width=160, height=120, profile="low_body_front")
        high = render_camera(body, room._scene(), width=160, height=120, profile="high_body_front")
        self.assertEqual(low["camera_profile"], "low_body_front")
        self.assertEqual(high["camera_profile"], "high_body_front")
        self.assertNotEqual(low["calibration"]["height_m"], high["calibration"]["height_m"])

    def test_camera_capture_is_rate_limited_without_freezing_body_observation(self):
        from body_runtime_host.worldmodel.sources import SimRobotSource

        source = SimRobotSource(camera_interval=60.0)
        first = source.observe()
        second = source.observe()
        self.assertIn("camera", first.modalities)
        self.assertIn("camera", second.modalities)
        self.assertGreaterEqual(float(second.modalities["camera"].get("stale_age_s", 0.0)), 0.0)
        self.assertEqual(first.scene[0].position, second.scene[0].position)

    def test_virtual_lidar_is_occlusion_aware_and_marked_virtual(self):
        from body_runtime_host.worldmodel.sim_world import SimulatedRoom
        from body_runtime_host.worldmodel.perception import sensor_projections

        observation = SimulatedRoom().observe()
        projections = sensor_projections(
            SimulatedRoom().body_state(), observation.scene, modalities=observation.modalities,
        )
        self.assertGreater(projections["lidar"]["returns"], 0)
        self.assertEqual(projections["quality"]["lidar"], "virtual")
        self.assertTrue(all("range" not in point or point["range"] > 0 for point in projections["lidar"]["points"]))

    def test_video_lidar_proxy_is_explicitly_estimated_and_metric(self):
        from body_runtime_host.worldmodel.video_lidar import estimate_lidar_from_frame

        points = estimate_lidar_from_frame(
            bytes(range(256)) * 20,
            width=64, height=40, columns=8, rows=3,
        )
        self.assertEqual(len(points), 24)
        self.assertTrue(all(item["source"] == "video_lidar_proxy" for item in points))
        self.assertTrue(all(item["range"] > 0 for item in points))
        self.assertTrue(all("x" in item and "y" in item and "z" in item for item in points))

    def test_video_lidar_png_dimensions_are_validated(self):
        from body_runtime_host.worldmodel.video_lidar import _png_dimensions

        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8 + (320).to_bytes(4, "big") + (240).to_bytes(4, "big")
        self.assertEqual(_png_dimensions(png), (320, 240))

    def test_video_replay_capture_size_has_640x480_floor(self):
        from body_runtime_host.worldmodel.video_lidar import _capture_dimensions

        self.assertEqual(_capture_dimensions(1280, 720), (1280, 720))
        self.assertEqual(_capture_dimensions(640, 480), (640, 480))
        with self.assertRaises(ValueError):
            _capture_dimensions(639, 480)
        with self.assertRaises(ValueError):
            _capture_dimensions(640, 479)

    def test_llm_semantics_are_grounded_to_observed_entities(self):
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        packet = {
            "frame_id": "frame-1",
            "timestamp": 123.0,
            "objects": [{"id": "cup", "label": "cup", "kind": "target", "position": [2, 3, 0]}],
        }
        model = BodySceneInterpreter._ground_interpretation({
            "primary_objects": ["cup", "invented"],
            "object_descriptions": [
                {"id": "cup", "description": "small vessel", "role": "graspable", "affordances": ["grab"]},
                {"id": "invented", "description": "hallucination"},
            ],
            "possible_paths": [
                {"action": "forward", "reason": "clear"},
                {"action": "fly", "reason": "not a Body capability"},
            ],
        }, packet)

        self.assertEqual(model["primary_object_ids"], ["cup"])
        self.assertEqual(len(model["entities"]), 1)
        self.assertEqual(model["entities"][0]["description"], "small vessel")
        self.assertEqual([item["action"] for item in model["possible_paths"]], ["forward"])
        self.assertEqual(model["geometry_source"], "sensor_projections")
        self.assertTrue(model["grounding"]["geometry_authoritative"])
        self.assertFalse(model["grounding"]["accepted_for_context"])

    def test_grounding_threshold_accepts_fully_observed_references(self):
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        packet = {
            "frame_id": "frame-2",
            "timestamp": 124.0,
            "objects": [{"id": "cup", "label": "cup", "kind": "target", "position": [2, 3, 0]}],
        }
        model = BodySceneInterpreter._ground_interpretation({
            "primary_objects": ["cup"],
            "object_descriptions": [{"id": "cup", "description": "small vessel"}],
        }, packet)
        # The pure grounding function remains deterministic; acceptance is
        # assigned by the configured interpreter threshold after the LLM call.
        self.assertEqual(model["grounding"]["reference_precision"], 1.0)
        self.assertFalse(model["grounding"]["accepted_for_context"])

    def test_grounding_resolves_semantic_labels_in_visual_blind_mode(self):
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        model = BodySceneInterpreter._ground_interpretation({
            "primary_objects": ["cup"],
            "object_descriptions": [{"label": "table", "description": "a surface"}],
        }, {
            "objects": [
                {"id": "cup", "label": "cup", "kind": "target"},
                {"id": "table", "label": "table", "kind": "table"},
            ]
        })

        self.assertEqual(model["primary_object_ids"], ["cup"])
        self.assertEqual(model["entities"][1]["description"], "a surface")
        self.assertEqual(model["grounding"]["reference_precision"], 1.0)

    def test_grounding_normalizes_sensor_semantic_aliases(self):
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        model = BodySceneInterpreter._ground_interpretation({
            "primary_objects": ["mug", "pillar"],
            "object_descriptions": [
                {"label": "column", "description": "vertical obstacle"},
            ],
        }, {
            "objects": [
                {"id": "cup", "label": "cup", "kind": "target"},
                {"id": "obstacle", "label": "pillar", "kind": "obstacle"},
            ],
            "sensor_fusion": {"matched": 2, "lidar_returns": 8, "method": "category_range_bearing"},
        })

        self.assertEqual(model["primary_object_ids"], ["cup", "obstacle"])
        self.assertEqual(model["entities"][1]["description"], "vertical obstacle")
        self.assertEqual(model["sensor_fusion"]["matched"], 2)

    def test_grounding_can_use_bounded_semantic_resolver_for_unknown_label(self):
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        model = BodySceneInterpreter._ground_interpretation({
            "primary_objects": ["drinking vessel"],
            "object_descriptions": [{"label": "vertical column", "description": "hazard"}],
        }, {
            "objects": [
                {"id": "cup", "label": "cup", "kind": "target"},
                {"id": "obstacle", "label": "pillar", "kind": "obstacle"},
            ]
        }, lambda values, known: {
            "drinking vessel": "cup",
            "vertical column": "obstacle",
        })

        self.assertEqual(model["primary_object_ids"], ["cup"])
        self.assertEqual(model["entities"][1]["description"], "hazard")
        self.assertEqual(model["grounding"]["semantic_matches"], 2)
        self.assertEqual(model["grounding"]["invented_object_references"], 0)

    def test_body_llm_prompt_uses_camera_calibration_profile(self):
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        low = BodySceneInterpreter._camera_view_note({
            "camera_profile": "low_body_front",
            "calibration": {"height_m": 0.18, "elevation_deg": -8.0,
                            "foreground_occluders": ["legs"]},
        })
        level = BodySceneInterpreter._camera_view_note({
            "camera_profile": "level_body_front",
            "calibration": {"height_m": 0.35, "elevation_deg": -2.0},
        })
        high = BodySceneInterpreter._camera_view_note({
            "camera_profile": "high_body_front",
            "calibration": {"height_m": 0.65, "elevation_deg": 5.0},
        })
        self.assertIn("low floor-biased perspective", low)
        self.assertIn("intermediate perspective", level)
        self.assertIn("high perspective", high)
        self.assertIn("chassis/legs", low)

    def test_scene_interpreter_retries_text_only_for_instruct_model(self):
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        interpreter = BodySceneInterpreter({
            "BODY_LLM_ENABLED": True,
            "BODY_LLM_MODEL": "qwen/qwen2.5-3b-instruct",
            "BODY_LLM_BASE_URL": "http://127.0.0.1:1234/v1",
        })
        packet = {
            "frame_id": "frame-vision",
            "timestamp": 123.0,
            "objects": [{"id": "cup", "label": "cup", "kind": "target", "position": [2, 3, 0]}],
            "modalities": {"camera": {"image_base64": "aGVsbG8=", "mime_type": "image/png"}},
        }

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return b'{"choices":[{"message":{"content":"{\\"primary_objects\\":[\\"cup\\"]}"}}]}'

        calls = []

        def fake_urlopen(request, timeout):
            calls.append(request.data.decode("utf-8"))
            if len(calls) < 3:
                raise HTTPError(request.full_url, 400, "unsupported request", {}, BytesIO(b"bad request"))
            return Response()

        with patch("body_runtime_host.worldmodel.scene_interpreter.urlopen", side_effect=fake_urlopen):
            result = interpreter._interpret(packet)

        self.assertEqual(result["status"], "interpreted")
        self.assertEqual(len(calls), 3)
        self.assertEqual(__import__("json").loads(calls[0])["response_format"], {"type": "json_object"})
        self.assertIn("image_url", calls[0])
        self.assertNotIn("response_format", calls[1])
        self.assertNotIn("image_url", calls[2])
        interpreter.close()


if __name__ == "__main__":
    unittest.main()
