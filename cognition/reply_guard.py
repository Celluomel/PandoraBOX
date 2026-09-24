"""Small, deterministic guards against verbatim long-answer loops."""
import re


def repeats_recent_assistant_reply(candidate: str, history: list[dict], min_chars: int = 80) -> bool:
    normalized = re.sub(r"\W+", "", str(candidate or "").casefold())
    if len(normalized) < min_chars:
        return False
    return any(
        normalized == re.sub(r"\W+", "", str(item.get("content", "") or "").casefold())
        for item in history
        if isinstance(item, dict) and item.get("role") == "assistant"
    )
