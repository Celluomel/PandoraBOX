"""Minimal network application for the authenticated Body WebSocket only."""
from __future__ import annotations

from fastapi import FastAPI

from core.body_bridge import body_bridge
from core.body_bridge_config import validate_bind

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_api_websocket_route("/api/interface/body/bridge", body_bridge)
