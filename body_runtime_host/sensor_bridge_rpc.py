"""Serialize sensor RPC calls over the local Arduino Router connection."""
from __future__ import annotations

import threading
from typing import Any


_RPC_LOCK = threading.Lock()


def call_sensor_rpc(bridge: Any, method: str, *, timeout: float) -> Any:
    with _RPC_LOCK:
        return bridge.call(method, timeout=timeout)
