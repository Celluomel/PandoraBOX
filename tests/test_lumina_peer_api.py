import asyncio
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI

from core.lumina_peer_api import router


class LuminaPeerApiTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.transport = httpx.ASGITransport(
            app=self.app, client=("192.168.0.50", 32000),
        )
        self.config = SimpleNamespace(
            LUMINA_NETWORK_ROLE="child",
            LUMINA_MASTER_ID="master",
            LUMINA_NETWORK_API_KEY="shared-test-key",
            PERSONA_NAME="Flux",
        )
        self.state = SimpleNamespace(ready=True, persona=object())
        self.peer_store = SimpleNamespace(generate_reply=AsyncMock(return_value={
            "response": "FLUX response",
            "cognitive_trace": {
                "scope": "peer",
                "cognitive_scope_id": "peer:master:conversation-1",
                "status": "completed",
                "stages": {"primary_generation": {"status": "completed"}},
            },
        }))
        self.patches = [
            patch("managers.settings_manager.config", self.config),
            patch("core.state.state", self.state),
            patch("cognition.peer_conversation.peer_conversation_store", self.peer_store),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def _post(self, *, sender_id="master", api_key="shared-test-key"):
        headers = {"x-lumina-api-key": api_key} if api_key else {}
        async def send():
            async with httpx.AsyncClient(
                transport=self.transport, base_url="http://child.test",
            ) as client:
                return await client.post(
                    "/lumina-network/chat",
                    headers=headers,
                    json={
                        "text": "Describe your current reasoning state.",
                        "sender_id": sender_id,
                        "sender_name": "Lumina",
                        "conversation_id": "conversation-1",
                    },
                )
        return asyncio.run(send())

    def test_master_request_returns_peer_scoped_cognitive_trace(self):
        response = self._post()

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["response"], "FLUX response")
        self.assertEqual(payload["sender_name"], "Flux")
        self.assertEqual(payload["cognitive_trace"]["scope"], "peer")
        self.assertEqual(payload["cognitive_trace"]["status"], "completed")
        self.peer_store.generate_reply.assert_awaited_once_with(
            self.state.persona,
            sender_id="master",
            sender_name="Lumina",
            conversation_id="conversation-1",
            text="Describe your current reasoning state.",
            include_trace=True,
        )

    def test_child_rejects_wrong_role_sender_and_missing_remote_key(self):
        self.config.LUMINA_NETWORK_ROLE = "master"
        self.assertEqual(self._post().status_code, 403)
        self.config.LUMINA_NETWORK_ROLE = "child"
        self.assertEqual(self._post(sender_id="other-brain").status_code, 403)
        self.assertEqual(self._post(api_key="").status_code, 401)
        self.peer_store.generate_reply.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
