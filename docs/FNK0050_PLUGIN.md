# FNK0031 / FNK0050 Body Plugins

The FNK0050 plugin is a development integration for a Freenove FNK0050
Wi-Fi quadruped. The same transport is now also exposed as an explicit
FNK0031 six-leg profile, which is the hardware currently owned for this
project. Both are deliberately disabled by default.

## Boundary

The plugin uses the Body's small robot protocol:

- `GET /health` (optional)
- `GET /sensors`
- `POST /command`

`/sensors` returns a JSON object containing the body pose, orientation,
capabilities, visible objects, carrying state, battery and timestamp. A
command has the shape `{ "type": "forward", "target": null, "params": {} }`
and returns an outcome, reward and description. The adapter is observation
only unless `FNK0050_ACTUATION_ENABLED` is explicitly enabled and the command
also passes the Body's approval path.

## Configuration

These values are stored in the Body configuration. Tokens are kept in the
local Body environment rather than committed configuration:

- `BODY_PLUGIN_ROBOT_ENABLED` (FNK0031)
- `FNK0031_URL` (falls back to the legacy `ROBOT_URL`)
- `FNK0031_TOKEN`
- `FNK0031_TIMEOUT`
- `FNK0031_POLL_INTERVAL`
- `FNK0031_SNN_ENABLED`
- `FNK0031_ACTUATION_ENABLED`
- `FNK0031_LEG_COUNT` (default `6`)

- `BODY_PLUGIN_FNK0050_ENABLED`
- `FNK0050_URL`
- `FNK0050_TOKEN`
- `FNK0050_TIMEOUT`
- `FNK0050_POLL_INTERVAL`
- `FNK0050_SNN_ENABLED`
- `FNK0050_ACTUATION_ENABLED`

The Brain discovers the plugin but does not own the Body's hardware settings.
For FNK0031, the Mega 2560 is treated as a sensor/servo endpoint; the SNN
and CPG run on the Body host and can communicate through an ESP Wi-Fi bridge.
When enabled with a URL, the Body world model selects the corresponding
FNK0031 or FNK0050 source even if its persisted development mode is still
`sim`. This makes a hardware
service easy to substitute for the simulator without changing the cognitive
core.

## SNN development path

`FNK0050_SNN_ENABLED` is a telemetry/experiment flag, not a claim that a
spiking controller is already running on the board. The next SNN increment is
to expose a timestamped locomotion stream from the board or simulator:

```json
{
  "snn": {
    "network": "izhikevich",
    "spikes": 12,
    "competence": 0.31,
    "reward": 0.04,
    "imu": {"pitch": 0.01, "roll": -0.02}
  }
}
```

That telemetry can then become a Body observation and be evaluated by the
world model without mixing motor-control learning with the Brain's language
conversation.

## FNK0031 controller now included

The Body contains an experimental `FNK0031LocomotionController`:

- a six-leg tripod CPG;
- an 18-neuron Izhikevich population;
- bounded reward-modulated STDP updates;
- pitch/roll stability input;
- persisted SNN weights under `data/body/locomotion/`.

This is not equivalent to MH-FLOCKE and has not demonstrated learned walking.
The current local plant generates heuristic tilt/progress signals; it has no
rigid-body/contact simulation, calibrated servo kinematics, fall detection, or
independent task evaluator. Those synthetic rewards therefore do not establish
locomotion competence. Synthetic scores no longer increase a competence gate;
the SNN output contribution stays disabled until independent evaluation exists.
The UI labels this as a gait/controller sandbox. A walking claim requires
repeatable trials with measured displacement, foot contacts, stability/falls,
and goal completion in a physics-backed simulator, followed by hardware
validation. The current saved weights are experimental state, not evidence of
walking skill.

The controller is called only through the approved FNK0031 action path. It
does not move a robot merely because `FNK0031_SNN_ENABLED` is enabled.

An ESP32 is a good companion for the Mega 2560: it can expose the Wi-Fi API,
relay sensor/IMU data and forward servo commands. It should not be treated as
the owner of the learned brain until timing, watchdog and emergency-stop
behaviour have been validated.
