# Body Runtime deployment to VENTUNO Q

The PC Body interface can detect a VENTUNO Q gateway through its authenticated
`GET /health` endpoint and stage a portable Body Runtime bundle through
`POST /deploy`.

The bundle contains the Body host, launch files, requirements, sanitized
`data/body/config.json`, and optionally learned world-model files. It never
contains `.venv`, `venv`, `body_venv`, Git metadata, caches, or token values.
The target operator must provide gateway, board, Home Assistant, and Body LLM
secrets through the VENTUNO environment or its local secret store.

## Enable staging on VENTUNO

Start the gateway with deployment explicitly enabled:

```sh
VENTUNO_DEPLOY_ENABLED=1 VENTUNO_GATEWAY_TOKEN='change-me' ./start_ventuno_gateway.sh
```

The gateway writes validated bundles to the staging directory. It does not
execute files. The interface can then explicitly activate a staged release by
updating the `current` release marker; it still does not restart the service.
Restart remains an explicit operator step on the VENTUNO Linux side.

## Use the Body interface

Open the independent Body page, enter the VENTUNO gateway URL and token, then:

1. **Detect VENTUNO Q** checks `/health` and confirms the FNK0031 servo-board
   actuator path.
2. Select **Include learned world-model files** only when the learned state is
   wanted on the target.
3. **Stage Body bundle** uploads the sanitized ZIP to `/deploy`.
4. **Activate staged bundle** switches the VENTUNO release marker after a
   confirmation. Restart the Body service explicitly afterward.
5. **Restart and verify Body** restarts the configured systemd service and
   waits for the Body `/health` endpoint. If it fails, the previous active
   release is selected and the service is restarted once more.

Set `PANDORABOX_BODY_SERVICE` and `PANDORABOX_BODY_HEALTH_URL` on VENTUNO to
match the installed service. The default values are `pandorabox-body` and
`http://127.0.0.1:8766/health`.

The FNK0031 remains the motor and servo controller. VENTUNO Q is the Linux
gateway, network endpoint, and optional edge-inference host.
