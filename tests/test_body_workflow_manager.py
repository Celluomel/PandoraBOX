import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from body_runtime_host.workflow_manager import WorkflowError, WorkflowManager


class FakeHost:
    def __init__(self):
        self.latest = {}
        self.worldmodel = None
        self._ros2_bridge = None
        self.sent = []

    def robot_status(self):
        return {"last_ok": None}

    def fnk0031_settings(self):
        return {"url": "", "actuation_enabled": False}

    def _bridge_put(self, observation):
        self.sent.append(observation)


class WorkflowManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.host = FakeHost()
        self.path = Path(self.temp.name) / "workflows.json"
        self.manager = WorkflowManager(self.host, self.path)

    def tearDown(self):
        self.temp.cleanup()

    def workflow(self, edges=None, extra_nodes=None):
        nodes = [
            {"id": "sensor", "type": "lidar", "x": 0, "y": 0},
            {"id": "brain", "type": "brain", "x": 200, "y": 0},
        ]
        if extra_nodes:
            nodes.extend(extra_nodes)
        return {"name": "Read-only test", "nodes": nodes, "edges": edges or [["sensor", "brain"]]}

    def test_first_run_seeds_persistent_starter_and_keeps_explicit_deletion(self):
        rows = self.manager.list()["workflows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "Body sensorimotor pipeline")
        self.assertEqual(len(rows[0]["nodes"]), 8)
        self.assertTrue(self.manager.delete(rows[0]["id"]))
        self.assertEqual(WorkflowManager(self.host, self.path).list()["workflows"], [])

    def test_save_reload_and_run_records_history(self):
        saved = self.manager.save(self.workflow())
        run = self.manager.execute(saved["id"])
        self.assertEqual(run["status"], "completed")
        self.assertEqual(len(self.host.sent), 1)
        reloaded = WorkflowManager(self.host, self.path)
        self.assertEqual(reloaded.get(saved["id"])["last_execution"]["id"], run["id"])
        self.assertEqual(len(reloaded.executions(saved["id"])["executions"]), 1)

    def test_cycle_is_rejected_before_save(self):
        with self.assertRaises(WorkflowError):
            self.manager.save(self.workflow(edges=[["sensor", "brain"], ["brain", "sensor"]]))
        self.assertEqual(len(self.manager.list()["workflows"]), 1)

    def test_physical_output_refuses_entire_graph_before_side_effects(self):
        workflow = self.workflow(
            edges=[["sensor", "brain"], ["sensor", "arm"]],
            extra_nodes=[{"id": "arm", "type": "fnk", "x": 400, "y": 0}],
        )
        saved = self.manager.save(workflow)
        with self.assertRaisesRegex(WorkflowError, "no nodes were run"):
            self.manager.execute(saved["id"])
        self.assertEqual(self.host.sent, [])

    def test_mobile_manipulation_demo_executes_typed_shared_frame_handoff(self):
        demo = self.manager.mobile_manipulation_demo()
        saved = self.manager.save(demo)

        run = self.manager.execute(saved["id"])

        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["execution_mode"], "simulation")
        self.assertEqual([node["status"] for node in run["nodes"]], ["success"] * 3)
        self.assertEqual(run["nodes"][-1]["output"]["status"], "simulated_success")
        self.assertEqual(run["nodes"][-1]["output"]["actuation"], False)

    def test_mobile_manipulation_rejects_frame_mismatch_and_unreachable_arm_pose(self):
        base = self.manager.MOBILE_MANIPULATION_DEMO["nodes"][0]
        guard = self.manager.MOBILE_MANIPULATION_DEMO["nodes"][1]

        with self.assertRaisesRegex(WorkflowError, "coordinate frame mismatch"):
            self.manager._execute_node("frame_guard", [self.manager._execute_node(
                "sim_base_navigate", [], {**base["config"], "frame_id": "odom"}
            )], guard["config"])

        with self.assertRaisesRegex(WorkflowError, "out of reach"):
            self.manager._execute_node("frame_guard", [self.manager._execute_node(
                "sim_base_navigate", [], base["config"]
            )], {**guard["config"], "x": 8.0})

    def test_typed_workflow_connections_reject_incompatible_pose_handoff(self):
        with self.assertRaisesRegex(WorkflowError, "incompatible connection"):
            self.manager.save({
                "name": "invalid typed graph",
                "nodes": [
                    {"id": "base", "type": "sim_base_navigate"},
                    {"id": "arm", "type": "sim_arm_action"},
                ],
                "edges": [["base", "arm"]],
            })

    def test_catalog_distinguishes_real_hardware_from_simulated_adapters(self):
        catalog = self.manager.catalog()
        devices = {device["id"]: device for device in catalog["devices"]}

        self.assertEqual(devices["fnk0031"]["mode"], "hardware")
        self.assertEqual(devices["sim_manipulator"]["mode"], "simulation")
        self.assertFalse(catalog["physical_actuation_enabled"])
        self.assertIn("sim_arm_action", {node["type"] for node in catalog["nodes"]})

    def test_workflow_editor_mounts_on_sidebar_navigation_and_exposes_vlm_analysis(self):
        from body_runtime_host.body_gui import BODY_GUI_HTML

        self.assertIn("if(view==='ros2')", BODY_GUI_HTML)
        self.assertIn("mountWorkflowEditor(rosView)", BODY_GUI_HTML)
        self.assertIn("Analyze with Body VLM", BODY_GUI_HTML)
        self.assertIn("/workflows/'+encodeURIComponent(workflowId)+'/analyze", BODY_GUI_HTML)

    def test_workflow_analysis_uses_saved_outputs_and_never_applies_suggestions(self):
        import json
        from types import SimpleNamespace
        from body_runtime_host.runtime import BodyHost

        saved = {
            "id": "wf-1", "nodes": [{"id": "camera", "type": "camera"}],
            "edges": [],
            "last_execution": {"id": "run-1", "status": "failed", "nodes": [
                {"id": "camera", "status": "failed", "error": "camera unavailable"},
            ]},
        }

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return json.dumps({"choices": [{"message": {"content": json.dumps({
                    "summary": "Camera input failed.",
                    "findings": [{"severity": "error", "issue": "camera unavailable",
                                  "evidence_node_ids": ["camera"], "cause": "No frame source.",
                                  "fix_options": ["Check the camera source."], "confidence": 0.9}],
                    "safety_notes": ["No physical command was sent."],
                })}}]}).encode()

        host = SimpleNamespace(
            workflow_manager=SimpleNamespace(get=lambda workflow_id: saved),
            body_llm_settings=lambda: {"model": "local-vlm", "base_url": "http://localhost:1234/v1",
                                       "max_tokens": 512, "timeout": 10},
            _camera_provider=lambda: None,
            value=lambda key, fallback=None: "",
            _workflow_analysis_safe=BodyHost._workflow_analysis_safe,
        )
        requests = []

        def fake_urlopen(request, timeout):
            requests.append(json.loads(request.data.decode()))
            return Response()

        with patch("body_runtime_host.runtime.urlopen", side_effect=fake_urlopen):
            result = BodyHost.analyze_workflow_execution(host, "wf-1")

        self.assertTrue(result["ok"])
        self.assertFalse(result["applied"])
        self.assertEqual(result["execution_id"], "run-1")
        self.assertIn("camera unavailable", requests[0]["messages"][1]["content"])


if __name__ == "__main__":
    unittest.main()
