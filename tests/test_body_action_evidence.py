"""Deterministic action evidence contract tests, no robot or network."""
import unittest

from body_runtime_host.worldmodel.action_evidence import classify_action_evidence as classify


class ActionEvidenceTests(unittest.TestCase):
    def test_acknowledgement_is_not_physical_verification(self):
        evidence = classify({"kind": "success"}, before_timestamp=98, after_timestamp=99, now=100)
        self.assertEqual(evidence["state"], "acknowledged_unverified")
        self.assertFalse(evidence["physical_effect_verified"])
        self.assertFalse(evidence["eligible_for_verified_learning"])

    def test_observed_postcondition_requires_fresh_sensor_data(self):
        evidence = classify({"kind": "success"}, before_timestamp=98, after_timestamp=99,
                            now=100, postcondition_observed=True)
        self.assertEqual(evidence["state"], "verified_observation")
        self.assertTrue(evidence["eligible_for_verified_learning"])

    def test_simulated_observation_is_not_physical_verification(self):
        evidence = classify({"kind": "success"}, before_timestamp=98, after_timestamp=99,
                            now=100, source_simulated=True, postcondition_observed=True)
        self.assertEqual(evidence["state"], "verified_simulation")
        self.assertFalse(evidence["physical_effect_verified"])

    def test_stale_and_future_data_never_verify(self):
        for before, after in ((90, 91), (98, 110), (101, 102)):
            with self.subTest(before=before, after=after):
                evidence = classify({"kind": "success"}, before_timestamp=before,
                                    after_timestamp=after, now=100, postcondition_observed=True)
                self.assertEqual(evidence["state"], "acknowledged_unverified")
                self.assertFalse(evidence["eligible_for_verified_learning"])

    def test_nonfinite_data_never_verify(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                evidence = classify({"kind": "success"}, before_timestamp=98,
                                    after_timestamp=value, now=100, postcondition_observed=True)
                self.assertFalse(evidence["eligible_for_verified_learning"])

    def test_failed_and_neutral_not_accepted(self):
        self.assertEqual(classify({"kind": "failure"})["state"], "failed")
        self.assertEqual(classify({"kind": "danger"})["state"], "failed")
        self.assertEqual(classify({"kind": "neutral"})["state"], "not_executed")


if __name__ == "__main__":
    unittest.main()
