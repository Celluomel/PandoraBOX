"""Privacy-preserving provenance receipts for context injected into chat turns."""

from __future__ import annotations

import hashlib
from typing import Any, Iterable, Mapping


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def memory_retrieval_evidence(
    query: str,
    memories: Iterable[Mapping[str, Any]],
    *,
    query_source: str = "user_input",
    attention_mode: str | None = None,
) -> dict:
    """Describe recalled candidates without copying their private text to traces."""
    candidates = []
    for memory in memories:
        text = str(memory.get("text", ""))
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
        })
    return {
        "query_sha256": _sha256(str(query)),
        "query_source": str(query_source)[:32],
        "attention_mode": str(attention_mode or "unavailable")[:24],
        "candidate_count": len(candidates),
        "candidates": candidates,
    }


def profile_context_evidence(status: str, source: str, context: str) -> dict:
    """Fingerprint profile prompt material without exposing its contents."""
    return {
        "status": str(status),
        "source": str(source),
        "context_sha256": _sha256(str(context)),
    }


def audit_safe_turn_summary(value: Any) -> dict[str, Any] | None:
    """Expose bounded provenance fields while keeping private prompt/memory text hidden."""
    if not isinstance(value, Mapping):
        return None

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
                })
                if len(candidates) >= 12:
                    break
        try:
            candidate_count = max(0, min(1000, int(value.get("candidate_count", len(candidates)))))
        except (TypeError, ValueError, OverflowError):
            candidate_count = len(candidates)
        return {
            "type": "memory_retrieval_evidence",
            "query_sha256": str(value.get("query_sha256", ""))[:64],
            "query_source": str(value.get("query_source", "unknown"))[:32],
            "attention_mode": str(value.get("attention_mode", "unavailable"))[:24],
            "candidate_count": candidate_count,
            "candidates": candidates,
            "quality": "present" if candidate_count else "empty",
        }

    if {"status", "source", "context_sha256"}.issubset(value):
        return {
            "type": "profile_context_evidence",
            "status": str(value.get("status", ""))[:32],
            "source": str(value.get("source", ""))[:40],
            "context_sha256": str(value.get("context_sha256", ""))[:64],
            "quality": "present",
        }

    if {"status", "changed", "quarantined_count"}.issubset(value):
        try:
            quarantined_count = max(0, min(1000, int(value.get("quarantined_count", 0))))
        except (TypeError, ValueError, OverflowError):
            quarantined_count = 0
        return {
            "type": "profile_learning_receipt",
            "status": str(value.get("status", ""))[:48],
            "changed": bool(value.get("changed")),
            "quarantined_count": quarantined_count,
            "quality": "present",
        }

    return None
