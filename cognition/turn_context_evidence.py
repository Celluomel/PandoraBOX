"""Privacy-preserving provenance receipts for context injected into chat turns."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Iterable, Mapping


USER_PROFILE_PROVENANCE_POLICY = (
    "User-profile evidence policy: the named UserManager profile is the source for "
    "explicitly recorded user facts. Treat only entries labeled 'User-stated' with a "
    "source receipt as explicit user statements; entries labeled legacy/unverified are "
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


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


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
            "categories": categories,
        }
    return result


def audit_safe_turn_summary(value: Any) -> dict[str, Any] | None:
    """Expose bounded provenance fields while keeping private prompt/memory text hidden."""
    if not isinstance(value, Mapping):
        return None

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
        try:
            quarantined_count = max(0, min(1000, int(value.get("quarantined_count", 0))))
        except (TypeError, ValueError, OverflowError):
            quarantined_count = 0
        try:
            extracted_count = max(0, min(1000, int(value.get("extracted_count", 0))))
        except (TypeError, ValueError, OverflowError):
            extracted_count = 0
        try:
            interaction_count = max(0, min(1_000_000, int(value.get("interaction_count", 0))))
        except (TypeError, ValueError, OverflowError):
            interaction_count = None
        status = str(value.get("status", ""))[:48]
        persisted_value = value.get("persisted")
        persisted = persisted_value if isinstance(persisted_value, bool) else None
        if status in {"persistence_failed", "failed"} or persisted is False:
            quality = "failed"
        elif status in {"skipped_by_scope", "skipped_no_named_profile", "skipped_empty_message"}:
            quality = "skipped"
        elif status in {"no_explicit_profile_fact", "no_profile_returned", "quarantined_ephemeral_profile_data"}:
            quality = "empty"
        elif persisted is True:
            quality = "present"
        else:
            quality = "unverified"
        categories = value.get("categories_updated", [])
        if not isinstance(categories, (list, tuple)):
            categories = []
        return {
            "type": "profile_learning_receipt",
            "status": status,
            "changed": bool(value.get("changed")),
            "persisted": persisted,
            "categories_updated": [str(item)[:32] for item in categories[:8]],
            "extracted_count": extracted_count,
            "quarantined_count": quarantined_count,
            "interaction_count": interaction_count,
            "quality": quality,
        }

    return None
