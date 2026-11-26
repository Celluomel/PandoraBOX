"""Scope and receipt helpers for learned behavioral user profiles."""

from __future__ import annotations

import re
import threading
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

_PROFILE_LOOKUP_EXAMPLES = (
    "What facts and preferences are explicitly stored in the named user profile?",
    "According to the saved user profile, which preferences or characteristics are recorded?",
    "Retrieve a provenance-backed fact from the person's persistent profile.",
    "Quelles préférences et caractéristiques sont explicitement enregistrées dans le profil utilisateur ?",
    "D'après les faits sauvegardés dans mon profil, quelles préférences sont enregistrées ?",
    "¿Qué hechos y preferencias están guardados explícitamente en el perfil de usuario?",
    "Welche Fakten und Präferenzen sind ausdrücklich im Benutzerprofil gespeichert?",
    "Welche Angaben über mich sind in meinem dauerhaften Nutzerprofil festgehalten?",
    "Nenne die Fakten, die ausdrücklich in meinem gespeicherten Benutzerprofil stehen.",
)
_HISTORY_RECALL_EXAMPLES = (
    "Recall a concern or fact that the user stated in an earlier conversation or chat.",
    "What did the user previously say in our past conversations? Retrieve that historical statement.",
    "Find an earlier user-authored message and report what it said, using conversation memory.",
    "Qu'est-ce que l'utilisateur a dit dans nos conversations précédentes ? Retrouve cette déclaration historique.",
    "Rappelle-moi un fait ou une préoccupation exprimée auparavant dans nos échanges.",
    "What concern had I raised in an earlier conversation about memory recall and how the user profile learns from exchanges?",
    "What did I previously say about memory recall and building my profile?",
    "Recall my earlier statement about memory recall and how the user profile is built.",
    "Quelle préoccupation avais-je exprimée lors de conversations antérieures concernant la mémoire et la construction du profil utilisateur ?",
    "Rappelle-moi ce que j'avais dit précédemment sur le rappel de mémoire et la façon dont mon profil utilisateur est construit.",
    "¿Qué preocupación expresé en conversaciones anteriores sobre la recuperación de memoria?",
    "¿Qué dije anteriormente sobre cómo se recuerda nuestra conversación?",
    "Welche Sorge habe ich in früheren Gesprächen über den Speicherabruf geäußert?",
    "Was habe ich zuvor über das Erinnern an unsere Gespräche gesagt?",
    "Rufe meine Aussage aus einem früheren Gespräch über das Gedächtnis ab.",
    "Was habe ich in unseren früheren Unterhaltungen zur Erinnerung gesagt? Suche meine damalige Aussage.",
)
_GENERAL_MEMORY_PROFILE_EXAMPLES = (
    "Explain conceptually how a user profile can be built from conversation exchanges.",
    "Describe the general process by which a system learns a user profile from dialogue.",
    "Comment un profil utilisateur peut-il se construire à partir des échanges, en général ?",
    "I have a concern about whether memory recall works and how my user profile is built from exchanges.",
    "I am concerned about whether memory retrieval and profile learning reflect what I say in conversation.",
    "Je m'inquiète du fonctionnement du rappel de mémoire et de la façon dont mon profil se construit à partir de nos échanges.",
    "Me preocupa si el sistema recuerda bien lo que digo y cómo construye mi perfil a partir de nuestras conversaciones.",
    "Ich mache mir Sorgen, ob das System meine Aussagen richtig erinnert und mein Profil aus unseren Gesprächen aufbaut.",
    "Erkläre allgemein, wie das Gesprächsgedächtnis funktioniert.",
)
_PROFILE_FACT_SCOPE_EXAMPLES = {
    "preference": (
        "Which preferences are explicitly recorded in the user's profile?",
        "What does the user prefer according to the saved profile?",
        "Quelles préférences sont explicitement enregistrées dans le profil ?",
        "¿Qué preferencias están registradas explícitamente en el perfil?",
        "Welche Vorlieben sind ausdrücklich im Profil gespeichert?",
    ),
    "dislike": (
        "Which dislikes or aversions are explicitly recorded in the user's profile?",
        "What does the user dislike according to the saved profile?",
        "Quelles aversions sont explicitement enregistrées dans le profil ?",
        "¿Qué cosas le disgustan al usuario según su perfil?",
        "Welche Abneigungen sind ausdrücklich im Profil gespeichert?",
    ),
    "interest": (
        "Which interests are explicitly recorded in the user's profile?",
        "What topics is the user interested in according to the saved profile?",
        "Quels centres d'intérêt sont explicitement enregistrés dans le profil ?",
        "¿Qué intereses están registrados explícitamente en el perfil?",
        "Welche Interessen sind ausdrücklich im Profil gespeichert?",
    ),
    "characteristic": (
        "Which user characteristics are explicitly recorded in the profile?",
        "What personal characteristics are recorded in the saved profile?",
        "Quelles caractéristiques de l'utilisateur sont explicitement enregistrées dans le profil ?",
        "¿Qué características personales están registradas en el perfil?",
        "Welche Eigenschaften der Person sind ausdrücklich im Profil gespeichert?",
    ),
}
_MEMORY_PROFILE_ROUTER_LOCK = threading.Lock()
_MEMORY_PROFILE_ROUTER_CENTROIDS: dict[str, tuple[Any, ...]] = {}


def classify_memory_profile_intents(user_texts, *, embedder=None) -> list[dict[str, Any]]:
    """Batch-classify dialogue recall, profile lookup, and general questions."""
    texts = [" ".join(str(value or "").split()) for value in user_texts]
    if not texts:
        return []
    results: list[dict[str, Any] | None] = [
        ({"status": "empty_input", "intent": "uncertain", "reason_code": "empty_input"}
         if not text else None)
        for text in texts
    ]
    active_indices = [index for index, text in enumerate(texts) if text]
    if not active_indices:
        return [item for item in results if item is not None]
    try:
        if embedder is None:
            from utils.shared_embedder import get_quality_embedder
            embedder = get_quality_embedder()
        encoder = getattr(embedder, "encode_interactive_with_metadata", None)
        if not callable(encoder):
            raise RuntimeError("interactive quality embedding unavailable")

        cache_hint = str(
            getattr(embedder, "embedding_space_id", "")
            or getattr(embedder, "model_name", "")
        )
        with _MEMORY_PROFILE_ROUTER_LOCK:
            cached = _MEMORY_PROFILE_ROUTER_CENTROIDS.get(cache_hint)
        if cached is None:
            vectors, space_id = encoder([
                *_PROFILE_LOOKUP_EXAMPLES, *_HISTORY_RECALL_EXAMPLES,
                *_GENERAL_MEMORY_PROFILE_EXAMPLES,
                *(
                    example
                    for category_examples in _PROFILE_FACT_SCOPE_EXAMPLES.values()
                    for example in category_examples
                ),
                *(texts[index] for index in active_indices),
            ])
            import numpy as np
            matrix = np.asarray(vectors, dtype="float64")
            prototype_count = (
                len(_PROFILE_LOOKUP_EXAMPLES) + len(_HISTORY_RECALL_EXAMPLES)
                + len(_GENERAL_MEMORY_PROFILE_EXAMPLES)
            )
            category_example_count = sum(
                len(category_examples)
                for category_examples in _PROFILE_FACT_SCOPE_EXAMPLES.values()
            )
            expected_rows = (
                prototype_count + category_example_count + len(active_indices)
            )
            if matrix.ndim != 2 or matrix.shape[0] != expected_rows or not np.isfinite(matrix).all():
                raise ValueError("memory/profile router received invalid embeddings")
            normalized = matrix / np.maximum(
                np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12
            )
            profile_end = len(_PROFILE_LOOKUP_EXAMPLES)
            history_end = profile_end + len(_HISTORY_RECALL_EXAMPLES)
            general_end = history_end + len(_GENERAL_MEMORY_PROFILE_EXAMPLES)
            profile = normalized[:profile_end].mean(axis=0)
            history = normalized[profile_end:history_end].mean(axis=0)
            general = normalized[history_end:general_end].mean(axis=0)
            profile /= max(float(np.linalg.norm(profile)), 1e-12)
            history /= max(float(np.linalg.norm(history)), 1e-12)
            general /= max(float(np.linalg.norm(general)), 1e-12)
            category_centroids = {}
            category_offset = general_end
            for category, category_examples in _PROFILE_FACT_SCOPE_EXAMPLES.items():
                category_end = category_offset + len(category_examples)
                center = normalized[category_offset:category_end].mean(axis=0)
                center /= max(float(np.linalg.norm(center)), 1e-12)
                category_centroids[category] = center
                category_offset = category_end
            actual_space = str(space_id)
            if not actual_space.endswith(":text-embedding-nomic-embed-text-v1.5"):
                raise RuntimeError("memory/profile thresholds require Nomic v1.5")
            with _MEMORY_PROFILE_ROUTER_LOCK:
                _MEMORY_PROFILE_ROUTER_CENTROIDS[actual_space] = (
                    profile, history, general, category_centroids,
                )
            queries = normalized[prototype_count + category_example_count:]
        else:
            profile, history, general, category_centroids = cached
            vectors, actual_space = encoder([texts[index] for index in active_indices])
            import numpy as np
            queries = np.asarray(vectors, dtype="float64")
            if queries.ndim != 2 or queries.shape != (len(active_indices), profile.size) or not np.isfinite(queries).all():
                raise ValueError("memory/profile query vector is incompatible")
            queries /= np.maximum(np.linalg.norm(queries, axis=1, keepdims=True), 1e-12)

        for index, query in zip(active_indices, queries):
            profile_score = float(query @ profile)
            history_score = float(query @ history)
            general_score = float(query @ general)
            margin = profile_score - history_score
            if profile_score >= 0.63 and margin >= 0.04 and profile_score - general_score >= 0.04:
                status, intent = "profile_lookup", "profile_lookup"
            elif history_score >= 0.63 and margin <= -0.04 and history_score - general_score >= 0.02:
                status, intent = "history_recall", "history_recall"
            else:
                status, intent = "intent_uncertain", "uncertain"
            category_scores = {
                category: float(query @ center)
                for category, center in category_centroids.items()
            }
            ranked_categories = sorted(
                category_scores.items(), key=lambda item: item[1], reverse=True,
            )
            category_margin = ranked_categories[0][1] - ranked_categories[1][1]
            category_scope = (
                ranked_categories[0][0]
                if ranked_categories[0][1] >= 0.64 and category_margin >= 0.025
                else "all"
            )
            results[index] = {
                "status": status,
                "intent": intent,
                "profile_similarity": round(profile_score, 4),
                "history_similarity": round(history_score, 4),
                "general_similarity": round(general_score, 4),
                "margin": round(margin, 4),
                "score_semantics": "uncalibrated Nomic v1.5 cosine routing score; not a probability",
                "embedding_space": actual_space,
                "reason_code": "cross_lingual_semantic_centroid_margin",
                "profile_fact_scope": {
                    "scope": category_scope,
                    "status": "classified" if category_scope != "all" else "uncertain_includes_all",
                    "top_similarity": round(ranked_categories[0][1], 4),
                    "margin": round(category_margin, 4),
                    "scores": {
                        key: round(value, 4)
                        for key, value in category_scores.items()
                    },
                    "embedding_space": actual_space,
                    "score_semantics": "uncalibrated Nomic v1.5 cosine similarity; not a probability",
                },
            }
    except Exception as exc:
        for index in active_indices:
            results[index] = {
                "status": "router_unavailable",
                "intent": "uncertain",
                "reason_code": type(exc).__name__,
                "score_semantics": "unavailable; do not intercept the user's response",
            }
    return [item for item in results if item is not None]


def classify_memory_profile_intent(user_text: str, *, embedder=None) -> dict[str, Any]:
    """Classify one input through the batched, cross-lingual semantic router."""
    return classify_memory_profile_intents([user_text], embedder=embedder)[0]


def is_explicit_named_profile_query(
    user_text: str, *, intent_result: dict[str, Any] | None = None, embedder=None,
) -> bool:
    """Return true only for a confident semantic named-profile lookup."""
    result = intent_result or classify_memory_profile_intent(user_text, embedder=embedder)
    return result.get("intent") == "profile_lookup"


def classify_profile_fact_scope(user_text: str, *, embedder=None) -> dict[str, Any]:
    """Semantically select a requested profile category; uncertainty includes all.

    The scope affects which provenance-backed facts are displayed, never which
    facts are considered true. An uncertain or unavailable classifier returns
    ``all`` so it cannot silently hide relevant categories.
    """
    result = classify_memory_profile_intent(user_text, embedder=embedder)
    scope = result.get("profile_fact_scope")
    if isinstance(scope, dict):
        return scope
    return {
        "scope": "all",
        "status": "router_unavailable_includes_all",
        "reason_code": str(result.get("reason_code") or result.get("status") or "unavailable"),
        "score_semantics": "unavailable; include all provenance-backed categories",
    }


def render_explicit_profile_facts(
    facts: list[dict], user_text: str, *, requested_categories=None,
) -> dict[str, object]:
    """Render a direct answer from provenance-backed profile values only."""
    text = str(user_text or "").casefold()
    french = bool(
        re.search(r"\b(?:mon|ma|notre|votre|quelle|quelles|selon|enregistr[eé])\b", text)
        or re.search(r"[àâçéèêëîïôùûüÿœ]", text)
    )
    selected_categories = (
        {str(value) for value in requested_categories}
        if requested_categories is not None else None
    )
    eligible = [
        item for item in facts
        if isinstance(item, dict)
        and isinstance(item.get("value"), str)
        and item.get("category") in {"preference", "dislike", "interest", "characteristic"}
        and (selected_categories is None or item.get("category") in selected_categories)
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
