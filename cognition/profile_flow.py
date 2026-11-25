"""Scope and receipt helpers for learned behavioral user profiles."""

from __future__ import annotations

import re
from typing import Any


_PROFILE_LEARNING_OPTOUT_PATTERNS = (
    re.compile(
        r"\b(?:do\s+not|don't|never)\s+.{0,100}\b"
        r"(?:add|put|include|save|store|record|learn)\b.{0,80}\b"
        r"(?:to|in|into|on)\s+(?:my|the\s+user)\s+profile\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bne\s+(?:l['’])?(?:ajoute|mets|inscris|enregistre|"
        r"stocke|apprends|consigne)\b.{0,80}\bpas\b.{0,80}\b"
        r"(?:dans|à|sur)\s+(?:mon|notre)\s+profil\b",
        re.IGNORECASE,
    ),
)


def has_explicit_profile_learning_opt_out(user_text: str) -> bool:
    """Recognize an explicit request not to add this turn to a user profile."""
    text = " ".join(str(user_text or "").split())
    return any(pattern.search(text) for pattern in _PROFILE_LEARNING_OPTOUT_PATTERNS)


def update_behavioral_user_profile(
    world_model: Any,
    *,
    user_id: str,
    user_text: str,
    response: str,
    emotion: str,
    human_interaction: bool,
    learn_semantic_profile: bool = True,
) -> dict:
    """Update a human profile and return a safe receipt; never learn from peer turns."""
    if not human_interaction:
        return {"status": "skipped_by_scope", "changed": False}
    if has_explicit_profile_learning_opt_out(user_text):
        return {
            "status": "skipped_explicit_opt_out",
            "changed": False,
            "persisted": False,
            "learning_scope": "none",
            "extracted_count": 0,
            "categories_updated": [],
        }
    if world_model is None or not callable(getattr(world_model, "update_from_interaction", None)):
        return {"status": "unavailable", "changed": False}
    try:
        update_with_receipt = getattr(
            world_model, "update_from_interaction_with_receipt", None,
        )
        if callable(update_with_receipt):
            profile, update_receipt = update_with_receipt(
                user_id=user_id,
                user_text=user_text,
                response=response,
                emotion=emotion,
                learn_semantic_profile=learn_semantic_profile,
            )
            update_receipt = update_receipt if isinstance(update_receipt, dict) else {}
            if profile is None:
                return {
                    **update_receipt,
                    "status": "persistence_failed",
                    "changed": True,
                    "persisted": False,
                }
            return {
                **update_receipt,
                "status": "updated",
                "changed": True,
                "persisted": True,
                "learning_scope": update_receipt.get("learning_scope"),
                "interaction_count": getattr(profile, "interaction_count", None),
            }

        profile = world_model.update_from_interaction(
            user_id=user_id, user_text=user_text,
            response=response, emotion=emotion,
        )
        if profile is None:
            return {
                "status": "persistence_failed",
                "changed": True,
                "persisted": False,
            }
        return {
            "status": "updated" if profile is not None else "no_profile_returned",
            "changed": profile is not None,
            "persisted": True,
            "interaction_count": getattr(profile, "interaction_count", None),
        }
    except Exception as exc:
        return {"status": "failed", "changed": False, "error_type": type(exc).__name__}
