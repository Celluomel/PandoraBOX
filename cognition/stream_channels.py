"""Sanitize private reasoning markers at model output boundaries."""

from __future__ import annotations

import re


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
