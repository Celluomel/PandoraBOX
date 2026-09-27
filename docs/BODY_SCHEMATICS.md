# PandoraBOX Body Schematics

This document describes the implemented Body boundary and the intended data
flow. It is a protocol and ownership map, not a claim that physical FNK0031
hardware is already connected.

## 1. Process separation

```mermaid
flowchart LR
    User[User / voice / chat] --> Brain[Brain process\nconversation, memory, goals\nconfigured application port]
    Brain -->|read-only observations\nvalidated plans| Connector[Body connector\nHTTP / optional WebSocket]
    Connector -->|GET context, health, sensors\nPOST validated plan| Body[Independent Body Runtime\n127.0.0.1:8766]
    Body --> BodyData[(body/config.json\nbody_venv\nworld-model state)]
    Body --> UI[Body management UI\n8766]
```

Ownership rules:

- the Body owns plugins, credentials, physical memory, geometry and actuation;
- the Brain can consume Body context but cannot rewrite Body state directly;
- the Body may run with no Brain connected;
- a physical command must be validated, auditable and confirmation-gated.

## 2. Perception fusion

```mermaid
flowchart TD
    Cam[Camera frame\nimage/video] --> Sync[Frame synchronizer\ncommon timestamp]
    Lidar[LiDAR / depth points] --> Sync
    Odom[Pose, heading, speed, IMU] --> Sync
    Cal[Camera/LiDAR calibration\nmetric coordinate frame] --> Sync
    Sync --> Frame[body_perception_frame.v2]
    Frame --> VLM[Body VLM\nscene/object description\nuncertainty]
    Frame --> Geo[Metric geometry\nclusters, clearance, tracks]
    VLM --> Assoc[Association layer\ncategory + position + distance\nconfidence]
    Geo --> Assoc
    Assoc --> WM[Embodied World Model\nmap, memory, dynamics, policy]
    WM --> BrainContext[Grounded context for Brain]
```

The VLM is advisory. It may name an object or describe a surface, but it does
not override metric geometry, collision checks, pose, speed or action legality.
Unknown or low-confidence entities are retained as uncertain evidence or
rejected from the actionable scene rather than silently becoming facts.

## 3. World-model control loop

```mermaid
flowchart TD
    Observe[Observe current frame] --> State[Build metric Body state]
    State --> Encode[Encode geometry, objects, affordances]
    Encode --> Imagine[Evaluate legal actions\nforward, turn, wait, retreat, sprint]
    Imagine --> Decide[Choose safety/speed trade-off\nwith reason and estimated cost]
    Decide --> Validate[Continuous clearance + capability checks]
    Validate -->|accepted| Execute[Sim robot or hardware gateway]
    Validate -->|rejected| Recover[Replan, wait, retreat or alert]
    Execute --> Feedback[Outcome, reward, near miss, latency]
    Recover --> Feedback
    Feedback --> Learn[Replay, dynamics update, route memory]
    Learn --> Observe
    Decide --> Telemetry[Live decision telemetry\nchosen action, cost, alternative, reason]
```

The same loop supports a simulated robot and a physical gateway. Simulation is
used for bounded evaluation and learning; it is not hardware validation.

## 4. FNK0031 transport

```mermaid
sequenceDiagram
    participant B as Body Runtime
    participant V as VENTUNO Q gateway
    participant F as FNK0031 servo board
    participant S as Sensors / IMU
    B->>V: GET /health, /capabilities
    V->>F: module discovery / health
    F-->>V: servo topology, firmware, module state
    V-->>B: normalized capabilities
    loop sensor interval
        B->>V: GET /sensors
        V->>S: read IMU, odometry, modules
        S-->>V: timestamped measurements
        V-->>B: normalized Body observation
    end
    B->>V: validated command + lease
    V->>F: servo targets / stop
    F-->>V: command outcome
    V-->>B: actuation feedback
```

The FNK0031 owns servo timing and the local hard stop. VENTUNO Q provides
networking, Linux services and optional camera/LiDAR/VLM processing. Loss of
the Body or gateway connection must leave the actuator path stopped.

## 5. Deployment flow

```mermaid
flowchart LR
    PC[PC Body interface] -->|GET /health| V[VENTUNO Q gateway]
    PC -->|POST sanitized bundle| Stage[Staging release]
    Stage --> Review[Operator review]
    Review --> Activate[Activate release marker]
    Activate --> Restart[Explicit service restart]
    Restart --> Verify[Health + module verification]
    Verify -->|failure| Rollback[Select previous release]
    Rollback --> Restart
```

Bundles exclude virtual environments, Git metadata, caches and secret values.
The target device supplies its own tokens and local environment configuration.

## 6. Evidence gates

| Gate | Evidence required | Current meaning |
|---|---|---|
| Simulation | repeated shuffled scenes, zero collisions, useful route metrics | Provisional policy evidence |
| Perception | VLM grounding precision, invented-object rate, vision/LiDAR association stability | Required before trusting semantic scene context |
| Restart/resume | persisted plan lease and next-step continuity | Software validation |
| Gateway | module health, normalized sensors, hard-stop response | Integration validation |
| Hardware | calibrated servos, IMU/odometry, slow-speed trials and physical safety | Not established by simulation |

