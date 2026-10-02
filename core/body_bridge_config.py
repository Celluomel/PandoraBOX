"""Validation for the Brain's isolated Body bridge listener settings."""
from __future__ import annotations

import ipaddress


def validate_bind(host: str, port: int, api_host: str, api_port: int) -> tuple[str, int]:
    host = str(host or "127.0.0.1").strip()
    try:
        port = int(port)
    except (TypeError, ValueError) as exc:
        raise ValueError("Bridge listen port must be an integer") from exc
    if host not in {"127.0.0.1", "0.0.0.0", "::1", "::"}:
        try:
            address = ipaddress.ip_address(host)
        except ValueError as exc:
            raise ValueError("Bridge listen host must be a literal IP address") from exc
        if not address.is_private:
            raise ValueError("Bridge listen host must be loopback or a private LAN address")
    if not 1024 <= port <= 65535:
        raise ValueError("Bridge listen port must be between 1024 and 65535")
    if port == int(api_port):
        raise ValueError("Bridge listener must use a port different from the Brain REST API")
    return host, port
