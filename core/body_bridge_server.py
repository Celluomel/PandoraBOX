"""Lifecycle helper for the isolated authenticated Body WebSocket listener."""
from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass

import uvicorn

from core.body_bridge_listener import app as bridge_app, validate_bind

logger = logging.getLogger(__name__)


@dataclass
class BodyBridgeServer:
    server: uvicorn.Server
    thread: threading.Thread


def start_body_bridge_server(settings, api_host: str, api_port: int) -> BodyBridgeServer | None:
    """Start the bridge on its own port when enabled; return None if disabled."""
    if not bool(getattr(settings, "BODY_BRIDGE_LISTEN_ENABLED", False)):
        return None

    host, port = validate_bind(
        settings.BODY_BRIDGE_LISTEN_HOST,
        settings.BODY_BRIDGE_LISTEN_PORT,
        api_host,
        api_port,
    )
    server = uvicorn.Server(uvicorn.Config(
        app=bridge_app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    ))

    def run() -> None:
        asyncio.run(server.serve())

    thread = threading.Thread(target=run, daemon=True, name="body-bridge-api")
    thread.start()
    deadline = time.monotonic() + 5.0
    while thread.is_alive() and not server.started and time.monotonic() < deadline:
        time.sleep(0.02)
    if not server.started:
        server.should_exit = True
        thread.join(timeout=1.0)
        raise RuntimeError("Body bridge listener did not start; check its bind address and port")

    logger.info(
        "Authenticated Body bridge listener → ws://%s:%d/api/interface/body/bridge",
        host,
        port,
    )
    return BodyBridgeServer(server=server, thread=thread)


def stop_body_bridge_server(listener: BodyBridgeServer | None) -> None:
    if listener is None:
        return
    listener.server.should_exit = True
    listener.thread.join(timeout=5.0)
    if listener.thread.is_alive():
        logger.warning("Body bridge listener did not stop within 5 seconds")
