import unittest
from unittest.mock import patch

from body_runtime_host.worldmodel.evaluation import (
    _restart_resume_probe,
    collect_body_llm_grounding,
    run_vlm_sensorimotor_scenario,
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
            return {
                "status": "interpreted",
                "interpretation_mode": "sensor_packet" if visual_options["include_sensor_context"] else "image_only",
                "latency_ms": 12.5,
                "interpretation": {"scene_summary": "A clear route bends around an obstacle."},
                "semantic_scene": {"grounding": {
                    "reference_precision": 1.0, "accepted_for_context": True,
                    "geometry_authoritative": True,
                }},
            }

        with patch(
            "body_runtime_host.worldmodel.evaluation.BodySceneInterpreter.interpret_now",
            new=fake_interpret,
        ):
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
        self.assertEqual([item["stage"] for item in result["snapshots"]], ["camera_only", "camera_plus_lidar"])
        self.assertEqual(result["snapshots"][0]["frame_id"], result["snapshots"][1]["frame_id"])
        self.assertEqual(result["snapshots"][0]["timestamp"], result["snapshots"][1]["timestamp"])
        self.assertEqual(result["snapshots"][0]["vlm_mode"], "image_only")
        self.assertEqual(result["snapshots"][1]["vlm_mode"], "sensor_packet")
        self.assertEqual(result["snapshots"][0]["sensor_packet"]["lidar"]["points_sent_to_vlm"], [])
        self.assertGreater(len(result["snapshots"][1]["sensor_packet"]["lidar"]["points_sent_to_vlm"]), 0)
        self.assertTrue(result["modality_comparison"]["same_frame_id"])
        self.assertTrue(result["modality_comparison"]["same_timestamp"])
        self.assertFalse(result["modality_comparison"]["movement_uses_vlm_output"])
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


if __name__ == "__main__":
    unittest.main()
