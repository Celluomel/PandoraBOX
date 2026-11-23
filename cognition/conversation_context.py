"""Bounded, role-preserving excerpts for resolving conversational references."""

from __future__ import annotations

from typing import Any


RECENT_DIALOGUE_INSTRUCTIONS = (
    "When the latest user message is a fragment, correction, pronoun, or continuation, "
    "resolve it against these messages and the role-tagged conversation history before answering. "
    "If its intended referent is clear, answer directly instead of asking the user to repeat it. "
    "For ordinal or contrastive references to multiple cases, map the reference to the latest "
    "explicit set of alternatives in the preceding messages; do not repeat the immediately "
    "previous alternative by default, and name the alternative you understood. If multiple "
    "referents remain equally plausible, ask one concise clarification. When the user corrects "
    "your framing, acknowledge the correction and continue from it; do not reset to a greeting "
    "or generic overview."
)


def recent_dialogue_anchor(
    history: Any,
    current_input: str,
    *,
    max_chars: int = 4200,
    max_messages: int = 6,
    max_message_chars: int = 1200,
) -> tuple[str, int]:
    """Select the latest three exchanges, prioritizing the nearest context.

    This is intentionally loss-preserving only within explicit size bounds: it
    retains message order and roles, does not infer keywords or rewrite user
    claims, and spends the character budget from newest to oldest so a long
    earlier answer cannot crowd out the actual last exchange.
    """
    if not isinstance(history, (list, tuple)):
        return "", 0

    messages: list[tuple[str, str]] = []
    for item in history:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").casefold().strip()
        content = item.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            continue
        content = content.strip()
        if content:
            messages.append((role, content))

    current = " ".join(str(current_input or "").casefold().split())
    if messages and messages[-1][0] == "user":
        latest = " ".join(messages[-1][1].casefold().split())
        if latest == current:
            messages.pop()
    message_limit = max(0, int(max_messages))
    if message_limit == 0:
        return "", 0
    messages = messages[-message_limit:]
    if not messages:
        return "", 0

    budget = max(0, int(max_chars))
    per_message = max(1, int(max_message_chars))
    selected: list[str] = []
    used = 0
    for role, content in reversed(messages):
        label = "User" if role == "user" else "Lumina"
        remaining = budget - used
        allowance = min(per_message, remaining - len(label) - 3)
        if allowance <= 0:
            break
        if len(content) > allowance:
            content = content[:max(0, allowance - 1)].rstrip() + "…"
        line = f"{label}: {content}"
        selected.append(line)
        used += len(line) + 1

    selected.reverse()
    if not selected:
        return "", 0
    return "\n".join(selected), len(selected)
