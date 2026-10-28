"""Conservative, transport-safe evidence classification for Body actions.

A controller success response is only an acknowledgement. Physical effect
verification requires independently observed postconditions and is not inferred
from two timestamps or a successful HTTP response.
"""
from __future__ import annotations

import math
import time
from typing import Any, Dict, Optional


def classify_action_evidence(
    outcome: Dict[str, Any],
    *,
    before_timestamp: Optional[float] = None,
    after_timestamp: Optional[float] = None,
    source_simulated: bool = False,
    postcondition_observed: bool = False,
    now: Optional[float] = None,
) -> Dict[str, Any]:
    now = time.time() if now is None else float(now)
    kind = str((outcome or {}).get("kind") or "unknown")
    fresh = False
    try:
        if before_timestamp is not None and after_timestamp is not None:
            before = float(before_timestamp)
            after = float(after_timestamp)
            fresh = (
                all(math.isfinite(v) for v in (before, after, now))
                and 0 <= now - after <= 5.0
                and 0 <= now - before <= 5.0
                and after > before
            )
    except (TypeError, ValueError, OverflowError):
        pass
    if kind in {"failure", "danger"}:
        state = "failed"
    elif kind == "neutral":
        state = "not_executed"
    elif kind == "success" and fresh and postcondition_observed:
        state = "verified_simulation" if source_simulated else "verified_observation"
    elif kind == "success":
        state = "acknowledged_unverified"
    else:
        state = "unknown"
    return {
        "state": state,
        "acknowledged": kind == "success",
        "postcondition_observed": bool(postcondition_observed and fresh),
        "observation_fresh": fresh,
        "source_simulated": bool(source_simulated),
        "physical_effect_verified": state == "verified_observation",
        "eligible_for_verified_learning": state in {"verified_simulation", "verified_observation"},
    }
