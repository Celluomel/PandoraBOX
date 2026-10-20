"""Serialize sensor RPC calls over the local Arduino Router connection."""
from __future__ import annotations

import threading
import time
from typing import Any


_RPC_LOCK = threading.Lock()


def call_sensor_rpc(bridge: Any, method: str, *, timeout: float,
                    args: tuple[Any, ...] = ()) -> Any:
    deadline = time.monotonic() + max(0.0, float(timeout))
    if not _RPC_LOCK.acquire(timeout=max(0.0, float(timeout))):
        raise TimeoutError(f"sensor RPC queue busy before {method}")
    try:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"sensor RPC deadline expired before {method}")
        return bridge.call(method, *args, timeout=remaining)
    finally:
        _RPC_LOCK.release()
