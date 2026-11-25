"""Scope and receipt helpers for learned behavioral user profiles."""

from __future__ import annotations

from typing import Any


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
