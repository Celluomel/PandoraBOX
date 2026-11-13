"""Effect receipts must distinguish real updates from no-op outcome hooks."""
from pathlib import Path
from types import SimpleNamespace
import ast
import threading

from cognition.abstract_reasoning_engine import AbstractReasoningEngine, ReasoningResult
from cognition.empathy_engine import (
    AffectRead,
    EmpathyEngine,
    SIGNAL_EXPLORING,
    UserAffectModel,
)


ROOT = Path(__file__).resolve().parents[1]


class _Attractors:
    def __init__(self):
        self.values = {"curiosity": 0.5, "analytical_depth": 0.5}

    def get(self, trait):
        return self.values[trait]

    def nudge(self, trait, delta):
        self.values[trait] += delta


class _RelationalMemory:
    def __init__(self):
        self.relationship = SimpleNamespace(interaction_count=4)

    def get_or_create(self, _user_id):
        return self.relationship

    def record_exchange(self, **_kwargs):
        self.relationship.interaction_count += 1
        return self.relationship


def _empathy(*, has_read=True):
    engine = object.__new__(EmpathyEngine)
    engine._lock = threading.RLock()
    engine._last_reads = {}
    engine._models = {}
    engine._org = SimpleNamespace(attractor_system=_Attractors())
    engine._rm = _RelationalMemory()
    if has_read:
        engine._last_reads["u"] = AffectRead(
            user_id="u", signals=[SIGNAL_EXPLORING], valence="neutral", arousal="medium"
        )
        engine._models["u"] = UserAffectModel(user_id="u")
    return engine


def test_empathy_receipt_confirms_counter_and_trait_changes_without_claiming_durability():
    receipt = _empathy().record_outcome("u", "question", "answer")
    assert receipt == {
        "status": "updated",
        "relational_interaction_increment": 1,
        "attractor_traits_changed": 2,
        "persistence": "attempted_unverified",
    }


def test_empathy_without_prior_read_is_an_explicit_skip():
    receipt = _empathy(has_read=False).record_outcome("u", "question", "answer")
    assert receipt["status"] == "skipped_no_prior_affect_read"
    assert receipt["relational_interaction_increment"] == 0


def _are(result, beliefs=None):
    engine = object.__new__(AbstractReasoningEngine)
    engine._lock = threading.Lock()
    engine._cache = {"u": result} if result else {}
    engine._org = SimpleNamespace(
        world_model=SimpleNamespace(causal_beliefs=beliefs or [])
    )
    return engine


def test_abstract_reasoning_does_not_validate_its_own_insight_by_repetition():
    belief = SimpleNamespace(antecedent="a", consequent="b", confidence=0.4)
    engine = _are(ReasoningResult(user_id="u", causal_pair=("a", "b")), [belief])
    receipt = engine.record_outcome("u", "response repeats the insight")
    assert receipt == {
        "status": "skipped_no_independent_outcome_evidence",
        "beliefs_updated": 0,
        "causal_pair_available": True,
    }
    assert belief.confidence == 0.4


def test_abstract_reasoning_without_a_current_result_is_an_explicit_skip():
    engine = _are(ReasoningResult(user_id="u", causal_pair=("a", "b")))
    engine._cache.clear()
    receipt = engine.record_outcome("u", "response")
    assert receipt == {"status": "skipped_no_current_result", "beliefs_updated": 0}


def test_post_turn_reducer_handles_effect_receipts_before_generic_completed_branch():
    source = ROOT / "cognition" / "persona_bridge.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    bridge = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge")
    method = next(
        node for node in bridge.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_stream_with_full_lifecycle"
    )
    body = ast.get_source_segment(source.read_text(encoding="utf-8"), method)
    assert body is not None
    assert '"skipped_no_prior_affect_read"' in body
    assert '"skipped_no_independent_outcome_evidence"' in body
    assert "invalid or unreported effect receipt" in body
    assert body.index("elif stage_name in {\"empathy_outcome\", \"abstract_reasoning_outcome\"}") < body.rindex("else:\n                    self._record_turn_stage(")
