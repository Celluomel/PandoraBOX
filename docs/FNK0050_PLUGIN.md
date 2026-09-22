# FNK0050 Body Plugin

The FNK0050 plugin is a development integration for a Freenove FNK0050
Wi-Fi quadruped. It is deliberately disabled by default and does not require
the hardware to be present.

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

These values are stored in the Body configuration. `FNK0050_TOKEN` is kept in
the local Body environment rather than committed configuration:

- `BODY_PLUGIN_FNK0050_ENABLED`
- `FNK0050_URL`
- `FNK0050_TOKEN`
- `FNK0050_TIMEOUT`
- `FNK0050_POLL_INTERVAL`
- `FNK0050_SNN_ENABLED`
- `FNK0050_ACTUATION_ENABLED`

The Brain discovers the plugin but does not own the Body's hardware settings.
When enabled with a URL, the Body world model selects the FNK0050 source even
if its persisted development mode is still `sim`. This makes a hardware
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
