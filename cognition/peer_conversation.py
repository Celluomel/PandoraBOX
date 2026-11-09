"""Peer-only conversation history and generation boundary for Lumina links."""

from __future__ import annotations

import asyncio
import threading
from typing import Any


class PeerTurnUnavailable(RuntimeError):
    """A peer turn could not produce a valid cognitive response."""


class PeerConversationStore:
    """Keep network-peer transcripts separate from human memory and LLM history."""

    def __init__(self, max_messages: int = 24, max_conversations: int = 256):
        self._max_messages = max(2, int(max_messages))
        self._max_conversations = max(1, int(max_conversations))
        self._histories: dict[tuple[str, str], list[dict[str, str]]] = {}
        self._locks: dict[tuple[str, str], tuple[asyncio.AbstractEventLoop, asyncio.Lock]] = {}
        self._guard = threading.RLock()

    def history(self, sender_id: str, conversation_id: str) -> list[dict[str, str]]:
        key = (str(sender_id), str(conversation_id))
        with self._guard:
            return [dict(message) for message in self._histories.get(key, [])]

    def record_exchange(
        self, sender_id: str, conversation_id: str, incoming: str, response: str,
    ) -> None:
        key = (str(sender_id), str(conversation_id))
        exchange = [
            {"role": "user", "content": str(incoming)},
            {"role": "assistant", "content": str(response)},
        ]
        with self._guard:
            history = self._histories.pop(key, [])
            history.extend(exchange)
            if len(history) > self._max_messages:
                del history[:-self._max_messages]
            self._histories[key] = history
            while len(self._histories) > self._max_conversations:
                self._histories.pop(next(iter(self._histories)))

    def _conversation_lock(self, key: tuple[str, str]) -> asyncio.Lock:
        loop = asyncio.get_running_loop()
        with self._guard:
            existing = self._locks.get(key)
            if existing is not None and existing[0] is loop:
                return existing[1]
            lock = asyncio.Lock()
            self._locks[key] = (loop, lock)
            while len(self._locks) > self._max_conversations:
                removable = next((
                    old_key for old_key, (_, old_lock) in self._locks.items()
                    if old_key != key and not old_lock.locked()
                ), None)
                if removable is None:
                    break
                self._locks.pop(removable, None)
            return lock

    @staticmethod
    def _public_cognitive_trace(persona: Any, expected_scope: str) -> dict | None:
        """Expose bounded stage evidence without prompt or exception details."""
        getter = getattr(persona, "get_last_turn_trace", None)
        if not callable(getter):
            return None
        try:
            trace = getter()
        except Exception:
            return None
        if not isinstance(trace, dict) or trace.get("cognitive_scope_id") != expected_scope:
            return None
        stages = {}
        raw_stages = trace.get("stages", {})
        if isinstance(raw_stages, dict):
            for name, stage in list(raw_stages.items())[:80]:
                if isinstance(stage, dict) and isinstance(stage.get("status"), str):
                    stages[str(name)[:80]] = {
                        "status": stage["status"][:48],
                        **({"at": stage["at"]} if isinstance(stage.get("at"), (int, float)) else {}),
                    }
        sources = {}
        raw_sources = trace.get("context_sources", {})
        if isinstance(raw_sources, dict):
            for name, source in list(raw_sources.items())[:40]:
                if isinstance(source, dict) and isinstance(source.get("status"), str):
                    sources[str(name)[:80]] = {"status": source["status"][:48]}
        return {
            "turn_id": str(trace.get("turn_id", ""))[:100],
            "scope": "peer",
            "peer_name": str(trace.get("peer_name", ""))[:80],
            "cognitive_scope_id": expected_scope,
            "status": str(trace.get("status", "unknown"))[:48],
            "stages": stages,
            "context_sources": sources,
        }

    async def generate_reply(
        self,
        persona: Any,
        *,
        sender_id: str,
        sender_name: str,
        conversation_id: str,
        text: str,
        include_trace: bool = False,
    ) -> str | dict:
        """Run a peer-scoped PersonaBridge turn and commit only successful turns."""
        if not persona or not callable(getattr(persona, "get_response_stream", None)):
            raise PeerTurnUnavailable("PersonaBridge is unavailable for peer dialogue")

        peer_id = str(sender_id or "unknown")
        peer_name = str(sender_name or "Network peer")
        conv_id = str(conversation_id)
        lock = self._conversation_lock((peer_id, conv_id))
        async with lock:
            prior_history = self.history(peer_id, conv_id)
            parts: list[str] = []
            try:
                async for chunk in persona.get_response_stream(
                    text,
                    user_id=f"lumina_peer_{peer_id}",
                    allow_body_actions=False,
                    record_history=False,
                    conversation_history=prior_history,
                    peer_name=peer_name,
                    cognitive_scope_id=f"peer:{peer_id}:{conv_id}",
                ):
                    if isinstance(chunk, dict):
                        if chunk.get("__meta__") and chunk.get("error"):
                            raise PeerTurnUnavailable("Peer-scoped cognitive generation failed")
                        continue
                    if chunk is not None:
                        parts.append(str(chunk))
            except PeerTurnUnavailable:
                raise
            except Exception as exc:
                raise PeerTurnUnavailable("Peer-scoped cognitive generation failed") from exc

            response = "".join(parts).strip()
            if not response:
                raise PeerTurnUnavailable("Peer-scoped cognitive generation returned no answer")

            expected_scope = f"peer:{peer_id}:{conv_id}"
            cognitive_trace = self._public_cognitive_trace(persona, expected_scope)
            self.record_exchange(peer_id, conv_id, text, response)
            if include_trace:
                return {"response": response, "cognitive_trace": cognitive_trace}
            return response


peer_conversation_store = PeerConversationStore()
