"""Shared provenance checks for machine-derived semantic-concept records."""

from __future__ import annotations

from typing import Any, Mapping


def is_semantic_concept_belief(record: Mapping[str, Any] | None, key: str = "") -> bool:
    """Identify graph-statistic concepts that must not become self-beliefs.

    New records carry the explicit ``semantic_concept`` category. Older
    versions copied their reserved ``semantic_hub_*`` key into the self model
    under one or more ``expressed_`` prefixes, losing that category. Normalize
    only this reserved machine provenance marker for backwards compatibility.
    """
    if not isinstance(record, Mapping):
        return False
    category = str(record.get("category") or record.get("source_category") or "")
    if category == "semantic_concept":
        return True

    name = str(record.get("name") or key or "").strip().lower()
    while name.startswith("expressed_"):
        name = name[len("expressed_"):]
    return name.startswith("semantic_hub_")
