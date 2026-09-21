"""EmbodiedWorldModel — the Body's world model, owned by the Body.

This is the single entry point that wires the whole embodied stack:

    ArtificialCortex      — affordance encoder (perception indexed on the body)
    PhysicalMemory        — anchors: lieux / objets / trajectoires
    LatentWorldDynamics   — learned s_{t+1} = f(s_t, a_t) + imagination
    Policy                — decision by anticipation (imagined rollouts)
    ConsolidationEngine   — revision / optimization / reinforcement
    SimulatedRoom         — the executable test body (sim mode)

Architecture rule (from the spec): the Body OWNS this model and its memory.
The Brain only *reads* ``context_for_brain()`` / ``status_summary()``; it
never mutates anchors or dynamics directly.  In *bridge* mode the Body's
real actuators are reached through ``BodyRuntime.enqueue_command`` (queued,
confirmation-required — the existing safety posture).

``step()`` runs the 11-step sensorimotor protocol:
    1 observe   2 body state   3 cortex encode   4 anchor activation
    5 physical latent   6 cognitive latent   7 global state
    8 policy decision   9 execute   10 learn (prediction error + update)
    11 consolidate + log
"""
from __future__ import annotations

import json
import logging
import math
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from .anchors import PhysicalMemory, atomic_write_json
from .consolidation import ConsolidationEngine
from .concepts import EmbodiedConceptMemory
from .cortex import ArtificialCortex, action_space_for_body
from .dynamics import LatentWorldDynamics
from .navigation import navigation_guidance
from .policy import Policy
from .sim_world import SimulatedRoom
from .sources import SimRobotSource
from .types import (
    Action, BodyState, Episode, GlobalState, Observation, Outcome,
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "enabled": False,              # background loop off by default (opt-in)
    # Sensor source modes:
    #   "sim"    — built-in simulated robot (sandbox; default)
    #   "bridge" — legacy: brain-side BodyRuntime (Home Assistant centred)
    # An explicit ``source`` object (robot plugin, sim robot, HA fallback)
    # always takes priority over the mode.
    "mode": "sim",
    "step_interval": 2.0,          # seconds between background steps (sim)
    "horizon": 8,                  # imagination horizon
    "lr": 5e-3,
    "batch": 64,
    "train_every": 8,             # keep action selection off the training hot path
    "train_epochs": 1,
    "consolidation_every": 50,     # background_pass every N steps
    "max_buffer": 4096,
    "max_episodes": 2000,
    "embed_quality": False,        # use FAST tier for hot path (recommended)
    "exploration": 0.35,
    "risk_aversion": 0.25,
    "body_actuation_enabled": False,
}


class EmbodiedWorldModel:
    """The Body's embodied world model + physical memory + policy."""

    def __init__(
        self,
        body: Optional[Any] = None,
        data_dir: str | Path = "data/body/worldmodel",
        config: Optional[Dict[str, Any]] = None,
        source: Optional[Any] = None,
    ):
        self.body = body  # legacy "bridge" mode: brain-side BodyRuntime
        self.data_dir = Path(data_dir)
        self._cfg = dict(DEFAULT_CONFIG)
        self._cfg.update(self._load_config())
        if config:
            self._cfg.update(config)
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._steps = 0
        self._step_history: deque = deque(maxlen=512)
        self._episodes: deque = deque(maxlen=64)
        self._pred_error_ema = 0.0
        self._last_loss: Optional[Dict[str, float]] = None
        self._last_decision: Optional[Dict[str, Any]] = None
        self._last_navigation: Dict[str, Any] = {}
        self._last_report: Optional[Dict[str, Any]] = None
        self._last_success_step = -1
        # Keep the latest perception boundary observable without re-polling a
        # physical source from the status endpoint.
        self._last_observation: Optional[Observation] = None
        self._last_body_state: Optional[BodyState] = None
        self._last_affordances: Dict[str, Any] = {}

        # -- components ------------------------------------------------------
        self.memory = PhysicalMemory(self.data_dir / "anchors.json")
        self.cortex = ArtificialCortex(quality=bool(self._cfg.get("embed_quality", False)))
        # Sensor source: explicit plugin (robot > sim robot > HA fallback >
        # null) wins; otherwise derived from the configured mode.
        if source is not None:
            self.source = source
        elif self._cfg.get("mode") == "bridge":
            self.source = None  # legacy brain-side bridge path
        else:
            self.source = SimRobotSource()
        # dynamics input dim is fixed by the cortex output dim
        probe = self.cortex.encode(Observation(), BodyState())
        self.dynamics = LatentWorldDynamics(
            in_dim=int(probe.shape[0]),
            latent_dim=32,
            hidden_dim=64,
            lr=float(self._cfg.get("lr", 3e-3)),
            save_path=self.data_dir / "dynamics.pt",
        )
        self.policy = Policy(
            self.dynamics,
            horizon=int(self._cfg.get("horizon", 8)),
            risk_aversion=float(self._cfg.get("risk_aversion", 0.25)),
            exploration=float(self._cfg.get("exploration", 0.10)),
        )
        self.consolidation = ConsolidationEngine(self.memory)
        self.concepts = EmbodiedConceptMemory(self.data_dir / "concepts.json")
        self._episodes_path = self.data_dir / "episodes.jsonl"
        self._maybe_trim_episodes_file()

    # ── config ──────────────────────────────────────────────────────────────

    def _load_config(self) -> Dict[str, Any]:
        try:
            p = self.data_dir / "config.json"
            if p.exists():
                payload = json.loads(p.read_text(encoding="utf-8"))
                return payload if isinstance(payload, dict) else {}
        except Exception:
            pass
        return {}

    def config(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._cfg)

    def update_config(self, values: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            for k, v in (values or {}).items():
                if k in DEFAULT_CONFIG or k in self._cfg:
                    self._cfg[k] = v
            payload = dict(self._cfg)
            mode_changed = payload.get("mode")
        try:
            atomic_write_json(self.data_dir / "config.json", payload)
        except Exception as exc:
            logger.warning("[worldmodel] config save failed: %s", exc)
        if mode_changed == "sim" and not isinstance(self.source, SimRobotSource):
            self.source = SimRobotSource()
        if mode_changed == "bridge":
            self.source = None
        if self._cfg.get("enabled"):
            self.start()
        else:
            self.stop()
        return dict(payload)

    # ── lifecycle ───────────────────────────────────────────────────────────

    def start(self) -> None:
        with self._lock:
            if not self._cfg.get("enabled"):
                self._cfg["enabled"] = True
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, name="lumina-body-worldmodel", daemon=True)
            self._thread.start()
        logger.info("[worldmodel] background loop started (mode=%s, interval=%ss)",
                    self._cfg.get("mode"), self._cfg.get("step_interval"))

    def stop(self) -> None:
        self._stop.set()
        t = self._thread
        if t and t.is_alive():
            t.join(timeout=2.0)
        self._thread = None
        try:
            self.memory.save()
            if self.dynamics.available:
                self.dynamics.save()
        except Exception:
            pass

    def _run(self) -> None:
        while not self._stop.wait(max(0.2, float(self._cfg.get("step_interval", 2.0)))):
            try:
                self.step()
            except Exception:
                logger.exception("[worldmodel] background step failed")

    # ── the 11-step protocol ────────────────────────────────────────────────

    def step(self) -> Dict[str, Any]:
        with self._lock:
            # 1) observe (sensor source: robot > sim robot > HA fallback)
            if self.source is not None:
                obs = self.source.observe()
            else:
                obs = self._bridge_observation()
            # 2) body state
            body_state = self.source.body_state() if self.source is not None else self._bridge_body_state()
            # 3) cortex encode (affordance features, body-conditioned)
            features = self.cortex.encode(obs, body_state)
            aff = self.cortex.affordances(obs, body_state)
            self._last_observation = obs
            self._last_body_state = body_state
            self._last_affordances = aff
            # 4) anchor activation (upsert what we see now)
            self._activate_anchors(obs, body_state, aff)
            # 5) physical latent
            s = self.dynamics.encode(features)
            # 6) cognitive latent (Brain context — optional, read-only)
            cog = self._cognitive_latent()
            # 7) global state
            state = GlobalState(physical={"latent_dim": int(s.shape[0])}, cognitive=cog, body=body_state)
            # 8) policy decision by imagined rollouts
            candidates = self._candidates(obs, body_state, aff)
            carrying = bool(getattr(self.sim, "carrying", None))
            navigation = navigation_guidance(obs, body_state, carrying=carrying)
            forbidden = set(navigation.get("forbidden", []))
            if forbidden:
                safe = [candidate for candidate in candidates if str(candidate.get("type")) not in forbidden]
                if safe:
                    candidates = safe
            # Exploration anneals down as the policy gains experience
            # (more plastic early, more stable later — mirrors the
            # stability/plasticity principle applied to behaviour).
            self.policy.exploration = max(0.08, 0.40 * (0.997 ** self._steps))
            # Affordance-guided steering prior (weak, phase-aware) — the
            # cortex's action-oriented channel informs exploration; learned
            # value dominates once the model has real signal.
            prior = self._steering_prior(obs, aff, body_state)
            for action, score in navigation.get("prior", {}).items():
                prior[action] = max(float(prior.get(action, 0.0)), float(score))
            decision = self.policy.decide(s, candidates, prior=prior or None)
            chosen = decision.get("action")
            # 9) execute (robot actuators, sandbox physics, or legacy bridge)
            if self.source is not None:
                obs_after, outcome = self.source.execute(self._as_action(chosen))
            else:
                obs_after, outcome = self._bridge_execute(chosen)
            reward = outcome.reward
            # 10) learn: prediction error + online update
            pred_s_next = self.dynamics.step(s, self._action_vec(chosen))
            next_body = self.source.body_state() if self.source is not None else body_state
            actual_features = self.cortex.encode(obs_after, next_body)
            s_next_actual = self.dynamics.encode(actual_features)
            # Scale-free prediction error: RMS difference over the latent dim
            # (the latent is tanh-bounded, so this stays in ~[0, 2] and is a
            # meaningful "how wrong was the world model" signal).
            diff = np.asarray(pred_s_next, dtype="float32") - np.asarray(s_next_actual, dtype="float32")
            pred_error = float(np.sqrt(np.mean(np.square(diff))))
            self._pred_error_ema = (0.9 * self._pred_error_ema + 0.1 * pred_error) if self._steps else pred_error
            if self.dynamics.available:
                success = outcome.kind == "success"
                self.dynamics.remember(features, chosen, actual_features, reward, success)
                train_every = max(1, int(self._cfg.get("train_every", 8)))
                if (self._steps + 1) % train_every == 0:
                    self._last_loss = self.dynamics.train_step(
                        batch=int(self._cfg.get("batch", 64)),
                        epochs=max(1, int(self._cfg.get("train_epochs", 1))),
                    )
            # 11) consolidate + log
            episode = Episode(
                step_id=self._steps,
                obs_before=obs,
                action=self._as_action(chosen),
                obs_after=obs_after,
                outcome=outcome,
                reward=reward,
                prediction_error=round(pred_error, 5),
                policy_score=float(decision.get("score", 0.0)),
            )
            report = self.consolidation.process_episode(
                episode, pred_error,
                body_position=list(body_state.position),
                obs_after=obs_after,
            )
            self.concepts.learn(episode)
            self._log_episode(episode)
            self._steps += 1
            self._step_history.append({
                "step": self._steps,
                "action": self._action_label(chosen),
                "reward": round(reward, 4),
                "pred_error": round(pred_error, 5),
                "outcome": outcome.kind,
                "t": round(time.time(), 1),
            })
            if outcome.kind == "success" and reward >= 0.5:
                self._last_success_step = self._steps
            if self._steps % max(1, int(self._cfg.get("consolidation_every", 50))) == 0:
                self.consolidation.background_pass()
                self.memory.save()
            self._last_decision = {
                "action": self._action_label(chosen),
                "score": decision.get("score"),
                "reason": decision.get("reason"),
                "top": [
                    {"action": self._action_label(t.get("action")), "score": t.get("score")}
                    for t in decision.get("top", [])[:3]
                ],
            }
            self._last_navigation = navigation
            self._last_report = report
            return self._step_summary(episode, decision, aff, pred_error)

    def execute_external(self, action: Action) -> Dict[str, Any]:
        """Execute one explicitly approved Body command and learn its outcome.

        The autonomous world-model loop never calls this method. Physical
        sources expose actuation only through this permissioned boundary.
        """
        with self._lock:
            if self.source is None:
                obs = self._bridge_observation()
                outcome = Outcome(kind="failure", reward=-0.1, description="no actuator source attached")
            else:
                obs = self.source.observe()
                body_state = self.source.body_state()
                executor = getattr(self.source, "execute_authorized", None)
                obs_after = obs
                if not callable(executor):
                    outcome = Outcome(kind="failure", reward=-0.1, description="source has no authorized actuator adapter")
                else:
                    obs_after, outcome = executor(action)
            episode = Episode(
                step_id=self._steps,
                obs_before=obs,
                action=action,
                obs_after=obs_after,
                outcome=outcome,
                reward=outcome.reward,
                prediction_error=0.0,
                policy_score=0.0,
            )
            self._log_episode(episode)
            self._episodes.append(episode)
            self._steps += 1
            self._last_success_step = self._steps if outcome.kind == "success" else self._last_success_step
            return {
                "step": episode.step_id,
                "action": self._action_label(action),
                "target": action.target,
                "outcome": outcome.as_dict(),
                "reward": outcome.reward,
            }

    # ── step output ─────────────────────────────────────────────────────────

    def _step_summary(self, episode: Episode, decision: Dict, aff: Dict, pred_error: float) -> Dict[str, Any]:
        return {
            "step": episode.step_id,
            "action": self._action_label(episode.action),
            "target": episode.action.target,
            "outcome": episode.outcome.as_dict(),
            "reward": episode.reward,
            "prediction_error": round(pred_error, 5),
            "pred_error_ema": round(self._pred_error_ema, 5),
            "policy": self._last_decision,
            "affordances_top": {
                "which2act": aff.get("which2act", [])[:3],
                "how2act": aff.get("how2act", [])[:4],
            },
            "consolidation": self._last_report,
        }

    # ── anchor activation ───────────────────────────────────────────────────

    def _activate_anchors(self, obs: Observation, body: BodyState, aff: Dict) -> None:
        # place anchor for where the body currently is
        self.memory.upsert_lieu(
            label=self.memory.find_lieu(list(body.position)) and (self.memory.find_lieu(list(body.position)).label)
                or f"place({body.position[0]:.1f},{body.position[1]:.1f})",
            position=list(body.position),
            orientation=body.orientation,
            objects=[o.id for o in obs.scene][:8],
            affordances={h["action"]: h["score"] for h in aff.get("how2act", [])[:6]},
        )
        # object anchors for everything perceived
        for o in obs.scene[:12]:
            obj_scores = {
                h["action"]: h["score"]
                for h in aff.get("how2act", [])
                if h.get("id") == o.id
            } or {}
            self.memory.upsert_objet(
                object_id=o.id, label=o.label, kind=o.kind,
                position=list(o.position),
                props={"size": o.size, "mass": o.mass, **(o.props or {})},
                affordances=obj_scores,
            )

    # ── candidates & execution ──────────────────────────────────────────────

    @property
    def sim(self) -> Optional[SimulatedRoom]:
        """Backward-compat accessor: the sandbox room behind a sim source."""
        return getattr(getattr(self, "source", None), "room", None)

    def _candidates(self, obs: Observation, body: BodyState, aff: Dict) -> List[Dict[str, Any]]:
        base = [a.as_dict() for a in action_space_for_body(body)]
        if self.source is not None and aff.get("target_id"):
            # attach the most actionable target to grab/push (from affordances)
            which = {w["id"]: w for w in aff.get("which2act", [])}
            for cand in base:
                if cand["type"] in {"grab", "push"}:
                    best = None
                    for w in aff.get("which2act", []):
                        if w["id"] in which and any(a in which[w["id"]]["actions"] for a in [cand["type"]]):
                            best = w
                            break
                    if best is not None:
                        cand["target"] = best["id"]
                        cand["params"] = {
                            "target_kind": which[best["id"]]["kind"],
                            "body_pos": [round(float(body.position[0]), 2), round(float(body.position[1]), 2)],
                        }
        return base

    def _steering_prior(self, obs: Observation, aff: Dict, body: BodyState) -> Dict[str, float]:
        """Affordance-guided steering prior for exploration.

        Uses the cortex's *action-oriented* output (which/where2act bearings)
        to bias locomotion toward the most actionable target.  Weak by design
        and constant: it is an exploration signal, not a controller — the
        learned imagined value (task rewards up to +1.0) dominates once the
        model has real signal.

        Phase-aware: while the body *carries* something, the goal is the drop
        zone (shelf), not the carried object — read from the sensor stream.
        """
        import re
        text = obs.text or ""
        carrying = bool(re.search(r"Carrying \w+", text))
        shelf = None
        m = re.search(r"Shelf at \(([-\d.]+),\s*([-\d.]+)\)", text)
        if m:
            shelf = (float(m.group(1)), float(m.group(2)))

        px, py = float(body.position[0]), float(body.position[1])
        if carrying and shelf is not None:
            gx, gy = shelf
            score = 0.9  # carried object must reach the drop zone
        else:
            which = aff.get("which2act") or []
            if not which:
                return {}
            best = next((w for w in which if w.get("kind") == "target"), which[0])
            score = float(best.get("score", 0.0))
            if score < 0.2:
                return {}
            gx = gy = None
            for w in aff.get("where2act") or []:
                if w.get("id") == best.get("id"):
                    gx, gy = float(w["point"][0]), float(w["point"][1])
                    break
            if gx is None:
                return {}

        bearing = math.atan2(gy - py, gx - px)
        heading = float(body.orientation)
        diff = math.atan2(math.sin(bearing - heading), math.cos(bearing - heading))
        k = 0.08 * score
        prior: Dict[str, float] = {}
        if abs(diff) <= math.pi / 4:
            prior["forward"] = k
        elif diff > 0:
            prior["turn_left"] = k * 0.8
        else:
            prior["turn_right"] = k * 0.8
        return prior

    def _bridge_observation(self) -> Observation:
        """Build an Observation from the Body's real sensor stream (HA etc.)."""
        if self.body is None:
            return Observation(subject="scene", text="No body sensors attached.", source="body")
        try:
            items = self.body.snapshot(max_age=300.0)[:12]
        except Exception:
            items = []
        text = "Body sensors: " + (
            "; ".join(f"{i.get('subject')}={i.get('value')}" for i in items) if items else "none active."
        )
        # Derive a coarse 2-D position from presence signals (room => cell).
        pos = [0.0, 0.0, 0.0]
        for i in items:
            if str(i.get("value", "")).lower() in {"on", "true", "present", "1"} and "presence" in str(i.get("subject", "")).lower():
                h = abs(hash(i.get("subject", ""))) % 8
                pos = [float(h), float((abs(hash(i.get("subject", ""))) >> 3) % 8), 0.0]
                break
        return Observation(subject="sensors", value=None, source="body", kind="sensor_stream", text=text)

    def _bridge_body_state(self) -> BodyState:
        obs = self._bridge_observation()
        # position heuristic from the observation text (stable per room label)
        pos = [0.0, 0.0, 0.0]
        try:
            if self.body is not None:
                items = self.body.snapshot(max_age=300.0)
                for i in items:
                    if "presence" in str(i.get("subject", "")).lower() and str(i.get("value", "")).lower() in {"on", "true", "1"}:
                        h = abs(hash(i.get("subject", "")))
                        pos = [float(h % 8), float((h >> 3) % 8), 0.0]
                        break
        except Exception:
            pass
        return BodyState(position=pos, capabilities={"reach": 1.0, "strength": 10.0, "gripper": 0.0, "speed": 1.0})

    def _bridge_execute(self, chosen: Any) -> tuple[Observation, Outcome]:
        """Execute a decision against the real body: queue a confirmed command."""
        a = self._as_action(chosen)
        if self.body is None or not a.target:
            return self._bridge_observation(), Outcome(kind="neutral", reward=0.0, description="bridge idle (no target)")
        try:
            self.body.enqueue_command(
                target=str(a.target), action=a.type or "set_state",
                payload={"params": a.params, "origin": "body-worldmodel"},
            )
            return self._bridge_observation(), Outcome(
                kind="neutral", reward=0.0,
                description=f"command queued for {a.target} ({a.type}) — pending confirmation",
            )
        except Exception as exc:
            return self._bridge_observation(), Outcome(kind="failure", reward=-0.1, description=f"bridge error: {exc}")

    # ── cognitive bridge (Brain -> Body, read-only) ─────────────────────────

    def _cognitive_latent(self) -> Dict[str, Any]:
        """Project the Brain's current state into a small conditioning dict.

        Deliberately lightweight and non-fatal: the Body must stay fully
        functional without a Brain attached.
        """
        cog: Dict[str, Any] = {}
        org = getattr(self.body, "organism", None)
        if org is None:
            return cog
        try:
            emo = getattr(getattr(org, "ai_system", None), "emotional_state", None)
            if emo is not None and hasattr(emo, "get_overall_valence_arousal"):
                v, a = emo.get_overall_valence_arousal()
                cog["valence"] = round(float(v), 3)
                cog["arousal"] = round(float(a), 3)
        except Exception:
            pass
        try:
            goals = getattr(org, "goal_system", None)
            if goals is not None and hasattr(goals, "active_goals"):
                active = list(goals.active_goals())[:3] if callable(getattr(goals, "active_goals", None)) else []
                if active:
                    cog["goal_hint"] = str(active[0])[:120]
        except Exception:
            pass
        return cog

    def context_for_brain(self, max_age: float = 3600.0) -> str:
        """Text summary of the Body's world knowledge, for the Brain prompt.

        This is the ONLY channel through which the world model informs the
        Brain (the inverse direction — Brain writing anchors — is forbidden,
        keeping the Brain/Body ownership boundary intact).
        """
        with self._lock:
            stats = self.memory.stats()
            top = self.memory.top_anchors(limit=3)
            n_steps = self._steps
            ema = self._pred_error_ema
            last_success = self._last_success_step
            sim_status = self.sim.status() if self.sim is not None else None
            source_status = self.source.status() if self.source is not None else None
        if n_steps == 0 and stats["lieux"]["count"] == 0:
            return ""
        lines = [
            "BODY WORLD MODEL (physical world knowledge owned by the Body):",
            f"- Learned {n_steps} embodied steps; prediction error (EMA) {ema:.3f}.",
            f"- Memory: {stats['lieux']['count']} places (avg reliability "
            f"{stats['lieux'].get('avg_reliability', 0):.2f}), "
            f"{stats['objets']['count']} objects (avg reliability "
            f"{stats['objets'].get('avg_reliability', 0):.2f}), "
            f"{stats['trajectories']['count']} action sequences.",
        ]
        concepts = self.concepts.snapshot(limit=5)
        if concepts:
            lines.append("- Reusable embodied concepts (confidence): " + "; ".join(f"{c['label']} ({c['confidence']:.2f})" for c in concepts) + ".")
        for family in ("objets", "lieux", "trajectories"):
            items = top.get(family, [])
            if items:
                lines.append(
                    f"- Most reliable {family}: "
                    + ", ".join(f"{i['label']} (r={i['reliability']:.2f})" for i in items[:3])
                    + "."
                )
        if sim_status is not None:
            task = "complete" if sim_status.get("done") else "in progress"
            lines.append(
                f"- Physical task state: {task} (carrying={sim_status.get('carrying')}, "
                f"steps={sim_status.get('steps')}, collisions={sim_status.get('collisions')})."
            )
        if source_status is not None:
            src = source_status.get("source")
            if src == "robot":
                lines.append(
                    f"- Sensor source: LIVE ROBOT at {source_status.get('url')} "
                    f"(last ok {source_status.get('last_ok_age_s')}s ago, "
                    f"latency {source_status.get('last_latency_ms')}ms)."
                )
            elif src == "sim_robot":
                lines.append("- Sensor source: simulated robot sandbox (dev/test).")
            elif src == "home_assistant":
                lines.append("- Sensor source: Home Assistant presence cues (auxiliary only).")
            elif src == "null":
                lines.append("- Sensor source: none attached (body without sensors).")
        if last_success >= 0:
            lines.append(f"- Last goal success at step {last_success}.")
        lines.append("Treat this as grounded physical evidence, not abstract belief.")
        return "\n".join(lines)

    # ── logging ─────────────────────────────────────────────────────────────

    def _log_episode(self, episode: Episode) -> None:
        self._episodes.append(episode)
        try:
            self._episodes_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._episodes_path, "a", encoding="utf-8") as fh:
                slim = episode.as_dict()
                slim["obs_before"] = {
                    "text": episode.obs_before.text,
                    "n_objects": len(episode.obs_before.scene),
                }
                slim["obs_after"] = {
                    "text": (episode.obs_after.text if episode.obs_after else None),
                    "n_objects": len(episode.obs_after.scene) if episode.obs_after else 0,
                }
                fh.write(json.dumps(slim, ensure_ascii=False, default=str) + "\n")
        except Exception:
            logger.debug("[worldmodel] episode log failed", exc_info=True)

    def _maybe_trim_episodes_file(self) -> None:
        try:
            if not self._episodes_path.exists():
                return
            max_lines = int(self._cfg.get("max_episodes", 2000))
            lines = self._episodes_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if len(lines) > max_lines:
                self._episodes_path.write_text("\n".join(lines[-max_lines:]) + "\n", encoding="utf-8")
        except Exception:
            logger.debug("[worldmodel] episode trim failed", exc_info=True)

    # ── helpers ─────────────────────────────────────────────────────────────

    def _as_action(self, a: Any) -> Action:
        if isinstance(a, Action):
            return a
        if isinstance(a, dict):
            return Action.from_dict(a)
        if isinstance(a, str):
            return Action(type=a)
        return Action(type="wait")

    def _action_vec(self, a: Any) -> np.ndarray:
        from .dynamics import _action_to_vec
        return _action_to_vec(a)

    def _action_label(self, a: Any) -> str:
        a = self._as_action(a)
        return f"{a.type}→{a.target}" if a.target else a.type

    # ── control & reporting ─────────────────────────────────────────────────

    def reset(self, clear_memory: bool = False) -> Dict[str, Any]:
        with self._lock:
            if self.sim is not None:
                self.sim.reset()
            if clear_memory:
                self.memory.reset()
            if self.dynamics.available:
                # re-init weights to fresh (keep the architecture)
                g = self.dynamics._torch.Generator().manual_seed(7)
                self.dynamics._torch.manual_seed(7)
                for mod in (self.dynamics._enc, self.dynamics._dyn, self.dynamics._dec, self.dynamics._value):
                    for p in mod.parameters():
                        if p.dim() >= 2:
                            self.dynamics._torch.nn.init.xavier_uniform_(p)
                        else:
                            self.dynamics._torch.nn.init.zeros_(p)
                self.dynamics._buffer.clear()
                self.dynamics._steps_trained = 0
            self._steps = 0
            self._step_history.clear()
            self._episodes.clear()
            self._pred_error_ema = 0.0
            self._last_loss = None
            self._last_decision = None
            self._last_navigation = {}
            self._last_observation = None
            self._last_body_state = None
            self._last_affordances = {}
        return self.status_summary()

    def status_summary(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "enabled": bool(self._cfg.get("enabled")),
                "mode": self._cfg.get("mode"),
                "source": self.source.status() if self.source is not None else {"source": "bridge"},
                "running": bool(self._thread and self._thread.is_alive()),
                "steps": self._steps,
                "last_success_step": self._last_success_step,
                "prediction_error_ema": round(self._pred_error_ema, 5),
                "dynamics": {
                    "available": self.dynamics.available,
                    "steps_trained": self.dynamics._steps_trained,
                    "buffer": len(self.dynamics._buffer),
                    "last_loss": self._last_loss,
                },
                "memory": self.memory.stats(),
                "concepts": self.concepts.stats(),
                "top_anchors": self.memory.top_anchors(limit=3),
                "policy": {
                    "horizon": self.policy.horizon,
                    "action_values": self.policy.action_value_history(),
                },
                "last_decision": self._last_decision,
                "navigation": self._last_navigation,
                "last_report": self._last_report,
                "perception": self._perception_summary(),
                "recent_steps": list(self._step_history)[-12:],
                "sim": self.sim.status() if self.sim is not None else None,
                "brain_bridge": {
                    "body_attached": self.body is not None,
                    "organism_attached": getattr(self.body, "organism", None) is not None,
                },
            }

    def _perception_summary(self) -> Dict[str, Any]:
        """Expose the Body boundary and interpretation, not raw model tensors.

        The simulator's exact state remains under ``sim`` as a debug oracle;
        this section is the observation and affordance view available to the
        cognitive stack.
        """
        obs = self._last_observation
        body = self._last_body_state
        if obs is None or body is None:
            return {"available": False, "note": "No Body observation recorded yet."}
        return {
            "available": True,
            "source": obs.source,
            "kind": obs.kind,
            "timestamp": obs.timestamp,
            "age_seconds": round(max(0.0, time.time() - obs.timestamp), 3),
            "text": obs.text,
            "body": body.as_dict(),
            "objects": [o.as_dict() for o in obs.scene],
            "affordances": {
                "which2act": list(self._last_affordances.get("which2act", []))[:12],
                "where2act": list(self._last_affordances.get("where2act", []))[:12],
                "how2act": list(self._last_affordances.get("how2act", []))[:16],
            },
            "ground_truth_available": isinstance(self.source, SimRobotSource),
        }

    def recent_episodes(self, limit: int = 12) -> List[Dict[str, Any]]:
        with self._lock:
            eps = list(self._episodes)[-max(1, limit):]
        out = []
        for e in eps:
            out.append({
                "step": e.step_id,
                "action": e.action.type,
                "target": e.action.target,
                "outcome": e.outcome.kind,
                "reward": round(e.reward, 4),
                "pred_error": round(e.prediction_error, 5),
                "description": e.outcome.description,
            })
        return list(reversed(out))

    def anchors_payload(self, limit: int = 40) -> Dict[str, Any]:
        """One-call anchor dump (used by the brain-side HTTP endpoints)."""
        with self.memory._lock:
            return {
                "stats": self.memory.stats(),
                "top": self.memory.top_anchors(limit=5),
                "lieux": [a.as_dict() for a in list(self.memory.lieux.values())[:limit]],
                "objets": [a.as_dict() for a in list(self.memory.objets.values())[:limit]],
                "trajectories": [a.as_dict() for a in list(self.memory.trajectories.values())[:limit]],
            }


# ── singleton per Body ───────────────────────────────────────────────────────


def get_embodied_worldmodel(body: Optional[Any] = None, **kwargs: Any) -> EmbodiedWorldModel:
    """Return one embodied world model per Body (adopt pattern)."""
    if body is not None:
        existing = getattr(body, "_worldmodel", None)
        if existing is not None:
            return existing
    wm = EmbodiedWorldModel(body=body, **kwargs)
    if body is not None:
        try:
            body._worldmodel = wm
        except Exception:
            pass
    return wm
