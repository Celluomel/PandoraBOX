"""
UserManager — Persistent user profiles with face recognition bridge.

Responsibilities:
  - Store and retrieve UserProfile records (data/users/users.json)
  - Track the currently active user across the session
  - Bridge face_id (vision) → user_id (memory/persona)
  - Auto-switch active user when a known face is detected
  - Provide user_id to RelationalMemory, FAISS memory, and AgentController

Profile fields:
  id           : slug, e.g. "alice"  (used as the key everywhere)
  display_name : "Alice"
  face_ids     : ["face_1", "face_3"]  ← links to vision_manager face_encodings
  notes        : free-text bio / preferences the AI should know
  color        : hex accent colour for UI avatar chip  e.g. "#6366f1"
  created_at   : ISO timestamp
  last_seen    : ISO timestamp (updated on every interaction)
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import tempfile
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

USERS_FILE = Path("data/users/users.json")

# ── Palette for auto-assigned avatar colours ─────────────────────────────────
_PALETTE = [
    "#6366f1", "#8b5cf6", "#ec4899", "#f97316",
    "#22c55e", "#06b6d4", "#eab308", "#ef4444",
]


def _slugify(name: str) -> str:
    """Turn a display name into a safe slug: 'Alice B.' → 'alice_b'"""
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or f"user_{int(time.time())}"


# ─────────────────────────────────────────────────────────────────────────────
#  Data model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class UserProfile:
    id:           str
    display_name: str
    face_ids:     List[str]  = field(default_factory=list)
    notes:        str        = ""          # free-text, injected into system prompt
    preferences:  List[str]  = field(default_factory=list)
    dislikes:     List[str]  = field(default_factory=list)
    interests:    List[str]  = field(default_factory=list)
    characteristics: List[str] = field(default_factory=list)
    profile_fact_provenance: Dict[str, Dict[str, List[Dict]]] = field(default_factory=dict)
    profile_provenance_quarantine: List[Dict] = field(default_factory=list)
    color:        str        = "#6366f1"
    created_at:   str        = field(default_factory=lambda: datetime.now().isoformat())
    last_seen:    str        = field(default_factory=lambda: datetime.now().isoformat())

    def touch(self):
        self.last_seen = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict) -> "UserProfile":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def short_bio(self) -> str:
        """One-liner for prompt injection."""
        parts = [f"User's name: {self.display_name}."]
        if self.notes:
            parts.append(self.notes.strip())
        if self.preferences:
            parts.append("Preferences: " + "; ".join(self.preferences[:4]) + ".")
        if self.dislikes:
            parts.append("Dislikes: " + "; ".join(self.dislikes[:4]) + ".")
        if self.interests:
            parts.append("Interests: " + ", ".join(self.interests[:5]) + ".")
        if self.characteristics:
            parts.append("Known characteristics: " + ", ".join(self.characteristics[:4]) + ".")
        return " ".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
#  Manager
# ─────────────────────────────────────────────────────────────────────────────

class UserManager:
    """
    Singleton — import and use `user_manager` from this module.

    Thread-safe: all mutations go through _lock.
    Auto-saves on every write.
    """

    GUEST_ID = "guest"

    def __init__(self, path: Path = USERS_FILE):
        self._path   = path
        self._lock   = threading.RLock()
        self._users: Dict[str, UserProfile] = {}
        self._prompt_cache: Dict[str, str] = {}
        self._active_id: str = self.GUEST_ID
        self._face_candidate_id: Optional[str] = None
        self._face_candidate_hits = 0
        self._face_candidate_at = 0.0
        self._load()
        self._ensure_guest()

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def create(
        self,
        display_name: str,
        face_ids: List[str] = None,
        notes: str = "",
        color: str = None,
    ) -> UserProfile:
        """Create a new user. Returns the profile."""
        with self._lock:
            base   = _slugify(display_name)
            uid    = base
            suffix = 2
            while uid in self._users:        # avoid slug collision
                uid = f"{base}_{suffix}"
                suffix += 1

            color = color or _PALETTE[len(self._users) % len(_PALETTE)]
            profile = UserProfile(
                id=uid,
                display_name=display_name,
                face_ids=face_ids or [],
                notes=notes,
                color=color,
            )
            self._users[uid] = profile
            self._prompt_cache.pop(uid, None)
            self._save()
            logger.info(f"👤 Created user: {uid} ({display_name})")
            return profile

    def get(self, user_id: str) -> Optional[UserProfile]:
        return self._users.get(user_id)

    def get_or_guest(self, user_id: str) -> UserProfile:
        return self._users.get(user_id) or self._users[self.GUEST_ID]

    def all_users(self) -> List[UserProfile]:
        with self._lock:
            return list(self._users.values())

    def named_users(self) -> List[UserProfile]:
        """All users except the guest placeholder."""
        return [u for u in self.all_users() if u.id != self.GUEST_ID]

    def update(
        self,
        user_id: str,
        display_name: str = None,
        notes: str = None,
        color: str = None,
    ) -> Optional[UserProfile]:
        with self._lock:
            profile = self._users.get(user_id)
            if not profile:
                return None
            if display_name is not None:
                profile.display_name = display_name
            if notes is not None:
                profile.notes = notes
            if color is not None:
                profile.color = color
            self._prompt_cache.pop(user_id, None)
            self._save()
            return profile

    def delete(self, user_id: str) -> bool:
        if user_id == self.GUEST_ID:
            return False
        with self._lock:
            if user_id not in self._users:
                return False
            del self._users[user_id]
            if self._active_id == user_id:
                self._active_id = self.GUEST_ID
            self._save()
            logger.info(f"🗑️  Deleted user: {user_id}")
            return True

    # ── Face ↔ User bridge ───────────────────────────────────────────────────

    def link_face(self, user_id: str, face_id: str) -> bool:
        """Associate a vision face_id with this user."""
        with self._lock:
            profile = self._users.get(user_id)
            if not profile:
                return False
            if face_id not in profile.face_ids:
                profile.face_ids.append(face_id)
                self._prompt_cache.pop(user_id, None)
                self._save()
                logger.info(f"🔗 Linked face {face_id} → user {user_id}")
            return True

    def unlink_face(self, user_id: str, face_id: str) -> bool:
        with self._lock:
            profile = self._users.get(user_id)
            if not profile or face_id not in profile.face_ids:
                return False
            profile.face_ids.remove(face_id)
            self._save()
            return True

    def find_by_face(self, face_id: str) -> Optional[UserProfile]:
        """Return the user who owns this face_id, or None."""
        for profile in self._users.values():
            if face_id in profile.face_ids:
                return profile
        return None

    def find_by_name(self, display_name: str) -> Optional[UserProfile]:
        """Return a named profile using a case-insensitive display-name match."""
        wanted = str(display_name or "").strip().casefold()
        if not wanted:
            return None
        for profile in self._users.values():
            if profile.id != self.GUEST_ID and profile.display_name.casefold() == wanted:
                return profile
        return None

    def resolve_faces(self, detected_faces: List[Dict]) -> Optional[UserProfile]:
        """
        Given a list of dicts from vision_manager.detect_faces(),
        return the highest-confidence known user found, or None.

        Call this every frame and pass the result to set_active_from_face().
        """
        best: Optional[UserProfile] = None
        best_conf = 0.0
        for face in detected_faces:
            fid  = face.get("id")
            conf = face.get("confidence", 0.0)
            if fid and conf > best_conf:
                profile = self.find_by_face(fid)
                if profile:
                    best      = profile
                    best_conf = conf
        return best

    # ── Active user ──────────────────────────────────────────────────────────

    @property
    def active_id(self) -> str:
        return self._active_id

    def resolve_interaction_user_id(self, user_id: str | None) -> str:
        """Resolve the Brain API's generic default to the persisted active user.

        Explicit identities remain untouched. This lets headless `/chat`
        requests use the same named profile as the UI without guessing from
        message text or silently switching an explicitly selected user.
        """
        requested = str(user_id or "").strip()
        if requested.casefold() not in {"", "default"}:
            return requested
        with self._lock:
            active_id = str(self._active_id or "").strip()
            if active_id and active_id in self._users:
                return active_id
        return self.GUEST_ID

    @property
    def active(self) -> UserProfile:
        return self.get_or_guest(self._active_id)

    def set_active(self, user_id: str) -> bool:
        """Manually switch the active user."""
        with self._lock:
            if user_id not in self._users:
                return False
            if self._active_id != user_id:
                self._active_id = user_id
                self._users[user_id].touch()
                self._save()
                logger.info(f"👤 Active user → {user_id}")
            return True

    def set_active_from_face(self, profile: Optional[UserProfile]) -> bool:
        """
        Called when vision detects faces.
        Only switches if confidence is high enough.
        Returns True if the active user changed.
        """
        if not profile:
            return False
        if profile.id == self._active_id:
            return False
        changed = self.set_active(profile.id)
        if changed:
            logger.info(f"🎥 Auto-switched to user '{profile.display_name}' via face recognition")
        return changed

    def sync_active_from_faces(self, detected_faces: List[Dict]) -> Optional[UserProfile]:
        """Resolve the strongest recognized face and make it the active profile.

        A face can be named in the vision database before an interlocutor
        profile exists.  In that case, reuse a same-name profile or create one
        and link the recognition id.  This keeps camera presence, chat memory,
        and the active interlocutor on the same identity.
        """
        profile = self.resolve_faces(detected_faces or [])
        if profile is None:
            candidates = []
            for face in detected_faces or []:
                face_id = str(face.get("id") or "").strip()
                name = str(face.get("name") or "").strip()
                if (
                    not face_id
                    or face_id == "__unknown__"
                    or name.casefold() in {"", "unknown", "unknown person", "known person"}
                ):
                    continue
                try:
                    confidence = float(face.get("confidence", 0.0) or 0.0)
                except (TypeError, ValueError):
                    confidence = 0.0
                candidates.append((confidence, face_id, name))

            if candidates:
                _, face_id, name = max(candidates, key=lambda item: item[0])
                profile = self.find_by_name(name)
                if profile is None:
                    profile = self.create(name, face_ids=[face_id])
                    logger.info("Created interlocutor profile for recognized face '%s'", name)
                elif face_id not in profile.face_ids:
                    self.link_face(profile.id, face_id)

        if profile:
            matching_confidences = [
                float(face.get("confidence", 0.0) or 0.0)
                for face in detected_faces or []
                if self.find_by_face(str(face.get("id") or "")) is profile
            ]
            confidence = max(matching_confidences, default=0.0)
            now = time.monotonic()
            if profile.id == self._active_id:
                self._face_candidate_id = None
                self._face_candidate_hits = 0
            elif confidence >= 0.50:
                if (
                    self._face_candidate_id == profile.id
                    and now - self._face_candidate_at <= 5.0
                ):
                    self._face_candidate_hits += 1
                else:
                    self._face_candidate_id = profile.id
                    self._face_candidate_hits = 1
                self._face_candidate_at = now
                if self._face_candidate_hits >= 3:
                    self.set_active_from_face(profile)
                    self._face_candidate_id = None
                    self._face_candidate_hits = 0
            profile.touch()
        return profile

    def touch_active(self):
        """Update last_seen for the active user."""
        with self._lock:
            self.active.touch()
            self._save()

    # ── Prompt helper ────────────────────────────────────────────────────────

    def active_context_for_prompt(self) -> str:
        """
        Returns a short string for injection into the system prompt.
        Empty string if the active user is just 'guest'.
        """
        profile = self.active
        if profile.id == self.GUEST_ID:
            return ""
        return self.prompt_context_for(profile.id)

    def prompt_context_for(self, user_id: str) -> str:
        """Return a small cached profile block for the critical chat path."""
        profile = self.get(user_id)
        if not profile or profile.id == self.GUEST_ID:
            return ""
        with self._lock:
            self._quarantine_ephemeral_characteristics(profile)
            cached = self._prompt_cache.get(profile.id)
            if cached is None:
                parts = [f"User's name: {profile.display_name}."]
                if profile.notes.strip():
                    parts.append(
                        "Legacy profile notes (source turn not recorded; treat as unverified): "
                        + profile.notes.strip()
                    )
                for kind, label in (
                    ("preference", "preferences"),
                    ("dislike", "dislikes"),
                    ("interest", "interests"),
                    ("characteristic", "characteristics"),
                ):
                    field_name = {
                        "preference": "preferences",
                        "dislike": "dislikes",
                        "interest": "interests",
                        "characteristic": "characteristics",
                    }[kind]
                    values = getattr(profile, field_name)
                    provenanced = []
                    legacy = []
                    for value in values:
                        fact_key = hashlib.sha256(value.casefold().encode("utf-8")).hexdigest()
                        provenance = profile.profile_fact_provenance
                        category = provenance.get(kind, {}) if isinstance(provenance, dict) else {}
                        sources = category.get(fact_key, []) if isinstance(category, dict) else []
                        if isinstance(sources, list) and sources and isinstance(sources[-1], dict):
                            source = sources[-1]
                            turn_id = str(source.get("turn_id") or "")
                            source_hash = str(source.get("source_sha256") or "")[:12]
                            source_ref = ", ".join(
                                item for item in (
                                    f"turn {turn_id}" if turn_id else "",
                                    f"source {source_hash}" if source_hash else "",
                                ) if item
                            )
                            provenanced.append(
                                f"{value} [explicit user statement"
                                f"{': ' + source_ref if source_ref else ''}]"
                            )
                        else:
                            legacy.append(value)
                    if provenanced:
                        parts.append(f"User-stated {label}: " + "; ".join(provenanced[:4]) + ".")
                    if legacy:
                        parts.append(
                            f"Legacy {label} without source receipt (unverified): "
                            + "; ".join(legacy[:4]) + "."
                        )
                cached = " ".join(parts)[:1200]
                self._prompt_cache[profile.id] = cached
            return cached

    @staticmethod
    def _is_ephemeral_characteristic(value: str) -> bool:
        """Reject conversational state/turn fragments as durable user traits."""
        normalized = " ".join(str(value or "").casefold().split())
        return bool(re.match(
            r"^(?:back\b|de retour|ravi(?:e)?\b|not convinced\b|not sure\b|"
            r"pr[eê]t(?:e)?\b|curieux(?:euse)?\s+(?:de\s+|d['’])(?:savoir|comprendre|voir)\b|"
            r"curious\s+(?:to\s+(?:know|understand|see)|about\s+(?:how|why|what))\b)",
            normalized,
        ))

    def _quarantine_ephemeral_characteristics(self, profile: UserProfile) -> int:
        kept = []
        moved = 0
        for value in profile.characteristics:
            if self._is_ephemeral_characteristic(value):
                if not any(
                    item.get("value", "").casefold() == str(value).casefold()
                    for item in profile.profile_provenance_quarantine
                    if isinstance(item, dict)
                ):
                    profile.profile_provenance_quarantine.append({
                        "value": value,
                        "reason": "conversation_state_or_question_fragment_not_durable_trait",
                        "quarantined_at": datetime.now().isoformat(),
                    })
                moved += 1
            else:
                kept.append(value)
        if moved:
            profile.characteristics = kept
            self._prompt_cache.pop(profile.id, None)
        return moved

    @staticmethod
    def _is_direct_user_assertion(text: str, start: int, end: int) -> bool:
        """Reject profile-shaped phrases that are quoted, reported, or hypothetical.

        The fact patterns below are intentionally lexical and only useful for
        direct first-person assertions. Without this context check, a sentence
        such as `Lumina said "I prefer X"` or `If I prefer X, would that help?`
        is incorrectly persisted as a durable user preference.
        """
        value = str(text or "")
        start = max(0, min(len(value), int(start)))
        end = max(start, min(len(value), int(end)))

        for pattern in (
            r'"[^"\r\n]*"',
            r"“[^”\r\n]*”",
            r"‘[^’\r\n]*’",
            r"«[^»\r\n]*»",
            r"(?<!\w)'[^'\r\n]+'(?!\w)",
        ):
            if any(match.start() <= start and end <= match.end()
                   for match in re.finditer(pattern, value)):
                return False

        left = max(value.rfind(mark, 0, start) for mark in (".", "!", "?", ";", "\n"))
        right_candidates = [value.find(mark, end) for mark in (".", "!", "?", ";", "\n")]
        right_candidates = [position for position in right_candidates if position >= 0]
        right = min(right_candidates) if right_candidates else len(value)
        clause = value[left + 1:right].strip()
        relative_start = max(0, start - left - 1)
        prefix = clause[:relative_start].strip()

        # A question or a conditional/hedged premise does not assert a settled
        # personal fact, even when it contains a first-person verb pattern.
        if "?" in clause or "？" in clause:
            return False
        if re.match(
            r"^(?:(?:what\s+)?if|unless|assuming|provided\s+that|whether|"
            r"si|dans\s+le\s+cas\s+où|à\s+condition\s+que|"
            r"maybe|perhaps|possibly|peut[- ]être|peut etre|je\s+pense\s+que|"
            r"je\s+crois\s+que|i\s+think\s+that|i\s+think|i\s+believe\s+that)\b",
            prefix,
            flags=re.IGNORECASE,
        ):
            return False

        # Do not turn someone else's claim about the user into the user's own
        # assertion. Handle English and French reported-speech frames.
        if re.search(
            r"\b(?:you|lumina|he|she|they|someone|the\s+assistant|"
            r"tu|il|elle|on|quelqu['’]un|l['’]assistant)\s+"
            r"(?:(?:have|has)\s+)?(?:said|say|claimed|claim|stated|mentioned|"
            r"wrote|replied|told\s+me|as\s+dit|a\s+dit|dit|as\s+répondu|"
            r"a\s+répondu|répondu|prétend|prétendu|affirmé|affirme|"
            r"penses|pense|crois|croit)"
            r"(?:\s+(?:that|que))?\s*$",
            prefix,
            flags=re.IGNORECASE,
        ):
            return False
        return True

    def learn_from_message(
        self,
        user_id: str,
        message: str,
        *,
        return_receipt: bool = False,
        source_turn_id: str = "",
    ):
        """Persist only explicit preference, interest, and trait statements."""
        profile = self.get(user_id)
        if not profile or profile.id == self.GUEST_ID:
            receipt = {"status": "skipped_no_named_profile", "changed": False}
            return receipt if return_receipt else False
        if not message:
            receipt = {"status": "skipped_empty_message", "changed": False}
            return receipt if return_receipt else False
        with self._lock:
            migrated = self._quarantine_ephemeral_characteristics(profile)
            if migrated:
                self._save()
        text = " ".join(str(message).strip().split())
        try:
            from managers.settings_manager import get_persona_name
            from cognition.identity_boundary import claims_persona_identity
            persona_name = get_persona_name()
            claims_persona_name = claims_persona_identity(text, persona_name)
            # Keep the safety boundary intact even when a plugin or test
            # replaces identity_boundary with an older implementation.
            if not claims_persona_name and persona_name:
                escaped = re.escape(" ".join(str(persona_name).split()))
                claims_persona_name = bool(re.search(
                    rf"\b(?:i am|i'm|je suis|moi c['’]est|mon nom est|je m['’]appelle)\s+"
                    rf"(?:the\s+|la\s+|le\s+|l['’])?{escaped}\b",
                    text,
                    flags=re.IGNORECASE,
                ))
        except Exception:
            claims_persona_name = False
        learned: List[tuple[str, str]] = []
        patterns = (
            # Keep polarity explicit. A negative statement cannot be stored
            # under the positive preference label without reversing its meaning.
            ("dislike", r"(?:i do not like|i don't like|i dislike|je n'aime pas|je n’aime pas)\s+([^.!?]{3,100})"),
            ("preference", r"(?:i prefer|i like|i love|je préfère|j'aime|j’aime)\s+([^.!?]{3,100})"),
            ("interest", r"(?:i am interested in|i'm interested in|i enjoy|je m'intéresse à|je m'interesse a)\s+([^.!?]{3,100})"),
            # A bare copula predicate ("I am curious", "je suis fatigué")
            # is ambiguous between a durable trait and the current turn's
            # state. Only learn a characteristic automatically from explicit
            # identity-style noun phrases or explicit self-characterization.
            ("characteristic", r"(?:i am|i'm)\s+(?:a|an)\s+([^.!?]{3,70})"),
            ("characteristic", r"je suis\s+(?:un|une)\s+([^.!?]{3,70})"),
            ("characteristic", r"(?:i consider myself|je me considère comme|je me considere comme)\s+([^.!?]{3,70})"),
        )
        for kind, pattern in patterns:
            if kind == "characteristic" and claims_persona_name:
                continue
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                value = match.group(1).strip(" ,;:")
                if not self._is_direct_user_assertion(
                    text, match.start(), match.end(),
                ):
                    continue
                if kind == "characteristic" and re.search(
                    r"\b(?:curieux|curieuse|curious)\s+(?:"
                    r"(?:de\s+|d['’])(?:savoir|comprendre|connaitre|connaître|voir)|"
                    r"to\s+(?:know|understand|learn|find)|"
                    r"about\s+(?:how|why|what|whether|if))\b",
                    value,
                    flags=re.IGNORECASE,
                ):
                    # Conversational lead-ins such as "je suis curieux de comprendre"
                    # describe the current question, not a durable user trait.
                    continue
                if (
                    value and len(value.split()) <= 16
                    and not (kind == "characteristic" and self._is_ephemeral_characteristic(value))
                ):
                    learned.append((kind, value))
        if not learned:
            receipt = {
                "status": "quarantined_ephemeral_profile_data" if migrated else "no_explicit_profile_fact",
                "changed": False,
                "quarantined_count": migrated,
            }
            return receipt if return_receipt else False
        changed = False
        changed_categories = set()
        provenance_records_added = 0
        source_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        recorded_at = datetime.now().isoformat()
        profile_fields = {
            "preference": "preferences",
            "dislike": "dislikes",
            "interest": "interests",
            "characteristic": "characteristics",
        }
        with self._lock:
            previous_values = {
                kind: list(getattr(profile, profile_fields[kind]))
                for kind, _value in learned[:3]
            }
            previous_last_seen = profile.last_seen
            previous_provenance = json.loads(json.dumps(profile.profile_fact_provenance))
            for kind, value in learned[:3]:
                target = getattr(profile, profile_fields[kind])
                fact_key = hashlib.sha256(value.casefold().encode("utf-8")).hexdigest()
                category_provenance = profile.profile_fact_provenance.setdefault(kind, {})
                sources = category_provenance.setdefault(fact_key, [])
                already_recorded = any(
                    isinstance(item, dict)
                    and (
                        item.get("turn_id") == source_turn_id
                        if source_turn_id
                        else item.get("source_sha256") == source_sha256
                    )
                    for item in sources
                )
                if not already_recorded:
                    sources.append({
                        "turn_id": str(source_turn_id or ""),
                        "source_sha256": source_sha256,
                        "recorded_at": recorded_at,
                        "source_role": "user",
                    })
                    del sources[:-5]
                    changed = True
                    changed_categories.add(kind)
                    provenance_records_added += 1
                if value.casefold() not in {item.casefold() for item in target}:
                    target.append(value)
                    del target[:-8]
                    changed = True
                    changed_categories.add(kind)
            if changed:
                self._prompt_cache.pop(profile.id, None)
                profile.touch()
                self._save()
                try:
                    persisted = json.loads(self._path.read_text(encoding="utf-8"))
                    persisted_profile = persisted.get("users", {}).get(profile.id)
                    persistence_verified = persisted_profile == profile.to_dict()
                except Exception:
                    persistence_verified = False
                if not persistence_verified:
                    for kind, values in previous_values.items():
                        setattr(profile, profile_fields[kind], values)
                    profile.profile_fact_provenance = previous_provenance
                    profile.last_seen = previous_last_seen
                    self._prompt_cache.pop(profile.id, None)
                    receipt = {
                        "status": "persistence_failed",
                        "changed": False,
                        "persisted": False,
                        "categories_updated": [],
                        "extracted_count": len(learned),
                        "quarantined_count": migrated,
                    }
                    return receipt if return_receipt else False
        if changed:
            logger.info("Learned explicit profile details for %s", profile.id)
        receipt = {
            "status": "updated" if changed else "duplicate_explicit_profile_fact",
            "changed": changed,
            "persisted": True,
            "categories_updated": sorted(changed_categories),
            "extracted_count": len(learned),
            "quarantined_count": migrated,
            "provenance_records": provenance_records_added,
        }
        return receipt if return_receipt else changed

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save(self):
        temporary_path = None
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "active_id": self._active_id,
                "users":     {uid: p.to_dict() for uid, p in self._users.items()},
            }
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=str(self._path.parent),
                prefix=self._path.name + ".", suffix=".tmp", delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(json.dumps(data, indent=2, ensure_ascii=False))
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, self._path)
        except Exception as e:
            logger.error(f"UserManager save error: {e}")
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    logger.warning("Could not remove temporary user profile file")

    def _load(self):
        try:
            if not self._path.exists():
                return
            data = json.loads(self._path.read_text())
            migrated_profiles = False
            for uid, pd in data.get("users", {}).items():
                profile = UserProfile.from_dict(pd)
                if self._quarantine_ephemeral_characteristics(profile):
                    migrated_profiles = True
                self._users[uid] = profile
            saved_active = data.get("active_id", self.GUEST_ID)
            if saved_active in self._users:
                self._active_id = saved_active
            if migrated_profiles:
                self._save()
            logger.info(f"👥 Loaded {len(self._users)} users (active: {self._active_id})")
        except Exception as e:
            logger.error(f"UserManager load error: {e}")

    def _ensure_guest(self):
        if self.GUEST_ID not in self._users:
            self._users[self.GUEST_ID] = UserProfile(
                id=self.GUEST_ID,
                display_name="Guest",
                color="#64748b",
            )


# ── Singleton ─────────────────────────────────────────────────────────────────
user_manager = UserManager()
