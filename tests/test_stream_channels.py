from cognition.stream_channels import strip_private_reasoning


def test_strips_well_formed_reasoning_and_keeps_final_answer():
    assert strip_private_reasoning("<think>private</think>Public answer") == "Public answer"


def test_strips_orphaned_reasoning_prefix_before_final_answer():
    assert strip_private_reasoning("private internal draft</think>Final answer") == "Final answer"


def test_drops_unclosed_private_reasoning_block():
    assert strip_private_reasoning("Visible prefix <think>private unfinished") == "Visible prefix"


def test_strips_escaped_orphan_marker():
    assert strip_private_reasoning("private internal draft\\</think>Final answer") == "Final answer"
