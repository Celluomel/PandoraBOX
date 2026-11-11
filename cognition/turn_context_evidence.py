"""Privacy-preserving provenance receipts for context injected into chat turns."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Iterable, Mapping


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def format_memory_for_prompt(memory: Mapping[str, Any], max_chars: int = 720) -> str:
    """Render stored conversation turns with explicit speaker provenance."""
    text = str(memory.get("text", "")).strip()
    limit = max(160, min(1200, int(max_chars)))
    match = re.match(r"^Conversation\s+[—–-]\s*User:\s*(.*)$", text, re.IGNORECASE | re.DOTALL)
    if not match:
        memory_type = str(memory.get("memory_type", "memory"))[:40]
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
        has_user_message = bool(re.match(
            r"^\s*Conversation\s+[—–-]\s*User:", text, re.IGNORECASE
        ))
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
                    "has_user_message": bool(candidate.get("has_user_message")),
                    "has_assistant_reply": bool(candidate.get("has_assistant_reply")),
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
