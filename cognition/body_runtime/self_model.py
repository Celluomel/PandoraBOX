"""Evidence-derived functional self-model for Brain grounding.

The model deliberately separates observed sensors, declared hardware, modeled
simulation capabilities, and command outcomes. It summarizes evidence; it does
not infer that a device exists merely because a planner can model it.
"""
from __future__ import annotations

import time
from typing import Any, Iterable

from cognition.body_runtime.robot_capabilities import latest_observations, robot_capability_report


def body_functional_self_model(
    observations: Iterable[dict[str, Any]], *, now: float | None = None
) -> list[str]:
    """Return concise, timestamp-aware capability facts for the cognitive prompt."""
    current = time.time() if now is None else float(now)

    def stamp(item: dict[str, Any]) -> float:
        try:
            return float(item.get("observed_at") or 0.0)
        except (TypeError, ValueError, OverflowError):
            return 0.0

    observations = list(observations)
    latest = latest_observations(observations)

    lines = [
        "FUNCTIONAL SELF-MODEL (derived from current Body evidence; not a personality claim):",
        "Use this model to explain what each source measures and what actions are actually available. "
        "A planner's modeled capability is not proof of installed hardware.",
        "- Brain planning capability: the existing action planner can interpret an objective and destination, produce ordered steps with required capabilities/constraints, and validate them against a Body snapshot. Planning or feasibility validation is not execution.",
    ]

    inventory = latest.get("robot.capability_inventory")
    inventory_value = inventory.get("value") if isinstance(inventory, dict) else None
    if isinstance(inventory_value, dict):
        inventory_age = max(0.0, current - stamp(inventory)) if stamp(inventory) else None
        inventory_freshness = f"age={inventory_age:.1f}s" if inventory_age is not None else "age unknown"
        lines.append(
            f"- Active robot profile reported by Body: {inventory_value.get('robot_model') or inventory_value.get('robot_id') or 'unnamed'}; "
            f"inventory source={inventory_value.get('inventory_source') or 'unknown'}; {inventory_freshness}; "
            f"simulated={bool(inventory_value.get('simulated', False))}."
        )
        capabilities = inventory_value.get("capabilities")
        if isinstance(capabilities, dict):
            for name, record in sorted(capabilities.items()):
                if not isinstance(record, dict):
                    continue
                state = "ready" if robot_capability_report(observations, name, now=current).get("ready") else "not established/ready"
                actions = record.get("supported_actions")
                action_text = "; actions=" + ", ".join(str(action) for action in actions[:8]) if isinstance(actions, list) and actions else ""
                lines.append(
                    f"- Robot capability {name}: {state}; installed={record.get('installed', 'unknown')}; "
                    f"operational={record.get('operational', 'unknown')}; authorized={record.get('authorized', 'unknown')}{action_text}."
                )
    else:
        lines.append("- Robot profile/capability inventory: unknown; Body has not supplied a current structured report. Do not infer hardware from the simulator or robot name.")

    # Keep controller state visible even when a separate robot inventory is
    # present. Inventory and USB status answer different questions and must not
    # be silently collapsed into a generic claim that motors are ready.
    controller = latest.get("fnk0031.usb_status")
    controller_value = controller.get("value") if isinstance(controller, dict) else None
    if isinstance(controller_value, dict):
        observed_at = stamp(controller)
        age = max(0.0, current - observed_at) if observed_at else None
        age_note = f"age={age:.1f}s" if age is not None else "age unknown"
        connected = controller_value.get("connected") is True
        motors = controller_value.get("servo_motors_installed")
        hardware = "absent" if motors is False else "installed" if motors is True else "unknown"
        lines.append(
            f"- FNK0031 controller: USB {'connected' if connected else 'not confirmed connected'}; "
            f"servo motors {hardware} per Body hardware inventory ({age_note})."
        )
        lines.append(
            "- Actuation enabled is only a software authorization flag. It does not mean motors are installed, powered, or moving. "
            "If servo inventory is absent, physical locomotion is unavailable regardless of that flag."
        )
        readiness = robot_capability_report(observations, "locomotion", now=current)
        lines.append(
            "- Physical locomotion: "
            + ("available according to fresh installed/operational/authorized evidence; this does not prove movement occurred"
               if readiness["ready"] and motors is True
               else "unavailable because servo motors are declared absent"
               if motors is False
               else "not established because installed/operational/authorized hardware evidence is incomplete")
            + "."
        )
        supported = controller_value.get("supported_actions")
        if isinstance(supported, list) and supported:
            lines.append("- FNK controller command primitives (not proof of physical capability): " + ", ".join(str(value) for value in supported[:12]) + ".")
        leg_state = controller_value.get("estimated_leg_state")
        if isinstance(leg_state, dict):
            measured = controller_value.get("estimated_state_is_measured") is True or leg_state.get("measured_feedback") is True
            angle_rows = []
            for leg in leg_state.get("legs", []):
                if isinstance(leg, dict) and isinstance(leg.get("joint_angles_deg"), (list, tuple)):
                    angle_rows.append(f"L{leg.get('leg', '?')}={list(leg['joint_angles_deg'])}")
            lines.append(
                "- FNHR joint angles: "
                + ("measured feedback" if measured else "command-derived estimates only")
                + ("; " + "; ".join(angle_rows) if angle_rows else "")
                + (". Physical servo angles are not applicable because servos are declared absent." if motors is False else ".")
            )
        elif motors is False:
            lines.append("- Physical servo angles: not applicable; servos are absent. Do not substitute IMU roll/pitch/yaw or synthetic zero-degree measurements.")
    elif not isinstance(inventory_value, dict):
        lines.append("- Controller status: unavailable; do not infer motor installation, power, readiness, joint angles, or movement.")

    world = latest.get("body.world_model")
    world_value = world.get("value") if isinstance(world, dict) else None
    if isinstance(world_value, dict) and world_value.get("simulated_only") is True:
        lines.append("- Scene/pose/capabilities from the current world-model snapshot are simulation-only; they do not establish physical location, objects, or actuators.")
    elif isinstance(world_value, dict):
        lines.append("- A non-simulation Body world-model snapshot is present; use only its timestamped fields and provenance, and do not treat its capability fields as measured joint/contact feedback.")
    else:
        lines.append("- No current Body world-model snapshot establishes scene geometry or physical pose.")

    sensors = sorted(
        subject for subject in latest
        if subject.startswith("sensor.")
    )
    lines.append(
        "- Available sensor channels in this snapshot: " + (", ".join(sensors) if sensors else "none") + "."
    )
    lines.extend([
        "- Interpret every observation only for its named source, target, frame, and timestamp; a detection label is not a complete scene description, and sensor proximity is not an object association.",
        "- Distinguish planning/finding a feasible method, approval, delivery acknowledgement, simulation execution, and physically observed outcome. Never claim movement without correlated fresh physical evidence.",
    ])

    outcomes = [item for item in latest.values() if item.get("kind") == "actuation_feedback"]
    if outcomes:
        outcome = max(outcomes, key=stamp)
        provenance = outcome.get("provenance") if isinstance(outcome.get("provenance"), dict) else {}
        observed_at = stamp(outcome)
        age = max(0.0, current - observed_at) if observed_at else float("inf")
        lines.append(
            f"- Latest command evidence: {outcome.get('subject')} status={provenance.get('command_status', outcome.get('value', 'unknown'))}; "
            f"verification={provenance.get('verification_status', 'unknown')}; age={age:.1f}s."
        )
    else:
        lines.append("- No command outcome is present in the current Body snapshot; do not report a recent action as completed.")
    return lines
