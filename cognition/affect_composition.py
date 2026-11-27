"""Input-driven affect profile composition helpers.

These helpers preserve the affect channels supplied by the model. They do not
classify language, map words to feelings, or constrain the channel vocabulary.
"""
from __future__ import annotations

import math
import re
from typing import Any


_CHANNEL_ID = re.compile(r"^[a-z][a-z0-9_]{0,47}$")
_PROFILE_SCALARS = ("valence", "arousal", "mood_valence", "mood_arousal")


def affect_channel_deviations(profile: Any) -> dict[str, float]:
    """Return finite baseline-relative channel deviations from a snapshot."""
    if not isinstance(profile, dict):
        return {}
    channels = profile.get("channels")
    if not isinstance(channels, dict):
        return {}
    result: dict[str, float] = {}
    for raw_name, item in channels.items():
        name = str(raw_name).casefold()
        if not _CHANNEL_ID.fullmatch(name) or not isinstance(item, dict):
            continue
        try:
            value = float(item["value"])
            baseline = float(item.get("baseline", value))
            deviation = float(item.get("deviation", value - baseline))
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        if all(math.isfinite(number) for number in (value, baseline, deviation)):
            result[name] = max(-1.0, min(1.0, deviation))
    return result


def affect_profile_change(previous: Any, current: Any) -> float:
    """Measure the largest change in channel deviations or affect projections."""
    before = affect_channel_deviations(previous)
    after = affect_channel_deviations(current)
    changes = [abs(after.get(name, 0.0) - before.get(name, 0.0))
               for name in before.keys() | after.keys()]
    for name in _PROFILE_SCALARS:
        try:
            old = float(previous.get(name)) if isinstance(previous, dict) else math.nan
            new = float(current.get(name)) if isinstance(current, dict) else math.nan
        except (TypeError, ValueError, OverflowError):
            continue
        if math.isfinite(old) and math.isfinite(new):
            changes.append(abs(new - old))
    return max(changes, default=0.0)


def describe_affect_configuration(profile: Any, *, limit: int = 6) -> str:
    """Describe a changing affect mixture from the data's own channel names."""
    if not isinstance(profile, dict):
        return "affect configuration unavailable"
    deviations = affect_channel_deviations(profile)
    salient = sorted(
        ((abs(delta), name, delta) for name, delta in deviations.items()
         if abs(delta) >= 0.015),
        reverse=True,
    )[:max(1, min(8, int(limit)))]
    if salient:
        mixture = "; ".join(f"{name} {delta:+.2f} from baseline"
                             for _, name, delta in salient)
    elif deviations:
        mixture = "channel levels are close to their baselines"
    else:
        mixture = "no channel deviations are recorded"

    projections = []
    for name in _PROFILE_SCALARS:
        try:
            value = float(profile[name])
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        if math.isfinite(value):
            projections.append(f"{name}={value:+.2f}" if "valence" in name
                               else f"{name}={value:.2f}")
    suffix = f"; {', '.join(projections)}" if projections else ""
    return f"affect configuration: {mixture}{suffix}"
