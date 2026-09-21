"""Learned latent dynamics of the world (Dreamer-style, numpy-free).

    s_t     = encoder( x_t )                 # x_t = cortex features
    s_{t+1} = dyn( s_t, a_t )                # action-conditioned transition
    x_hat   = decoder( s_{t+1} )             # reconstruction (control only)
    V(s)    = value head                     # expected future utility

Training losses (the five losses from the spec):

    L = λ_dyn · ‖s_next − s_next_pred‖²          # dynamics
      + λ_rec · ‖x_next − dec(s_next)‖²          # reconstruction
      + λ_aff · BCE-style affordance-success head # affordance
      + λ_pol · TD value regression               # policy / value
      + λ_w   · weight decay                      # stability

Continuous learning: ``train_step`` is called after *every* real experience
with a small batch sampled from the replay buffer — there is no
train/inference phase boundary.
"""
from __future__ import annotations

import logging
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    TORCH_OK = True
except Exception:  # pragma: no cover - torch expected in the venv
    torch = None
    nn = None
    TORCH_OK = False


ACTION_TYPES = ["forward", "backward", "turn_left", "turn_right", "wait", "grab", "release", "push"]
ACTION_DIM = len(ACTION_TYPES) + 4  # one-hot + 4 continuous params


def encode_action(action: Dict[str, Any]) -> np.ndarray:
    """Action dict -> fixed-size vector (one-hot + params)."""
    vec = np.zeros(ACTION_DIM, dtype="float32")
    t = str(action.get("type") or "wait")
    idx = ACTION_TYPES.index(t) if t in ACTION_TYPES else ACTION_TYPES.index("wait")
    vec[idx] = 1.0
    params = action.get("params") or {}
    dx = float(params.get("dx", 0.0))
    dy = float(params.get("dy", 0.0))
    has_target = 1.0 if action.get("target") else 0.0
    kind = str(params.get("target_kind") or "")
    kind_idx = {"table": 0, "chair": 1, "target": 2, "obstacle": 3, "mobile_obstacle": 3, "object": 4, "generic": 4}.get(kind, 4)
    vec[-4] = dx
    vec[-3] = dy
    vec[-2] = has_target
    vec[-1] = kind_idx / 4.0
    return vec


def _action_to_vec(action: Any) -> np.ndarray:
    if isinstance(action, dict):
        return encode_action(action)
    if hasattr(action, "as_dict"):
        return encode_action(action.as_dict())
    if isinstance(action, str):
        return encode_action({"type": action})
    return encode_action({"type": "wait"})


class LatentWorldDynamics:
    """Encoder + transition + decoder + value head, with continuous training."""

    def __init__(
        self,
        in_dim: int,
        latent_dim: int = 32,
        hidden_dim: int = 64,
        lr: float = 3e-3,
        weights: float = 1e-4,
        save_path: Optional[str | Path] = None,
        seed: int = 7,
    ):
        self.in_dim = int(in_dim)
        self.latent_dim = int(latent_dim)
        self.save_path = Path(save_path) if save_path else None
        self.lr = float(lr)
        self.weights = float(weights)
        self._torch = None
        self._opt = None
        self._buffer: deque = deque(maxlen=4096)
        self._steps_trained = 0
        self._seed = seed
        if not TORCH_OK:  # pragma: no cover
            logger.warning("[dynamics] torch unavailable — world model dynamics disabled")
            return
        g = torch.Generator().manual_seed(seed)
        torch.manual_seed(seed)
        dev = "cpu"
        enc = nn.Sequential(
            nn.Linear(self.in_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, self.latent_dim),
        )
        dyn = nn.Sequential(
            nn.Linear(self.latent_dim + ACTION_DIM, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, self.latent_dim),
        )
        dec = nn.Sequential(
            nn.Linear(self.latent_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, self.in_dim),
        )
        value = nn.Linear(self.latent_dim, 1)
        self._torch = torch
        self._enc, self._dyn, self._dec, self._value = enc, dyn, dec, value
        self._opt = torch.optim.Adam(
            list(enc.parameters()) + list(dyn.parameters()) + list(dec.parameters()) + list(value.parameters()),
            lr=self.lr, weight_decay=self.weights,
        )
        self._load()

    # ── API ─────────────────────────────────────────────────────────────────

    @property
    def available(self) -> bool:
        return TORCH_OK and self._torch is not None

    def encode(self, x: np.ndarray) -> np.ndarray:
        if not self.available:
            return np.zeros(self.latent_dim, dtype="float32")
        with torch.no_grad():
            t = torch.as_tensor(np.asarray(x, dtype="float32").reshape(1, -1))
            s = self._enc(t)
        return s.numpy().reshape(-1).astype("float32")

    def step(self, s: np.ndarray, a: np.ndarray) -> np.ndarray:
        if not self.available:
            return np.asarray(s, dtype="float32")
        with torch.no_grad():
            st = torch.as_tensor(np.asarray(s, dtype="float32").reshape(1, -1))
            at = torch.as_tensor(np.asarray(a, dtype="float32").reshape(1, -1))
            sn = self._dyn(torch.cat([st, at], dim=1))
        return sn.numpy().reshape(-1).astype("float32")

    def decode(self, s: np.ndarray) -> np.ndarray:
        if not self.available:
            return np.zeros(self.in_dim, dtype="float32")
        with torch.no_grad():
            st = torch.as_tensor(np.asarray(s, dtype="float32").reshape(1, -1))
            xh = self._dec(st)
        return xh.numpy().reshape(-1).astype("float32")

    def value(self, s: np.ndarray) -> float:
        if not self.available:
            return 0.0
        with torch.no_grad():
            st = torch.as_tensor(np.asarray(s, dtype="float32").reshape(1, -1))
            v = self._value(st)
        return float(v.item())

    def rollout(self, s: np.ndarray, actions: Sequence[Any], horizon: int) -> Tuple[List[np.ndarray], List[float]]:
        """Imagined forward rollout in latent space (the *imagination* pillar)."""
        states: List[np.ndarray] = []
        values: List[float] = []
        cur = np.asarray(s, dtype="float32")
        for i in range(max(0, min(int(horizon), len(actions)))):
            cur = self.step(cur, _action_to_vec(actions[i]))
            states.append(cur.copy())
            values.append(self.value(cur))
        return states, values

    def counterfactual(self, s: np.ndarray, action: Any, horizon: int = 8) -> Dict[str, Any]:
        """'What would happen if I did this?' — single-action imagined rollout.

        Causal by construction: the transition is *action-conditioned*, so the
        difference between two counterfactuals from the same s isolates the
        effect of the action itself (correlation vs causation separation).
        """
        states, values = self.rollout(s, [action] * horizon, horizon)
        return {
            "action": action if isinstance(action, (str, dict)) else getattr(action, "type", "unknown"),
            "terminal_value": round(values[-1], 4) if values else 0.0,
            "mean_value": round(float(np.mean(values)), 4) if values else 0.0,
            "horizon": len(values),
            "terminal_state_norm": round(float(np.linalg.norm(states[-1])), 4) if states else 0.0,
        }

    # ── learning ────────────────────────────────────────────────────────────

    def remember(self, x: np.ndarray, a: Any, x_next: np.ndarray, reward: float, success: bool) -> None:
        self._buffer.append((
            np.asarray(x, dtype="float32").reshape(-1).copy(),
            _action_to_vec(a).copy(),
            np.asarray(x_next, dtype="float32").reshape(-1).copy(),
            float(reward),
            1.0 if success else 0.0,
        ))

    def train_step(self, batch: int = 32, epochs: int = 1) -> Optional[Dict[str, float]]:
        """One online update from the replay buffer (continuous learning)."""
        if not self.available or len(self._buffer) < 4:
            return None
        n = min(batch, len(self._buffer))
        idx = np.random.default_rng().choice(len(self._buffer), size=n, replace=False)
        xs, acts, xns, rews, succ = [], [], [], [], []
        for i in idx:
            x, a, xn, r, s = self._buffer[int(i)]
            xs.append(x); acts.append(a); xns.append(xn); rews.append(r); succ.append(s)

        Xt = self._torch.stack([self._torch.as_tensor(v, dtype=self._torch.float32) for v in xs])
        At = self._torch.stack([self._torch.as_tensor(v, dtype=self._torch.float32) for v in acts])
        Xn = self._torch.stack([self._torch.as_tensor(v, dtype=self._torch.float32) for v in xns])
        R = self._torch.tensor(rews, dtype=self._torch.float32)
        S = self._torch.tensor(succ, dtype=self._torch.float32)

        self._opt.zero_grad()
        for _ in range(max(1, epochs)):
            s = self._enc(Xt)
            s_next = self._dyn(self._torch.cat([s, At], dim=1))
            s_next_target = self._enc(Xn)

            l_dyn = self._torch.nn.functional.mse_loss(s_next, s_next_target)
            x_hat = self._dec(s_next)
            l_rec = self._torch.nn.functional.mse_loss(x_hat, Xn) * 0.1
            # affordance / success head: value should track success
            v = self._value(s_next).squeeze(-1)
            l_aff = self._torch.nn.functional.binary_cross_entropy_with_logits(v, S)
            # value bootstrap: current value should approach reward + γ·next value
            gamma = 0.9
            v_cur = self._value(s).squeeze(-1)
            with self._torch.no_grad():
                target_v = (R + gamma * self._value(s_next_target).squeeze(-1))
            l_pol = self._torch.nn.functional.mse_loss(v_cur, target_v)

            loss = l_dyn + l_rec + 0.5 * l_aff + 0.5 * l_pol
            loss.backward()
            self._opt.step()

        self._steps_trained += 1
        self._maybe_save()
        return {
            "loss": round(float(loss.item()), 6),
            "l_dyn": round(float(l_dyn.item()), 6),
            "l_rec": round(float(l_rec.item()), 6),
            "l_aff": round(float(l_aff.item()), 6),
            "l_pol": round(float(l_pol.item()), 6),
            "buffer": len(self._buffer),
            "steps_trained": self._steps_trained,
        }

    # ── persistence ─────────────────────────────────────────────────────────

    def _maybe_save(self) -> None:
        if self.save_path is None:
            return
        if self._steps_trained % 25 != 0:
            return
        self.save()

    def save(self) -> None:
        if not self.available or self.save_path is None:
            return
        try:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "in_dim": self.in_dim,
                "latent_dim": self.latent_dim,
                "enc": self._enc.state_dict(),
                "dyn": self._dyn.state_dict(),
                "dec": self._dec.state_dict(),
                "value": self._value.state_dict(),
                "steps_trained": self._steps_trained,
                "seed": self._seed,
            }
            torch.save(payload, str(self.save_path))
        except Exception as exc:
            logger.debug("[dynamics] save failed: %s", exc)

    def _load(self) -> None:
        if not self.available or self.save_path is None or not Path(self.save_path).exists():
            return
        try:
            payload = torch.load(str(self.save_path), map_location="cpu", weights_only=True)
            if int(payload.get("in_dim", 0)) != self.in_dim or int(payload.get("latent_dim", 0)) != self.latent_dim:
                logger.info("[dynamics] saved model dim mismatch — starting fresh")
                return
            self._enc.load_state_dict(payload["enc"])
            self._dyn.load_state_dict(payload["dyn"])
            self._dec.load_state_dict(payload["dec"])
            self._value.load_state_dict(payload["value"])
            self._steps_trained = int(payload.get("steps_trained", 0))
            logger.info("[dynamics] restored %d training steps from %s", self._steps_trained, self.save_path)
        except Exception as exc:
            logger.warning("[dynamics] load failed (%s) — starting fresh", exc)
