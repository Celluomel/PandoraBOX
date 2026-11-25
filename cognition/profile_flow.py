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

_PROFILE_FACT_QUERY_TERMS = re.compile(
    r"\b(?:what|which|what's|whats|list|show|tell\s+me|do\s+you\s+have|"
    r"what\s+is|que|quel(?:le)?s?|quels?|quelles|liste|montre|"
    r"dis[- ]moi|selon|d['’]apr[eè]s)\b",
    re.IGNORECASE,
)
_PROFILE_FACT_SUBJECT = re.compile(
    r"\b(?:my|your|user)\s+(?:(?:named|stored|saved|user)\s+)?profile\b|"
    r"\b(?:mon|ma|notre|votre)\s+profil(?:e)?\b",
    re.IGNORECASE,
)
_PROFILE_FACT_UPDATE_INTENT = re.compile(
    r"^\s*(?:please\s+)?(?:add|put|include|save|store|record|update|change|remove)\b"
    r".{0,100}\b(?:to|into|in)\s+(?:my|the\s+user)\s+profile\b|"
    r"^\s*(?:(?:s['’]il\s+te\s+pla[iî]t)\s+)?"
    r"(?:ajoute|mets|enregistre|stocke|modifie|change|supprime)\b"
    r".{0,100}\b(?:à|dans|sur)\s+(?:mon|notre)\s+profil\b",
    re.IGNORECASE,
)


def is_explicit_named_profile_query(user_text: str) -> bool:
    """Recognize a question asking for facts from the named user profile."""
    text = " ".join(str(user_text or "").split())
    return bool(
        _PROFILE_FACT_SUBJECT.search(text)
        and _PROFILE_FACT_QUERY_TERMS.search(text)
        and not _PROFILE_FACT_UPDATE_INTENT.search(text)
    )


def render_explicit_profile_facts(
    facts: list[dict], user_text: str,
) -> dict[str, object]:
    """Render a direct answer from provenance-backed profile values only."""
    text = str(user_text or "").casefold()
    french = bool(
        re.search(r"\b(?:mon|ma|notre|votre|quelle|quelles|selon|enregistr[eé])\b", text)
        or re.search(r"[àâçéèêëîïôùûüÿœ]", text)
    )
    wants_preferences = bool(re.search(r"\b(?:preference|preferences|pr[eé]f[eé]rence|pr[eé]f[eé]rences)\b", text))
    eligible = [
        item for item in facts
        if isinstance(item, dict)
        and isinstance(item.get("value"), str)
        and item.get("category") in {"preference", "dislike", "interest", "characteristic"}
        and (not wants_preferences or item.get("category") == "preference")
    ]
    if not eligible:
        answer = (
            "Le profil utilisateur nommé ne contient aucun fait explicite avec une provenance utilisateur pour cette demande."
            if french else
            "The named user profile contains no provenance-backed explicit fact for that request."
        )
        return {"answer": answer, "fact_count": 0, "categories": [], "status": "empty"}

    labels = {
        "preference": "préférence" if french else "preference",
        "dislike": "aversion" if french else "dislike",
        "interest": "centre d’intérêt" if french else "interest",
        "characteristic": "caractéristique" if french else "characteristic",
    }
    grouped: dict[str, list[str]] = {}
    for item in eligible:
        grouped.setdefault(str(item["category"]), []).append(str(item["value"]))
    details = [
        f"{labels[category]}: " + "; ".join(values)
        for category, values in grouped.items()
    ]
    answer = (
        "Dans le profil utilisateur nommé, les faits explicitement enregistrés sont : "
        + ". ".join(details) + "."
        if french else
        "The explicitly recorded facts in the named user profile are: "
        + ". ".join(details) + "."
    )
    return {
        "answer": answer,
        "fact_count": len(eligible),
        "categories": sorted(grouped),
        "status": "rendered_from_provenance_backed_profile",
    }


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
