# Brain–Body cognitive harness

## Design

The Brain remains the interpreter and planner. The Body is an evidence source
and, when hardware is explicitly declared and available, an action endpoint.
The harness must make the Brain's existing competencies visible to its
conversation model and preserve their evidence boundaries.

### Existing cognitive competencies

- `GoalEngine` persists long-lived internal goals. It is not the per-request
  robot action planner.
- `goal_means_reasoning` frames practical decisions around the primary goal,
  destination, required participants/resources, alternatives and feasibility.
- `body_plan_compiler.compile_body_plan` translates a user request into an
  objective, ordered steps, target entities, required capabilities and
  constraints. `PersonaBridge.assess_body_action_request` asks the Body to
  validate that draft against its current snapshot.
- `BodyPlanRuntime.validate` checks the plan and snapshot freshness. This is a
  feasibility result in that snapshot's domain; it is not an actuator result.
- The command lifecycle records acknowledgement separately from verified
  observation. Only correlated, fresh, non-simulated post-action evidence can
  support a physical-success claim.

### Evidence and self-model contract

For each Brain turn, construct a compact functional self-model from the latest
timestamped Body evidence:

1. Identify each source and state which frame, target, and time its observation
   covers. Keep the Brain-PC camera distinct from the Body camera.
2. Report actuator inventory as declared present, declared absent, or unknown.
   Report connectivity and actuation authorization separately. Missing data is
   unknown, never an implicit yes.
3. Label modeled/simulated capabilities as simulation-only. A planner default,
   kit leg count, learned skill, or successful validation does not establish
   installed physical hardware.
4. Keep the stages distinct: interpreted objective → proposed method/steps →
   snapshot validation → operator approval → command delivery/acknowledgement
   → observed result. No stage implies the next.
5. Use the existing Brain planner for intent and ordered steps, then the Body
   validator for current scene feasibility. Do not introduce a parallel Body
   planner or a semantic sensor-classification dictionary.

## Implemented in this change

- A Brain-side evidence-derived functional self-model is injected beside the
  Body's timestamped observations.
- The final response contract explicitly distinguishes planning and
  feasibility from physical execution and requires correlated physical
  evidence before reporting success.
- The action-intent gateway catches movement requests with intervening polite
  phrasing so they reach the semantic Brain action classifier.
- Plan responses expose the analyzed objective and ordered steps, and state
  whether validation was simulation-only, physical-snapshot based, or had an
  unknown domain.
- Body publishes a robot-agnostic `body_robot_capability_inventory.v1` report
  with the active robot identity and each capability's installed, operational,
  authorized, available, hardware, and supported-action fields.
- The FNK0031 USB adapter maps its operator-declared servo inventory into that
  common contract. Brain planning gates consume the generic report and do not
  assume a hexapod; the direct FNHR command shortcut remains FNK-specific.
- Generic physical capability checks fail closed when the Body report is
  missing, stale, simulated, or incomplete. Other adapters may publish the
  same explicit contract through `publish_robot()`; world-model defaults and
  numeric affordances are not treated as installed hardware.
- The planner receives the current capability inventory in its Body snapshot.
  Required capabilities are also derived from generic action verbs
  (`navigate`/`explore` → `locomotion`; `grab`/`release`/`push` →
  `manipulation`) so the model cannot omit those actuator requirements.

## Limits

This is a software grounding contract, not proof that every language model will
follow it perfectly. Each Body adapter must report its selected hardware
inventory and refresh operational and authorization fields with provenance.
No physical robot action or Ventuno deployment is authorized by this design
or implementation.
