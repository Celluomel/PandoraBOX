from datetime import datetime, timezone

from cognition.temporal_reasoning import build_temporal_frame


def test_temporal_prompt_provides_facts_without_narrating_prompt_instructions():
    frame = build_temporal_frame(
        "I need to arrive in 2 hours.",
        now=datetime(2026, 11, 22, 12, 0, tzinfo=timezone.utc),
    )

    fragment = frame.prompt_fragment()

    assert f"Reference instant: {frame.now.strftime('%Y-%m-%d %H:%M %Z')}" in fragment
    assert "User-stated duration: 2 hour(s)" in fragment
    assert (
        "Computed deadline, when a duration is available: "
        f"{frame.deadline.strftime('%Y-%m-%d %H:%M %Z')}"
    ) in fragment
    assert "internal reasoning" not in fragment.casefold()
    assert "use this frame silently" not in fragment.casefold()
    assert "do not mention t0" not in fragment.casefold()


def test_temporal_prompt_has_no_meta_instruction_added_to_user_message():
    from pathlib import Path

    source = Path("cognition/persona_bridge.py").read_text(encoding="utf-8")

    assert "Use the temporal frame only as internal reasoning" not in source
