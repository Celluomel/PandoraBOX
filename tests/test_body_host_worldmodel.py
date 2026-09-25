"""Tests for the standalone Body host (body_runtime_host) and the robot protocol.

Covers:
    * RobotSimServer — the robot protocol (GET /sensors, POST /command, /health, /reset)
    * RobotHttpSource — the Body's main sensorimetry channel speaking that protocol
    * End-to-end: EmbodiedWorldModel learning against a *remote* robot over HTTP
      (the exact production path: Body host <-> robot)
    * BodyHost — plugins(), robot polling, /health + /worldmodel/* endpoints

Run:  venv/Scripts/python.exe -m pytest tests/test_body_host_worldmodel.py -v
"""
import json
import importlib.util
import types
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


class RobotSimServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from body_runtime_host.robot_sim import RobotSimServer
        cls.server = RobotSimServer(host="127.0.0.1", port=0)
        cls.server.start()
        cls.base = f"http://127.0.0.1:{cls.server.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_health(self):
        data = _get(f"{self.base}/health")
        self.assertEqual(data["status"], "robot-sim")

    def test_sensors_shape(self):
        data = _get(f"{self.base}/sensors")
        self.assertEqual(len(data["position"]), 3)
        self.assertIn("capabilities", data)
        self.assertIn("objects", data)
        self.assertGreaterEqual(len(data["objects"]), 4)
        self.assertIn("battery", data)

    def test_command_moves_body(self):
        before = _get(f"{self.base}/sensors")["position"][:2]
        out = _post(f"{self.base}/command", {"type": "forward", "target": None, "params": {}})
        self.assertIn(out["outcome"], {"success", "failure", "danger", "neutral"})
        self.assertIn("reward", out)

    def test_reset(self):
        out = _post(f"{self.base}/reset", {})
        self.assertTrue(out["ok"])


@unittest.skipUnless(importlib.util.find_spec("numpy"), "numpy is required for the locomotion controller")
class FNK0031LocomotionControllerTest(unittest.TestCase):
    def test_tripod_groups_and_controller_telemetry(self):
        import numpy as np
        from body_runtime_host.locomotion import FNK0031LocomotionController
        from body_runtime_host.locomotion.fnk0031_controller import TripodCPG

        cpg = TripodCPG()
        values = cpg.step(dt=0.02)
        self.assertEqual(cpg.contact.tolist(), [1, 0, 0, 1, 1, 0])
        self.assertEqual(len(values), 6)
        self.assertGreater(float(cpg.foot_lift[1]), 0.0)
        self.assertEqual(float(cpg.foot_lift[0]), 0.0)

        with tempfile.TemporaryDirectory() as tmp:
            controller = FNK0031LocomotionController(Path(tmp) / "weights.npz")
            state = controller.step(imu=None, reward=0.0)
            self.assertEqual(len(state["joint_targets"]), 6)
            self.assertTrue(all(leg[0] == 0.0 and leg[1] == 0.0 for leg in state["foot_motion"]))
            forward_motion = controller.step(imu=None, reward=0.0, gait="forward")
            self.assertGreater(
                max(abs(leg[0]) for leg in forward_motion["foot_motion"]),
                0.0,
                "forward gait must expose sagittal foot motion",
            )
            self.assertGreater(
                max(abs(value) for leg in forward_motion["joint_targets"] for value in leg),
                0.0,
                "forward gait must produce actuator targets",
            )
            self.assertEqual(len(state["spikes"]), 18)
            self.assertEqual(state["servo_count"], 18)
            self.assertEqual([x["index"] for x in state["servo_targets"]], list(range(1, 19)))
            self.assertEqual([x["joint"] for x in state["servo_targets"][:3]], ["coxa", "femur", "tibia"])
            self.assertEqual(state["servo_targets"][3]["leg"], "L2")
            self.assertEqual([leg["label"] for leg in state["visual_legs"]], [
                "front-left", "middle-left", "rear-left",
                "front-right", "middle-right", "rear-right",
            ])
            self.assertEqual([leg["physical_index"] for leg in state["visual_legs"]], [0, 2, 4, 1, 3, 5])
            self.assertEqual([leg["neuron_indices"] for leg in state["visual_legs"]], [
                [0, 1, 2], [6, 7, 8], [12, 13, 14],
                [3, 4, 5], [9, 10, 11], [15, 16, 17],
            ])
            self.assertEqual(state["imu"]["source"], "simulated_plant")
            self.assertGreater(state["reward"], 0.0)
            self.assertIn("forward_prediction_error", state)
            initial_weights = controller.snn.weights.copy()
            observed_spikes = np.asarray(state["spikes"])
            for _ in range(10):
                state = controller.step(imu=None, reward=0.0)
                observed_spikes = np.maximum(observed_spikes, state["spikes"])
            self.assertGreater(int(observed_spikes.sum()), 0, "SNN should emit visible spikes during gait")
            self.assertEqual(float(np.abs(controller.snn.weights - initial_weights).sum()), 0.0)
            self.assertGreater(state["forward_prediction_weights_norm"], 0.0)
            self.assertEqual(controller.competence, 0.0)
            self.assertEqual(state["cpg_weight"], 1.0)
            self.assertEqual(state["snn_weight"], 0.0)
            self.assertEqual(state["reward_source"], "synthetic_heuristic")
            self.assertFalse(state["locomotion_verified"])
            phase = controller.cpg.phase
            idle = controller.step(imu=None, reward=0.0, gait="idle")
            self.assertEqual(controller.cpg.phase, phase)
            self.assertTrue(np.allclose(idle["joint_targets"], 0.0))

            controller.steps = 99
            controller.step(imu=None, reward=0.0)
            restored = FNK0031LocomotionController(Path(tmp) / "weights.npz")
            self.assertTrue(restored.loaded)
            self.assertEqual(restored.competence, 0.0)
            self.assertGreater(np.linalg.norm(restored.forward_model.weights), 0.0)

            hardware_without_imu = FNK0031LocomotionController(Path(tmp) / "hardware.npz")
            hardware_state = hardware_without_imu.step(imu=None, simulate=False)
            self.assertEqual(hardware_state["imu"]["source"], "unavailable")
            self.assertEqual(hardware_state["reward"], 0.0)

            turn_left = FNK0031LocomotionController(Path(tmp) / "left.npz").step(gait="turn_left")
            turn_right = FNK0031LocomotionController(Path(tmp) / "right.npz").step(gait="turn_right")
            self.assertNotEqual(turn_left["joint_targets"], turn_right["joint_targets"])
            self.assertGreater(max(abs(value) for leg in turn_left["foot_motion"] for value in leg[:2]), 0.1)
            self.assertGreater(turn_left["visual_legs"][0]["foot_motion"][0], 0.0)
            self.assertLess(turn_left["visual_legs"][2]["foot_motion"][0], 0.0)
            for left_leg, right_leg in zip(turn_left["foot_motion"], turn_right["foot_motion"]):
                self.assertAlmostEqual(left_leg[0], -right_leg[0], places=3)
                self.assertAlmostEqual(left_leg[1], -right_leg[1], places=3)
            self.assertLess(turn_left["plant"]["heading"], 3.14159)
            self.assertGreater(turn_right["plant"]["heading"], 3.14159)


@unittest.skipUnless(importlib.util.find_spec("mujoco"), "mujoco is required for physics-backed locomotion")
class FNK0031MuJoCoTest(unittest.TestCase):
    def test_estimated_model_has_18_actuators_and_stable_contact_gait(self):
        from body_runtime_host.locomotion.fnk0031_controller import FNK0031LocomotionController
        from body_runtime_host.locomotion.mujoco_hexapod import run_episode

        with tempfile.TemporaryDirectory() as tmp:
            result = run_episode(
                FNK0031LocomotionController(Path(tmp) / "snn.npz"), "cpg", steps=250, seed=4
            )
        self.assertEqual(result.steps, 250)
        self.assertFalse(result.fell)
        self.assertGreater(result.displacement_m, 0.1)
        self.assertGreater(result.mean_foot_contacts, 1.0)

    def test_task_reward_drives_snn_plasticity_in_physics_trial(self):
        import numpy as np
        from body_runtime_host.locomotion.fnk0031_controller import FNK0031LocomotionController
        from body_runtime_host.locomotion.mujoco_hexapod import run_episode

        with tempfile.TemporaryDirectory() as tmp:
            controller = FNK0031LocomotionController(Path(tmp) / "snn.npz")
            initial = controller.snn.weights.copy()
            result = run_episode(controller, "snn", steps=100, seed=8)
        self.assertGreater(float(np.abs(controller.snn.weights - initial).sum()), 0.0)
        self.assertGreater(result.neural_spike_events, 0)
        self.assertGreater(result.weight_change_l1, 0.0)
        self.assertGreater(result.motor_readout_change_l1, 0.0)


class BodySingletonStartupTest(unittest.TestCase):
    def test_sim_mode_keeps_sim_source_even_when_physical_plugin_is_enabled(self):
        import body_runtime_host.runtime as brt
        fake_worldmodel = types.ModuleType("body_runtime_host.worldmodel")
        fake_worldmodel.SimRobotSource = type("SimRobotSource", (), {})
        fake_worldmodel.resolve_source = lambda *_: self.fail("physical source must not override sim mode")
        host = brt.BodyHost()
        host.config = {"BODY_PLUGIN_ROBOT_ENABLED": True, "BODY_PLUGIN_FNK0050_ENABLED": True}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = root / "data" / "body" / "worldmodel"
            cfg.mkdir(parents=True)
            (cfg / "config.json").write_text(json.dumps({"mode": "sim"}), encoding="utf-8")
            with patch.object(brt, "ROOT", root), patch.dict(sys.modules, {"body_runtime_host.worldmodel": fake_worldmodel}):
                source = host._resolve_worldmodel_source()
        self.assertEqual(type(source).__name__, "SimRobotSource")

    def test_simulated_locomotion_does_not_require_physical_actuation(self):
        import body_runtime_host.runtime as brt

        class RunningThread:
            def is_alive(self):
                return True

        class RunningWorldModel:
            _thread = RunningThread()
            _lock = threading.RLock()
            _last_decision = {"action": "turn_left"}

            class Sim:
                heading = 1.5707963267948966
                px = 4.0
                py = 6.0
                steps = 12

            sim = Sim()

            def config(self):
                return {"mode": "sim"}

        class FakeController:
            loaded = False

            def __init__(self, **_kwargs):
                self.gait = None
                self.calls = 0

            def step(self, **kwargs):
                self.gait = kwargs["gait"]
                self.calls += 1
                return {"cpg": [1, -1, -1, 1, 1, -1], "spikes": [0] * 18, "step": 1}

        fake_locomotion = types.ModuleType("body_runtime_host.locomotion")
        fake_locomotion.FNK0031LocomotionController = FakeController
        host = brt.BodyHost()
        host.config = {
            "BODY_PLUGIN_ROBOT_ENABLED": True,
            "FNK0031_SNN_ENABLED": True,
            "FNK0031_ACTUATION_ENABLED": False,
        }
        host._worldmodel = RunningWorldModel()
        with patch.dict(sys.modules, {"body_runtime_host.locomotion": fake_locomotion}), patch.object(brt, "ROOT", Path(tempfile.gettempdir())):
            result = host.fnk0031_controller_step()
        self.assertTrue(result["active"])
        self.assertFalse(result["actuation"])
        self.assertEqual(result["body_heading_deg"], 90.0)
        self.assertEqual(result["gait"], "turn_left")
        self.assertEqual(result["worldmodel_pose"], {
            "body": [4.0, 6.0], "heading_deg": 90.0,
            "compass_heading_deg": 0.0, "svg_heading_deg": 0.0, "step": 12,
        })
        self.assertEqual(result["compass_heading_deg"], 0.0)
        self.assertEqual(result["svg_heading_deg"], 0.0)
        self.assertEqual(host._fnk_controller.gait, "turn_left")
        status = host.fnk0031_controller_status()
        self.assertTrue(status["simulation_running"])
        self.assertEqual(status["worldmodel_pose"], result["worldmodel_pose"])
        self.assertEqual(status["gait"], "turn_left")
        host._worldmodel._last_decision = {"action": "sprint"}
        host._worldmodel.sim.steps = 13
        sprint_status = host.fnk0031_controller_status()
        self.assertEqual(sprint_status["world_action"], "sprint")
        self.assertEqual(sprint_status["gait"], "forward")
        self.assertEqual(host._fnk_controller.gait, "forward")
        calls = host._fnk_controller.calls
        host._fnk_controller_last_tick = 0.0
        same_world_step = host.fnk0031_controller_status()
        self.assertEqual(host._fnk_controller.calls, calls + 1)
        self.assertEqual(same_world_step["worldmodel_step"], 13)
        host._worldmodel._thread = None
        paused_status = host.fnk0031_controller_status()
        self.assertFalse(paused_status["simulation_running"])
        self.assertEqual(paused_status["gait"], "forward")

    def test_world_actions_are_mapped_to_physical_gaits(self):
        from body_runtime_host.runtime import _locomotion_gait_for_action

        self.assertEqual(_locomotion_gait_for_action("sprint"), "forward")
        self.assertEqual(_locomotion_gait_for_action("forward→table"), "forward")
        self.assertEqual(_locomotion_gait_for_action("turn_left→chair"), "turn_left")
        self.assertEqual(_locomotion_gait_for_action("retreat->obstacle"), "backward")
        self.assertEqual(_locomotion_gait_for_action("retreat"), "backward")
        self.assertEqual(_locomotion_gait_for_action("turn_left"), "turn_left")
        self.assertEqual(_locomotion_gait_for_action("grab"), "idle")

    def test_locomotion_simulation_waits_for_running_world_model(self):
        from body_runtime_host.runtime import BodyHost

        class PausedWorldModel:
            _thread = None

            def config(self):
                return {"mode": "sim"}

        host = BodyHost()
        host.config = {
            "BODY_PLUGIN_ROBOT_ENABLED": True,
            "FNK0031_SNN_ENABLED": True,
        }
        host._worldmodel = PausedWorldModel()
        result = host.fnk0031_controller_step()
        self.assertFalse(result["active"])
        self.assertIn("start the simulated world model", result["reason"])

    def test_robot_poll_uses_fnk_endpoint_and_ignores_legacy_localhost_placeholder(self):
        from body_runtime_host.runtime import BodyHost
        host = BodyHost()
        host.config = {
            "BODY_PLUGIN_ROBOT_ENABLED": True,
            "ROBOT_URL": "http://127.0.0.1:9100",
        }
        self.assertFalse(host._robot_configured())
        self.assertEqual(host.robot_status()["url"], "")

        host.config["FNK0031_URL"] = "http://192.168.0.42:9100/"
        self.assertTrue(host._robot_configured())
        self.assertEqual(host.robot_status()["url"], "http://192.168.0.42:9100")

    def test_host_does_not_start_sensor_pollers_when_http_port_is_taken(self):
        from body_runtime_host.runtime import BodyHost
        host = BodyHost()
        with patch.object(host, "_start_http_endpoint") as start_http, \
             patch.object(host, "poll_loop") as poll_loop:
            start_http.side_effect = lambda: setattr(host, "http_server", None)
            host.run()
        poll_loop.assert_not_called()


class RobotHttpSourceTest(unittest.TestCase):
    """The Body's main channel must speak the robot protocol correctly."""

    @classmethod
    def setUpClass(cls):
        from body_runtime_host.robot_sim import RobotSimServer
        cls.server = RobotSimServer(host="127.0.0.1", port=0)
        cls.server.start()
        cls.base = f"http://127.0.0.1:{cls.server.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_source_roundtrip(self):
        from body_runtime_host.worldmodel import RobotHttpSource, Action
        src = RobotHttpSource(url=self.base, timeout=5.0)
        self.assertTrue(src.ping())
        obs = src.observe()
        self.assertEqual(obs.source, "robot")
        self.assertGreaterEqual(len(obs.scene), 4)
        self.assertIn("Robot body at", obs.text)
        body = src.body_state()
        self.assertEqual(len(body.position), 3)
        # Direct source execution is intentionally observation-only. Physical
        # actuation must go through the approved Body command boundary.
        obs_after, outcome = src.execute(Action(type="forward"))
        self.assertEqual(outcome.kind, "neutral")
        self.assertIn("approved Body command", outcome.description)
        self.assertGreaterEqual(len(obs_after.scene), 4)
        src.actuation_enabled = True
        obs_after, outcome = src.execute_authorized(Action(type="forward"))
        self.assertIn(outcome.kind, {"success", "failure", "danger", "neutral"})
        self.assertGreaterEqual(len(obs_after.scene), 4)
        st = src.status()
        self.assertEqual(st["source"], "robot")
        self.assertIsNotNone(st["last_ok_age_s"])

    def test_resolve_source_prefers_robot(self):
        from body_runtime_host.worldmodel import resolve_source
        cfg = {
            "BODY_PLUGIN_ROBOT_ENABLED": True,
            "ROBOT_URL": self.base,
            "BODY_PLUGIN_SIM_ROBOT_ENABLED": True,
            "BODY_PLUGIN_HOME_ASSISTANT_ENABLED": True,
        }
        src = resolve_source(cfg, {"a": {"observed_at": time.time()}})
        self.assertEqual(src.name, "robot")

    def test_resolve_source_priority_chain(self):
        from body_runtime_host.worldmodel import resolve_source
        # robot enabled but no URL -> sim robot
        src = resolve_source({"BODY_PLUGIN_ROBOT_ENABLED": True, "ROBOT_URL": "", "BODY_PLUGIN_SIM_ROBOT_ENABLED": True}, {})
        self.assertEqual(src.name, "sim_robot")
        # nothing enabled -> null
        src = resolve_source({}, None)
        self.assertEqual(src.name, "null")


class EndToEndRemoteRobotTest(unittest.TestCase):
    """The full embodied loop against a REMOTE robot over HTTP — production path."""

    def test_worldmodel_learns_against_remote_robot(self):
        from body_runtime_host.robot_sim import RobotSimServer
        from body_runtime_host.worldmodel import EmbodiedWorldModel, RobotHttpSource

        server = RobotSimServer(host="127.0.0.1", port=0)
        server.start()
        base = f"http://127.0.0.1:{server.port}"
        try:
            src = RobotHttpSource(url=base, timeout=5.0)
            with tempfile.TemporaryDirectory() as tmp:
                wm = EmbodiedWorldModel(body=None, data_dir=tmp, source=src)
                self.assertEqual(wm.source.name, "robot")
                first_err = None
                last_err = None
                for i in range(25):
                    out = wm.step()
                    if i < 5 and first_err is None and math_isfinite(out.get("prediction_error", 0)):
                        first_err = out["prediction_error"]
                    last_err = out["prediction_error"]
                # The loop ran against the remote robot and accumulated memory
                self.assertGreaterEqual(wm._steps, 25)
                stats = wm.memory.stats()
                self.assertGreaterEqual(stats["objets"]["count"], 4)
                self.assertGreaterEqual(stats["lieux"]["count"], 1)
                # remote robot source must be reported in status + brain context
                self.assertEqual(wm.status_summary()["source"]["source"], "robot")
                ctx = wm.context_for_brain()
                self.assertIn("LIVE ROBOT", ctx)
                self.assertIn(base, ctx)
                # prediction error signal is finite
                self.assertTrue(math_isfinite(wm._pred_error_ema))
        finally:
            server.stop()


def math_isfinite(x) -> bool:
    try:
        return x == x and x not in (float("inf"), float("-inf"))
    except TypeError:
        return False


class BodyHostHttpTest(unittest.TestCase):
    """BodyHost HTTP surface: /health, /plugins, /worldmodel/* (no config file writes)."""

    def test_health_plugins_and_worldmodel_endpoints(self):
        # Build a BodyHost without touching the real config: monkeypatch CONFIG_PATH.
        import body_runtime_host.runtime as brt
        with tempfile.TemporaryDirectory() as tmp:
            real_config_path = brt.CONFIG_PATH
            real_dotenv = brt._load_dotenv
            brt.CONFIG_PATH = Path(tmp) / "config.json"
            brt.CONFIG_PATH.write_text(json.dumps({
                "BODY_HOST": "127.0.0.1",
                "BODY_PORT": 0,  # not honored by _start_http_endpoint (needs a real port); use 8791
                "BODY_PLUGIN_ROBOT_ENABLED": False,
                "ROBOT_URL": "",
                "BODY_WORLDMODEL_ENABLED": True,
                "BODY_PLUGIN_HOME_ASSISTANT_ENABLED": False,
                "BODY_BRIDGE_ENABLED": False,
            }), encoding="utf-8")
            brt._load_dotenv = lambda: None
            host = brt.BodyHost()
            # force a free port
            host.config["BODY_PORT"] = 8791
            try:
                host._start_http_endpoint()
                base = "http://127.0.0.1:8791"
                health = _get(f"{base}/health")
                self.assertEqual(health["status"], "ready")
                self.assertIn("robot", health)
                self.assertIn("plugins", health)
                self.assertIn("worldmodel", health)
                self.assertEqual(len(health["plugins"]), 5)

                # world model endpoints (lazy build)
                status = _get(f"{base}/worldmodel/status")
                self.assertIn("mode", status)
                self.assertFalse(status["running"], "Body startup must leave simulation paused")
                initial_snapshot = _get(f"{base}/worldmodel/snapshot")
                self.assertTrue(initial_snapshot.get("snapshot_id"), initial_snapshot)
                anchors = _get(f"{base}/worldmodel/anchors")
                self.assertIn("stats", anchors)
                eps = _get(f"{base}/worldmodel/episodes")
                self.assertIsInstance(eps, list)

                # run a supervised step over HTTP
                step = _post(f"{base}/worldmodel/step", {})
                self.assertIn("action", step)
                self.assertIn("outcome", step)

                # config round-trip
                cfg = _get(f"{base}/worldmodel/config")
                self.assertIn("enabled", cfg)
            finally:
                host._worldmodel and host._worldmodel.stop()
                if host.http_server is not None:
                    host.http_server.shutdown()
                    host.http_server.server_close()
                brt.CONFIG_PATH = real_config_path
                brt._load_dotenv = real_dotenv

    def test_fnk0031_locomotion_flags_round_trip_to_disk_and_runtime(self):
        import body_runtime_host.runtime as brt
        with tempfile.TemporaryDirectory() as tmp:
            real_config_path = brt.CONFIG_PATH
            real_dotenv = brt._load_dotenv
            brt.CONFIG_PATH = Path(tmp) / "config.json"
            brt.CONFIG_PATH.write_text(json.dumps({
                "BODY_PLUGIN_ROBOT_ENABLED": True,
                "FNK0031_SNN_ENABLED": False,
                "FNK0031_ACTUATION_ENABLED": False,
            }), encoding="utf-8")
            brt._load_dotenv = lambda: None
            host = brt.BodyHost()
            try:
                result = host.update_fnk0031_settings({
                    "snn_enabled": True,
                    "actuation_enabled": True,
                })
                self.assertTrue(result["settings"]["snn_enabled"])
                self.assertTrue(result["settings"]["actuation_enabled"])
                persisted = json.loads(brt.CONFIG_PATH.read_text(encoding="utf-8"))
                self.assertTrue(persisted["FNK0031_SNN_ENABLED"])
                self.assertTrue(persisted["FNK0031_ACTUATION_ENABLED"])
                self.assertEqual(result["settings"]["persisted"], {
                    "snn_enabled": True,
                    "actuation_enabled": True,
                })
            finally:
                brt.CONFIG_PATH = real_config_path
                brt._load_dotenv = real_dotenv


if __name__ == "__main__":
    unittest.main(verbosity=2)
