"""Conversation-history policy for telemetry-grounded self-reports."""
from __future__ import annotations

from typing import Any


def history_without_assistant_claims(history: Any) -> tuple[list[dict], dict[str, int]]:
    """Keep user-authored context while excluding prior model claims as evidence.

    This is intentionally narrow: factual self-reports receive current structured
    telemetry in the system prompt, so previous assistant answers must not
    compete with that telemetry as a source of facts. User turns remain available
    to preserve the conversation topic and corrections.
    """
    if not isinstance(history, list):
        return [], {"retained_user_messages": 0, "excluded_assistant_messages": 0}

    retained: list[dict] = []
    retained_users = 0
    excluded_assistant = 0
    for item in history:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        if role == "assistant":
            if str(item.get("content") or "").strip():
                excluded_assistant += 1
            continue
        if role == "user" and str(item.get("content") or "").strip():
            retained.append(dict(item))
            retained_users += 1
    return retained, {
        "retained_user_messages": retained_users,
        "excluded_assistant_messages": excluded_assistant,
    }
