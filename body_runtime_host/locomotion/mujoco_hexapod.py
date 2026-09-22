"""Physics-backed FNK0031-scale hexapod sandbox and locomotion evaluation.

The geometry is an explicit initial estimate, not a measured CAD model. Link
lengths, masses, servo zeros and limits must be calibrated against the user's
assembled kit before transferring a policy to hardware.
"""
from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass
from typing import Any, Callable

import numpy as np


# Controller/servo order: front-left, front-right, middle-left, middle-right,
# rear-left, rear-right. Keep this aligned with TripodCPG and its IK inputs.
LEGS = ("L1", "L4", "L2", "L5", "L3", "L6")
HIP_X = (0.12, 0.12, 0.0, 0.0, -0.12, -0.12)
HIP_Y = (0.075, -0.075, 0.09, -0.09, 0.075, -0.075)
COXA = 0.05
FEMUR = 0.12
TIBIA = 0.14
NOMINAL_FEMUR = 0.78
NOMINAL_KNEE = 0.82
PHYSICS_DT = 0.005
CONTROL_DT = 0.02


def _leg_xml(index: int) -> str:
    name = LEGS[index]
    theta = math.atan2(HIP_Y[index], HIP_X[index])
    return f"""
    <body name="{name}_coxa" pos="{HIP_X[index]} {HIP_Y[index]} 0" euler="0 0 {theta}">
      <joint name="{name}_coxa_joint" axis="0 0 1" range="-0.65 0.65" damping="0.15"/>
      <geom name="{name}_coxa_geom" type="capsule" fromto="0 0 0 {COXA} 0 0" size="0.012" mass="0.055" rgba="0.25 0.55 0.43 1"/>
      <body name="{name}_femur" pos="{COXA} 0 0">
        <joint name="{name}_femur_joint" axis="0 1 0" range="-0.10 1.35" damping="0.18"/>
        <geom name="{name}_femur_geom" type="capsule" fromto="0 0 0 {FEMUR} 0 0" size="0.014" mass="0.075" rgba="0.42 0.72 0.56 1"/>
        <body name="{name}_tibia" pos="{FEMUR} 0 0">
          <joint name="{name}_tibia_joint" axis="0 1 0" range="-0.10 1.55" damping="0.16"/>
          <geom name="{name}_tibia_geom" type="capsule" fromto="0 0 0 {TIBIA} 0 0" size="0.010" mass="0.045" rgba="0.60 0.78 0.66 1"/>
          <geom name="{name}_foot" type="sphere" pos="{TIBIA} 0 0" size="0.018" mass="0.025" friction="1.4 0.02 0.002" rgba="0.87 0.72 0.40 1"/>
        </body>
      </body>
    </body>"""


def build_hexapod_mjcf() -> str:
    legs = "\n".join(_leg_xml(index) for index in range(6))
    actuators = "\n".join(
        f'<position name="{leg}_{joint}_motor" joint="{leg}_{joint}_joint" '
        f'kp="8" ctrllimited="true" ctrlrange="{low} {high}"/>'
        for leg in LEGS
        for joint, low, high in (
            ("coxa", -0.65, 0.65),
            ("femur", -0.10, 1.35),
            ("tibia", -0.10, 1.55),
        )
    )
    return f"""<mujoco model="fnk0031_hexapod_estimate">
      <compiler angle="radian" autolimits="true"/>
      <option timestep="{PHYSICS_DT}" gravity="0 0 -9.81" integrator="implicitfast" cone="elliptic"/>
      <size njmax="2000" nconmax="400"/>
      <default><joint limited="true"/><geom condim="4" friction="1.2 0.02 0.002" solref="0.006 1" solimp="0.94 0.99 0.001"/></default>
      <worldbody>
        <light pos="0 0 2" dir="0 0 -1" diffuse="0.8 0.8 0.8"/>
        <geom name="ground" type="plane" size="4 4 0.1" rgba="0.18 0.21 0.19 1"/>
        <body name="torso" pos="0 0 0.255">
          <freejoint name="root"/>
          <geom name="chassis" type="box" size="0.105 0.075 0.026" mass="0.72" rgba="0.16 0.31 0.24 1"/>
          <site name="imu" pos="0 0 0"/>
          {legs}
        </body>
      </worldbody>
      <actuator>{actuators}</actuator>
    </mujoco>"""


@dataclass
class LocomotionEpisode:
    policy: str
    steps: int
    duration_s: float
    displacement_m: float
    mean_forward_speed_m_s: float
    mean_abs_pitch_rad: float
    mean_abs_roll_rad: float
    mean_foot_contacts: float
    energy_proxy: float
    fell: bool
    completed: bool
    return_value: float
    neural_spike_events: int
    weight_change_l1: float
    motor_readout_change_l1: float


class MuJoCoHexapodSim:
    """Headless MuJoCo model with contact, free-body dynamics and 18 servos."""

    def __init__(self, friction: float = 1.2) -> None:
        try:
            import mujoco
        except ImportError as exc:
            raise RuntimeError("MuJoCo is not installed; run start_body.bat again to install Body dependencies") from exc
        self.mj = mujoco
        self.model = mujoco.MjModel.from_xml_string(build_hexapod_mjcf())
        self.data = mujoco.MjData(self.model)
        self.model.geom_friction[0, 0] = float(friction)
        self.actuator_ids = np.asarray([
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, f"{leg}_{joint}_motor")
            for leg in LEGS
            for joint in ("coxa", "femur", "tibia")
        ], dtype=np.int32)
        self.joint_qpos = np.asarray([
            self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, f"{leg}_{joint}_joint")]
            for leg in LEGS
            for joint in ("coxa", "femur", "tibia")
        ], dtype=np.int32)
        self.foot_geom_ids = {
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, f"{leg}_foot") for leg in LEGS
        }
        self.reset()

    def reset(self) -> None:
        self.mj.mj_resetData(self.model, self.data)
        self.data.qpos[2] = 0.255
        self.data.qpos[3:7] = (1.0, 0.0, 0.0, 0.0)
        self.data.qpos[self.joint_qpos] = np.tile((0.0, NOMINAL_FEMUR, NOMINAL_KNEE), 6)
        self.data.ctrl[self.actuator_ids] = self.data.qpos[self.joint_qpos]
        self.mj.mj_forward(self.model, self.data)
        self.start_x = float(self.data.xpos[self.model.body("torso").id, 0])

    def observe(self) -> dict[str, float]:
        torso = self.model.body("torso").id
        rotation = self.data.xmat[torso].reshape(3, 3)
        pitch = math.atan2(-rotation[2, 0], math.hypot(rotation[0, 0], rotation[1, 0]))
        roll = math.atan2(rotation[2, 1], rotation[2, 2])
        return {
            "x": float(self.data.xpos[torso, 0]),
            "pitch": pitch,
            "roll": roll,
            "height": float(self.data.xpos[torso, 2]),
            "forward_velocity": float(self.data.qvel[0]),
        }

    def contact_count(self) -> int:
        contacts: set[int] = set()
        for index in range(self.data.ncon):
            contact = self.data.contact[index]
            if contact.geom1 in self.foot_geom_ids:
                contacts.add(int(contact.geom1))
            if contact.geom2 in self.foot_geom_ids:
                contacts.add(int(contact.geom2))
        return len(contacts)

    @staticmethod
    def inverse_kinematics(leg: int, stride: float, lift: float) -> np.ndarray:
        """Approximate 3-DOF leg IK; output joint radians in local order."""
        hx, hy = HIP_X[leg], HIP_Y[leg]
        base_heading = math.atan2(hy, hx)
        nominal_reach = COXA + FEMUR * math.cos(NOMINAL_FEMUR) + TIBIA * math.cos(NOMINAL_FEMUR + NOMINAL_KNEE)
        foot_x = hx + math.cos(base_heading) * nominal_reach + stride
        foot_y = hy + math.sin(base_heading) * nominal_reach
        dx, dy = foot_x - hx, foot_y - hy
        yaw = math.atan2(dy, dx) - base_heading
        radial = max(0.04, math.hypot(dx, dy) - COXA)
        z = -0.22 + float(np.clip(lift, 0.0, 1.0)) * 0.045
        distance2 = radial * radial + z * z
        cos_knee = float(np.clip((distance2 - FEMUR**2 - TIBIA**2) / (2 * FEMUR * TIBIA), -0.999, 0.999))
        knee = math.acos(cos_knee)
        femur = math.atan2(-z, radial) - math.atan2(TIBIA * math.sin(knee), FEMUR + TIBIA * math.cos(knee))
        return np.asarray((yaw, femur, knee), dtype=np.float64)

    def targets_from_gait(self, cpg: np.ndarray, lift: np.ndarray, correction: np.ndarray | None = None,
                          learned_mix: float = 0.0) -> np.ndarray:
        correction = np.zeros((6, 3), dtype=np.float64) if correction is None else np.asarray(correction).reshape(6, 3)
        targets = np.vstack([
            self.inverse_kinematics(i, float(cpg[i]) * 0.045, float(lift[i]))
            for i in range(6)
        ])
        targets += np.clip(learned_mix, 0.0, 0.25) * correction * np.asarray((0.25, 0.20, 0.20))
        targets[:, 0] = np.clip(targets[:, 0], -0.65, 0.65)
        targets[:, 1] = np.clip(targets[:, 1], -0.10, 1.35)
        targets[:, 2] = np.clip(targets[:, 2], -0.10, 1.55)
        return targets.reshape(18)

    def step(self, joint_targets: np.ndarray) -> dict[str, Any]:
        targets = np.asarray(joint_targets, dtype=np.float64).reshape(18)
        self.data.ctrl[self.actuator_ids] = targets
        self.mj.mj_step(self.model, self.data, nstep=round(CONTROL_DT / PHYSICS_DT))
        state = self.observe()
        state["foot_contacts"] = self.contact_count()
        state["fallen"] = bool(state["height"] < 0.13 or abs(state["pitch"]) > 1.0 or abs(state["roll"]) > 1.0)
        state["displacement_m"] = state["x"] - self.start_x
        state["energy_proxy"] = float(np.square(self.data.actuator_force).sum() * CONTROL_DT)
        state["reward"] = float(
            8.0 * (state["x"] - self._last_x)
            + 0.025 * state["foot_contacts"]
            - 0.05 * (abs(state["pitch"]) + abs(state["roll"]))
            - 0.0005 * state["energy_proxy"]
            - (1.0 if state["fallen"] else 0.0)
        )
        self._last_x = state["x"]
        return state

    def start_episode(self) -> None:
        self.reset()
        self._last_x = self.start_x


def run_episode(controller: Any, policy: str, steps: int = 250, seed: int = 0) -> LocomotionEpisode:
    """Run a measured straight-walking episode using actual contact dynamics."""
    rng = random.Random(seed)
    sim = MuJoCoHexapodSim(friction=rng.uniform(0.9, 1.5))
    sim.start_episode()
    controller.cpg.phase = rng.uniform(0.0, 2.0 * math.pi)
    controller.snn.v = controller.snn.c.copy()
    controller.snn.u = controller.snn.b * controller.snn.v
    controller.snn.pre_trace.fill(0.0)
    controller.snn.post_trace.fill(0.0)
    controller.snn.last_spikes.fill(0.0)
    pitch_values: list[float] = []
    roll_values: list[float] = []
    contact_values: list[float] = []
    energy = 0.0
    returns = 0.0
    spike_events = 0
    initial_weights = controller.snn.weights.copy()
    initial_motor_weights = controller.motor_weights.copy()
    last_reward = 0.0
    fall = False
    actual_steps = 0
    for _ in range(max(1, int(steps))):
        observation = sim.observe()
        state = controller.step(
            imu={"pitch": observation["pitch"], "roll": observation["roll"]},
            reward=last_reward,
            dt=CONTROL_DT,
            gait="forward",
            simulate=False,
            learning_mode=policy == "snn",
        )
        spike_events += int(sum(state["spikes"]))
        targets = sim.targets_from_gait(
            np.asarray(state["cpg"]), np.asarray(state["foot_lift"]),
            np.asarray(state["snn_correction"]), learned_mix=0.18 if policy == "snn" else 0.0,
        )
        outcome = sim.step(targets)
        last_reward = outcome["reward"]
        returns += last_reward
        energy += outcome["energy_proxy"]
        pitch_values.append(abs(outcome["pitch"]))
        roll_values.append(abs(outcome["roll"]))
        contact_values.append(outcome["foot_contacts"])
        actual_steps += 1
        if outcome["fallen"]:
            fall = True
            break
    final = sim.observe()
    duration = actual_steps * CONTROL_DT
    displacement = final["x"] - sim.start_x
    return LocomotionEpisode(
        policy=policy,
        steps=actual_steps,
        duration_s=round(duration, 4),
        displacement_m=round(displacement, 5),
        mean_forward_speed_m_s=round(displacement / max(duration, 1e-6), 5),
        mean_abs_pitch_rad=round(float(np.mean(pitch_values)) if pitch_values else 0.0, 5),
        mean_abs_roll_rad=round(float(np.mean(roll_values)) if roll_values else 0.0, 5),
        mean_foot_contacts=round(float(np.mean(contact_values)) if contact_values else 0.0, 3),
        energy_proxy=round(energy, 5),
        fell=fall,
        completed=not fall and displacement >= 0.5,
        return_value=round(returns, 5),
        neural_spike_events=spike_events,
        weight_change_l1=round(float(np.abs(controller.snn.weights - initial_weights).sum()), 7),
        motor_readout_change_l1=round(float(np.abs(controller.motor_weights - initial_motor_weights).sum()), 7),
    )


def run_training_experiment(state_path: str, training_episodes: int = 24,
                            evaluation_episodes: int = 8, steps_per_episode: int = 250,
                            on_progress: Callable[[dict[str, Any]], None] | None = None) -> dict[str, Any]:
    """Train online with R-STDP, then compare against a fresh CPG baseline."""
    from .fnk0031_controller import FNK0031LocomotionController

    baseline = []
    total = evaluation_episodes * 2 + training_episodes
    completed = 0
    for i in range(evaluation_episodes):
        baseline.append(asdict(run_episode(FNK0031LocomotionController(
            state_path=f"{state_path}.baseline-{i}", load_state=False, seed=31
        ), "cpg", steps_per_episode, i)))
        completed += 1
        if on_progress:
            on_progress({"phase": "baseline", "completed": completed, "total": total})
    learner = FNK0031LocomotionController(state_path=state_path, load_state=False, seed=31)
    for episode in range(training_episodes):
        run_episode(learner, "snn", steps_per_episode, episode)
        completed += 1
        if on_progress:
            on_progress({"phase": "training", "completed": completed, "total": total})
    learner._save_state()
    learned = []
    for i in range(evaluation_episodes):
        learned.append(asdict(run_episode(learner, "snn", steps_per_episode, i)))
        completed += 1
        if on_progress:
            on_progress({"phase": "evaluation", "completed": completed, "total": total})
    baseline_mean = float(np.mean([item["return_value"] for item in baseline]))
    learned_mean = float(np.mean([item["return_value"] for item in learned]))
    delta = learned_mean - baseline_mean
    relative = delta / max(abs(baseline_mean), 1e-6)
    baseline_distance = float(np.mean([item["displacement_m"] for item in baseline]))
    learned_distance = float(np.mean([item["displacement_m"] for item in learned]))
    baseline_falls = sum(bool(item["fell"]) for item in baseline)
    learned_falls = sum(bool(item["fell"]) for item in learned)
    displacement_gain = learned_distance / max(abs(baseline_distance), 1e-6) - 1.0
    candidate_improvement = displacement_gain >= 0.03 and delta > 0.0 and learned_falls <= baseline_falls
    return {
        "simulator": "MuJoCo",
        "model": "FNK0031-scale estimated 18-actuator hexapod",
        "model_calibration": "estimated_geometry_requires_robot_measurements",
        "status": "candidate_simulation_improvement" if candidate_improvement else "no_reliable_improvement",
        "verified_hardware_skill": False,
        "training_episodes": training_episodes,
        "evaluation_episodes_per_policy": evaluation_episodes,
        "steps_per_episode": steps_per_episode,
        "baseline_mean_return": round(baseline_mean, 5),
        "snn_mean_return": round(learned_mean, 5),
        "return_delta": round(delta, 5),
        "relative_change": round(relative, 5),
        "displacement_change": round(displacement_gain, 5),
        "baseline_mean_displacement_m": round(baseline_distance, 5),
        "snn_mean_displacement_m": round(learned_distance, 5),
        "baseline_falls": baseline_falls,
        "snn_falls": learned_falls,
        "minimum_displacement_improvement": 0.03,
        "baseline": baseline,
        "snn": learned,
        "next_hardware_requirement": "calibrate joint zero/direction/range and link geometry before transfer",
    }
