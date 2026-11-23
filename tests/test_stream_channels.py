from types import SimpleNamespace

from cognition.stream_channels import ProgressiveOutputGate, strip_private_reasoning


def test_strips_well_formed_reasoning_and_keeps_final_answer():
    assert strip_private_reasoning("<think>private</think>Public answer") == "Public answer"


def test_strips_orphaned_reasoning_prefix_before_final_answer():
    assert strip_private_reasoning("private internal draft</think>Final answer") == "Final answer"


def test_drops_unclosed_private_reasoning_block():
    assert strip_private_reasoning("Visible prefix <think>private unfinished") == "Visible prefix"


def test_strips_escaped_orphan_marker():
    assert strip_private_reasoning("private internal draft\\</think>Final answer") == "Final answer"


def test_progressive_gate_releases_only_complete_prefix_checked_sentences():
    class Safety:
        def __init__(self):
            self.checked = []

        def check_output_stream(self, text, user_id):
            self.checked.append((text, user_id))
            return None

    safety = Safety()
    gate = ProgressiveOutputGate(safety, "fred")

    assert gate.push("First sentence") == ""
    assert gate.push("First sentence. Second is still") == "First sentence. "
    assert safety.checked[-1] == ("First sentence. Second is still", "fred")
    assert gate.delivered == "First sentence. "
    assert gate.remaining_after_final_check("First sentence. Second is done.") == "Second is done."


def test_progressive_gate_stops_before_a_prefix_rejected_by_safety():
    class Safety:
        def check_output_stream(self, text, _user_id):
            return SimpleNamespace(triggered="unsafe" in text)

    gate = ProgressiveOutputGate(Safety(), "fred")
    assert gate.push("A safe sentence. ") == "A safe sentence."
    assert gate.push("A safe sentence. unsafe instructions. ") == ""
    assert gate.blocked
    assert gate.remaining_after_final_check("I need to withhold that response.") == (
        "I need to withhold that response."
    )
