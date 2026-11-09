# Lumina Network Roles

The same Brain code can run as a master or as a child. The recommended Windows
deployment uses two folders containing the same code. Each process starts with
the normal `BrainOnly.bat` (or `start.bat`) from its folder and reads that
folder's `config.json`; the role, persona name, API port, and memory paths in
that file distinguish the instances. No role-specific launcher is required.
`LUMINA_CONFIG_PATH` remains available for deployments that intentionally use
one checkout with multiple profiles.

## Master

```json
{
  "LUMINA_NETWORK_ROLE": "master",
  "LUMINA_NETWORK_ENABLED": true,
  "LUMINA_MASTER_ID": "master",
  "LUMINA_MASTER_NAME": "Lumina",
  "LUMINA_ALLOW_CHILD_INITIATED_MESSAGES": false,
  "BRAIN_API_HOST": "127.0.0.1",
  "BRAIN_API_PORT": 8765,
  "LUMINA_CHILDREN": [
    {"id": "flux", "name": "Flux", "url": "http://127.0.0.1:8767", "role": "child"}
  ]
}
```

For the two-folder deployment, keep Lumina's master settings in the main
folder's `config.json` and the chosen child persona's settings in the child's
own `config.json`. For example, Lumina listens on 8765 and lists the child URL
at 8767; the child sets `LUMINA_NETWORK_ROLE` to `child`, its chosen
`PERSONA_NAME`, and `BRAIN_API_PORT` to 8767. Keep each folder's existing data
and configuration when syncing code. `body_runtime_host/` and
`cognition/body_runtime/` may be omitted from a child deployment that does not
use Body features.

To run both processes from a single checkout instead, use PowerShell and
separate config profiles:

```powershell
$env:LUMINA_CONFIG_PATH = 'config_Flux.json'
.\BrainOnly.bat
```

The profile files are local deployment configuration and should remain ignored
by Git. Both processes share the checkout's local secret store (`.venv/.env`),
so configure `LUMINA_NETWORK_API_KEY` there once; each process resolves it even
if its profile predates that setting. Never put the key in tracked files.

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
  "BRAIN_API_HOST": "127.0.0.1",
  "BRAIN_API_PORT": 8767,
  "MEMORY_DB_PATH": "data_flux/persona/ai_system.db",
  "MEMORY_FAISS_PATH": "data_flux/persona/faiss_index.bin",
  "MEMORY_WORLD_PATH": "data_flux/persona/world_model.json",
  "MEMORY_PERSONA_PATH": "data_flux/persona",
  "MEMORY_COGNEE_PATH": "data_flux/persona/cognee"
}
```

The separate API port and memory paths matter when both processes run on one
PC: Lumina owns loopback port 8765 and its own memory; FLUX owns loopback port
8767 and a separate, initially empty memory directory. They share source code,
not live memory or a listening socket.

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
