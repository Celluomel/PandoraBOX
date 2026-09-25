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


def compile_body_plan(
    request: str,
    snapshot: Dict[str, Any],
    llm: Callable[..., str],
    *,
    max_tokens: int = 700,
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
        "Return exactly JSON with objective, steps, required_capabilities and "
        "constraints. Each step has step_id, verb, target, arguments, "
        "preconditions and postconditions. Allowed verbs are navigate, grab, "
        "release, push, wait and inspect. A release onto a surface must include "
        "postcondition {type:on_surface,target:<held object>,surface:<surface>}."
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
    for structured in (True, False):
        try:
            raw = llm(
                prompt,
                system,
                max_tokens=max(320, min(int(max_tokens), 1200)),
                temperature=0.1,
                json_mode=structured,
                reasoning_format="none",
            )
        except TypeError:
            try:
                raw = llm(prompt, system, max_tokens=900, temperature=0.1)
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
            "arguments": dict(item.get("arguments") or {}),
            "preconditions": list(item.get("preconditions") or []),
            "postconditions": list(item.get("postconditions") or []),
            "max_retries": int(item.get("max_retries", 3) or 3),
        })
    return {
        "accepted": True,
        "status": "draft",
        "requires_confirmation": True,
        "objective": str(plan.get("objective") or request).strip(),
        "source": "chat",
        "steps": normalized,
        "required_capabilities": [str(value) for value in plan.get("required_capabilities") or []],
        "constraints": dict(plan.get("constraints") or {}),
        "body_snapshot_id": snapshot.get("snapshot_id"),
    }
