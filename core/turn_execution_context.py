"""Context-local identity for correlating module calls with one cognitive turn."""

from __future__ import annotations

from contextvars import ContextVar
import re


current_turn_id: ContextVar[str] = ContextVar("lumina_current_turn_id", default="")
_SAFE_TURN_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")


def normalize_turn_id(value: object) -> str:
    candidate = str(value or "")
    return candidate if _SAFE_TURN_ID.fullmatch(candidate) else ""


def set_current_turn_id(value: object):
    """Set a bounded, opaque trace ID and return its ContextVar reset token."""
    return current_turn_id.set(normalize_turn_id(value))
