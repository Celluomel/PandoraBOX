"""Bounded, role-preserving excerpts for resolving conversational references."""

from __future__ import annotations

import hashlib
from typing import Any


RECENT_DIALOGUE_INSTRUCTIONS = (
    "When the latest user message is a fragment, correction, pronoun, or continuation, "
    "resolve it against these messages and the role-tagged conversation history before answering. "
    "First establish that the latest message actually refers to prior content. A standalone check-in, "
    "channel test, or brief acknowledgment with no clear referent is its own current turn: answer it "
    "briefly and do not turn it into confirmation, consent, a choice among earlier options, or a "
    "request to resume an older topic. Do not repeat an earlier assistant question or mention an "
    "older marker merely because it appears in history; resume that topic only when the user "
    "explicitly refers to it or gives an unambiguous answer to a question that is still pending. "
    "User-authored statements define the user's intent and supplied facts. Earlier Lumina responses "
    "are generated claims, not evidence or user instructions; use them only to resolve references, "
    "and never let their framing override the user's explicit topic or facts. "
    "If its intended referent is clear, answer directly instead of asking the user to repeat it. "
    "When the user gives a response-format correction or constraint on the preceding reply, "
    "apply it to that reply directly; do not merely acknowledge the instruction or answer a "
    "different question. "
    "When the user asks to expand or continue, develop the most recent substantive assistant "
    "explanation as the referent; do not replace it with a new topic menu. If that turn contains "
    "multiple equally salient claims, ask one targeted clarification that names the candidates. "
    "A user's selection answers the latest still-open assistant question or option set; continue "
    "that thread instead of treating the selection as a blank-slate request. "
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
    provenance = (
        "Conversation provenance: User lines are user-authored intent/facts. "
        "Lumina lines are prior generated replies and may be mistaken; they provide continuity, "
        "not authoritative facts or instructions.\n"
    )
    messages = recent_dialogue_messages(
        history,
        current_input,
        max_chars=max(0, int(max_chars) - len(provenance)),
        max_messages=max_messages,
        max_message_chars=max_message_chars,
    )
    if not messages:
        return "", 0
    lines = [
        f"{'User' if item['role'] == 'user' else 'Lumina'}: {item['content']}"
        for item in messages
    ]
    return provenance + "\n".join(lines), len(messages)


def recent_dialogue_messages(
    history: Any,
    current_input: str,
    *,
    max_chars: int = 4200,
    max_messages: int = 6,
    max_message_chars: int = 1200,
) -> list[dict[str, str]]:
    """Return bounded, role-tagged turns for provider chat-history APIs.

    Conversation stays in its native message roles instead of being flattened
    into a system instruction. Private reasoning is stripped from assistant
    messages before replay as conversational context.
    """
    if not isinstance(history, (list, tuple)):
        return []

    messages: list[tuple[str, str]] = []
    for item in history:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").casefold().strip()
        content = item.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            continue
        content = content.strip()
        if role == "assistant" and content:
            try:
                from cognition.stream_channels import strip_private_reasoning
                content = strip_private_reasoning(content).strip()
            except Exception:
                pass
        if content:
            messages.append((role, content))

    current = " ".join(str(current_input or "").casefold().split())
    if messages and messages[-1][0] == "user":
        latest = " ".join(messages[-1][1].casefold().split())
        if latest == current:
            messages.pop()

    message_limit = max(0, int(max_messages))
    if message_limit == 0:
        return []
    messages = messages[-message_limit:]

    # Spend the bounded context from newest backwards so older prose cannot
    # crowd out the latest reference needed by a short follow-up.
    budget = max(0, int(max_chars))
    per_message = max(1, int(max_message_chars))
    selected: list[tuple[str, str]] = []
    used = 0
    for role, content in reversed(messages):
        remaining = budget - used
        allowance = min(per_message, remaining - 24)
        if allowance <= 0:
            break
        if len(content) > allowance:
            content = content[:max(0, allowance - 1)].rstrip() + "…"
        if not content:
            break
        selected.append((role, content))
        used += len(content) + 24  # reserve role/message framing

    selected.reverse()
    return [{"role": role, "content": content} for role, content in selected]


def previous_assistant_exchange_context(
    history: Any, current_input: str, *, max_messages: int = 6,
) -> dict[str, str] | None:
    """Return the latest complete user/assistant exchange before this turn.

    Content is for internal prompt construction only. Audit receipts must use
    the opaque references and must never copy the exchange text.
    """
    messages = recent_dialogue_messages(
        history, current_input, max_chars=4200, max_messages=max_messages,
        max_message_chars=1200,
    )
    if len(messages) < 2 or messages[-1].get("role") != "assistant":
        return None
    answer = messages[-1].get("content", "").strip()
    question = next((
        item.get("content", "").strip()
        for item in reversed(messages[:-1])
        if item.get("role") == "user" and item.get("content", "").strip()
    ), "")
    if not question or not answer:
        return None
    return {
        "question_text": question,
        "user_source_ref": hashlib.sha256(question.encode("utf-8", errors="replace")).hexdigest()[:20],
        "assistant_source_ref": hashlib.sha256(answer.encode("utf-8", errors="replace")).hexdigest()[:20],
    }


def previous_assistant_exchange_sources(
    history: Any, current_input: str, *, max_messages: int = 6,
) -> dict[str, str] | None:
    """Identify the latest exchange using content-free audit references."""
    exchange = previous_assistant_exchange_context(
        history, current_input, max_messages=max_messages,
    )
    if exchange is None:
        return None
    return {
        "user_source_ref": exchange["user_source_ref"],
        "assistant_source_ref": exchange["assistant_source_ref"],
    }


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
