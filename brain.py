"""
brain.py — PandoraBOX Headless Runner
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Starts the full cognitive organism with zero GUI dependency.

What runs:
  ✅ LLM manager          — language model backend
  ✅ Memory manager        — semantic + episodic memory
  ✅ Persona / PandoraBOX      — full cognitive organism
  ✅ Autonomous orchestrator — drive-based activity loop
  ✅ Telegram connector    — if TELEGRAM_TOKEN in config.json
  ✅ WhatsApp connector    — if WHATSAPP_TWILIO_* in config.json
  ✅ REST API (FastAPI)    — POST /chat  GET /status  GET /state
  ✅ WhatsApp webhook      — POST /webhook/whatsapp  (Twilio)
  ✅ Terminal REPL         — --repl flag
  ❌ NiceGUI / browser     — never imported

Usage
━━━━━
  python brain.py                        # headless + API + messaging
  python brain.py --repl                 # add interactive terminal
  python brain.py --port 9000            # custom API port
  python brain.py --host 0.0.0.0        # expose to LAN/internet
  python brain.py --no-api              # skip REST API
  python brain.py --no-telegram         # skip Telegram
  python brain.py --vision              # enable camera (default: off)

REST API  http://127.0.0.1:8765
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  GET  /status                          brain health + uptime
  GET  /state                           organism snapshot
  GET  /thoughts?n=10                   recent thought stream
  POST /chat  {"text":"hi","user_id":"me"}
  POST /chat  {"text":"hi","stream":true}  → SSE
  POST /inject  {"event":"reflect"}
  POST /webhook/whatsapp                Twilio WhatsApp inbound
  GET  /messaging/users                 list registered users
  POST /messaging/send                  push message to any platform
  GET  /docs                            Swagger UI
"""

# ══════════════════════════════════════════════════════════════════════
#  0.  CLI FLAGS  (parsed before any heavy import)
# ══════════════════════════════════════════════════════════════════════
import argparse as _ap

_parser = _ap.ArgumentParser(description="PandoraBOX headless brain runner")
_parser.add_argument("--repl",         action="store_true", help="Launch interactive terminal REPL")
_parser.add_argument("--no-api",       action="store_true", help="Disable REST API")
_parser.add_argument("--no-telegram",  action="store_true", help="Disable Telegram connector")
_parser.add_argument("--port",         type=int, default=None, help="REST API port (default: BRAIN_API_PORT from the selected config profile)")
_parser.add_argument("--host",         default=None,         help="REST API bind host (default: BRAIN_API_HOST from the selected config profile)")
_parser.add_argument("--vision",       action="store_true",   help="Enable camera (default: off)")
_ARGS = _parser.parse_args() if __name__ == "__main__" else _parser.parse_args([])


# ══════════════════════════════════════════════════════════════════════
#  1.  SECURITY BOOTSTRAP
# ══════════════════════════════════════════════════════════════════════
from core.bootstrap import _bootstrap_security
_bootstrap_security()


# ══════════════════════════════════════════════════════════════════════
#  2.  PLATFORM SETUP
# ══════════════════════════════════════════════════════════════════════
import sys
import os
import asyncio
import logging
import time
import uuid
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)-8s  %(message)s",
)

if sys.platform == "win32":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

logger = logging.getLogger("brain")


# ══════════════════════════════════════════════════════════════════════
#  3.  BRAIN BOOT
# ══════════════════════════════════════════════════════════════════════
from managers.settings_manager import config

# Keep the headless Brain API aligned with the configured network contract.
# An explicit CLI flag still wins, which is useful when running a second Brain
# beside the main process.  The Body remains independently bound to BODY_PORT.
if _ARGS.port is None:
    _ARGS.port = int(getattr(config, "BRAIN_API_PORT", 8765) or 8765)
if _ARGS.host is None:
    _ARGS.host = str(getattr(config, "BRAIN_API_HOST", "127.0.0.1") or "127.0.0.1")
from core.state import state

async def _boot() -> bool:
    """
    Initialise the cognitive organism.
    Returns True when the brain is ready to accept messages.
    """
    logger.info("🧠 Booting PandoraBOX cognitive organism…")
    state.local_vision_launch_enabled = bool(_ARGS.vision)

    # Disable camera autostart unless --vision flag was passed.
    # Use __dict__ bypass so it works on both pydantic v1 and v2
    # regardless of model config (no VISION_ENABLED field exists).
    if not _ARGS.vision:
        try:
            config.__dict__["CAMERA_AUTOSTART"] = False
        except Exception:
            pass   # best-effort; won't break boot

    await state.initialize()

    if not state.ready:
        logger.error(
            "❌ Brain core unavailable — check LLM provider and PersonaBridge initialization."
        )
        return False

    logger.info(f"✅ LLM ready        — {config.LLM_PROVIDER}/{config.LLM_MODEL}")
    logger.info(f"✅ Memory ready      — {config.MEMORY_BACKEND}")
    logger.info(f"✅ Persona ready     — {getattr(state.persona, 'is_ready', False)}")

    if state.orchestrator:
        await state.orchestrator.start()
        logger.info("✅ Orchestrator running")
    else:
        logger.warning("⚠️  Orchestrator not available")

    # ── Ensure the cognitive organism's autonomous background loop is running ──
    # PersonaBridge calls organism.start() when the full GUI app loads.
    # In headless mode (brain.py) that call was never made, so the
    # InternalThoughtLoop's self-driving thread — which runs all v47-v49
    # cognitive modules (experimentation, audit, immune system) — was
    # silently absent.  We call it here explicitly; it is idempotent.
    organism = getattr(getattr(state, 'persona', None), '_organism', None)
    if organism and not getattr(organism, '_loop_started', False):
        organism.start()
        logger.info("✅ CognitiveOrganism autonomous loop started (headless mode)")
    elif organism:
        logger.info("✅ CognitiveOrganism loop already running")

    return True


# ══════════════════════════════════════════════════════════════════════
#  4.  REST API  (FastAPI + uvicorn)
# ══════════════════════════════════════════════════════════════════════
from fastapi import FastAPI, HTTPException
from fastapi.requests import Request
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel

api = FastAPI(
    title="PandoraBOX Brain API",
    description="Headless REST interface to the PandoraBOX cognitive organism.",
    version="1.0.0",
)
from core.lumina_peer_api import mount_lumina_peer_routes
mount_lumina_peer_routes(api)

# Global messaging manager — set in _main after start()
_messaging = None


# ── GET /status ───────────────────────────────────────────────────────
@api.get("/status")
async def status():
    orch_status = state.orchestrator.status() if state.orchestrator else {}
    uptime = time.time() - getattr(state, "start_time", time.time())
    return {
        "ready":        state.ready,
        "uptime_secs":  round(uptime, 1),
        "llm":          f"{config.LLM_PROVIDER}/{config.LLM_MODEL}",
        "memory":       config.MEMORY_BACKEND,
        "persona":      getattr(state.persona, "is_ready", False),
        "orchestrator": orch_status.get("running", False),
        "cycle_count":  orch_status.get("cycle_count", 0),
    }


# ── GET /state ────────────────────────────────────────────────────────
@api.get("/state")
async def organism_state():
    if not state.persona:
        raise HTTPException(503, "Persona not ready")
    org = getattr(state.persona, "_organism", None)
    out: dict = {}
    if org:
        try:
            out["emotion"] = org._read_emotion_state()
        except Exception:
            out["emotion"] = "unknown"
        if state.orchestrator:
            try:
                s = state.orchestrator.status()
                out["drives"]    = s.get("drives", {})
                out["workspace"] = s.get("workspace", {})
                out["clock"]     = s.get("clock", {})
            except Exception:
                pass

        # CAG snapshot
        try:
            if state.acc:
                out["cag"] = state.acc.snapshot()
        except Exception:
            pass
        try:
            out["personality"] = {
                k: round(float(v), 3)
                for k, v in vars(org.personality).items()
                if not k.startswith("_")
            }
        except Exception:
            pass
        try:
            out["energy"] = round(float(getattr(org, "energy", {}).get("current", 1.0)), 3)
        except Exception:
            pass

        # ── Prompt influence dashboard (behavioral consequence observability) ──
        # Shows which cognitive modules actually contributed to recent prompts,
        # their selection rates, and mean token spend — surfaces "technically
        # injected but practically ignored" issues.
        try:
            from cognition.prompt_context_budget import PromptContextBudget
            _pcb = PromptContextBudget()
            _summary = _pcb.contribution_summary()
            if _summary:
                out["prompt_influence"] = {
                    src: {
                        "selection_rate": s["selection_rate"],
                        "mean_tokens":    s["mean_tokens"],
                        "appearances":    s["appearances"],
                    }
                    for src, s in sorted(
                        _summary.items(),
                        key=lambda x: x[1]["selection_rate"],
                        reverse=True,
                    )
                }
        except Exception:
            pass

        # ── Cognitive system status (audit + immune) ──────────────────────────
        try:
            loop = getattr(org, '_loop', None)
            cae  = getattr(loop, '_cognitive_audit', None) if loop else None
            if cae:
                out["cognitive_audit"] = cae.status_summary()
            cis = getattr(loop, '_cognitive_immune', None) if loop else None
            if cis:
                out["cognitive_immune"] = cis.status_summary()
            clf = getattr(loop, '_cross_layer_feedback', None) if loop else None
            if clf:
                out["cross_layer_feedback"] = clf.status()
            tp  = getattr(loop, '_temporal_projection', None) if loop else None
            if tp:
                out["temporal_projection"] = tp.status()
            mf  = getattr(loop, '_motivational_field', None) if loop else None
            if mf:
                out["motivational_field"] = mf.status()
        except Exception:
            pass

    return out


# ── GET /thoughts ─────────────────────────────────────────────────────
@api.get("/thoughts")
async def thoughts(n: int = 10):
    org = getattr(getattr(state, "persona", None), "_organism", None)
    if org is None or not hasattr(org, "thought_stream"):
        return {"thoughts": []}
    try:
        recent = org.thought_stream.recent(n)
        return {
            "thoughts": [
                {
                    "content":   t.content,
                    "type":      t.thought_type,
                    "priority":  round(float(t.priority), 3),
                    "timestamp": getattr(t, "timestamp", None),
                }
                for t in recent
            ]
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# ── POST /chat ────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    text:    str
    user_id: str  = "default"
    stream:  bool = False

@api.post("/chat")
async def chat(req: ChatRequest):
    if not state.ready or not state.persona:
        raise HTTPException(503, "Brain not ready yet — try again in a moment")
    state.notify_user_turn(req.text, req.user_id)

    if req.stream:
        async def _sse():
            assistant_parts = []
            turn_completed = False
            completed_turn_id = ""
            cognitive_scope_id = req.user_id
            async for chunk in state.persona.get_response_stream(req.text, req.user_id):
                if isinstance(chunk, dict) and chunk.get("__meta__"):
                    turn_completed = not bool(chunk.get("error"))
                    completed_turn_id = str(chunk.get("turn_id") or "")
                    cognitive_scope_id = str(chunk.get("cognitive_scope_id") or req.user_id)
                    yield f"data: [DONE] {chunk.get('emotion','neutral')}\n\n"
                else:
                    if chunk is not None:
                        assistant_parts.append(str(chunk))
                    yield f"data: {chunk}\n\n"
            if turn_completed:
                state.schedule_deferred_cognitive_stages(
                    req.text, "".join(assistant_parts), req.user_id,
                    turn_id=completed_turn_id, cognitive_scope_id=cognitive_scope_id,
                )
        return StreamingResponse(_sse(), media_type="text/event-stream")

    full_text   = ""
    emotion     = "neutral"
    token_count = 0
    sources     = []
    body_plan   = None
    turn_completed = False
    completed_turn_id = ""
    cognitive_scope_id = req.user_id
    async for chunk in state.persona.get_response_stream(req.text, req.user_id):
        if isinstance(chunk, dict):
            if chunk.get("__meta__"):
                emotion = chunk.get("emotion", "neutral")
                turn_completed = not bool(chunk.get("error"))
                completed_turn_id = str(chunk.get("turn_id") or "")
                cognitive_scope_id = str(chunk.get("cognitive_scope_id") or req.user_id)
                if chunk.get("body_plan") is not None:
                    body_plan = chunk.get("body_plan")
            elif chunk.get("type") == "web_sources":
                sources = chunk.get("sources") or []
            # Structured reasoning/events are transport metadata, not text.
            # Concatenating them caused Brain-only /chat to return HTTP 500.
        elif chunk is not None:
            full_text   += str(chunk)
            token_count += 1

    if turn_completed:
        state.schedule_deferred_cognitive_stages(
            req.text, full_text, req.user_id,
            turn_id=completed_turn_id, cognitive_scope_id=cognitive_scope_id,
        )

    return {
        "response": full_text.strip(),
        "emotion":  emotion,
        "tokens":   token_count,
        "user_id":  req.user_id,
        "sources":  sources,
        "body_plan": body_plan,
    }


# ── POST /inject ──────────────────────────────────────────────────────
class InjectRequest(BaseModel):
    event:   str
    payload: dict = {}

@api.post("/inject")
async def inject(req: InjectRequest):
    if not state.orchestrator:
        raise HTTPException(503, "Orchestrator not running")
    org = getattr(getattr(state, "persona", None), "_organism", None)
    if org is None:
        raise HTTPException(503, "Organism not available")
    evt = req.event.lower()
    try:
        if evt == "reflect":
            loop = getattr(org, "_loop", None)
            if loop and hasattr(loop, "_run_reflection"):
                await asyncio.to_thread(loop._run_reflection, org)
            return {"injected": "reflect"}
        elif evt == "dream":
            pb = state.persona
            if hasattr(pb, "_system") and hasattr(pb._system, "run_dream_cycle"):
                await asyncio.to_thread(pb._system.run_dream_cycle)
            return {"injected": "dream"}
        elif evt == "consolidate":
            if hasattr(org, "semantic_consolidator"):
                await asyncio.to_thread(org.semantic_consolidator.run_consolidation_cycle)
            return {"injected": "consolidate"}
        elif evt == "evolve":
            if hasattr(org, "personality_evolution"):
                await asyncio.to_thread(org.personality_evolution.maybe_evolve)
            return {"injected": "evolve"}
        else:
            raise HTTPException(400, f"Unknown event '{evt}'. Valid: reflect, dream, consolidate, evolve")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# ── POST /webhook/whatsapp ────────────────────────────────────────────
@api.post("/webhook/whatsapp", response_class=Response)
async def whatsapp_webhook(request: Request):
    """
    Twilio WhatsApp inbound webhook.
    Returns TwiML XML.

    Setup:
      1. Run:  python brain.py --host 0.0.0.0
      2. Run:  ngrok http 8765
      3. In Twilio Console → Messaging → Sandbox Settings
         "When a message comes in" → https://YOUR.ngrok.app/webhook/whatsapp
    """
    from managers.messaging_manager import MessagingManager

    if _messaging is None:
        return Response(
            content=MessagingManager._twiml("Brain starting — try again in a moment."),
            media_type="application/xml",
        )

    form  = await request.form()
    data  = dict(form)
    sig   = request.headers.get("X-Twilio-Signature", "")
    url   = str(request.url)

    twiml = await _messaging.handle_whatsapp_webhook(data, sig, url)
    return Response(content=twiml, media_type="application/xml")


# ── GET /messaging/users ──────────────────────────────────────────────
@api.get("/messaging/users")
async def messaging_users():
    """List all registered WhatsApp / Telegram users."""
    if _messaging is None:
        return {"users": []}
    return {"users": _messaging.list_users()}


# ── POST /messaging/send ──────────────────────────────────────────
class SendRequest(BaseModel):
    platform: str     # "whatsapp" | "telegram"
    to:       str     # phone (+1234...) or Telegram chat_id
    text:     str

@api.post("/messaging/send")
async def messaging_send(req: SendRequest):
    """Push a raw message to any platform (no LLM — direct delivery)."""
    if _messaging is None:
        raise HTTPException(503, "Messaging not started")
    await _messaging.send_message(req.platform, req.to, req.text)
    return {"sent": True}


# ══════════════════════════════════════════════════════════════════════
#  5.  TERMINAL REPL
# ══════════════════════════════════════════════════════════════════════
async def _repl():
    print()
    print("━" * 60)
    print("  🧠 PandoraBOX REPL — type a message, Enter to send")
    print("  Commands:  /status  /state  /thoughts  /users  /quit")
    print("━" * 60)
    print()

    user_id = "repl_user"
    loop    = asyncio.get_event_loop()

    while True:
        try:
            text = await loop.run_in_executor(None, lambda: input("You: ").strip())
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Shutting down REPL…")
            break

        if not text:
            continue

        if text == "/quit":
            break

        if text == "/status":
            st = await status()
            for k, v in st.items():
                print(f"   {k}: {v}")
            continue

        if text == "/state":
            st = await organism_state()
            for k, v in st.items():
                if isinstance(v, dict):
                    print(f"   {k}:")
                    for kk, vv in v.items():
                        print(f"      {kk}: {vv}")
                else:
                    print(f"   {k}: {v}")
            continue

        if text == "/thoughts":
            th = await thoughts(n=5)
            for t in th["thoughts"]:
                print(f"   [{t['type']}] ({t['priority']:.2f}) {t['content'][:100]}")
            continue

        if text == "/users":
            if _messaging:
                users = _messaging.list_users()
                for u in users:
                    print(f"   {u['platform_key']} → {u['lumina_id']}  ({u['name']})")
            else:
                print("   Messaging not started")
            continue

        if text.startswith("/inject "):
            evt = text.split(" ", 1)[1]
            try:
                r = await inject(InjectRequest(event=evt))
                print(f"   ✅ {r}")
            except HTTPException as e:
                print(f"   ❌ {e.detail}")
            continue

        if not state.ready or not state.persona:
            print("   ⏳ Brain not ready yet — please wait…")
            continue

        state.notify_user_turn(text, user_id)

        print("PandoraBOX: ", end="", flush=True)
        emotion = "neutral"
        assistant_parts = []
        turn_completed = False
        completed_turn_id = ""
        cognitive_scope_id = user_id
        try:
            async for chunk in state.persona.get_response_stream(text, user_id):
                if isinstance(chunk, dict) and chunk.get("__meta__"):
                    emotion = chunk.get("emotion", "neutral")
                    turn_completed = not bool(chunk.get("error"))
                    completed_turn_id = str(chunk.get("turn_id") or "")
                    cognitive_scope_id = str(chunk.get("cognitive_scope_id") or user_id)
                else:
                    if chunk is not None:
                        assistant_parts.append(str(chunk))
                    print(chunk, end="", flush=True)
        except Exception as e:
            print(f"\n[Error: {e}]")

        if turn_completed:
            state.schedule_deferred_cognitive_stages(
                text, "".join(assistant_parts), user_id,
                turn_id=completed_turn_id, cognitive_scope_id=cognitive_scope_id,
            )

        print(f"\n   ({emotion})\n")


# ══════════════════════════════════════════════════════════════════════
#  6.  MESSAGING CONNECTORS
# ══════════════════════════════════════════════════════════════════════
async def _start_messaging():
    if not state.orchestrator:
        logger.warning("Messaging: orchestrator not available — skipping")
        return None
    try:
        from managers.messaging_manager import MessagingManager
        mm = MessagingManager(state.orchestrator, config)
        await mm.start()
        return mm
    except Exception as e:
        logger.warning(f"Messaging connectors failed to start: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════
#  7.  MAIN
# ══════════════════════════════════════════════════════════════════════
async def _main():
    global _messaging

    # ── Boot brain ────────────────────────────────────────────────────
    ready = await _boot()
    if not ready:
        sys.exit(1)

    # ── Messaging connectors ──────────────────────────────────────────
    if not _ARGS.no_telegram:
        _messaging = await _start_messaging()

    # ── REST API in background thread ─────────────────────────────────
    api_listener = None
    bridge_listener = None
    if not _ARGS.no_api:
        logger.info(f"🌐 REST API → http://{_ARGS.host}:{_ARGS.port}")
        logger.info(f"   Docs    → http://{_ARGS.host}:{_ARGS.port}/docs")
        from core.brain_api_server import start_brain_api_server
        api_listener = start_brain_api_server(
            config, api, host=_ARGS.host, port=_ARGS.port,
        )

        if bool(getattr(config, "BODY_BRIDGE_LISTEN_ENABLED", False)):
            try:
                from core.body_bridge_server import start_body_bridge_server
                bridge_listener = start_body_bridge_server(config, _ARGS.host, _ARGS.port)
            except (ValueError, OSError, RuntimeError) as exc:
                logger.error("Body bridge listener configuration is invalid: %s", exc)

    # ── Banner ─────────────────────────────────────────────────────────
    tg_ok    = bool(_messaging and getattr(_messaging, "_tg_app", None))
    wa_ok    = bool(_messaging and getattr(_messaging, "_twilio", None))
    print()
    print("╔" + "═" * 58 + "╗")
    print("║   🧠  PANDORABOX — HEADLESS BRAIN                            ║")
    print("╠" + "═" * 58 + "╣")
    print(f"║   LLM        : {config.LLM_PROVIDER}/{config.LLM_MODEL:<35}║")
    print(f"║   Memory     : {config.MEMORY_BACKEND:<42}║")
    print(f"║   Telegram   : {'✅ polling' if tg_ok else '— set TELEGRAM_TOKEN in config':<42}║")
    print(f"║   WhatsApp   : {'✅ webhook ready' if wa_ok else '— set WHATSAPP_TWILIO_* in config':<42}║")
    if not _ARGS.no_api:
        print(f"║   REST API   : http://{_ARGS.host}:{_ARGS.port:<36}║")
        print(f"║   WA Webhook : POST /webhook/whatsapp{' '*22}║")
        print(f"║   Docs       : http://{_ARGS.host}:{_ARGS.port}/docs{' '*30}║")
    if bridge_listener:
        print(f"║   Body bridge: ws://{config.BODY_BRIDGE_LISTEN_HOST}:{config.BODY_BRIDGE_LISTEN_PORT:<27}║")
    print(f"║   Vision     : {'✅ enabled' if _ARGS.vision else '— pass --vision to enable':<42}║")
    print("╠" + "═" * 58 + "╣")
    print("║   Send !help via WhatsApp/Telegram to get started       ║")
    print("║   Ctrl+C to stop                                         ║")
    print("╚" + "═" * 58 + "╝")
    print()

    # ── REPL or idle heartbeat ────────────────────────────────────────
    try:
        if _ARGS.repl:
            await _repl()
        else:
            while True:
                await asyncio.sleep(60)
                uptime = round(time.time() - getattr(state, "start_time", time.time()))
                cycles = state.orchestrator.status().get("cycle_count", "—") if state.orchestrator else "—"
                logger.info(f"💓 uptime={uptime}s  orch_cycles={cycles}")
    except KeyboardInterrupt:
        pass

    # ── Graceful shutdown ─────────────────────────────────────────────
    logger.info("🛑 Shutting down…")
    if _messaging:
        await _messaging.stop()
    try:
        organism = getattr(getattr(state, "persona", None), "_organism", None)
        if organism is not None:
            from cognition.universal_connector import get_universal_connector
            await get_universal_connector(organism).stop_home_assistant_monitor()
    except Exception:
        logger.debug("Home Assistant monitor shutdown failed", exc_info=True)
    if state.orchestrator:
        await state.orchestrator.stop()
    try:
        from managers.session_manager import get_session_manager
        sess = get_session_manager()
        if state.llm:
            sess.on_shutdown(state.llm.history)
    except Exception:
        pass
    if api_listener:
        from core.brain_api_server import stop_brain_api_server
        stop_brain_api_server(api_listener)
    if bridge_listener:
        from core.body_bridge_server import stop_body_bridge_server
        stop_body_bridge_server(bridge_listener)
    logger.info("✅ Brain shutdown complete")


if __name__ == "__main__":
    asyncio.run(_main())
