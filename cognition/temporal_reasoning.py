"""Universal temporal and causal frame for conversational reasoning.

This is deliberately deterministic and inexpensive. It does not decide the
answer; it constrains generated reasoning to the real order of events.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass(frozen=True)
class TemporalFrame:
    now: datetime
    horizon: Optional[timedelta] = None
    horizon_text: str = ""

    @property
    def deadline(self) -> Optional[datetime]:
        return self.now + self.horizon if self.horizon is not None else None

    def prompt_fragment(self) -> str:
        now = self.now.strftime("%Y-%m-%d %H:%M %Z")
        deadline = self.deadline.strftime("%Y-%m-%d %H:%M %Z") if self.deadline else "not established"
        horizon = self.horizon_text or "no explicit relative horizon detected"
        return "\n".join([
            "Temporal facts and constraints:",
            f"Reference instant: {now}",
            f"User-stated duration: {horizon}",
            f"Computed deadline, when a duration is available: {deadline}",
            "For chronological questions, causes and prerequisites precede their effects and objectives.",
            "Distinguish recorded timestamps from estimates; do not invent missing durations, routes, or start times.",
            "Check practical feasibility against physical, logistical, and human constraints.",
        ])


def _duration(text: str) -> tuple[Optional[timedelta], str]:
    match = re.search(
        r"\b(?:dans|in)\s+(une|un|an|one|\d+)\s*"
        r"(heure|heures|hour|hours|h|minute|minutes)\b",
        text.casefold(),
    )
    if not match:
        return None, ""
    amount = 1 if match.group(1) in {"une", "un", "an", "one"} else int(match.group(1))
    unit = match.group(2)
    minutes = amount * 60 if unit.startswith(("heure", "hour", "h")) else amount
    label = f"{amount} hour(s)" if minutes % 60 == 0 else f"{minutes} minute(s)"
    return timedelta(minutes=minutes), label


def build_temporal_frame(text: str, now: Optional[datetime] = None) -> TemporalFrame:
    """Build a present-anchored frame for any user turn."""
    current = now.astimezone() if now is not None else datetime.now().astimezone()
    horizon, label = _duration(str(text or ""))
    return TemporalFrame(current, horizon, label)

