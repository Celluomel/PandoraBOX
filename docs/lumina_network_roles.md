# Lumina Network Roles

The same Brain code can run as a master or as a child. Give each running
instance its own `config.json` in its working directory.

## Master

```json
{
  "LUMINA_NETWORK_ROLE": "master",
  "LUMINA_NETWORK_ENABLED": true,
  "LUMINA_MASTER_ID": "master",
  "LUMINA_MASTER_NAME": "Lumina",
  "LUMINA_ALLOW_CHILD_INITIATED_MESSAGES": false,
  "LUMINA_CHILDREN": [
    {"id": "flux", "name": "Flux", "url": "http://192.168.0.28:8765", "role": "child"}
  ]
}
```

Only a master instance creates `LuminaNetwork`, exposes outbound child actions,
and starts dialogue. It sends each message as an HTTP request and receives the
child answer in that request's response. No callback URL or unsolicited child
push is needed for this one-way initiated exchange.

## Child

```json
{
  "LUMINA_NETWORK_ROLE": "child",
  "LUMINA_NETWORK_ENABLED": false,
  "LUMINA_MASTER_ID": "master",
  "LUMINA_CHILDREN": [],
  "BRAIN_API_HOST": "0.0.0.0",
  "BRAIN_API_PORT": 8765
}
```

A child serves `/lumina-network/chat` and accepts requests only when
`sender_id` matches `LUMINA_MASTER_ID`; the shared API key is still required for
requests arriving from another host. Child role does not create an outbound
network manager, and its UI cannot start child dialogues. The inbound
`/lumina-network/receive` push endpoint is denied unless a master explicitly
sets `LUMINA_ALLOW_CHILD_INITIATED_MESSAGES` to `true`.

The child also accepts `/lumina-network/epistemic` updates only from the
configured master. The master sends these through the child URL and includes
the per-child shared API key; a master instance rejects epistemic updates that
would arrive from a child.

The default role is `master` to preserve existing deployments where
`LUMINA_NETWORK_ENABLED` already opted into the parent connector. Use
`standalone` to run the Brain without either network role.
