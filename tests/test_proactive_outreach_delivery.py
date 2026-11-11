import asyncio
import sys
import threading
import unittest
from collections import deque
from dataclasses import asdict
from types import ModuleType, SimpleNamespace as NS
from unittest.mock import patch

from cognition.proactive_outreach import (
    OutreachEvent,
    OutreachState,
    ProactiveOutreachEngine,
)
from cognition.goal_action_executor import GoalActionExecutor
from managers.messaging_manager import MessagingManager


class ProactiveOutreachDeliveryTests(unittest.TestCase):
    def test_messaging_manager_reports_platform_acceptance(self):
        class Bot:
            async def send_message(self, **kwargs):
                return object()

        manager = MessagingManager.__new__(MessagingManager)
        manager._tg_app = NS(bot=Bot())

        self.assertTrue(asyncio.run(manager.send_message("telegram", "123", "hello")))
        self.assertFalse(asyncio.run(manager.send_message("unsupported", "123", "hello")))

    def test_telegram_failure_is_not_reported_as_sent(self):
        class Bot:
            async def send_message(self, **kwargs):
                raise RuntimeError("provider unavailable")

        manager = MessagingManager.__new__(MessagingManager)
        manager._tg_app = NS(bot=Bot())

        self.assertFalse(asyncio.run(manager.send_message("telegram", "123", "hello")))

    def test_outreach_counts_only_successful_platform_acceptance(self):
        event = OutreachEvent(
            user_id="user-a", message_text="hello", platform="telegram",
            delivery_status="pending",
        )
        engine = ProactiveOutreachEngine.__new__(ProactiveOutreachEngine)
        engine._lock = threading.RLock()
        engine._state = OutreachState(outreach_log=[asdict(event)])
        engine._save = lambda: None

        failed_core_state = ModuleType("core.state")
        failed_core_state.state = NS(persona=None)
        with patch.dict(sys.modules, {"core.state": failed_core_state}):
            engine._complete_delivery(event.event_id, False, "provider unavailable")
        failed = engine._state.outreach_log[0]
        self.assertFalse(failed["sent"])
        self.assertEqual(failed["delivery_status"], "failed")
        self.assertEqual(engine._state.total_sent, 0)
        self.assertNotIn("user-a", engine._state.last_outreach_by_user)

        with patch.dict(sys.modules, {"core.state": failed_core_state}):
            engine._complete_delivery(event.event_id, True)
        delivered = engine._state.outreach_log[0]
        self.assertTrue(delivered["sent"])
        self.assertEqual(delivered["delivery_status"], "accepted")
        self.assertEqual(engine._state.total_sent, 1)
        self.assertIn("user-a", engine._state.last_outreach_by_user)

    def test_async_outreach_records_provider_rejection(self):
        completed = threading.Event()

        class Messaging:
            _user_map = {"telegram:123": "user-a"}

            async def send_message(self, platform, target, text):
                return False

        engine = ProactiveOutreachEngine.__new__(ProactiveOutreachEngine)
        engine._lock = threading.RLock()
        engine._state = OutreachState()
        engine._save = lambda: None
        engine._o = NS(ai_system=NS(messaging_manager=Messaging()))
        engine._generate_message = lambda event, rel: "hello"
        complete = engine._complete_delivery

        def observe_completion(event_id, sent, error=""):
            complete(event_id, sent, error)
            completed.set()

        engine._complete_delivery = observe_completion
        engine._send(OutreachEvent(user_id="user-a"), rel=NS())

        self.assertTrue(completed.wait(timeout=2.0))
        self.assertEqual(len(engine._state.outreach_log), 1)
        failed = engine._state.outreach_log[0]
        self.assertFalse(failed["sent"])
        self.assertEqual(failed["delivery_status"], "failed")
        self.assertEqual(engine._state.total_sent, 0)

    def test_outreach_peek_does_not_consume_ui_delivery_queue(self):
        gae = GoalActionExecutor.__new__(GoalActionExecutor)
        gae._pending_delivery_lock = threading.Lock()
        gae._pending_user_question = "What should I inspect next?"
        gae._pending_insights = deque(["A queued insight"], maxlen=5)
        engine = ProactiveOutreachEngine.__new__(ProactiveOutreachEngine)
        engine._o = NS(_loop=NS(_goal_action_executor=gae))

        question = engine._peek_gae_content()
        self.assertEqual(question["text"], "What should I inspect next?")
        self.assertEqual(gae.peek_pending_user_question(), question["text"])
        self.assertEqual(gae.get_pending_user_question(), question["text"])
        self.assertIsNone(gae.peek_pending_user_question())

        insight = engine._peek_gae_content()
        self.assertEqual(insight["text"], "A queued insight")
        self.assertEqual(gae.peek_pending_insight(), insight["text"])
        self.assertEqual(gae.get_pending_insight(), insight["text"])
        self.assertIsNone(gae.peek_pending_insight())


if __name__ == "__main__":
    unittest.main()
