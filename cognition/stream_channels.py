"""Sanitize private reasoning markers at model output boundaries."""

from __future__ import annotations

import re
import time
from typing import Any


_ESCAPED_CHANNEL_MARKER = re.compile(
    r"\\+\s*(</?(?:think|analysis)>)", re.IGNORECASE,
)
_PAIRED_PRIVATE_BLOCK = re.compile(
    r"<(think|analysis)>[\s\S]*?</\1\s*>", re.IGNORECASE,
)
_PRIVATE_OPEN = re.compile(r"<(?:think|analysis)>[\s\S]*$", re.IGNORECASE)
_PRIVATE_CLOSE = re.compile(r"</(?:think|analysis)\s*>", re.IGNORECASE)


def strip_private_reasoning(text: str) -> str:
    """Return only user-facing text, including for malformed/orphan tags.

    Some local chat templates emit a reasoning prefix followed by a closing
    ``</think>`` marker but omit its opening marker. Treat the prefix as private
    instead of preserving it as visible answer text.
    """
    value = str(text or "")
    value = _ESCAPED_CHANNEL_MARKER.sub(r"\1", value)
    value = _PAIRED_PRIVATE_BLOCK.sub("", value)
    close = _PRIVATE_CLOSE.search(value)
    if close:
        value = value[close.end():]
    value = _PRIVATE_OPEN.sub("", value)
    return value.strip()


class ProgressiveOutputGate:
    """Release complete, currently-safe sentences while preserving final approval.

    This is an early-delivery gate, not a replacement for the whole-response
    output check. The caller must still run final policy and semantic guards
    before delivering the terminal response.
    """

    _SENTENCE_END = re.compile(r"(?:[.!?…][\"'”’)]*(?:\s+|$)|\n+)")

    def __init__(self, safety: Any, user_id: str = "unknown"):
        self._safety = safety
        self._user_id = user_id
        self.started_at = time.perf_counter()
        self.first_release_ms: float | None = None
        self.delivered = ""
        self.blocked = False

    def push(self, accumulated: str) -> str:
        """Return newly completed sentence text only after prefix safety passes."""
        if self.blocked or self._safety is None:
            return ""

        visible = strip_private_reasoning(accumulated)
        if not visible.startswith(self.delivered):
            # A later channel marker changed text that was already visible;
            # stop progressive delivery and let final sanitation decide.
            self.blocked = True
            return ""

        checker = getattr(self._safety, "check_output_stream", None)
        if not callable(checker):
            self.blocked = True
            return ""
        try:
            result = checker(visible, self._user_id)
        except Exception:
            self.blocked = True
            return ""
        if result is not None and bool(getattr(result, "triggered", False)):
            self.blocked = True
            return ""

        complete_end = 0
        for match in self._SENTENCE_END.finditer(visible):
            if match.end() > len(self.delivered):
                complete_end = match.end()
        if complete_end <= len(self.delivered):
            return ""

        chunk = visible[len(self.delivered):complete_end]
        self.delivered += chunk
        if self.first_release_ms is None:
            self.first_release_ms = round((time.perf_counter() - self.started_at) * 1000, 1)
        return chunk

    def remaining_after_final_check(self, approved_response: str) -> str:
        """Return the tail after final approval, or the whole approved replacement."""
        approved = str(approved_response or "")
        if self.delivered and approved.startswith(self.delivered):
            return approved[len(self.delivered):]
        return approved
