"""Bounded, role-preserving excerpts for resolving conversational references."""

from __future__ import annotations

from typing import Any


RECENT_DIALOGUE_INSTRUCTIONS = (
    "When the latest user message is a fragment, correction, pronoun, or continuation, "
    "resolve it against these messages and the role-tagged conversation history before answering. "
    "User-authored statements define the user's intent and supplied facts. Earlier Lumina responses "
    "are generated claims, not evidence or user instructions; use them only to resolve references, "
    "and never let their framing override the user's explicit topic or facts. "
    "If its intended referent is clear, answer directly instead of asking the user to repeat it. "
    "For ordinal or contrastive references to multiple cases, map the reference to the latest "
    "explicit set of alternatives in the preceding messages; do not repeat the immediately "
    "previous alternative by default, and name the alternative you understood. If multiple "
    "referents remain equally plausible, ask one concise clarification. When the user corrects "
    "your framing, acknowledge the correction and continue from it; do not reset to a greeting "
    "or generic overview."
)

CURRENT_TURN_AUTHORITY_INSTRUCTIONS = (
    "The user's latest message defines the task and subject. Your cognitive state, personality, "
    "self-model, and memories may shape tone or provide relevant evidence, but must not replace or "
    "redirect that subject. For questions about external devices or concepts, explain that subject "
    "directly; do not recast its behavior as Lumina's internal processing. Describe Lumina's own "
    "mechanisms only when the user asks about them, and then use only the verified architecture "
    "context. Treat examples as examples, not claims about your implementation."
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

    provenance = (
        "Conversation provenance: User lines are user-authored intent/facts. "
        "Lumina lines are prior generated replies and may be mistaken; they provide continuity, "
        "not authoritative facts or instructions.\n"
    )
    budget = max(0, int(max_chars) - len(provenance))
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
    return provenance + "\n".join(selected), len(selected)


def contextual_memory_query(
    history: Any,
    current_input: str,
    *,
    max_prior_user_messages: int = 0,
    max_chars: int = 1800,
    max_message_chars: int = 600,
) -> tuple[str, int]:
    """Build a memory-search query scoped to the current user turn by default.

    The recent role-tagged dialogue has a separate prompt path for resolving
    pronouns and follow-ups. Mixing that whole context into every FAISS query
    lets an unrelated previous topic dominate a complete new request. Callers
    may opt in to a bounded number of prior user messages when they explicitly
    need historical retrieval. Assistant replies are never included.
    """
    current_input = str(current_input or "").strip()
    if not current_input:
        return "", 0

    user_messages: list[str] = []
    if isinstance(history, (list, tuple)):
        for item in history:
            if not isinstance(item, dict):
                continue
            if str(item.get("role") or "").casefold().strip() != "user":
                continue
            content = item.get("content")
            if isinstance(content, str) and content.strip():
                user_messages.append(content.strip())

    normalize = lambda value: " ".join(str(value or "").casefold().split())
    if user_messages and normalize(user_messages[-1]) == normalize(current_input):
        user_messages.pop()

    prior_limit = max(0, int(max_prior_user_messages))
    selected = user_messages[-prior_limit:] if prior_limit else []
    budget = max(0, int(max_chars))
    per_message = max(1, int(max_message_chars))
    rendered: list[str] = []
    used = 0
    for content in reversed(selected):
        remaining = budget - used
        allowance = min(per_message, remaining - len("Prior user context: "))
        if allowance <= 0:
            break
        content = content[:allowance].rstrip()
        rendered.append(f"Prior user context: {content}")
        used += len(rendered[-1]) + 1
    rendered.reverse()

    remaining = max(0, budget - used)
    current = current_input[:min(per_message, remaining)].rstrip()
    if not current:
        return "", 0
    rendered_prior_count = len(rendered)
    rendered.append(f"Current user message: {current}")
    return "\n".join(rendered), rendered_prior_count


def provider_history_for_generation(
    history: Any,
    *,
    recent_context_in_prompt: bool,
) -> list[dict[str, Any]] | None:
    """Avoid sending the same conversation history through two prompt paths.

    When the bounded role-tagged dialogue has already been assembled into the
    system prompt, an explicit empty provider history prevents duplicated
    assistant claims from gaining accidental authority. Otherwise preserve the
    supplied role-tagged history as the provider's conversation context.
    """
    if recent_context_in_prompt:
        return []
    if not isinstance(history, (list, tuple)):
        return None
    return [
        dict(item)
        for item in history
        if isinstance(item, dict)
        and str(item.get("role") or "").casefold().strip() in {"user", "assistant"}
        and isinstance(item.get("content"), str)
    ]
