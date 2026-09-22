"""A small, inspectable CPG + Izhikevich + R-STDP controller.

This is intentionally a locomotion primitive, not an LLM feature.  The CPG
provides a safe tripod rhythm; the spiking population learns bounded phase
corrections from reward and IMU stability.  The controller never sends
hardware commands itself: the FNK0031 Body adapter decides whether a command
is authorised and transports the generated joint targets.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np


class IzhikevichNetwork:
    """Regular-spiking Izhikevich population with reward-modulated STDP."""

    def __init__(self, neurons: int = 18, seed: int = 31) -> None:
        self.n = max(6, int(neurons))
        rng = np.random.default_rng(seed)
        self.a = np.full(self.n, 0.02, dtype=np.float32)
        self.b = np.full(self.n, 0.2, dtype=np.float32)
        self.c = np.full(self.n, -65.0, dtype=np.float32)
        self.d = np.full(self.n, 8.0, dtype=np.float32)
        self.v = self.c.copy()
        self.u = self.b * self.v
        self.weights = rng.normal(0.0, 0.08, (self.n, self.n)).astype(np.float32)
        np.fill_diagonal(self.weights, 0.0)
        self.pre_trace = np.zeros(self.n, dtype=np.float32)
        self.post_trace = np.zeros(self.n, dtype=np.float32)
        self.last_spikes = np.zeros(self.n, dtype=np.float32)

    def step(self, current: np.ndarray, reward: float = 0.0, dt: float = 1.0) -> np.ndarray:
        current = np.asarray(current, dtype=np.float32).reshape(-1)
        if current.size != self.n:
            current = np.resize(current, self.n).astype(np.float32)
        recurrent = self.weights @ self.last_spikes
        i = current + recurrent
        # Two half-steps are the standard stable Izhikevich Euler update.
        self.v += 0.5 * (0.04 * self.v * self.v + 5.0 * self.v + 140.0 - self.u + i) * dt
        self.v += 0.5 * (0.04 * self.v * self.v + 5.0 * self.v + 140.0 - self.u + i) * dt
        fired = self.v >= 30.0
        self.v[fired] = self.c[fired]
        self.u[fired] += self.d[fired]
        spikes = fired.astype(np.float32)
        decay = 0.95
        self.pre_trace = decay * self.pre_trace + spikes
        self.post_trace = decay * self.post_trace + spikes
        # Reward-modulated eligibility: causal pre/post coincidences only
        # alter weights when an external stability reward is supplied.
        eligibility = np.outer(self.post_trace, spikes) - np.outer(spikes, self.pre_trace)
        self.weights += np.float32(0.0008 * float(np.clip(reward, -1.0, 1.0))) * eligibility
        self.weights = np.clip(self.weights, -0.5, 0.5)
        self.last_spikes = spikes
        return spikes

    def state(self) -> Dict[str, Any]:
        return {
            "neurons": self.n,
            "spike_count": int(self.last_spikes.sum()),
            "firing_rate": float(self.last_spikes.mean()),
            "weight_mean": float(self.weights.mean()),
            "weight_std": float(self.weights.std()),
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(path, v=self.v, u=self.u, weights=self.weights,
                 pre_trace=self.pre_trace, post_trace=self.post_trace)

    def load(self, path: Path) -> bool:
        if not path.exists():
            return False
        try:
            data = np.load(path)
            for name in ("v", "u", "weights", "pre_trace", "post_trace"):
                value = getattr(self, name)
                loaded = np.asarray(data[name], dtype=np.float32)
                if loaded.shape != value.shape:
                    return False
                setattr(self, name, loaded)
            return True
        except Exception:
            return False


class TripodCPG:
    """Six-leg tripod oscillator: legs A/C/E oppose B/D/F."""

    def __init__(self, frequency_hz: float = 1.2) -> None:
        self.phase = 0.0
        self.frequency_hz = float(frequency_hz)

    def step(self, dt: float = 0.02) -> np.ndarray:
        self.phase = (self.phase + 2.0 * math.pi * self.frequency_hz * dt) % (2.0 * math.pi)
        phases = np.asarray([self.phase, self.phase + math.pi] * 3, dtype=np.float32)
        return np.sin(phases)


class FNK0031LocomotionController:
    """CPG scaffold plus learned bounded SNN correction for six legs."""

    def __init__(self, state_path: str | Path = "data/body/locomotion/fnk0031_snn.npz") -> None:
        self.cpg = TripodCPG()
        self.snn = IzhikevichNetwork(neurons=18)
        self.state_path = Path(state_path)
        self.steps = 0
        self.competence = 0.0
        self.loaded = self.snn.load(self.state_path)

    def step(self, imu: Optional[Dict[str, float]] = None, reward: float = 0.0,
             dt: float = 0.02, gait: str = "forward") -> Dict[str, Any]:
        imu = imu or {}
        pitch = float(imu.get("pitch", 0.0) or 0.0)
        roll = float(imu.get("roll", 0.0) or 0.0)
        stability = max(-1.0, min(1.0, 1.0 - (abs(pitch) + abs(roll)) / 0.8))
        total_reward = max(-1.0, min(1.0, float(reward) + 0.25 * stability))
        cpg = self.cpg.step(dt)
        input_current = np.repeat(cpg, 3) * 4.0
        input_current[::3] += np.float32(-pitch * 2.0)
        input_current[1::3] += np.float32(-roll * 2.0)
        spikes = self.snn.step(input_current, total_reward, dt=dt)
        correction = np.tanh(self.snn.weights.mean(axis=1)).reshape(6, 3)
        correction *= min(0.6, 0.05 + self.competence * 0.55)
        tripod = np.repeat(cpg, 3).reshape(6, 3)
        joints = np.clip(tripod + correction, -1.0, 1.0)
        if gait == "turn_left":
            joints[::2] *= 0.65
        elif gait == "turn_right":
            joints[1::2] *= 0.65
        self.competence = max(0.0, min(1.0, 0.995 * self.competence + 0.005 * max(0.0, total_reward)))
        self.steps += 1
        if self.steps % 100 == 0:
            self.snn.save(self.state_path)
        return {
            "joint_targets": joints.round(4).tolist(),
            "cpg": cpg.round(4).tolist(),
            "imu": {"pitch": pitch, "roll": roll},
            "reward": round(total_reward, 5),
            "competence": round(self.competence, 5),
            "step": self.steps,
            "network": self.snn.state(),
        }

