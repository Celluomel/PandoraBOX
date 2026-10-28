"""Non-invasive reproducibility gates for the cognitive experiment.

These checks do not claim to measure subjective consciousness.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ExperimentSafetyGates(unittest.TestCase):
    def test_brain_runner_parses(self):
        path = ROOT / "brain.py"
        self.assertTrue(path.is_file(), "Missing headless brain runner")
        ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))

    def test_experiment_protocol_covers_controls(self):
        protocol = (ROOT / "experiments/sentience/README.md").read_text(encoding="utf-8").lower()
        for term in ("persistence", "autonomy", "affect", "self-model", "control", "temporary storage"):
            with self.subTest(term=term):
                self.assertIn(term, protocol)

    def test_no_executable_hardware_or_memory_access_in_this_suite(self):
        source = Path(__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        banned = {"subprocess", "socket", "requests", "serial", "sqlite3", "faiss"}
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertFalse(imports & banned)


if __name__ == "__main__":
    unittest.main()
