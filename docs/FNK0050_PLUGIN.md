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

## FNK0031 locomotion software status

The Body contains an experimental `FNK0031LocomotionController`:

- a six-leg tripod CPG;
- an 18-neuron Izhikevich population;
- bounded reward-modulated STDP updates;
- pitch/roll stability input;
- persisted SNN weights under `data/body/locomotion/`.

The Body now includes an optional MuJoCo-backed training experiment, installed
with the independent Body requirements. It models 18 bounded position
actuators, a floating chassis, six three-joint legs, ground contact and IMU-like
orientation. The experiment runs a CPG baseline, trains with task reward and
R-STDP, then compares paired randomized held-out episodes by displacement,
contact, tilt, effort proxy and falls. It is launched asynchronously from the
FNK0031 plugin page and sends no commands to hardware.

The local model is an explicit geometry estimate, not a measured FNK0031 CAD
model. The experiment now includes a reward-modulated plastic motor readout,
not just recurrent SNN-weight updates. However, neither of these establishes
that the policy has learned to walk. A 24-episode/8-pair run measured mean
displacement of 1.07142 m for CPG and 1.06579 m for SNN. A longer run with 240
training episodes and 32 held-out pairs measured 1.07056 m for CPG and 1.06667
m for SNN; both policies had zero falls. Both runs correctly report
`no_reliable_improvement`. Weight changes and spikes demonstrate activity, not
a learned walking skill. This is not equivalent to MH-FLOCKE and does not
establish hardware competence. The learning policy itself needs further work
before transfer. After that, the physical robot still needs measured link
geometry, servo zero/direction/range calibration, sensor validation, and safe
low-speed trials. Freenove recommends its leg-level motion interface over
commanding individual servos without calibration.

The controller is called only through the approved FNK0031 action path. It
does not move a robot merely because `FNK0031_SNN_ENABLED` is enabled.

An ESP32 is a good companion for the Mega 2560: it can expose the Wi-Fi API,
relay sensor/IMU data and forward servo commands. It should not be treated as
the owner of the learned brain until timing, watchdog and emergency-stop
behaviour have been validated.
