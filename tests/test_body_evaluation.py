import unittest
from unittest.mock import patch

from body_runtime_host.worldmodel.evaluation import (
    _restart_resume_probe,
    collect_body_llm_grounding,
    run_vlm_sensorimotor_scenario,
    run_vlm_sensorimotor_suite,
    run_shuffled_trials,
)


class BodyEvaluationTests(unittest.TestCase):
    def test_restart_resume_probe_restores_next_step_and_lease(self):
        result = _restart_resume_probe()

        self.assertTrue(result["passed"], result)
        self.assertEqual(result["current_step_index"], 1)
        self.assertEqual(result["next_step"], "wait")
        self.assertTrue(result["single_lease_enforced"])

    def test_generic_plan_survives_shuffled_scenes(self):
        result = run_shuffled_trials(trials=5, max_steps=180)

        self.assertEqual(result["trials"], 5)
        self.assertEqual(result["successes"], 5)
        self.assertEqual(result["collisions"], 0)
        self.assertIn("near_misses", result)
        self.assertIn("avg_detour_distance", result)
        self.assertIn("detour_action_counts", result)
        self.assertIn("avg_decision_time_ms", result)
        self.assertIn("time_cost_vs_baseline_steps", result)
        self.assertIn("detour_distance_cost_vs_baseline", result)
        self.assertIn("near_misses", result["baseline_without_recovery"])
        self.assertIn("learning", result)
        self.assertGreater(result["learning"]["final"]["transitions"], 0)
        self.assertIn("capability_gate", result)
        self.assertEqual(result["capability_gate"]["state"], "TESTING")
        self.assertFalse(result["capability_gate"]["criteria"]["randomized_trials"]["passed"])
        self.assertIn("restart_resume", result["capability_gate"]["pending_gates"])
        self.assertTrue(result["restart_resume_probe"]["passed"])
        self.assertTrue(all(item["success"] for item in result["results"]))

    def test_grounding_collection_passes_deterministic_camera_image(self):
        captured = []

        def fake_interpret(_interpreter, packet):
            captured.append(packet)
            return {
                "status": "interpreted",
                "semantic_scene": {
                    "grounding": {
                        "reference_precision": 1.0,
                        "accepted_for_context": True,
                        "geometry_authoritative": True,
                        "primary_object_references": 1,
                        "valid_primary_object_references": 1,
                    }
                },
            }

        with patch(
            "body_runtime_host.worldmodel.evaluation.BodySceneInterpreter._interpret",
            new=fake_interpret,
        ):
            result = collect_body_llm_grounding(
                1,
                {
                    "BODY_LLM_ENABLED": True,
                    "BODY_LLM_MODEL": "qwen2.5-vl-3b-instruct",
                },
                seeds=[7],
            )

        self.assertEqual(result["accepted"], 1)
        self.assertEqual(len(captured), 1)
        packet = captured[0]
        camera = packet["modalities"]["camera"]
        self.assertTrue(packet["visual_blind"])
        self.assertEqual(camera["frame_id"], packet["frame_id"])
        self.assertEqual(camera["validation"], "deterministic_scene_fixture")
        self.assertTrue(camera["image_base64"].startswith("iVBOR"))
        self.assertGreater(len(camera["image_base64"]), 200)

    def test_sensorimotor_scenario_pairs_vlm_frames_and_moves_without_collisions(self):
        captured = []

        def fake_interpret(_interpreter, packet, *, visual_options=None):
            captured.append((packet, visual_options))
            frame_id = packet["frame_id"]
            target = next(item for item in packet["objects"] if item["id"] == "target")
            return {
                "status": "interpreted",
                "interpretation_mode": "sensor_packet" if visual_options["include_sensor_context"] else "image_only",
                "latency_ms": 12.5,
                "interpretation": {
                    "scene_summary": "A clear route bends around an obstacle.",
                    "object_descriptions": [{"label": "purple cube", "description": "A purple cube on the floor.", "role": "goal"}],
                },
                "semantic_scene": {
                    "frame_id": frame_id,
                    "entities": [{
                        "id": "target", "semantic_label": "purple cube",
                        "description": "A purple cube on the floor.", "role": "goal",
                        "position": target["position"], "size": target["size"],
                    }],
                    "grounding": {
                        "frame_id": frame_id, "reference_precision": 1.0,
                        "accepted_for_context": True, "geometry_authoritative": True,
                    },
                },
            }

        with patch("body_runtime_host.worldmodel.evaluation.BodySceneInterpreter.interpret_now", new=fake_interpret), \
                patch("body_runtime_host.worldmodel.evaluation.BodySceneInterpreter._semantic_reference_resolver",
                      return_value={"purple cube": "target"}):
            result = run_vlm_sensorimotor_scenario({
                "BODY_LLM_ENABLED": True,
                "BODY_LLM_MODEL": "test-vlm",
                "BODY_LLM_VISUAL_IMAGE_MAX_WIDTH": 640,
            })

        self.assertEqual(result["status"], "completed", result)
        self.assertEqual(result["execution"], "simulation_only")
        self.assertFalse(result["physical_actuation"])
        self.assertEqual(result["collisions"], 0)
        self.assertTrue(result["vlm_multimodal"])
        self.assertEqual(result["vlm_calls"], 2)
        self.assertGreater(result["actions"], 0)
        self.assertEqual(len(captured), 2)
        self.assertEqual([item["stage"] for item in result["snapshots"]], ["camera_only", "camera_plus_sensors"])
        self.assertEqual(result["snapshots"][0]["frame_id"], result["snapshots"][1]["frame_id"])
        self.assertEqual(result["snapshots"][0]["timestamp"], result["snapshots"][1]["timestamp"])
        self.assertEqual(captured[0][0]["objects"][0]["label"], "purple cube")
        self.assertEqual(result["snapshots"][0]["vlm_mode"], "image_only")
        self.assertEqual(result["snapshots"][1]["vlm_mode"], "sensor_packet")
        self.assertEqual(result["snapshots"][0]["vlm_interpretation"]["object_descriptions"][0]["label"], "purple cube")
        self.assertEqual(result["snapshots"][0]["sensor_packet"]["lidar"]["points_sent_to_vlm"], [])
        self.assertGreater(len(result["snapshots"][1]["sensor_packet"]["lidar"]["points_sent_to_vlm"]), 0)
        self.assertTrue(result["modality_comparison"]["same_frame_id"])
        self.assertTrue(result["modality_comparison"]["same_timestamp"])
        self.assertTrue(result["modality_comparison"]["movement_uses_vlm_output"])
        self.assertEqual(result["autonomy"]["target_id"], "target")
        self.assertEqual(result["autonomy"]["target_semantic_label"], "purple cube")
        self.assertGreaterEqual(result["autonomy"]["target_clearance_m"], result["autonomy"]["minimum_clearance_m"])
        first_sensor_packet = result["snapshots"][0]["sensor_packet"]
        self.assertEqual(first_sensor_packet["frame_id"], result["snapshots"][0]["frame_id"])
        self.assertEqual(first_sensor_packet["timestamp"], result["snapshots"][0]["timestamp"])
        self.assertTrue(first_sensor_packet["camera"]["image_attached"])
        self.assertEqual(first_sensor_packet["lidar"]["points_sent_to_vlm"], [])
        for packet, options in captured:
            self.assertTrue(packet["visual_blind"])
            self.assertEqual(packet["modalities"]["camera"]["frame_id"], packet["frame_id"])
            self.assertEqual(packet["modalities"]["lidar"]["frame_id"], packet["frame_id"])
            self.assertEqual(packet["modalities"]["camera"]["timestamp"], packet["timestamp"])
            self.assertEqual(packet["modalities"]["lidar"]["timestamp"], packet["timestamp"])
            self.assertGreater(len(packet["modalities"]["lidar"]["points"]), 0)
        self.assertEqual(captured[0][0]["frame_id"], captured[1][0]["frame_id"])
        mmwave = captured[1][0]["modalities"]["mmwave_radar"]
        self.assertEqual(mmwave["frame_id"], captured[1][0]["frame_id"])
        self.assertEqual(mmwave["timestamp"], captured[1][0]["timestamp"])
        self.assertEqual(mmwave["targets"][0]["position_m"], captured[1][0]["objects"][0]["position"])

    def test_sensorimotor_suite_pairs_varied_scene_geometry_across_camera_lidar_and_mmwave(self):
        captured = []

        def fake_interpret(_interpreter, packet, *, visual_options=None):
            captured.append((packet, visual_options))
            target = next(item for item in packet["objects"] if item["id"] == "target")
            frame_id = packet["frame_id"]
            return {
                "status": "interpreted",
                "interpretation_mode": "sensor_packet" if visual_options["include_sensor_context"] else "image_only",
                "latency_ms": 10.0,
                "interpretation": {"object_descriptions": [{
                    "label": "purple cube", "description": "purple cube on the floor", "role": "goal",
                }]},
                "semantic_scene": {
                    "frame_id": frame_id,
                    "entities": [{
                        "id": "target", "semantic_label": "purple cube",
                        "description": "purple cube on the floor", "role": "goal",
                        "position": target["position"], "size": target["size"],
                    }],
                    "grounding": {"frame_id": frame_id, "accepted_for_context": True},
                },
            }

        with patch("body_runtime_host.worldmodel.evaluation.BodySceneInterpreter.interpret_now", new=fake_interpret), \
                patch("body_runtime_host.worldmodel.evaluation.BodySceneInterpreter._semantic_reference_resolver",
                      return_value={"purple cube": "target"}):
            result = run_vlm_sensorimotor_suite({
                "BODY_LLM_ENABLED": True, "BODY_LLM_MODEL": "test-vlm",
            }, scene_count=3)

        self.assertEqual(result["status"], "completed", result["scene_results"])
        self.assertEqual(result["successes"], 3)
        self.assertEqual(result["collisions"], 0)
        self.assertEqual(result["near_misses"], 0)
        self.assertEqual(result["grounding_acceptance_rate"], 1.0)
        self.assertEqual(result["invented_object_references"], 0)
        self.assertEqual(result["vlm_calls"], 4)
        self.assertEqual([scene["target_id"] for scene in result["scene_results"]], ["target"] * 3)
        paired_scenes = [packet for packet, options in captured if options["include_sensor_context"]]
        self.assertEqual(len(paired_scenes), 3)
        geometry = [next(item for item in packet["objects"] if item["id"] == "target")["position"][:2]
                    for packet in paired_scenes]
        self.assertEqual(geometry, [[5.0, 4.0], [6.0, 5.0], [5.0, 5.0]])
        for packet, _options in captured:
            frame = packet["frame_id"]
            timestamp = packet["timestamp"]
            self.assertEqual(packet["modalities"]["camera"]["frame_id"], frame)
            self.assertEqual(packet["modalities"]["lidar"]["frame_id"], frame)
            self.assertEqual(packet["modalities"]["mmwave_radar"]["frame_id"], frame)
            self.assertEqual(packet["modalities"]["camera"]["timestamp"], timestamp)
            self.assertEqual(packet["modalities"]["lidar"]["timestamp"], timestamp)
            self.assertEqual(packet["modalities"]["mmwave_radar"]["timestamp"], timestamp)

    def test_mmwave_roi_suite_compares_two_inputs_on_identical_frame(self):
        captured = []

        def fake_interpret(_interpreter, packet, *, visual_options=None):
            captured.append((packet, visual_options))
            target = next(item for item in packet["objects"] if item["id"] == "target")
            frame_id = packet["frame_id"]
            return {
                "status": "interpreted", "interpretation_mode": "sensor_packet", "latency_ms": 10.0,
                "visual_input": ({"mmwave_rois": [{"x": 500, "y": 100, "width": 130, "height": 200}]}
                                 if visual_options.get("mmwave_roi") else {}),
                "interpretation": {"object_descriptions": [{
                    "label": "purple cube", "description": "purple cube on the floor", "role": "goal",
                }]},
                "semantic_scene": {
                    "frame_id": frame_id,
                    "entities": [{"id": "target", "semantic_label": "purple cube", "role": "goal",
                                  "description": "purple cube on the floor",
                                  "position": target["position"], "size": target["size"]}],
                    "grounding": {"frame_id": frame_id, "accepted_for_context": True},
                },
            }

        with patch("body_runtime_host.worldmodel.evaluation.BodySceneInterpreter.interpret_now", new=fake_interpret), \
                patch("body_runtime_host.worldmodel.evaluation.BodySceneInterpreter._semantic_reference_resolver",
                      return_value={"purple cube": "target"}):
            result = run_vlm_sensorimotor_suite({
                "BODY_LLM_ENABLED": True, "BODY_LLM_MODEL": "test-vlm",
            }, scene_count=1, roi_compare=True)

        self.assertEqual(result["status"], "completed", result)
        self.assertEqual(result["vlm_calls"], 2)
        self.assertEqual(len(captured), 2)
        self.assertEqual(captured[0][0]["frame_id"], captured[1][0]["frame_id"])
        self.assertEqual(captured[0][0]["timestamp"], captured[1][0]["timestamp"])
        self.assertFalse(captured[0][1]["mmwave_roi"])
        self.assertTrue(captured[1][1]["mmwave_roi"])
        self.assertEqual(result["roi_comparison"]["roi_count"], 1)
        self.assertTrue(result["roi_comparison"]["same_frame_id"])
        self.assertTrue(result["roi_comparison"]["task_target_covered"])
        self.assertEqual(result["roi_comparison"]["full_image_latency_ms"], 10.0)
        roi_snapshot = next(item for item in result["snapshots"] if item["stage"] == "mmwave_roi")
        self.assertTrue(roi_snapshot["roi_evaluation"]["same_frame_as_full_image"])

    def test_sensorimotor_scenario_stops_when_multimodal_grounding_is_rejected(self):
        def fake_interpret(_interpreter, packet, *, visual_options=None):
            frame_id = packet["frame_id"]
            return {
                "status": "interpreted",
                "interpretation_mode": "sensor_packet" if visual_options["include_sensor_context"] else "image_only",
                "latency_ms": 1.0,
                "semantic_scene": {
                    "frame_id": frame_id,
                    "grounding": {"frame_id": frame_id, "accepted_for_context": False},
                },
            }

        with patch("body_runtime_host.worldmodel.evaluation.BodySceneInterpreter.interpret_now", new=fake_interpret):
            result = run_vlm_sensorimotor_scenario({
                "BODY_LLM_ENABLED": True,
                "BODY_LLM_MODEL": "test-vlm",
            })

        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["autonomy"]["status"], "safety_stop")
        self.assertFalse(result["autonomy"]["movement_started"])
        self.assertFalse(result["modality_comparison"]["movement_uses_vlm_output"])
        self.assertEqual(result["actions"], 0)
        self.assertEqual(result["final_position_m"], [1.0, 1.0])


if __name__ == "__main__":
    unittest.main()
