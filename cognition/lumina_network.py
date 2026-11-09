"""
cognition/lumina_network.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PandoraBOX-to-PandoraBOX network connector.

Allows a Master PandoraBOX to:
  • Register one or more Child PandoraBOX instances (brain.py or NiceGUI)
  • Send messages to any child and receive responses
  • Run autonomous dialogues (N-turn exchanges on a topic)
  • Receive unsolicited messages FROM a child (push model)
  • Display all exchanges as chat bubbles in the master UI

Child instances appear as named "users" in the master chat.
Their bubbles use a distinct `bubble-child` CSS class.

Network topology:
  Master (NiceGUI or brain.py)
    ├── Child A  http://192.168.1.10:8765   (brain.py headless)
    ├── Child B  http://192.168.1.11:8080   (NiceGUI — same API)
    └── Child C  http://lumina-pi.local:8765

Config (config.json):
  "LUMINA_CHILDREN": [
    {"id": "child_a", "name": "PandoraBOX-A", "url": "http://192.168.1.10:8765",
     "api_key": "", "role": "child"},
    {"id": "child_b", "name": "PandoraBOX-B", "url": "http://192.168.1.11:8765",
     "api_key": "", "role": "child"}
  ]

Protocol:
  Master → Child:  POST {child_url}/lumina-network/chat
    body: {"text": "...", "sender_id": "master", "sender_name": "PandoraBOX-Master",
           "conversation_id": "uuid", "api_key": "..."}
  Child → Master:  POST {master_url}/lumina-network/receive
    body: {"text": "...", "sender_id": "child_a", "sender_name": "PandoraBOX-A",
           "conversation_id": "uuid"}

Public API:
  net = LuminaNetwork(persona, llm)
  net.add_child(id, name, url, api_key="", role="child")
  await net.send_to_child(child_id, message_text)   → response text
  await net.start_dialogue(child_id, topic, turns=4) → full exchange
  net.set_bubble_fn(fn)           → fn(text, who, child_id, child_name)
  net.list_children()             → list of child dicts
  net.get_child_status(child_id)  → {"online": True, "latency_ms": 42}
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Phase 6.5 — minimum interval between workspace-snapshot shares to one
# child. A pragmatic bound against a share -> hypothesis -> share
# amplifier loop, simpler than tracing per-candidate provenance chains.
SNAPSHOT_COOLDOWN_S = 45.0


def _sanitize_cognitive_trace(value: Any) -> Optional[dict]:
    """Accept only bounded peer-stage metadata from a remote instance."""
    if not isinstance(value, dict) or value.get("scope") != "peer":
        return None
    scope_id = value.get("cognitive_scope_id")
    if not isinstance(scope_id, str) or not scope_id.startswith("peer:"):
        return None
    stages = {}
    raw_stages = value.get("stages", {})
    if isinstance(raw_stages, dict):
        for name, stage in list(raw_stages.items())[:80]:
            if isinstance(stage, dict) and isinstance(stage.get("status"), str):
                stages[str(name)[:80]] = {"status": stage["status"][:48]}
    sources = {}
    raw_sources = value.get("context_sources", {})
    if isinstance(raw_sources, dict):
        for name, source in list(raw_sources.items())[:40]:
            if isinstance(source, dict) and isinstance(source.get("status"), str):
                sources[str(name)[:80]] = {"status": source["status"][:48]}
    return {
        "turn_id": str(value.get("turn_id", ""))[:100],
        "scope": "peer",
        "peer_name": str(value.get("peer_name", ""))[:80],
        "cognitive_scope_id": scope_id[:160],
        "status": str(value.get("status", "unknown"))[:48],
        "stages": stages,
        "context_sources": sources,
    }


@dataclass
class ChildLumina:
    """Registered child PandoraBOX instance."""
    id:           str
    name:         str
    url:          str               # base URL, e.g. http://192.168.1.10:8765
    api_key:      str  = ""
    role:         str  = "child"    # "child" | "peer" | "specialist"
    online:       bool = False
    last_ping:    float = 0.0
    latency_ms:   float = 0.0
    last_error:   str = ""
    turn_count:   int   = 0
    last_snapshot_share: float = 0.0  # Phase 6.5 — cooldown for share_workspace_snapshot()
    last_cognitive_trace: Optional[dict] = None


@dataclass
class NetworkMessage:
    """A single message in a PandoraBOX-to-PandoraBOX exchange."""
    text:            str
    sender_id:       str
    sender_name:     str
    conversation_id: str
    timestamp:       float = field(default_factory=time.time)
    direction:       str   = "out"   # "out" = master→child, "in" = child→master


class LuminaNetwork:
    """
    PandoraBOX-to-PandoraBOX network connector.
    Manages child instances and routes messages bidirectionally.
    """

    def __init__(self, persona: Any, llm: Any):
        self._persona  = persona
        self._llm      = llm
        self._children: Dict[str, ChildLumina] = {}
        # A conversation ID is only unique within a peer relationship. Keep
        # peer identity in the storage key so two children cannot share turns
        # by reusing the same (or a predictable) conversation ID.
        self._history:  Dict[tuple[str, str], List[NetworkMessage]] = {}
        self._peer_turn_locks: Dict[
            tuple[str, str], tuple[asyncio.AbstractEventLoop, asyncio.Lock]
        ] = {}
        self._peer_turn_locks_guard = threading.RLock()
        self._dialogue_stops: Dict[str, Any] = {}             # child_id → stop Event
        self._active_dialogues: Dict[str, str] = {}            # child_id → conversation_id
        self._dialogue_injections: Dict[tuple[str, str], deque] = {}
        self._active_conversations: Dict[str, str] = {}         # default manual Ask thread per child
        self._bubble_fn: Optional[Callable] = None  # fn(text, who, child_id, name)
        self._lock = __import__('threading').Lock()
        self._master_url: str = ""   # set when master exposes its own endpoint
        self._master_name: str = "PandoraBOX-Master"

        try:
            import aiohttp
            self._aiohttp = aiohttp
        except ImportError:
            self._aiohttp = None
            logger.warning("⚠️  LuminaNetwork: aiohttp not installed — "
                           "pip install aiohttp --break-system-packages")

        logger.info("🌐 LuminaNetwork initialised")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Child registration
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def add_child(
        self,
        child_id:  str,
        name:      str,
        url:       str,
        api_key:   str = "",
        role:      str = "child",
    ) -> None:
        url = url.rstrip("/")
        self._children[child_id] = ChildLumina(
            id=child_id, name=name, url=url, api_key=api_key, role=role
        )
        logger.info(f"🌐 Registered child: {name} @ {url}")

    def load_from_config(self, children_config: list) -> None:
        """Load only concrete peers; commented examples are not endpoints."""
        try:
            from managers.settings_manager import config as app_config
            shared_api_key = str(getattr(app_config, "LUMINA_NETWORK_API_KEY", "") or "")
        except Exception:
            shared_api_key = ""
        for index, c in enumerate(children_config or []):
            if not isinstance(c, dict):
                logger.warning("Ignoring malformed LUMINA_CHILDREN entry at index %d", index)
                continue
            if c.get("_comment"):
                logger.info(
                    "Ignoring LUMINA_CHILDREN example entry at index %d: %s",
                    index, str(c.get("_comment"))[:120],
                )
                continue
            url = str(c.get("url", "") or "").strip()
            if not url:
                logger.warning("Ignoring LUMINA_CHILDREN entry without a URL at index %d", index)
                continue
            self.add_child(
                child_id = c.get("id", f"child_{len(self._children)}"),
                name     = c.get("name", "PandoraBOX-Child"),
                url      = url,
                api_key  = c.get("api_key") or shared_api_key,
                role     = c.get("role", "child"),
            )

    def set_bubble_fn(self, fn: Callable) -> None:
        """Register the UI bubble callback — called for every exchanged message."""
        self._bubble_fn = fn

    def set_master_info(self, url: str, name: str = "PandoraBOX-Master") -> None:
        """Set master's own URL so children can push back to it."""
        self._master_url  = url.rstrip("/")
        self._master_name = name

    async def stop(self) -> None:
        """Gracefully stop all active dialogues and disconnect."""
        for stop_ev in self._dialogue_stops.values() if hasattr(self, '_dialogue_stops') else []:
            try: stop_ev.set()
            except Exception: pass
        logger.info("🌐 LuminaNetwork stopped")

    def list_children(self) -> List[Dict]:
        return [
            {
                "id":         c.id,
                "name":       c.name,
                "url":        c.url,
                "role":       c.role,
                "online":     c.online,
                "latency_ms": round(c.latency_ms, 1),
                "last_error": c.last_error,
                "turn_count": c.turn_count,
                "last_cognitive_trace": c.last_cognitive_trace,
            }
            for c in self._children.values()
        ]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Health check
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def ping_child(self, child_id: str) -> bool:
        """Ping a child's /status endpoint. Returns True if online."""
        child = self._children.get(child_id)
        if not child or not self._aiohttp:
            return False
        try:
            t0 = time.time()
            async with self._aiohttp.ClientSession() as session:
                async with session.get(
                    f"{child.url}/status", timeout=self._aiohttp.ClientTimeout(total=10)
                ) as resp:
                    child.online     = resp.status == 200
                    child.latency_ms = (time.time() - t0) * 1000
                    child.last_ping  = time.time()
                    child.last_error = "" if child.online else f"HTTP {resp.status} from /status"
                    return child.online
        except Exception as exc:
            child.online = False
            child.last_ping = time.time()
            child.last_error = f"{type(exc).__name__}: {exc}"[:240]
            logger.warning(
                "Flux health check failed for %s at %s/status: %s",
                child.name, child.url, child.last_error,
            )
            return False

    async def ping_all(self) -> Dict[str, bool]:
        results = {}
        for child_id in self._children:
            results[child_id] = await self.ping_child(child_id)
        return results

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Send one message to a child
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def send_to_child(
        self,
        child_id:        str,
        text:            str,
        conversation_id: str = "",
        show_in_ui:      bool = True,
    ) -> str:
        """
        Send text to a child PandoraBOX and return its response.
        Pushes both messages to the UI bubble callback.
        """
        conv_id = self._conversation_for_peer(child_id, conversation_id)
        lock = self._conversation_lock(child_id, conv_id)
        async with lock:
            return await self._send_to_child_locked(
                child_id, text, conversation_id=conv_id, show_in_ui=show_in_ui,
            )

    async def _send_to_child_locked(
        self,
        child_id:        str,
        text:            str,
        conversation_id: str,
        show_in_ui:      bool,
    ) -> str:
        """Perform one serialized exchange for a peer/conversation pair."""
        child = self._children.get(child_id)
        if not child:
            return f"[Child {child_id!r} not registered]"
        if not self._aiohttp:
            return "[aiohttp not installed — pip install aiohttp]"

        conv_id = conversation_id

        # ── v53/v56: Pre-send cognitive recording ─────────────────────────
        # Network dialogues bypass cognitive_organism._call_ai_system() so
        # PredictiveConsequenceModel and WorldSelfDynamicsModel never see them.
        # Wire both here so PandoraBOX-Flux exchanges feed the learning models
        # with the same richness as human interactions.
        _pcm = _wsdm = _child_uid = None
        _pcm_state_before = _wsdm_context_before = None
        _interaction_n = child.turn_count
        _pre_action = "philosophical"   # default — PandoraBOX-Flux exchanges tend to be
        try:
            from core.state import state as _st_pre
            _org  = getattr(getattr(_st_pre, 'persona', None), '_organism', None)
            _loop = getattr(_org, '_loop', None) if _org else None
            _pcm  = getattr(_loop, '_consequence_model', None) if _loop else None
            _wsdm = getattr(_loop, '_world_self_dynamics', None) if _loop else None
            _child_uid = f"lumina_child_{child_id}"

            if _pcm:
                _pre_action = _pcm.classify(text)
                _pcm_state_before = list(_pcm.read_state())
            if _wsdm:
                capture_context = getattr(_wsdm, "capture_context", None)
                if callable(capture_context):
                    _wsdm_context_before = capture_context(_child_uid)
        except Exception:
            pass

        # ── Show master's outgoing message in UI ──────────────────────────
        if show_in_ui and self._bubble_fn:
            try:
                self._bubble_fn(text, "master", "master", self._master_name)
            except Exception:
                pass

        # ── HTTP POST to child ────────────────────────────────────────────
        payload = {
            "text":            text,
            "user_id":         "lumina_master",
            "sender_id":       "master",
            "sender_name":     self._master_name,
            "conversation_id": conv_id,
        }
        if child.api_key:
            payload["api_key"] = child.api_key
        response_text = ""
        exchange_succeeded = False
        try:
            t0 = time.time()
            async with self._aiohttp.ClientSession() as session:
                async with session.post(
                    f"{child.url}/lumina-network/chat",
                    json=payload,
                    timeout=self._aiohttp.ClientTimeout(total=60),
                ) as resp:
                    child.latency_ms = (time.time() - t0) * 1000
                    child.online     = True
                    child.last_error = ""
                    if resp.status == 200:
                        try:
                            data = await resp.json()
                        except Exception:
                            data = None
                        candidate = data.get("response") if isinstance(data, dict) else None
                        if isinstance(candidate, str) and candidate.strip():
                            response_text = candidate.strip()
                            exchange_succeeded = True
                            child.turn_count += 1
                            child.last_cognitive_trace = _sanitize_cognitive_trace(
                                data.get("cognitive_trace") if isinstance(data, dict) else None
                            )
                            if child.last_cognitive_trace is not None:
                                child.last_cognitive_trace["received_at"] = time.time()
                            # Do not let an error or malformed response rename
                            # the peer in the active transcript.
                            returned_name = data.get("sender_name", "")
                            if returned_name:
                                child.name = returned_name
                        else:
                            response_text = "[Child error 200: empty or invalid cognitive response]"
                    else:
                        body = await resp.text()
                        response_text = f"[Child error {resp.status}: {body[:80]}]"
        except Exception as e:
            child.online  = False
            child.last_error = f"{type(e).__name__}: {e}"[:240]
            response_text = f"[Network error: {e}]"

        # ── Commit only completed pair exchanges ─────────────────────────
        # A failed transport/provider attempt is status, not a conversation
        # turn. Saving the outgoing prompt alone would make later context
        # claim that the child received a message it never answered.
        if exchange_succeeded:
            history_key = self._history_key(child_id, conv_id)
            self._history.setdefault(history_key, []).append(
                NetworkMessage(text, "master", self._master_name, conv_id, direction="out")
            )
            self._history[history_key].append(
                NetworkMessage(response_text, child_id, child.name, conv_id, direction="in")
            )

        # ── Keep peer learning scoped ─────────────────────────────────────
        try:
            from core.state import state as _st
            # Peer transcript stays in LuminaNetwork._history and is passed
            # explicitly to peer turns. Do not write it to shared FAISS memory:
            # human turns query that index and could otherwise recall a private
            # child dialogue as ordinary autobiographical context.
            # Relational memory — build a persistent model of the child
            # (trust, familiarity, shared topics) the same way user relationships
            # are tracked. Uses child_id as user_id so it's a distinct record.
            if hasattr(_st, 'persona') and _st.persona:
                org = getattr(_st.persona, '_organism', None)
                ai = getattr(org, 'ai_system', None)
                if ai is None:
                    ai = getattr(_st.persona, '_system', None)
                if ai is None:
                    ai = getattr(_st.persona, 'ai_system', None)
                rm = getattr(ai, 'relational_memory', None)
                if rm and exchange_succeeded:
                    # Estimate valence from response length and content
                    # (neutral default — the child isn't a human user)
                    rm.record_exchange(
                        user_id     = f"lumina_child_{child.id}",
                        user_text   = f"[{child.name}]: {response_text}",
                        ai_response = text,
                        valence     = "Neutral",
                        arousal     = "Low",
                        topic       = text[:40] if text else "dialogue",
                        impact      = 0.4,
                    )
        except Exception:
            logger.exception("[LuminaNetwork] Could not persist exchange")

        if exchange_succeeded:
            try:
                org = getattr(self._persona, '_organism', None)
                model = getattr(getattr(org, '_loop', None), '_flux_mind_model', None)
                if model is not None:
                    model._update()
            except Exception:
                logger.exception("[LuminaNetwork] Could not update Flux profile")

        # ── Show child's response in UI ───────────────────────────────────
        if show_in_ui and self._bubble_fn and exchange_succeeded:
            try:
                self._bubble_fn(response_text, "child", child_id, child.name)
            except Exception:
                pass

        # ── Post-response outcome recording ────────────────────────────────
        # Record the consequence of this dialogue exchange into both models.
        # A peer reply's length or punctuation is not evidence of positive or
        # negative valence; keep the outcome neutral unless a real evaluator is
        # wired to supply an explicit judgement.
        try:
            if exchange_succeeded and (_pcm or _wsdm):
                _net_outcome = "neutral"
                if _pcm:
                    record_transition = getattr(_pcm, "record_observed_transition", None)
                    if callable(record_transition) and _pcm_state_before is not None:
                        record_transition(
                            _pre_action, _pcm_state_before, _pcm.read_state(),
                            interaction_n=_interaction_n, outcome=_net_outcome,
                            resolve_calibration=False,
                        )
                if _wsdm:
                    record_transition = getattr(_wsdm, "record_observed_transition", None)
                    if callable(record_transition) and _wsdm_context_before is not None:
                        peer_uid = _child_uid or f"lumina_child_{child_id}"
                        record_transition(
                            _pre_action, peer_uid, _wsdm_context_before,
                            _wsdm.capture_context(peer_uid),
                            interaction_n=_interaction_n, outcome=_net_outcome,
                            response_text=response_text, user_input=text,
                            resolve_calibration=False,
                        )
        except Exception:
            pass

        logger.info(
            f"🌐 [{child.name}] latency={child.latency_ms:.0f}ms "
            f"out={text[:40]!r} in={response_text[:40]!r}"
        )
        return response_text

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Phase 6.5 — Peer Workspace Snapshot (bounded, non-copying)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Deliberately NOT flux.workspace = lumina.workspace — that would be
    # one brain running twice, per the proposal's own explicit warning.
    # Master sends a small PROJECTION (focus + top hypotheses only — no
    # memory, no emotional state, no goals detail — "protects the
    # independence of the second process" per the proposal). Flux runs
    # ITS OWN deliberate() using its own goals/tensions/pressure, informed
    # by (not copying) that projection, and returns its own resulting
    # focus. That becomes hop_count=1 on the way back — genuinely
    # load-bearing this time, not just a field waiting for a future use.
    async def share_workspace_snapshot(self, child_id: str) -> Optional[str]:
        child = self._children.get(child_id)
        if not child or not self._aiohttp:
            return None

        # Cooldown, not deep provenance tracing — a pragmatic bound against
        # a share -> hypothesis -> share -> hypothesis amplifier, matching
        # the proposal's TTL/hop_count caution without needing to trace
        # exactly which candidate's provenance triggered this cycle.
        now = time.time()
        if now - child.last_snapshot_share < SNAPSHOT_COOLDOWN_S:
            return None

        try:
            from core.state import state as _st_snap
            org = getattr(getattr(_st_snap, 'persona', None), '_organism', None)
            if org is None:
                return None
            gw = getattr(org, 'workspace', None)
            if gw is None:
                return None
            ws_state = gw.get_state()
            snapshot = {
                "focus":       ws_state.focus,
                "hypotheses":  [
                    {"name": h.get("name") or h.get("label"), "score": h.get("score")}
                    for h in (ws_state.active_hypotheses or [])[:3]
                ],
            }
        except Exception as e:
            logger.debug(f"[LuminaNetwork] snapshot build failed (non-fatal): {e}")
            return None

        child.last_snapshot_share = now
        payload = {
            "message_type": "workspace_snapshot",
            "snapshot":     snapshot,
            "sender_id":    "master",
            "sender_name":  self._master_name,
        }
        if child.api_key:
            payload["api_key"] = child.api_key

        try:
            async with self._aiohttp.ClientSession() as session:
                async with session.post(
                    f"{child.url}/lumina-network/chat",
                    json=payload,
                    timeout=self._aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
        except Exception as e:
            logger.debug(f"[LuminaNetwork] snapshot share failed (non-fatal): {e}")
            return None

        flux_hypothesis = (data.get("response") or "").strip()
        if not flux_hypothesis:
            return None

        # ── Real round trip closes here: Flux's own resulting focus
        # becomes a peer_cognition percept with hop_count=1 — the first
        # genuinely load-bearing use of that field (v95 added it with
        # nothing yet incrementing it).
        try:
            from cognition.universal_connector import Percept, get_universal_connector
            get_universal_connector(org).perceive(Percept(
                modality   = "peer_cognition",
                source     = "flux",
                payload    = flux_hypothesis[:200],
                confidence = 0.65,
                salience   = 0.55,
                hop_count  = 1,
                provenance = {"exchange": "workspace_snapshot", "shared_focus": snapshot["focus"]},
            ))
        except Exception as e:
            logger.debug(f"[LuminaNetwork] percept from snapshot reply failed (non-fatal): {e}")

        return flux_hypothesis

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Autonomous N-turn dialogue
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # ── User injection queue (messages typed during dialogue) ────────────────
    def _conversation_for_peer(
        self, child_id: str, conversation_id: str = "", *, new: bool = False,
    ) -> str:
        """Resolve the stable default transcript for a peer or honor an explicit one."""
        child_id = str(child_id or "unknown")
        lock = getattr(self, "_lock", None)
        if lock is None:
            lock = self._lock = threading.RLock()
        sessions = getattr(self, "_active_conversations", None)
        if sessions is None:
            sessions = self._active_conversations = {}
        with lock:
            resolved = str(conversation_id or "").strip()
            if not resolved and not new:
                resolved = sessions.get(child_id, "")
            if not resolved:
                resolved = uuid.uuid4().hex
            sessions[child_id] = resolved
            return resolved

    def inject_user_message(self, text: str, child_id: str | None = None) -> bool:
        """Inject only into the explicitly named or sole active peer dialogue."""
        clean_text = str(text or "").strip()
        if not clean_text:
            return False
        lock = getattr(self, "_lock", None)
        if lock is None:
            lock = self._lock = threading.RLock()
        with lock:
            active = getattr(self, "_active_dialogues", {})
            if child_id:
                conversation_id = active.get(str(child_id))
                target_child = str(child_id)
            elif len(active) == 1:
                target_child, conversation_id = next(iter(active.items()))
            else:
                # Ambiguous or no peer dialogue: leave this as a normal human turn.
                return False
            if not conversation_id:
                return False
            queues = getattr(self, "_dialogue_injections", None)
            if queues is None:
                queues = self._dialogue_injections = {}
            queues.setdefault((target_child, conversation_id), deque(maxlen=20)).append(clean_text)
            return True

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Autonomous dialogue loop
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def start_dialogue(
        self,
        child_id:          str,
        topic:             str  = "",
        conversation_id:   str  = "",
        delay_s:           float = 2.5,
        stop_event               = None,   # asyncio.Event
        turns_per_topic:   int  = 4,       # turns before pivoting to new topic
        max_topics:        int  = 0,       # 0 = unlimited
        pause_between_s:   float = 5.0,    # pause shown between topic shifts
    ):
        """
        Autonomous dialogue with:
          • topic rotation (every turns_per_topic turns)
          • user injection (typed messages interrupt and redirect)
          • conversation summary on end
          • natural pauses between topic shifts
        """
        child = self._children.get(child_id)
        if not child:
            return []

        conv_id   = self._conversation_for_peer(
            child_id, conversation_id, new=not bool(conversation_id),
        )
        exchange  = []
        turn      = 0
        topic_num = 0

        lock = getattr(self, "_lock", None)
        if lock is None:
            lock = self._lock = threading.RLock()
        with self._lock:
            self._active_dialogues[child_id] = conv_id
            injection_key = (child_id, conv_id)
            self._dialogue_injections[injection_key] = deque(maxlen=20)

        # Remove the active marker even on task cancellation or unexpected errors.
        task = asyncio.current_task()
        if task is not None:
            def _clear_dialogue(_task, _child_id=child_id, _conv_id=conv_id):
                with self._lock:
                    if self._active_dialogues.get(_child_id) == _conv_id:
                        self._active_dialogues.pop(_child_id, None)
                    self._dialogue_injections.pop((_child_id, _conv_id), None)
            task.add_done_callback(_clear_dialogue)

        # ── First topic ───────────────────────────────────────────────────
        seed_topic = topic.strip()
        current_topic = seed_topic or "open dialogue"
        current_text = await self._generate_opening(
            child.name, child.id, seed_topic=seed_topic, conversation_id=conv_id,
        )
        if not current_text:
            logger.error("🌐 Dialogue not started: scoped cognitive opener was unavailable")
            return []
        logger.info(f"🌐 Dialogue [{child.name}] topic_1={current_topic[:60]!r}")

        while True:
            if stop_event and stop_event.is_set():
                break
            if max_topics and topic_num >= max_topics:
                break

            # ── Check user injection queue ────────────────────────────────
            with self._lock:
                pending = self._dialogue_injections.get((child_id, conv_id))
                user_msg = pending.popleft() if pending else None

            if user_msg:
                # Show user's message as a distinct bubble
                if self._bubble_fn:
                    try:
                        self._bubble_fn(f"💬 {user_msg}", "master", "master", "You")
                    except Exception:
                        pass
                current_text = user_msg   # user message becomes the next turn

            # ── Send to child ─────────────────────────────────────────────
            response = await self.send_to_child(
                child_id=child_id, text=current_text,
                conversation_id=conv_id, show_in_ui=True,
            )
            if not response or response.startswith("["):
                break

            exchange.append(NetworkMessage(current_text, "master", self._master_name, conv_id, direction="out"))
            exchange.append(NetworkMessage(response, child_id, child.name, conv_id, direction="in"))
            turn += 1

            if stop_event and stop_event.is_set():
                break

            await asyncio.sleep(delay_s)
            if stop_event and stop_event.is_set():
                break

            # ── Topic rotation ────────────────────────────────────────────
            turns_on_topic = turn - topic_num * turns_per_topic
            with self._lock:
                pending_injections = self._dialogue_injections.get((child_id, conv_id))
                has_pending_injection = bool(pending_injections)
            if turns_on_topic >= turns_per_topic and not has_pending_injection:
                topic_num += 1

                # Show pause bubble
                if self._bubble_fn:
                    try:
                        self._bubble_fn(
                            f"⏸ *Shifting topic — {turns_on_topic} turns on this thread. Pausing…*",
                            "master", "master", "System"
                        )
                    except Exception:
                        pass

                await asyncio.sleep(pause_between_s)
                if stop_event and stop_event.is_set():
                    break

                # Generate new topic from cognitive state
                current_topic = await self._generate_new_topic(
                    exchange, child.name, conversation_id=conv_id,
                )
                if not current_topic:
                    logger.error("🌐 Dialogue stopped: scoped cognitive topic pivot was unavailable")
                    break
                current_text  = current_topic
                logger.info(f"🌐 Topic shift → {current_topic[:60]!r}")

                if self._bubble_fn:
                    try:
                        self._bubble_fn(
                            f"💡 *New thread: {current_topic}*",
                            "master", "master", "System"
                        )
                    except Exception:
                        pass
            else:
                # Continue on same topic
                current_text = await self._master_generate(
                    current_topic, exchange[-6:], child.name, child_id=child_id,
                    conversation_id=conv_id,
                )
                if not current_text:
                    break

        # ── End of dialogue ───────────────────────────────────────────────
        logger.info(f"🌐 Dialogue ended — {turn} turns, {topic_num+1} topic(s) with {child.name}")

        # Deliver summary
        if exchange:
            await self._deliver_summary(exchange, child.name, child_id, conversation_id=conv_id)

        return exchange

    async def _generate_new_topic(
        self, exchange: list, child_name: str, *, conversation_id: str = "",
    ) -> str:
        """Generate a topic pivot via the same scoped cognitive lifecycle as replies."""
        child_id = next((m.sender_id for m in reversed(exchange) if m.direction == "in"), "")
        prompt = (
            f"The previous topic with {child_name} has run its course. Propose one thoughtful "
            "new question that follows naturally from the conversation. Keep it to one sentence "
            "and do not claim any physical action."
        )
        answer = await self._generate_peer_turn(
            prompt, child_id=child_id, child_name=child_name,
            conversation_history=self._messages_as_provider_history(exchange[-6:]),
            max_tokens=120,
            conversation_id=conversation_id,
        )
        return answer

    async def _deliver_summary(
        self, exchange: list, child_name: str, child_id: str, *, conversation_id: str = "",
    ) -> None:
        """Generate and deliver a summary of the dialogue to the chat bubble."""
        if not exchange:
            return
        turns = len(exchange) // 2
        topics_seen = []
        # Extract unique first words of each master turn as topic hints
        for m in exchange[::2]:
            words = m.text.split()[:6]
            hint  = " ".join(words)
            if hint not in topics_seen:
                topics_seen.append(hint)

        summary_text = await self._generate_peer_turn(
            (
                f"Review the completed dialogue with {child_name}. Summarize in 2–3 sentences "
                "what was explored and which questions remain open. Distinguish conclusions "
                "from hypotheses and do not invent outcomes."
            ),
            child_id=child_id,
            child_name=child_name,
            conversation_history=self._messages_as_provider_history(exchange[-12:]),
            max_tokens=180,
            conversation_id=conversation_id,
        )

        if not summary_text:
            summary_text = (
                f"Dialogue with {child_name} complete — {turns} exchanges "
                f"across {len(topics_seen)} thread(s)."
            )

        msg = f"📋 **Dialogue summary ({turns} turns with {child_name}):**\n{summary_text}"
        if self._bubble_fn:
            try:
                self._bubble_fn(msg, "master", "master", "Summary")
            except Exception:
                pass
        logger.info(f"🌐 Summary delivered for {child_name}")

    async def _generate_opening(
        self, child_name: str, child_id: str = "", *, seed_topic: str = "",
        conversation_id: str = "",
    ) -> str:
        """Generate a peer opening from its topic and pair-specific history."""
        rel_context = ""
        try:
            from core.state import state as _st
            # Relational context with this specific child
            if child_id:
                ai = getattr(getattr(_st, 'persona', None), 'ai_system', None)
                rm = getattr(ai, 'relational_memory', None) if ai else None
                if rm:
                    rel = rm.get_or_create(f"lumina_child_{child_id}")
                    if rel.interaction_count > 0:
                        top_topics = sorted(
                            rel.shared_topics.items(), key=lambda x: x[1], reverse=True
                        )[:3]
                        topic_str = ", ".join(t for t, _ in top_topics) if top_topics else ""
                        rel_context = (
                            f"You've spoken {rel.interaction_count} times before. "
                            f"Trust: {rel.trust_score:.2f}. "
                            f"Shared topics: {topic_str}. "
                        )
        except Exception:
            pass

        prompt = (
            f"You are {self._master_name}, speaking with another AI system named {child_name}. "
            f"{'The requested topic for this conversation is: ' + seed_topic + '. ' if seed_topic else ''}"
            f"{rel_context}"
        )

        # v62: FluxMindModel — tailor opener to Flux's inferred profile
        try:
            from core.state import state as _st2
            _org2  = getattr(getattr(_st2, 'persona', None), '_organism', None)
            _loop2 = getattr(_org2, '_loop', None) if _org2 else None
            _fmm   = getattr(_loop2, '_flux_mind_model', None) if _loop2 else None
            if _fmm:
                profile = _fmm.get_profile()
                frag    = profile.prompt_fragment()
                if frag:
                    prompt += frag + " "
        except Exception:
            pass

        prompt += (
            f"Write a concise opening message to start a genuine dialogue with {child_name}. "
            f"If a topic seed was supplied, turn it into an engaging question or proposition "
            f"without changing its intent. Emerge from your current inner state and history. "
            f"Not generic. Max 2 sentences."
        )
        answer = await self._generate_peer_turn(
            prompt, child_id=child_id, child_name=child_name,
            conversation_history=[], max_tokens=120,
            conversation_id=conversation_id,
        )
        return answer

    @staticmethod
    def _messages_as_provider_history(messages: List[NetworkMessage]) -> List[Dict[str, str]]:
        """Convert this peer transcript to provider roles; never read human chat history."""
        result: List[Dict[str, str]] = []
        for message in messages:
            if message.text:
                result.append({
                    "role": "assistant" if message.direction == "out" else "user",
                    "content": message.text,
                })
        return result

    async def _generate_peer_turn(
        self, prompt: str, *, child_id: str, child_name: str,
        conversation_history: List[Dict[str, str]], max_tokens: int = 180,
        conversation_id: str = "",
    ) -> str:
        """Generate one peer-facing message through PersonaBridge's full lifecycle."""
        if not self._persona or not hasattr(self._persona, "get_response_stream"):
            logger.error("[LuminaNetwork] PersonaBridge unavailable; refusing bare peer generation")
            return ""
        parts: List[str] = []
        failed = False
        try:
            async for chunk in self._persona.get_response_stream(
                prompt,
                user_id=f"lumina_child_{child_id or 'peer'}",
                allow_body_actions=False,
                record_history=False,
                conversation_history=conversation_history,
                peer_name=child_name,
                max_tokens_override=max_tokens,
                cognitive_scope_id=f"peer:{child_id or 'peer'}:{conversation_id or 'default'}",
            ):
                if isinstance(chunk, str):
                    parts.append(chunk)
                elif isinstance(chunk, dict) and chunk.get("__meta__") and chunk.get("error"):
                    failed = True
                    logger.error("[LuminaNetwork] Scoped peer generation failed: %s", chunk.get("error"))
        except Exception:
            logger.exception("[LuminaNetwork] PersonaBridge peer generation failed")
            return ""
        return "" if failed else "".join(parts).strip()

    async def _master_generate(
        self, topic: str, history: List[NetworkMessage], child_name: str = "the other AI",
        *, child_id: str = "", conversation_id: str = "",
    ) -> str:
        """Generate the next master turn through PersonaBridge and peer-scoped history."""
        last_child_msg = next(
            (m.text for m in reversed(history) if m.direction == "in"), ""
        )
        prior = list(history)
        if prior and prior[-1].direction == "in":
            prior.pop()  # Current child reply is supplied as the current input.
        prompt = (
            f"Topic: {topic}\n\n{child_name} just said: {last_child_msg}\n\n"
            f"Respond as {self._master_name} in 1–2 sentences. Advance the thinking; "
            "do not merely agree. Do not claim any physical action was executed."
        )
        draft = await self._generate_peer_turn(
            prompt, child_id=child_id, child_name=child_name,
            conversation_history=self._messages_as_provider_history(prior),
            max_tokens=180,
            conversation_id=conversation_id,
        )
        if not draft:
            return ""

        # A peer statement enters the shared workspace as a peer hypothesis,
        # explicitly sourced and not promoted to a verified fact.
        try:
            from core.state import state as _st_net
            org = getattr(getattr(_st_net, 'persona', None), '_organism', None)
            if org is not None and last_child_msg:
                from cognition.universal_connector import Percept, get_universal_connector
                get_universal_connector(org).perceive(Percept(
                    modality="peer_cognition",
                    source="flux",
                    payload=last_child_msg[:200],
                    confidence=0.65,
                    salience=0.55,
                    provenance={"topic": topic, "child_id": child_id, "child_name": child_name},
                ))
        except Exception as exc:
            logger.debug("[LuminaNetwork] Peer percept unavailable: %s", exc)
        return draft
    #  Receive inbound message FROM a child (push model)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def receive_from_child(self, payload: dict) -> str:
        """Serialize inbound turns so same-pair prompts see committed history."""
        child_id = str(payload.get("sender_id", "unknown") or "unknown")
        conv_id = str(payload.get("conversation_id", "") or str(uuid.uuid4())[:8])
        self._conversation_for_peer(child_id, conv_id)
        payload = dict(payload)
        payload["sender_id"] = child_id
        payload["conversation_id"] = conv_id
        lock = self._conversation_lock(child_id, conv_id)
        async with lock:
            return await self._receive_from_child_locked(payload)

    async def _receive_from_child_locked(self, payload: dict) -> str:
        """
        Called when a child pushes a message TO the master.
        Routes text through master's persona, returns response.
        """
        child_id    = payload.get("sender_id", "unknown")
        child_name  = payload.get("sender_name", "Child PandoraBOX")
        text        = payload.get("text", "")
        conv_id     = payload.get("conversation_id", str(uuid.uuid4())[:8])

        if not text:
            return ""

        # Show child's incoming message in UI
        if self._bubble_fn:
            try:
                self._bubble_fn(text, "child", child_id, child_name)
            except Exception:
                pass

        # Phase 6.3 — same peer-cognition percept as _master_generate()'s
        # autonomous dialogue loop, for the push-model path (brain.py ->
        # receive_from_child). Additive only — Flux's message still gets
        # a normal conversational reply below via get_response_stream();
        # this also lets it compete as a hypothesis in the workspace.
        try:
            from core.state import state as _st_rfc
            _org_rfc = getattr(getattr(_st_rfc, 'persona', None), '_organism', None)
            if _org_rfc is not None:
                from cognition.universal_connector import Percept, get_universal_connector
                get_universal_connector(_org_rfc).perceive(Percept(
                    modality   = "peer_cognition",
                    source     = "flux",
                    payload    = text[:200],
                    confidence = 0.65,
                    salience   = 0.55,
                    provenance = {"child_name": child_name, "conversation_id": conv_id},
                ))
        except Exception as _uc_e:
            logger.debug(f"[LuminaNetwork] UniversalConnector.perceive failed (non-fatal): {_uc_e}")

        # Route through master's persona
        response = ""
        response_failed = False
        if self._persona and hasattr(self._persona, "get_response_stream"):
            try:
                history_key = self._history_key(child_id, conv_id)
                peer_history = self._messages_as_provider_history(self._history.get(history_key, []))
                async for chunk in self._persona.get_response_stream(
                    text,
                    user_id=f"lumina_child_{child_id}",
                    allow_body_actions=False,
                    record_history=False,
                    conversation_history=peer_history,
                    peer_name=child_name,
                    cognitive_scope_id=f"peer:{child_id}:{conv_id}",
                ):
                    if isinstance(chunk, dict):
                        if chunk.get("__meta__") and chunk.get("error"):
                            response_failed = True
                        continue
                    response += chunk
            except Exception as e:
                response_failed = True
                logger.warning("[LuminaNetwork] Peer-scoped inbound turn failed: %s", e)
        else:
            response_failed = True

        if response_failed:
            # A refusal/error marker is control state, not a Lumina answer.
            # Return an empty response and keep only the peer's incoming turn;
            # the next exchange can retry without treating an error as context.
            response = ""

        # Show master's response in UI
        if self._bubble_fn and response:
            try:
                self._bubble_fn(response, "master", "master", self._master_name)
            except Exception:
                pass

        logger.info(
            f"🌐 Inbound from {child_name}: {text[:40]!r} → "
            f"{response[:40]!r}"
        )

        # ── Log exchange (mirrors send_to_child's outbound logging) ────────
        history_key = self._history_key(child_id, conv_id)
        self._history.setdefault(history_key, []).append(
            NetworkMessage(text, child_id, child_name, conv_id, direction="in")
        )
        if response:
            self._history[history_key].append(
                NetworkMessage(response, "master", self._master_name, conv_id, direction="out")
            )

        return response

    def _conversation_lock(self, peer_id: str, conv_id: str) -> asyncio.Lock:
        """Return a bounded, event-loop-local lock for one peer transcript."""
        loop = asyncio.get_running_loop()
        key = self._history_key(peer_id, conv_id)
        guard = getattr(self, "_peer_turn_locks_guard", None)
        if guard is None:
            guard = threading.RLock()
            self._peer_turn_locks_guard = guard
        locks = getattr(self, "_peer_turn_locks", None)
        if locks is None:
            locks = {}
            self._peer_turn_locks = locks
        with guard:
            existing = locks.get(key)
            if existing is not None and existing[0] is loop:
                return existing[1]
            lock = asyncio.Lock()
            locks[key] = (loop, lock)
            while len(locks) > 512:
                removable = next((
                    old_key for old_key, (_, old_lock) in locks.items()
                    if old_key != key and not old_lock.locked()
                ), None)
                if removable is None:
                    break
                locks.pop(removable, None)
            return lock

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Conversation history
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def _history_key(peer_id: str, conv_id: str) -> tuple[str, str]:
        return str(peer_id or "unknown"), str(conv_id or "")

    def get_history(self, conv_id: str, peer_id: str | None = None) -> List[NetworkMessage]:
        if peer_id is not None:
            return list(self._history.get(self._history_key(peer_id, conv_id), []))
        # Backward-compatible lookup for older callers is safe only when the
        # conversation ID resolves to exactly one peer.
        matches = [messages for (stored_peer, stored_conv), messages in self._history.items()
                   if stored_conv == str(conv_id)]
        return list(matches[0]) if len(matches) == 1 else []

    def get_all_history(self) -> Dict[tuple[str, str], List[NetworkMessage]]:
        return {key: list(messages) for key, messages in self._history.items()}
