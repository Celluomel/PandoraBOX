"""Tests for the native camera/LiDAR perception boundary."""
import sys
import types
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class BodyPerceptionModalitiesTest(unittest.TestCase):
    def test_native_lidar_projection_bounds_points_and_reports_truncation(self):
        from types import SimpleNamespace
        from body_runtime_host.worldmodel.perception import sensor_projections

        body = SimpleNamespace(position=[0.0, 0.0, 0.0], orientation=0.0, timestamp=1.0)
        points = [{"x": float(index + 1), "y": 0.0, "z": 0.2} for index in range(5_012)]
        result = sensor_projections(body, [], modalities={
            "lidar": {"native": True, "source": "fixture_lidar", "frame": "world", "points": points},
        })
        self.assertEqual(result["lidar"]["returns"], 5_000)
        self.assertEqual(result["lidar"]["input_returns"], 5_012)
        self.assertTrue(result["lidar"]["points_truncated"])

    def test_scene_interpreter_waits_and_exposes_embedding_configuration(self):
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        interpreter = BodySceneInterpreter({
            "BODY_LLM_ENABLED": True,
            "BODY_LLM_MODEL": "vision-model",
            "BODY_LLM_EMBEDDING_MODEL": "text-embedding-nomic-embed-text-v1.5",
        })
        status = interpreter.status()
        self.assertEqual(status["status"], "waiting")
        self.assertEqual(status["embedding_model"], "text-embedding-nomic-embed-text-v1.5")
        self.assertEqual(status["embedding"]["last_resolution"]["status"], "not_run")
        interpreter.close()

    def test_embedding_probe_matches_only_observed_scene_objects(self):
        import json
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        interpreter = BodySceneInterpreter({
            "BODY_LLM_ENABLED": True,
            "BODY_LLM_BASE_URL": "http://embedding.test/v1",
            "BODY_LLM_EMBEDDING_MODEL": "text-embedding-nomic-embed-text-v1.5",
            "BODY_LLM_EMBEDDING_THRESHOLD": 0.78,
        })
        known = {
            "cup": {"id": "cup", "label": "cup", "kind": "target"},
            "table": {"id": "table", "label": "table", "kind": "table"},
        }

        class Response:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return json.dumps(self.payload).encode()

        def fake_urlopen(request, timeout):
            payload = json.loads(request.data.decode())
            if payload["input"] and payload["input"][0].startswith("search_document: "):
                vectors = [[1.0, 0.0] if "cup" in text else [0.0, 1.0] for text in payload["input"]]
            else:
                vectors = [[0.99, 0.01] for _ in payload["input"]]
                self.assertEqual(payload["input"], ["search_query: mug"])
            return Response({"data": [{"index": i, "embedding": vector} for i, vector in enumerate(vectors)]})

        with patch("body_runtime_host.worldmodel.scene_interpreter.urlopen", side_effect=fake_urlopen):
            result = interpreter.test_embedding_resolution("mug", known)

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["matched_object_id"], "cup")
        self.assertEqual(result["model"], "text-embedding-nomic-embed-text-v1.5")
        self.assertEqual(result["scene_objects"], [
            {"id": "cup", "label": "cup"}, {"id": "table", "label": "table"},
        ])
        self.assertEqual(interpreter.status()["embedding"]["requests"], 2)
        self.assertEqual(interpreter.status()["embedding"]["accepted"], 1)
        interpreter.close()

    def test_local_fastembed_provider_uses_body_model_and_returns_grounded_match(self):
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter, LOCAL_EMBEDDING_MODEL

        class FakeEmbedding:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def embed(self, texts, batch_size):
                return ([1.0, 0.0] if "cup" in text.lower() or "mug" in text.lower() else [0.0, 1.0]
                        for text in texts)

        fake_module = types.ModuleType("fastembed")
        fake_module.TextEmbedding = FakeEmbedding
        interpreter = BodySceneInterpreter({
            "BODY_LLM_EMBEDDING_PROVIDER": "local_fastembed",
            "BODY_LLM_EMBEDDING_MODEL": "text-embedding-nomic-embed-text-v1.5",
            "BODY_LLM_EMBEDDING_THRESHOLD": 0.78,
        })
        known = {
            "cup": {"id": "cup", "label": "cup", "kind": "target"},
            "table": {"id": "table", "label": "table", "kind": "table"},
        }
        with patch.dict(sys.modules, {"fastembed": fake_module}), \
                patch("body_runtime_host.worldmodel.scene_interpreter.importlib.util.find_spec", return_value=object()):
            result = interpreter.test_embedding_resolution("mug", known)
        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"], "local_fastembed")
        self.assertEqual(result["model"], LOCAL_EMBEDDING_MODEL)
        self.assertEqual(result["matched_object_id"], "cup")
        self.assertEqual(interpreter.status()["embedding"]["requests"], 2)
        interpreter.close()

    def test_body_llm_settings_persist_local_embedding_provider(self):
        from body_runtime_host.runtime import BodyHost

        host = BodyHost()
        host.config = {}
        defaults = host.body_llm_settings()
        self.assertEqual(defaults["visual_max_objects"], 5)
        self.assertEqual(defaults["visual_max_tokens"], 128)
        self.assertEqual(defaults["visual_image_max_width"], 640)
        self.assertEqual(defaults["target_latency_s"], 5.0)
        with patch.object(host, "save_config") as save_config:
            result = host.update_body_llm_settings({
                "embedding_provider": "local_fastembed",
                "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "visual_max_objects": 7,
                "visual_max_tokens": 256,
                "visual_image_max_width": 480,
                "target_latency_s": 8,
            })
        save_config.assert_called_once()
        self.assertEqual(host.config["BODY_LLM_EMBEDDING_PROVIDER"], "local_fastembed")
        self.assertEqual(result["settings"]["embedding_provider"], "local_fastembed")
        self.assertEqual(
            result["settings"]["embedding_model"],
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        )
        self.assertEqual(host.config["BODY_LLM_VISUAL_MAX_OBJECTS"], 7)
        self.assertEqual(host.config["BODY_LLM_VISUAL_MAX_TOKENS"], 256)
        self.assertEqual(result["settings"]["visual_max_objects"], 7)
        self.assertEqual(result["settings"]["visual_max_tokens"], 256)
        self.assertEqual(host.config["BODY_LLM_VISUAL_IMAGE_MAX_WIDTH"], 480)
        self.assertEqual(host.config["BODY_LLM_TARGET_LATENCY_S"], 8)
        self.assertEqual(result["settings"]["visual_image_max_width"], 480)
        self.assertEqual(result["settings"]["target_latency_s"], 8)

    def test_vlm_analysis_resize_preserves_original_camera_frame(self):
        import base64
        from types import SimpleNamespace
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        class Frame:
            shape = (480, 640, 3)

        fake_cv2 = types.ModuleType("cv2")
        fake_cv2.IMREAD_COLOR = 1
        fake_cv2.IMWRITE_JPEG_QUALITY = 2
        fake_cv2.INTER_AREA = 3
        fake_cv2.imdecode = lambda *_: Frame()
        fake_cv2.resize = lambda _frame, size, **_kwargs: SimpleNamespace(shape=(size[1], size[0], 3))
        class Encoded:
            def tobytes(self):
                return b"resized-jpeg"
        fake_cv2.imencode = lambda *_: (True, Encoded())
        fake_numpy = types.ModuleType("numpy")
        fake_numpy.uint8 = object()
        fake_numpy.frombuffer = lambda *_args, **_kwargs: b"source-jpeg"
        original = base64.b64encode(b"source-jpeg").decode("ascii")

        with patch.dict(sys.modules, {"cv2": fake_cv2, "numpy": fake_numpy}):
            resized, metadata = BodySceneInterpreter._resize_visual_input(
                original, {"width": 640, "height": 480}, 320
            )

        self.assertEqual(base64.b64decode(resized), b"resized-jpeg")
        self.assertEqual(metadata["original_width"], 640)
        self.assertEqual(metadata["original_height"], 480)
        self.assertEqual(metadata["analysis_width"], 320)
        self.assertEqual(metadata["analysis_height"], 240)
        self.assertTrue(metadata["image_resized_for_vlm"])

    def test_vlm_can_receive_camera_image_and_sensor_packet_together(self):
        import json
        from urllib.request import Request
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        sent = {}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return json.dumps({"choices": [{"message": {"content": json.dumps({
                    "scene_summary": "Obstacle ahead.", "primary_objects": [],
                    "object_descriptions": [], "environment": [], "possible_paths": [],
                    "uncertainty": [],
                })}}]}).encode()

        def fake_urlopen(request, timeout):
            self.assertIsInstance(request, Request)
            sent.update(json.loads(request.data.decode()))
            return Response()

        interpreter = BodySceneInterpreter({
            "BODY_LLM_ENABLED": True, "BODY_LLM_MODEL": "test-vlm",
            "BODY_LLM_BASE_URL": "http://vlm.test/v1",
            "BODY_LLM_VISUAL_IMAGE_MAX_WIDTH": 320,
        })
        packet = {
            "timestamp": 123.0, "frame_id": "paired-frame-1", "visual_blind": True,
            "objects": [{"id": "obstacle", "label": "pillar", "kind": "obstacle",
                         "position": [2.0, 0.0, 0.0]}],
            "body": {"position": [0.0, 0.0, 0.0], "orientation": 0.0},
            "modalities": {
                "camera": {"image_base64": "dGVzdA==", "mime_type": "image/png",
                           "width": 320, "height": 240, "frame_id": "paired-frame-1"},
                "lidar": {"source": "virtual_lidar", "frame": "body", "unit": "m",
                          "frame_id": "paired-frame-1", "timestamp": 123.0,
                          "points": [{"x": 1.5, "y": 0.0, "z": 0.3,
                                      "range": 1.5, "object_id": "must-not-leak"}]},
            },
        }
        try:
            with patch("body_runtime_host.worldmodel.scene_interpreter.urlopen", side_effect=fake_urlopen):
                result = interpreter.interpret_now(packet, visual_options={"include_sensor_context": True})
                self.assertEqual(result["status"], "interpreted")
                self.assertEqual(result["interpretation_mode"], "sensor_packet")
                content = sent["messages"][1]["content"]
                self.assertEqual([part["type"] for part in content], ["text", "image_url"])
                self.assertIn("virtual_lidar", content[0]["text"])
                self.assertIn('"frame":"body"', content[0]["text"])
                self.assertIn('"unit":"m"', content[0]["text"])
                self.assertIn('"x":1.5', content[0]["text"])
                self.assertNotIn("must-not-leak", content[0]["text"])
                visual_only = interpreter.interpret_now(
                    packet, visual_options={"include_sensor_context": False, "bypass_cache": True}
                )
                self.assertEqual(visual_only["interpretation_mode"], "image_only")
                content = sent["messages"][1]["content"]
                self.assertEqual([part["type"] for part in content], ["text", "image_url"])
                self.assertNotIn("virtual_lidar", content[0]["text"])
                self.assertNotIn('"x":1.5', content[0]["text"])
                self.assertNotIn("must-not-leak", content[0]["text"])
        finally:
            interpreter.close()

    def test_open_vocabulary_root_description_is_normalized_and_semantically_grounded(self):
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        packet = {
            "frame_id": "open-vocabulary-frame", "timestamp": 12.0,
            "objects": [{"id": "obstacle", "label": "pillar", "kind": "obstacle",
                         "position": [2.0, 0.0, 0.0]}],
        }
        calls = []

        def resolve(values, known):
            calls.extend(values)
            self.assertIn("obstacle", known)
            return {"purple_cube": "obstacle"}

        scene = BodySceneInterpreter._ground_interpretation(
            {"label": "purple_cube", "visual_description": "A purple cube centered ahead", "confidence": 0.98},
            packet,
            label_resolver=resolve,
        )

        self.assertEqual(scene["primary_object_ids"], [])
        self.assertIn("purple_cube", calls)
        self.assertEqual(scene["grounding"]["valid_described_object_references"], 1)
        self.assertEqual(scene["entities"][0]["description"], "A purple cube centered ahead")
        self.assertEqual(scene["grounding"]["semantic_match_labels"]["purple_cube"], "obstacle")

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
                "lidar": {"native": True, "points": [{"x": 1.0, "y": 2.0, "z": 0.4,
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

    def test_video_depth_proxy_is_not_classified_as_native_lidar(self):
        from body_runtime_host.worldmodel.perception import sensor_projections
        from body_runtime_host.worldmodel.types import BodyState

        projections = sensor_projections(
            BodyState(position=[0, 0, 0]), [],
            modalities={"lidar": {
                "source": "video_lidar_proxy",
                "frame": "body_sensor",
                "points": [{"x": 1.0, "y": 0.0, "z": 0.2}],
            }},
        )
        self.assertEqual(projections["quality"]["lidar"], "derived")
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

    def test_grounding_tolerates_malformed_optional_description_array(self):
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        model = BodySceneInterpreter._ground_interpretation({
            "primary_objects": "cup",
            "object_descriptions": 42,
        }, {"objects": [{"id": "cup", "label": "cup", "kind": "target"}]})
        self.assertEqual(model["primary_object_ids"], ["cup"])
        self.assertEqual(model["grounding"]["described_object_references"], 0)

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

    def test_scene_interpreter_surfaces_provider_http_error_details(self):
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        interpreter = BodySceneInterpreter({
            "BODY_LLM_ENABLED": True,
            "BODY_LLM_MODEL": "qualcomm/Intern3.5-VL-2B:W4A16",
            "BODY_LLM_BASE_URL": "http://127.0.0.1:18181/v1",
        })
        packet = {
            "frame_id": "frame-vision",
            "timestamp": 123.0,
            "objects": [],
            "modalities": {"camera": {"image_base64": "aGVsbG8=", "mime_type": "image/jpeg"}},
        }
        calls = []

        def fake_urlopen(request, timeout):
            calls.append(request.data.decode("utf-8"))
            detail = f"provider detail {len(calls)}"
            raise HTTPError(request.full_url, 400, "bad request", {}, BytesIO(detail.encode()))

        with patch("body_runtime_host.worldmodel.scene_interpreter.urlopen", side_effect=fake_urlopen):
            result = interpreter._interpret(packet)

        self.assertEqual(result["status"], "error")
        self.assertIn("Provider rejected Body request", result["error"])
        self.assertIn("provider detail 1", result["error"])
        self.assertIn("provider detail 2", result["error"])
        self.assertIn("provider detail 3", result["error"])
        self.assertEqual(len(calls), 3)
        interpreter.close()

    def test_scene_interpreter_surfaces_nonretryable_provider_http_errors(self):
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        interpreter = BodySceneInterpreter({
            "BODY_LLM_ENABLED": True,
            "BODY_LLM_MODEL": "qualcomm/Intern3.5-VL-2B:W4A16",
            "BODY_LLM_BASE_URL": "http://127.0.0.1:18181/v1",
        })
        packet = {
            "frame_id": "frame-provider-error",
            "timestamp": 123.0,
            "objects": [],
            "modalities": {"camera": {"image_base64": "aGVsbG8=", "mime_type": "image/jpeg"}},
        }

        def fake_urlopen(request, timeout):
            raise HTTPError(request.full_url, 500, "internal error", {}, BytesIO(b"NPU memory allocation failed"))

        with patch("body_runtime_host.worldmodel.scene_interpreter.urlopen", side_effect=fake_urlopen):
            result = interpreter._interpret(packet)

        self.assertEqual(result["status"], "error")
        self.assertIn("VLM provider HTTP 500", result["error"])
        self.assertIn("NPU memory allocation failed", result["error"])
        interpreter.close()

    def test_scene_interpreter_bounds_multimodal_prompt_for_small_context_models(self):
        import json
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        interpreter = BodySceneInterpreter({
            "BODY_LLM_ENABLED": True,
            "BODY_LLM_MODEL": "qualcomm/Intern3.5-VL-2B:W4A16",
            "BODY_LLM_BASE_URL": "http://127.0.0.1:18181/v1",
            "BODY_LLM_VISUAL_MAX_OBJECTS": 7,
            "BODY_LLM_VISUAL_MAX_TOKENS": 256,
        })
        points = [
            {"x": float(index), "y": 1.0, "z": 0.0, "range_m": float(index + 1),
             "angle_deg": float(index), "object_id": f"object-{index}", "debug_payload": "x" * 300}
            for index in range(200)
        ]
        packet = {
            "frame_id": "compact-frame",
            "timestamp": 123.0,
            "source": "sensor",
            "body": {"position": [0, 0, 0], "orientation": 0, "unused": "x" * 1000},
            "objects": [{"id": "cup", "label": "cup", "kind": "target", "props": "x" * 1000}],
            "modalities": {
                "camera": {"image_base64": "aGVsbG8=", "mime_type": "image/jpeg", "unused": "x" * 1000},
                "lidar": {"points": points, "unused": "x" * 1000},
                "vision_projection": {"objects": ["x" * 1000] * 100},
                "fusion": {"associations": ["x" * 1000] * 100},
            },
            "sensor_fusion": {"unused": "x" * 1000},
        }

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return b'{"choices":[{"message":{"content":"{\\"scene_summary\\":\\"scene\\"}"}}]}'

        calls = []

        def fake_urlopen(request, timeout):
            calls.append(json.loads(request.data.decode("utf-8")))
            return Response()

        with patch("body_runtime_host.worldmodel.scene_interpreter.urlopen", side_effect=fake_urlopen):
            result = interpreter._interpret(packet)

        prompt = calls[0]["messages"][1]["content"][0]["text"]
        self.assertEqual(result["status"], "interpreted")
        self.assertLess(len(prompt), 6000)
        self.assertIn("up to 7 salient objects clearly visible", prompt)
        self.assertIn("object_descriptions (up to 7 objects", prompt)
        self.assertNotIn("compact-frame", prompt)
        self.assertNotIn('"cup"', prompt)
        self.assertNotIn("lidar", prompt.lower())
        self.assertNotIn("vision_projection", prompt)
        self.assertNotIn("debug_payload", prompt)
        self.assertTrue(any(part.get("type") == "image_url" for part in calls[0]["messages"][1]["content"]))
        self.assertEqual(calls[0]["max_tokens"], 256)
        interpreter.close()

    def test_scene_interpreter_reuses_image_semantics_but_regrounds_fresh_geometry(self):
        import json
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        interpreter = BodySceneInterpreter({
            "BODY_LLM_ENABLED": True,
            "BODY_LLM_MODEL": "qualcomm/Intern3.5-VL-2B:W4A16",
            "BODY_LLM_BASE_URL": "http://127.0.0.1:18181/v1",
        })

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return b'{"choices":[{"message":{"content":"{\\"primary_objects\\":[\\"cup\\"],\\"object_descriptions\\":[{\\"label\\":\\"cup\\",\\"description\\":\\"small handled vessel\\",\\"confidence\\":0.9}]}"}}]}'

        calls = []

        def fake_urlopen(request, timeout):
            calls.append(json.loads(request.data.decode("utf-8")))
            return Response()

        camera = {"image_base64": "same-frame-image", "mime_type": "image/jpeg", "camera_profile": "low_body_front"}
        first = {
            "frame_id": "frame-1", "timestamp": 1,
            "objects": [{"id": "cup", "label": "cup", "kind": "target", "position": [1, 2, 0]}],
            "modalities": {"camera": dict(camera)},
        }
        second = {
            "frame_id": "frame-2", "timestamp": 2,
            "objects": [{"id": "cup", "label": "cup", "kind": "target", "position": [8, 9, 0]}],
            "modalities": {"camera": dict(camera)},
        }
        with patch("body_runtime_host.worldmodel.scene_interpreter.urlopen", side_effect=fake_urlopen):
            result1 = interpreter._interpret(first)
            result2 = interpreter._interpret(second)

        self.assertEqual(result1["status"], "interpreted")
        self.assertEqual(result2["status"], "interpreted")
        self.assertEqual(len(calls), 1)
        self.assertEqual(result1["semantic_scene"]["entities"][0]["position"], [1.0, 2.0, 0.0])
        self.assertEqual(result2["semantic_scene"]["entities"][0]["position"], [8.0, 9.0, 0.0])
        self.assertEqual(interpreter.status()["visual_cache"], {"hits": 1, "misses": 1, "entries": 1})
        interpreter.close()

    def test_multimodal_prompt_requires_structured_descriptions_for_named_objects(self):
        import json
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        interpreter = BodySceneInterpreter({
            "BODY_LLM_ENABLED": True,
            "BODY_LLM_MODEL": "qualcomm/Qwen3-VL-4B-Instruct:W4A16",
            "BODY_LLM_BASE_URL": "http://127.0.0.1:18181/v1",
        })

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return b'{"choices":[{"message":{"content":"{\\"scene_summary\\":\\"A purple cube is ahead.\\",\\"primary_objects\\":[\\"purple cube\\"],\\"object_descriptions\\":[{\\"label\\":\\"purple cube\\",\\"description\\":\\"A purple cube on the floor\\",\\"confidence\\":0.9}]}"}}]}'

        calls = []

        def fake_urlopen(request, timeout):
            calls.append(json.loads(request.data.decode("utf-8")))
            return Response()

        packet = {
            "frame_id": "paired-frame",
            "timestamp": 123.0,
            "objects": [],
            "modalities": {
                "camera": {"image_base64": "aGVsbG8=", "mime_type": "image/jpeg"},
                "lidar": {"points": [{"x": 1.0, "y": 0.2, "z": 0.0, "range_m": 1.02}]},
            },
        }
        with patch("body_runtime_host.worldmodel.scene_interpreter.urlopen", side_effect=fake_urlopen):
            result = interpreter._interpret(packet, visual_options={"include_sensor_context": True})

        prompt = calls[0]["messages"][1]["content"][0]["text"]
        self.assertIn("Every concrete object named in scene_summary must also appear in object_descriptions", prompt)
        self.assertIn("Use free-form labels grounded in the image, not a fixed category list", prompt)
        self.assertIn("support proximity or obstacle relevance", prompt)
        self.assertEqual(result["status"], "interpreted")
        self.assertEqual(result["interpretation"]["object_descriptions"][0]["label"], "purple cube")
        interpreter.close()

    def test_qnn_model_load_error_has_payload_independent_diagnosis(self):
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        result = BodySceneInterpreter({"BODY_LLM_MODEL": "qualcomm/Intern3.5-VL-2B:W4A16"})._error(
            'VLM provider HTTP 500: {"code":-100201,"error":"SDKError(Model loading failed)"}'
        )
        self.assertEqual(result["diagnosis"]["code"], "qnn_model_load_failed")
        self.assertFalse(result["diagnosis"]["payload_related"])
        self.assertIn("CMA", result["diagnosis"]["checks"][0])

    def test_qnn_model_load_failure_uses_short_circuit_cooldown(self):
        from body_runtime_host.worldmodel.scene_interpreter import BodySceneInterpreter

        interpreter = BodySceneInterpreter({
            "BODY_LLM_ENABLED": True,
            "BODY_LLM_MODEL": "qualcomm/Intern3.5-VL-2B:W4A16",
            "BODY_LLM_BASE_URL": "http://127.0.0.1:18181/v1",
        })
        packet = {
            "frame_id": "qnn-fail",
            "objects": [],
            "modalities": {"camera": {"image_base64": "image", "mime_type": "image/jpeg"}},
        }
        calls = []

        def fail_load(request, timeout):
            calls.append(request)
            raise HTTPError(
                request.full_url, 500, "model load failed", {},
                BytesIO(b'{"code":-100201,"error":"SDKError(Model loading failed)"}'),
            )

        with patch("body_runtime_host.worldmodel.scene_interpreter.urlopen", side_effect=fail_load):
            first = interpreter._interpret(packet)
            second = interpreter._interpret(packet)

        self.assertEqual(first["diagnosis"]["code"], "qnn_model_load_failed")
        self.assertEqual(second["diagnosis"]["code"], "qnn_model_load_failed")
        self.assertIn("retry suppressed", second["error"])
        self.assertEqual(len(calls), 1)
        self.assertGreater(interpreter.status()["provider_cooldown_seconds"], 0)
        interpreter.close()

    def test_body_vlm_test_identifies_observation_stage_failures(self):
        from body_runtime_host.runtime import BodyHost

        class Source:
            def observe(self):
                raise RuntimeError("HTTP Error 400: bad request")

        class WorldModel:
            source = Source()

        host = BodyHost.__new__(BodyHost)
        host._worldmodel = WorldModel()
        result = host.test_body_vlm()

        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "observe")
        self.assertIn("HTTP Error 400", result["error"])

    def test_body_vlm_diagnostic_runs_as_pollable_background_job(self):
        import threading
        import time
        from body_runtime_host.runtime import BodyHost

        host = BodyHost.__new__(BodyHost)
        host._body_vlm_test_lock = threading.Lock()
        host._body_vlm_test_status = {"status": "idle", "job_id": None}
        gate = threading.Event()

        def fake_test():
            gate.wait(1)
            return {"ok": True, "stage": "complete", "model": "test-vlm"}

        host.test_body_vlm = fake_test
        started = host.start_body_vlm_test()
        self.assertEqual(started["status"], "running")
        self.assertIsNotNone(started["job_id"])
        gate.set()
        deadline = time.monotonic() + 1
        while host.body_vlm_test_status()["status"] == "running" and time.monotonic() < deadline:
            time.sleep(0.01)
        completed = host.body_vlm_test_status()
        self.assertEqual(completed["status"], "completed")
        self.assertTrue(completed["ok"])
        self.assertGreaterEqual(completed["latency_ms"], 0)

    def test_vlm_profile_benchmark_compares_one_frame_without_saving_settings(self):
        import threading
        import time
        from body_runtime_host.runtime import BodyHost

        class Source:
            def observe(self):
                return {"frame": "same"}

            def body_state(self):
                return {"position": [0, 0, 0]}

        class Interpreter:
            def __init__(self):
                self.calls = []

            def interpret_now(self, packet, *, visual_options):
                self.calls.append((packet, visual_options["image_max_width"]))
                time.sleep({640: 0.003, 480: 0.002, 320: 0.001}[visual_options["image_max_width"]])
                return {
                    "status": "interpreted", "latency_ms": 1,
                    "interpretation": {
                        "scene_summary": "Table and cup visible",
                        "object_descriptions": [{"label": "table"}, {"label": "cup"}],
                    },
                }

        interpreter = Interpreter()
        class WorldModel:
            source = Source()
            scene_interpreter = interpreter

            @staticmethod
            def _scene_packet(*args):
                return {"modalities": {"camera": {"image_base64": "image"}}}

        host = BodyHost.__new__(BodyHost)
        host._worldmodel = WorldModel()
        host._worldmodel_lock = threading.Lock()
        host._body_vlm_test_lock = threading.Lock()
        host._body_vlm_test_status = {"status": "running"}
        host.config = {"BODY_LLM_TARGET_LATENCY_S": 1.0}
        host.value = lambda key, default=None: host.config.get(key, default)
        host.body_llm_settings = lambda: {"model": "test-vlm", "visual_max_objects": 5, "visual_max_tokens": 128}

        result = host.benchmark_body_vlm_profiles()

        self.assertTrue(result["ok"])
        self.assertEqual([width for _, width in interpreter.calls], [640, 480, 320])
        self.assertEqual(len({id(packet) for packet, _ in interpreter.calls}), 1)
        self.assertEqual(result["recommendation"]["image_max_width"], 320)
        self.assertTrue(result["target_met"])
        self.assertFalse(result["saved_settings_changed"])


if __name__ == "__main__":
    unittest.main()
