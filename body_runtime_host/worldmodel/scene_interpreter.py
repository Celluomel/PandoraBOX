"""Asynchronous Body-side scene interpretation.

The interpreter turns the Body's grounded sensor packet into a compact,
structured description for navigation support. It never selects or executes
an actuator command; geometry and the task planner remain authoritative.
"""
from __future__ import annotations

import json
import logging
import math
import re
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Dict, Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .perception import canonical_category

logger = logging.getLogger(__name__)


def _cosine(left: list[float], right: list[float]) -> float:
    """Return a bounded cosine score without making geometry decisions."""
    if not left or not right or len(left) != len(right):
        return -1.0
    dot = sum(a * b for a, b in zip(left, right))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if not norm_left or not norm_right:
        return -1.0
    return dot / (norm_left * norm_right)


class BodySceneInterpreter:
    def __init__(self, config: Dict[str, Any]):
        self._config = config
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="body-scene-llm")
        self._future: Optional[Future] = None
        self._last_submit = 0.0
        self._last_effective_interval = self._interval()
        self._last_cadence_reason = "initial"
        self._grounding_samples = 0
        self._grounding_precision_sum = 0.0
        self._grounding_rejected = 0
        self._embedding_cache: Dict[str, list[float]] = {}
        self._latest: Dict[str, Any] = {
            "status": "disabled",
            "model": str(config.get("BODY_LLM_MODEL") or ""),
            "updated_at": 0.0,
        }

    def _enabled(self) -> bool:
        return bool(self._config.get("BODY_LLM_ENABLED", False))

    def _base_url(self) -> str:
        return str(self._config.get("BODY_LLM_BASE_URL") or "http://127.0.0.1:1234/v1").rstrip("/")

    def _interval(self) -> float:
        try:
            return max(2.0, float(self._config.get("BODY_LLM_INTERVAL", 8.0) or 8.0))
        except (TypeError, ValueError):
            return 8.0

    @staticmethod
    def _number(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _interval_for_packet(self, packet: Dict[str, Any]) -> tuple[float, str]:
        """Tie semantic scene sampling to measured motion and safety risk.

        The Body LLM is advisory and expensive, so it should not interpret an
        unchanged scene at a fixed rate.  Motion is measured by the Body
        runtime between sensor frames; risk is derived from generic clearance
        and recovery fields, not from object names or a particular scenario.
        """
        base = self._interval()
        motion = packet.get("motion") if isinstance(packet.get("motion"), dict) else {}
        speed = max(0.0, self._number(motion.get("speed")))
        relative_speed = max(0.0, self._number(motion.get("relative_speed"), speed))
        closing_speed = max(0.0, self._number(motion.get("closing_speed")))
        angular_speed = max(0.0, self._number(motion.get("angular_speed")))
        effective_speed = max(speed, relative_speed, closing_speed, angular_speed)
        risk = max(0.0, min(1.0, self._number(motion.get("perception_risk"))))
        moving = bool(motion.get("moving")) or effective_speed > 0.05
        if not moving and risk < 0.25:
            return base, "rest"

        reference = max(0.1, self._number(self._config.get("BODY_LLM_SPEED_REFERENCE"), 0.5))
        speed_factor = min(2.0, effective_speed / reference)
        effective = base / (1.0 + speed_factor)
        reason = "motion"
        if risk >= 0.5:
            effective = min(effective, base * 0.35)
            reason = "elevated-risk"
        if risk >= 0.8:
            effective = min(effective, base * 0.2)
            reason = "high-risk"
        return max(1.0, min(base, effective)), reason

    def status(self) -> Dict[str, Any]:
        with self._lock:
            if self._future is not None and self._future.done():
                try:
                    self._latest = dict(self._future.result())
                except Exception as exc:
                    self._latest = self._error(str(exc))
                self._future = None
            current = dict(self._latest)
            current["enabled"] = self._enabled()
            current["model"] = str(self._config.get("BODY_LLM_MODEL") or "")
            current["in_flight"] = bool(self._future and not self._future.done())
            current["effective_interval"] = round(float(self._last_effective_interval), 3)
            current["cadence_reason"] = self._last_cadence_reason
            current["grounding_metrics"] = {
                "samples": self._grounding_samples,
                "average_reference_precision": round(
                    self._grounding_precision_sum / self._grounding_samples, 3
                ) if self._grounding_samples else None,
                "rejected_contexts": self._grounding_rejected,
                "minimum_precision": self._grounding_threshold(),
            }
            if current.get("observed_at"):
                current["age_seconds"] = round(max(0.0, time.time() - float(current["observed_at"])), 3)
                current["fresh"] = current["age_seconds"] <= max(10.0, self._interval() * 2.0)
            return current

    def _grounding_threshold(self) -> float:
        try:
            return max(0.0, min(1.0, float(self._config.get("BODY_LLM_GROUNDING_THRESHOLD", 0.8) or 0.8)))
        except (TypeError, ValueError):
            return 0.8

    def _focus_range(self) -> float:
        try:
            return max(1.0, min(20.0, float(self._config.get("BODY_LLM_FOCUS_RANGE_M", 5.0) or 5.0)))
        except (TypeError, ValueError):
            return 5.0

    def _embedding_model(self) -> str:
        return str(
            self._config.get("BODY_LLM_EMBEDDING_MODEL")
            or self._config.get("QUALITY_EMBED_MODEL")
            or ""
        ).strip()

    def _embedding_threshold(self) -> float:
        try:
            return max(0.0, min(1.0, float(
                self._config.get("BODY_LLM_EMBEDDING_THRESHOLD", 0.78) or 0.78
            )))
        except (TypeError, ValueError):
            return 0.78

    def _semantic_reference_resolver(self, values: list[Any], known: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """Resolve only unknown labels through one bounded embedding batch.

        Exact ids, labels and canonical categories remain authoritative. This
        fallback handles genuine vocabulary variation while keeping the Body's
        measured entities as the only possible targets.
        """
        model = self._embedding_model()
        unknown = []
        for value in values:
            key = " ".join(str(value or "").lower().split())
            if key and key not in unknown:
                unknown.append(key)
        if not model or not unknown or not known:
            return {}
        candidates = []
        candidate_ids = []
        for object_id, item in known.items():
            text = " ".join(str(value) for value in (
                object_id, item.get("label"), item.get("kind"), canonical_category(object_id),
            ) if value).strip()
            candidates.append(text)
            candidate_ids.append(object_id)
        cache_key = f"{self._base_url()}::{model}::{tuple(candidates)}"
        try:
            timeout = min(8.0, max(1.0, float(self._config.get("BODY_LLM_EMBEDDING_TIMEOUT", 4.0) or 4.0)))
        except (TypeError, ValueError):
            timeout = 4.0
        try:
            with self._lock:
                missing = [text for text in candidates if f"{cache_key}::{text}" not in self._embedding_cache]
            if missing:
                logger.info(
                    "[BodyEmbeddings] request model=%s endpoint=%s kind=candidates inputs=%d",
                    model, f"{self._base_url()}/embeddings", len(missing),
                )
                request = Request(
                    f"{self._base_url()}/embeddings",
                    data=json.dumps({"model": model, "input": missing}).encode("utf-8"),
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                logger.info(
                    "[BodyEmbeddings] response model=%s kind=candidates vectors=%d",
                    model, len(payload.get("data") or []),
                )
                rows = sorted(payload.get("data") or [], key=lambda row: int(row.get("index", 0)))
                with self._lock:
                    for text, row in zip(missing, rows):
                        vector = row.get("embedding") if isinstance(row, dict) else None
                        if isinstance(vector, list) and vector:
                            self._embedding_cache[f"{cache_key}::{text}"] = [float(v) for v in vector]
            query_request = Request(
                f"{self._base_url()}/embeddings",
                data=json.dumps({"model": model, "input": unknown}).encode("utf-8"),
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                method="POST",
            )
            logger.info(
                "[BodyEmbeddings] request model=%s endpoint=%s kind=queries inputs=%d",
                model, f"{self._base_url()}/embeddings", len(unknown),
            )
            with urlopen(query_request, timeout=timeout) as response:
                query_payload = json.loads(response.read().decode("utf-8"))
            logger.info(
                "[BodyEmbeddings] response model=%s kind=queries vectors=%d",
                model, len(query_payload.get("data") or []),
            )
            query_rows = sorted(query_payload.get("data") or [], key=lambda row: int(row.get("index", 0)))
            resolved: Dict[str, str] = {}
            threshold = self._embedding_threshold()
            for value, row in zip(unknown, query_rows):
                vector = row.get("embedding") if isinstance(row, dict) else None
                if not isinstance(vector, list):
                    continue
                scores = []
                for object_id, text in zip(candidate_ids, candidates):
                    with self._lock:
                        candidate_vector = self._embedding_cache.get(f"{cache_key}::{text}")
                    scores.append((
                        _cosine([float(v) for v in vector], candidate_vector or []), object_id
                    ))
                if scores:
                    score, object_id = max(scores)
                    if score >= threshold:
                        resolved[value] = object_id
                        logger.info(
                            "[BodyEmbeddings] accepted label=%r target=%s score=%.3f threshold=%.3f",
                            value, object_id, score, threshold,
                        )
                    else:
                        logger.info(
                            "[BodyEmbeddings] rejected label=%r target=%s score=%.3f threshold=%.3f reason=below_threshold",
                            value, object_id, score, threshold,
                        )
                else:
                    logger.info(
                        "[BodyEmbeddings] rejected label=%r score=unavailable reason=no_candidate_score",
                        value,
                    )
            return resolved
        except Exception as exc:
            logger.warning(
                "[BodyEmbeddings] unavailable model=%s endpoint=%s error=%s",
                model, f"{self._base_url()}/embeddings", str(exc)[:240],
            )
            return {}

    @staticmethod
    def _camera_view_note(camera: Dict[str, Any]) -> str:
        """Describe the current optical geometry without guessing object facts."""
        calibration = camera.get("calibration") if isinstance(camera, dict) else {}
        calibration = calibration if isinstance(calibration, dict) else {}
        profile = str(camera.get("camera_profile") or calibration.get("profile") or "unknown")
        try:
            height = float(calibration.get("height_m"))
        except (TypeError, ValueError):
            height = None
        try:
            elevation = float(calibration.get("elevation_deg"))
        except (TypeError, ValueError):
            elevation = None
        if height is None and elevation is None and not calibration:
            return "The camera calibration is unavailable. Treat apparent size as unreliable."
        details = [f"profile={profile}"]
        if height is not None:
            details.append(f"height={height:.2f}m")
        if elevation is not None:
            details.append(f"elevation={elevation:.1f}deg")
        perspective = "low floor-biased perspective"
        if height is not None and height >= 0.55:
            perspective = "high perspective with stronger top-down separation"
        elif height is not None and height >= 0.30:
            perspective = "intermediate perspective"
        occlusion = " Foreground chassis/legs may occlude nearby surfaces." if calibration.get("foreground_occluders") else ""
        return (
            "Camera geometry is calibrated (" + ", ".join(details) + f", {perspective})."
            " Do not infer range, height or object size from pixels alone; use LiDAR geometry." + occlusion
        )

    def submit(self, packet: Dict[str, Any]) -> None:
        """Schedule at most one bounded interpretation at a time."""
        if not self._enabled():
            return
        now = time.time()
        with self._lock:
            if self._future is not None and not self._future.done():
                return
            interval, reason = self._interval_for_packet(packet)
            self._last_effective_interval = interval
            self._last_cadence_reason = reason
            if now - self._last_submit < interval:
                return
            self._last_submit = now
            self._future = self._executor.submit(self._interpret, packet)

    def interpret_now(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """Run one explicit diagnostic interpretation and publish its result.

        The Body VLM test is a user-triggered diagnostic, so it must be visible
        through the same status endpoint as the background interpreter.  This
        also keeps the UI from showing an old ``No interpretation yet`` value
        after a successful test.
        """
        result = self._interpret(packet)
        with self._lock:
            self._latest = dict(result)
        return result

    def _error(self, message: str) -> Dict[str, Any]:
        return {
            "status": "error",
            "error": str(message)[:240],
            "updated_at": time.time(),
            "model": str(self._config.get("BODY_LLM_MODEL") or ""),
        }

    @staticmethod
    def _ground_interpretation(interpretation: Dict[str, Any], packet: Dict[str, Any], label_resolver=None) -> Dict[str, Any]:
        """Turn free-form LLM semantics into a Body-owned scene model.

        The LLM may name and describe only entities present in the measured
        packet. Positions, ranges and collision geometry always come from the
        sensor projection and are copied here without modification.
        """
        objects = [item for item in packet.get("objects") or [] if isinstance(item, dict)]
        known = {str(item.get("id")): item for item in objects if item.get("id")}
        labels = {
            " ".join(str(item.get("label") or item_id).lower().split()): item_id
            for item_id, item in known.items()
        }
        normalized_labels = {}
        for item_id, item in known.items():
            for value in (item_id, item.get("label"), item.get("kind")):
                category = canonical_category(value)
                if category not in normalized_labels:
                    normalized_labels[category] = item_id

        def as_items(value: Any) -> list[Any]:
            """Keep normalization total when a VLM emits a scalar for an array."""
            if isinstance(value, (list, tuple)):
                return list(value)
            if value is None:
                return []
            return [value]

        unresolved: list[str] = []
        semantic_matches: Dict[str, str] = {}

        def resolve_reference(value: Any) -> str:
            reference = " ".join(str(value or "").lower().split())
            if reference in known:
                return reference
            if reference in labels:
                return labels[reference]
            resolved = normalized_labels.get(canonical_category(value), "")
            if not resolved:
                key = " ".join(str(value or "").lower().split())
                if key:
                    unresolved.append(key)
                    resolved = semantic_matches.get(key, "")
            return resolved

        if label_resolver:
            raw_values = list(as_items(interpretation.get("primary_objects")))
            raw_values.extend(
                item.get("id") or item.get("label")
                for item in (interpretation.get("object_descriptions") or [])
                if isinstance(item, dict)
            )
            semantic_matches.update(label_resolver(raw_values, known) or {})

        primary = [resolve_reference(value) for value in as_items(interpretation.get("primary_objects"))]
        primary = [value for value in primary if value]
        descriptions = {}
        raw_descriptions = interpretation.get("object_descriptions") or []
        if isinstance(raw_descriptions, dict):
            raw_descriptions = [dict(value, id=key) for key, value in raw_descriptions.items() if isinstance(value, dict)]
        for item in raw_descriptions:
            if not isinstance(item, dict):
                continue
            object_id = resolve_reference(item.get("id") or item.get("label"))
            if object_id not in known:
                continue
            descriptions[object_id] = {
                "description": str(item.get("description") or "")[:240],
                "role": str(item.get("role") or known[object_id].get("kind") or "object")[:80],
                "affordances": [str(value)[:50] for value in as_items(item.get("affordances"))][:8],
            }
        entities = []
        for object_id, observed in known.items():
            entity = {
                "id": object_id,
                "label": observed.get("label") or object_id,
                "kind": observed.get("kind") or "object",
                "position": list(observed.get("position") or []),
                "size": observed.get("size"),
                "observed": True,
            }
            entity.update(descriptions.get(object_id, {}))
            entities.append(entity)
        allowed_actions = {"forward", "sprint", "backward", "retreat", "turn_left", "turn_right", "wait", "grab", "release"}
        paths = []
        for path in as_items(interpretation.get("possible_paths")):
            if not isinstance(path, dict) or str(path.get("action") or "") not in allowed_actions:
                continue
            paths.append({
                "action": str(path["action"]),
                "reason": str(path.get("reason") or "")[:240],
                "target_id": str(path.get("target_id") or "") if str(path.get("target_id") or "") in known else None,
            })
        primary_total = len([value for value in (interpretation.get("primary_objects") or []) if value])
        primary_valid = len(primary)
        description_total = len([item for item in raw_descriptions if isinstance(item, dict)])
        description_valid = len(descriptions)
        referenced_total = primary_total + description_total
        referenced_valid = primary_valid + description_valid
        fusion = packet.get("sensor_fusion")
        if not isinstance(fusion, dict):
            fusion = ((packet.get("sensor_projections") or {}).get("fusion")
                      if isinstance(packet.get("sensor_projections"), dict) else {})
        return {
            "contract": "semantic_scene.v1",
            "frame_id": packet.get("frame_id"),
            "observed_at": packet.get("timestamp"),
            "entities": entities,
            "primary_object_ids": primary,
            "environment": [str(value)[:240] for value in as_items(interpretation.get("environment"))][:16],
            "possible_paths": paths[:12],
            "uncertainty": [str(value)[:240] for value in as_items(interpretation.get("uncertainty"))][:12],
            "sensor_fusion": {
                "matched": int((fusion or {}).get("matched", 0) or 0),
                "lidar_returns": int((fusion or {}).get("lidar_returns", 0) or 0),
                "unmatched_vision": list((fusion or {}).get("unmatched_vision") or [])[:16],
                "unmatched_lidar_point_indices": list(
                    (fusion or {}).get("unmatched_lidar_point_indices") or []
                )[:32],
                "method": str((fusion or {}).get("method") or "unavailable"),
                "geometry_authoritative": str((fusion or {}).get("geometry_authoritative") or "lidar"),
            },
            "geometry_source": "sensor_projections",
            "llm_role": "semantic_interpretation_only",
            "grounding": {
                "observed_object_count": len(known),
                "primary_object_references": primary_total,
                "valid_primary_object_references": primary_valid,
                "described_object_references": description_total,
                "valid_described_object_references": description_valid,
                "invented_object_references": max(0, referenced_total - referenced_valid),
                "reference_precision": round(
                    referenced_valid / referenced_total, 3
                ) if referenced_total else 1.0,
                "frame_id": packet.get("frame_id"),
                "geometry_authoritative": True,
                "accepted_for_context": False,
                "semantic_matches": len(semantic_matches),
                "semantic_match_labels": dict(semantic_matches),
                "embedding_threshold": None,
            },
        }

    @staticmethod
    def _parse_json_object(content: str) -> Optional[Dict[str, Any]]:
        """Extract one JSON object without trusting surrounding model prose."""
        text = str(content or "").strip()
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()
        decoder = json.JSONDecoder()
        for match in re.finditer(r"\{", text):
            try:
                value, _ = decoder.raw_decode(text[match.start():])
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value
        return None

    def _interpret(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        model = str(self._config.get("BODY_LLM_MODEL") or "").strip()
        if not model:
            return self._error("BODY_LLM_MODEL is not configured")
        # Keep the provider prompt compact.  The full perception frame is
        # still exposed through the Body API, but sending it here duplicates
        # the same LiDAR, projections and fusion data several times.  The
        # camera image is attached separately below as a vision part.
        prompt_packet = {
            key: packet.get(key)
            for key in ("timestamp", "frame_id", "contract", "source", "confidence", "body", "objects", "motion", "navigation")
            if key in packet
        }
        for bulky_key in ("perception_frame", "vision_2d", "lidar_3d", "sensor_fusion", "quality"):
            prompt_packet.pop(bulky_key, None)
        if packet.get("visual_blind"):
            # Evaluation mode: the image and LiDAR are the evidence. The
            # simulator's object list remains outside the prompt for scoring.
            prompt_packet.pop("objects", None)
            prompt_packet["visual_validation"] = (
                "Identify only objects visibly supported by the attached image "
                "and LiDAR. Use semantic names such as table, chair, cup or "
                "obstacle when appropriate; do not assume unseen objects."
            )
        else:
            prompt_packet["objects"] = [
                {key: item.get(key) for key in ("id", "label", "kind")}
                for item in packet.get("objects") or [] if isinstance(item, dict)
            ]
        # The image is attached as a vision part below. Never duplicate its
        # Base64 bytes inside the JSON prompt; that doubles latency and token
        # transport for every Body interpretation.
        modalities = dict(packet.get("modalities") or {})
        camera_meta = dict(modalities.get("camera") or {})
        camera_image = camera_meta.pop("image_base64", None) or camera_meta.pop("image_url", None)
        depth_image = camera_meta.pop("depth_base64", None)
        camera_meta["image_attached"] = bool(camera_image)
        camera_meta["depth_attached"] = bool(depth_image)
        modalities["camera"] = camera_meta
        lidar = dict(modalities.get("lidar") or {})
        points = [point for point in lidar.get("points") or [] if isinstance(point, dict)]
        if len(points) > 96:
            # Preserve the nearest returns first; the full cloud remains in
            # the Body perception API and is not needed for semantic captioning.
            points.sort(key=lambda point: self._number(point.get("range_m"), float("inf")))
            lidar["points"] = points[:96]
            lidar["points_truncated"] = len(points) - 96
        modalities["lidar"] = lidar
        if packet.get("visual_blind"):
            # Do not leak simulator identities through the derived projections.
            # The vision model must infer them from pixels and unlabeled ranges.
            vision = dict(modalities.get("vision_projection") or {})
            vision.pop("objects", None)
            modalities["vision_projection"] = vision
            lidar = dict(modalities.get("lidar") or {})
            lidar["points"] = [
                {key: value for key, value in point.items() if key != "object_id"}
                for point in lidar.get("points") or [] if isinstance(point, dict)
            ]
            modalities["lidar"] = lidar
            # The association layer is used for post-call scoring, but must
            # not leak simulator identities or fused labels to the blind VLM.
            modalities.pop("fusion", None)
            prompt_packet.pop("sensor_fusion", None)
        prompt_packet["modalities"] = modalities
        prompt_packet["attention"] = {
            "policy": "near_actionable_and_hazardous",
            "focus_range_m": self._focus_range(),
            "max_detailed_objects": 5,
            "global_context": "summarize distant structure without enumerating uncertain objects",
            "uncertainty_rule": "use uncertain instead of inventing an object",
        }
        camera_view_note = self._camera_view_note(modalities.get("camera") or {})
        prompt = (
            "Interpret this timestamped Body sensor packet. The packet contract is authoritative "
            "about timestamps and provenance. Return JSON only with keys: "
            "scene_summary (one concise global sentence), primary_objects (array of ids or semantic labels for "
            "near, actionable or hazardous objects only), object_descriptions (array of at most five "
            "near/actionable/hazardous objects with id, description, role and affordances), environment (array of "
            "observed facts), possible_paths (array of objects with action and reason), "
            "movement_support (array of monitoring or recovery suggestions), uncertainty (array). "
            f"Prioritize objects within approximately {self._focus_range():.1f} metres of the Body, objects on the "
            "current path, and hazards. Do not enumerate distant objects unless they are necessary for navigation. "
            "A distant or ambiguous visual shape must go into uncertainty, not into primary_objects. "
            + camera_view_note + " "
            "Use only observed data. Prefer native camera/LiDAR returns when quality says native; "
            "label derived projections as inferred. Do not invent objects, coordinates, or completion. "
            "This is advisory perception; never issue actuator commands.\n\n"
            + json.dumps(prompt_packet, ensure_ascii=False, separators=(",", ":"))
        )
        logger.info(
            "[BodyVLM] prompt model=%s chars=%d estimated_tokens=%d context_window=%s image=%s lidar_points=%d",
            model,
            len(prompt),
            max(1, len(prompt) // 4),
            self._config.get("BODY_LLM_CONTEXT_WINDOW", "unknown"),
            bool(camera_image),
            len(lidar.get("points") or []),
        )
        user_content: Any = prompt
        camera = packet.get("modalities", {}).get("camera") if isinstance(packet.get("modalities"), dict) else None
        if isinstance(camera, dict):
            image = camera.get("image_base64") or camera.get("image_url")
            if image:
                if str(image).startswith("data:") or str(image).startswith("http"):
                    image_url = str(image)
                else:
                    mime = str(camera.get("mime_type") or "image/jpeg")
                    image_url = f"data:{mime};base64,{image}"
                # OpenAI-compatible vision format, supported by LM Studio
                # vision models. Text-only models simply use the JSON branch.
                user_content = [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ]
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are the local embodied-scene interpreter for a robot Body."},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
            "max_tokens": int(self._config.get("BODY_LLM_MAX_TOKENS", 360) or 360),
            # LM Studio vision providers differ in structured-output support.
            # Text mode is the interoperable contract; the bounded JSON parser
            # below remains responsible for validating the returned object.
            "response_format": {"type": "json_object"} if bool(
                self._config.get("BODY_LLM_JSON_MODE", True)
            ) else {"type": "text"},
            "stream": False,
        }
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        token = str(self._config.get("BODY_LLM_TOKEN") or "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        timeout = float(self._config.get("BODY_LLM_TIMEOUT", 8.0) or 8.0)
        def request_completion() -> Dict[str, Any]:
            request = Request(
                f"{self._base_url()}/chat/completions",
                data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST",
            )
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))

        try:
            result = request_completion()
        except HTTPError as exc:
            # LM Studio versions differ in JSON-schema support. First remove
            # that optional constraint, then fall back to text-only input for
            # instruct models that reject a vision content part with 400/422.
            if exc.code not in {400, 422}:
                raise
            payload.pop("response_format", None)
            try:
                result = request_completion()
            except HTTPError as retry_exc:
                if retry_exc.code not in {400, 422} or not isinstance(user_content, list):
                    raise
                payload["messages"][1]["content"] = prompt
                result = request_completion()
        content = (((result.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
        if not content:
            return self._error("Body LLM returned no content")
        interpretation = self._parse_json_object(content)
        if interpretation is None:
            # Keep the recovery generic and bounded. A local model may emit a
            # nearly valid object even when JSON response mode is unavailable;
            # ask it once to normalize its own output, without adding facts or
            # allowing the repair path to issue an actuator command.
            repair_payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Convert the supplied model output into one valid JSON object. "
                            "Preserve only information already present. Do not add facts, "
                            "markdown, commentary, or actuator commands. Return JSON only."
                        ),
                    },
                    {"role": "user", "content": content[:12000]},
                ],
                "temperature": 0.0,
                "max_tokens": int(self._config.get("BODY_LLM_MAX_TOKENS", 360) or 360),
                "stream": False,
            }
            try:
                repair_request = Request(
                    f"{self._base_url()}/chat/completions",
                    data=json.dumps(repair_payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urlopen(repair_request, timeout=timeout) as response:
                    repaired_result = json.loads(response.read().decode("utf-8"))
                repaired_content = (
                    (((repaired_result.get("choices") or [{}])[0].get("message") or {}).get("content") or "")
                    .strip()
                )
                interpretation = self._parse_json_object(repaired_content)
            except Exception as exc:
                logger.debug("Body LLM JSON repair failed: %s", exc)
        if interpretation is None:
            return self._error("Body LLM returned malformed JSON interpretation")
        semantic_scene = self._ground_interpretation(
            interpretation, packet, self._semantic_reference_resolver
        )
        semantic_scene["grounding"]["embedding_threshold"] = self._embedding_threshold()
        grounding = semantic_scene.get("grounding") or {}
        precision = float(grounding.get("reference_precision", 0.0) or 0.0)
        referenced = (
            int(grounding.get("primary_object_references", 0) or 0)
            + int(grounding.get("described_object_references", 0) or 0)
        )
        valid_references = (
            int(grounding.get("valid_primary_object_references", 0) or 0)
            + int(grounding.get("valid_described_object_references", 0) or 0)
        )
        # An empty description must not pass the grounding gate merely because
        # zero references produces a vacuous precision of 1.0.
        accepted = (
            referenced > 0
            and valid_references > 0
            and precision >= self._grounding_threshold()
            and bool(grounding.get("geometry_authoritative"))
        )
        grounding["accepted_for_context"] = accepted
        semantic_scene["grounding"] = grounding
        with self._lock:
            self._grounding_samples += 1
            self._grounding_precision_sum += precision
            if not accepted:
                self._grounding_rejected += 1
        return {
            "status": "interpreted",
            "model": model,
            "observed_at": packet.get("timestamp"),
            "updated_at": time.time(),
            "interpretation": interpretation,
            "semantic_scene": semantic_scene,
        }

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
