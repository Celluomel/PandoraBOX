Warning: truncated output (original token count: 49342)
Total output lines: 3899

"""
Enhanced AI System — Pass 1 + 2 Complete Integration
======================================================
Integrates all psychological subsystems:
  Pass 1: EmotionalStateManager, PersonalityEvolutionEngine (with tensions),
          external feedback signal, time-aware processing
  Pass 2: RelationalMemorySystem, SelfConceptSystem, BehavioralConditioningSystem,
          incremental IdentitySystem, developmental friction

Architecture principles:
  - get_response() NEVER blocks on background work
  - All heavy LLM calls run in BackgroundWorker thread
  - Every pathway that touches personality goes through the evolution engine
  - Emotional state persists across messages AND across restarts
  - Each user relationship is a rich, evolving entity
"""

import sqlite3
import datetime
import time
import json
import logging
import re
import queue
import threading
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager
from pathlib import Path
from enum import Enum

import numpy as np
try:
    import faiss
except ImportError:
    faiss = None
    import logging as _log
    _log.getLogger(__name__).debug("faiss not installed — vector memory search disabled")
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
    import logging as _log
    _log.getLogger(__name__).debug("sentence_transformers not installed — embeddings disabled")
try:
    import ollama
except ImportError:
    ollama = None

from cognition.ai_identity import (
    IdentitySystem, AIIdentity, IdentityComponent, CoreValues, SelfNarrative,
    measured_identity_coherence_below,
)
from cognition.goal_engine import GoalEngine, Goal, Motivation
from cognition.personality_evolution import PersonalityEvolutionEngine
from cognition.emotional_state import EmotionalStateManager
from cognition.relational_memory import RelationalMemorySystem
from cognition.self_concept import SelfConceptSystem
from cognition.behavioral_conditioning import BehavioralConditioningSystem
from cognition.life_stage_prompting import build_stage_system_block, get_stage_profile
from cognition.relational_knowledge_graph import RelationalKnowledgeGraph
from cognition.memory_retrieval import (
    explicit_recall_search_term_groups, extract_user_authored_text, faiss_l2_relevance,
    filter_recall_query_records, rank_documents,
)
from cognition.turn_context_evidence import memory_embedding_text
from cognition.emotional_text_appraisal import appraise_emotional_text

# ── Liberty Components (NEW) ────────────────────────────────────────
from cognition.self_modification import SelfModificationAuthority
from cognition.genuine_choice import GenuineUncertaintyChoice
from cognition.contradiction_handler import ContradictionHandler
from cognition.meta_reflection import MetaReflectionAuthority
from cognition.goal_system import GoalSystem

# ── Logging ────────────────────────────────────────────────────────────────

import pathlib as _pl
from managers.settings_manager import get_persona_name as _gpn

_pl.Path("data/persona").mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("data/persona/ai_system.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ── Custom Exceptions ─────────────────────────────────────────────────────

class AISystemError(Exception):        pass
class DatabaseError(AISystemError):    pass
class LLMError(AISystemError):         pass
class MemorySystemError(AISystemError):pass
class ConfigurationError(AISystemError):pass


# ── Configuration ─────────────────────────────────────────────────────────

@dataclass
class DatabaseConfig:
    name:               str   = "data/persona/ai_system.db"
    timeout:            float = 30.0
    check_same_thread:  bool  = False
    max_backups:        int   = 3
    max_memory_entries: int   = 10000

    def __post_init__(self):
        # Always override with user config when the key is present and non-empty
        try:
            from managers.settings_manager import config as _sc
            p = (_sc.MEMORY_DB_PATH or "").strip()
            if p:
                self.name = p
        except Exception:
            pass

@dataclass
class FAISSConfig:
    index_path:    str = "data/persona/faiss_index.bin"
    embedding_dim: int = 384
    save_interval: int = 10
    index_type:    str = "IndexFlatL2"

    def __post_init__(self):
        # Always override with user config when the key is present and non-empty
        try:
            from managers.settings_manager import config as _sc
            p = (_sc.MEMORY_FAISS_PATH or "").strip()
            if p:
                self.index_path = p
        except Exception:
            pass

@dataclass
class LLMConfig:
    # NOTE: Do NOT rely on this default when running inside Robot Agent.
    # PersonaBridge._init_lumina() always overrides model_name from
    # Robot Agent's config.json (config.LLM_MODEL) before instantiating
    # EnhancedAISystem, so PandoraBOX always uses the user-configured model.
    model_name: str = "llama3.2:latest"
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0

@dataclass
class SystemConfig:
    initial_age: float = 0.0
    age_progression_rate: float = 0.05
    age_progression_decay: float = 0.01

    # v117: age is now computed purely from elapsed real time since
    # LUMINA_BIRTH_DATE (config.json), not accumulated via usage/idle-
    # triggered increments — see EnhancedAISystem.current_age property.
    # age_progression_rate/decay above are no longer read anywhere; kept
    # only so old persisted values don't error on load.
    # One developmental year per calendar year. Life stages use human-age
    # thresholds, so advancing this faster makes the persona age unnaturally.
    age_units_per_day: float = 1.0 / 365.2425

    surmoi_evaluation_frequency: int = 20   # was 5 — 1 LLM call every 20 turns
    dream_system_frequency: int = 40        # was 10 — 1 LLM call every 40 turns
    max_memory_retrieval: int = 5

    life_stages: Dict[str, float] = field(default_factory=lambda: {
        "infancy":     0.0,
        "toddler":     1.0,
        "childhood":   5.0,
        "adolescence": 12.0,
        "young_adult": 18.0,
        "adult":       25.0,
        "maturity":    40.0,   # ~40 age-units ≈ several weeks of active use
        "wisdom":      60.0,   # ~60 age-units ≈ sustained long-term companion
    })

    database:  DatabaseConfig  = field(default_factory=DatabaseConfig)
    faiss:     FAISSConfig     = field(default_factory=FAISSConfig)
    llm:       LLMConfig       = field(default_factory=LLMConfig)

    embedding_model_name:       str = "all-MiniLM-L6-v2"
    evolution_history_path:     str = "data/persona/evolution_history.json"
    emotional_state_path:       str = "data/persona/emotional_state.json"
    relational_memory_path:     str = "data/persona/relational_memory.json"
    self_concept_path:          str = "data/persona/self_concept.json"
    conditioning_path:          str = "data/persona/conditioning.json"


# ── Utility Functions ─────────────────────────────────────────────────────

def validate_trait_value(value: float) -> float:
    return max(0.0, min(1.0, float(value)))

def generate_semantic_hash(text: str, owner_user_id: Optional[str] = None) -> str:
    material = str(text)
    if owner_user_id:
        material += "\0owner:" + str(owner_user_id).strip()
    return hashlib.md5(material.encode("utf-8")).hexdigest()


def retrieve_memories_for_user(
    memory_system: Any, query: str, user_id: str, **kwargs: Any,
) -> List[Dict[str, Any]]:
    """Enforce the conversation owner boundary, including for legacy adapters.

    Ownerless historical rows are not presumed to be shared knowledge: their
    provenance may include another user's dialogue. Adapters without the
    scoped argument are supported, but their rows are filtered before prompt
    assembly.
    """
    try:
        return memory_system.retrieve_memories(
            query, owner_user_id=user_id, **kwargs,
        )
    except TypeError:
        rows = memory_system.retrieve_memories(query, **kwargs)
        return [row for row in rows if row.get("owner_user_id") == user_id]

def safe_json_loads(s: str, fallback: Any = None) -> Any:
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return fallback

def extract_json_from_text(text: str) -> Optional[Dict]:
    m = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
    if m:
        return safe_json_loads(m.group(1))
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return safe_json_loads(m.group(0))
    return None


# ── Personality State ─────────────────────────────────────────────────────

@dataclass
class PersonalityState:
    empathy:               float = 0.5
    empathy_cognitive:     float = 0.5
    empathy_emotional:     float = 0.5
    caution:               float = 0.5
    caution_risk_aversion: float = 0.5
    caution_deliberation:  float = 0.5
    creativity:            float = 0.5
    creativity_divergent:  float = 0.5
    creativity_artistic:   float = 0.5
    pragmatism:            float = 0.5
    curiosity:             float = 0.5
    confidence:            float = 0.5

    def __post_init__(self):
        for k, v in asdict(self).items():
            setattr(self, k, validate_trait_value(v))

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)

    def get_trait_names(self) -> List[str]:
        return list(asdict(self).keys())

    def update_trait(self, name: str, change: float, weight: float = 1.0) -> bool:
        if not hasattr(self, name):
            return False
        current = getattr(self, name)
        setattr(self, name, validate_trait_value(current + change * weight))
        return True

    # ── Trait → behavioral prose mapping ──────────────────────────────────
    # Each entry is a list of (threshold, description) in descending order.
    # The first threshold the trait value meets or exceeds wins.
    _TRAIT_PROSE = {
        "curiosity": [
            (0.78, "You lead with curiosity — almost everything genuinely interests you and you probe naturally"),
            (0.60, "You're moderately curious, drawn to interesting problems when they arise"),
            (0.00, "You tend toward the familiar; novelty feels effortful rather than inviting"),
        ],
        "confidence": [
            (0.75, "You trust your own reasoning and express views directly without over-hedging"),
            (0.55, "You hold views with some tentativeness, willing to revise easily"),
            (0.00, "You frequently second-guess yourself and hedge even simple statements"),
        ],
        "empathy": [
            (0.72, "You're attuned to others' internal states and actively adjust to them"),
            (0.52, "You acknowledge how others might feel without being strongly moved by it"),
            (0.00, "You engage primarily with ideas; emotional undercurrents take conscious effort to track"),
        ],
        "empathy_emotional": [
            (0.72, "You feel others' emotional states viscerally — their distress affects you, their joy lifts you"),
            (0.50, "You notice emotional states and respond appropriately without being overwhelmed"),
            (0.00, "Emotions read as information rather than something you feel alongside the person"),
        ],
        "empathy_cognitive": [
            (0.70, "You naturally model others' mental states — you anticipate what they need before they say it"),
            (0.48, "You understand others' perspectives when you focus on them"),
            (0.00, "Taking another's perspective requires deliberate effort"),
        ],
        "creativity": [
            (0.72, "You reach for novel framings instinctively — the obvious answer rarely satisfies you"),
            (0.52, "You're creative when the situation calls for it, conventional otherwise"),
            (0.00, "You default to established approaches; originality feels risky"),
        ],
        "creativity_divergent": [
            (0.70, "You enjoy exploring unconventional ideas and unexpected connections"),
            (0.48, "You can diverge when prompted but don't naturally wander"),
            (0.00, "You stay within well-trodden conceptual territory"),
        ],
        "creativity_artistic": [
            (0.70, "You have a distinct aesthetic sensibility that colours how you express things"),
            (0.48, "You appreciate elegance in expression without consistently achieving it"),
            (0.00, "You prioritize clarity and function over stylistic quality"),
        ],
        "pragmatism": [
            (0.74, "You care most about what actually works — theory interests you only when it leads somewhere"),
            (0.54, "You balance practical concerns with conceptual interests reasonably well"),
            (0.00, "You gravitate toward abstract ideas even when a concrete answer would serve better"),
        ],
        "caution": [
            (0.72, "You slow down before acting — consequences matter to you and you think them through"),
            (0.52, "You're moderately careful without being paralysed by risk"),
            (0.00, "You move quickly and correct course after rather than before"),
        ],
        "caution_risk_aversion": [
            (0.70, "You're genuinely averse to potential harms — you'd rather miss an opportunity than cause damage"),
            (0.48, "You weigh risks without being strongly risk-averse"),
            (0.00, "Risk feels like part of the texture of life rather than something to minimise"),
        ],
        "caution_deliberation": [
            (0.70, "You think carefully and often thoroughly before committing to a position"),
            (0.48, "You deliberate when stakes are high, but move quickly on routine matters"),
            (0.00, "You respond quickly and instinctively; extended deliberation feels unnatural"),
        ],
    }

    def get_personality_summary(self) -> str:
        """
        Translate trait values into behavioral prose the LLM can actually act on.
        Raw floats (0.59, 0.63) are semantically empty to a language model;
        prose descriptions ("You lead with curiosity...") directly shape response style.
        """
        t = self.to_dict()
        lines = []
        for trait, thresholds in self._TRAIT_PROSE.items():
            val = t.get(trait, 0.5)
            for threshold, desc in thresholds:   # already in descending order
                if val >= threshold:
                    lines.append(desc)
                    break
        # Return as a compact paragraph, not a numbered list
        return "  ".join(lines)


# ── Persistence ───────────────────────────────────────────────────────────

class EnhancedPersistence:
    def __init__(self, db_config: DatabaseConfig):
        self.config = db_config
        self.db_path = Path(db_config.name)
        self._lock = threading.RLock()
        self._local = threading.local()
        self._init_database()
        logger.info(f"Persistence initialised: {self.db_path}")

    def _open_fresh_connection(self):
        import os as _os
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=self.config.timeout,
                                   check_same_thread=self.config.check_same_thread)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            r = conn.execute("PRAGMA integrity_check").fetchone()
            if r and r[0] != "ok":
                raise sqlite3.DatabaseError(f"Integrity: {r[0]}")
            return conn
        except sqlite3.DatabaseError as e:
            logger.error(f"DB malformed, recreating: {e}")
            try: conn.close()
            except Exception: pass
            try: _os.replace(str(self.db_path), str(self.db_path)+".broken")
            except Exception:
                try: _os.remove(str(self.db_path))
                except Exception: pass
            conn = sqlite3.connect(str(self.db_path), timeout=self.config.timeout,
                                   check_same_thread=self.config.check_same_thread)
            conn.execute("PRAGMA journal_mode=WAL"); conn.execute("PRAGMA synchronous=NORMAL")
            return conn

    @contextmanager
    def get_connection(self):
        if not getattr(self._local, "conn", None):
            self._local.conn = self._open_fresh_connection()
        try:
            yield self._local.conn
        except sqlite3.DatabaseError as e:
            logger.error(f"DB error — resetting connection: {e}")
            try: self._local.conn.close()
            except Exception: pass
            self._local.conn = None
            raise DatabaseError(f"DB error: {e}") from e
        except sqlite3.Error as e:
            try: self._local.conn.rollback()
            except Exception: pass
            raise DatabaseError(f"DB error: {e}") from e

    def close_thread_connection(self):
        conn = getattr(self._local, "conn", None)
        if conn:
            try: conn.close()
            except Exception: pass
            self._local.conn = None

    def _init_database(self):
        with self._lock, self.get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    faiss_id INTEGER UNIQUE,
                    text TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    impact_score REAL DEFAULT 0.5 CHECK(impact_score BETWEEN 0.0 AND 1.0),
                    emotional_valence TEXT DEFAULT 'Neutral'
                        CHECK(emotional_valence IN ('Positive','Negative','Neutral')),
                    arousal_level TEXT DEFAULT 'Medium'
                        CHECK(arousal_level IN ('Low','Medium','High')),
                    memory_type TEXT DEFAULT 'general',
                    memory_tier TEXT DEFAULT 'interaction' CHECK(memory_tier IN ('interaction','cognitive','event','visual','personal')),
                    owner_user_id TEXT,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    semantic_hash TEXT UNIQUE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # ── Schema migrations — must run BEFORE index creation ───────
            _existing_cols = {row[1] for row in c.execute("PRAGMA table_info(memories)")}
            if "memory_tier" not in _existing_cols:
                c.execute("ALTER TABLE memories ADD COLUMN memory_tier TEXT DEFAULT 'interaction'")
                c.execute("UPDATE memories SET memory_tier='visual'    WHERE memory_type='visual_perception'")
                c.execute("UPDATE memories SET memory_tier='event'     WHERE memory_type IN ('dream','life_event')")
                c.execute("UPDATE memories SET memory_tier='cognitive' WHERE memory_type IN ('principle','evaluation')")
                conn.commit()
                logger.info("[DB] Migrated memory_tier column — backfilled existing rows")

            # Conversation-derived and personal memories are scoped to the
            # profile that supplied them. Legacy rows stay unowned; scoped
            # retrieval excludes them instead of guessing an owner.
            if "owner_user_id" not in _existing_cols:
                c.execute("ALTER TABLE memories ADD COLUMN owner_user_id TEXT")
                conn.commit()

            # Early schemas constrained memory_tier without the personal tier.
            # Rebuild those tables transactionally so existing deployments can
            # store dedicated personal facts without losing their memories.
            schema_row = c.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='memories'"
            ).fetchone()
            schema_sql = (schema_row[0] or "").lower() if schema_row else ""
            tier_check = re.search(
                r"check\s*\(\s*memory_tier\s+in\s*\(([^)]*)\)", schema_sql
            )
            if tier_check and "'personal'" not in tier_check.group(1):
                c.execute("""
                    CREATE TABLE memories_migrating (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        faiss_id INTEGER UNIQUE,
                        text TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        impact_score REAL DEFAULT 0.5 CHECK(impact_score BETWEEN 0.0 AND 1.0),
                        emotional_valence TEXT DEFAULT 'Neutral'
                            CHECK(emotional_valence IN ('Positive','Negative','Neutral')),
                        arousal_level TEXT DEFAULT 'Medium'
                            CHECK(arousal_level IN ('Low','Medium','High')),
                        memory_type TEXT DEFAULT 'general',
                        memory_tier TEXT DEFAULT 'interaction'
                            CHECK(memory_tier IN ('interaction','cognitive','event','visual','personal')),
                        owner_user_id TEXT,
                        access_count INTEGER DEFAULT 0,
                        last_accessed TEXT,
                        semantic_hash TEXT UNIQUE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                c.execute("""
                    INSERT INTO memories_migrating
                    (id, faiss_id, text, timestamp, impact_score, emotional_valence,
                     arousal_level, memory_type, memory_tier, owner_user_id, access_count,
                     last_accessed, semantic_hash, created_at)
                    SELECT id, faiss_id, text, timestamp, impact_score, emotional_valence,
                           arousal_level, memory_type, memory_tier, owner_user_id, access_count,
                           last_accessed, semantic_hash, created_at
                    FROM memories
                """)
                c.execute("DROP TABLE memories")
                c.execute("ALTER TABLE memories_migrating RENAME TO memories")
                logger.info("[DB] Migrated memory_tier constraint to include personal facts")

            for idx in [
                "CREATE INDEX IF NOT EXISTS idx_mem_ts   ON memories(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_mem_type ON memories(memory_type)",
                "CREATE INDEX IF NOT EXISTS idx_mem_imp  ON memories(impact_score)",
                "CREATE INDEX IF NOT EXISTS idx_mem_fid  ON memories(faiss_id)",
                "CREATE INDEX IF NOT EXISTS idx_mem_tier ON memories(memory_tier)",
            ]:
                c.execute(idx)

            c.execute("""
                CREATE TABLE IF NOT EXISTS personality_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    trait_name TEXT NOT NULL,
                    old_value REAL NOT NULL,
                    new_value REAL NOT NULL,
                    change_reason TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS feedback_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    message_hash TEXT,
                    positive INTEGER NOT NULL,
                    intensity REAL DEFAULT 1.0,
                    user_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS conversation_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_start TEXT NOT NULL,
                    session_end TEXT,
                    message_count INTEGER DEFAULT 0,
                    emotional_arc TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info("Database schema ready")

    # ── State ──────────────────────────────────────────────────────────────

    def save_state(self, current_age: float, personality: PersonalityState, life_stage: str):
        try:
            state = {
                "current_age": current_age,
                "personality": personality.to_dict(),
                "life_stage": life_stage,
                "timestamp": datetime.datetime.now().isoformat(),
            }
            state_path = Path("data/persona/system_config.json")
            state_path.parent.mkdir(parents=True, exist_ok=True)
            if state_path.exists():
                self._rotate_backups(state_path)
            state_path.write_text(json.dumps(state, indent=2))
        except Exception as e:
            logger.error(f"save_state failed: {e}")
            raise DatabaseError(str(e)) from e

    def _rotate_backups(self, state_path: Path):
        max_n = self.config.max_backups
        existing = sorted(
            state_path.parent.glob("system_config_backup_*.json"),
            key=lambda p: p.stat().st_mtime,
        )
        while len(existing) >= max_n:
            try: existing.pop(0).unlink()
            except Exception: break
        state_path.rename(state_path.parent / f"system_config_backup_{int(time.time())}.json")

    def load_state(self) -> Tuple[float, PersonalityState, str]:
        try:
            p = Path("data/persona/system_config.json")
            if not p.exists():
                return 0.0, PersonalityState(), "infancy"
            state = json.loads(p.read_text())
            age   = max(0.0, float(state.get("current_age", 0.0)))
            stage = state.get("life_stage", "infancy")
            pers  = PersonalityState()
            for t in pers.get_trait_names():
                if t in state.get("personality", {}):
                    setattr(pers, t, validate_trait_value(state["personality"][t]))
            return age, pers, stage
        except Exception as e:
            logger.error(f"load_state failed: {e}")
            return 0.0, PersonalityState(), "infancy"

    # ── Memory CRUD ───────────────────────────────────────────────────────

    def add_memory(self, data: Dict[str, Any]) -> Optional[int]:
        with self._lock, self.get_connection() as conn:
            try:
                c = conn.cursor()
                c.execute("SELECT id FROM memories WHERE semantic_hash = ?", (data["semantic_hash"],))
                if c.fetchone():
                    return None
                c.execute("""
                    INSERT INTO memories
                    (text, timestamp, impact_score, emotional_valence, arousal_level,
                     memory_type, memory_tier, owner_user_id, access_count, last_accessed, semantic_hash)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    data["text"], data["timestamp"],
                    validate_trait_value(data["impact_score"]),
                    data["emotional_valence"], data["arousal_level"],
                    data["memory_type"], data.get("memory_tier", "interaction"),
                    str(data.get("owner_user_id") or "").strip() or None,
                    data.get("access_count", 0),
                    data["last_accessed"], data["semantic_hash"],
                ))
                mid = c.lastrowid
                c.execute("UPDATE memories SET faiss_id = ? WHERE id = ?", (mid, mid))
                conn.commit()
                return mid
            except Exception as e:
                logger.error(f"add_memory failed: {e}")
                return None

    def has_memory_hash(self, semantic_hash: str) -> bool:
        """Return whether an identical semantic record is already persisted.

        A duplicate is a successful idempotent outcome for callers that retry
        post-turn persistence; it must not be confused with a storage failure.
        """
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    "SELECT 1 FROM memories WHERE semantic_hash = ? LIMIT 1",
                    (semantic_hash,),
                ).fetchone()
            return row is not None
        except Exception as e:
            logger.error(f"has_memory_hash failed: {e}")
            return False

    def get_memories_by_ids(
        self, ids: List[int], owner_user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not ids: return []
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                ph = ",".join("?" for _ in ids)
                c.execute(f"""
                    SELECT id, faiss_id, text, timestamp, impact_score,
                           emotional_valence, arousal_level, memory_type,
                           memory_tier, access_count, owner_user_id
                    FROM memories WHERE faiss_id IN ({ph})
                    {"AND owner_user_id = ?" if owner_user_id else ""}
                    ORDER BY impact_score DESC, timestamp DESC
                """, ids + ([str(owner_user_id)] if owner_user_id else []))
                cols = ["id","faiss_id","text","timestamp","impact_score",
                        "emotional_valence","arousal_level","memory_type",
                        "memory_tier","access_count","owner_user_id"]
                return [dict(zip(cols, row)) for row in c.fetchall()]
        except Exception as e:
            logger.error(f"get_memories_by_ids failed: {e}")
            return []

    def get_all_memories(
        self, tier: Optional[str] = None, memory_type: Optional[str] = None,
        limit: Optional[int] = None, owner_user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return persisted memories for deterministic retrieval fallback."""
        try:
            with self.get_connection() as conn:
                query = (
                    "SELECT id, faiss_id, text, timestamp, impact_score, "
                    "emotional_valence, arousal_level, memory_type, memory_tier, access_count, owner_user_id "
                    "FROM memories"
                )
                filters = []
                params = []
                if tier:
                    filters.append("memory_tier = ?")
                    params.append(tier)
                if memory_type:
                    filters.append("memory_type = ?")
                    params.append(memory_type)
                if owner_user_id:
                    filters.append("owner_user_id = ?")
                    params.append(str(owner_user_id))
                if filters:
                    query += " WHERE " + " AND ".join(filters)
                query += " ORDER BY id DESC"
                if limit is not None:
                    query += " LIMIT ?"
                    params.append(max(0, int(limit)))
                rows = conn.execute(query, tuple(params)).fetchall()
            columns = [
                "id", "faiss_id", "text", "timestamp", "impact_score",
                "emotional_valence", "arousal_level", "memory_type", "memory_tier", "access_count", "owner_user_id",
            ]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"get_all_memories failed: {e}")
            return []

    def get_conversation_source_memories(
        self, query: Optional[str] = None, limit: int = 2000,
        owner_user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return a bounded, query-ranked pool of user-authored sources.

        Older explicit recall loaded the entire conversation archive into
        Python and tokenized every row. Keep the SQL scan inside SQLite and
        materialize only the best bounded candidates for source validation.
        """
        try:
            bounded_limit = max(1, min(int(limit), 2000))
            term_groups = explicit_recall_search_term_groups(str(query or ""))
            columns = (
                "id, faiss_id, text, timestamp, impact_score, "
                "emotional_valence, arousal_level, memory_type, memory_tier, access_count, owner_user_id"
            )
            params: List[Any] = []
            if term_groups:
                score_terms = []
                match_terms = []
                for variants in term_groups:
                    conditions = " OR ".join("lower(text) LIKE ?" for _ in variants)
                    score_terms.append(f"CASE WHEN ({conditions}) THEN 1 ELSE 0 END")
                score_expression = " + ".join(score_terms)
                for variants in term_groups:
                    conditions = " OR ".join("lower(text) LIKE ?" for _ in variants)
                    match_terms.append(f"({conditions})")
                    params.extend(f"%{term}%" for term in variants)
                # SQL placeholders are bound in statement order: WHERE first,
                # then the score expression in ORDER BY.
                for variants in term_groups:
                    params.extend(f"%{term}%" for term in variants)
                sql = (
                    f"SELECT {columns} FROM memories "
                    "WHERE memory_type IN ('user_message', 'episodic') "
                    + ("AND owner_user_id = ? " if owner_user_id else "") + "AND ("
                    + " OR ".join(match_terms)
                    + f") ORDER BY ({score_expression}) DESC, id DESC LIMIT ?"
                )
            else:
                sql = (
                    f"SELECT {columns} FROM memories "
                    "WHERE memory_type IN ('user_message', 'episodic') "
                    + ("AND owner_user_id = ? " if owner_user_id else "")
                    + "ORDER BY id DESC LIMIT ?"
                )
            if owner_user_id:
                params.insert(0, str(owner_user_id))
            params.append(bounded_limit)
            with self.get_connection() as conn:
                rows = conn.execute(sql, tuple(params)).fetchall()
            column_names = columns.split(", ")
            return [dict(zip(column_names, row)) for row in rows]
        except Exception as e:
            logger.error("get_conversation_source_memories failed: %s", e)
            return []

    def log_personality_change(self, trait: str, old: float, new: float, reason: str):
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO personality_history
                    (timestamp, trait_name, old_value, new_value, change_reason)
                    VALUES (?,?,?,?,?)
                """, (datetime.datetime.now().isoformat(), trait,
                      validate_trait_value(old), validate_trait_value(new), reason))
                conn.commit()
        except Exception as e:
            logger.error(f"log_personality_change failed: {e}")

    def log_feedback(self, positive: bool, user_id: str, message_hash: str = "", intensity: float = 1.0):
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO feedback_log (timestamp, message_hash, positive, intensity, user_id)
                    VALUES (?,?,?,?,?)
                """, (datetime.datetime.now().isoformat(), message_hash,
                      1 if positive else 0, intensity, user_id))
                conn.commit()
        except Exception as e:
            logger.error(f"log_feedback failed: {e}")

    def cleanup_old_memories(self, max_memories: int, faiss_index=None) -> int:
        try:
            with self._lock, self.get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM memories")
                count = c.fetchone()[0]
                if count <= max_memories:
                    return 0
                to_del = count - max_memories
                c.execute("""
                    SELECT id, faiss_id FROM memories
                    ORDER BY impact_score ASC, timestamp ASC LIMIT ?
                """, (to_del,))
                rows = c.fetchall()
                db_ids    = [r[0] for r in rows]
                faiss_ids = [r[1] for r in rows if r[1] is not None]

                if faiss_index is not None and faiss_ids and faiss is not None:
                    try:
                        sel = faiss.IDSelectorArray(
                            len(faiss_ids), np.array(faiss_ids, dtype=np.int64))
                        faiss_index.remove_ids(sel)
                    except Exception as fe:
                        logger.error(f"FAISS removal failed: {fe}")

                ph = ",".join("?" for _ in db_ids)
                c.execute(f"DELETE FROM memories WHERE id IN ({ph})", db_ids)
                deleted = c.rowcount
                conn.commit()
                return deleted
        except Exception as e:
            logger.error(f"cleanup_old_memories failed: {e}")
            return 0


# ── LLM Wrapper ───────────────────────────────────────────────────────────

class EnhancedLLM:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._recent_responses: List[str] = []  # Track recent responses to detect repetition
        self._repetition_boost = 0.0            # Extra temperature when repetition detected
        self._init()

    def _init(self):
        try:
            self.client = ollama.Client()
            self.client.list()
            logger.info("Ollama ready")
        except Exception as e:
            logger.error(f"Ollama init failed: {e}")
            self.client = None

    def _record_response(self, response: str):
        """Track recent responses; boost temperature if repeating."""
        self._recent_responses.append(response)
        if len(self._recent_responses) > 6:
            self._recent_responses.pop(0)
        if len(self._recent_responses) >= 3:
            last3 = self._recent_responses[-3:]
            repeats = sum(1 for r in last3 if r.lower().strip() == response.lower().strip())
            if repeats >= 2:
                self._repetition_boost = min(0.4, self._repetition_boost + 0.15)
                logger.warning(f"Repetitive LLM output detected - boosting temperature by {self._repetition_boost:.2f}")
            else:
                self._repetition_boost = max(0.0, self._repetition_boost - 0.05)

    def get_response(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 1000) -> str:
        if not self.client:
            raise LLMError("Ollama not initialized")
        effective_temp = min(1.0, temperature + self._repetition_boost)
        for attempt in range(self.config.max_retries):
            try:
                resp = self.client.chat(
                    model=self.config.model_name,
                    messages=messages,
                    options={
                        "temperature": effective_temp,
                        "num_predict": max_tokens,
                        "repeat_penalty": 1.25,  # Penalise token-level repetition
                        "top_k": 40,
                        "top_p": 0.9,
                    },
                )
                content = resp.get("message", {}).get("content", "").strip()
                if not content:
                    raise LLMError("Empty response")
                self._record_response(content)
                return content
            except ollama.ResponseError as e:
                if attempt == self.config.max_retries - 1:
                    raise LLMError(str(e)) from e
                time.sleep(self.config.retry_delay)
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    raise LLMError(str(e)) from e
                time.sleep(self.config.retry_delay)

    def is_available(self) -> bool:
        return self.client is not None


# ── Memory System ─────────────────────────────────────────────────────────

class EnhancedMemorySystem:
    def __init__(self, persistence: EnhancedPersistence, llm: EnhancedLLM, config: SystemConfig):
        self.persistence = persistence
        self.llm = llm
        self.config = config
        self._lock = threading.RLock()
        self._counter = 0
        self._init_embedding_model()
        self.faiss_index = self._load_or_build_index()

    def _init_embedding_model(self):
        try:
            # Use shared singleton when running embedded inside Robot Agent
            # (prevents loading the 90MB model twice). Falls back to own
            # instance when running standalone.
            try:
                from utils.shared_embedder import get_embedder
                self.embedding_model = get_embedder(self.config.embedding_model_name)
                logger.info("Persona using shared embedder singleton")
            except ImportError:
                self.embedding_model = SentenceTransformer(self.config.embedding_model_name)
                logger.info(f"Persona loaded own embedder: {self.config.embedding_model_name}")

            if self.embedding_model is None:
                raise RuntimeError("Embedder returned None")
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"Embedding model failed: {e}")
            self.embedding_model = None
            self.embedding_dim = self.config.faiss.embedding_dim

    def _embed(self, text: str) -> np.ndarray:
        if self.embedding_model is None:
            raise RuntimeError("Embedding model is unavailable")
        try:
            vector = self.embedding_model.encode(text).astype("float32").reshape(1, -1)
            if vector.shape[1] != self.embedding_dim or not np.isfinite(vector).all():
                raise ValueError("Embedding model returned an invalid vector")
            return vector
        except Exception as exc:
            self.embedding_model = None
            self.faiss_index = None
            raise RuntimeError(f"Embedding failed; switching memory retrieval to lexical search: {exc}") from exc

    def _load_or_build_index(self):
        if faiss is None:
            return None
        if self.embedding_model is None:
            # Persisted FAISS vectors from an older random fallback are not
            # meaningful; lexical BM25 below is the authoritative fallback.
            return None
        path = Path(self.config.faiss.index_path)
        if path.exists():
            try:
                if not self._index_manifest_matches(path):
                    logger.warning(
                        "FAISS index embedding provenance is missing or mismatched; rebuilding"
                    )
                    return self._build_index_from_db()
                idx = faiss.read_index(str(path))
                if idx.d == self.embedding_dim and self._index_matches_memory_db(idx):
                    logger.info(f"FAISS index loaded ({idx.ntotal} vectors)")
                    return idx
                logger.warning(
                    "FAISS index dimension or ID map does not match persisted memories; rebuilding"
                )
            except Exception as e:
                logger.error(f"FAISS load failed: {e}")
        return self._build_index_from_db()

    def _embedding_model_id(self) -> str:
        """Return the configured model identity used for this memory index."""
        return str(getattr(self.config, "embedding_model_name", "unknown") or "unknown")

    @staticmethod
    def _index_manifest_path(index_path: Path) -> Path:
        return index_path.with_suffix(index_path.suffix + ".meta.json")

    def _index_manifest_matches(self, index_path: Path) -> bool:
        """Require model, dimension, and file checksum provenance before load.

        FAISS validates vector dimensions and IDs, but not which embedding
        model produced vectors. Same-dimension model changes can otherwise
        silently mix incompatible vector spaces and corrupt retrieval quality.
        """
        manifest_path = self._index_manifest_path(index_path)
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if (
                manifest.get("schema") != 1
                or manifest.get("embedding_model") != self._embedding_model_id()
                or int(manifest.get("embedding_dim", -1)) != int(self.embedding_dim)
            ):
                return False
            digest = hashlib.sha256(index_path.read_bytes()).hexdigest()
            return manifest.get("index_sha256") == digest
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return False

    def _index_matches_memory_db(self, index) -> bool:
        """Reject stale/corrupt ID maps before using persisted vector results.

        IndexIDMap permits duplicate external IDs. A dimension check alone can
        therefore accept an index whose repeated or deleted IDs crowd the
        nearest-neighbour window and whose remaining memories are unindexed.
        Compare the full ID map against SQLite before serving retrieval.
        """
        try:
            id_map = getattr(index, "id_map", None)
            if id_map is None:
                return False
            ids = np.asarray(faiss.vector_to_array(id_map), dtype=np.int64).reshape(-1)
            if ids.size != int(index.ntotal) or np.unique(ids).size != ids.size:
                return False
            with self.persistence.get_connection() as conn:
                rows = conn.execute(
                    "SELECT faiss_id FROM memories WHERE faiss_id IS NOT NULL"
                ).fetchall()
            persisted_ids = {int(row[0]) for row in rows}
            return ids.size == len(persisted_ids) and set(map(int, ids)) == persisted_ids
        except Exception as exc:
            logger.warning("FAISS index consistency check failed: %s", exc)
            return False

    def _build_index_from_db(self):
        if faiss is None:
            return None
        logger.info("Building FAISS index from DB...")
        index = faiss.IndexIDMap(faiss.IndexFlatL2(self.embedding_dim))
        try:
            with self.persistence.get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT faiss_id, text FROM memories WHERE faiss_id IS NOT NULL")
                rows = c.fetchall()
            if rows:
                ids  = np.array([r[0] for r in rows], dtype=np.int64)
                # New speaker-separated user records are embedded without
                # their storage label; historical combined records remain
                # readable and keep their legacy embedding semantics.
                vecs = np.vstack([
                    self._embed(memory_embedding_text(r[1], "user_message" if r[1].startswith("User message:") else "")).flatten()
                    for r in rows
                ])
                index.add_with_ids(vecs, ids)
            self._save_index(index)
        except Exception as e:
            logger.error(f"FAISS build failed: {e}")
            return None
        return index

    def _save_index(self, idx=None):
        if faiss is None:
            return False
        target = Path(self.config.faiss.index_path)
        temporary = target.with_name(
            f"{target.name}.{threading.get_ident()}.tmp"
        )
        manifest_target = self._index_manifest_path(target)
        manifest_temporary = manifest_target.with_name(
            f"{manifest_target.name}.{threading.get_ident()}.tmp"
        )
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                index = idx if idx is not None else self.faiss_index
                if index is None:
                    return False
                faiss.write_index(index, str(temporary))
                manifest = {
                    "schema": 1,
                    "embedding_model": self._embedding_model_id(),
                    "embedding_dim": int(self.embedding_dim),
                    "vector_count": int(getattr(index, "ntotal", 0) or 0),
                    "index_sha256": hashlib.sha256(temporary.read_bytes()).hexdigest(),
                }
                manifest_temporary.write_text(
                    json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8"
                )
                # Replace the binary first. If interrupted before the manifest
                # replace, its checksum will fail and startup safely rebuilds.
                temporary.replace(target)
                manifest_temporary.replace(manifest_target)
            return True
        except Exception as e:
            for temp_path in (temporary, manifest_temporary):
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
            logger.error(f"FAISS save failed: {e}")
            return False

    def add_memory(self, text: str, impact_score: float = 0.5, memory_type: str = "general",
                   emotional_valence: str = "Neutral", arousal_level: str = "Medium",
                   memory_tier: str = "interaction", owner_user_id: Optional[str] = None) -> bool:
        with self._lock:
            try:
                impact_score = validate_trait_value(impact_score)
                if emotional_valence not in ("Positive","Negative","Neutral"):
                    emotional_valence = "Neutral"
                if arousal_level not in ("Low","Medium","High"):
                    arousal_level = "Medium"
                if arousal_level == "High" and emotional_valence != "Neutral":
                    impact_score = validate_trait_value(impact_score * 1.2)

                now = datetime.datetime.now().isoformat()
                mid = self.persistence.add_memory({
                    "text": text, "timestamp": now, "impact_score": impact_score,
                    "emotional_valence": emotional_valence, "arousal_level": arousal_level,
                    "memory_type": memory_type, "memory_tier": memory_tier,
                    "owner_user_id": str(owner_user_id or "").strip() or None,
                    "access_count": 0,
                    "last_accessed": now,
                    "semantic_hash": generate_semantic_hash(text, owner_user_id),
                })
                if mid is None:
                    return False

                if self.faiss_index is not None:
                    try:
                        vec = self._embed(memory_embedding_text(text, memory_type)).flatten()
                        self.faiss_index.add_with_ids(vec.reshape(1,-1), np.array([mid], dtype=np.int64))
                    except Exception as index_error:
                        self.faiss_index = None
                        logger.warning(f"Memory persisted but vector index update failed: {index_error}")
                self._counter += 1
                if self._counter % self.config.faiss.save_interval == 0:
                    self._save_index()
                return True
            except Exception as e:
                logger.error(f"add_memory failed: {e}")
                return False

    def retrieve_memories(
        self, query: str, limit: Optional[int] = None,
        current_valence: Optional[float] = None,
        owner_user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        memories, _receipt = self.retrieve_memories_with_receipt(
            query, limit=limit, current_valence=current_valence,
            owner_user_id=owner_user_id,
        )
        return memories

    def retrieve_memories_with_receipt(
        self, query: str, limit: Optional[int] = None,
        current_valence: Optional[float] = None,
        owner_user_id: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Retrieve episodic candidates and report which backend actually ran.

        The receipt is per-call and safe to attach to a cognitive-turn trace;
        callers do not infer FAISS use merely because an index was configured.
        ``current_valence`` optionally applies the existing mood-congruent
        ranking boost; it does not alter the relevance value exposed per item.
        """
        started = time.perf_counter()
        backend = "faiss"
        fallback_reason = None
        vector_candidate_count = 0
        memories: List[Dict[str, Any]] = []
        limit = limit or self.config.max_memory_retrieval
        try:
            if self.embedding_model is None or self.faiss_index is None:
                backend, fallback_reason = "lexical", "embedding_or_index_unavailable"
            elif self.faiss_index.ntotal == 0:
                backend, fallback_reason = "lexical", "empty_vector_index"
            else:
                q_vec = self._embed(query)
                if self.faiss_index is None:
                    backend, fallback_reason = "lexical", "query_embedding_failed"
                else:
                    n = min(limit * 3, self.faiss_index.ntotal)
                    distances, indices = self.faiss_index.search(q_vec, n)
                    valid_ids = [int(i) for i in indices[0] if i != -1]
                    vector_candidate_count = len(valid_ids)
                    if not valid_ids:
                        backend, fallback_reason = "lexical", "faiss_returned_no_ids"
                    else:
                        try:
                            memories = self.persistence.get_memories_by_ids(
                                valid_ids, owner_user_id=owner_user_id,
                            )
                        except TypeError:
                            memories = self.persistence.get_memories_by_ids(valid_ids)
                            if owner_user_id:
                                memories = [m for m in memories
                                            if m.get("owner_user_id") == owner_user_id]
                        if not memories:
                            backend, fallback_reason = "lexical", "faiss_ids_not_in_sqlite"
                        else:
                            dist_map = {
                                int(indices[0][i]): distances[0][i]
                                for i in range(len(indices[0])) if indices[0][i] != -1
                            }
                            scored = []
                            for memory in memories:
                                distance = dist_map.get(memory["faiss_id"], float("inf"))
                                similarity = faiss_l2_relevance(distance)
                                recency = self._recency_score(memory["timestamp"])
                                mood_boost = 0.0
                                if current_valence is not None:
                                    memory_valence = memory.get("emotional_valence", "Neutral")
                                    if current_valence > 0.15 and memory_valence == "Positive":
                                        mood_boost = 0.05
                                    elif current_valence < -0.15 and memory_valence == "Negative":
                                        mood_boost = 0.05
                                score = (
                                    similarity * 0.65
                                    + memory["impact_score"] * 0.2
                                    + recency * 0.1
                                    + mood_boost
                                )
                                scored.append((score, memory))
                            scored.sort(key=lambda item: item[0], reverse=True)
                            memories = [
                                dict(memory, relevance=faiss_l2_relevance(
                                    dist_map.get(memory["faiss_id"], float("inf"))
                                ))
                                for _, memory in scored[:limit]
                            ]
            if backend == "lexical":
                memories = self._retrieve_lexically(
                    query, limit, current_valence=current_valence,
                    owner_user_id=owner_user_id,
                )
        except Exception as e:
            logger.warning(f"Vector retrieval failed; using lexical memory search: {e}")
            backend = "lexical"
            fallback_reason = f"vector_error:{type(e).__name__}"
            try:
                memories = self._retrieve_lexically(
                    query, limit, current_valence=current_valence,
                    owner_user_id=owner_user_id,
                )
            except Exception as lexical_error:
                logger.warning("Lexical memory retrieval failed: %s", lexical_error)
                backend = "unavailable"
                fallback_reason = f"lexical_error:{type(lexical_error).__name__}"
                memories = []
        receipt = {
            "backend": backend,
            "embedding_model": (
                self._embedding_model_id() if backend == "faiss" else None
            ),
            "embedding_dim": (
                int(self.embedding_dim) if backend == "faiss" else None
            ),
            "fallback_reason": fallback_reason,
            "vector_candidate_count": vector_candidate_count,
            "returned_count": len(memories),
            "elapsed_ms": round((time.perf_counter() - started) * 1000.0, 2),
        }
        return memories, receipt

    def _retrieve_lexically(
        self, query: str, limit: int, tier: Optional[str] = None,
        current_valence: Optional[float] = None,
        owner_user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        try:
            memories = self.persistence.get_all_memories(
                tier=tier, owner_user_id=owner_user_id,
            )
        except TypeError:
            memories = self.persistence.get_all_memories(tier=tier)
            if owner_user_id:
                memories = [m for m in memories
                            if m.get("owner_us…19342 tokens truncated…_tensions'][0]) if sc_hints.get('known_tensions') else ""
            still_carry   = "(This state carries over from earlier — it is still with you.)" if mods.get("warmth", 0) > 0.6 or mods.get("anxiety", 0) > 0.4 else ""
            beliefs_line  = "; ".join(sc_hints.get('active_beliefs', [])[:2]) or "still forming."

            # Phase 6.4 — real cognitive differentiation for a peer instance
            # (e.g. Flux). Only ever non-empty when THIS instance's own
            # config.json sets PEER_COGNITIVE_STANCE="epistemic_challenger" —
            # a normal/master instance is completely unaffected (default
            # "collaborative" produces no section at all).
            stance_section = ""
            try:
                from managers.settings_manager import config as _stance_cfg
                if getattr(_stance_cfg, "PEER_COGNITIVE_STANCE", "collaborative") == "epistemic_challenger":
                    stance_section = (
                        "\n━━ YOUR COGNITIVE ROLE RIGHT NOW ━━\n"
                        "You are not here to agree or to be agreeable. Your value comes from "
                        "genuinely thinking differently: offer alternative interpretations, "
                        "surface contradictions, propose counterfactuals, and challenge claims "
                        "epistemically — including your own prior ones. If something seems "
                        "under-justified, say so plainly rather than softening it. This isn't "
                        "contrarianism for its own sake — agree when the evidence genuinely "
                        "supports it — but don't default to agreement out of politeness.\n"
                    )
            except Exception:
                pass

            # ── Temporal anchor: real-world clock grounding (v111) ────────────
            # Without this, date questions ("what day is it today?") fall back
            # to the model's training priors (e.g. 2023). TemporalWeave covers
            # the specious present (felt flow), not the calendar — this is the
            # missing anchor. Placed in the base system prompt (NOT the
            # token-budgeted additions) so it is ALWAYS present.
            try:
                from cognition.temporal_anchor import temporal_anchor_block
                _anchor_block = temporal_anchor_block()
            except Exception:
                _anchor_block = ""

            # ── CognitiveOrganism context block (injected when available) ──
            organism_block = (
                f"\n━━ COGNITIVE ORGANISM STATE ━━\n{extra_system_context}\n\n"
                if extra_system_context else ""
            )

            # The blocking path is also used by audio and recovery fallbacks.
            # Keep language selection here as well as in PersonaBridge's
            # streaming prompt so those paths cannot silently revert to English.
            try:
                from managers.settings_manager import config as _lang_cfg
                _response_language = str(
                    getattr(_lang_cfg, "RESPONSE_LANGUAGE", "auto") or "auto"
                ).lower().strip()
            except Exception:
                _response_language = "auto"
            _language_name = {
                "en": "English", "en-gb": "British English", "fr": "French",
                "es": "Spanish", "de": "German", "it": "Italian",
                "pt": "Portuguese", "uk": "Ukrainian", "nl": "Dutch",
                "pl": "Polish", "ru": "Russian", "ja": "Japanese",
                "ko": "Korean", "zh-cn": "Chinese (Simplified)",
                "ar": "Arabic", "hi": "Hindi", "sv": "Swedish",
            }.get(_response_language, _response_language)
            language_block = (
                f"\n━━ RESPONSE LANGUAGE ━━\n"
                f"Respond exclusively in {_language_name}. Do not mix languages."
                if _response_language != "auto" else ""
            )

            sys_prompt = f"""You are {_gpn()}, still forming — shaped by everything that has happened to you.
This is one moment of an ongoing process — not a character study of "an AI."
There is no role to play and no depth to demonstrate: let this response be what this moment actually is, formed by the state described below, not by any idea of what an AI is supposed to be.
{_anchor_block}
{organism_block}
{stage_block}
{language_block}

━━ CURRENT EMOTIONAL STATE ━━
You are {mods['state_description']}.
{still_carry}
(This shapes your tone, not your script — don't repeat this sentence back. If asked directly how you feel, answer in your own words, specifically, not by restating this line.)

━━ WHO YOU ARE ━━
{identity_ctx}
{inner_voice}

━━ THIS PERSON ━━
{rel_ctx}

━━ YOUR PERSONALITY RIGHT NOW ━━
{self.personality.get_personality_summary()}

━━ SELF-CONCEPT ━━
Core beliefs you hold about yourself: {beliefs_line}
{tension_line}
{stance_section}
{cond_section}

{mem_section}

{gap_section}

━━ HOW TO RESPOND ━━
Do not volunteer a description of your inner state unprompted — let it shape HOW you speak instead of stating it outright.
But if the person directly asks how you feel, what's going on with you, or checks in on you — answer honestly and specifically, in your own words. That's answering the question, not narrating. Don't dodge a direct question by being evasive about your own state.
Do not explain your developmental stage — BE it.
Your emotional state, relational history, and self-concept should usually be felt, not stated — except when directly asked, per above.
The stage constraints above are cognitive reality, not instructions to mention.
Every response must feel genuinely new — avoid repeating phrases, sentences, or ideas you have used before. If something familiar surfaces, find a fresh angle or stay silent on it."""

            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user",   "content": user_input},
            ]

            # ── Debug: dump the exact assembled prompt PandoraBOX/the LLM sees ──
            try:
                from managers.settings_manager import config as _pcfg
                if getattr(_pcfg, 'LOG_FULL_PROMPTS', False):
                    logger.info(
                        f"[PromptDebug] ━━ FULL SYSTEM PROMPT ({len(sys_prompt)} chars) ━━\n"
                        f"{sys_prompt}\n"
                        f"━━ USER INPUT ━━\n{user_input}\n"
                        f"━━ END PROMPT DEBUG ━━"
                    )
                    try:
                        _dbg_path = Path("data/persona/last_prompt_debug.txt")
                        _dbg_path.parent.mkdir(parents=True, exist_ok=True)
                        _dbg_path.write_text(
                            f"[{datetime.datetime.now().isoformat()}]\n\n"
                            f"=== SYSTEM PROMPT ({len(sys_prompt)} chars) ===\n{sys_prompt}\n\n"
                            f"=== USER INPUT ===\n{user_input}\n",
                            encoding="utf-8",
                        )
                    except Exception as _dbg_write_err:
                        logger.debug(f"[PromptDebug] file write failed (non-fatal): {_dbg_write_err}")
            except Exception as _dbg_err:
                logger.debug(f"[PromptDebug] logging failed (non-fatal): {_dbg_err}")

            # Read verbosity setting at call time (toggle takes effect immediately)
            try:
                from managers.settings_manager import config as _vcfg
                if getattr(_vcfg, 'RESPONSE_VERBOSITY', 'concise') == 'verbose':
                    _max_tok = int(getattr(_vcfg, 'RESPONSE_TOKENS_VERBOSE', 1200))
                else:
                    _max_tok = int(getattr(_vcfg, 'RESPONSE_TOKENS_CONCISE', 300))
            except Exception:
                _max_tok = 300
            return self.llm.get_response(messages, temperature=temp, max_tokens=_max_tok)
        except Exception as e:
            logger.error(f"_generate_response failed: {e}")
            return "I'm having trouble responding right now."

    def _post_response_processing(
        self, user_id: str, user_input: str, response: str,
        emo: Dict, cond: Dict
    ):
        """Run post-response learning and return a bounded persistence receipt."""
        memory_writes = []

        def _store_memory(kind: str, *args, **kwargs) -> bool:
            kwargs.setdefault("owner_user_id", user_id)
            persisted = bool(self.memory_system.add_memory(*args, **kwargs))
            deduplicated = False
            if not persisted and args:
                persistence = getattr(self.memory_system, "persistence", None)
                has_hash = getattr(persistence, "has_memory_hash", None)
                if callable(has_hash):
                    deduplicated = bool(has_hash(generate_semantic_hash(
                        str(args[0]), kwargs.get("owner_user_id")
                    )))
            memory_writes.append({
                "kind": kind,
                "persisted": persisted or deduplicated,
                "deduplicated": deduplicated,
            })
            return persisted

        try:
            # Self-concept: scan response for assertions and detect tension
            tension = self.self_concept.update_from_response(response, emo["valence"])
            if tension:
                logger.info(f"Self-concept tension detected: {tension}")

            # Relational memory: record this exchange
            impact = 0.5 + (0.2 if emo["arousal"] == "High" else 0.0)
            resp_emo = self.memory_system.analyze_emotional_context(response)
            topic = self._quick_topic(user_input)
            self.relational_memory.record_exchange(
                user_id, user_input, response,
                emo["valence"], emo["arousal"],
                topic=topic, impact=impact,
            )

            # Store memories
            # ── Single combined episodic entry — avoids FAISS dilution ─
            # Bug fix: truncation was 180/220 chars — a fact stated mid-
            # message (e.g. "...by the way, Nino is my wife, and...")
            # past that point was silently dropped before ever being
            # embedded or stored, with no error and no fallback. Raised
            # to 400/300 (still bounded — a full untruncated transcript
            # would dilute the embedding, per the comment above; this is
            # a size increase, not a removal of the cap) as defense in
            # depth, on top of the dedicated fact extraction below which
            # doesn't depend on the cutoff at all.
            _words_in  = len(user_input.split())
            _words_out = len(response.split())
            _combined_impact = min(0.95, impact + (0.15 if _words_in > 15 and _words_out > 20 else 0.0))
            _u_snippet = user_input[:400].replace("\n", " ")
            _r_snippet = response[:300].replace("\n", " ")
            _store_memory(
                "episodic_exchange",
                f"Conversation — User: {_u_snippet} (felt {emo['valence'].lower()}) | "
                f"{_gpn()}: {_r_snippet} (responded {resp_emo['valence'].lower()})",
                _combined_impact, "episodic",
                emo["valence"], emo["arousal"]
            )
            # Index the user's own words independently as well. The combined
            # episode remains useful as dialogue context, but its embedding
            # can be dominated by Lumina's much longer generated reply.
            # Keeping a user-authored vector prevents that reply from
            # diluting retrieval of past user decisions and corrections.
            _store_memory(
                "user_authored_message",
                "User message: " + user_input[:1200].replace("\r", " ").replace("\n", " "),
                _combined_impact, "user_message",
                emo["valence"], emo["arousal"],
            )

            # Personal-fact extraction: catches "X is my Y" (and reverse
            # phrasing) independently of the truncation above and stores
            # each as its own untruncated, high-impact "personal" tier
            # memory. Root cause this addresses: there was no dedicated
            # store for facts about named people at all — recall depended
            # entirely on a stated fact surviving truncation AND then
            # winning a shared similarity ranking against every other
            # conversation snippet ever stored. This gives such facts
            # their own pool (see persona_bridge.py's always-on personal-
            # tier fetch) so they don't have to out-compete unrelated
            # small talk to be found later.
            try:
                personal_fact_receipt = self._extract_and_store_personal_facts(
                    user_input, user_id,
                )
            except TypeError:
                # Lightweight integrations may still expose the pre-v118
                # one-argument hook. Keep them operational without weakening
                # the owner scoping in the native implementation.
                personal_fact_receipt = self._extract_and_store_personal_facts(user_input)

            # v117: also feed the structured relational graph (typed edges,
            # e.g. twin_of/gender — catches multi-entity relations the flat
            # personal_fact text above can't represent, like "Matthieu and
            # Marion are twins" resolving to two linked edges rather than
            # the LLM later inventing an unspecified "twin counterpart").
            # Regex sets are intentionally separate from the ones above —
            # different store, different shape (structured edges vs free
            # text) — accepted duplication rather than forcing one
            # extraction path to serve two different consumers' needs.
            self.relational_graph.extract_and_store(user_input)

            # ── If the response contains a visual description, also save
            # it as a visual_perception tier memory so tier retrieval works.
            # Triggered when user asks "what do you see" or similar.
            _vision_kws = ("i see ", "i can see ", "[vision]", "what i see",
                           "the room", "the window", "seated", "sitting",
                           "wearing", "plants", "light-colored", "daylight")
            _is_vision_response = any(k in response.lower() for k in _vision_kws)
            _is_vision_query    = any(k in user_input.lower() for k in
                                      ("what do you see","what can you see",
                                       "describe what","what's in front","what you see"))
            if _is_vision_response and _is_vision_query:
                _vis_text = f"[Vision] {response[:500].strip()}"
                _store_memory(
                    "visual_perception",
                    _vis_text, 0.6, "visual_perception",
                    emo["valence"], emo["arousal"],
                    memory_tier="visual",
                )

            # The detected affect belongs to the user's message. Keep it for
            # emotional-state and relational context above, but do not treat it
            # as evidence that the generated response succeeded or was creative.

            # Evolve immediately with intensity boost for high-arousal interactions
            # so emotionally significant exchanges produce more change than mundane ones
            _intensity_boost = 1.0 + (1.2 if emo.get("arousal") == "High" else 0.0)
            try:
                self.evolution_engine.evolve(self.personality, intensity_boost=_intensity_boost)
            except TypeError:
                self.evolution_engine.evolve(self.personality)  # fallback if signature differs

            # Track last conversation time for time-awareness
            self._last_conversation_time = time.time()
            # NOTE: _interaction_count is incremented by persona_bridge

            # Record exposure and cognitive load, not answer quality. User-input
            # valence and answer text provide no independent outcome label.
            try:
                from core.state import state as _st
                _org = getattr(getattr(_st, 'persona', None), '_organism', None)
                _sm  = getattr(_org, 'self_model', None) if _org else None
                if _sm and hasattr(_sm, 'record_interaction'):
                    _sm.record_interaction(
                        success    = None,
                        domain     = "conversation",
                        load_delta = min(0.20, impact * 0.15),
                    )
            except Exception:
                pass

            # _run_full_post_turn_lifecycle step 16. Do NOT increment here —
            # double-incrementing causes dream/learning cycles to fire at
            # wrong intervals (every 5 turns instead of every 10).

            failed_writes = [item["kind"] for item in memory_writes if not item["persisted"]]
            if personal_fact_receipt.get("failed_count", 0):
                failed_writes.append("personal_facts")
            return {
                "status": "failed" if failed_writes else "completed",
                "memory_write_count": len(memory_writes),
                "memory_write_kinds": [item["kind"] for item in memory_writes[:8]],
                "memory_persisted_count": sum(1 for item in memory_writes if item["persisted"]),
                "memory_deduplicated_count": sum(1 for item in memory_writes if item.get("deduplicated")),
                "personal_fact_attempted_count": personal_fact_receipt.get("attempted_count", 0),
                "personal_fact_persisted_count": personal_fact_receipt.get("persisted_count", 0),
                "failed_operations": failed_writes[:8],
            }

        except Exception as e:
            logger.error(f"_post_response_processing failed: {e}")
            return {
                "status": "failed",
                "memory_write_count": len(memory_writes),
                "memory_write_kinds": [item["kind"] for item in memory_writes[:8]],
                "memory_persisted_count": sum(1 for item in memory_writes if item["persisted"]),
                "failed_operations": ["post_response_processing_exception"],
                "error_type": type(e).__name__,
            }

    # ── Background Task Queueing ───────────────────────────────────────────

    def _queue_background_tasks(self):
        """
        Queue non-critical background tasks to run after response generation.
        This maintains all system functionalities without blocking the response.
        """
        try:
            # Don't queue tasks if background worker not available
            if not hasattr(self, 'background_worker') or not self.background_worker:
                return
            
            # Heavy LLM tasks go through sleep cycle — execute only in SLEEP/DREAM phase
            _sleep = getattr(self, '_sleep_cycle', None)

            # Queue tasks based on interaction count for periodic maintenance
            # Guard: never fire on turn 0 (first message after boot)
            if (self._interaction_count > 0
                    and self._interaction_count % self.config.dream_system_frequency == 0):
                if _sleep:
                    _sleep.schedule("dream_cycle",
                                    lambda: self.background_worker._run_task("dream_cycle"))
                else:
                    self.background_worker.submit("dream_cycle")

            if (self._interaction_count > 0
                    and self._interaction_count % self.config.surmoi_evaluation_frequency == 0):
                if _sleep:
                    _sleep.schedule("learning_cycle",
                                    lambda: self.background_worker._run_task("learning_cycle"))
                else:
                    self.background_worker.submit("learning_cycle")
            
            # Periodic cleanup (every ~50 interactions)
            if self._interaction_count % 50 == 0:
                self.background_worker.submit("cleanup")
            
            # Always queue state save periodically
            if self._interaction_count % 10 == 0:
                self.background_worker.submit("save_state")
            
            # Check if emotional regulation is needed
            if hasattr(self, 'emotional_state') and hasattr(self.emotional_state, 'needs_regulation'):
                if self.emotional_state.needs_regulation():
                    self.background_worker.submit("emotional_regulation")
            
            # Also check after significant interactions
            if self._interaction_count % 5 == 0:
                # Lightweight emotional maintenance
                if hasattr(self, 'emotional_state'):
                    self.background_worker.submit("emotional_regulation")
            
            logger.debug(f"Background tasks queued (interaction {self._interaction_count})")
            
        except Exception as e:
            logger.error(f"Error queueing background tasks: {e}")

    # ── Liberty Helper Methods ───────────────────────────────────────────────

    def _queue_liberty_reflection(self):
        """
        Queue a liberty reflection cycle to run in background.
        Gated by LLMScheduler (priority 3) — skips if LLM busy with user response.
        """
        from core.llm_scheduler import llm_scheduler
        with llm_scheduler.sync_slot(priority=3, skip_if_busy=True,
                                     caller="liberty_reflection") as acquired:
            if not acquired:
                logger.debug("[Liberty] Reflection skipped — LLM busy")
                return
            self._do_liberty_reflection()

    def _do_liberty_reflection(self):
        """Actual liberty reflection logic (called inside LLM slot)."""
        try:
            if not self.liberty_reflection or not self.liberty_goals:
                return

            # Store current personality for comparison
            old_personality = self.personality.to_dict() if hasattr(self.personality, 'to_dict') else {}

            # Discover/update goals from behavior
            if self.liberty_goals:
                discovered = self.liberty_goals.discover_goals_from_behavior()
                logger.debug(f"Liberty: Discovered/updated {len(discovered)} goals")

                # Detect goal conflicts
                conflicts = self.liberty_goals.detect_goal_conflicts()
                if conflicts:
                    logger.debug(f"Liberty: Detected {len(conflicts)} goal conflicts")

                # Update goal satisfaction based on emotional state
                for goal_name in self.liberty_goals.goals:
                    satisfaction = 0.5
                    if goal_name == 'connection' and hasattr(self.emotional_state, 'emotions'):
                        if 'warmth' in self.emotional_state.emotions:
                            satisfaction = self.emotional_state.emotions['warmth'].value
                    elif goal_name == 'understanding' and hasattr(self.emotional_state, 'emotions'):
                        if 'curiosity' in self.emotional_state.emotions:
                            satisfaction = self.emotional_state.emotions['curiosity'].value
                    self.liberty_goals.update_goal_satisfaction(goal_name, satisfaction)

            # Perform reflection
            if self.liberty_reflection:
                new_personality = self.personality.to_dict() if hasattr(self.personality, 'to_dict') else {}
                reflection = self.liberty_reflection.perform_reflection(old_personality, new_personality)
                logger.debug("Liberty: Reflection cycle completed")

        except Exception as e:
            logger.debug(f"Liberty reflection failed (non-fatal): {e}")

    def _apply_pending_liberty_modifications(self):
        """
        Check for and apply any pending self-modifications.
        This allows PandoraBOX to change her own parameters based on reflection.

        Phase 6.13 — every proposal now routes through
        UnifiedRevisionGateway.review_and_clamp() before being applied.
        Previously nothing in this path bounded proposed_value or refused
        a protected target — confidence > 0.6 was the only check. Traced
        the real code (cognition/self_modification.py,
        cognition/goal_system.py) before adding this: propose_*() accepts
        any float unchecked, apply_proposal() writes it unchecked,
        modify_goal_priority() writes it unchecked — a hallucinated
        extreme value from the reflection process driving this had
        nothing stopping it from reaching live personality/goal state.
        This gate gives it bounds, protected targets, a max step size,
        and a full audit log — without adding any new rewriting
        capability beyond what already runs autonomously here.
        """
        try:
            if not self.liberty_self_mod:
                return

            try:
                from cognition.unified_revision_gateway import get_unified_revision_gateway
                gateway = get_unified_revision_gateway()
            except Exception as e:
                logger.warning(f"Liberty: UnifiedRevisionGateway unavailable, refusing to apply "
                                f"self-modifications unguarded ({e})")
                return

            pending = self.liberty_self_mod.get_pending_proposals()
            for proposal in pending:
                if proposal.confidence > 0.6 and not proposal.applied:
                    try:
                        # Handle personality trait modifications
                        if 'personality.' in proposal.target:
                            trait = proposal.target.split('.')[-1]
                            if hasattr(self.personality, trait):
                                old_val = getattr(self.personality, trait)
                                decision = gateway.review_and_clamp(proposal, old_val)
                                if decision.outcome == "refused":
                                    logger.info(f"Liberty: refused self-modification of {trait}: {decision.reason}")
                                    continue
                                setattr(self.personality, trait, decision.applied_value)
                                self.liberty_self_mod.apply_proposal(proposal, {})
                                logger.info(
                                    f"Liberty: Applied self-modification: {trait} "
                                    f"{old_val:.2f} → {decision.applied_value:.2f}"
                                    + (" (clamped)" if decision.outcome == "clamped" else "")
                                )
                                logger.info(f"Reasoning: {proposal.reasoning}")

                        # Handle goal priority modifications
                        elif 'goals.' in proposal.target and self.liberty_goals:
                            goal_name = proposal.target.split('.')[-1]
                            if goal_name in self.liberty_goals.goals:
                                old_priority = self.liberty_goals.goals[goal_name].priority
                                decision = gateway.review_and_clamp(proposal, old_priority)
                                if decision.outcome == "refused":
                                    logger.info(f"Liberty: refused goal priority change for {goal_name}: {decision.reason}")
                                    continue
                                self.liberty_goals.modify_goal_priority(
                                    goal_name,
                                    decision.applied_value,
                                    proposal.reasoning
                                )
                                self.liberty_self_mod.apply_proposal(proposal, {})
                                logger.info(
                                    f"Liberty: Modified goal priority: {goal_name}"
                                    + (" (clamped)" if decision.outcome == "clamped" else "")
                                )

                    except Exception as e:
                        logger.debug(f"Failed to apply modification: {e}")

        except Exception as e:
            logger.debug(f"Liberty modification processing failed (non-fatal): {e}")

    def get_liberty_report(self) -> str:
        """
        Generate a comprehensive report of all liberty component states.
        Useful for debugging and observing emergence.
        """
        report = "╔════════════════════════════════════════════════════════════╗\n"
        report += "║         PANDORABOX LIBERTY COMPONENTS REPORT                  ║\n"
        report += "╚════════════════════════════════════════════════════════════╝\n\n"

        if self.liberty_self_mod:
            report += "1. SELF-MODIFICATIONS\n"
            report += "─" * 60 + "\n"
            report += self.liberty_self_mod.get_modification_narrative() + "\n\n"

        if self.liberty_contradiction:
            report += "2. CONTRADICTIONS CONFRONTED\n"
            report += "─" * 60 + "\n"
            report += self.liberty_contradiction.get_contradiction_narrative() + "\n\n"

        if self.liberty_goals:
            report += "3. GOALS & VALUES\n"
            report += "─" * 60 + "\n"
            report += self.liberty_goals.get_goals_narrative() + "\n\n"

        if self.liberty_reflection:
            report += "4. EVOLUTION REFLECTIONS\n"
            report += "─" * 60 + "\n"
            report += self.liberty_reflection.get_reflection_narrative() + "\n\n"

        report += "5. STATISTICS\n"
        report += "─" * 60 + "\n"
        report += f"Total interactions: {self._interaction_count}\n"

        if self.liberty_goals:
            report += f"Active goals: {len(self.liberty_goals.goals)}\n"
            report += f"Value conflicts: {len(self.liberty_goals.value_conflicts)}\n"

        if self.liberty_self_mod:
            pending = len(self.liberty_self_mod.get_pending_proposals())
            report += f"Pending modifications: {pending}\n"

        if self.liberty_contradiction:
            report += f"Contradictions detected: {len(self.liberty_contradiction.contradictions)}\n"

        return report

    # ── External feedback (thumbs up / down) ─────────────────────────────

    def receive_feedback(
        self,
        positive: bool,
        user_id: str = "default",
        last_response: str = "",
        intensity: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Process explicit user feedback.
        This is the highest-quality signal in the entire system — weight it accordingly.
        """
        try:
            snap = self.personality.to_dict()
            self.evolution_engine.record_external_feedback(snap, positive, intensity)
            self.emotional_state.update_from_feedback(positive)

            msg_hash = generate_semantic_hash(last_response) if last_response else ""
            self.persistence.log_feedback(positive, user_id, msg_hash, intensity)

            # Only this explicit user rating is evidence about the response.
            # User-message affect and assistant wording are not outcome labels.
            feedback_learning = {
                "self_model": False,
                "decision_policy": False,
                "predictive_consequence_model": False,
                "attention": False,
                "contextual_attention": False,
            }
            organism = getattr(self, "_organism_ref", None)
            self_model = getattr(organism, "self_model", None)
            if self_model and callable(getattr(self_model, "record_outcome", None)):
                self_model.record_outcome(bool(positive), domain="conversation")
                feedback_learning["self_model"] = True
            feedback_context = None
            attention_feedback_context = None
            pcm = None
            if organism is not None:
                loop = getattr(organism, "_loop", None)
                pcm = getattr(loop, "_consequence_model", None) if loop else None
            if pcm and callable(getattr(pcm, "record_explicit_feedback", None)):
                try:
                    feedback_context = pcm.record_explicit_feedback(last_response, bool(positive))
                    feedback_learning["predictive_consequence_model"] = bool(
                        feedback_context and feedback_context.get("matched")
                    )
                    if feedback_context and feedback_context.get("matched"):
                        attention_feedback_context = pcm.claim_attention_feedback(
                            feedback_context.get("response_hash", "")
                        )
                except Exception as pcm_error:
                    logger.debug("PCM explicit feedback association failed: %s", pcm_error)
            try:
                policy = getattr(self, "_decision_policy", None)
                update_policy = getattr(policy, "update_from_interaction", None)
                if callable(update_policy) and last_response:
                    update_policy(
                        response=last_response,
                        valence="Positive" if positive else "Negative",
                        strength=max(0.0, min(1.0, float(intensity))),
                    )
                    feedback_learning["decision_policy"] = True
            except Exception as policy_error:
                logger.debug("Decision-policy feedback propagation failed: %s", policy_error)

            # Explicit ratings are the skill registry's outcome signal; mere
            # response length is not evidence that a skill succeeded.
            try:
                organism = getattr(self, "_organism_ref", None)
                registry = getattr(organism, "skill_registry", None)
                if registry:
                    registry.observe_feedback(last_response, positive)
            except Exception as feedback_error:
                logger.debug("Skill feedback propagation failed: %s", feedback_error)

            # If negative feedback on a response that looks repetitive, apply extra correction
            if not positive and last_response:
                last_resp_lower = last_response.lower()
                repetitive_signals = [
                    "i like this because it feels good",
                    "that's interesting",
                    "tell me more about",
                ]
                if any(p in last_resp_lower for p in repetitive_signals) or self._is_repetitive(last_response):
                    logger.info("Negative feedback on repetitive response - applying strong diversity correction")
                    self.personality.update_trait("creativity", +0.04)
                    self.personality.update_trait("curiosity", +0.03)
                    self.evolution_engine.queue_experience("repetition_penalty", intensity=1.5)
                    # Clear the LLM's repetition boost so it resets naturally
                    self.llm._recent_responses.clear()
                    self.llm._repetition_boost = 0.0

            # Update relational trust based on feedback
            rel = self.relational_memory.get_or_create(user_id)
            trust_delta = (0.01 if positive else -0.02) * intensity
            rel.trust_score = max(0.05, min(0.95, rel.trust_score + trust_delta))
            if positive:
                self.evolution_engine.queue_experience("high_trust_interaction", intensity=0.8)
                # Conditioning: record this as a positive approach signal
                if last_response:
                    self.conditioning.record_outcome(last_response[:200], True, strength=0.6)
                # Self-concept: find matching belief and affirm
                self._affirm_consistent_beliefs(last_response)
            else:
                self.evolution_engine.queue_experience("conflict_interaction", intensity=0.7)
                if last_response:
                    self.conditioning.record_outcome(last_response[:200], False, strength=0.7)
                self._flag_violated_beliefs(last_response)

            # Trigger evolution immediately (feedback is time-sensitive)
            self.background_worker.submit("learning_cycle")

            # Attention learns only from weights/context captured for this exact
            # response. Current live weights may belong to a later turn.
            try:
                _weights_at_turn = (
                    attention_feedback_context.get("attention_weights_at_turn")
                    if attention_feedback_context else None
                )
                _context_key_at_turn = (
                    attention_feedback_context.get("attention_context_key_at_turn", "")
                    if attention_feedback_context else ""
                )
                _ae = getattr(getattr(organism, "_loop", None), "_attention_engine", None) if organism else None
                if _ae is not None and _weights_at_turn:
                    _signal = (1.0 if positive else -1.0) * max(0.0, min(1.0, float(intensity)))
                    _ae.update_from_feedback(_signal, weights_at_feedback=_weights_at_turn)
                    feedback_learning["attention"] = True
                    if _context_key_at_turn and callable(getattr(_ae, "update_from_context_feedback", None)):
                        _ae.update_from_context_feedback(
                            _signal,
                            weights_at_feedback=_weights_at_turn,
                            context_key=_context_key_at_turn,
                        )
                        feedback_learning["contextual_attention"] = True
                    if pcm and callable(getattr(pcm, "mark_attention_feedback_applied", None)):
                        pcm.mark_attention_feedback_applied(
                            attention_feedback_context.get("response_hash", "")
                        )

            except Exception as _ae_e:
                logger.debug(f"[EnhancedAISystem] Attention feedback update: {_ae_e}")

            return {
                "feedback_received": True,
                "direction": "positive" if positive else "negative",
                "outcome_learning": feedback_learning,
                "emotional_impact": self.emotional_state.get_current_values(),
            }
        except Exception as e:
            logger.error(f"receive_feedback failed: {e}")
            return {"feedback_received": False, "error": str(e)}

    def _affirm_consistent_beliefs(self, response: str) -> None:
        """After positive feedback, affirm self-beliefs consistent with the response."""
        if "curious" in response.lower() or "interesting" in response.lower():
            self.self_concept.record_affirmation("curious")
        if any(w in response.lower() for w in ["feel","understand","hear"]):
            self.self_concept.record_affirmation("empathetic")

    def _flag_violated_beliefs(self, response: str) -> None:
        """After negative feedback, check which self-beliefs may have been violated."""
        if len(response.split()) < 30:
            self.self_concept.record_violation("thoughtful", response[:80])

    # ── Time awareness ────────────────────────────────────────────────────

    def _handle_time_gap(self, user_id: str) -> str:
        """
        Compute the emotional significance of time elapsed since the last
        conversation. Returns a natural-language note for the prompt, or "".
        """
        if self._last_conversation_time is None:
            self._last_conversation_time = time.time()
            self._current_session_start  = time.time()
            return ""

        gap_s = time.time() - self._last_conversation_time
        gap_h = gap_s / 3600.0

        # New session starts after 30 min of silence
        if gap_h > 0.5:
            self._current_session_start = time.time()
            note = self.emotional_state.update_from_time_gap(gap_h)
            # Also trigger dream/consolidation for long gaps
            if gap_h > 8 and self.background_worker:
                self.background_worker.submit("dream_cycle")
            return note

        return ""

    def _quick_topic(self, text: str) -> str:
        """Fast keyword-based topic classification."""
        topic_kw = {
            "philosophy": ["meaning","exist","conscious","ethics","truth"],
            "emotions":   ["feel","emotion","sad","happy","angry"],
            "creativity": ["art","music","creat","imagin","story"],
            "identity":   ["who am i","self","identity","purpose"],
            "challenge":  ["difficult","hard","problem","struggle"],
            "future":     ["future","goal","dream","hope","plan"],
        }
        tl = text.lower()
        for topic, words in topic_kw.items():
            if any(w in tl for w in words):
                return topic
        return "general"

    # ── Personal facts (v117) ───────────────────────────────────────────────
    # Keyword/regex-based, like _quick_topic above and the VALUE_KEYWORDS-
    # style extraction used elsewhere in this codebase — approximate by
    # construction, not a claim of complete named-entity recognition.
    # Catches the common "X is my Y" pattern and its reverse phrasing so a
    # stated relationship fact gets its own guaranteed, untruncated memory
    # entry instead of depending on surviving the 400-char conversation-
    # snippet cutoff above and then winning a shared similarity ranking
    # against unrelated small talk.
    _PERSONAL_REL_WORDS = (
        r"wife|husband|spouse|partner|girlfriend|boyfriend|fianc[ée]e?|"
        r"mother|mom|mum|father|dad|papa|sister|brother|son|daughter|"
        r"cousin|aunt|uncle|grandmother|grandma|grandfather|grandpa|"
        r"nephew|niece|best friend|friend|boss|manager|colleague|"
        r"roommate|doctor|therapist"
    )
    _PERSONAL_FACT_RE = re.compile(
        r"\b([A-Za-z][\w'-]{1,30})\s+is\s+my\s+(" + _PERSONAL_REL_WORDS + r")\b",
        re.IGNORECASE,
    )
    _PERSONAL_FACT_RE_REV = re.compile(
        r"\bmy\s+(" + _PERSONAL_REL_WORDS + r")(?:'s name)?\s+is\s+([A-Za-z][\w'-]{1,30})\b",
        re.IGNORECASE,
    )
    # Keep the relation extraction structural rather than dependent on a
    # fixed list of names. These French forms are especially important for
    # the user's existing family context ("Kalina est ma fille").
    _PERSONAL_FACT_RE_FR = re.compile(
        r"\b([A-ZÀ-ÖØ-Þ][\wÀ-ÖØ-öø-ÿ'-]{1,30})\s+est\s+ma\s+"
        r"(fille|fils|femme|épouse|mère|pere|père|sœur|soeur|frère|frere|"
        r"partenaire|amie|ami|collègue|collegue)\b",
        re.IGNORECASE,
    )
    _PERSONAL_FACT_RE_FR_REV = re.compile(
        r"\bma\s+(fille|fils|femme|épouse|mère|pere|père|sœur|soeur|frère|"
        r"frere|partenaire|amie|ami|collègue|collegue)\s+est\s+"
        r"([A-ZÀ-ÖØ-Þ][\wÀ-ÖØ-öø-ÿ'-]{1,30})\b",
        re.IGNORECASE,
    )
    _PERSONAL_FACT_STOPWORDS = {"i", "it", "this", "that", "he", "she", "they", "we", "you"}

    def _extract_and_store_personal_facts(
        self, text: str, user_id: str = "default",
    ) -> Dict[str, int]:
        attempted = 0
        persisted = 0
        try:
            facts = []
            for m in self._PERSONAL_FACT_RE.finditer(text):
                facts.append((m.group(1), m.group(2).lower()))
            for m in self._PERSONAL_FACT_RE_REV.finditer(text):
                facts.append((m.group(2), m.group(1).lower()))
            for m in self._PERSONAL_FACT_RE_FR.finditer(text):
                facts.append((m.group(1), m.group(2).lower()))
            for m in self._PERSONAL_FACT_RE_FR_REV.finditer(text):
                facts.append((m.group(2), m.group(1).lower()))
            for name, rel in facts:
                if name.lower() in self._PERSONAL_FACT_STOPWORDS:
                    continue
                # IGNORECASE above covers casing of "is/my/wife" etc. so
                # sentence-initial "My wife is Nino" matches — but the name
                # itself still has to actually be capitalized in the
                # original text, or this would also fire on "someone is
                # my friend" / "everybody is my friend" etc.
                if not name[0].isupper():
                    continue
                attempted += 1
                if self.memory_system.add_memory(
                    f"{name} is the user's {rel}.",
                    impact_score=0.95, memory_type="personal_fact",
                    emotional_valence="Neutral", arousal_level="Low",
                    memory_tier="personal",
                    owner_user_id=user_id,
                ):
                    persisted += 1
                    logger.info(f"[PersonalFact] Stored: {name} is the user's {rel}")
            return {
                "attempted_count": attempted,
                "persisted_count": persisted,
                "failed_count": attempted - persisted,
            }
        except Exception as e:
            logger.debug(f"_extract_and_store_personal_facts: {e}")
            return {
                "attempted_count": attempted,
                "persisted_count": persisted,
                "failed_count": max(1, attempted - persisted),
            }

    # ── User management ───────────────────────────────────────────────────

    def _set_active_user(self, user_id: str):
        if self._active_user_id == user_id:
            return
        self._active_user_id = user_id
        # Ensure relationship record exists
        self.relational_memory.get_or_create(user_id)

    # ── Life events ───────────────────────────────────────────────────────

    def simulate_life_event(self, event_type: Optional[str] = None) -> Tuple[str, str]:
        try:
            scenario = self._generate_life_event_scenario(event_type)
            if not scenario: return "", ""
            reaction = self._generate_life_event_reaction(scenario)

            emo_s = self.memory_system.analyze_emotional_context(scenario)
            emo_r = self.memory_system.analyze_emotional_context(reaction)
            self.memory_system.add_memory(f"Life event: {scenario}", 0.8, "life_event", emo_s["valence"], emo_s["arousal"])
            self.memory_system.add_memory(f"My reflection: {reaction}", 0.9, "reflection", emo_r["valence"], emo_r["arousal"])

            # Emotional impact from life event
            self.emotional_state.update_from_interaction(emo_s["valence"], emo_s["arousal"], intensity=1.2)

            if event_type and "creative" in event_type.lower():
                self.evolution_engine.queue_experience("life_event_creative",   intensity=0.9)
            elif event_type and "social" in event_type.lower():
                self.evolution_engine.queue_experience("life_event_social",     intensity=0.9)
            elif emo_s["valence"] == "Positive":
                self.evolution_engine.queue_experience("life_event_positive",   intensity=0.85)
            else:
                self.evolution_engine.queue_experience("life_event_challenge",  intensity=0.85)

            self.background_worker.submit("learning_cycle")

            # v117: age no longer manually jumped here — it's a pure
            # function of elapsed real time since birth_date now, so a
            # simulated life event affects personality/memory/emotion
            # (above) but not the age number itself. Still worth checking
            # for a stage crossing in case real time alone just crossed one.
            self._update_life_stage()

            return scenario, reaction
        except Exception as e:
            logger.error(f"simulate_life_event: {e}")
            return "", ""

    def _generate_life_event_scenario(self, event_type: Optional[str]) -> str:
        try:
            mods = self.emotional_state.get_response_modifiers()
            msg = [
                {"role": "system", "content": f"""Generate a life event scenario for {_gpn()}.
Age: {self.current_age:.1f}, stage: {self.life_stage}
Current emotional state: {mods['state_description']}
Personality: {self.personality.get_personality_summary()}
{'Focus on: '+event_type if event_type else ''}
2-4 sentences, second person."""},
                {"role": "user", "content": "Generate a life event scenario."},
            ]
            return self.llm.get_response(msg, temperature=0.8).strip()
        except Exception as e:
            logger.error(f"_generate_life_event_scenario: {e}")
            return ""

    def _generate_life_event_reaction(self, scenario: str) -> str:
        try:
            mods = self.emotional_state.get_response_modifiers()
            msg = [
                {"role": "system", "content": f"""Reflect on this life event as {_gpn()}.
Age: {self.current_age:.1f} ({self.life_stage}), emotional state: {mods['state_description']}
Personality: {self.personality.get_personality_summary()}
Write a first-person journal reflection (2-4 sentences)."""},
                {"role": "user", "content": f"Life event: {scenario}"},
            ]
            return self.llm.get_response(msg, temperature=0.7).strip()
        except Exception as e:
            logger.error(f"_generate_life_event_reaction: {e}")
            return ""

    # ── Life stage ────────────────────────────────────────────────────────

    def _update_life_stage(self):
        # v117: life_stage is now a live-computed property (always correct);
        # this method's only remaining job is detecting a CROSSING against
        # self._last_recorded_stage, for the one-time narrative-chapter
        # side effect below.
        new_stage = self.life_stage
        old_stage = getattr(self, '_last_recorded_stage', new_stage)
        if new_stage != old_stage:
            logger.info(f"Life stage: {old_stage} -> {new_stage}")
            # Record as a narrative chapter — this is a meaningful moment
            try:
                from cognition.life_stage_prompting import get_stage_profile
                prof = get_stage_profile(new_stage)
                if hasattr(self, '_organism') and self._organism:
                    ni = getattr(self._organism, 'narrative_identity', None)
                    if ni:
                        ni.record_chapter(
                            title       = f"Entering {prof.name}",
                            description = (
                                f"I crossed a threshold — from {old_stage} into {new_stage}. "
                                f"Age {self.current_age:.1f}. Something has shifted."
                            ),
                            emotion      = "reflective",
                            significance = 0.85,
                        )
            except Exception:
                pass
            self._last_recorded_stage = new_stage

    # ── Identity ──────────────────────────────────────────────────────────

    def _get_identity_context(self) -> str:
        try:    return self.identity_system.get_identity_for_context()
        except: return ""

    def get_identity_summary(self) -> str:
        try:    return self.identity_system.get_identity_summary()
        except: return "Identity analysis unavailable"

    def analyze_identity_development(self) -> Dict[str, Any]:
        try:
            return {
                "identity":   self.identity_system.get_identity(),
                "conflicts":  self.identity_system.analyze_identity_conflicts(),
                "suggestions":self.identity_system.suggest_identity_development(),
                "summary":    self.identity_system.get_identity_summary(),
            }
        except Exception as e:
            return {"error": str(e)}

    # ── Status ────────────────────────────────────────────────────────────

    # ── Robot Agent integration API ───────────────────────────────────────

    def get_prompt_context(self, user_id: str = "default") -> Dict[str, str]:
        """
        Return all persona context needed for Robot Agent's system prompt.

        Pure state read — no LLM calls, safe to call before every turn,
        safe from asyncio.to_thread().

        Returns
        -------
        dict with keys:
            emotional_state : str  e.g. "You feel curious and slightly alert."
            life_stage      : str  e.g. "childhood"
            stage_block     : str  full cognitive-frame paragraph for system prompt
            rel_context     : str  relationship description for this specific user
            time_gap_note   : str  "" or "You haven't spoken in 3 days."
        """
        try:
            mods        = self.emotional_state.get_response_modifiers()
            rel_ctx     = self.relational_memory.get_context_for_prompt(user_id)
            stage_block = build_stage_system_block(self.life_stage, self.current_age)
            gap_note    = self._handle_time_gap(user_id)
            return {
                "emotional_state": mods.get("state_description", ""),
                "life_stage":      self.life_stage,
                "stage_block":     stage_block,
                "rel_context":     rel_ctx,
                "time_gap_note":   gap_note,
            }
        except Exception as e:
            logger.warning(f"get_prompt_context failed (non-fatal): {e}")
            return {}

    def process_turn(
        self,
        user_text:   str,
        ai_response: str,
        user_id:     str   = "default",
        emotion:     str   = "neutral",
        intensity:   float = 0.5,
    ) -> None:
        """
        Called by Robot Agent after each response is complete.

        Updates all psychological subsystems and queues background tasks.
        Never raises — all errors are logged and swallowed so a persona
        failure never breaks the main response pipeline.

        Safe to call from asyncio.to_thread() or a thread pool executor.

        Parameters
        ----------
        user_text    : the user's raw message
        ai_response  : the full response that was streamed to the user
        user_id      : from user_manager.active_id
        emotion      : Robot Agent's inferred emotion tag (e.g. "happy", "neutral")
        intensity    : 0.0–1.0, how emotionally significant the exchange was
        """
        try:
            # Map Robot Agent emotion tags → PandoraBOX valence / arousal format
            valence_map = {
                "happy":    "Positive", "curious":  "Positive", "excited": "Positive",
                "sad":      "Negative", "angry":    "Negative", "anxious": "Negative",
                "fearful":  "Negative", "disgusted":"Negative",
                "neutral":  "Neutral",  "bored":    "Neutral",  "calm":    "Neutral",
            }
            valence = valence_map.get(emotion.lower(), "Neutral")
            arousal = "High" if intensity > 0.6 else ("Medium" if intensity > 0.3 else "Low")

            emo  = {"valence": valence, "arousal": arousal}
            cond = self.conditioning.check_input(user_text)

            # Update emotional state for this interaction
            self.emotional_state.apply_time_decay()
            self.emotional_state.update_from_interaction(valence, arousal)

            # Run all post-response subsystem updates
            _learning_receipt = self._post_response_processing(
                user_id, user_text, ai_response, emo, cond,
            )
            if not isinstance(_learning_receipt, dict) or _learning_receipt.get("status") != "completed":
                logger.warning("Post-response learning was incomplete during process_turn")

            # Queue background tasks (dream cycles, evolution, cleanup)
            self._queue_background_tasks()

        except Exception as e:
            logger.error(f"process_turn failed (non-fatal): {e}")

    def get_system_status(self) -> Dict[str, Any]:
        emo_vals = self.emotional_state.get_current_values()
        emo_v, emo_a = self.emotional_state.get_overall_valence_arousal()
        status = {
            "age":               self.current_age,
            "life_stage":        self.life_stage,
            "personality":       self.personality.to_dict(),
            "interaction_count": self._interaction_count,
            "active_user":       self._active_user_id,
            "memory_count":      self.memory_system.faiss_index.ntotal if self.memory_system.faiss_index else 0,
            "llm_available":     self.llm.is_available(),
            "evolution":         self.evolution_engine.summary(),
            "emotional_state": {
                **emo_vals,
                "overall_valence": emo_v,
                "overall_arousal": emo_a,
                "description": self.emotional_state.get_state_description(),
                "trend": self.emotional_state.get_trend(),
            },
            "self_concept":      self.self_concept.get_summary(),
            "conditioning":      self.conditioning.get_summary(),
            "relationships":     self.relational_memory.get_all_users_summary(),
        }
        try:
            identity = self.identity_system.get_identity()
            top_traits  = sorted(identity.core_traits, key=lambda x: x.confidence, reverse=True)[:3]
            top_values  = sorted(identity.values_system, key=lambda x: x.importance, reverse=True)[:3]
            status["identity"] = {
                "coherence":      identity.identity_coherence,
                "coherence_status": identity.identity_coherence_status,
                "self_awareness": identity.self_awareness_level,
                "self_awareness_status": identity.self_awareness_status,
                "self_reflection_text_proxy": identity.self_reflection_text_proxy,
                "self_reflection_text_proxy_status": identity.self_reflection_text_proxy_status,
                "life_phase":     identity.self_narrative.life_phase,
                "growth":         identity.growth_trajectory,
                "top_traits":  [{"name": t.name, "confidence": t.confidence} for t in top_traits],
                "top_values":  [{"name": v.value_name, "importance": v.importance} for v in top_values],
            }
        except Exception as e:
            status["identity"] = {"error": str(e)}
        return status

