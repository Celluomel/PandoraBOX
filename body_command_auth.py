"""Shared, fail-closed signing contract for Brain-approved Body commands."""
from __future__ import annotations

import hashlib
import hmac
import json
import math
from typing import Any, Mapping


def approval_message(command: Mapping[str, Any]) -> bytes:
    """Canonical bytes bind approval to the exact action and delivery window."""
    fields = {
        "version": 1,
        "command_id": str(command.get("command_id") or ""),
        "target": str(command.get("target") or ""),
        "action": str(command.get("action") or ""),
        "payload": command.get("payload") if isinstance(command.get("payload"), dict) else {},
        "created_at": _finite_number(command.get("created_at")),
        "expires_at": _finite_number(command.get("expires_at")),
        "approved_at": _finite_number(command.get("approved_at")),
        "approved_by": str(command.get("approved_by") or ""),
        "requires_confirmation": bool(command.get("requires_confirmation", True)),
        "origin": str(command.get("origin") or ""),
    }
    return json.dumps(fields, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sign_approval(command: Mapping[str, Any], secret: str) -> str:
    key = str(secret or "").encode("utf-8")
    if len(key) < 32:
        return ""
    try:
        message = approval_message(command)
    except (TypeError, ValueError, OverflowError):
        return ""
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def verify_approval(command: Mapping[str, Any], secret: str, *, now: float, max_age_s: float = 300.0) -> bool:
    proof = str(command.get("approval_proof") or "")
    approved_at = _finite_number(command.get("approved_at"))
    expires_at = _finite_number(command.get("expires_at"))
    created_at = _finite_number(command.get("created_at"))
    now = _finite_number(now)
    max_age_s = _finite_number(max_age_s)
    if not proof or not command.get("command_id") or not command.get("action"):
        return False
    if len(str(secret or "").encode("utf-8")) < 32:
        return False
    if approved_at is None or expires_at is None or created_at is None:
        return False
    if now is None or max_age_s is None or max_age_s <= 0:
        return False
    if (approved_at > now + 5.0 or created_at > approved_at + 5.0
            or now - approved_at > max_age_s or approved_at >= expires_at
            or expires_at <= now):
        return False
    expected = sign_approval(command, secret)
    return bool(expected) and hmac.compare_digest(proof, expected)


def _finite_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None
