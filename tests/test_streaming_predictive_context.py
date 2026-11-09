import sys
import threading
import types
import unittest
from unittest.mock import Mock


class StreamingPredictiveContextTests(unittest.TestCase):
    def test_cognitive_organism_prepares_pcm_wsdm_and_prospective_stages(self):
        from cognition.cognitive_organism import CognitiveOrganism

        pcm = Mock()
        pcm.classify.return_value = "reasoning"
        pcm.read_state.return_value = [0.7, 0.8, 0.6]
        pcm.predict_and_advise.return_value = "Consider the uncertainty."
        wsdm = Mock()
        wsdm.narrative_summary.return_value = "Prior reasoning outcomes are mixed."
        organism = CognitiveOrganism.__new__(CognitiveOrganism)
        organism._loop = types.SimpleNamespace(
            _consequence_model=pcm,
            _world_self_dynamics=wsdm,
        )
        organism.ai_system = types.SimpleNamespace(_interaction_count=12)
        prospective = types.ModuleType("cognition.prospective_deliberation")
        prospective.deliberate = Mock(return_value=types.SimpleNamespace(
            advisory="Compare alternatives before answering.",
        ))

        original = sys.modules.get("cognition.prospective_deliberation")
        sys.modules["cognition.prospective_deliberation"] = prospective
        try:
            result = organism.prepare_response_context(
                "Which option is more reliable?", user_id="lumina_peer_flux",
            )
        finally:
            if original is None:
                sys.modules.pop("cognition.prospective_deliberation", None)
            else:
                sys.modules["cognition.prospective_deliberation"] = original

        pcm.record_action.assert_called_once_with(
            "reasoning", [0.7, 0.8, 0.6], interaction_n=12,
        )
        wsdm.record_context.assert_called_once_with(
            action_type="reasoning",
            user_id="lumina_peer_flux",
            interaction_n=12,
        )
        prospective.deliberate.assert_called_once_with(
            pcm, wsdm, "reasoning", [0.7, 0.8, 0.6],
            user_id="lumina_peer_flux",
        )
        self.assertEqual(result["pcm_status"], "prepared")
        self.assertEqual(result["wsdm_status"], "prepared")
        self.assertEqual(result["prospective_status"], "completed")
        self.assertIn("Consider the uncertainty.", result["pcm_advisory"])
        self.assertIn("Compare alternatives", result["pcm_advisory"])
        self.assertEqual(result["wsdm_narrative"], "Prior reasoning outcomes are mixed.")

    def test_persona_bridge_traces_pre_llm_predictive_modules(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {"stages": {}}
        bridge._organism = types.SimpleNamespace(prepare_response_context=Mock(return_value={
            "pcm_status": "prepared",
            "pcm_advisory": "Use cautious inference.",
            "wsdm_status": "prepared",
            "wsdm_narrative": "Recent outcomes vary.",
            "prospective_status": "not_applicable",
        }))

        context = bridge._prepare_predictive_context("peer turn", "lumina_peer_flux")

        self.assertIn("Use cautious inference.", context)
        self.assertIn("Recent outcomes vary.", context)
        self.assertEqual(
            bridge._last_turn_trace["stages"]["predictive_consequence_model"]["status"],
            "prepared",
        )
        self.assertEqual(
            bridge._last_turn_trace["stages"]["world_self_dynamics_model"]["status"],
            "prepared",
        )
        self.assertEqual(
            bridge._last_turn_trace["stages"]["prospective_deliberation"]["status"],
            "not_applicable",
        )

    def test_missing_predictive_modules_are_traced_as_skipped(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._turn_trace_lock = threading.Lock()
        bridge._last_turn_trace = {"stages": {}}
        bridge._organism = None

        self.assertEqual(bridge._prepare_predictive_context("turn", "fred"), "")
        for stage in (
            "predictive_consequence_model",
            "world_self_dynamics_model",
            "prospective_deliberation",
        ):
            self.assertEqual(bridge._last_turn_trace["stages"][stage]["status"], "skipped_unavailable")


if __name__ == "__main__":
    unittest.main()
