"""Asynchronous Body-side scene interpretation.

The interpreter turns the Body's grounded sensor packet into a compact,
structured description for navigation support. It never selects or executes
an actuator command; geometry and the task planner remain authoritative.
"""
from __future__ import annotations

import json
import importlib.util
import hashlib
import base64
import logging
import math
import re
import threading
import time
from collections import OrderedDict
from pathlib import Path
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Dict, Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .perception import canonical_category

logger = logging.getLogger(__name__)
LOCAL_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _bounded_confidence(value: Any) -> Optional[float]:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    return round(max(0.0, min(1.0, score)), 4) if math.isfinite(score) else None


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
        self._last_provider_latency_s = 0.0
        self._grounding_samples = 0
        self._grounding_precision_sum = 0.0
        self._grounding_rejected = 0
        self._embedding_cache: Dict[str, list[float]] = {}
        self._local_embedding_engine = None
        self._local_embedding_engine_model = ""
        self._embedding_requests = 0
        self._embedding_accepted = 0
        self._embedding_rejected = 0
        self._embedding_last_resolution: Dict[str, Any] = {"status": "not_run"}
        self._visual_cache: OrderedDict[str, tuple[float, Dict[str, Any]]] = OrderedDict()
        self._visual_cache_hits = 0
        self._visual_cache_misses = 0
        self._qnn_cooldown_until = 0.0
        self._qnn_cooldown_model = ""
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
            self._consume_completed_locked()
            current = dict(self._latest)
            current["enabled"] = self._enabled()
            if not current.get("updated_at"):
                current["status"] = "waiting" if self._enabled() else "disabled"
            current["model"] = str(self._config.get("BODY_LLM_MODEL") or "")
            current["embedding_model"] = self._embedding_model()
            current["embedding_provider"] = self._embedding_provider()
            current["local_embedding_available"] = importlib.util.find_spec("fastembed") is not None
            current["embedding"] = {
                "requests": self._embedding_requests,
                "accepted": self._embedding_accepted,
                "rejected": self._embedding_rejected,
                "cache_entries": len(self._embedding_cache),
                "last_resolution": dict(self._embedding_last_resolution),
            }
            current["in_flight"] = bool(self._future and not self._future.done())
            current["visual_cache"] = {
                "hits": self._visual_cache_hits,
                "misses": self._visual_cache_misses,
                "entries": len(self._visual_cache),
            }
            current["provider_cooldown_seconds"] = round(
                max(0.0, self._qnn_cooldown_until - time.monotonic()), 1
            )
            current["effective_interval"] = round(float(self._last_effective_interval), 3)
            current["last_provider_latency_seconds"] = round(self._last_provider_latency_s, 3)
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

    def _consume_completed_locked(self) -> None:
        if self._future is None or not self._future.done():
            return
        try:
            self._latest = dict(self._future.result())
        except Exception as exc:
            self._latest = self._error(str(exc))
        self._last_provider_latency_s = max(
            0.0, self._number(self._latest.get("latency_ms")) / 1000.0
        )
        self._future = None

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
        configured = str(
            self._config.get("BODY_LLM_EMBEDDING_MODEL")
            or self._config.get("QUALITY_EMBED_MODEL")
            or ""
        ).strip()
        if self._embedding_provider() == "local_fastembed" and (
            not configured or "nomic-embed-text-v1.5" in configured.lower()
        ):
            return LOCAL_EMBEDDING_MODEL
        return configured

    def _embedding_provider(self) -> str:
        provider = str(self._config.get("BODY_LLM_EMBEDDING_PROVIDER") or "openai").strip().lower()
        return provider if provider in {"openai", "local_fastembed"} else "openai"

    def _embed(self, texts: list[str], *, model: str, timeout: float, kind: str) -> list[list[float]]:
        """Run an embedding batch through the selected remote or local provider."""
        provider = self._embedding_provider()
        if provider == "local_fastembed":
            if not importlib.util.find_spec("fastembed"):
                raise RuntimeError("FastEmbed is not installed in the Body Python environment")
            with self._lock:
                if self._local_embedding_engine is None or self._local_embedding_engine_model != model:
                    from fastembed import TextEmbedding

                    cache_dir = Path(__file__).resolve().parents[2] / "data" / "body" / "embedding_models"
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(
                        "[BodyEmbeddings] loading local provider=fastembed model=%s cache=%s threads=2",
                        model, cache_dir,
                    )
                    self._local_embedding_engine = TextEmbedding(
                        model_name=model, cache_dir=str(cache_dir), threads=2,
                    )
                    self._local_embedding_engine_model = model
            logger.info(
                "[BodyEmbeddings] request provider=fastembed model=%s kind=%s inputs=%d",
                model, kind, len(texts),
            )
            with self._lock:
                rows = list(self._local_embedding_engine.embed(texts, batch_size=32))
            vectors = [[float(value) for value in row] for row in rows]
            logger.info(
                "[BodyEmbeddings] response provider=fastembed model=%s kind=%s vectors=%d dimensions=%s",
                model, kind, len(vectors), len(vectors[0]) if vectors else 0,
            )
            return vectors

        url = f"{self._base_url()}/embeddings"
        logger.info(
            "[BodyEmbeddings] request provider=openai model=%s endpoint=%s kind=%s inputs=%d",
            model, url, kind, len(texts),
        )
        request = Request(
            url,
            data=json.dumps({"model": model, "input": texts}).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rows = sorted(payload.get("data") or [], key=lambda row: int(row.get("index", 0)))
        vectors = [row.get("embedding") for row in rows if isinstance(row, dict)]
        logger.info(
            "[BodyEmbeddings] response provider=openai model=%s kind=%s vectors=%d",
            model, kind, len(vectors),
        )
        return vectors

    def _embedding_threshold(self) -> float:
        try:
            return max(0.0, min(1.0, float(
                self._config.get("BODY_LLM_EMBEDDING_THRESHOLD", 0.55) or 0.55
            )))
        except (TypeError, ValueError):
            return 0.55

    def _semantic_reference_resolver(self, values: list[Any], known: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """Resolve only unknown labels through one bounded embedding batch.

        Exact ids, labels and canonical categories remain authoritative. This
        fallback handles genuine vocabulary variation while keeping the Body's
        measured entities as the only possible targets.
        """
        model = self._embedding_model()
        provider = self._embedding_provider()
        nomic_v15 = provider == "openai" and "nomic-embed-text-v1.5" in model.lower()
        unknown = []
        for value in values:
            key = " ".join(re.sub(r"[_-]+", " ", str(value or "").lower()).split())
            if key and key not in unknown:
                unknown.append(key)
        if not model:
            logger.info("[BodyEmbeddings] skipped reason=model_not_configured")
            return {}
        if not unknown or not known:
            logger.info(
                "[BodyEmbeddings] skipped reason=%s queries=%d scene_objects=%d",
                "no_unknown_labels" if not unknown else "no_scene_objects", len(unknown), len(known),
            )
            return {}
        candidates = []
        candidate_ids = []
        for object_id, item in known.items():
            text = str(item.get("label") or canonical_category(object_id) or object_id).strip()
            if nomic_v15:
                text = f"search_document: {text}"
            candidates.append(text)
            candidate_ids.append(object_id)
        cache_scope = self._base_url() if provider == "openai" else "local"
        cache_key = f"{provider}::{cache_scope}::{model}::{tuple(candidates)}"
        try:
            timeout = min(8.0, max(1.0, float(self._config.get("BODY_LLM_EMBEDDING_TIMEOUT", 4.0) or 4.0)))
        except (TypeError, ValueError):
            timeout = 4.0
        try:
            with self._lock:
                missing = [text for text in candidates if f"{cache_key}::{text}" not in self._embedding_cache]
            if missing:
                with self._lock:
                    self._embedding_requests += 1
                vectors = self._embed(missing, model=model, timeout=timeout, kind="candidates")
                with self._lock:
                    for text, vector in zip(missing, vectors):
                        if isinstance(vector, (list, tuple)) and vector:
                            self._embedding_cache[f"{cache_key}::{text}"] = [float(v) for v in vector]
            usable_candidates = []
            with self._lock:
                for object_id, text in zip(candidate_ids, candidates):
                    vector = self._embedding_cache.get(f"{cache_key}::{text}")
                    if vector:
                        usable_candidates.append((object_id, text, vector))
            if not usable_candidates:
                raise ValueError("embedding provider returned no usable vectors for scene objects")
            with self._lock:
                self._embedding_requests += 1
            query_texts = [f"search_query: {value}" for value in unknown] if nomic_v15 else unknown
            query_vectors = self._embed(query_texts, model=model, timeout=timeout, kind="queries")
            resolved: Dict[str, str] = {}
            threshold = self._embedding_threshold()
            for value, vector in zip(unknown, query_vectors):
                if not isinstance(vector, list) or not vector:
                    logger.info(
                        "[BodyEmbeddings] rejected label=%r reason=missing_query_vector",
                        value,
                    )
                    continue
                scores = []
                for object_id, _text, candidate_vector in usable_candidates:
                    scores.append((
                        _cosine([float(v) for v in vector], candidate_vector), object_id
                    ))
                if scores:
                    ranked = sorted(scores, reverse=True)
                    score, object_id = ranked[0]
                    runner_up_score = ranked[1][0] if len(ranked) > 1 else 0.0
                    margin = score - runner_up_score
                    if score >= threshold and margin >= 0.04:
                        resolved[value] = object_id
                        with self._lock:
                            self._embedding_accepted += 1
                            self._embedding_last_resolution = {
                                "status": "accepted", "label": value, "target": object_id,
                                "score": round(score, 4), "threshold": threshold,
                                "runner_up_score": round(runner_up_score, 4), "margin": round(margin, 4),
                            }
                        logger.info(
                            "[BodyEmbeddings] accepted label=%r target=%s score=%.3f threshold=%.3f runner_up=%.3f margin=%.3f",
                            value, object_id, score, threshold, runner_up_score, margin,
                        )
                    else:
                        reason = "below_threshold" if score < threshold else "ambiguous_candidates"
                        with self._lock:
                            self._embedding_rejected += 1
                            self._embedding_last_resolution = {
                                "status": "rejected", "label": value, "target": object_id,
                                "score": round(score, 4), "threshold": threshold,
                                "runner_up_score": round(runner_up_score, 4),
                                "margin": round(margin, 4), "reason": reason,
                            }
                        logger.info(
                            "[BodyEmbeddings] rejected label=%r target=%s score=%.3f threshold=%.3f runner_up=%.3f margin=%.3f reason=%s",
                            value, object_id, score, threshold, runner_up_score, margin, reason,
                        )
                else:
                    with self._lock:
                        self._embedding_rejected += 1
                        self._embedding_last_resolution = {
                            "status": "rejected", "label": value,
                            "reason": "no_candidate_score", "threshold": threshold,
                        }
                    logger.info(
                        "[BodyEmbeddings] rejected label=%r score=unavailable reason=no_candidate_score",
                        value,
                    )
            return resolved
        except Exception as exc:
            with self._lock:
                self._embedding_last_resolution = {
                    "status": "unavailable", "model": model, "error": str(exc)[:240],
                }
            logger.warning(
                "[BodyEmbeddings] unavailable model=%s endpoint=%s error=%s",
                model, "local:fastembed" if provider == "local_fastembed" else f"{self._base_url()}/embeddings", str(exc)[:240],
            )
            return {}

    def test_embedding_resolution(
        self, label: str, known: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Exercise the configured embedding endpoint against current scene objects."""
        normalized = " ".join(re.sub(r"[_-]+", " ", str(label or "").lower()).split())[:160]
        if not normalized:
            return {"ok": False, "status": "invalid_input", "error": "Enter a label to test."}
        if not known:
            return {"ok": False, "status": "no_scene_objects", "error": "The latest Body scene has no objects."}
        matches = self._semantic_reference_resolver([normalized], known)
        with self._lock:
            detail = dict(self._embedding_last_resolution)
        detail.update({
            "ok": detail.get("status") in {"accepted", "rejected"},
            "model": self._embedding_model(),
            "provider": self._embedding_provider(),
            "scene_objects": [
                {"id": object_id, "label": str(item.get("label") or item.get("kind") or object_id)}
                for object_id, item in known.items()
            ],
            "matched_object_id": matches.get(normalized),
        })
        return detail

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
            self._consume_completed_locked()
            if self._future is not None and not self._future.done():
                return
            interval, reason = self._interval_for_packet(packet)
            provider_interval = min(60.0, self._last_provider_latency_s * 1.5)
            if provider_interval > interval:
                interval, reason = provider_interval, "provider-limited"
            self._last_effective_interval = interval
            self._last_cadence_reason = reason
            if now - self._last_submit < interval:
                return
            self._last_submit = now
            self._future = self._executor.submit(self._interpret_adaptive, packet)

    @staticmethod
    def _radar_focus_ready(packet: Dict[str, Any]) -> bool:
        modalities = packet.get("modalities") or {}
        camera = modalities.get("camera") or {}
        radar = modalities.get("mmwave_radar") or {}
        calibration = camera.get("calibration") or {}
        if not (camera.get("image_base64") or camera.get("image_url")):
            return False
        if not (calibration.get("fov_deg") or camera.get("fov_deg")):
            return False
        if (camera.get("source") != "virtual_camera"
                and calibration.get("radar_alignment_verified") is not True):
            return False
        if str(radar.get("coordinate_frame") or radar.get("frame") or "").lower() not in {
            "world", "map", "local_map", "body", "base_link", "base_footprint"
        }:
            return False
        if not any(isinstance(item, dict) and BodySceneInterpreter._number(item.get("confidence")) >= 0.6
                   for item in radar.get("targets") or []):
            return False
        camera_stamp = BodySceneInterpreter._number(camera.get("timestamp"))
        radar_stamp = BodySceneInterpreter._number(radar.get("timestamp"))
        if camera_stamp and radar_stamp:
            return abs(camera_stamp - radar_stamp) <= 0.2
        return bool(camera.get("frame_id") and camera.get("frame_id") == radar.get("frame_id"))

    def _interpret_adaptive(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        if not self._config.get("BODY_LLM_RADAR_FOCUS_ENABLED", True) or not self._radar_focus_ready(packet):
            return self._interpret(packet)
        focused = self._interpret(packet, visual_options={"include_sensor_context": True,
                                                          "mmwave_focus": True})
        strategy = (focused.get("visual_input") or {}).get("strategy")
        if strategy != "radar_attention_strip":
            return focused
        grounding = ((focused.get("semantic_scene") or {}).get("grounding") or {})
        if focused.get("status") != "interpreted" or grounding.get("accepted_for_context") is True:
            return focused
        logger.info("[BodyVLM] radar focus ungrounded; retrying full frame=%s", packet.get("frame_id"))
        fallback = self._interpret(packet)
        fallback["radar_focus_fallback"] = True
        fallback["radar_focus_latency_ms"] = focused.get("latency_ms")
        fallback["latency_ms"] = round(
            self._number(focused.get("latency_ms")) + self._number(fallback.get("latency_ms")), 1
        )
        return fallback

    def interpret_now(
        self, packet: Dict[str, Any], *, visual_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run one explicit diagnostic interpretation and publish its result.

        The Body VLM test is a user-triggered diagnostic, so it must be visible
        through the same status endpoint as the background interpreter.  This
        also keeps the UI from showing an old ``No interpretation yet`` value
        after a successful test.
        """
        result = self._interpret(packet, visual_options=visual_options)
        with self._lock:
            self._latest = dict(result)
        return result

    def _error(self, message: str) -> Dict[str, Any]:
        error = {
            "status": "error",
            "error": str(message)[:240],
            "updated_at": time.time(),
            "model": str(self._config.get("BODY_LLM_MODEL") or ""),
        }
        if "-100201" in message or "model loading failed" in message.lower():
            error["diagnosis"] = {
                "code": "qnn_model_load_failed",
                "stage": "htp_graph_initialization",
                "payload_related": False,
                "summary": "GenieX/QAIRT could not initialize the compiled model graph. This happens before scene interpretation; shrinking the prompt or camera image is unlikely to fix it.",
                "checks": [
                    "FastRPC shared-buffer/CMA capacity, device-tree reservation, and cDSP mapping/address-space limits",
                    "GenieX, QAIRT and VENTUNO Q firmware compatibility",
                    "whether another QNN graph holds HTP shared buffers",
                ],
            }
        return error

    def _visual_cache_key(self, image: str, camera: Dict[str, Any], model: str) -> str:
        calibration = camera.get("calibration") if isinstance(camera.get("calibration"), dict) else {}
        identity = {
            "image_sha256": hashlib.sha256(image.encode("utf-8")).hexdigest(),
            "model": model,
            "endpoint": self._base_url(),
            "profile": camera.get("camera_profile"),
            "calibration": calibration,
            "prompt": "visual-scene-v2",
        }
        return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def _visual_cache_get(self, key: str) -> Optional[Dict[str, Any]]:
        now = time.monotonic()
        with self._lock:
            cached = self._visual_cache.get(key)
            if cached is None:
                self._visual_cache_misses += 1
                return None
            expires_at, value = cached
            if expires_at <= now:
                del self._visual_cache[key]
                self._visual_cache_misses += 1
                return None
            self._visual_cache.move_to_end(key)
            self._visual_cache_hits += 1
            return json.loads(json.dumps(value))

    def _visual_cache_put(self, key: str, value: Dict[str, Any]) -> None:
        with self._lock:
            self._visual_cache[key] = (time.monotonic() + 300.0, json.loads(json.dumps(value)))
            self._visual_cache.move_to_end(key)
            while len(self._visual_cache) > 24:
                self._visual_cache.popitem(last=False)

    @staticmethod
    def _resize_visual_input(image: str, camera: Dict[str, Any], max_width: int) -> tuple[str, Dict[str, Any]]:
        """Downscale only the VLM copy; retain the original camera frame elsewhere."""
        metadata = dict(camera)
        if not image or image.startswith("http"):
            return image, metadata
        prefix = ""
        encoded = image
        if image.startswith("data:"):
            prefix, separator, encoded = image.partition(",")
            if not separator:
                return image, metadata
            prefix += ","
        try:
            declared_width = int(metadata.get("width") or 0)
            declared_height = int(metadata.get("height") or 0)
        except (TypeError, ValueError):
            declared_width = declared_height = 0
        if declared_width and declared_width <= max_width:
            metadata.update({
                "original_width": declared_width,
                "original_height": declared_height,
                "analysis_width": declared_width,
                "analysis_height": declared_height,
            })
            return image, metadata
        try:
            import cv2
            import numpy as np

            raw = base64.b64decode(encoded, validate=False)
            frame = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                return image, metadata
            height, width = frame.shape[:2]
            metadata["original_width"] = int(width)
            metadata["original_height"] = int(height)
            if width <= max_width:
                metadata["analysis_width"] = int(width)
                metadata["analysis_height"] = int(height)
                return image, metadata
            resized_height = max(1, round(height * max_width / width))
            resized = cv2.resize(frame, (max_width, resized_height), interpolation=cv2.INTER_AREA)
            ok, jpeg = cv2.imencode(".jpg", resized, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
            if not ok:
                return image, metadata
            metadata["analysis_width"] = int(max_width)
            metadata["analysis_height"] = int(resized_height)
            metadata["image_resized_for_vlm"] = True
            return prefix + base64.b64encode(jpeg.tobytes()).decode("ascii"), metadata
        except Exception as exc:
            logger.warning("[BodyVLM] analysis image resize skipped: %s", str(exc)[:160])
            return image, metadata

    @staticmethod
    def _mmwave_roi_crops(
        image: str, camera: Dict[str, Any], packet: Dict[str, Any], *, max_rois: int = 2,
    ) -> tuple[list[tuple[str, Dict[str, Any]]], list[Dict[str, Any]]]:
        """Make conservative, lower-field crops around radar-projected bearings.

        The full frame remains in the request as global context. Radar IDs and
        classifications are intentionally excluded from the descriptors sent
        to the VLM: radar selects where to inspect, not what the object is.
        """
        if not image or image.startswith("http"):
            return [], []
        raw_radar = ((packet.get("modalities") or {}).get("mmwave_radar") or {})
        coordinate_frame = str(raw_radar.get("coordinate_frame") or raw_radar.get("frame") or "").lower()
        body = packet.get("body") if isinstance(packet.get("body"), dict) else {}
        body_frame = str(body.get("coordinate_frame") or "").lower()
        frame = coordinate_frame or body_frame
        if frame in {"map", "world", "local_map"} and not isinstance(body.get("position"), (list, tuple)):
            return [], []
        if frame not in {"map", "world", "local_map", "body", "base_link", "base_footprint"}:
            return [], []
        encoded = image.partition(",")[2] if image.startswith("data:") else image
        if image.startswith("data:") and "," not in image:
            return [], []
        try:
            import cv2
            import numpy as np

            raw = base64.b64decode(encoded, validate=False)
            frame_image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame_image is None:
                return [], []
            height, width = frame_image.shape[:2]
            calibration = camera.get("calibration") if isinstance(camera.get("calibration"), dict) else {}
            fov = float(calibration.get("fov_deg") or camera.get("fov_deg") or 90.0)
            fov = max(20.0, min(170.0, fov))
            pose = body.get("position") or [0.0, 0.0, 0.0]
            bx, by = float(pose[0]), float(pose[1])
            yaw = float(body.get("orientation") or 0.0)
            camera_yaw = math.radians(float(calibration.get("yaw_offset_deg") or 0.0))
            candidates = []
            for target in raw_radar.get("targets") or []:
                if not isinstance(target, dict):
                    continue
                try:
                    position = target.get("position_m") or target.get("position")
                    tx, ty = float(position[0]), float(position[1])
                    if frame in {"map", "world", "local_map"}:
                        dx, dy = tx - bx, ty - by
                        bearing = math.atan2(dy, dx) - yaw - camera_yaw
                        distance = math.hypot(dx, dy)
                    else:
                        bearing = math.atan2(ty, tx) - camera_yaw
                        distance = math.hypot(tx, ty)
                    bearing = math.atan2(math.sin(bearing), math.cos(bearing))
                    confidence = max(0.0, min(1.0, float(target.get("confidence", 0.5))))
                except (IndexError, TypeError, ValueError):
                    continue
                if distance < 0.15 or distance > float(calibration.get("far_m") or 12.0):
                    continue
                if abs(bearing) > math.radians(fov / 2.0):
                    continue
                candidates.append((confidence, distance, bearing))
            candidates.sort(key=lambda item: (-item[0], item[1]))
            crops = []
            descriptors = []
            used_ranges: list[tuple[int, int]] = []
            half_fov = math.radians(fov) / 2.0
            for confidence, distance, bearing in candidates:
                if len(crops) >= max(0, min(2, int(max_rois))):
                    break
                center_x = int(round(width * (0.5 + (bearing / half_fov) * 0.46)))
                # A 12-degree minimum angular margin absorbs radar/camera
                # extrinsic error; low-confidence detections get a wider crop.
                half_angle = min(32.0, 12.0 + (1.0 - confidence) * 12.0)
                half_px = max(int(width * 0.125), int(round(width * 0.46 * half_angle / (fov / 2.0))))
                x0, x1 = max(0, center_x - half_px), min(width, center_x + half_px)
                if x1 - x0 < width * 0.20:
                    extra = int(width * 0.20 - (x1 - x0)) // 2 + 1
                    x0, x1 = max(0, x0 - extra), min(width, x1 + extra)
                if any(max(x0, left) < min(x1, right) for left, right in used_ranges):
                    continue
                # Floor-level robot cameras see actionable objects below the
                # horizon. Keep a generous vertical band because radar has no
                # object-height measurement.
                y0, y1 = int(height * 0.38), int(height * 0.98)
                crop = frame_image[y0:y1, x0:x1]
                ok, jpeg = cv2.imencode(".jpg", crop, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
                if not ok:
                    continue
                image_url = "data:image/jpeg;base64," + base64.b64encode(jpeg.tobytes()).decode("ascii")
                descriptor = {
                    "x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0,
                    "normalized": [round(x0 / width, 4), round(y0 / height, 4),
                                   round((x1 - x0) / width, 4), round((y1 - y0) / height, 4)],
                    "bearing_deg": round(math.degrees(bearing), 1),
                    "range_m": round(distance, 2), "confidence": round(confidence, 2),
                }
                crops.append((image_url, descriptor))
                descriptors.append(descriptor)
                used_ranges.append((x0, x1))
            return crops, descriptors
        except Exception as exc:
            logger.warning("[BodyVLM] mmWave ROI skipped: %s", str(exc)[:160])
            return [], []

    @staticmethod
    def _mmwave_focus_strip(
        image: str, crop: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """Keep scene context and one radar region in a single, small image."""
        try:
            import cv2
            import numpy as np

            def decode(value: str):
                encoded = value.partition(",")[2] if value.startswith("data:") else value
                return cv2.imdecode(np.frombuffer(base64.b64decode(encoded), dtype=np.uint8),
                                    cv2.IMREAD_COLOR)

            overview, detail = decode(image), decode(crop)
            if overview is None or detail is None:
                return None, None
            canvas = np.full((240, 640, 3), (20, 30, 34), dtype=np.uint8)
            for index, (label, source) in enumerate((("SCENE", overview), ("RADAR FOCUS", detail))):
                x0 = index * 320
                cv2.putText(canvas, label, (x0 + 8, 18), cv2.FONT_HERSHEY_SIMPLEX,
                            0.43, (206, 230, 225), 1, cv2.LINE_AA)
                scale = min(308 / source.shape[1], 210 / source.shape[0])
                resized = cv2.resize(source, (max(1, round(source.shape[1] * scale)),
                                              max(1, round(source.shape[0] * scale))),
                                     interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
                px = x0 + (320 - resized.shape[1]) // 2
                py = 24 + (210 - resized.shape[0]) // 2
                canvas[py:py + resized.shape[0], px:px + resized.shape[1]] = resized
            ok, encoded = cv2.imencode(".jpg", canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
            if not ok:
                return None, None
            preview = base64.b64encode(encoded.tobytes()).decode("ascii")
            return "data:image/jpeg;base64," + preview, preview
        except Exception as exc:
            logger.warning("[BodyVLM] radar focus strip skipped: %s", str(exc)[:160])
            return None, None

    @staticmethod
    def _mmwave_roi_mosaic(
        image: str, crops: list[tuple[str, Dict[str, Any]]],
    ) -> tuple[Optional[str], Optional[str]]:
        """Pack one overview and up to two crops into one fixed-size vision image."""
        try:
            import cv2
            import numpy as np

            def decode(value: str):
                encoded = value.partition(",")[2] if value.startswith("data:") else value
                return cv2.imdecode(np.frombuffer(base64.b64decode(encoded, validate=False), dtype=np.uint8),
                                    cv2.IMREAD_COLOR)

            source = decode(image)
            if source is None:
                return None, None
            tile_w, tile_h, header_h = 320, 240, 26
            canvas = np.full((tile_h * 2, tile_w * 2, 3), (20, 30, 34), dtype=np.uint8)

            def place(tile_x: int, tile_y: int, title: str, content, annotation: str = "") -> None:
                x0, y0 = tile_x * tile_w, tile_y * tile_h
                cv2.rectangle(canvas, (x0, y0), (x0 + tile_w - 1, y0 + tile_h - 1), (83, 105, 110), 1)
                cv2.rectangle(canvas, (x0 + 1, y0 + 1), (x0 + tile_w - 2, y0 + header_h), (31, 53, 57), -1)
                cv2.putText(canvas, title[:42], (x0 + 8, y0 + 18), cv2.FONT_HERSHEY_SIMPLEX,
                            0.42, (206, 230, 225), 1, cv2.LINE_AA)
                if content is not None:
                    available_w, available_h = tile_w - 12, tile_h - header_h - 8
                    scale = min(available_w / content.shape[1], available_h / content.shape[0])
                    resized = cv2.resize(content, (max(1, int(content.shape[1] * scale)),
                                                  max(1, int(content.shape[0] * scale))),
                                         interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
                    px = x0 + (tile_w - resized.shape[1]) // 2
                    py = y0 + header_h + (available_h - resized.shape[0]) // 2
                    canvas[py:py + resized.shape[0], px:px + resized.shape[1]] = resized
                if annotation:
                    cv2.putText(canvas, annotation[:44], (x0 + 8, y0 + tile_h - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.36, (160, 206, 200), 1, cv2.LINE_AA)

            place(0, 0, "GLOBAL VIEW", source)
            for index in range(2):
                if index < len(crops):
                    crop_image = decode(crops[index][0])
                    box = crops[index][1]
                    place(1, index, f"RADAR ROI {index + 1}", crop_image,
                          f"bearing {box['bearing_deg']} deg · range {box['range_m']} m")
                else:
                    place(1, index, "RADAR ROI", None, "no additional region selected")
            note = np.full((tile_h - header_h - 8, tile_w - 12, 3), (20, 30, 34), dtype=np.uint8)
            cv2.putText(note, "Radar guides attention only;", (8, 40), cv2.FONT_HERSHEY_SIMPLEX,
                        0.43, (206, 230, 225), 1, cv2.LINE_AA)
            cv2.putText(note, "it does not identify objects.", (8, 70), cv2.FONT_HERSHEY_SIMPLEX,
                        0.43, (206, 230, 225), 1, cv2.LINE_AA)
            place(0, 1, "SENSOR CUE", note)
            ok, encoded = cv2.imencode(".jpg", canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
            if not ok:
                return None, None
            preview = base64.b64encode(encoded.tobytes()).decode("ascii")
            return "data:image/jpeg;base64," + preview, preview
        except Exception as exc:
            logger.warning("[BodyVLM] mmWave attention mosaic skipped: %s", str(exc)[:160])
            return None, None

    @staticmethod
    def _normalize_interpretation_schema(interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize common VLM JSON shapes without constraining its vocabulary."""
        normalized = dict(interpretation)

        def get_text(item: Dict[str, Any], names: tuple[str, ...]) -> str:
            for name in names:
                value = item.get(name)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            return ""

        def descriptive_text(item: Dict[str, Any]) -> str:
            value = get_text(item, ("description", "visual_description", "appearance", "caption"))
            if value:
                return value
            for key, raw in item.items():
                if (str(key).lower().endswith("_description")
                        and isinstance(raw, str) and raw.strip()):
                    return raw.strip()
            return ""

        if not get_text(normalized, ("scene_summary", "summary")):
            caption = get_text(normalized, ("scene_description", "caption", "overview"))
            if caption:
                normalized["scene_summary"] = caption

        descriptions = normalized.get("object_descriptions")
        if not descriptions:
            for key in ("objects", "entities", "detections", "items"):
                candidate = normalized.get(key)
                if isinstance(candidate, (list, tuple, dict)) and candidate:
                    descriptions = candidate
                    break

        if isinstance(descriptions, dict):
            descriptions = [
                ({"id": key, **value} if isinstance(value, dict) else {"id": key, "label": value})
                for key, value in descriptions.items()
            ]
        elif not isinstance(descriptions, (list, tuple)):
            descriptions = []

        canonical_descriptions = []
        for value in descriptions:
            if isinstance(value, dict):
                item = dict(value)
                label = get_text(item, ("label", "name", "class", "category", "object"))
                description = descriptive_text(item)
                if label and not item.get("label"):
                    item["label"] = label
                if description and not item.get("description"):
                    item["description"] = description
                if item.get("confidence") is None:
                    item["confidence"] = item.get("score", item.get("probability"))
                canonical_descriptions.append(item)
            elif isinstance(value, str) and value.strip():
                canonical_descriptions.append({"label": value.strip()})

        root_label = get_text(normalized, ("label", "name", "class", "category", "object"))
        root_description = descriptive_text(normalized)
        existing_labels = {
            get_text(item, ("label", "name", "class", "category", "object")).casefold()
            for item in canonical_descriptions if isinstance(item, dict)
        }
        if (root_label or root_description) and root_label.casefold() not in existing_labels:
            canonical_descriptions.append({
                "label": root_label or root_description[:80],
                "description": root_description,
                "confidence": normalized.get("confidence", normalized.get("score")),
            })
        if canonical_descriptions:
            normalized["object_descriptions"] = canonical_descriptions
        return normalized

    @staticmethod
    def _ground_interpretation(interpretation: Dict[str, Any], packet: Dict[str, Any], label_resolver=None) -> Dict[str, Any]:
        """Turn free-form LLM semantics into a Body-owned scene model.

        The LLM may name and describe only entities present in the measured
        packet. Positions, ranges and collision geometry always come from the
        sensor projection and are copied here without modification.
        """
        interpretation = BodySceneInterpreter._normalize_interpretation_schema(interpretation)
        objects = [item for item in packet.get("objects") or [] if isinstance(item, dict)]
        known = {str(item.get("id")): item for item in objects if item.get("id")}
        def normalize_label(value: Any) -> str:
            return " ".join(re.sub(r"[_-]+", " ", str(value or "").lower()).split())

        labels = {normalize_label(item.get("label") or item_id): item_id for item_id, item in known.items()}
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
            raw_reference = str(value or "").strip().lower()
            if raw_reference in known:
                return raw_reference
            reference = normalize_label(value)
            if reference in labels:
                return labels[reference]
            resolved = normalized_labels.get(canonical_category(value), "")
            if not resolved:
                key = normalize_label(value)
                if key:
                    unresolved.append(key)
                    resolved = semantic_matches.get(key, "")
            return resolved

        def image_region(value: Any) -> Optional[Dict[str, float]]:
            if not isinstance(value, dict):
                return None
            try:
                x, y = float(value.get("x")), float(value.get("y"))
                width, height = float(value.get("width")), float(value.get("height"))
            except (TypeError, ValueError):
                return None
            if (not all(math.isfinite(v) for v in (x, y, width, height))
                    or width <= 0 or height <= 0 or x < 0 or y < 0
                    or x + width > 1 or y + height > 1):
                return None
            return {"x": round(x, 5), "y": round(y, 5),
                    "width": round(width, 5), "height": round(height, 5)}

        def attributes(value: Any) -> Dict[str, Any]:
            if not isinstance(value, dict):
                return {}
            safe: Dict[str, Any] = {}
            for key, raw in list(value.items())[:16]:
                name = str(key).strip().lower()[:40]
                if not name or name in {"position", "coordinates", "x", "y", "z", "center", "size_m"}:
                    continue
                if isinstance(raw, (str, bool, int, float)):
                    if isinstance(raw, float) and not math.isfinite(raw):
                        continue
                    safe[name] = str(raw)[:100] if isinstance(raw, str) else raw
            return safe

        if label_resolver:
            raw_values = list(as_items(interpretation.get("primary_objects")))
            raw_values.extend(
                item.get("label") or item.get("id")
                for item in as_items(interpretation.get("object_descriptions"))
                if isinstance(item, dict)
            )
            matches = label_resolver(raw_values, known) or {}
            semantic_matches.update({normalize_label(key): value for key, value in matches.items()})

        primary = [resolve_reference(value) for value in as_items(interpretation.get("primary_objects"))]
        primary = [value for value in primary if value]
        descriptions = {}
        raw_descriptions = interpretation.get("object_descriptions") or []
        if isinstance(raw_descriptions, dict):
            raw_descriptions = [dict(value, id=key) for key, value in raw_descriptions.items() if isinstance(value, dict)]
        elif not isinstance(raw_descriptions, (list, tuple)):
            raw_descriptions = []
        for item in raw_descriptions:
            if not isinstance(item, dict):
                continue
            object_id = resolve_reference(item.get("label") or item.get("id"))
            if object_id not in known:
                continue
            descriptions[object_id] = {
                "semantic_label": normalize_label(item.get("label") or item.get("id"))[:120],
                "description": str(item.get("description") or "")[:240],
                "role": str(item.get("role") or known[object_id].get("kind") or "object")[:80],
                "affordances": [str(value)[:50] for value in as_items(item.get("affordances"))][:8],
                "attributes": attributes(item.get("attributes")),
                "image_region": image_region(item.get("image_region")),
                "confidence": _bounded_confidence(item.get("confidence")),
                "relations": [],
            }
            for relation in as_items(item.get("relations"))[:12]:
                if not isinstance(relation, dict):
                    continue
                target_id = resolve_reference(relation.get("target_id") or relation.get("target"))
                relation_type = str(relation.get("type") or "").strip()[:50]
                if target_id and target_id != object_id and relation_type:
                    descriptions[object_id]["relations"].append({
                        "type": relation_type, "target_id": target_id,
                    })
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
        raw_primary = as_items(interpretation.get("primary_objects"))
        primary_total = len([value for value in raw_primary if value])
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

    def _interpret(
        self, packet: Dict[str, Any], *, visual_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        call_started = time.monotonic()
        model = str(self._config.get("BODY_LLM_MODEL") or "").strip()
        if not model:
            return self._error("BODY_LLM_MODEL is not configured")
        with self._lock:
            cooldown = self._qnn_cooldown_until - time.monotonic()
            cooldown_model = self._qnn_cooldown_model
        if cooldown > 0 and cooldown_model == model:
            return self._error(
                f"GenieX QNN model loading failed recently; retry suppressed for {cooldown:.0f}s to avoid repeating the same HTP allocation failure"
            )
        # Keep the provider prompt compact.  The full perception frame is
        # still exposed through the Body API, but sending it here duplicates
        # the same LiDAR, projections and fusion data several times.  The
        # camera image is attached separately below as a vision part.
        prompt_packet = {
            key: packet.get(key)
            for key in ("timestamp", "frame_id", "contract", "source", "confidence")
            if key in packet
        }
        def compact_fields(value: Any, fields: tuple[str, ...]) -> Dict[str, Any]:
            if not isinstance(value, dict):
                return {}
            return {key: value[key] for key in fields if key in value and value[key] is not None}

        prompt_packet["body"] = compact_fields(
            packet.get("body"), ("position", "orientation", "posture", "coordinate_frame", "position_source")
        )
        if packet.get("visual_blind"):
            # Evaluation mode keeps simulator identities outside the prompt.
            prompt_packet.pop("objects", None)
            prompt_packet["visual_validation"] = (
                "Identify only objects visibly supported by the attached camera image. "
                "No LiDAR or radar evidence is available; do not infer metric distances, "
                "coordinates, or unseen objects. Use open-vocabulary descriptions."
                if packet.get("camera_only") else
                "Identify only objects visibly supported by the attached image and LiDAR. "
                "Use semantic names when appropriate; do not assume unseen objects."
            )
        else:
            prompt_packet["objects"] = [
                {key: item.get(key) for key in ("id", "label", "kind")}
                for item in (packet.get("objects") or [])[:5] if isinstance(item, dict)
            ]
        # The image is attached as a vision part below. Never duplicate its
        # Base64 bytes inside the JSON prompt; that doubles latency and token
        # transport for every Body interpretation.
        modalities = dict(packet.get("modalities") or {})
        camera_meta = dict(modalities.get("camera") or {})
        camera_image = camera_meta.pop("image_base64", None) or camera_meta.pop("image_url", None)
        visual_options = visual_options if isinstance(visual_options, dict) else {}
        visual_image_max_width = max(320, min(640, int(
            visual_options.get("image_max_width", self._config.get("BODY_LLM_VISUAL_IMAGE_MAX_WIDTH", 640)) or 640
        )))
        visual_input = {}
        if camera_image:
            camera_image, visual_input = self._resize_visual_input(
                str(camera_image), camera_meta, visual_image_max_width
            )
            camera_meta.update({key: value for key, value in visual_input.items() if key != "image_resized_for_vlm"})
        visual_input["max_width"] = visual_image_max_width
        camera_image_size = len(str(camera_image)) if camera_image else 0
        roi_crops: list[tuple[str, Dict[str, Any]]] = []
        roi_descriptors: list[Dict[str, Any]] = []
        focused_crop = bool(visual_options.get("mmwave_focus"))
        if (visual_options.get("mmwave_roi") or focused_crop) and camera_image:
            roi_crops, roi_descriptors = self._mmwave_roi_crops(
                str(camera_image), camera_meta, packet,
                max_rois=1 if focused_crop else int(visual_options.get("max_rois", 2) or 2),
            )
            visual_input["mmwave_roi_count"] = len(roi_crops)
            visual_input["mmwave_rois"] = roi_descriptors
            if roi_crops:
                if focused_crop:
                    strip, preview = self._mmwave_focus_strip(str(camera_image), roi_crops[0][0])
                    if strip:
                        camera_image = strip
                        camera_image_size = len(camera_image)
                        visual_input.update({"strategy": "radar_attention_strip", "image_count": 1,
                                             "preview_base64": preview})
                    else:
                        focused_crop = False
                        roi_crops, roi_descriptors = [], []
                        visual_input.update({"mmwave_roi_count": 0, "mmwave_rois": [],
                                             "strategy": "full_frame_fallback", "image_count": 1})
                else:
                    mosaic, preview = self._mmwave_roi_mosaic(str(camera_image), roi_crops)
                    if mosaic:
                        camera_image = mosaic
                        camera_image_size = len(camera_image)
                        visual_input.update({"strategy": "single_image_attention_mosaic", "image_count": 1,
                                             "global_context_width": 320, "preview_base64": preview})
                    else:
                        roi_crops, roi_descriptors = [], []
                        visual_input.update({"mmwave_roi_count": 0, "mmwave_rois": [],
                                             "strategy": "full_frame_fallback", "image_count": 1})
            elif focused_crop:
                visual_input.update({"strategy": "full_frame_fallback", "image_count": 1})
        depth_image = camera_meta.pop("depth_base64", None)
        camera_meta["image_attached"] = bool(camera_image)
        camera_meta["depth_attached"] = bool(depth_image)
        modalities = {
            "camera": compact_fields(
                camera_meta,
                ("camera_profile", "width", "height", "calibration", "image_attached", "depth_attached", "source"),
            )
        }
        lidar = dict(modalities.get("lidar") or {})
        raw_lidar = (packet.get("modalities") or {}).get("lidar") or {}
        points = [point for point in raw_lidar.get("points") or [] if isinstance(point, dict)]
        points.sort(key=lambda point: self._number(point.get("range_m"), float("inf")))
        point_fields = ("x", "y", "z", "range_m", "angle_deg", "object_id")
        compact_points = [
            {key: point[key] for key in point_fields if key in point}
            for point in points[:24]
        ]
        modalities["lidar"] = {
            **compact_fields(raw_lidar, ("frame_id", "timestamp", "source", "quality", "coordinate_frame", "frame", "unit", "native")),
            "points": compact_points,
            "points_truncated": max(0, len(points) - len(compact_points)),
        }
        raw_radar = (packet.get("modalities") or {}).get("mmwave_radar") or {}
        radar_targets = [item for item in raw_radar.get("targets") or [] if isinstance(item, dict)]
        modalities["mmwave_radar"] = {
            **compact_fields(raw_radar, ("frame_id", "timestamp", "source", "quality", "frame", "coordinate_frame")),
            "targets": [{key: item[key] for key in (
                "position_m", "velocity_mps", "radial_speed_mps", "confidence"
            ) if key in item} for item in radar_targets[:12]],
            "targets_truncated": max(0, len(radar_targets) - 12),
        }
        raw_motion = packet.get("motion")
        if isinstance(raw_motion, dict):
            prompt_packet["motion"] = compact_fields(
                raw_motion,
                ("speed", "relative_speed", "closing_speed", "angular_speed", "moving", "perception_risk", "minimum_clearance_m"),
            )
        raw_navigation = packet.get("navigation")
        if isinstance(raw_navigation, dict):
            prompt_packet["navigation"] = compact_fields(
                raw_navigation, ("task", "recommended", "reason", "recovery_mode", "mobile_obstacle")
            )
        if packet.get("visual_blind"):
            # Do not leak simulator identities through derived projections.
            modalities["lidar"]["points"] = [
                {key: value for key, value in point.items() if key != "object_id"}
                for point in modalities["lidar"]["points"]
            ]
            if not visual_options.get("include_sensor_context"):
                modalities["lidar"]["points"] = []
                modalities["mmwave_radar"]["targets"] = []
        prompt_packet["modalities"] = modalities
        prompt_packet["attention"] = {
            "policy": "near_actionable_and_hazardous",
            "focus_range_m": self._focus_range(),
            "max_detailed_objects": 5,
            "global_context": "summarize distant structure without enumerating uncertain objects",
            "uncertainty_rule": "use uncertain instead of inventing an object",
        }
        camera_view_note = self._camera_view_note(modalities.get("camera") or {})
        camera_only_prompt = bool(visual_options.get("camera_only") or packet.get("camera_only"))
        metric_evidence_prompt = (
            "No LiDAR or mmWave data is available; describe appearance from pixels only and do not infer metric range or position. "
            if camera_only_prompt else
            "Use mmWave targets only as metric motion evidence (position/velocity), never as proof of visual identity. "
        )
        association_prompt = (
            "Do not infer metric coordinates or object dimensions from image regions. "
            if camera_only_prompt else
            "For camera/LiDAR matches, describe only image-visible appearance and use the LiDAR packet solely to "
            "support proximity or obstacle relevance; do not invent an association when evidence is ambiguous. "
            "Do not classify floor grids, camera reticles, crosshairs, LiDAR rays, projected points, or reference "
            "markers as physical objects unless a separate object silhouette is visible in the camera image. "
        )
        prompt = (
            "Interpret this timestamped Body sensor packet. The packet contract is authoritative "
            "about timestamps and provenance. Return JSON only with keys: "
            "scene_summary (one concise global sentence), primary_objects (array of ids or semantic labels for "
            "near, actionable or hazardous objects only), object_descriptions (array of at most five "
            "near/actionable/hazardous objects with a required short open-vocabulary label, description, role, "
            "affordances and confidence 0..1; include id only when the packet provides a stable track ID; optional "
            "open-vocabulary scalar attributes, optional image_region {x,y,width,height} normalized to 0..1, and "
            "optional relations [{type,target_id}] referencing another observed object), environment (array of "
            "observed facts), possible_paths (array of objects with action and reason), "
            "movement_support (array of monitoring or recovery suggestions), uncertainty (array). "
            f"Prioritize objects within approximately {self._focus_range():.1f} metres of the Body, objects on the "
            "current path, and hazards. Do not enumerate distant objects unless they are necessary for navigation. "
            + metric_evidence_prompt +
            "Every concrete object named in scene_summary must also appear in object_descriptions with a short "
            "open-vocabulary label and a visual description; do not leave object_descriptions empty when the "
            "summary names a visible object. Use free-form labels grounded in the image, not a fixed category list. "
            "If navigation.task is present, identify its requested object in the image and set its role to goal; "
            "the task object remains relevant even when it is farther than the focus range. "
            + association_prompt +
            "A distant or ambiguous visual shape must go into uncertainty, not into primary_objects. "
            "Image regions describe pixels only; "
            + camera_view_note + " "
            "Use only observed data. Prefer native camera/LiDAR returns when quality says native; "
            "label derived projections as inferred. Do not invent objects, coordinates, or completion. "
            "This is advisory perception; never issue actuator commands.\n\n"
            + json.dumps(prompt_packet, ensure_ascii=False, separators=(",", ":"))
        )
        if focused_crop and roi_crops:
            task = str((packet.get("navigation") or {}).get("task") or "identify nearby objects")[:180]
            prompt = (
                "The attached robot camera image has the full scene on the left and one radar-selected "
                "detail on the right. Radar cannot identify objects. "
                "Describe objects only when visually supported; the detail may enlarge the task object. "
                "Return compact JSON with scene_summary and object_descriptions (at most 3 items, "
                "each with label, short visual description, role and confidence 0..1). "
                "Use role goal only if the requested object is visible. Do not infer distance, "
                "coordinates, identities or unseen objects. Use an empty array when uncertain. "
                "Task: " + task + ". Camera: " + self._camera_view_note(camera_meta) + "."
            )
        elif roi_crops:
            prompt += (
                "\nThe attached image is a 2x2 attention mosaic: top-left is the complete global scene; "
                "top-right and bottom-right are the first and second crops; bottom-left contains only "
                "sensor guidance text. Inspect each image region visually. Overlaid bearing/range text "
                "is metadata, not a scene object. Radar does not identify objects. Regions: "
                + json.dumps(roi_descriptors, separators=(",", ":"))
            )
        visual_only = bool(camera_image) and not bool(visual_options.get("include_sensor_context"))
        visual_max_objects = max(1, min(10, int(self._config.get("BODY_LLM_VISUAL_MAX_OBJECTS", 5) or 5)))
        visual_max_tokens = max(32, min(512, int(self._config.get("BODY_LLM_VISUAL_MAX_TOKENS", 128) or 128)))
        if visual_only:
            camera_context = compact_fields(
                camera_meta, ("camera_profile", "width", "height", "calibration", "source")
            )
            prompt = (
                "Identify up to " + str(visual_max_objects) + " salient objects clearly visible in this robot camera image. "
                "Return compact JSON only with scene_summary (one short sentence) and "
                "object_descriptions (up to " + str(visual_max_objects) + " objects, each with label, "
                "a brief visual description, and confidence 0..1). Do not add coordinates, "
                "distance, motion, free space, or path advice. Do not use simulator or sensor "
                "object lists. Use an empty array when uncertain; never invent an object. "
                "This is semantic perception only, not navigation or actuator control. "
                + self._camera_view_note(camera_context)
                + " Camera metadata: "
                + json.dumps(camera_context, ensure_ascii=False, separators=(",", ":"))
            )
        logger.info(
            "[BodyVLM] prompt mode=%s model=%s chars=%d estimated_tokens=%d context_window=%s image=%s image_chars=%d lidar_points_sent=%d lidar_points_available=%d",
            "image_only" if visual_only else "sensor_packet",
            model,
            len(prompt),
            max(1, len(prompt) // 4),
            self._config.get("BODY_LLM_CONTEXT_WINDOW", "unknown"),
            bool(camera_image),
            camera_image_size,
            0 if visual_only else len(compact_points),
            0 if visual_only else len(points),
        )
        user_content: Any = prompt
        camera = packet.get("modalities", {}).get("camera") if isinstance(packet.get("modalities"), dict) else None
        if isinstance(camera, dict):
            image = camera_image
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
        if roi_crops:
            logger.info(
                "[BodyVLM] mmWave ROI regions=%d frame=%s image_parts=1 boxes=%s",
                len(roi_crops), packet.get("frame_id"), json.dumps(roi_descriptors, separators=(",", ":")),
            )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are the local embodied-scene interpreter for a robot Body."},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
            "max_tokens": (min(192, max(96, int(self._config.get("BODY_LLM_MAX_TOKENS", 360) or 360)))
                           if focused_crop and roi_crops else visual_max_tokens if visual_only else min(
                2048, max(64, int(self._config.get("BODY_LLM_MAX_TOKENS", 360) or 360))
            )),
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
        def request_completion(attempt: str) -> Dict[str, Any]:
            request_data = json.dumps(payload).encode("utf-8")
            started = time.monotonic()
            logger.info(
                "[BodyVLM] request attempt=%s bytes=%d response_format=%s image=%s",
                attempt,
                len(request_data),
                (payload.get("response_format") or {}).get("type", "none"),
                isinstance(payload["messages"][1]["content"], list),
            )
            request = Request(
                f"{self._base_url()}/chat/completions",
                data=request_data, headers=headers, method="POST",
            )
            try:
                with urlopen(request, timeout=timeout) as response:
                    raw = response.read()
                logger.info(
                    "[BodyVLM] response attempt=%s status=200 latency_ms=%.1f response_bytes=%d",
                    attempt, (time.monotonic() - started) * 1000.0, len(raw),
                )
                return json.loads(raw.decode("utf-8"))
            except HTTPError as exc:
                logger.warning(
                    "[BodyVLM] response attempt=%s status=%d latency_ms=%.1f",
                    attempt, exc.code, (time.monotonic() - started) * 1000.0,
                )
                raise

        def describe_http_error(exc: HTTPError, attempt: str) -> str:
            try:
                detail = exc.read(1600).decode("utf-8", errors="replace").strip()
            except Exception:
                detail = ""
            finally:
                exc.close()
            detail = " ".join(detail.split())[:500]
            logger.warning(
                "[BodyVLM] provider rejected attempt=%s status=%d detail=%s",
                attempt,
                exc.code,
                detail or exc.reason,
            )
            return detail or str(exc.reason or "provider rejected request")

        visual_cache_key = (
            self._visual_cache_key(str(camera_image), camera_meta, model)
            if visual_only and not visual_options.get("bypass_cache") else ""
        )
        cached_interpretation = self._visual_cache_get(visual_cache_key) if visual_cache_key else None
        if cached_interpretation is not None:
            logger.info("[BodyVLM] visual cache hit model=%s frame=%s", model, packet.get("frame_id"))
            content = json.dumps(cached_interpretation, ensure_ascii=False)
            result = None
        else:
            logger.info("[BodyVLM] visual cache miss model=%s frame=%s", model, packet.get("frame_id"))
            try:
                result = request_completion("json+image")
            except HTTPError as exc:
            # LM Studio versions differ in JSON-schema support. First remove
            # that optional constraint, then fall back to text-only input for
            # instruct models that reject a vision content part with 400/422.
                if exc.code not in {400, 422}:
                    detail = describe_http_error(exc, "json+image")
                    if exc.code == 500 and ("-100201" in detail or "Model loading failed" in detail):
                        with self._lock:
                            self._qnn_cooldown_until = time.monotonic() + 60.0
                            self._qnn_cooldown_model = model
                    return self._error(f"VLM provider HTTP {exc.code}: {detail}")
                first_detail = describe_http_error(exc, "json+image")
                payload.pop("response_format", None)
                try:
                    result = request_completion("image-no-format")
                except HTTPError as retry_exc:
                    if retry_exc.code not in {400, 422} or not isinstance(user_content, list):
                        detail = describe_http_error(retry_exc, "image-no-format")
                        return self._error(f"VLM provider HTTP {retry_exc.code}: {detail}")
                    second_detail = describe_http_error(retry_exc, "image-no-format")
                    payload["messages"][1]["content"] = prompt
                    try:
                        result = request_completion("text-only-fallback")
                    except HTTPError as final_exc:
                        final_detail = describe_http_error(final_exc, "text-only-fallback")
                        def short(value: str) -> str:
                            return " ".join(value.split())[:48]

                        return self._error(
                            "Provider rejected Body request: "
                            f"JSON+image {exc.code} {short(first_detail)}; "
                            f"image {retry_exc.code} {short(second_detail)}; "
                            f"text {final_exc.code} {short(final_detail)}"
                        )
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
        if visual_cache_key and cached_interpretation is None:
            self._visual_cache_put(visual_cache_key, interpretation)
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
            "interpretation_mode": "image_only" if visual_only else "sensor_packet",
            "visual_cache_hit": cached_interpretation is not None,
            "latency_ms": round((time.monotonic() - call_started) * 1000.0, 1),
            "visual_input": visual_input if visual_only or roi_crops else None,
            "observed_at": packet.get("timestamp"),
            "updated_at": time.time(),
            "interpretation": interpretation,
            "semantic_scene": semantic_scene,
        }

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
