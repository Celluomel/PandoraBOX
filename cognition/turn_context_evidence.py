"""Privacy-preserving provenance receipts for context injected into chat turns."""

from __future__ import annotations

import hashlib
from typing import Any, Iterable, Mapping


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def memory_retrieval_evidence(query: str, memories: Iterable[Mapping[str, Any]]) -> dict:
    """Describe recalled candidates without copying their private text to traces."""
    candidates = []
    for memory in memories:
        text = str(memory.get("text", ""))
        stable_key = str(memory.get("id") or memory.get("faiss_id") or text)
        candidates.append({
            "ref": _sha256(stable_key)[:20],
            "memory_tier": str(memory.get("memory_tier") or "unknown")[:24],
            "memory_type": str(memory.get("memory_type") or "unknown")[:40],
            "source": str(memory.get("source") or "memory_store")[:40],
            "timestamp_present": bool(memory.get("timestamp")),
        })
    return {
        "query_sha256": _sha256(str(query)),
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
