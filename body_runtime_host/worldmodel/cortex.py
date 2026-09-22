"""Artificial visual cortex — an *affordance encoder*, not a decoder.

Principle implemented here (from the embodied-cognition spec):

    The visual cortex is not a passive image decoder.  It encodes the world
    *around the body's action capabilities*: which objects are actionable
    (which2act), where to act (where2act), how to act (how2act).

The encoder therefore produces:

    1. a compact sensorimotor feature vector ``u_t`` used as the world
       model's state input (semantic scene embedding + analytic geometry
       relative to the body + body capabilities);
    2. an explicit affordance map (which / where / how) that is consumed by
       the policy and by the anchor memory.

The semantic embedding reuses the Body/Brain shared two-tier embedder
(FAST local MiniLM first, QUALITY via LM Studio when available).  If no
embedder is available at all (headless), a deterministic character-n-gram
hashing embedding keeps the system fully functional — the Body must never
crash because a text model is missing.
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

import numpy as np

from .types import Action, BodyState, Observation, SceneObject

logger = logging.getLogger(__name__)

EMBED_DIM = 384  # FAST tier dimension (all-MiniLM-L6-v2)
GEOM_DIM = 20     # analytic scene geometry features
BODY_DIM = 8      # body state features


# ── Fallback embedder (deterministic char-n-gram hashing) ───────────────────


class HashEmbedder:
    """Dependency-free, deterministic text embedder.

    Not semantically as strong as MiniLM, but stable, fast, and always
    available.  Used only when the shared embedder is unavailable.
    """

    def __init__(self, dim: int = EMBED_DIM):
        self.dim = dim

    def encode(self, texts) -> np.ndarray:  # noqa: D102 - sentence-transformers surface
        single = isinstance(texts, str)
        out = []
        for text in ([texts] if single else list(texts)):
            vec = np.zeros(self.dim, dtype="float32")
            s = f" {str(text).lower().strip()} "
            for n in (2, 3, 4):
                for i in range(max(0, len(s) - n + 1)):
                    gram = s[i:i + n]
                    h = hash(gram) % self.dim
                    sign = 1.0 if (h & 1) == 0 else -1.0
                    vec[h % self.dim] += sign
            norm = float(np.linalg.norm(vec))
            if norm > 1e-8:
                vec /= norm
            out.append(vec)
        mat = np.asarray(out, dtype="float32")
        return mat[0] if single else mat


class _SharedEmbedderAdapter:
    """Wrap the shared two-tier embedder behind a stable .encode() surface."""

    def __init__(self, quality: bool = False):
        self.quality = quality

    def encode(self, texts) -> np.ndarray:  # noqa: D102
        from utils.shared_embedder import get_embedder
        return np.asarray(get_embedder(quality=self.quality).encode(texts), dtype="float32")


# ── Analytic geometry (body-relative) ────────────────────────────────────────


def _angle_between(a: float, b: float) -> float:
    return abs(math.atan2(math.sin(b - a), math.cos(b - a)))


def scene_geometry(objects: List[SceneObject], body: BodyState) -> np.ndarray:
    """Analytic, body-relative geometric features of the scene.

    Every feature is *indexed on the body*: distances are relative to the
    body position, angles relative to the body heading, reachability is
    computed against the body's reach capability.
    """
    feats = np.zeros(GEOM_DIM, dtype="float32")
    px, py = float(body.position[0]), float(body.position[1])
    reach = float(body.capabilities.get("reach", 1.8))
    heading = float(body.orientation)

    if not objects:
        feats[0] = 0.0
        return feats

    dists = []
    for o in objects:
        ox, oy = float(o.position[0]), float(o.position[1])
        dists.append(math.hypot(ox - px, oy - py))

    dmin = min(dists)
    feats[0] = 1.0 if dmin <= reach else 0.0          # something within reach?
    feats[1] = min(1.0, dmin / max(1e-6, reach))      # nearest distance / reach
    feats[2] = min(1.0, (sum(dists) / len(dists)) / (reach * 2.0))
    feats[3] = min(1.0, max(dists) / (reach * 4.0))
    feats[4] = min(1.0, len(objects) / 8.0)           # object density

    # bearing of nearest object relative to heading
    nearest = min(objects, key=lambda o: math.hypot(o.position[0] - px, o.position[1] - py))
    bearing = math.atan2(float(nearest.position[1]) - py, float(nearest.position[0]) - px)
    rel = _angle_between(heading, bearing)
    feats[5] = rel / math.pi                            # 0 = straight ahead, 1 = behind
    feats[6] = 1.0 if rel < math.pi / 4 else 0.0        # in front?
    feats[7] = math.sin(rel) * (1.0 if math.atan2(float(nearest.position[1]) - py, 0) >= 0 else -1.0)

    # kind composition
    kinds = [o.kind for o in objects]
    feats[8] = min(1.0, kinds.count("target") / max(1, len(objects)))
    feats[9] = min(1.0, sum(kind in {"obstacle", "mobile_obstacle"} for kind in kinds) / max(1, len(objects)))
    feats[10] = min(1.0, kinds.count("table") / max(1, len(objects)))
    feats[11] = min(1.0, kinds.count("chair") / max(1, len(objects)))

    # mass distribution relative to body strength
    strength = float(body.capabilities.get("strength", 20.0))
    pushable = sum(1 for o in objects if o.mass <= strength)
    feats[12] = pushable / max(1, len(objects))
    graspable = sum(1 for o in objects if o.kind in {"target", "chair", "generic"} and o.mass <= max(5.0, strength * 0.5))
    feats[13] = graspable / max(1, len(objects))

    # free space around body (heuristic: inverse of nearby obstacle density)
    near = sum(1 for o in objects if math.hypot(o.position[0] - px, o.position[1] - py) < reach)
    feats[14] = 1.0 - min(1.0, near / 3.0)
    feats[15] = math.hypot(*body.position[:2]) / (reach * 8.0)  # distance from origin, normalised

    # per-kind nearest distance — the invariants a policy must be able to read
    # (e.g. "how far is the target object?" regardless of other clutter)
    for i, k in enumerate(("target", "table", "chair", "obstacle")):
        kd = [d for o, d in zip(objects, dists) if o.kind == k]
        feats[16 + i] = min(1.0, min(kd) / (reach * 4.0)) if kd else 0.0
    return feats


def body_features(body: BodyState) -> np.ndarray:
    f = np.zeros(BODY_DIM, dtype="float32")
    cap = body.capabilities
    f[0] = float(body.position[0]) / 16.0
    f[1] = float(body.position[1]) / 16.0
    f[2] = float(body.position[2]) / 4.0
    f[3] = math.sin(float(body.orientation))
    f[4] = math.cos(float(body.orientation))
    f[5] = min(2.0, float(cap.get("reach", 1.8))) / 2.0
    f[6] = min(2.0, float(cap.get("speed", 1.0))) / 2.0
    f[7] = min(1.0, float(cap.get("gripper", 1.0)))
    return f


# ── The cortex ───────────────────────────────────────────────────────────────


class ArtificialCortex:
    """Affordance encoder conditioned on the body's capabilities.

    ``encode(observation, body) -> np.ndarray``  (EMBED_DIM + GEOM_DIM + BODY_DIM)
    ``affordances(observation, body) -> dict``   (which / where / how)
    """

    def __init__(self, embedder: Optional[Any] = None, quality: bool = False):
        self._embedder = embedder
        self._quality = quality
        self._fallback = HashEmbedder(EMBED_DIM)

    # -- embedding -----------------------------------------------------------

    def _embed(self, text: str) -> np.ndarray:
        if self._embedder is not None:
            try:
                v = np.asarray(self._embedder.encode(text), dtype="float32").reshape(-1)
                if v.shape[0] == EMBED_DIM:
                    return v
                # Dimension mismatch (e.g. QUALITY tier 768-dim): project to
                # FAST dimension with a fixed random projection so the two
                # never get mixed inside one latent computation.
                return self._project_to(v, EMBED_DIM)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("[cortex] shared embedder failed (%s); using hash fallback", exc)
        v = self._fallback.encode(text)
        if v.shape[0] != EMBED_DIM:
            v = self._project_to(v, EMBED_DIM)
        return v

    @staticmethod
    def _project_to(vec: np.ndarray, dim: int) -> np.ndarray:
        seed = np.array(list(vec.tobytes()), dtype=np.uint8)
        rng = np.random.default_rng(int.from_bytes(seed[:8].tobytes().ljust(8, b"\0")[:8], "big"))
        proj = rng.standard_normal((dim, vec.shape[0])) * (1.0 / math.sqrt(vec.shape[0]))
        out = proj @ vec.astype("float64")
        out = out.astype("float32")
        n = float(np.linalg.norm(out))
        if n > 1e-8:
            out /= n
        return out

    # -- main encode ----------------------------------------------------------

    def encode(self, observation: Observation, body: BodyState) -> np.ndarray:
        text = observation.text or self.describe_scene(observation, body)
        semantic = self._embed(text)
        geom = scene_geometry(observation.scene, body)
        bfeat = body_features(body)
        return np.concatenate([semantic, geom, bfeat]).astype("float32")

    def describe_scene(self, observation: Observation, body: BodyState) -> str:
        """Natural-language scene description (also used by the Brain)."""
        if observation.text:
            return observation.text
        parts = [f"Body at ({body.position[0]:.1f},{body.position[1]:.1f}) heading {math.degrees(body.orientation):.0f}deg."]
        reach = body.capabilities.get("reach", 1.8)
        objs = []
        for o in observation.scene:
            d = math.hypot(o.position[0] - body.position[0], o.position[1] - body.position[1])
            rel = "within reach" if d <= reach else f"{d:.1f} away"
            objs.append(f"{o.label} ({o.kind}, {rel})")
        if objs:
            parts.append("Scene: " + "; ".join(objs) + ".")
        else:
            parts.append("Scene: empty.")
        return " ".join(parts)

    # -- affordances ----------------------------------------------------------

    def affordances(self, observation: Observation, body: BodyState) -> Dict[str, Any]:
        """Compute which / where / how affordances for the current scene.

        An object is only actionable if the body *can* act on it (reach,
        strength, gripper).  Scores are in [0, 1].
        """
        reach = float(body.capabilities.get("reach", 1.8))
        strength = float(body.capabilities.get("strength", 20.0))
        gripper = float(body.capabilities.get("gripper", 1.0))
        px, py = body.position[0], body.position[1]

        which: List[Dict[str, Any]] = []
        where: List[Dict[str, Any]] = []
        how: List[Dict[str, Any]] = []

        for o in observation.scene:
            ox, oy = float(o.position[0]), float(o.position[1])
            d = math.hypot(ox - px, oy - py)
            bearing = math.atan2(oy - py, ox - px)
            in_reach = d <= reach * (1.0 + 0.25 * o.size)
            if o.kind in {"obstacle", "mobile_obstacle"}:
                score = 0.2  # only "avoid" is meaningful
                actions = ["avoid"]
            elif in_reach and gripper > 0.5 and o.mass <= max(5.0, strength * 0.5):
                score = min(1.0, 1.0 - (d / (reach * 1.25)) * 0.5)
                actions = ["grab", "push"]
            elif in_reach and o.mass <= strength:
                score = min(1.0, 0.9 - (d / (reach * 1.25)) * 0.4)
                actions = ["push"]
            elif o.kind == "target" and d < reach * 3.0:
                score = max(0.25, 0.8 - d / (reach * 6.0))
                actions = ["approach"]
            else:
                score = max(0.1, 0.5 - d / (reach * 8.0))
                actions = ["approach"]

            entry = {
                "id": o.id, "label": o.label, "kind": o.kind,
                "distance": round(d, 3), "in_reach": bool(in_reach),
                "score": round(float(score), 3), "actions": actions,
            }
            which.append(entry)
            where.append({
                "id": o.id, "label": o.label,
                "point": [round(ox, 3), round(oy, 3), 0.0],
                "bearing": round(float(bearing), 3),
            })
            for act in actions:
                how.append({"id": o.id, "action": act, "score": round(float(score), 3)})

        which.sort(key=lambda e: e["score"], reverse=True)
        how.sort(key=lambda e: e["score"], reverse=True)
        return {
            "which2act": which[:8],
            "where2act": where[:8],
            "how2act": how[:12],
            "body": {
                "position": [round(float(v), 3) for v in body.position[:3]],
                "heading_deg": round(math.degrees(body.orientation), 1),
                "reach": reach,
            },
        }


def action_space_for_body(body: BodyState) -> List[Action]:
    """Candidate actions available to the body given its capabilities."""
    actions = [
        Action(type="forward"),
        Action(type="backward"),
        Action(type="turn_left"),
        Action(type="turn_right"),
        Action(type="wait"),
    ]
    if float(body.capabilities.get("max_speed", 1.0)) > 1.0:
        actions.append(Action(type="sprint", params={"speed": float(body.capabilities["max_speed"])}))
    if float(body.capabilities.get("gripper", 1.0)) > 0.5:
        actions += [Action(type="grab"), Action(type="release")]
    if float(body.capabilities.get("strength", 0.0)) > 1.0:
        actions.append(Action(type="push"))
    return actions
