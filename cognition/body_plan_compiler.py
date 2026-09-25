"""Translate a natural-language Body request into a validated plan draft.

The compiler is deliberately separate from actuation.  An LLM may interpret
the user's intention, but it cannot choose an unknown entity or bypass the
Body's snapshot, capability and safety validation.
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, Optional


_VERBS = {"navigate", "grab", "release", "push", "wait", "inspect"}


def _mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, json.JSONDecodeError):
            return {}
    return {}


def _extract_json(raw: str) -> Optional[Dict[str, Any]]:
    text = str(raw or "").strip()
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).replace("```", "").strip()
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None
        try:
            value = json.loads(match.group(0))
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            return None


def _split_implicit_release_steps(steps: list[dict[str, Any]], snapshot: Dict[str, Any]) -> list[dict[str, Any]]:
    """Expand navigation steps whose postcondition describes a placement.

    Some providers compress ``navigate to chair`` plus ``cup on chair`` into
    one step. The Body cannot make that physical transition implicitly: it
    must arrive, then release. Expand the semantic postcondition without
    relying on object names or a fixed room scenario.
    """
    expanded: list[dict[str, Any]] = []
    for index, step in enumerate(steps):
        postconditions = list(step.get("postconditions") or [])
        placement = next(
            (predicate for predicate in postconditions
             if isinstance(predicate, dict)
             and str(predicate.get("type") or "").lower() in {"on_surface", "goal_reached"}),
            None,
        )
        if step.get("verb") != "navigate" or placement is None:
            expanded.append(step)
            continue
        destination = str(placement.get("surface") or placement.get("goal") or step.get("target") or "")
        held = str(placement.get("target") or "")
        next_step = steps[index + 1] if index + 1 < len(steps) else None
        has_explicit_release = bool(
            next_step and next_step.get("verb") == "release"
            and str(next_step.get("target") or "") == destination
        )
        navigation = dict(step)
        navigation["postconditions"] = [] if not has_explicit_release else [
            predicate for predicate in postconditions if predicate is not placement
        ]
        expanded.append(navigation)
        if not has_explicit_release:
            release = {
                "step_id": f"{step.get('step_id') or index + 1}-release",
                "verb": "release",
                "target": destination,
                "arguments": {"surface": destination, "held": held} if held else {"surface": destination},
                "preconditions": [],
                "postconditions": postconditions,
                "max_retries": int(step.get("max_retries", 3) or 3),
            }
            expanded.append(release)
    return expanded


def _normalize_release_steps(steps: list[dict[str, Any]], snapshot: Dict[str, Any]) -> None:
    """Repair an ambiguous release target using semantic plan evidence.

    The LLM can refer to the held object when it means the receiving surface.
    Resolve that ambiguity from an explicit ``on_surface`` postcondition or
    the nearest preceding navigation step, while leaving genuinely unknown
    plans for Body validation to reject.
    """
    objects = {
        str(item.get("id")): str(item.get("kind") or "").lower()
        for item in (snapshot.get("objects") or [])
        if isinstance(item, dict) and item.get("id")
    }
    surface_kinds = {"table", "chair", "shelf", "support", "surface", "zone"}
    held = ""
    for index, step in enumerate(steps):
        verb = str(step.get("verb") or "").lower()
        if verb == "grab" and step.get("target"):
            held = str(step["target"])
            continue
        if verb != "release":
            continue
        arguments = dict(step.get("arguments") or {})
        destination = str(arguments.get("surface") or arguments.get("destination") or step.get("target") or "")
        inferred_surface = ""
        inferred_held = str(arguments.get("held") or "")
        for predicate in step.get("postconditions") or []:
            if not isinstance(predicate, dict):
                continue
            predicate_type = str(predicate.get("type") or "").lower()
            if predicate_type not in {"on_surface", "goal_reached"}:
                continue
            inferred_surface = str(predicate.get("surface") or predicate.get("goal") or "")
            inferred_held = inferred_held or str(predicate.get("target") or "")
            break
        if not inferred_surface and objects.get(destination) in surface_kinds:
            inferred_surface = destination
        if not inferred_surface and objects.get(destination) not in surface_kinds:
            # A preceding navigate step is the generic structural cue for a
            # destination, independent of any particular room or object names.
            for previous in reversed(steps[:index]):
                if previous.get("verb") == "navigate" and objects.get(str(previous.get("target") or "")) in surface_kinds:
                    inferred_surface = str(previous["target"])
                    break
        if inferred_surface:
            step["target"] = inferred_surface
            arguments["surface"] = inferred_surface
        if inferred_held or held:
            arguments["held"] = inferred_held or held
        step["arguments"] = arguments


def compile_body_plan(
    request: str,
    snapshot: Dict[str, Any],
    llm: Callable[..., str],
    *,
    max_tokens: int = 1400,
) -> Dict[str, Any]:
    """Return a safe plan draft, never an actuator command.

    Entity names come from the current Body snapshot.  The LLM supplies only
    intent and ordering; the Body remains responsible for final acceptance.
    """
    if not str(request or "").strip():
        return {"accepted": False, "status": "invalid", "error": "empty Body request"}
    system = (
        "You translate a user's physical-world request into a generic Body plan. "
        "Use only entity ids present in the supplied snapshot; never invent one. "
        "Do not execute anything and do not write prose. Preserve the user's "
        "requested destination, even when it differs from prior tasks. "
        "Return compact JSON with objective, steps, required_capabilities and "
        "constraints. Each step needs only step_id, verb, target and, when "
        "needed, postconditions. Do not emit empty arguments or preconditions. "
        "Allowed verbs are navigate, grab, release, push, wait and inspect. "
        "Only list hardware or actuator capabilities in required_capabilities; "
        "wait, inspect, observe, replan and avoid are intrinsic Body operations "
        "and must be omitted from that list. When the user asks to avoid or "
        "circumvent an obstacle, keep the requested destination as the navigate "
        "target and express the obstacle in constraints. Never navigate toward "
        "the obstacle merely because it is mentioned as something to avoid. "
        "For grab, target is the object to hold. For navigate and release, target is "
        "the destination entity. A release target must be the requested receiving "
        "surface (chair, table, shelf or another support), never the held object. "
        "A release may include postcondition {type:on_surface,target:<held object>,surface:<destination>}."
    )
    prompt = json.dumps(
        {"user_request": str(request).strip(), "body_snapshot": snapshot},
        ensure_ascii=False,
    )
    raw = ""
    last_error = ""
    # Prefer provider-enforced JSON. Some local OpenAI-compatible servers do
    # not implement response_format consistently, so retain a plain-prompt
    # retry rather than making the feature provider-specific.
    for attempt, structured in enumerate((True, False), start=1):
        try:
            raw = llm(
                prompt,
                system + (" The previous response was truncated; emit the complete compact JSON now." if attempt == 2 else ""),
                max_tokens=max(900, min(int(max_tokens), 1800)),
                temperature=0.1,
                json_mode=structured,
                reasoning_format="none",
            )
        except TypeError:
            try:
                raw = llm(prompt, system, max_tokens=1600, temperature=0.1)
            except Exception as exc:
                last_error = str(exc)
                continue
        except Exception as exc:
            last_error = str(exc)
            continue
        plan = _extract_json(raw)
        if plan:
            break
    else:
        plan = None
    if not plan:
        detail = str(raw or last_error or "provider returned no content").strip()
        return {"accepted": False, "status": "invalid", "error": f"LLM returned no plan JSON ({detail[:180]})"}
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        return {"accepted": False, "status": "invalid", "error": "plan requires ordered steps"}
    normalized = []
    for index, item in enumerate(steps):
        if not isinstance(item, dict):
            return {"accepted": False, "status": "invalid", "error": f"step {index + 1} is not an object"}
        verb = str(item.get("verb") or "").strip().lower()
        if verb not in _VERBS:
            return {"accepted": False, "status": "invalid", "error": f"unsupported Body verb: {verb or '<empty>'}"}
        normalized.append({
            "step_id": str(item.get("step_id") or f"step-{index + 1}"),
            "verb": verb,
            "target": str(item.get("target") or ""),
            "arguments": _mapping(item.get("arguments")),
            "preconditions": list(item.get("preconditions") or []),
            "postconditions": list(item.get("postconditions") or []),
            "max_retries": int(item.get("max_retries", 3) or 3),
        })
    normalized = _split_implicit_release_steps(normalized, snapshot)
    _normalize_release_steps(normalized, snapshot)
    intrinsic = {"wait", "inspect", "observe", "replan", "avoid"}
    required_capabilities = [
        str(value) for value in plan.get("required_capabilities") or []
        if str(value).strip().lower() not in intrinsic
    ]
    return {
        "accepted": True,
        "status": "draft",
        "requires_confirmation": True,
        "objective": str(plan.get("objective") or request).strip(),
        "source": "chat",
        "steps": normalized,
        "required_capabilities": required_capabilities,
        "constraints": _mapping(plan.get("constraints")),
        "body_snapshot_id": snapshot.get("snapshot_id"),
    }
