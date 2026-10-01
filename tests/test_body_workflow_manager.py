import tempfile
import unittest
from pathlib import Path

from body_runtime_host.workflow_manager import WorkflowError, WorkflowManager


class FakeHost:
    def __init__(self):
        self.latest = {}
        self.worldmodel = None
        self._ros2_bridge = None
        self.sent = []

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


if __name__ == "__main__":
    unittest.main()
