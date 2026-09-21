# PandoraBOX Embodied Development Blueprint

Status: proposed implementation roadmap  
Owner boundary: Body owns physical perception and execution; Brain owns interpretation, intention, planning and dialogue.  
Primary test platform: the local simulated room.  
Target physical platform: FNK0031 / Arduino Mega 2560 class robot with Wi-Fi.

## 1. Purpose

This document is the implementation plan for taking PandoraBOX from a Body that
can observe a simulated scene and execute a small closed-loop task to an
embodied cognitive system that can:

1. receive a natural-language objective from the user;
2. inspect the current scene and the Body's capabilities;
3. construct a grounded, ordered and constraint-aware plan;
4. delegate executable motor sub-goals to the Body;
5. observe the result of every action;
6. revise the plan when reality differs from expectation;
7. report progress, uncertainty and failure to the user;
8. transfer the same protocol from simulation to a real robot.

The goal is not to make the Body LLM an unrestricted autonomous controller.
The goal is to create a clear, auditable division of responsibility between
the conversational Brain, the embodied Body and the physical actuator layer.

## 2. Current baseline

The repository already contains the foundations below.

### Body runtime

- Independent Body process and GUI.
- Plugin boundary for robot, simulated robot, Home Assistant and world model.
- HTTP Body host with optional Brain bridge.
- Separate Body configuration and secret handling.
- Observation polling and timestamped perception forwarding.
- Confirmation-gated external actuation path.

### Embodied world model

- Simulated grid room with Body pose, heading, objects, obstacles and goal.
- Sensorimotor episodes with reward and prediction error.
- Persistent physical memory for places, objects and trajectories.
- Learned dynamics and policy components.
- Embodied concept consolidation.
- Observable perception map and Body state in the World Model page.
- Geometric navigation guidance using object coordinates.
- Boundary and obstacle avoidance.
- Sequential simulated task:
  `to_target -> to_table -> to_target_from_table -> to_shelf`.
- Scene and goal shuffling when a new simulation is started.

### Existing limitation

The current task sequence is encoded in the simulator and the navigation layer.
The Brain does not yet send a general structured plan to the Body. The Body
does not yet expose a general objective interpreter or a formal plan execution
contract. This blueprint addresses that gap.

## 3. Design principles

### 3.1 Grounding over narration

An action is valid only when it is supported by a recent Body observation. A
language model may propose an action, but it may not invent object positions,
capabilities, success or completion.

### 3.2 Explicit state over hidden assumptions

Every plan, step, observation, action and result has an ID, timestamp, source,
status and confidence. The UI and logs must be able to answer: what did the
Brain believe, what did the Body see, what action was sent and what actually
happened?

### 3.3 Brain and Body have different jobs

The Brain handles meaning, user intent, long-horizon planning, dialogue and
trade-offs. The Body handles sensor interpretation, spatial grounding,
affordances, local navigation, actuator safety and execution feedback.

### 3.4 Learned policy is subordinate to physical safety

The learned policy can rank legal actions and improve from outcomes. It cannot
override collision checks, workspace bounds, actuator permissions, stale
observations or an emergency stop.

### 3.5 Simulation before hardware

Every new Body capability must have a local simulator or deterministic mock
before it is enabled for FNK0031. The same message contracts must be used in
both modes.

### 3.6 Reversible development

Plans can be paused, cancelled and resumed. Every state transition is
persisted. A failed experiment must not corrupt the Body's learned memory or
the user's conversation.

## 4. Target architecture

```text
User
  |
  v
Brain / PandoraBOX cognitive core
  |  intent, constraints, plan, dialogue, evaluation
  |
  |  authenticated Plan / Query / Cancel messages
  v
Body Gateway
  |  validation, permissions, leases, command routing
  |
  +--> Body LLM (optional local model)
  |      local scene interpretation and action proposal
  |
  +--> Embodied World Model
  |      scene, pose, objects, memory, dynamics, affordances
  |
  +--> Local Planner
  |      route, manipulation sequence, collision checks
  |
  +--> Actuator Adapter
         simulation | FNK0031 | future robots
  |
  v
Sensors / motors / gripper / camera / lidar
  |
  +--> timestamped observation and action outcome
```

### Ownership rules

| Concern | Owner | Brain access |
|---|---|---|
| Raw sensor polling | Body plugin | Structured observations only |
| Robot pose and object coordinates | Body world model | Read-only snapshot and stream |
| User intent | Brain | N/A |
| Long-horizon plan | Brain | Full ownership |
| Local route and safe next action | Body | Brain can inspect and constrain |
| Physical command permission | Body Gateway | Brain requests, Body validates |
| Actuator execution | Body adapter | Never direct from LLM |
| User confirmation | Brain/UI | Required by policy |
| Action result | Body | Returned to Brain and persisted |

## 5. Canonical data contracts

The first major implementation task is to create typed Python models for these
messages. JSON is the transport representation; validation must occur before
execution.

### 5.1 Body snapshot

```json
{
  "type": "body_snapshot",
  "snapshot_id": "snap-00042",
  "timestamp": 1790000000.25,
  "source": "sim_robot",
  "frame": "world",
  "pose": {"x": 4.0, "y": 2.0, "yaw": 1.5708},
  "objects": [
    {"id": "cup", "kind": "target", "x": 8.0, "y": 7.0, "radius": 0.2},
    {"id": "table", "kind": "surface", "x": 3.0, "y": 5.0, "radius": 0.6}
  ],
  "obstacles": [{"id": "pillar", "x": 5.0, "y": 4.0, "radius": 0.6}],
  "capabilities": ["navigate", "grab", "release"],
  "reliability": 0.94,
  "age_ms": 80
}
```

### 5.2 Brain plan

```json
{
  "type": "body_plan",
  "plan_id": "plan-2026-0007",
  "created_at": 1790000000.3,
  "expires_at": 1790000600.3,
  "objective": "move the cup to the marked goal",
  "source": "user",
  "required_capabilities": ["navigate", "grab", "release"],
  "constraints": {
    "avoid": ["obstacle"],
    "do_not_drop": true,
    "max_retries_per_step": 3,
    "confirmation_policy": "simulation_auto_physical_confirm"
  },
  "steps": [
    {"step_id": "s1", "verb": "navigate", "target": "cup"},
    {"step_id": "s2", "verb": "grab", "target": "cup"},
    {"step_id": "s3", "verb": "navigate", "target": "table"},
    {"step_id": "s4", "verb": "release", "target": "table"},
    {"step_id": "s5", "verb": "grab", "target": "cup"},
    {"step_id": "s6", "verb": "navigate", "target": "goal"},
    {"step_id": "s7", "verb": "release", "target": "goal"}
  ]
}
```

### 5.3 Body action proposal

```json
{
  "type": "body_action_proposal",
  "plan_id": "plan-2026-0007",
  "step_id": "s3",
  "action_id": "act-00031",
  "action": "forward",
  "target": "table",
  "reason": "forward reduces distance to table and is collision-free",
  "based_on_snapshot": "snap-00042",
  "confidence": 0.88,
  "requires_confirmation": false
}
```

### 5.4 Action result

```json
{
  "type": "body_action_result",
  "plan_id": "plan-2026-0007",
  "step_id": "s3",
  "action_id": "act-00031",
  "status": "success",
  "outcome": "moved_forward",
  "reward": 0.12,
  "timestamp": 1790000001.1,
  "snapshot_id": "snap-00043",
  "prediction_error": 0.04,
  "next_step": "s4",
  "requires_replan": false
}
```

## 6. Execution state machine

```text
DRAFT
  -> VALIDATING
  -> READY
  -> EXECUTING
  -> OBSERVING
  -> EVALUATING
       | success -> NEXT_STEP
       | mismatch -> REPLANNING
       | blocked -> RECOVERY
       | unsafe -> PAUSED
  -> COMPLETED

Any active state -> CANCELLED
Any physical safety violation -> EMERGENCY_STOP
```

### Required invariants

- Only one active plan may own an actuator lease.
- An action must reference a recent snapshot.
- A step cannot be marked complete without an outcome.
- A failed action cannot silently advance the plan.
- A stale or contradictory snapshot forces re-observation.
- `COMPLETED` is allowed only after the final postcondition is observed.
- Simulation and physical execution use the same state machine.

## 7. Development phases

### Phase 0 - Contract and observability

Goal: make the current system measurable before adding more intelligence.

Deliverables:

- `body_runtime_host/worldmodel/contracts.py` with typed contracts.
- Plan, step, snapshot and action-result IDs.
- Persisted `plans.jsonl` and `actions.jsonl`.
- World Model UI section showing current plan and active step.
- Structured event log for every transition.

Acceptance tests:

- A plan can be serialized and restored.
- Invalid target, capability and expired-plan messages are rejected.
- Every action result points to a snapshot.
- Restarting the Body restores the active plan without duplicating actions.

### Phase 1 - General sequential task engine

Goal: replace simulator-specific stage assumptions with a reusable task graph.

Deliverables:

- `TaskGraph` with ordered steps and preconditions/postconditions.
- Generic predicates: `at`, `near`, `holding`, `on_surface`, `released`,
  `clear_path`, `goal_reached`.
- Step completion based on observations, not action names.
- Retry, timeout and recovery policies.
- Current task stage exposed to Brain and UI.

Acceptance scenario:

`cup at start -> holding cup -> cup on table -> holding cup -> cup at goal`.

The exact object coordinates may change without changing the task graph.

### Phase 2 - Body local planner

Goal: let the Body solve local navigation and manipulation while respecting a
Brain plan.

Deliverables:

- Grid or graph route planner with obstacle inflation.
- Waypoint generation and route invalidation.
- Reachability and graspability checks.
- Local action selection from the current snapshot.
- Explicit reason codes: `toward_target`, `avoid_obstacle`,
  `align_for_grasp`, `recover_from_blockage`.
- Bounded replanning after map changes.

Acceptance metrics:

- No repeated identical failed action beyond configured retry limit.
- Zero intentional boundary collisions in simulation.
- Goal completion across at least 100 shuffled scenes.
- Route length no more than 1.5 times the known shortest valid route.

### Phase 3 - Body LLM adapter

Goal: use a local LLM as a grounded Body reasoning assistant without giving it
unrestricted actuator access.

The Body LLM receives only:

- current snapshot;
- active plan step;
- available capabilities;
- legal actions;
- safety constraints;
- recent failed actions;
- local planner alternatives.

It returns a validated action proposal, never a direct device command. The
deterministic gateway checks the proposal against the world model before
execution.

Fallback hierarchy:

1. deterministic safety controller;
2. local geometric planner;
3. Body LLM proposal;
4. learned policy ranking among legal actions.

The LLM is useful for interpreting ambiguous affordances and proposing
recovery strategies, but the Body remains functional without it.

### Phase 4 - Brain planning bridge

Goal: let a user ask PandoraBOX for a physical task in natural language.

Example:

> Take the cup, place it on the table, then bring it to the goal without
> touching the pillar.

Brain responsibilities:

- resolve entities against the Body snapshot;
- ask a clarification question when an object is ambiguous;
- build a plan graph;
- identify safety-sensitive steps;
- request confirmation according to policy;
- monitor Body results;
- explain progress and deviations.

Body responsibilities:

- validate that requested entities exist;
- check capabilities and reachability;
- execute the current local step;
- report grounded outcomes;
- request replanning when the scene changes.

### Phase 5 - User control and supervision

Goal: make embodied autonomy understandable and interruptible.

World Model UI additions:

- active objective and plan progress;
- current Body pose and orientation;
- current stage and next postcondition;
- target and destination markers;
- route and blocked cells;
- action proposal with reason and confidence;
- approve, pause, cancel and emergency stop controls;
- action timeline with before/after snapshots;
- replan explanation;
- simulation seed and shuffled-scene replay.

The user should be able to say:

- "pause";
- "continue";
- "cancel this plan";
- "use the other route";
- "show me why you are blocked";
- "repeat the last action".

### Phase 6 - Body hardware adapter

Goal: connect the protocol to FNK0031 without changing Brain logic.

Required robot-side protocol:

- `GET /health`;
- `GET /sensors`;
- `POST /command`;
- `POST /stop`;
- optional `GET /capabilities`;
- optional WebSocket `/stream` for low-latency telemetry.

Minimum sensor payload:

- timestamp;
- pose or odometry estimate;
- heading;
- obstacle/distance sensors;
- gripper state;
- battery and connectivity;
- firmware protocol version.

The physical adapter must implement a hard stop locally. Loss of Body or Brain
connection must not leave motors running.

### Phase 7 - World model learning

Goal: learn reusable dynamics and concepts without confusing memory with truth.

Learn separately:

- object identity and persistence;
- traversability and obstacle geometry;
- action effects;
- grasp success conditions;
- surface affordances;
- route reliability;
- failure and recovery patterns.

Each learned fact requires:

- evidence count;
- source and timestamps;
- reliability;
- positive and negative outcomes;
- map/context scope;
- stale flag;
- ability to be contradicted by new observations.

The same concept should generalize across maps only when its relation is
frame-independent, for example `solid obstacle blocks forward motion`, not
`cell (6,6) is blocked`.

### Phase 8 - Evaluation and capability promotion

Goal: distinguish a working demo from a verified embodied capability.

Capability states:

```text
PROPOSED -> IMPLEMENTED -> TESTING -> PROVISIONAL
         -> VERIFIED
         -> REGRESSED / RETIRED
```

Promotion requires:

- baseline measurement;
- repeated randomized trials;
- success and failure evidence;
- recovery evidence;
- restart/resume test;
- safety test;
- comparison against a deterministic baseline;
- persisted evaluation report.

## 8. Evaluation matrix

| Capability | Baseline | Target |
|---|---:|---:|
| Scene parsing | known simulator objects | >= 99% identity in simulator |
| Target localization | fixed map | >= 95% across shuffled maps |
| Collision avoidance | current policy | 0 avoidable collisions |
| Sequential manipulation | direct cup-to-goal | >= 90% full-sequence success |
| Recovery | no recovery | >= 80% recoverable disturbances |
| Plan persistence | restart loses active step | resume from last confirmed step |
| Action grounding | occasional stale action | 0 actions from expired snapshot |
| Physical safety | command queue only | hard stop and permission audit |
| Latency | synchronous LLM path | local action decision under configured budget |

Recommended first benchmark: 100 deterministic seeds in simulation, followed
by 100 randomized scenes with one object displacement or obstacle change during
execution.

## 9. Failure and recovery model

The Body must classify failures rather than returning generic errors.

| Failure | Immediate response | Brain response |
|---|---|---|
| Target not visible | re-observe | ask user or search |
| Target unreachable | local replan | report blocked objective |
| Obstacle appears | invalidate route | continue if safe |
| Grasp fails | reposition and retry | report after retry budget |
| Object moved | refresh world model | revise plan |
| Sensor stale | stop movement | request fresh observation |
| Body disconnected | local stop | pause plan |
| LLM unavailable | deterministic fallback | continue or explain limitation |
| Actuator fault | emergency stop | require operator intervention |

No failure may silently become a successful step.

## 10. Security and physical safety

- Keep Body tokens and robot credentials outside Git.
- Authenticate Brain-to-Body communication.
- Use short-lived plan leases and replay protection.
- Validate every command against the current capability set.
- Separate observation permissions from actuator permissions.
- Require explicit confirmation for real-world movement until trust is earned.
- Add speed, workspace and energy limits.
- Add a local emergency stop independent of the Brain.
- Record who approved every physical action.
- Never allow generated text to become an actuator command without schema
  validation.

## 11. Proposed implementation order

1. Add typed contracts and persistent plan/action records.
2. Extract the current simulator stages into a generic TaskGraph.
3. Add postcondition-based step completion and retry limits.
4. Add deterministic route planning and waypoint visibility.
5. Add Body LLM proposal endpoint with legal-action validation.
6. Add Brain plan creation from natural-language user requests.
7. Add pause/cancel/replan UI and action timeline.
8. Add randomized benchmark runner and capability reports.
9. Implement FNK0031 adapter and local emergency stop.
10. Run the same benchmark through simulation, robot simulator HTTP mode and
    the physical robot at reduced speed.

## 12. Definition of next-level embodiment

The next level is reached when a user can say:

> Take the cup, put it on the table, then bring it to the goal.

and PandoraBOX can:

1. inspect the Body's current scene;
2. identify the cup, table and goal;
3. produce a visible plan;
4. ask for confirmation when needed;
5. execute one grounded step at a time;
6. show what the Body perceives;
7. detect and explain a deviation;
8. replan without losing the original intention;
9. stop safely when uncertain;
10. prove completion through a postcondition observation;
11. preserve the experience as scoped embodied knowledge;
12. replay and evaluate the complete episode.

That is the transition from a simulated robot that moves to an embodied
cognitive system that understands what it is trying to accomplish, what it can
do, what actually happened and how to adapt.
