"""
semantic_extractor.py — Real-time Semantic Extraction (Global Workspace hook)
==============================================================================

Called after every interaction from cognitive_organism.py post-response hook.
Uses a FAST, lightweight prompt — no full LLM conversation, just a structured
JSON extraction of concepts + relations from the exchange.

Design constraints
------------------
  - Must complete in < 1s  (non-blocking, runs in background thread)
  - LLM call is optional  (falls back to keyword extraction if LLM busy)
  - Durable concepts and relations are grounded in the incoming message
  - Assistant response text is context, never evidence for its own claims
"""

import json
import logging
import math
import queue
import re
import threading
import time
from typing import Dict, List, Optional, Tuple

from cognition.semantic_memory import SemanticMemory

logger = logging.getLogger(__name__)

# Stopwords — never create concepts for these
_STOP = {
    # pronouns / determiners
    "i", "me", "my", "we", "our", "you", "your", "it", "its", "he", "she",
    "his", "her", "they", "them", "their", "this", "that", "these", "those",
    # articles / conjunctions / prepositions
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "of",
    "for", "with", "about", "from", "by", "as", "up", "out", "off", "over",
    "into", "onto", "upon", "after", "before", "since", "until", "while",
    # auxiliaries / common verbs
    "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "must", "shall",
    "get", "got", "go", "went", "come", "came", "make", "made", "say", "said",
    "know", "think", "want", "use", "see", "look", "seem", "tell", "ask",
    "understand", "explain", "describe", "discuss", "consider",
    "put", "take", "give", "show", "find", "let", "keep", "need", "turn",
    # generic adjectives / adverbs that aren't concepts
    "good", "bad", "big", "small", "new", "old", "right", "left", "same",
    "own", "other", "next", "last", "long", "little", "few", "more", "most",
    "just", "also", "very", "really", "quite", "still", "even", "back",
    "well", "much", "many", "any", "some", "all", "both", "each", "such",
    "like", "way", "man", "men", "woman", "women", "thing", "things",
    "time", "year", "day", "way", "part", "place", "case", "point",
    # negations / connectors
    "not", "no", "nor", "so", "if", "then", "than", "too", "only",
    "now", "here", "there", "when", "where", "why", "how", "what", "who",
    # agent name
    "lumina", "fred", "frédéric",
    "avec", "dans", "pour", "mais", "donc", "alors", "comme", "cette",
    "cela", "être", "avoir", "faire", "tout", "tous", "nous", "vous",
    "quoi", "quel", "quelle", "quand", "pourquoi", "comment", "sans",
    "je", "tu", "il", "elle", "on", "me", "te", "se", "est", "suis",
    "sont", "dois", "doit", "faire", "fait", "ma", "mon", "mes", "au",
    "aux", "du", "des", "les", "une", "un", "et", "ou", "pas", "qui",
    "que", "quoi", "où", "leur", "leurs", "nous", "vous", "dans", "sur",
    # Conversation fillers and inflected forms frequently extracted as topics.
    "toujours", "quelles", "quels", "assez", "sois", "soit", "soyez",
    "savoir", "curieux", "curieuse", "curiosité", "tente", "essayez",
    "essaie", "peux", "peut", "pourrais", "pourrait", "dites", "faut",
    "semble", "sembler", "vraiment",
}

# Minimum character length for a concept to be kept
_MIN_CONCEPT_LEN = 4

# Concepts that are too generic even if not in stopwords
_GENERIC_CONCEPTS = {
    "thing", "things", "something", "anything", "everything", "nothing",
    "someone", "anyone", "everyone", "person", "people", "world", "life",
    "work", "working", "done", "doing", "able", "going", "being",
    "different", "important", "possible", "available",
    "chose", "choses", "truc", "trucs",
}

_EXTRACTION_PROMPT = """Extract concepts and relations stated or requested in the incoming message.
Return ONLY valid JSON, no preamble, no markdown.

Incoming message: {user_input}
Assistant response (context only; never use it as evidence): {response_summary}

Return exactly this structure:
{{
  "concepts": [{{"name": "concept1", "evidence": "exact words from the incoming message"}}],
  "relations": [
    {{"from": "concept1", "to": "concept2", "type": "leads_to", "evidence": "exact words from the incoming message supporting this relation"}}
  ],
  "dominant_topic": "one of the concept names",
  "cognitive_load": 0.0
}}

Rules:
- Persist only concepts and relations grounded in the incoming message. Assistant wording is not evidence of an interlocutor's belief, fact, preference, or intent.
- concepts: 0-8 lowercase nouns or noun phrases, max 3 words each; every concept needs an exact evidence phrase from the incoming message
- relations: max 5, both endpoints must be concepts; evidence must directly support the relation in the incoming message
- Do not infer a relation from co-occurrence alone
- dominant_topic must be selected from concepts
- cognitive_load: float 0.0-1.0 (0=trivial, 1=very complex reasoning)
- NO extra keys, NO explanation"""

_RELATION_TYPES = {"leads_to", "related_to", "part_of", "causes", "contradicts", "enables"}


class SemanticExtractor:
    """
    Real-time concept extractor. Runs in a daemon thread so it never
    blocks the main response loop.
    """

    def __init__(self, semantic_memory: SemanticMemory, llm_fn=None, organism=None):
        self._memory = semantic_memory
        self._llm    = llm_fn        # optional: fn(prompt: str) -> str
        self._organism = organism
        self._lock   = threading.Lock()
        self._queue: queue.Queue = queue.Queue()
        self._worker_running = False

    def set_llm(self, llm_fn):
        """Set or update the LLM function (called once ai_system is ready)."""
        self._llm = llm_fn

    def extract_async(
        self,
        user_input:    str,
        response:      str,
        meta_scores:   Optional[Dict] = None,
        workspace=None,
        observation_role: str = "user_topic",
    ):
        """Queue a completed turn for semantic extraction.

        ``meta_scores`` remains accepted for caller compatibility, but is not
        persisted as capability evidence: current MetaCognition scores are
        heuristic proxies without independent outcome validation.
        """
        role = str(observation_role or "user_topic")
        if role not in {"user_topic", "peer_topic"}:
            role = "user_topic"
        item = (user_input, response, None, workspace, role)
        with self._lock:
            self._queue.put_nowait(item)
            if self._worker_running:
                return
            self._worker_running = True
        threading.Thread(
            target=self._drain_queue,
            daemon=True,
            name="SemanticExtractor",
        ).start()

    def _drain_queue(self) -> None:
        while True:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                with self._lock:
                    if self._queue.empty():
                        self._worker_running = False
                        return
                continue
            try:
                self._extract(*item)
            finally:
                self._queue.task_done()

    def _extract(self, user_input, response, meta_scores, workspace,
                 observation_role="user_topic"):
        try:
            t0 = time.time()
            concepts, relations, topic, cog_load = self._parse(user_input, response)

            # Write to semantic memory
            for c in concepts:
                self._memory.upsert_concept(c, strength_boost=0.04)
            # Keep interlocutor topics distinct from assistant prose and from
            # other interlocutors. FLUX may contribute shared concepts, but its
            # utterances must never qualify as human-originated goal evidence.
            is_peer = observation_role == "peer_topic"
            for c in dict.fromkeys(self._keyword_extract(user_input or "")):
                self._memory.record_observation(
                    c,
                    source="peer_dialogue" if is_peer else "conversation",
                    role=observation_role,
                    confidence=0.8,
                )
            for rel in relations:
                self._memory.upsert_relation(
                    rel["from"], rel["to"], rel["type"], weight_boost=0.05)

            # Broadcast dominant topic into Global Workspace
            if workspace and topic:
                try:
                    workspace.broadcast(
                        source   = "peer_semantic_extractor" if is_peer else "semantic_extractor",
                        content  = (
                            f"peer hypothesis: {topic} — extracted concepts: {', '.join(concepts[:3])}"
                            if is_peer else
                            f"semantic: {topic} — concepts: {', '.join(concepts[:3])}"
                        ),
                        priority = 0.4,
                    )
                except Exception:
                    pass

            elapsed = time.time() - t0
            logger.info(
                f"[SemanticExtractor] {len(concepts)} concepts, "
                f"{len(relations)} relations — topic: '{topic}' in {elapsed*1000:.0f}ms"
            )
        except Exception as e:
            logger.debug(f"[SemanticExtractor] Error: {e}")

    def _parse(self, user_input: str, response: str
               ) -> Tuple[List[str], List[Dict], str, float]:
        """Try LLM extraction, fall back to keyword extraction."""

        # Durable graph evidence comes only from the authored input. If
        # assistant wording were folded into this graph, later recall and
        # associative thought could recycle Lumina's own claims as evidence.
        user_concepts = self._keyword_extract(user_input)
        kw_concepts = list(user_concepts)
        kw_relations = self._keyword_relations(kw_concepts)

        if not self._llm:
            return kw_concepts, kw_relations, kw_concepts[0] if kw_concepts else "", 0.3

        try:
            prompt = _EXTRACTION_PROMPT.format(
                user_input=user_input[:1200],
                response_summary=response[:1600],
            )
            raw = self._llm(prompt)
            # Strip markdown fences
            raw = re.sub(r"```(?:json)?|```", "", raw).strip()
            data = json.loads(raw)

            input_source = " ".join((user_input or "").casefold().split())
            input_llm_concepts = self._ground_concepts(data.get("concepts", []), input_source)
            concepts = list(dict.fromkeys(user_concepts + input_llm_concepts + kw_concepts))[:8]
            relations = self._ground_relations(data.get("relations", []), concepts, input_source)
            topic_value = data.get("dominant_topic", "")
            topic = self._normalize_concept(topic_value)
            if topic not in user_concepts and topic not in input_llm_concepts:
                topic = (input_llm_concepts[0] if input_llm_concepts else
                         user_concepts[0] if user_concepts else "")
            raw_load = float(data.get("cognitive_load", 0.3))
            cog_load = max(0.0, min(1.0, raw_load)) if math.isfinite(raw_load) else 0.3

            # If the model's extraction cannot be grounded in the user input,
            # use the conservative local concepts and do not invent relations.
            if not concepts:
                return kw_concepts, [], kw_concepts[0] if kw_concepts else "", 0.3
            return concepts, relations, topic, cog_load

        except Exception as e:
            logger.debug(f"[SemanticExtractor] LLM parse failed ({e}), using keywords")
            return kw_concepts, kw_relations, kw_concepts[0] if kw_concepts else "", 0.3

    def _keyword_extract(self, text: str) -> List[str]:
        """Lightweight keyword extraction — nouns and noun phrases only."""
        # Require min 4 chars, letters only (no hyphens catching fragments)
        words = re.findall(r"[^\W\d_][^\W\d_'-]{2,}", text.casefold(), flags=re.UNICODE)
        freq: Dict[str, int] = {}
        for w in words:
            if w not in _STOP and w not in _GENERIC_CONCEPTS and len(w) >= _MIN_CONCEPT_LEN:
                freq[w] = freq.get(w, 0) + 1
        # Only keep words appearing ≥ 1 time, sorted by frequency
        sorted_w = [w for w, _ in sorted(freq.items(), key=lambda k: -k[1])]
        # Extract 2-word noun phrases (both words must pass filters)
        phrases = re.findall(
            r"([^\W\d_][^\W\d_'-]{2,})\s+([^\W\d_][^\W\d_'-]{2,})",
            text.casefold(), flags=re.UNICODE,
        )
        phrase_list = [
            f"{a} {b}" for a, b in phrases
            if a not in _STOP and b not in _STOP
            and a not in _GENERIC_CONCEPTS and b not in _GENERIC_CONCEPTS
        ][:3]
        return (sorted_w[:5] + phrase_list)[:8]

    def _keyword_relations(self, concepts: List[str]) -> List[Dict]:
        """Co-occurrence alone is not evidence of a semantic relation."""
        return []

    @staticmethod
    def _normalize_concept(value) -> str:
        if not isinstance(value, str):
            return ""
        words = re.findall(r"[^\W\d_][\w'-]*", value.casefold(), flags=re.UNICODE)
        return " ".join(words[:3]).strip()[:60]

    def _ground_concepts(self, values, source: str) -> List[str]:
        if not isinstance(values, list):
            return []
        grounded = []
        for item in values[:12]:
            if isinstance(item, dict):
                name = self._normalize_concept(item.get("name"))
                evidence = str(item.get("evidence", "")).casefold().strip()
            else:
                # Older local model outputs are accepted only when the concept
                # itself occurs in the turn; they cannot add synonym guesses.
                name = self._normalize_concept(item)
                evidence = name
            if (not name or len(name) < _MIN_CONCEPT_LEN or name in _STOP
                    or name in _GENERIC_CONCEPTS or not evidence):
                continue
            evidence_terms = set(re.findall(r"[^\W\d_][\w'-]{2,}", evidence, flags=re.UNICODE))
            name_terms = set(re.findall(r"[^\W\d_][\w'-]{2,}", name, flags=re.UNICODE))
            if not name_terms or not evidence_terms or not name_terms.issubset(evidence_terms):
                continue
            normalized_source = " ".join(source.split())
            normalized_evidence = " ".join(evidence.split())
            if normalized_evidence not in normalized_source:
                continue
            if name not in grounded:
                grounded.append(name)
            if len(grounded) == 8:
                break
        return grounded

    def _ground_relations(self, values, concepts: List[str], source: str) -> List[Dict]:
        if not isinstance(values, list):
            return []
        concept_set = set(concepts)
        normalized_source = " ".join(source.split())
        relations = []
        seen = set()
        for item in values[:10]:
            if not isinstance(item, dict):
                continue
            left = self._normalize_concept(item.get("from"))
            right = self._normalize_concept(item.get("to"))
            rel_type = str(item.get("type", "")).casefold().strip()
            evidence = str(item.get("evidence", "")).casefold().strip()
            normalized_evidence = " ".join(evidence.split())
            evidence_terms = set(re.findall(r"[^\W\d_][\w'-]{2,}", evidence, flags=re.UNICODE))
            if (left not in concept_set or right not in concept_set or left == right
                    or rel_type not in _RELATION_TYPES or len(evidence_terms) < 2
                    or normalized_evidence not in normalized_source):
                continue
            key = (left, right, rel_type)
            if key not in seen:
                relations.append({"from": left, "to": right, "type": rel_type})
                seen.add(key)
            if len(relations) == 5:
                break
        return relations
