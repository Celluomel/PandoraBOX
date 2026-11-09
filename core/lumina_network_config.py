"""Shared address selection for Lumina peer callbacks."""
from __future__ import annotations

from urllib.parse import urlsplit


def master_callback_base_url(config) -> str:
    """Return the callback base peers can use to reach this Lumina instance.

    The default remains loopback for same-machine deployments. Cross-machine
    deployments must explicitly set ``LUMINA_MASTER_CALLBACK_URL`` to an
    address reachable by the child; this helper never advertises 0.0.0.0.
    """
    configured = str(
        getattr(config, "LUMINA_MASTER_CALLBACK_URL", "") or ""
    ).strip().rstrip("/")
    if not configured:
        port = int(getattr(config, "NICEGUI_PORT", 8080) or 8080)
        return f"http://127.0.0.1:{port}"

    parsed = urlsplit(configured)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError(
            "LUMINA_MASTER_CALLBACK_URL must be an HTTP(S) base URL "
            "without credentials, query, or fragment"
        )
    if parsed.hostname in {"0.0.0.0", "::"}:
        raise ValueError("LUMINA_MASTER_CALLBACK_URL must be reachable, not a wildcard bind address")
    try:
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            raise ValueError
    except ValueError as exc:
        raise ValueError("LUMINA_MASTER_CALLBACK_URL has an invalid port") from exc
    return configured
