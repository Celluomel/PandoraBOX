import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class BrainBodyStatusResponseTest(unittest.TestCase):
    def test_developmental_autonomy_question_returns_audit_not_unrelated_battery_answer(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._pending_body_plans = {}
        bridge._classify_body_chat_turn = lambda *args, **kwargs: self.fail("developmental audit must not fall through to chat classification")
        prompt = (
            "Lumina, tu viens de proposer de transformer ton aspiration en hypothèse vérifiable. "
            "Je ne veux pas que tu m'expliques comment tu pourrais le faire. "
            "Je veux savoir si ton architecture actuelle te permet de prendre réellement en charge cette démarche. "
            "Détermine si tu peux, sans modification de ton code et sans mon intervention ultérieure : "
            "créer un objectif développemental persistant associé à cette hypothèse; définir une mesure initiale fondée sur des observations réelles; "
            "planifier une première vérification; exécuter les actions nécessaires avec tes capacités actuelles; conserver les résultats et réviser ton objectif selon les observations. "
            "Distingue ce que tu as effectivement exécuté, ce que tu peux exécuter mais n'as pas encore fait, et ce qui nécessite une intervention extérieure. "
            "Ne prétends pas avoir programmé, enregistré ou exécuté une action sans preuve vérifiable. "
            "Si tu disposes de cette autonomie, réalise uniquement la première étape sûre et fournis son identifiant vérifiable. Sinon, indique précisément ce qui t'en empêche."
        )

        result = bridge.handle_body_chat_turn(prompt)

        self.assertEqual(result["status"], "capability_audit")
        self.assertIn("Aucun objectif ni test n'a été créé", result["response"])
        self.assertNotIn("Batterie du Body", result["response"])
        self.assertFalse(result["audit"]["real_observation_baseline"])
        self.assertIsNone(result["audit"]["id"])

    def test_sensor_data_question_returns_hardware_telemetry_not_camera_detections(self):
        from cognition.persona_bridge import PersonaBridge

        now = __import__("time").time()
        body = SimpleNamespace(snapshot=lambda max_age=None: [{
            "subject": "sensor.ultrasonic",
            "source": "remote:body:hc_sr04_ventuno_bridge",
            "observed_at": now,
            "value": {"available": True, "simulated": False, "sensors": [
                {"id": "front_left", "available": True, "distance_m": 0.75},
                {"id": "front_right", "available": True, "distance_m": 2.28},
                {"id": "rear", "available": True, "distance_m": 1.78},
            ]},
        }, {
            "subject": "sensor.odometry",
            "source": "remote:body:ros2_simulation",
            "observed_at": now,
            "value": {"position_m": [0.5, 0.0, 0.0]},
        }], camera_yolo_status=lambda: {
            "state": "ready", "captured_at": now,
            "detections": [{"label": "person", "confidence": 0.74}],
        })
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._pending_body_plans = {}
        bridge._organism = SimpleNamespace(_body_runtime=body)
        bridge._classify_body_chat_turn = lambda *args, **kwargs: self.fail("sensor query must not be routed through the language classifier")

        result = bridge.handle_body_chat_turn("what are the body sensors providing")

        self.assertIn("front_left 0.75m", result["response"])
        self.assertIn("front_right 2.28m", result["response"])
        self.assertNotIn("person", result["response"])
        self.assertNotIn("0.5", result["response"])

    def test_gps_localization_question_returns_coordinates_and_map_link(self):
        from cognition.persona_bridge import PersonaBridge

        now = __import__("time").time()
        body = SimpleNamespace(snapshot=lambda max_age=None: [{
            "subject": "sensor.gps",
            "source": "remote:body:ventuno_usart3_gps",
            "observed_at": now,
            "value": {"available": True, "simulated": False, "fix": True,
                      "latitude": 48.862452, "longitude": 2.118805, "satellites": 9},
        }])
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._pending_body_plans = {}
        bridge._organism = SimpleNamespace(_body_runtime=body)
        bridge._classify_body_chat_turn = lambda *args, **kwargs: self.fail("GPS localization must be deterministic")

        result = bridge.handle_body_chat_turn("from GPS coordinates can you establish the localisation")

        self.assertIn("48.862452, 2.118805", result["response"])
        self.assertIn("openstreetmap.org", result["location"]["map_url"])
        self.assertFalse(result["location"]["stale"])
        self.assertIn("pas sa pose précise", result["response"])

    def test_move_toward_person_explains_missing_metric_localization_and_sends_nothing(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._pending_body_plans = {}
        bridge._organism = SimpleNamespace(_body_runtime=SimpleNamespace())
        bridge._classify_body_chat_turn = lambda *args, **kwargs: "body_action"
        bridge.assess_body_action_request = lambda _text: {
            "accepted": True,
            "feasibility": {"feasible": False, "errors": ["step 1 references unknown target: person"]},
        }

        result = bridge.handle_body_chat_turn("can you move toward the person")

        self.assertEqual(result["status"], "blocked")
        self.assertIn("boîte 2D", result["response"])
        self.assertIn("position métrique", result["response"])
        self.assertIn("Aucun mouvement n'a été envoyé", result["response"])

    def test_movement_status_prioritizes_ack_without_claiming_physical_motion(self):
        from cognition.persona_bridge import PersonaBridge

        now = __import__("time").time()
        observations = [{
            "subject": "fnk0031.usb_status",
            "source": "remote:body:fnk0031_usb",
            "kind": "hardware_status",
            "observed_at": now,
            "value": {"connected": True, "estimated_leg_state": None,
                      "estimated_state_is_measured": False},
        }, {
            "subject": "robot.turn_left",
            "source": "remote:body_action",
            "kind": "actuation_feedback",
            "observed_at": now,
            "value": "acknowledged",
            "provenance": {"command_status": "acknowledged", "verification_status": "unknown"},
        }, {
            "subject": "sensor.odometry",
            "source": "remote:body:ros2_simulation",
            "kind": "sensor",
            "observed_at": now,
            "value": {"position_m": [2.0, 0.0, 0.0]},
        }]
        body = SimpleNamespace(snapshot=lambda max_age=None: observations)
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_status_response("what is the robot movement status")

        self.assertIn("contrôleur FNK0031 connecté", result["response"])
        self.assertIn("robot.turn_left: acknowledged", result["response"])
        self.assertIn("déplacement physique non vérifié", result["response"])
        self.assertIn("Aucune odométrie physique indépendante", result["response"])
        self.assertNotIn("2.0", result["response"])
        self.assertFalse(result["body_status"]["physical_odometry_confirmed"])

    def test_movement_status_reports_no_recent_command_and_disconnected_controller(self):
        from cognition.persona_bridge import PersonaBridge

        body = SimpleNamespace(snapshot=lambda max_age=None: [{
            "subject": "fnk0031.usb_status",
            "source": "remote:body:fnk0031_usb",
            "kind": "hardware_status",
            "observed_at": __import__("time").time(),
            "value": {"connected": False},
        }])
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_status_response("status of robot movements")

        self.assertIn("contrôleur FNK0031 non connecté", result["response"])
        self.assertIn("aucun résultat récent de commande", result["response"])

    def test_no_plan_still_reports_bridged_runtime_observation(self):
        from cognition.persona_bridge import PersonaBridge

        observation = {
            "subject": "body.runtime",
            "source": "remote:body-ventuno:body_runtime",
            "observed_at": __import__("time").time(),
            "value": {
                "camera": {"status": "capturing", "available": True, "observed_fps": 15.0},
                "robot": {"enabled": False, "connected": False},
                "world_model": {"enabled": False, "running": False},
                "plugins": [],
            },
        }
        body = SimpleNamespace(
            worldmodel_plan=lambda: {"active_plan": None},
            worldmodel=None,
            status=lambda: {"brain_bridge": {"connected": True}, "observation_count": 1},
            snapshot=lambda max_age=None: [observation],
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        with patch("cognition.persona_bridge.time.time", return_value=1791069001.0):
            result = bridge._body_status_response()

        self.assertEqual(result["status"], "reported")
        self.assertIn("Aucun plan Body actif", result["response"])
        self.assertIn("camera", result["response"])
        self.assertIn("15", result["response"])
        self.assertIn("pont", result["response"].lower())

    def test_battery_question_returns_compact_estimate_instead_of_sensor_dump(self):
        from cognition.persona_bridge import PersonaBridge

        observation = {
            "subject": "body.runtime",
            "source": "remote:body-ventuno:body_runtime",
            "observed_at": __import__("time").time(),
            "value": {
                "power": {
                    "battery_estimate": {
                        "level_percent_est": 10.2,
                        "remaining_wh_est": 8.562,
                        "source": "continuous INA232 input-rail integration; estimate only",
                    }
                }
            },
        }
        body = SimpleNamespace(
            worldmodel_plan=lambda: {"active_plan": None},
            worldmodel=None,
            status=lambda: {"brain_bridge": {"connected": True}, "observation_count": 1},
            snapshot=lambda max_age=None: [observation],
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_status_response("quel le niveau de battery du body")

        self.assertIn("10.2%", result["response"])
        self.assertIn("8.56 Wh", result["response"])
        self.assertIn("pas une mesure directe", result["response"])
        self.assertNotIn("ranges_m", result["response"])

    def test_body_status_formats_live_sensor_channels_without_raw_json_dump(self):
        from cognition.persona_bridge import PersonaBridge

        observations = [{
            "subject": "sensor.ultrasonic",
            "source": "remote:body:hc_sr04_ventuno_bridge",
            "observed_at": __import__("time").time(),
            "value": {"available": True, "simulated": False, "sensors": [
                {"id": "front_left", "available": True, "distance_m": 0.73},
                {"id": "front_right", "available": False, "distance_m": None},
                {"id": "rear", "available": True, "distance_m": 1.2},
            ]},
        }, {
            "subject": "body.world_model",
            "source": "remote:body:world_model",
            "observed_at": __import__("time").time(),
            "value": {"simulated_only": True, "objects": [{"label": "table"}]},
        }]
        body = SimpleNamespace(
            worldmodel_plan=lambda: {"active_plan": None},
            worldmodel=None,
            status=lambda: {"brain_bridge": {"connected": True}},
            snapshot=lambda max_age=None: observations,
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_status_response("explain body feedback")

        self.assertIn("front_left 0.73m", result["response"])
        self.assertIn("front_right no echo/data", result["response"])
        self.assertIn("simulation-only", result["response"])
        self.assertNotIn('"distance_m"', result["response"])

    def test_body_status_excludes_ros2_simulation_sensors(self):
        from cognition.persona_bridge import PersonaBridge

        observations = [{
            "subject": "sensor.odometry",
            "source": "remote:body:ros2_simulation",
            "observed_at": __import__("time").time(),
            "value": {"position_m": [0.5, 0.0, 0.0]},
        }, {
            "subject": "sensor.gps",
            "source": "remote:body:ventuno_usart3_gps",
            "observed_at": __import__("time").time(),
            "value": {"available": True, "fix": True, "latitude": 48.86,
                      "longitude": 2.11, "satellites": 6},
        }]
        body = SimpleNamespace(
            worldmodel_plan=lambda: {"active_plan": None},
            worldmodel=None,
            status=lambda: {"brain_bridge": {"connected": True}},
            snapshot=lambda max_age=None: observations,
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_status_response("explain body feedback")

        self.assertIn("gps live: fix 48.860000, 2.110000", result["response"])
        self.assertIn("Nav2 simulés", result["response"])
        self.assertNotIn("0.5", result["response"])
        self.assertNotIn("sensor.odometry [remote", result["response"])

    def test_body_status_shows_older_hardware_samples_as_stale_not_missing(self):
        from cognition.persona_bridge import PersonaBridge

        observation = {
            "subject": "sensor.gps",
            "source": "remote:body:ventuno_usart3_gps",
            "observed_at": __import__("time").time() - 24,
            "value": {"available": True, "fix": True, "latitude": 48.86,
                      "longitude": 2.11, "satellites": 6},
        }
        body = SimpleNamespace(
            worldmodel_plan=lambda: {"active_plan": None},
            worldmodel=None,
            status=lambda: {"brain_bridge": {"connected": True}},
            snapshot=lambda max_age=None: [observation],
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_status_response("body status")

        self.assertIn("STALE sample (24s)", result["response"])
        self.assertIn("gps live: fix", result["response"])

    def test_body_status_never_expands_simulation_snapshot_without_flag(self):
        from cognition.persona_bridge import PersonaBridge

        observation = {
            "subject": "body.world_model",
            "source": "remote:body:world_model",
            "observed_at": __import__("time").time(),
            "value": {"source": "ros2_simulation", "objects": [{"label": "simulated chair"}]},
        }
        body = SimpleNamespace(
            worldmodel_plan=lambda: {"active_plan": None},
            worldmodel=None,
            status=lambda: {"brain_bridge": {"connected": True}},
            snapshot=lambda max_age=None: [observation],
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_status_response("body status")

        self.assertIn("simulation-only scene", result["response"])
        self.assertNotIn("simulated chair", result["response"])

    def test_perception_response_uses_real_sensor_telemetry_when_scene_is_simulated(self):
        from cognition.persona_bridge import PersonaBridge

        body = SimpleNamespace(
            snapshot=lambda max_age=None: [{
                "subject": "sensor.gps",
                "value": {"available": True, "fix": True, "latitude": 48.8625,
                          "longitude": 2.1187, "satellites": 7},
            }],
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)
        bridge.current_body_perception = lambda: {
            "available": True,
            "snapshot": {"ground_truth_available": True, "objects": [{"label": "simulated chair"}]},
        }

        result = bridge._body_perception_response()

        self.assertIn("simulation, pas une observation du robot réel", result["response"])
        self.assertIn("48.862500, 2.118700", result["response"])
        self.assertNotIn("simulated chair", result["response"])

    def test_perception_response_still_reports_sensors_without_scene_snapshot(self):
        from cognition.persona_bridge import PersonaBridge

        body = SimpleNamespace(snapshot=lambda max_age=None: [{
            "subject": "sensor.tof",
            "value": {"available": True, "distance_m": 0.62, "simulated": False},
        }])
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)
        bridge.current_body_perception = lambda: {"available": False, "error": "stale world model"}

        result = bridge._body_perception_response()

        self.assertEqual(result["status"], "reported")
        self.assertIn("Capteurs réels", result["response"])
        self.assertIn("0.62m", result["response"])
        self.assertFalse(result["perception"]["scene_available"])

    def test_perception_response_rejects_simulation_source_without_flag(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=SimpleNamespace(snapshot=lambda max_age=None: []))
        bridge.current_body_perception = lambda: {
            "available": True,
            "snapshot": {"source": "ros2_simulation", "objects": [{"label": "simulated chair"}]},
        }

        result = bridge._body_perception_response()

        self.assertIn("simulation, pas une observation", result["response"])
        self.assertNotIn("simulated chair", result["response"])

    def test_perception_response_rejects_simulated_room_source(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=SimpleNamespace(snapshot=lambda max_age=None: []))
        bridge.current_body_perception = lambda: {
            "available": True,
            "snapshot": {"source": "simulated_room", "objects": [{"label": "moving obstacle"}]},
        }

        result = bridge._body_perception_response()

        self.assertIn("simulation, pas une observation", result["response"])
        self.assertNotIn("moving obstacle", result["response"])

    def test_perception_response_prefers_fresh_live_yolox_over_simulated_map(self):
        from cognition.persona_bridge import PersonaBridge

        now = __import__("time").time()
        body = SimpleNamespace(
            camera_yolo_status=lambda: {
                "state": "ready", "frame_id": "camera-42", "captured_at": now,
                "detections": [
                    {"label": "person", "confidence": 0.7931},
                    {"label": "person", "confidence": 0.4156},
                ],
            },
            body_snapshot=lambda: {
                "source": "simulated_room", "objects": [{"label": "simulated chair"}],
            },
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_perception_response()

        self.assertIn("YOLOX", result["response"])
        self.assertIn("2 détection(s) 2D", result["response"])
        self.assertIn("person (79%)", result["response"])
        self.assertIn("simulateur", result["response"])
        self.assertNotIn("simulated chair", result["response"])

    def test_perception_response_reports_stale_yolox_as_stale_not_live(self):
        from cognition.persona_bridge import PersonaBridge

        now = __import__("time").time()
        body = SimpleNamespace(
            camera_yolo_status=lambda: {
                "state": "ready", "frame_id": "camera-old", "captured_at": now - 28,
                "detections": [{"label": "person", "confidence": 0.77}],
            },
            body_snapshot=lambda: {"source": "simulated_room", "objects": []},
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_perception_response()

        self.assertIn("dernière analyse il y a 28s · STALE", result["response"])
        self.assertIn("person (77%)", result["response"])
        self.assertTrue(result["perception"]["camera"]["stale"])


if __name__ == "__main__":
    unittest.main()
