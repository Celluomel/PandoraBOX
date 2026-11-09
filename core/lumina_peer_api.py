"""Shared HTTP routes for Lumina-to-Lumina peer conversations.

Mounted by both the full NiceGUI application and the headless Brain runner so
the same peer protocol is available in either deployment mode.
"""
from __future__ import annotations

import logging
import hmac
import ipaddress
import uuid

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger(__name__)
router = APIRouter()


def _authorize_peer_request(request: Request, body: dict | None = None) -> None:
    """Require a shared peer key off-host; allow keyless loopback development."""
    from managers.settings_manager import config

    expected = str(getattr(config, "LUMINA_NETWORK_API_KEY", "") or "")
    presented = str((body or {}).get("api_key") or "")
    headers = getattr(request, "headers", {}) or {}
    if not presented:
        presented = str(headers.get("x-lumina-api-key", "") or "")
    if not presented:
        auth = str(headers.get("authorization", "") or "")
        if auth.lower().startswith("bearer "):
            presented = auth[7:].strip()

    client = getattr(request, "client", None)
    host = str(getattr(client, "host", "") or "").strip().lower()
    try:
        is_loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        is_loopback = host == "localhost"

    if not expected:
        if is_loopback:
            return
        raise HTTPException(
            status_code=503,
            detail="Remote Lumina peer access requires LUMINA_NETWORK_API_KEY",
        )
    if presented and hmac.compare_digest(presented, expected):
        return
    raise HTTPException(status_code=401, detail="Invalid Lumina peer API key")


@router.post("/lumina-network/chat")
async def lumina_network_chat(request: Request):
    from core.state import state
    from managers.settings_manager import config

    body = await request.json()
    _authorize_peer_request(request, body)
    role = str(getattr(config, "LUMINA_NETWORK_ROLE", "master") or "master").strip().lower()
    if role != "child":
        raise HTTPException(403, "Peer chat endpoint is enabled only for a configured child Brain")
    text = str(body.get("text", "") or "").strip()
    sender_id = str(body.get("sender_id", "lumina_master") or "lumina_master")
    sender_name = str(body.get("sender_name", "Master") or "Master")
    expected_master_id = str(getattr(config, "LUMINA_MASTER_ID", "master") or "master")
    if sender_id != expected_master_id:
        raise HTTPException(403, "This child accepts cognitive turns only from its configured master")
    conversation_id = str(body.get("conversation_id") or uuid.uuid4().hex)

    # A workspace snapshot is an explicitly distinct peer percept, not a
    # conversational turn. Keep its historical behavior in both runtimes.
    if body.get("message_type") == "workspace_snapshot":
        if not state.ready or not state.persona:
            raise HTTPException(503, "Brain not ready")
        snapshot = body.get("snapshot") or {}
        shared_focus = str(snapshot.get("focus") or "").strip()
        organism = getattr(state.persona, "_organism", None)
        if organism is None or not shared_focus:
            return {
                "response": "",
                "sender_id": "flux",
                "sender_name": "Flux",
                "conversation_id": conversation_id,
            }
        try:
            from cognition.universal_connector import Percept, get_universal_connector
            get_universal_connector(organism).perceive(Percept(
                modality="peer_cognition",
                source="lumina_master",
                payload=shared_focus[:200],
                confidence=0.6,
                salience=0.5,
                provenance={"exchange": "workspace_snapshot", "sender": sender_name},
            ))
        except Exception as exc:
            logger.debug("Peer workspace snapshot percept failed: %s", exc)

        flux_focus = ""
        try:
            from cognition.recursive_deliberation import deliberate
            deliberate(organism, shared_focus)
            workspace = getattr(organism, "workspace", None)
            if workspace is not None:
                flux_focus = workspace.get_state().focus or ""
        except Exception as exc:
            logger.debug("Peer workspace snapshot deliberation failed: %s", exc)

        from managers.settings_manager import config
        child_persona = getattr(config, "PERSONA_NAME", "Flux")
        return {
            "response": flux_focus,
            "sender_id": child_persona.lower().replace(" ", "_"),
            "sender_name": child_persona,
            "conversation_id": conversation_id,
        }

    if not text:
        raise HTTPException(400, "text required")
    if not state.ready or not state.persona:
        raise HTTPException(503, "Brain not ready")

    from cognition.peer_conversation import PeerTurnUnavailable, peer_conversation_store
    try:
        response_text = await peer_conversation_store.generate_reply(
            state.persona,
            sender_id=sender_id,
            sender_name=sender_name,
            conversation_id=conversation_id,
            text=text,
            include_trace=True,
        )
    except PeerTurnUnavailable as exc:
        logger.warning(
            "Peer-scoped turn failed peer=%s conversation=%s: %s",
            sender_id, conversation_id, exc,
        )
        raise HTTPException(503, "Peer cognitive response unavailable") from exc

    cognitive_trace = None
    if isinstance(response_text, dict):
        cognitive_trace = response_text.get("cognitive_trace")
        response_text = str(response_text.get("response", ""))

    from managers.settings_manager import config
    child_persona = getattr(config, "PERSONA_NAME", "Child")
    logger.info(
        "Peer response %s → %s: %r → %r",
        sender_name, child_persona, text[:40], response_text[:40],
    )
    return {
        "response": response_text.strip(),
        "sender_id": child_persona.lower().replace(" ", "_"),
        "sender_name": child_persona,
        "conversation_id": conversation_id,
        "cognitive_trace": cognitive_trace,
    }


@router.post("/lumina-network/receive")
async def lumina_network_receive(request: Request):
    from core.state import state
    from managers.settings_manager import config

    body = await request.json()
    _authorize_peer_request(request, body)
    role = str(getattr(config, "LUMINA_NETWORK_ROLE", "master") or "master").strip().lower()
    if role != "master" or not bool(
        getattr(config, "LUMINA_ALLOW_CHILD_INITIATED_MESSAGES", False)
    ):
        raise HTTPException(403, "Child-initiated messages are disabled for this Brain topology")
    network = getattr(state, "lumina_network", None)
    if not network:
        raise HTTPException(503, "LuminaNetwork not enabled")
    response = await network.receive_from_child(body)
    return {"response": response}


@router.get("/lumina-network/children")
async def lumina_network_children(request: Request):
    from core.state import state
    from managers.settings_manager import config

    _authorize_peer_request(request)
    network = getattr(state, "lumina_network", None)
    role = str(getattr(config, "LUMINA_NETWORK_ROLE", "master") or "master").strip().lower()
    return {
        "role": role,
        "children": network.list_children() if network and role == "master" else [],
    }


@router.post("/lumina-network/epistemic")
async def lumina_network_epistemic(request: Request):
    """Receive peer epistemic updates without sharing identity or beliefs."""
    from core.state import state

    try:
        body = await request.json()
        _authorize_peer_request(request, body)
        organism = getattr(getattr(state, "persona", None), "_organism", None)
        loop = getattr(organism, "_loop", None) if organism else None
        coupling = getattr(loop, "_structural_coupling", None) if loop else None
        if coupling:
            coupling.receive_update(body)
            return {"status": "ok", "incorporated": True}
        return {"status": "no_coupling_module", "incorporated": False}
    except Exception as exc:
        logger.exception("Peer epistemic update failed")
        return {"status": "error", "detail": str(exc)}


def mount_lumina_peer_routes(app) -> None:
    """Mount peer endpoints on the provided FastAPI-compatible application."""
    app.include_router(router)
