"""Privacy-preserving provenance receipts for context injected into chat turns."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any, Iterable, Mapping


USER_PROFILE_PROVENANCE_POLICY = (
    "User-profile evidence policy: the named UserManager profile is the source for "
    "explicitly recorded user facts. A profile display name without a source receipt is "
    "only an identity label, not proof that the user explicitly stated that name. Treat "
    "only entries labeled 'User-stated' with a source receipt as explicit user statements; "
    "entries labeled legacy/unverified are "
    "not confirmed facts. The WorldModel behavioral interaction model, communication "
    "style estimates, inferred familiarity, relationship estimates, time-pattern estimates, "
    "conversation topics, and retrieved memories are separate evidence sources. Never "
    "present any of those estimates or memories as explicit facts stored in the named "
    "profile. When asked what is explicitly recorded, the authoritative named-profile "
    "provenance counts control: never infer an entry or its count from memories or another "
    "model. List only provenance-backed entries; if the count is zero, say there are none. "
    "Do not pad empty categories with generic legacy labels. Keep historical recall separate "
    "from profile facts."
)

_MEMORY_RETRIEVAL_LANES = {
    "primary", "user_authored", "personal", "visual", "event",
    "explicit_recall_secondary", "session_visual_buffer",
}


def _safe_memory_retrieval_lane(value: Any) -> str:
    lane = str(value or "unattributed")[:40]
    return lane if lane in _MEMORY_RETRIEVAL_LANES else "unattributed"


def tag_memory_retrieval_lane(
    memories: Iterable[Mapping[str, Any]], lane: str,
) -> list[dict[str, Any]]:
    """Copy retrieved rows with a bounded, auditable lane label."""
    safe_lane = _safe_memory_retrieval_lane(lane)
    return [dict(memory, retrieval_lane=safe_lane)
            for memory in memories if isinstance(memory, Mapping)]


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def deterministic_reasoning_dependencies(
    *,
    selected: bool,
    memory_recall: bool = False,
    cognitive_audit_report: bool = False,
    planner_snapshot: bool = False,
    api_route_answer: bool = False,
    named_profile_facts: bool = False,
    source_provenance_report: bool = False,
) -> tuple[str, ...]:
    """Return only the recorded inputs that actually support a direct answer."""
    if not selected:
        return ()
    sources = ["turn_input"]
    if memory_recall:
        sources.append("memory_recall_answer")
    if cognitive_audit_report:
        sources.append("cognitive_audit_status_report")
    if planner_snapshot:
        # The answer renderer consumes the snapshot; deterministic reasoning
        # consumes that rendered answer, preserving the intermediate causal edge.
        sources.append("planner_factual_answer")
    if api_route_answer:
        sources.append("api_route_answer")
    if named_profile_facts:
        sources.append("explicit_profile_facts_answer")
    if source_provenance_report:
        sources.append("turn_source_provenance_answer")
    return tuple(sources)


def verify_history_exchange_append(
    before: Iterable[Any], after: Iterable[Any], prompt: str, response: str,
) -> bool:
    """Verify an exchange append even when bounded history trims old entries.

    At the history cap an append can evict an equal number of older messages,
    so list length does not prove whether this exchange was recorded. Verify
    the final user/assistant entries by role, content, and object identity.
    """
    before_items = tuple(before) if isinstance(before, Iterable) else ()
    after_items = tuple(after) if isinstance(after, Iterable) else ()
    if len(after_items) < 2:
        return False
    previous_ids = {id(item) for item in before_items}
    user_entry, assistant_entry = after_items[-2:]
    if id(user_entry) in previous_ids or id(assistant_entry) in previous_ids:
        return False
    return (
        isinstance(user_entry, Mapping)
        and user_entry.get("role") == "user"
        and user_entry.get("content") == str(prompt or "")
        and isinstance(assistant_entry, Mapping)
        and assistant_entry.get("role") == "assistant"
        and assistant_entry.get("content") == str(response or "")
    )


def format_memory_for_prompt(memory: Mapping[str, Any], max_chars: int = 720) -> str:
    """Render stored conversation turns with explicit speaker provenance."""
    text = str(memory.get("text", "")).strip()
    limit = max(160, min(1200, int(max_chars)))
    memory_type = str(memory.get("memory_type", "memory"))[:40]
    if memory.get("source") == "legacy_episodic_user_source":
        user_text = str(memory.get("user_authored_text", "")).strip()
        return (
            "- [user-authored segment extracted from a legacy dialogue; "
            "assistant reply omitted]\n"
            "  USER MESSAGE (evidence of what the user asked or stated; "
            "a question alone does not establish its answer): "
            + user_text[:min(900, limit)]
        )[:limit]
    if memory_type == "user_message":
        user_text = re.sub(r"^User message:\s*", "", text, flags=re.IGNORECASE).strip()
        return (
            "- [separately indexed, user-authored message]\n"
            "  USER MESSAGE (evidence of what the user asked or stated; a question alone does not establish its answer): "
            + user_text[:min(900, limit)]
        )[:limit]
    match = re.match(r"^Conversation\s+[—–-]\s*User:\s*(.*)$", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return f"- [{memory_type}] {text[:min(300, limit)]}"

    content = match.group(1)
    parts = re.split(r"\s+\|\s+(?:Lumina|Assistant):\s*", content, maxsplit=1, flags=re.IGNORECASE)
    user_text = parts[0].strip()[:360]
    assistant_text = parts[1].strip()[:300] if len(parts) > 1 else ""
    rendered = [
        "- [episodic dialogue record; speaker provenance preserved]",
        f"  USER MESSAGE (evidence of what the user asked or stated; a question alone does not establish its answer): {user_text}",
    ]
    if assistant_text:
        rendered.append(
            "  LUMINA REPLY (evidence only of what Lumina previously said; unverified and not proof of truth or agreement): "
            + assistant_text
        )
    result = "\n".join(rendered)
    return result[:limit]


def memory_embedding_text(text: str, memory_type: str = "") -> str:
    """Keep user-authored conversation embeddings free of assistant wording."""
    value = str(text or "").strip()
    if str(memory_type or "") == "user_message":
        return re.sub(r"^User message:\s*", "", value, flags=re.IGNORECASE).strip()
    return value


def memory_retrieval_evidence(
    query: str,
    memories: Iterable[Mapping[str, Any]],
    *,
    query_source: str = "user_input",
    attention_mode: str | None = None,
    retrieval_receipt: Mapping[str, Any] | None = None,
    explicit_recall: bool = False,
    candidate_count_before_recall_filter: int | None = None,
) -> dict:
    """Describe recalled candidates without copying their private text to traces."""
    candidates = []
    for memory in memories:
        text = str(memory.get("text", ""))
        has_user_message = bool(re.match(
            r"^\s*Conversation\s+[—–-]\s*User:", text, re.IGNORECASE
        )) or str(memory.get("memory_type", "")) == "user_message"
        has_assistant_reply = bool(re.search(
            r"\s+\|\s+(?:Lumina|Assistant):", text, re.IGNORECASE
        ))
        stable_key = str(memory.get("id") or memory.get("faiss_id") or text)
        relevance = memory.get("relevance")
        try:
            relevance = round(max(0.0, min(1.0, float(relevance))), 4)
        except (TypeError, ValueError, OverflowError):
            relevance = None
        candidates.append({
            "ref": _sha256(stable_key)[:20],
            "memory_tier": str(memory.get("memory_tier") or "unknown")[:24],
            "memory_type": str(memory.get("memory_type") or "unknown")[:40],
            "source": str(memory.get("source") or "memory_store")[:40],
            "retrieval_lane": _safe_memory_retrieval_lane(memory.get("retrieval_lane")),
            "timestamp_present": bool(memory.get("timestamp")),
            "relevance": relevance,
            "has_user_message": has_user_message,
            "has_assistant_reply": has_assistant_reply,
        })
    evidence = {
        "query_sha256": _sha256(str(query)),
        "query_source": str(query_source)[:32],
        "attention_mode": str(attention_mode or "unavailable")[:24],
        "explicit_recall": bool(explicit_recall),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    if candidate_count_before_recall_filter is not None:
        try:
            evidence["candidate_count_before_recall_filter"] = max(
                0, min(1000, int(candidate_count_before_recall_filter))
            )
        except (TypeError, ValueError, OverflowError):
            evidence["candidate_count_before_recall_filter"] = len(candidates)
    if isinstance(retrieval_receipt, Mapping):
        try:
            elapsed_ms = max(0.0, min(600000.0, float(retrieval_receipt.get("elapsed_ms", 0))))
        except (TypeError, ValueError, OverflowError):
            elapsed_ms = None
        try:
            vector_candidate_count = max(
                0, min(100000, int(retrieval_receipt.get("vector_candidate_count", 0)))
            )
        except (TypeError, ValueError, OverflowError):
            vector_candidate_count = 0
        try:
            primary_returned_count = max(
                0, min(100000, int(retrieval_receipt.get("returned_count", 0)))
            )
        except (TypeError, ValueError, OverflowError):
            primary_returned_count = 0
        evidence["retrieval"] = {
            "backend": str(retrieval_receipt.get("backend") or "unreported")[:24],
            "fallback_reason": str(retrieval_receipt.get("fallback_reason") or "")[:64],
            "vector_candidate_count": vector_candidate_count,
            "primary_returned_count": primary_returned_count,
            "final_pool_count": len(candidates),
            "elapsed_ms": elapsed_ms,
        }
        # Keep the actual FAISS vector-space identity visible in the audit
        # receipt.  The configured quality embedder is not necessarily the
        # model used by episodic memory (which may use the FAST tier).
        if str(retrieval_receipt.get("backend") or "") == "faiss":
            model = str(retrieval_receipt.get("embedding_model") or "")
            model = model.replace("\\", "/").rsplit("/", 1)[-1]
            model = re.sub(r"[^A-Za-z0-9._-]", "_", model)[:96]
            if model:
                evidence["retrieval"]["embedding_model"] = model
            dimension = retrieval_receipt.get("embedding_dim")
            if isinstance(dimension, int) and not isinstance(dimension, bool) and 0 < dimension <= 10000:
                evidence["retrieval"]["embedding_dim"] = dimension
    return evidence


def memory_prompt_injection_evidence(memories: Iterable[Mapping[str, Any]]) -> dict:
    """Identify which recalled records actually entered this turn's prompt."""
    injected = []
    for memory in memories:
        text = str(memory.get("text", ""))
        stable_key = str(memory.get("id") or memory.get("faiss_id") or text)
        injected.append({
            "ref": _sha256(stable_key)[:20],
            "memory_tier": str(memory.get("memory_tier") or "unknown")[:24],
            "memory_type": str(memory.get("memory_type") or "unknown")[:40],
            "retrieval_lane": _safe_memory_retrieval_lane(memory.get("retrieval_lane")),
        })
    return {"injected_count": len(injected), "records": injected[:12]}


def response_learning_evidence(receipt: Mapping[str, Any]) -> dict:
    """Keep persistence outcomes visible in traces without retaining message text."""
    def _count(name: str) -> int:
        try:
            return max(0, min(1000, int(receipt.get(name, 0))))
        except (TypeError, ValueError, OverflowError):
            return 0

    status = str(receipt.get("status") or "unreported")[:32]
    failed = receipt.get("failed_operations", [])
    if not isinstance(failed, (list, tuple)):
        failed = []
    kinds = receipt.get("memory_write_kinds", [])
    if not isinstance(kinds, (list, tuple)):
        kinds = []
    quality = "failed" if status == "failed" else "present" if status == "completed" else "unverified"
    return {
        "type": "response_learning_receipt",
        "status": status,
        "memory_write_count": _count("memory_write_count"),
        "memory_write_kinds": [str(item)[:40] for item in kinds[:8]],
        "memory_persisted_count": _count("memory_persisted_count"),
        "memory_deduplicated_count": _count("memory_deduplicated_count"),
        "personal_fact_attempted_count": _count("personal_fact_attempted_count"),
        "personal_fact_persisted_count": _count("personal_fact_persisted_count"),
        "failed_operations": [str(item)[:48] for item in failed[:8]],
        "quality": quality,
    }


def profile_context_evidence(
    status: str, source: str, context: str, provenance_summary: Mapping[str, Any] | None = None,
) -> dict:
    """Fingerprint profile prompt material without exposing its contents."""
    status = str(status)
    quality_by_status = {
        "injected": "present",
        "fallback_identity_only": "present",
        "empty": "empty",
        "skipped_by_scope": "skipped",
        "unavailable": "unavailable",
        "failed": "failed",
    }
    result = {
        "status": status,
        "source": str(source),
        "context_sha256": _sha256(str(context)),
        "quality": quality_by_status.get(status, "unverified"),
    }
    if isinstance(provenance_summary, Mapping):
        def safe_count(value: Any) -> int:
            try:
                return max(0, min(100000, int(value)))
            except (TypeError, ValueError, OverflowError):
                return 0

        categories = {}
        raw_categories = provenance_summary.get("categories")
        if isinstance(raw_categories, Mapping):
            for category in ("preferences", "dislikes", "interests", "characteristics"):
                counts = raw_categories.get(category)
                if isinstance(counts, Mapping):
                    categories[category] = {
                        "explicit_user_stated": safe_count(counts.get("explicit_user_stated", 0)),
                        "legacy_unverified": safe_count(counts.get("legacy_unverified", 0)),
                    }
        result["provenance_summary"] = {
            "explicit_user_stated_entries": safe_count(
                provenance_summary.get("explicit_user_stated_entries", 0)
            ),
            "legacy_unverified_entries": safe_count(
                provenance_summary.get("legacy_unverified_entries", 0)
            ),
            "display_name_source": str(
                provenance_summary.get("display_name_source", "unknown")
            )[:40],
            "categories": categories,
        }
    return result


def audit_safe_turn_summary(value: Any) -> dict[str, Any] | None:
    """Expose bounded provenance fields while keeping private prompt/memory text hidden."""
    if not isinstance(value, Mapping):
        return None

    if value.get("type") == "affect_advisory_context_receipt":
        receipt: dict[str, Any] = {
            "type": "affect_advisory_context_receipt",
            "quality": "present",
            "source": "emotional_state_manager_state_description",
        }
        for key in ("description_present",):
            if isinstance(value.get(key), bool):
                receipt[key] = value[key]
        for key in ("description_chars", "context_chars"):
            number = value.get(key)
            if isinstance(number, int) and not isinstance(number, bool):
                receipt[key] = max(0, min(4000, number))
        for key in ("description_sha256", "context_sha256"):
            digest = str(value.get(key) or "")
            if re.fullmatch(r"[a-f0-9]{64}", digest):
                receipt[key] = digest
        return receipt

    if value.get("type") in {
        "profile_learning_barrier_receipt", "memory_learning_barrier_receipt",
    }:
        receipt_type = str(value.get("type"))
        status = str(value.get("status") or "unverified")[:40]
        if status not in {
            "no_predecessor", "not_applicable_peer", "predecessor_completed",
            "predecessor_unverified", "predecessor_failed",
        }:
            status = "unverified"
        receipt = {
            "type": receipt_type,
            "status": status,
            "quality": (
                "present" if status in {"no_predecessor", "predecessor_completed"}
                else "failed" if status == "predecessor_failed" else "unverified"
            ),
        }
        learning_status = str(value.get("learning_status") or "")[:48]
        if learning_status and learning_status.replace("_", "").isalnum():
            receipt["learning_status"] = learning_status
        if isinstance(value.get("persisted"), bool):
            receipt["persisted"] = value["persisted"]
        predecessor_turn_id = str(value.get("predecessor_turn_id") or "")[:120]
        if predecessor_turn_id and all(
            char.isalnum() or char in "-_." for char in predecessor_turn_id
        ):
            receipt["predecessor_turn_id"] = predecessor_turn_id
        error_type = str(value.get("error_type") or "")[:64]
        if error_type and error_type.replace("_", "").isalnum():
            receipt["error_type"] = error_type
        return receipt

    profile_receipt_types = {
        "behavioral_user_model_context_receipt": {
            "source": "world_model_behavioral_model",
            "counts": ("interaction_count", "topic_count", "expertise_count"),
        },
        "communication_calibrator_context_receipt": {
            "source": "communication_calibrator",
            "counts": ("sample_count", "calibration_count"),
        },
    }
    receipt_type = value.get("type")
    if receipt_type in profile_receipt_types:
        policy = profile_receipt_types[receipt_type]
        status = str(value.get("status") or "unknown")[:40]
        receipt: dict[str, Any] = {
            "type": receipt_type,
            "status": status if status in {
                "injected", "empty", "omitted_by_prompt_budget", "unavailable", "failed",
            } else "unverified",
            "source": policy["source"],
            "quality": (
                "present" if status == "injected" else
                "omitted" if status == "omitted_by_prompt_budget" else
                "empty" if status == "empty" else "unverified"
            ),
        }
        included = value.get("context_included")
        if isinstance(included, bool):
            receipt["context_included"] = included
        source_available = value.get("source_available")
        if isinstance(source_available, bool):
            receipt["source_available"] = source_available
        budget_reason = str(value.get("budget_reason") or "")
        if budget_reason in {
            "budget_ok", "category_full", "total_cap", "empty",
            "not_registered", "not_assembled", "not_selected",
        }:
            receipt["budget_reason"] = budget_reason
        for key in policy["counts"]:
            raw = value.get(key)
            if isinstance(raw, int) and not isinstance(raw, bool):
                receipt[key] = max(0, min(1_000_000, raw))
        budget_tokens = value.get("budget_tokens")
        if isinstance(budget_tokens, int) and not isinstance(budget_tokens, bool):
            receipt["budget_tokens"] = max(0, min(1_000_000, budget_tokens))
        if receipt_type == "behavioral_user_model_context_receipt":
            if isinstance(value.get("profile_present"), bool):
                receipt["profile_present"] = value["profile_present"]
        digest = str(value.get("context_sha256") or "")
        if re.fullmatch(r"[a-f0-9]{64}", digest):
            receipt["context_sha256"] = digest
        return receipt

    if value.get("type") == "api_route_answer_receipt":
        receipt: dict[str, Any] = {
            "type": "api_route_answer_receipt",
            "status": str(value.get("status") or "unknown")[:40],
            "source": str(value.get("source") or "unknown")[:40],
            "resolution_source": str(value.get("resolution_source") or "unknown")[:64],
            "prior_route_context": str(value.get("prior_route_context") or "unknown")[:48],
        }
        receipt["quality"] = (
            "present" if receipt["status"] in {
                "matched_registered_route", "matched_live_route_followup",
            } else "empty" if receipt["status"] in {
                "no_unique_registered_route", "unresolved_route_followup",
            } else "unverified"
        )
        count = value.get("route_count")
        if isinstance(count, int) and not isinstance(count, bool):
            receipt["route_count"] = max(0, min(10000, count))
        selected = value.get("selected_route")
        if isinstance(selected, Mapping):
            method = str(selected.get("method") or "").upper()
            path = str(selected.get("path") or "")
            handler = str(selected.get("handler") or "")
            if re.fullmatch(r"[A-Z]{3,10}", method) and re.fullmatch(r"/[A-Za-z0-9._~!$&'()*+,;=:@%/-]{0,240}", path):
                receipt["selected_route"] = {
                    "method": method,
                    "path": path,
                    "handler": handler[:80],
                }
        digest = str(value.get("routes_sha256") or "")
        if re.fullmatch(r"[a-f0-9]{64}", digest):
            receipt["routes_sha256"] = digest
        return receipt

    if value.get("type") == "conversation_history_write_receipt":
        receipt = {
            "type": "conversation_history_write_receipt",
            "quality": "present" if value.get("status") == "recorded_in_memory" else "unverified",
            "status": str(value.get("status") or "unknown")[:40],
            "record_history_enabled": bool(value.get("record_history_enabled")),
            "manager_available": bool(value.get("manager_available")),
            "in_memory_tail_matches": bool(value.get("in_memory_tail_matches")),
            "durable_persistence": str(value.get("durable_persistence") or "unverified")[:24],
        }
        for key in ("before_message_count", "after_message_count", "appended_message_count"):
            number = value.get(key)
            if isinstance(number, int) and not isinstance(number, bool):
                receipt[key] = max(0, min(100000, number))
        error_type = str(value.get("error_type") or "")
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", error_type):
            receipt["error_type"] = error_type
        return receipt

    routing_fields = (
        "factual_plan_query", "closed_world_report", "architecture_query",
        "cognitive_trace_query", "runtime_execution_query", "explicit_memory_recall",
        "prompt_source_provenance_query",
    )
    if all(isinstance(value.get(key), bool) for key in routing_fields):
        return {
            "type": "turn_evidence_routing_receipt",
            "quality": "present",
            **{key: value[key] for key in routing_fields},
            "api_route_query": bool(value.get("api_route_query", False)),
            "explicit_named_profile_query": bool(
                value.get("explicit_named_profile_query", False)
            ),
            "prompt_source_provenance_query": bool(
                value.get("prompt_source_provenance_query", False)
            ),
        }

    if value.get("type") == "cognitive_deliberation_receipt":
        receipt: dict[str, Any] = {
            "type": "cognitive_deliberation_receipt",
            "quality": "present",
            "status": str(value.get("status") or "unknown")[:32],
        }
        for key in ("cycles_run", "candidates_considered"):
            number = value.get(key)
            if isinstance(number, int) and not isinstance(number, bool):
                receipt[key] = max(0, min(10000, number))
        for key in (
            "final_utility", "internal_pressure", "internal_pressure_delta",
            "internal_meta_error", "efficacy_observation_meta_error",
            "efficacy_multiplier", "efficacy_score_delta",
        ):
            number = value.get(key)
            if isinstance(number, (int, float)) and not isinstance(number, bool):
                numeric = float(number)
                if math.isfinite(numeric):
                    receipt[key] = max(-10000.0, min(10000.0, numeric))
        candidate_type = str(value.get("selected_candidate_type") or "unknown")
        if candidate_type in {"goal", "thought", "tension", "curiosity", "memory", "relational", "creative", "narrative", "aspiration", "unknown"}:
            receipt["selected_candidate_type"] = candidate_type
        for key in (
            "synthesized", "efficacy_candidate_present", "efficacy_applied_to_focus",
            "efficacy_prediction_recorded",
        ):
            if isinstance(value.get(key), bool):
                receipt[key] = value[key]
        return receipt

    if value.get("type") == "cognitive_effect_receipt":
        receipt: dict[str, Any] = {"type": "cognitive_effect_receipt", "quality": "present"}
        status = str(value.get("status") or "")[:48]
        if status:
            receipt["status"] = status
        for key in (
            "relational_interaction_increment", "attractor_traits_changed",
            "beliefs_updated",
        ):
            number = value.get(key)
            if isinstance(number, int) and not isinstance(number, bool):
                receipt[key] = max(0, min(1_000_000, number))
        if isinstance(value.get("causal_pair_available"), bool):
            receipt["causal_pair_available"] = value["causal_pair_available"]
        persistence = value.get("persistence")
        if persistence in {
            "not_attempted", "attempted_unverified",
            "operation_returned_effect_unverified",
        }:
            receipt["persistence"] = persistence
        return receipt

    if value.get("type") == "response_learning_receipt":
        return response_learning_evidence(value)

    if value.get("type") == "semantic_extraction_receipt":
        receipt: dict[str, Any] = {
            "type": "semantic_extraction_receipt",
            "quality": "present",
            "status": str(value.get("status") or "unknown")[:32],
            "persistence_status": str(value.get("persistence_status") or "unverified")[:24],
            "cag_status": str(value.get("cag_status") or "unknown")[:24],
            "workspace_status": str(value.get("workspace_status") or "unknown")[:24],
        }
        turn_kind = str(value.get("turn_kind") or "")[:24]
        if turn_kind in {"topic", "retrieval", "social", "instruction", "feedback", "decision", "other", "unclassified"}:
            receipt["turn_kind"] = turn_kind
        learning_status = str(value.get("learning_status") or "")[:32]
        if learning_status in {
            "accepted_topic_turn", "accepted_decision_turn", "skipped_non_topic_turn",
        }:
            receipt["learning_status"] = learning_status
        for key in (
            "concepts_parsed", "concept_upsert_calls_returned", "concepts_persisted",
            "observation_calls_returned", "observations_persisted",
            "relation_upsert_calls_returned", "relations_persisted",
        ):
            number = value.get(key)
            if isinstance(number, int) and not isinstance(number, bool):
                receipt[key] = max(0, min(1000, number))
        if isinstance(value.get("dominant_topic_selected"), bool):
            receipt["dominant_topic_selected"] = value["dominant_topic_selected"]
        curiosity_status = str(value.get("curiosity_status") or "")[:32]
        if curiosity_status in {
            "stimulated", "unavailable", "failed", "skipped_peer_source",
            "no_grounded_dominant_topic", "skipped_non_topic_turn",
        }:
            receipt["curiosity_status"] = curiosity_status
        if isinstance(value.get("curiosity_topic_selected"), bool):
            receipt["curiosity_topic_selected"] = value["curiosity_topic_selected"]
        curiosity_level = value.get("curiosity_level_after")
        if isinstance(curiosity_level, (int, float)) and not isinstance(curiosity_level, bool):
            numeric = float(curiosity_level)
            if math.isfinite(numeric):
                receipt["curiosity_level_after"] = max(0.0, min(1.0, numeric))
        curiosity_error = str(value.get("curiosity_error_type") or "")
        if curiosity_error and re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", curiosity_error):
            receipt["curiosity_error_type"] = curiosity_error
        duration = value.get("duration_ms")
        if isinstance(duration, (int, float)) and not isinstance(duration, bool):
            numeric = float(duration)
            if math.isfinite(numeric):
                receipt["duration_ms"] = max(0.0, min(600000.0, numeric))
        return receipt

    if {"query_sha256", "candidate_count", "candidates"}.issubset(value):
        candidates = []
        raw_candidates = value.get("candidates")
        if isinstance(raw_candidates, Iterable) and not isinstance(raw_candidates, (str, bytes, Mapping)):
            for candidate in raw_candidates:
                if not isinstance(candidate, Mapping):
                    continue
                candidates.append({
                    "ref": str(candidate.get("ref", ""))[:20],
                    "memory_tier": str(candidate.get("memory_tier", "unknown"))[:24],
                    "memory_type": str(candidate.get("memory_type", "unknown"))[:40],
                    "source": str(candidate.get("source", "memory_store"))[:40],
                    "retrieval_lane": _safe_memory_retrieval_lane(candidate.get("retrieval_lane")),
                    "timestamp_present": bool(candidate.get("timestamp_present")),
                    "relevance": candidate.get("relevance")
                    if isinstance(candidate.get("relevance"), (int, float))
                    and 0.0 <= float(candidate.get("relevance")) <= 1.0 else None,
                    "has_user_message": bool(candidate.get("has_user_message")),
                    "has_assistant_reply": bool(candidate.get("has_assistant_reply")),
                })
                if len(candidates) >= 12:
                    break
        try:
            candidate_count = max(0, min(1000, int(value.get("candidate_count", len(candidates)))))
        except (TypeError, ValueError, OverflowError):
            candidate_count = len(candidates)
        summary = {
            "type": "memory_retrieval_evidence",
            "query_sha256": str(value.get("query_sha256", ""))[:64],
            "query_source": str(value.get("query_source", "unknown"))[:32],
            "attention_mode": str(value.get("attention_mode", "unavailable"))[:24],
            "explicit_recall": bool(value.get("explicit_recall", False)),
            "candidate_count": candidate_count,
            "candidates": candidates,
            "quality": "present" if candidate_count else "empty",
        }
        if "candidate_count_before_recall_filter" in value:
            try:
                summary["candidate_count_before_recall_filter"] = max(
                    0, min(1000, int(value.get("candidate_count_before_recall_filter", candidate_count)))
                )
            except (TypeError, ValueError, OverflowError):
                summary["candidate_count_before_recall_filter"] = candidate_count
        retrieval = value.get("retrieval")
        if isinstance(retrieval, Mapping):
            try:
                elapsed_ms = max(0.0, min(600000.0, float(retrieval.get("elapsed_ms", 0))))
            except (TypeError, ValueError, OverflowError):
                elapsed_ms = None
            try:
                vector_candidate_count = max(
                    0, min(100000, int(retrieval.get("vector_candidate_count", 0)))
                )
            except (TypeError, ValueError, OverflowError):
                vector_candidate_count = 0
            try:
                primary_returned_count = max(
                    0, min(100000, int(retrieval.get("primary_returned_count", 0)))
                )
            except (TypeError, ValueError, OverflowError):
                primary_returned_count = 0
            try:
                final_pool_count = max(
                    0, min(100000, int(retrieval.get("final_pool_count", candidate_count)))
                )
            except (TypeError, ValueError, OverflowError):
                final_pool_count = candidate_count
            summary["retrieval"] = {
                "backend": str(retrieval.get("backend") or "unreported")[:24],
                "fallback_reason": str(retrieval.get("fallback_reason") or "")[:64],
                "vector_candidate_count": vector_candidate_count,
                "primary_returned_count": primary_returned_count,
                "final_pool_count": final_pool_count,
                "elapsed_ms": elapsed_ms,
            }
            model = retrieval.get("embedding_model")
            if isinstance(model, str) and re.fullmatch(r"[A-Za-z0-9._-]{1,96}", model):
                summary["retrieval"]["embedding_model"] = model
            dimension = retrieval.get("embedding_dim")
            if isinstance(dimension, int) and not isinstance(dimension, bool) and 0 < dimension <= 10000:
                summary["retrieval"]["embedding_dim"] = dimension
        return summary

    if {"injected_count", "records"}.issubset(value):
        records = []
        raw_records = value.get("records")
        if isinstance(raw_records, Iterable) and not isinstance(raw_records, (str, bytes, Mapping)):
            for record in raw_records:
                if not isinstance(record, Mapping):
                    continue
                records.append({
                    "ref": str(record.get("ref", ""))[:20],
                    "memory_tier": str(record.get("memory_tier", "unknown"))[:24],
                    "memory_type": str(record.get("memory_type", "unknown"))[:40],
                    "retrieval_lane": _safe_memory_retrieval_lane(record.get("retrieval_lane")),
                })
                if len(records) >= 12:
                    break
        try:
            injected_count = max(0, min(1000, int(value.get("injected_count", len(records)))))
        except (TypeError, ValueError, OverflowError):
            injected_count = len(records)
        return {
            "type": "memory_prompt_injection_evidence",
            "injected_count": injected_count,
            "records": records,
            "quality": "present" if injected_count else "empty",
        }

    if {"status", "source", "context_sha256"}.issubset(value):
        status = str(value.get("status", ""))[:32]
        quality_by_status = {
            "injected": "present",
            "fallback_identity_only": "present",
            "empty": "empty",
            "skipped_by_scope": "skipped",
            "unavailable": "unavailable",
            "failed": "failed",
        }
        return {
            "type": "profile_context_evidence",
            "status": status,
            "source": str(value.get("source", ""))[:40],
            "context_sha256": str(value.get("context_sha256", ""))[:64],
            "provenance_summary": value.get("provenance_summary", {}),
            "quality": quality_by_status.get(status, "unverified"),
        }

    profile_receipt_statuses = {
        "updated", "duplicate_explicit_profile_fact", "persistence_failed",
        "no_explicit_profile_fact", "quarantined_ephemeral_profile_data",
        "skipped_by_scope", "skipped_no_named_profile", "skipped_empty_message",
        "no_profile_returned", "failed", "unavailable",
    }
    if {"status", "changed"}.issubset(value) and (
        "quarantined_count" in value or "persisted" in value
        or str(value.get("status", "")) in profile_receipt_statuses
    ):
        def optional_count(field_name: str) -> int | None:
            if field_name not in value or value.get(field_name) is None:
                return None
            try:
                return max(0, min(1000, int(value[field_name])))
            except (TypeError, ValueError, OverflowError):
                return None

        quarantined_count = optional_count("quarantined_count")
        extracted_count = optional_count("extracted_count")
        try:
            interaction_count = max(0, min(1_000_000, int(value.get("interaction_count", 0))))
        except (TypeError, ValueError, OverflowError):
            interaction_count = None
        status = str(value.get("status", ""))[:48]
        persisted_value = value.get("persisted")
        persisted = persisted_value if isinstance(persisted_value, bool) else None
        if status.startswith("skipped_"):
            quality = "skipped"
        elif status in {"persistence_failed", "failed"} or persisted is False:
            quality = "failed"
        elif status in {"no_explicit_profile_fact", "no_profile_returned", "quarantined_ephemeral_profile_data"}:
            quality = "empty"
        elif persisted is True:
            quality = "present"
        else:
            quality = "unverified"
        categories = value.get("categories_updated")
        if categories is not None and not isinstance(categories, (list, tuple)):
            categories = None
        return {
            "type": "profile_learning_receipt",
            "status": status,
            "changed": bool(value.get("changed")),
            "persisted": persisted,
            "categories_updated": (
                [str(item)[:32] for item in categories[:8]]
                if isinstance(categories, (list, tuple)) else None
            ),
            "extracted_count": extracted_count,
            "quarantined_count": quarantined_count,
            "interaction_count": interaction_count,
            "learning_scope": str(value.get("learning_scope") or "")[:48] or None,
            "quality": quality,
        }

    return None

