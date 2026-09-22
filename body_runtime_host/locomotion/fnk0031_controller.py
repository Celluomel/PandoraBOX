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
        self.weights -= self.weights.mean(axis=1, keepdims=True)
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
        # Treat the previous recurrent population output as presynaptic activity
        # and current firing as postsynaptic activity, preserving spike timing.
        pre_spikes = self.last_spikes.copy()
        eligibility = np.outer(self.pre_trace, spikes) - np.outer(pre_spikes, self.post_trace)
        self.weights += np.float32(0.0008 * float(np.clip(reward, -1.0, 1.0))) * eligibility
        self.weights = np.clip(self.weights, -0.5, 0.5)
        decay = 0.95
        self.pre_trace = decay * self.pre_trace + pre_spikes
        self.post_trace = decay * self.post_trace + spikes
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


class SimulatedHexapodPlant:
    """Heuristic signal source for controller visualization, not robot physics."""

    def __init__(self) -> None:
        self.pitch = 0.0
        self.roll = 0.0
        self.heading = 0.0
        self.distance = 0.0

    def step(self, gait: str, joints: np.ndarray, phase: float, dt: float) -> Dict[str, float]:
        left = float(joints[::2, 0].mean())
        right = float(joints[1::2, 0].mean())
        front = float(joints[:2, 1].mean())
        rear = float(joints[4:, 1].mean())
        moving = gait in {"forward", "backward", "turn_left", "turn_right"}
        turn = 1.0 if gait == "turn_left" else -1.0 if gait == "turn_right" else 0.0
        direction = -1.0 if gait == "backward" else 1.0

        target_roll = 0.055 * math.sin(phase * 2.0) + 0.12 * (left - right)
        target_pitch = 0.045 * math.cos(phase) + 0.10 * (rear - front)
        if not moving:
            target_roll *= 0.25
            target_pitch *= 0.25
        response = min(1.0, max(0.0, dt * 7.0))
        self.roll += (target_roll - self.roll) * response
        self.pitch += (target_pitch - self.pitch) * response
        self.heading = (self.heading + turn * dt * 1.2) % (2.0 * math.pi)
        speed = 0.18 if gait in {"forward", "backward"} else 0.0
        self.distance += speed * dt * direction

        tilt = abs(self.pitch) + abs(self.roll)
        stability = max(-1.0, 1.0 - tilt / 0.45)
        progress = 0.2 if moving and stability > 0.0 else 0.0
        reward = max(-1.0, min(1.0, 0.8 * stability + progress - (0.5 if stability < 0 else 0.0)))
        return {
            "pitch": self.pitch,
            "roll": self.roll,
            "heading": self.heading,
            "distance": self.distance,
            "stability": stability,
            "reward": reward,
        }


class CerebellarForwardModel:
    """Cerebellar-inspired predictor, not a detailed Marr-Albus-Ito circuit."""

    def __init__(self) -> None:
        self.weights = np.zeros((2, 8), dtype=np.float32)
        self.last_error = np.zeros(2, dtype=np.float32)

    @staticmethod
    def features(imu: Dict[str, float], phase: float, gait: str) -> np.ndarray:
        gait_code = {
            "forward": (1.0, 0.0, 0.0), "backward": (-1.0, 0.0, 0.0),
            "turn_left": (0.0, 1.0, 0.0), "turn_right": (0.0, -1.0, 0.0),
        }.get(gait, (0.0, 0.0, 1.0))
        return np.asarray([
            float(imu.get("pitch", 0.0)), float(imu.get("roll", 0.0)),
            math.sin(phase), math.cos(phase), *gait_code, 1.0,
        ], dtype=np.float32)

    def predict(self, features: np.ndarray) -> np.ndarray:
        return np.tanh(self.weights @ features) * np.float32(0.35)

    def learn(self, features: np.ndarray, actual: np.ndarray) -> np.ndarray:
        prediction = self.predict(features)
        self.last_error = np.asarray(actual, dtype=np.float32) - prediction
        self.weights += np.float32(0.015) * np.outer(self.last_error, features)
        np.clip(self.weights, -2.0, 2.0, out=self.weights)
        return self.last_error.copy()


class TripodCPG:
    """Tripod foot trajectory; leg order is FL, FR, ML, MR, RL, RR."""

    def __init__(self, frequency_hz: float = 1.2) -> None:
        self.phase = 0.0
        self.frequency_hz = float(frequency_hz)
        self.contact = np.ones(6, dtype=np.int8)
        self.foot_lift = np.zeros(6, dtype=np.float32)

    def step(self, dt: float = 0.02) -> np.ndarray:
        self.phase = (self.phase + 2.0 * math.pi * self.frequency_hz * dt) % (2.0 * math.pi)
        # A = L1/L3/L5 (FL/RL/MR); B = L2/L4/L6 (ML/FR/RR).
        offsets = np.asarray([0.0, math.pi, math.pi, 0.0, 0.0, math.pi], dtype=np.float32)
        phases = np.mod(self.phase + offsets, 2.0 * math.pi) / (2.0 * math.pi)
        self.contact = (phases < 0.5).astype(np.int8)
        stance_position = 1.0 - 4.0 * phases
        swing_phase = np.clip((phases - 0.5) * 2.0, 0.0, 1.0)
        swing_position = -1.0 + 2.0 * swing_phase
        self.foot_lift = np.where(self.contact == 0, np.sin(math.pi * swing_phase), 0.0).astype(np.float32)
        return np.where(self.contact == 1, stance_position, swing_position).astype(np.float32)


class FNK0031LocomotionController:
    """CPG scaffold plus learned bounded SNN correction for six legs."""

    def __init__(self, state_path: str | Path = "data/body/locomotion/fnk0031_snn.npz",
                 load_state: bool = True, seed: int = 31) -> None:
        self.cpg = TripodCPG()
        self.snn = IzhikevichNetwork(neurons=18, seed=seed)
        self._rng = np.random.default_rng(seed + 1)
        self.motor_weights = np.zeros((18, 18), dtype=np.float32)
        self.motor_eligibility = np.zeros((18, 18), dtype=np.float32)
        self.plant = SimulatedHexapodPlant()
        self.forward_model = CerebellarForwardModel()
        self._pending_forward_features: Optional[np.ndarray] = None
        self.state_path = Path(state_path)
        self.steps = 0
        self.reward_baseline = 0.0
        # Kept for state/API compatibility. Only an independent locomotion
        # evaluator may raise this; the heuristic plant cannot verify skill.
        self.competence = 0.0
        self.loaded = bool(load_state and self.snn.load(self.state_path))
        if self.loaded:
            self._load_extended_state()

    def _load_extended_state(self) -> None:
        try:
            with np.load(self.state_path) as data:
                if "cpg_phase" in data:
                    self.cpg.phase = float(data["cpg_phase"])
                if "reward_baseline" in data:
                    self.reward_baseline = float(data["reward_baseline"])
                if "motor_weights" in data and data["motor_weights"].shape == self.motor_weights.shape:
                    self.motor_weights = data["motor_weights"].astype(np.float32)
                if "forward_weights" in data and data["forward_weights"].shape == self.forward_model.weights.shape:
                    self.forward_model.weights = data["forward_weights"].astype(np.float32)
                for key in ("pitch", "roll", "heading", "distance"):
                    if key in data:
                        setattr(self.plant, key, float(data[key]))
                if "steps" in data:
                    self.steps = int(data["steps"])
        except Exception:
            pass

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            self.state_path,
            v=self.snn.v, u=self.snn.u, weights=self.snn.weights,
            pre_trace=self.snn.pre_trace, post_trace=self.snn.post_trace,
            competence=np.asarray(self.competence), cpg_phase=np.asarray(self.cpg.phase),
            forward_weights=self.forward_model.weights,
            pitch=np.asarray(self.plant.pitch), roll=np.asarray(self.plant.roll),
            heading=np.asarray(self.plant.heading), distance=np.asarray(self.plant.distance),
            steps=np.asarray(self.steps),
            reward_baseline=np.asarray(self.reward_baseline),
            motor_weights=self.motor_weights,
        )

    def step(self, imu: Optional[Dict[str, float]] = None, reward: float = 0.0,
             dt: float = 0.02, gait: str = "forward", simulate: bool = True,
             learning_mode: bool = False) -> Dict[str, Any]:
        imu = imu or {}
        external_imu = "pitch" in imu or "roll" in imu
        simulated = simulate and not external_imu
        if simulated:
            imu = {"pitch": self.plant.pitch, "roll": self.plant.roll}
        pitch = float(imu.get("pitch", 0.0) or 0.0)
        roll = float(imu.get("roll", 0.0) or 0.0)
        imu_available = "pitch" in imu or "roll" in imu
        stability = max(-1.0, min(1.0, 1.0 - (abs(pitch) + abs(roll)) / 0.8)) if imu_available else 0.0
        total_reward = max(-1.0, min(1.0, float(reward) + (0.25 * stability if simulated else 0.0)))
        reward_prediction_error = 0.0
        if learning_mode:
            reward_prediction_error = max(-1.0, min(1.0, float(reward) - self.reward_baseline))
            self.reward_baseline += 0.02 * (float(reward) - self.reward_baseline)
        moving = gait in {"forward", "backward", "turn_left", "turn_right"}
        cpg = self.cpg.step(dt) if moving else np.zeros(6, dtype=np.float32)
        if not moving:
            self.cpg.contact.fill(1)
            self.cpg.foot_lift.fill(0.0)
        if gait == "backward":
            cpg *= -1.0
        turn_direction = 1.0 if gait == "turn_left" else -1.0 if gait == "turn_right" else 0.0
        # During a turn, feet sweep along the tangent of their position around
        # the body. Keep the tripod phase intact; mirroring the stride by side
        # made the preview look like a weak forward gait instead of a pivot.
        leg_positions = np.asarray([
            (-1.0, -0.65), (1.0, -0.65), (-1.0, 0.0),
            (1.0, 0.0), (-1.0, 0.65), (1.0, 0.65),
        ], dtype=np.float32)
        foot_motion = np.zeros((6, 3), dtype=np.float32)
        if turn_direction:
            foot_motion[:, 0] = -leg_positions[:, 1] * turn_direction * cpg * 0.72
            foot_motion[:, 1] = leg_positions[:, 0] * turn_direction * cpg * 0.72
            foot_motion[:, 2] = self.cpg.foot_lift
        else:
            foot_motion[:, 1] = cpg * 0.45
            foot_motion[:, 2] = self.cpg.foot_lift
        input_current = 12.0 + np.repeat(cpg, 3) * 8.0 if moving else np.zeros(18, dtype=np.float32)
        input_current[::3] += np.float32(-pitch * 2.0)
        input_current[1::3] += np.float32(-roll * 2.0)
        # The gait clock uses seconds; Izhikevich integration uses milliseconds.
        # Retain any spike from this control frame so the live view can show it.
        neural_steps = max(1, int(round(dt * 1000.0)))
        spikes = np.zeros(self.snn.n, dtype=np.float32)
        for neural_step in range(neural_steps):
            frame_spikes = self.snn.step(
                input_current,
                reward_prediction_error if learning_mode and neural_step == neural_steps - 1 else 0.0,
                dt=1.0,
            )
            spikes = np.maximum(spikes, frame_spikes)
        # The motor readout is the plastic policy: reward-modulated eligibility
        # links recently active neurons to exploratory joint corrections.
        action_noise = self._rng.normal(0.0, 0.10, 18).astype(np.float32) if learning_mode else np.zeros(18, dtype=np.float32)
        self.motor_eligibility *= np.float32(0.96)
        if learning_mode:
            self.motor_eligibility += np.outer(spikes, action_noise)
            self.motor_weights += np.float32(0.025 * reward_prediction_error) * self.motor_eligibility
            np.clip(self.motor_weights, -0.35, 0.35, out=self.motor_weights)
        motor_activity = self.motor_weights.T @ spikes + action_noise
        correction = np.tanh(motor_activity * 2.0).reshape(6, 3)
        tripod = np.repeat(cpg, 3).reshape(6, 3)
        # No physics-backed or hardware evaluator currently validates the SNN
        # policy, so synthetic rewards must not authorize learned motor output.
        snn_weight = 0.18 if learning_mode else 0.0
        cpg_weight = 1.0 - snn_weight
        snn_correction = correction.copy()
        correction *= snn_weight
        joints = np.clip(tripod * cpg_weight + correction, -1.0, 1.0)
        if not moving:
            joints.fill(0.0)
        features = self.forward_model.features(imu, self.cpg.phase, gait)
        prediction_error = np.zeros(2, dtype=np.float32)
        if self._pending_forward_features is not None:
            prediction_error = self.forward_model.learn(
                self._pending_forward_features,
                np.asarray([pitch, roll], dtype=np.float32),
            )
        predicted_tilt = self.forward_model.predict(features)
        cerebellar_bias = np.clip(-predicted_tilt, -0.12, 0.12)
        if not moving or (not simulated and not external_imu):
            cerebellar_bias.fill(0.0)
        joints[:, 1] = np.clip(joints[:, 1] + cerebellar_bias[0], -1.0, 1.0)
        joints[:, 2] = np.clip(joints[:, 2] + cerebellar_bias[1], -1.0, 1.0)
        if not simulated:
            plant_state = {
                "pitch": pitch, "roll": roll, "stability": stability if imu_available else 0.0,
                "reward": total_reward, "heading": 0.0, "distance": 0.0,
            }
        else:
            plant_state = self.plant.step(gait, joints, self.cpg.phase, dt)
            pitch, roll = plant_state["pitch"], plant_state["roll"]
            total_reward = plant_state["reward"]
            stability = plant_state["stability"]
        self._pending_forward_features = features
        self.steps += 1
        if self.steps % 100 == 0:
            self._save_state()
        servo_targets = [
            {
                "index": (visual_leg - 1) * 3 + joint + 1,
                "leg": f"L{visual_leg}",
                "joint": joint_name,
                "target": round(float(joints[physical_leg, joint]), 4),
            }
            for visual_leg, physical_leg in enumerate((0, 2, 4, 1, 3, 5), start=1)
            for joint, joint_name in enumerate(("coxa", "femur", "tibia"))
        ]
        return {
            "joint_targets": joints.round(4).tolist(),
            "servo_count": len(servo_targets),
            "servo_targets": servo_targets,
            "cpg": cpg.round(4).tolist(),
            "contact": self.cpg.contact.tolist(),
            "foot_lift": self.cpg.foot_lift.round(4).tolist(),
            "foot_motion": foot_motion.round(4).tolist(),
            "cpg_phase": round(float(self.cpg.phase), 5),
            "spikes": spikes.astype(int).tolist(),
            "imu": {"pitch": round(pitch, 5), "roll": round(roll, 5), "source": "hardware" if external_imu else "simulated_plant" if simulated else "unavailable"},
            "reward": round(total_reward, 5),
            "reward_source": "synthetic_heuristic" if simulated else "mujoco_task_evaluator" if learning_mode else "unverified_hardware_feedback",
            "learning_evidence": "mujoco_task_reward" if learning_mode else "none",
            "reward_prediction_error": round(reward_prediction_error, 5),
            "locomotion_verified": False,
            "snn_correction": snn_correction.round(5).tolist(),
            "stability": round(stability, 5),
            "competence": round(self.competence, 5),
            "cpg_weight": round(cpg_weight, 5),
            "snn_weight": round(snn_weight, 5),
            "forward_prediction_error": prediction_error.round(5).tolist(),
            "forward_model_type": "online_linear_cerebellar_inspired",
            "forward_prediction_weights_norm": round(float(np.linalg.norm(self.forward_model.weights)), 5),
            "plant": {key: round(float(value), 5) for key, value in plant_state.items()},
            "step": self.steps,
            "network": self.snn.state(),
        }
