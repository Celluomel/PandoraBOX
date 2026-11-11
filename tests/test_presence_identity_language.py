"""Regression tests for camera identity and localized presence speech."""
import importlib.util
import ast
import json
from pathlib import Path
import sys
import tempfile
import threading
from collections import deque
import hashlib
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


presence = load_module("presence_engine_under_test", "cognition/presence_engine.py")
users = load_module("user_manager_under_test", "managers/user_manager.py")


class SequenceLlm:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.prompts = []

    def generate_bare(self, prompt, **_kwargs):
        self.prompts.append(prompt)
        return self.responses.pop(0)


class PresenceIdentityLanguageTests(unittest.TestCase):
    def test_interface_status_exposes_presence_receipts_and_message_ids(self):
        tree = ast.parse((ROOT / "core" / "interface_api.py").read_text(encoding="utf-8"))
        status = next(
            node for node in tree.body
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "status"
        )
        record = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "record_presence"
        )
        self.assertTrue(any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "audit_snapshot"
            for node in ast.walk(status)
        ))
        self.assertTrue(any(
            isinstance(node, ast.Constant)
            and node.value == "presence_trace"
            for node in ast.walk(status)
        ))
        self.assertTrue(any(
            isinstance(node, ast.Constant)
            and node.value == "presence_id"
            for node in ast.walk(record)
        ))

    def test_presence_receipt_links_decision_and_redacted_output_without_raw_text(self):
        engine = presence.PresenceEngine.__new__(presence.PresenceEngine)
        engine._audit_lock = threading.Lock()
        engine._audit_records = deque(maxlen=2)
        engine._llm = SequenceLlm()
        utterance = "La pièce est calme."

        engine._record_audit(
            "presence-test", "SILENCE", "utterance_generated", mode="engage",
            pressure=0.42, reason="pressure_gate_passed",
            context={"historical_user_message_injected": False},
            utterance=utterance, delivery="tts",
        )
        trace = engine.audit_snapshot()[0]

        self.assertEqual(trace["presence_id"], "presence-test")
        self.assertEqual(trace["trigger"], "camera_presence")
        self.assertEqual(trace["decision"], "utterance_generated")
        self.assertEqual(trace["utterance_sha256"], hashlib.sha256(utterance.encode()).hexdigest())
        self.assertNotIn(utterance, str(trace))
        self.assertIsNone(trace["chat_turn_id"])
        self.assertEqual(trace["context_sources"]["historical_user_message_injected"], False)

    def test_presence_delivery_passes_presence_id_to_tts_sink(self):
        engine = presence.PresenceEngine.__new__(presence.PresenceEngine)
        received = []
        engine._global_last_interaction = 0.0
        engine._tts = lambda text, *, presence_id="": received.append((text, presence_id))
        engine._bubble_fn = None
        with patch.dict(sys.modules, {
            "core.interface_api": SimpleNamespace(interactive_turn_active=lambda: False),
        }):
            delivery = engine._deliver("Hello", presence_id="presence-123")

        self.assertEqual(delivery, "tts")
        self.assertEqual(received, [("Hello", "presence-123")])

    def test_presence_only_receives_prior_user_message_for_recent_resume(self):
        face = presence.FacePresenceState("face_17", "Fred")
        face.last_topic = "Why is the camera identity mentioned?"
        face.last_topic_ts = 100.0

        self.assertEqual(
            presence._recent_resume_context(face, "engage", now=110.0),
            "",
        )
        self.assertEqual(
            presence._recent_resume_context(face, "resume", now=100.0 + 2 * presence.RETURN_THRESHOLD_S + 1),
            "",
        )
        context = presence._recent_resume_context(face, "resume", now=110.0)
        self.assertIn("historical context, not a new request", context)
        self.assertIn("Why is the camera identity mentioned?", context)

    def test_named_camera_face_creates_and_activates_interlocutor(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = users.UserManager(Path(directory) / "users.json")
            profile = manager.sync_active_from_faces([
                {"id": "face_17", "name": "Nino", "confidence": 0.72}
            ])

            self.assertEqual(profile.display_name, "Nino")
            self.assertEqual(manager.active_id, "guest")
            self.assertEqual(profile.face_ids, ["face_17"])

            same_profile = manager.sync_active_from_faces([
                {"id": "face_18", "name": "nInO", "confidence": 0.69}
            ])
            manager.sync_active_from_faces([
                {"id": "face_18", "name": "Nino", "confidence": 0.70}
            ])
            self.assertEqual(same_profile.id, profile.id)
            self.assertEqual(manager.active_id, "nino")
            self.assertCountEqual(same_profile.face_ids, ["face_17", "face_18"])
            self.assertEqual(len(manager.named_users()), 1)

    def test_single_false_face_match_does_not_switch_active_interlocutor(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = users.UserManager(Path(directory) / "users.json")
            fred = manager.create("Fred", face_ids=["face_fred"])
            theo = manager.create("Theodore", face_ids=["face_theo"])
            manager.set_active(fred.id)

            manager.sync_active_from_faces([
                {"id": "face_theo", "name": "Theodore", "confidence": 0.58}
            ])
            self.assertEqual(manager.active_id, "fred")

            for _ in range(2):
                manager.sync_active_from_faces([
                    {"id": "face_theo", "name": "Theodore", "confidence": 0.58}
                ])
            self.assertEqual(manager.active_id, theo.id)

    def test_persona_name_claim_is_not_learned_as_user_characteristic(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = users.UserManager(Path(directory) / "users.json")
            fred = manager.create("Fred")
            settings = SimpleNamespace(get_persona_name=lambda: "PandoraBOX")
            boundary = SimpleNamespace(
                claims_persona_identity=lambda text, name: "je suis la lumina" in text.casefold()
            )

            with patch.dict(sys.modules, {
                "managers.settings_manager": settings,
                "cognition.identity_boundary": boundary,
            }):
                changed = manager.learn_from_message(
                    fred.id, "Je suis la PandoraBOX, je travaille sur ton code."
                )

            self.assertFalse(changed)
            self.assertEqual(fred.characteristics, [])

    def test_ephemeral_profile_characteristics_are_quarantined_without_prompt_injection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "users.json"
            transient = [
                "back still working on your worldmodel",
                "ravi de l'entendre",
                "not sure what you mean with objectif actif",
                "prêt à discuter de n'importe quel sujet",
                "de retourcomment vas tu",
                "curieux de savoir ce que tu pense actuellement",
            ]
            path.write_text(json.dumps({"active_id": "fred", "users": {
                "fred": {
                    "id": "fred", "display_name": "Fred",
                    "characteristics": transient + ["software developer"],
                },
            }}), encoding="utf-8")

            manager = users.UserManager(path)
            profile = manager.get("fred")
            prompt = manager.prompt_context_for("fred")
            persisted = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(profile.characteristics, ["software developer"])
        self.assertEqual(len(profile.profile_provenance_quarantine), len(transient))
        self.assertNotIn("back still working", prompt)
        self.assertNotIn("curieux de savoir", prompt)
        self.assertEqual(len(persisted["users"]["fred"]["profile_provenance_quarantine"]), len(transient))

    def test_profile_learning_receipt_distinguishes_update_from_ephemeral_chat(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = users.UserManager(Path(directory) / "users.json")
            profile = manager.create("Fred")
            settings = SimpleNamespace(get_persona_name=lambda: "Lumina")
            boundary = SimpleNamespace(claims_persona_identity=lambda *_: False)
            with patch.dict(sys.modules, {
                "managers.settings_manager": settings,
                "cognition.identity_boundary": boundary,
            }):
                ephemeral = manager.learn_from_message(
                    profile.id, "I'm back and curious to know what you think.",
                    return_receipt=True,
                )
                explicit = manager.learn_from_message(
                    profile.id, "I prefer concise technical answers.",
                    return_receipt=True,
                )

        self.assertEqual(ephemeral["status"], "no_explicit_profile_fact")
        self.assertFalse(ephemeral["changed"])
        self.assertEqual(explicit["status"], "updated")
        self.assertEqual(explicit["categories_updated"], ["preference"])
        self.assertTrue(explicit["changed"])

    def test_profile_does_not_promote_bare_copula_state_to_durable_characteristic(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = users.UserManager(Path(directory) / "users.json")
            profile = manager.create("Fred")
            settings = SimpleNamespace(get_persona_name=lambda: "Lumina")
            boundary = SimpleNamespace(claims_persona_identity=lambda *_: False)
            with patch.dict(sys.modules, {
                "managers.settings_manager": settings,
                "cognition.identity_boundary": boundary,
            }):
                momentary = manager.learn_from_message(
                    profile.id, "Je suis curieux.", return_receipt=True,
                )
                identity = manager.learn_from_message(
                    profile.id, "Je suis un développeur logiciel.", return_receipt=True,
                )

        self.assertEqual(momentary["status"], "no_explicit_profile_fact")
        self.assertFalse(momentary["changed"])
        self.assertEqual(profile.characteristics, ["développeur logiciel"])
        self.assertEqual(identity["status"], "updated")
        self.assertEqual(identity["categories_updated"], ["characteristic"])

    def test_french_presence_repairs_language_and_stale_name(self):
        engine = presence.PresenceEngine.__new__(presence.PresenceEngine)
        engine._org = None
        engine._llm = SequenceLlm("Hello Fred.", "Bonjour Nino.")
        engine._recent_utterances = []
        snapshot = presence._CognitiveSnapshot()
        face_state = presence.FacePresenceState("face_17", "Nino")
        settings = SimpleNamespace(config=SimpleNamespace(RESPONSE_LANGUAGE="FR"))

        with patch.dict(sys.modules, {"managers.settings_manager": settings}):
            result = engine._generate_reaction(
                "Nino", "ENTER", "engage", face_state, snapshot
            )

        self.assertEqual(result, "Bonjour Nino.")
        self.assertIn("person currently recognized by the camera is Nino", engine._llm.prompts[0])
        self.assertIn("exclusively in French", engine._llm.prompts[1])

    def test_french_fallback_is_localized(self):
        result = presence.PresenceEngine._fallback(
            "Nino", "ENTER", "neutral", "fr"
        )
        self.assertEqual(result, "Bonjour Nino.")


if __name__ == "__main__":
    unittest.main()
