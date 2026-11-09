"""Lifecycle for the Brain REST API shared by full and headless launchers."""
from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass
from typing import Any

import uvicorn

logger = logging.getLogger(__name__)


@dataclass
class BrainAPIServer:
    server: uvicorn.Server
    thread: threading.Thread
    host: str
    port: int


def start_brain_api_server(
    settings: Any,
    api_app: Any = None,
    *,
    host: str | None = None,
    port: int | None = None,
) -> BrainAPIServer:
    """Start the shared Brain API and wait until its socket is listening."""
    if api_app is None:
        # Importing brain.py only constructs the API. Its boot and CLI loop are
        # protected by __main__, so this reuses precisely the headless routes.
        from brain import api as api_app

    host = str(host or getattr(settings, "BRAIN_API_HOST", "127.0.0.1") or "127.0.0.1")
    port = int(port or getattr(settings, "BRAIN_API_PORT", 8765) or 8765)
    if not 1 <= port <= 65535:
        raise ValueError("BRAIN_API_PORT must be between 1 and 65535")

    server = uvicorn.Server(uvicorn.Config(
        app=api_app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    ))

    def run() -> None:
        asyncio.run(server.serve())

    thread = threading.Thread(target=run, daemon=True, name="brain-rest-api")
    thread.start()
    deadline = time.monotonic() + 5.0
    while thread.is_alive() and not server.started and time.monotonic() < deadline:
        time.sleep(0.02)
    if not server.started:
        server.should_exit = True
        thread.join(timeout=1.0)
        raise RuntimeError(
            f"Brain REST API did not start on {host}:{port}; check for a port conflict"
        )

    logger.info("Brain REST API listening on http://%s:%d", host, port)
    return BrainAPIServer(server=server, thread=thread, host=host, port=port)


def stop_brain_api_server(listener: BrainAPIServer | None) -> None:
    if listener is None:
        return
    listener.server.should_exit = True
    listener.thread.join(timeout=5.0)
    if listener.thread.is_alive():
        logger.warning("Brain REST API did not stop within 5 seconds")
