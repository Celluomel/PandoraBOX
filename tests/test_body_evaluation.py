import unittest

from body_runtime_host.worldmodel.evaluation import run_shuffled_trials


class BodyEvaluationTests(unittest.TestCase):
    def test_generic_plan_survives_shuffled_scenes(self):
        result = run_shuffled_trials(trials=5, max_steps=180)

        self.assertEqual(result["trials"], 5)
        self.assertEqual(result["successes"], 5)
        self.assertEqual(result["collisions"], 0)
        self.assertIn("near_misses", result)
        self.assertIn("near_misses", result["baseline_without_recovery"])
        self.assertTrue(all(item["success"] for item in result["results"]))


if __name__ == "__main__":
    unittest.main()
