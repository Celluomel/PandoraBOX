"""Authenticated WebSocket bridge between the independent Body and Brain."""
from __future__ import annotations

import asyncio
import logging
import time

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


def _body_runtime_for_state():
    from core.state import state

    organism = getattr(getattr(state, "persona", None), "_organism", None)
    if organism is not None:
        from cognition.body_runtime import get_body_runtime

        body = get_body_runtime(organism)
        state.body_runtime = body
        return body
    body = getattr(state, "body_runtime", None)
    if body is None:
        from cognition.body_runtime import get_body_runtime

        body = get_body_runtime()
        state.body_runtime = body
    return body


def _expected_bridge_token(body, config) -> str:
    return str(
        body.config_value("BODY_BRIDGE_TOKEN", "")
        or getattr(config, "BODY_BRIDGE_TOKEN", "")
        or ""
    )


async def body_bridge(websocket: WebSocket):
    """Exchange Body observations and queued commands using bearer auth."""
    body = _body_runtime_for_state()
    from managers.settings_manager import config

    expected = _expected_bridge_token(body, config)
    supplied = websocket.headers.get("authorization", "")
    token = supplied[7:].strip() if supplied.lower().startswith("bearer ") else ""
    if not expected or token != expected:
        await websocket.close(code=1008, reason="Body bridge authentication failed")
        return

    await websocket.accept()
    send_lock = asyncio.Lock()
    sender_task = None
    device_id = "body"

    async def send(payload):
        async with send_lock:
            await websocket.send_json(payload)

    async def send_commands():
        while True:
            command = await asyncio.to_thread(body.next_bridge_command, 1.0)
            if command:
                await send(command)

    try:
        sender_task = asyncio.create_task(send_commands())
        while True:
            message = await websocket.receive_json()
            if not isinstance(message, dict):
                await send({"type": "error", "reason": "message must be an object"})
                continue
            if message.get("type") == "hello":
                device_id = str(message.get("device_id") or "body")[:80]
                body.register_bridge_device(device_id)
                await send({"type": "hello_ack", "protocol": 1, "brain": "ready"})
                continue
            if message.get("type") == "command_result":
                result = body.record_command_outcome(message)
                await send({"type": "command_result_ack", "command_id": message.get("command_id"), **result})
                continue
            if message.get("type") != "observation" or not isinstance(message.get("observation"), dict):
                await send({"type": "error", "reason": "unsupported message"})
                continue
            item = message["observation"]
            from cognition.body_runtime import BodyObservation

            observation = BodyObservation(
                source=f"remote:{str(message.get('device_id') or 'body')[:80]}:{str(item.get('source') or 'unknown')[:100]}",
                kind=str(item.get("kind") or "sensor")[:100],
                subject=str(item.get("subject") or "observation")[:160],
                value=item.get("value"),
                unit=str(item.get("unit") or "")[:40],
                confidence=float(item.get("confidence", 1.0)),
                observed_at=float(item.get("observed_at") or time.time()),
                provenance=dict(item.get("provenance") or {}),
            )
            body.publish_observation(observation, forward=False)
            await send({"type": "observation_ack", "subject": observation.subject})
    except WebSocketDisconnect:
        logger.info("[BodyBridge] remote Body disconnected")
    except Exception:
        logger.exception("[BodyBridge] connection failed")
    finally:
        body.unregister_bridge_device(device_id)
        if sender_task is not None:
            sender_task.cancel()
            await asyncio.gather(sender_task, return_exceptions=True)
