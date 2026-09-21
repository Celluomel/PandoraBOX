"""Core data types for the Body's embodied world model.

Design principle (from the architecture spec):

    * The Body owns its world model.  These types describe a *physical*
      world: body state, observations, actions, outcomes, episodes and the
      three anchor families (lieux / objets / trajectoires).
    * The Brain only *consumes* summaries produced from these structures
      (via ``EmbodiedWorldModel.context_for_brain()``); it never mutates
      them directly.
    * Everything here is stdlib-only (no torch / numpy required to import)
      so the Body can be imported in the lightest possible process.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


def new_id(prefix: str) -> str:
    """Short, sortable, collision-resistant id (time-prefixed)."""
    return f"{prefix}-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"


# ── Body & world primitives ──────────────────────────────────────────────────


@dataclass
class BodyState:
    """State of Lumina's body at a point in time.

    ``position`` is expressed in the world frame (metres or grid units).
    ``capabilities`` describes what the body *can do* — the whole point of an
    affordance-based encoding is that perception is indexed on these limits.
    """

    position: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    orientation: float = 0.0  # radians, yaw
    posture: Dict[str, Any] = field(default_factory=dict)
    capabilities: Dict[str, float] = field(default_factory=lambda: {
        "reach": 1.8,          # metres
        "speed": 1.0,          # cells / step
        "strength": 20.0,      # max pushable mass (kg)
        "gripper": 1.0,        # 1.0 = has a working end-effector
    })
    timestamp: float = field(default_factory=time.time)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "BodyState":
        return cls(
            position=list(d.get("position") or [0.0, 0.0, 0.0])[:3] + [0.0] * (3 - len(d.get("position") or [])),
            orientation=float(d.get("orientation", 0.0)),
            posture=dict(d.get("posture") or {}),
            capabilities=dict(d.get("capabilities") or {}),
            timestamp=float(d.get("timestamp") or time.time()),
        )


@dataclass
class SceneObject:
    """A physical object as perceived by the body."""

    id: str
    label: str
    kind: str = "object"  # table | chair | obstacle | target | generic
    position: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    size: float = 1.0
    mass: float = 1.0
    props: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SceneObject":
        return cls(
            id=str(d.get("id") or new_id("obj")),
            label=str(d.get("label") or "object"),
            kind=str(d.get("kind") or "object"),
            position=list(d.get("position") or [0.0, 0.0, 0.0]),
            size=float(d.get("size", 1.0)),
            mass=float(d.get("mass", 1.0)),
            props=dict(d.get("props") or {}),
        )


@dataclass
class Observation:
    """A single normalized observation from the body's sensors.

    Mirrors the ``BodyObservation`` fields (source/kind/subject/value/...)
    and extends them with the *scene* the body is in plus a free-text
    description used by the semantic encoder.
    """

    subject: str = "scene"
    value: Any = None
    source: str = "body"
    kind: str = "scene"
    unit: str = ""
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)
    scene: List[SceneObject] = field(default_factory=list)
    text: str = ""  # natural-language description of the current scene

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["scene"] = [o.as_dict() for o in self.scene]
        d["age_seconds"] = round(max(0.0, time.time() - self.timestamp), 3)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Observation":
        scene = [SceneObject.from_dict(o) for o in (d.get("scene") or [])]
        return cls(
            subject=str(d.get("subject") or "scene"),
            value=d.get("value"),
            source=str(d.get("source") or "body"),
            kind=str(d.get("kind") or "scene"),
            unit=str(d.get("unit") or ""),
            confidence=float(d.get("confidence", 1.0)),
            timestamp=float(d.get("timestamp") or time.time()),
            scene=scene,
            text=str(d.get("text") or ""),
        )


@dataclass
class Action:
    """An action the body can execute.

    In *sim* mode the action is executed directly by the simulated world.
    In *bridge* mode it is enqueued as a ``BodyCommand`` (queued, requires
    confirmation — the safety posture already implemented by BodyRuntime).
    """

    type: str = "wait"
    target: Optional[str] = None  # object id or entity id
    params: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Action":
        return cls(
            type=str(d.get("type") or "wait"),
            target=d.get("target"),
            params=dict(d.get("params") or {}),
            timestamp=float(d.get("timestamp") or time.time()),
        )


@dataclass
class Outcome:
    """Result of executing an action, as judged by the world."""

    kind: str = "neutral"  # success | failure | danger | neutral
    reward: float = 0.0
    description: str = ""
    timestamp: float = field(default_factory=time.time)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Outcome":
        return cls(
            kind=str(d.get("kind") or "neutral"),
            reward=float(d.get("reward", 0.0)),
            description=str(d.get("description") or ""),
            timestamp=float(d.get("timestamp") or time.time()),
        )


@dataclass
class Episode:
    """One (state, action, next_state, reward) experience of the body."""

    step_id: int
    obs_before: Observation
    action: Action
    obs_after: Optional[Observation] = None
    outcome: Outcome = field(default_factory=Outcome)
    reward: float = 0.0
    prediction_error: float = 0.0
    policy_score: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "obs_before": self.obs_before.as_dict(),
            "action": self.action.as_dict(),
            "obs_after": self.obs_after.as_dict() if self.obs_after else None,
            "outcome": self.outcome.as_dict(),
            "reward": self.reward,
            "prediction_error": self.prediction_error,
            "policy_score": self.policy_score,
            "timestamp": self.timestamp,
        }


# ── Memory anchors (physical world memory) ───────────────────────────────────


def _anchor_common(d: Dict[str, Any], prefix: str) -> Dict[str, Any]:
    return {
        "id": str(d.get("id") or new_id(prefix)),
        "label": str(d.get("label") or prefix),
        "reliability": float(d.get("reliability", 0.5)),
        "utility": float(d.get("utility", 0.0)),
        "created_at": float(d.get("created_at") or time.time()),
        "updated_at": float(d.get("updated_at") or time.time()),
        "last_used_at": float(d.get("last_used_at") or time.time()),
        "stale": bool(d.get("stale", False)),
    }


@dataclass
class AnchorLieu:
    """A remembered *place*: stable spatial reference point."""

    id: str = field(default_factory=lambda: new_id("lieu"))
    label: str = ""
    position: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    orientation: float = 0.0
    topology: Dict[str, List[str]] = field(default_factory=dict)  # neighbours
    objects: List[str] = field(default_factory=list)  # AnchorObjet ids seen here
    affordances: Dict[str, float] = field(default_factory=dict)  # action -> strength
    episodes: List[int] = field(default_factory=list)
    reliability: float = 0.5
    utility: float = 0.0
    visits: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    stale: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AnchorLieu":
        base = _anchor_common(d, "lieu")
        return cls(
            id=base["id"], label=base["label"],
            position=list(d.get("position") or [0.0, 0.0, 0.0]),
            orientation=float(d.get("orientation", 0.0)),
            topology={str(k): list(v) for k, v in (d.get("topology") or {}).items()},
            objects=list(d.get("objects") or []),
            affordances={str(k): float(v) for k, v in (d.get("affordances") or {}).items()},
            episodes=[int(e) for e in (d.get("episodes") or [])],
            reliability=base["reliability"], utility=base["utility"],
            visits=int(d.get("visits", 0)),
            created_at=base["created_at"], updated_at=base["updated_at"],
            last_used_at=base["last_used_at"], stale=base["stale"],
        )


@dataclass
class AnchorObjet:
    """A remembered *physical object*: identity, properties, affordances."""

    id: str = field(default_factory=lambda: new_id("objet"))
    label: str = ""
    kind: str = "object"
    position: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    props: Dict[str, Any] = field(default_factory=dict)
    affordances: Dict[str, float] = field(default_factory=dict)  # action -> strength
    interactions: int = 0
    successes: int = 0
    failures: int = 0
    reliability: float = 0.5
    utility: float = 0.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    stale: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AnchorObjet":
        base = _anchor_common(d, "objet")
        return cls(
            id=base["id"], label=base["label"], kind=str(d.get("kind") or "object"),
            position=list(d.get("position") or [0.0, 0.0, 0.0]),
            props=dict(d.get("props") or {}),
            affordances={str(k): float(v) for k, v in (d.get("affordances") or {}).items()},
            interactions=int(d.get("interactions", 0)),
            successes=int(d.get("successes", 0)),
            failures=int(d.get("failures", 0)),
            reliability=base["reliability"], utility=base["utility"],
            created_at=base["created_at"], updated_at=base["updated_at"],
            last_used_at=base["last_used_at"], stale=base["stale"],
        )


@dataclass
class AnchorTrajectoire:
    """A remembered *trajectory*: a sequence of actions with its outcome."""

    id: str = field(default_factory=lambda: new_id("traj"))
    label: str = ""
    positions: List[List[float]] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    outcome: str = "neutral"  # success | failure | danger | neutral
    success_count: int = 0
    fail_count: int = 0
    utility: float = 0.0
    reliability: float = 0.5
    context_lieux: List[str] = field(default_factory=list)
    context_objets: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    stale: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AnchorTrajectoire":
        base = _anchor_common(d, "traj")
        return cls(
            id=base["id"], label=base["label"],
            positions=[[float(v) for v in p] for p in (d.get("positions") or [])],
            actions=list(d.get("actions") or []),
            outcome=str(d.get("outcome") or "neutral"),
            success_count=int(d.get("success_count", 0)),
            fail_count=int(d.get("fail_count", 0)),
            utility=float(d.get("utility", 0.0)),
            reliability=base["reliability"],
            context_lieux=list(d.get("context_lieux") or []),
            context_objets=list(d.get("context_objets") or []),
            created_at=base["created_at"], updated_at=base["updated_at"],
            last_used_at=base["last_used_at"], stale=base["stale"],
        )


# ── Latent state ─────────────────────────────────────────────────────────────


@dataclass
class GlobalState:
    """The unified state of the organism: cognitive + physical + body.

    The physical latent is the *primary* representation (the body owns it);
    the cognitive latent is an optional projection of the brain's state and
    is used only as an extra conditioning input for the dynamics.
    """

    physical: Dict[str, Any] = field(default_factory=dict)  # latent summary / features
    cognitive: Dict[str, Any] = field(default_factory=dict)
    body: Optional[BodyState] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "physical": self.physical,
            "cognitive": self.cognitive,
            "body": self.body.as_dict() if self.body else None,
        }
