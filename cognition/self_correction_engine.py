"""Persistent, low-latency self-correction from observable interaction errors.

This is deliberately a small control loop, not another prose generator.  It
turns a correction into a reusable behavioural rule and keeps evidence for
whether later turns improved.  The rule is injected into the next prompt;
the LLM still supplies the language, while this module owns the adaptation.
"""
from __future__ import annotations

import json
import logging
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_CORRECTION_MARKERS = (
    "tu as raison", "vous avez raison", "loupé", "rate", "incorrect",
    "ce n'est pas", "ce n’est pas", "tu oublies", "mais si", "en fait",
    "wrong", "that's not", "you missed", "you forgot", "actually",
)
_POSITIVE_MARKERS = ("exact", "correct", "c'est ça", "that's right", "yes")


def _contains_feedback_marker(text: str, markers: tuple[str, ...]) -> bool:
    normalized = str(text or "").casefold()
    return any(
        re.search(r"(?<!\w)" + re.escape(marker.casefold()) + r"(?!\w)", normalized)
        for marker in markers
    )


class SelfCorrectionEngine:
    """Learn compact response policies from corrections without blocking chat."""

    def __init__(self, path: str = "data/persona/self_corrections.json") -> None:
        self._path = Path(path)
        self._lock = threading.RLock()
        self._rules: List[Dict[str, Any]] = []
        self._load()

    def prompt_fragment(self, user_input: str = "") -> str:
        """Return only relevant, sufficiently evidenced rules for this turn."""
        query = self._tokens(user_input)
        with self._lock:
            rules = [r for r in self._rules if float(r.get("confidence", 0)) >= 0.55]
            ranked = []
            for rule in rules:
                context = self._tokens(str(rule.get("context", "")))
                overlap = len(query & context) if query and context else 0
                # A high-confidence correction from an unrelated topic must
                # not become a standing instruction for every future turn.
                # Require an actual lexical bridge, then rank by relevance
                # before confidence/use count.
                if overlap:
                    ranked.append((overlap, float(rule.get("confidence", 0)),
                                   int(rule.get("uses", 0)), rule))
            ranked.sort(key=lambda item: item[:3], reverse=True)
            selected = [item[3] for item in ranked[:2]]
        if not selected:
            return ""
        lines = [
            "[Self-correction guidance] Apply these learned response rules silently; "
            "do not mention telemetry or the rule itself:"
        ]
        for rule in selected:
            lines.append(
                f"- {rule['rule']} (evidence={int(rule.get('evidence', 0))}, "
                f"confidence={float(rule.get('confidence', 0)):.2f})"
            )
        return "\n".join(lines)

    def observe(
        self,
        user_input: str,
        response: str,
        validator_score: Optional[float] = None,
        cycle_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Record a correction or outcome and update the applicable rule."""
        text = f"{user_input or ''} {response or ''}".strip()
        lower = (user_input or "").lower()
        correction = _contains_feedback_marker(lower, _CORRECTION_MARKERS)
        positive = _contains_feedback_marker(lower, _POSITIVE_MARKERS)

        with self._lock:
            # A later turn is evidence about whether the previous guidance held.
            confirmed_rule_ids = []
            for rule in self._rules:
                if rule.get("pending") and positive and not correction:
                    rule["successful_turns"] = int(rule.get("successful_turns", 0)) + 1
                    rule["confidence"] = min(0.95, float(rule.get("confidence", 0.55)) + 0.015)
                    rule["pending"] = False
                    confirmed_rule_ids.append(str(rule.get("id", "")))
                elif rule.get("pending") and correction:
                    rule["confidence"] = max(0.20, float(rule.get("confidence", 0.55)) - 0.08)
                    rule["pending"] = False

            if positive and not correction:
                self._save()
                return {
                    "status": "explicit_positive_feedback",
                    "feedback_kind": "positive",
                    "confirmed_rule_ids": confirmed_rule_ids[:8],
                }

            if not correction and validator_score is not None and validator_score >= 0.70:
                self._save()
                return None
            if not correction and not positive:
                self._save()
                return None

            rule_text = self._derive_rule(user_input)
            context = (user_input or "")[:240]
            feedback_kind = "correction" if correction else "positive"
            existing = next(
                (r for r in self._rules if r.get("rule") == rule_text), None
            )
            if existing:
                existing["evidence"] = int(existing.get("evidence", 0)) + 1
                existing["uses"] = int(existing.get("uses", 0)) + 1
                existing["confidence"] = min(0.95, float(existing.get("confidence", 0.55)) + 0.06)
                existing["context"] = context
                existing["pending"] = True
                existing["feedback_kind"] = feedback_kind
                result = existing
            else:
                result = {
                    "id": "corr_" + uuid.uuid4().hex[:10],
                    "rule": rule_text,
                    "context": context,
                    "evidence": 1,
                    "uses": 1,
                    "successful_turns": 0,
                    "confidence": 0.58,
                    "pending": True,
                    "feedback_kind": feedback_kind,
                    "created_at": time.time(),
                    "last_seen": time.time(),
                }
                self._rules.append(result)
            result["last_seen"] = time.time()
            self._rules = sorted(self._rules, key=lambda r: r.get("last_seen", 0))[-40:]
            self._save()
            logger.info(
                "[SelfCorrection] learned rule=%r evidence=%s confidence=%.2f",
                result["rule"], result["evidence"], result["confidence"],
            )
            return dict(result)

    @staticmethod
    def _derive_rule(user_input: str) -> str:
        lower = (user_input or "").lower()
        if any(word in lower for word in ("objectif", "but", "intention", "laver", "cuire", "rattraper")):
            return (
                "Identify the user's primary intended action first; verify its required "
                "agent, object, preconditions, and physical limits before discussing secondary benefits."
            )
        if any(word in lower for word in ("temps", "heure", "demain", "future", "futur", "saint denis")):
            return (
                "Anchor the answer in the present state, then check elapsed time, causal order, "
                "and the future deadline before recommending an action."
            )
        return (
            "Treat the user's correction as evidence about the current task; restate the "
            "corrected constraint and adapt the next answer instead of defending the prior framing."
        )

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {t for t in re.findall(r"[a-zàâçéèêëîïôùûüÿñæœ0-9]+", text.lower()) if len(t) > 3}

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "rules": len(self._rules),
                "evidenced_rules": sum(1 for r in self._rules if int(r.get("evidence", 0)) > 0),
                "top_rules": [dict(r) for r in sorted(
                    self._rules, key=lambda r: float(r.get("confidence", 0)), reverse=True
                )[:5]],
            }

    def _load(self) -> None:
        try:
            if self._path.exists():
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._rules = list(data.get("rules", [])) if isinstance(data, dict) else []
        except Exception as exc:
            logger.debug("[SelfCorrection] load failed: %s", exc)

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps({"version": 1, "rules": self._rules}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.debug("[SelfCorrection] save failed: %s", exc)
