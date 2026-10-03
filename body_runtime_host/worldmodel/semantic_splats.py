"""Bridge grounded VLM semantics into Gaussian-splat renderer metadata."""
from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List


def build_semantic_splat_scene(
    observed_objects: Iterable[Dict[str, Any]],
    semantic_scene: Dict[str, Any] | None,
    *,
    frame_id: str,
    simulated: bool = False,
) -> Dict[str, Any]:
    """Create render groups only from accepted VLM references to observed entities.

    VLM-provided positions are intentionally ignored. The group anchor and
    extent are copied from the current Body observation; VLM fields provide
    semantic organization and display metadata only.
    """
    scene = semantic_scene if isinstance(semantic_scene, dict) else {}
    grounding = scene.get("grounding") or {}
    if not isinstance(grounding, dict):
        grounding = {}
    result: Dict[str, Any] = {
        "contract": "body_semantic_splats.v1",
        "status": "waiting_for_grounded_vlm",
        "frame_id": str(frame_id),
        "source": "body_vlm",
        "geometry_source": "current_body_observation",
        "appearance_source": "camera_reconstruction_pending",
        "render_backend": "semantic_group_adapter",
        "preview_only": bool(simulated),
        "safety_authoritative": False,
        "groups": [],
        "unmatched_entity_ids": [],
    }
    if not scene:
        return result
    if scene.get("frame_id") != frame_id:
        result.update({"status": "stale_semantic_frame", "semantic_frame_id": scene.get("frame_id")})
        return result
    if grounding.get("accepted_for_context") is not True or grounding.get("geometry_authoritative") is not True:
        result["status"] = "grounding_rejected"
        return result

    observed = {
        str(item.get("id")): item
        for item in observed_objects
        if isinstance(item, dict) and item.get("id") is not None
    }
    primary = {str(value) for value in scene.get("primary_object_ids") or []}
    groups: List[Dict[str, Any]] = []
    unmatched: List[str] = []
    for entity in scene.get("entities") or []:
        if not isinstance(entity, dict):
            continue
        entity_id = str(entity.get("id") or "")
        if not entity_id:
            continue
        described = bool(entity.get("description") or entity.get("attributes")
                         or entity.get("image_region") or entity.get("relations"))
        if entity_id not in primary and not described:
            continue
        measured = observed.get(entity_id)
        if measured is None:
            unmatched.append(entity_id)
            continue
        position = measured.get("position")
        if not isinstance(position, (list, tuple)) or len(position) < 3:
            unmatched.append(entity_id)
            continue
        try:
            metric_position = [float(value) for value in position[:3]]
            extent = max(0.05, float(measured.get("size") or 0.5))
            if not all(math.isfinite(value) for value in metric_position + [extent]):
                raise ValueError
        except (TypeError, ValueError):
            unmatched.append(entity_id)
            continue
        groups.append({
            "group_id": f"semantic:{entity_id}",
            "entity_id": entity_id,
            "label": str(entity.get("label") or measured.get("label") or entity_id)[:120],
            "kind": str(entity.get("kind") or measured.get("kind") or "object")[:80],
            "description": str(entity.get("description") or "")[:240],
            "role": str(entity.get("role") or "")[:80],
            "attributes": _safe_attributes(entity.get("attributes")),
            "relations": [item for item in (entity.get("relations") or []) if isinstance(item, dict)][:12]
            if isinstance(entity.get("relations"), (list, tuple)) else [],
            "image_region": _safe_region(entity.get("image_region")),
            "primary": entity_id in primary,
            "confidence": _confidence(entity.get("confidence")),
            "center_m": metric_position,
            "extent_m": extent,
            "coordinate_frame": str(measured.get("coordinate_frame") or "local_map"),
            "geometry_evidence": {
                "source": str(measured.get("position_source") or "body_observation"),
                "frame_id": frame_id,
                "position_accuracy_m": measured.get("position_accuracy_m"),
            },
            "semantic_evidence": {
                "source": "body_vlm",
                "frame_id": frame_id,
                "grounding_precision": _confidence(grounding.get("reference_precision")),
            },
            "gaussian_membership": "position_binding_pending",
        })

    result.update({
        "status": "ready" if groups else "no_grounded_render_groups",
        "semantic_frame_id": scene.get("frame_id"),
        "grounding_precision": _confidence(grounding.get("reference_precision")),
        "groups": groups,
        "unmatched_entity_ids": unmatched,
    })
    return result


def bind_gaussian_primitives(
    primitives: Iterable[Dict[str, Any]],
    semantic_scene: Dict[str, Any],
) -> Dict[str, Any]:
    """Assign Gaussian centers to nearby grounded semantic entity groups.

    This is a renderer adapter: it does not create or move Gaussian geometry.
    Unmatched primitives remain untouched and can render as unclassified scene
    appearance. Each primitive is assigned to at most one nearest group.
    """
    groups = [item for item in semantic_scene.get("groups", []) if isinstance(item, dict)]
    bound = []
    unbound = []
    for primitive in primitives:
        if not isinstance(primitive, dict):
            continue
        raw_center = primitive.get("center_m") or primitive.get("position_m")
        try:
            center = [float(value) for value in raw_center[:3]]
            if len(center) != 3 or not all(math.isfinite(value) for value in center):
                raise ValueError
        except (TypeError, ValueError, IndexError):
            unbound.append(primitive)
            continue
        candidates = []
        for group in groups:
            anchor = group.get("center_m") or []
            if len(anchor) < 3:
                continue
            distance = math.dist(center, [float(value) for value in anchor[:3]])
            radius = max(0.25, float(group.get("extent_m") or 0.5) * 0.9)
            if distance <= radius:
                candidates.append((distance, group))
        if not candidates:
            unbound.append(primitive)
            continue
        _, group = min(candidates, key=lambda item: item[0])
        bound.append({
            **primitive,
            "semantic_group_id": group["group_id"],
            "semantic_entity_id": group["entity_id"],
            "semantic_label": group["label"],
            "semantic_kind": group["kind"],
            "semantic_confidence": group.get("confidence"),
            "semantic_frame_id": group["semantic_evidence"]["frame_id"],
        })
    return {
        "contract": "body_semantic_splat_bindings.v1",
        "bound": bound,
        "unbound": unbound,
        "bound_count": len(bound),
        "unbound_count": len(unbound),
    }


def _confidence(value: Any) -> float | None:
    try:
        score = float(value)
        if math.isfinite(score):
            return round(max(0.0, min(1.0, score)), 4)
    except (TypeError, ValueError):
        pass
    return None


def _safe_attributes(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key)[:40]: (str(item)[:100] if isinstance(item, str) else item)
        for key, item in list(value.items())[:16]
        if isinstance(item, (str, bool, int, float))
        and not (isinstance(item, float) and not math.isfinite(item))
        and str(key).lower() not in {"position", "coordinates", "x", "y", "z", "center", "size_m"}
    }


def _safe_region(value: Any) -> Dict[str, float] | None:
    if not isinstance(value, dict):
        return None
    try:
        x, y = float(value["x"]), float(value["y"])
        width, height = float(value["width"]), float(value["height"])
    except (KeyError, TypeError, ValueError):
        return None
    if (not all(math.isfinite(v) for v in (x, y, width, height))
            or x < 0 or y < 0 or width <= 0 or height <= 0
            or x + width > 1 or y + height > 1):
        return None
    return {"x": round(x, 5), "y": round(y, 5),
            "width": round(width, 5), "height": round(height, 5)}
