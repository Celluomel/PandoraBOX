"""
semantic_extractor.py — Real-time Semantic Extraction (Global Workspace hook)
==============================================================================

Called after every interaction from cognitive_organism.py post-response hook.
Uses a FAST, lightweight prompt — no full LLM conversation, just a structured
JSON extraction of concepts + relations from the exchange.

Design constraints
------------------
  - Must complete in < 1s  (non-blocking, runs in background thread)
  - LLM call is optional; lexical fallback is unclassified and not persisted
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
  "turn_kind": "topic",
  "concepts": [{{"name": "concept1", "evidence": "exact words from the incoming message"}}],
  "relations": [
    {{"from": "concept1", "to": "concept2", "type": "leads_to", "evidence": "exact words from the incoming message supporting this relation"}}
  ],
  "dominant_topic": "one of the concept names",
  "cognitive_load": 0.0
}}

Rules:
- Classify the incoming message's primary conversational act as exactly one of: topic, retrieval, social, instruction, feedback, decision, other. Use "topic" for a substantive subject the user asks to explain, investigate, or discuss. Use "retrieval" when they ask what was said, decided, or observed earlier. Use "social" for greetings, thanks, and small talk. Use "instruction" for operational commands to the assistant/system. Use "feedback" for evaluation of a prior response. Use "decision" for a request to compare feasible actions to achieve a concrete outcome. Use "other" when none fits. Classify the user's intent, not the assistant response.
- Persist only concepts and relations grounded in the incoming message. Assistant wording is not evidence of an interlocutor's belief, fact, preference, or intent.
- concepts: 0-8 lowercase nouns or noun phrases, max 3 words each; every concept needs an exact evidence phrase from the incoming message
- relations: max 5, both endpoints must be concepts; evidence must directly support the relation in the incoming message
- Do not infer a relation from co-occurrence alone
- dominant_topic must be selected from concepts
- cognitive_load: float 0.0-1.0 (0=trivial, 1=very complex reasoning)
- NO extra keys, NO explanation"""

_RELATION_TYPES = {"leads_to", "related_to", "part_of", "causes", "contradicts", "enables"}
_TURN_KINDS = {"topic", "retrieval", "social", "instruction", "feedback", "decision", "other"}
_MAX_DEFERRED_RETRIES = 30
_DEFERRED_RETRY_DELAY_SECONDS = 1.0


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
        turn_id: str = "",
        completion_callback=None,
        turn_kind_hint: str = "",
    ):
        """Queue a completed turn for semantic extraction.

        ``meta_scores`` remains accepted for caller compatibility, but is not
        persisted as capability evidence: current MetaCognition scores are
        heuristic proxies without independent outcome validation.
        """
        role = str(observation_role or "user_topic")
        if role not in {"user_topic", "peer_topic"}:
            role = "user_topic"
        item = (
            user_input, response, None, workspace, role,
            str(turn_id or ""), completion_callback,
            str(turn_kind_hint or "").strip().casefold(), 0,
        )
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
                receipt = self._extract(*item[:8])
                retry_count = int(item[8]) if len(item) > 8 else 0
                if receipt.get("status") == "deferred":
                    if retry_count < _MAX_DEFERRED_RETRIES:
                        self._schedule_retry((*item[:8], retry_count + 1))
                        continue
                    receipt.update({
                        "status": "failed",
                        "learning_status": "deferred_retry_exhausted",
                        "retry_exhausted": True,
                    })
                completion_callback = item[6] if len(item) > 6 else None
                if callable(completion_callback):
                    try:
                        completion_callback(receipt)
                    except Exception as callback_error:
                        logger.debug(
                            "[SemanticExtractor] Completion receipt callback failed: %s",
                            callback_error,
                        )
            finally:
                self._queue.task_done()

    def _schedule_retry(self, item) -> None:
        """Requeue a provider-deferred turn without occupying the sole worker."""
        def _enqueue_retry():
            should_start_worker = False
            with self._lock:
                self._queue.put_nowait(item)
                if not self._worker_running:
                    self._worker_running = True
                    should_start_worker = True
            if should_start_worker:
                threading.Thread(
                    target=self._drain_queue,
                    daemon=True,
                    name="SemanticExtractor",
                ).start()

        retry_timer = threading.Timer(_DEFERRED_RETRY_DELAY_SECONDS, _enqueue_retry)
        retry_timer.daemon = True
        retry_timer.start()

    def _extract(self, user_input, response, meta_scores, workspace,
                 observation_role="user_topic", turn_id="", completion_callback=None,
                 turn_kind_hint=""):
        receipt = {
            "type": "semantic_extraction_receipt",
            "status": "failed",
            "turn_id": str(turn_id or "") or None,
            "concepts_parsed": 0,
            "concept_upsert_calls_returned": 0,
            "concepts_persisted": 0,
            "observation_calls_returned": 0,
            "observations_persisted": 0,
            "relation_upsert_calls_returned": 0,
            "relations_persisted": 0,
            "dominant_topic_selected": False,
            "persistence_status": "unverified",
            "cag_status": "not_available",
            "workspace_status": "not_requested",
        }
        try:
            t0 = time.time()
            # Some upstream stages already know the conversational act from
            # the route that produced the answer (e.g. a deterministic affect
            # report or a source-backed memory recall). Preserve that evidence
            # instead of spending another LLM call to rediscover it.
            trusted_hint = str(turn_kind_hint or "").strip().casefold()
            if trusted_hint in {"retrieval", "social", "instruction", "feedback", "other"}:
                parsed = ([], [], "", 0.3, trusted_hint)
                receipt["classification_source"] = "upstream_turn_contract"
            else:
                # The queue worker runs on a fresh thread, so ContextVars from
                # the response turn do not propagate automatically. Restore its
                # opaque turn ID so the provider event has a causal parent.
                from core.turn_execution_context import current_turn_id, set_current_turn_id
                turn_context_token = set_current_turn_id(turn_id)
                try:
                    parsed = self._parse(user_input, response)
                finally:
                    current_turn_id.reset(turn_context_token)
                if trusted_hint == "decision" and len(parsed) >= 5:
                    # The foreground decision analyzer already classified the
                    # conversational act. Keep semantic concept extraction in
                    # this post-response worker, but don't spend another model
                    # call rediscovering whether the user asked for a decision.
                    parsed = (*parsed[:4], "decision")
                    receipt["classification_source"] = "upstream_turn_contract_plus_semantic_extraction"
                else:
                    receipt["classification_source"] = "semantic_llm"
            if len(parsed) >= 5:
                concepts, relations, topic, cog_load, turn_kind = parsed[:5]
            else:
                # Preserve compatibility for integrations that provide the
                # pre-turn-kind four-value parser contract. The production
                # parser always returns an explicit classification.
                concepts, relations, topic, cog_load = parsed
                turn_kind = "topic"
            if turn_kind not in _TURN_KINDS:
                turn_kind = "unclassified"
            receipt["turn_kind"] = turn_kind
            receipt["concepts_parsed"] = len(concepts)
            receipt["dominant_topic_selected"] = bool(topic and topic in concepts)

            if turn_kind not in {"topic", "decision"}:
                receipt.update({
                    "status": "completed",
                    "learning_status": "skipped_non_topic_turn",
                    "persistence_status": "not_needed",
                    "cag_status": "skipped_non_topic_turn",
                    "workspace_status": "not_requested",
                    "curiosity_status": "skipped_non_topic_turn",
                    "curiosity_topic_selected": False,
                })
                receipt["duration_ms"] = round((time.time() - t0) * 1000, 3)
                logger.info(
                    "[SemanticExtractor] skipped durable learning for %s turn %s",
                    turn_kind, str(turn_id or "")[:48],
                )
                return receipt

            receipt["learning_status"] = (
                "accepted_decision_turn" if turn_kind == "decision"
                else "accepted_topic_turn"
            )

            # Curiosity receives only the dominant concept selected from, and
            # grounded in, this human-authored turn. The old organism cycle
            # guessed a topic from the first long tokens before semantic
            # extraction, which promoted prompt fragments into goals.
            if observation_role == "user_topic" and topic and topic in concepts:
                curiosity = getattr(self._organism, "curiosity", None)
                if curiosity is None:
                    receipt["curiosity_status"] = "unavailable"
                    receipt["curiosity_topic_selected"] = True
                else:
                    try:
                        curiosity_level = curiosity.stimulate(
                            topic, amount=0.15, source="user_semantic",
                        )
                        receipt["curiosity_status"] = "stimulated"
                        receipt["curiosity_topic_selected"] = True
                        receipt["curiosity_level_after"] = curiosity_level
                    except Exception as curiosity_error:
                        receipt["curiosity_status"] = "failed"
                        receipt["curiosity_topic_selected"] = True
                        receipt["curiosity_error_type"] = type(curiosity_error).__name__
            elif observation_role == "peer_topic":
                receipt["curiosity_status"] = "skipped_peer_source"
                receipt["curiosity_topic_selected"] = bool(topic and topic in concepts)
            else:
                receipt["curiosity_status"] = "no_grounded_dominant_topic"
                receipt["curiosity_topic_selected"] = False

            # CAG receives the concepts this extractor already grounded in the
            # incoming message. This avoids its former independent heuristic
            # pass over the concatenated user + assistant text.
            try:
                from core.state import state as runtime_state
                active_context = getattr(runtime_state, "acc", None)
                update_topics = getattr(active_context, "update_semantic_topics", None)
                if callable(update_topics):
                    update_topics(
                        concepts,
                        topic=topic,
                        evidence_text=user_input or "",
                        source_role=observation_role,
                    )
                    receipt["cag_status"] = "completed"
            except Exception as context_error:
                receipt["cag_status"] = "failed"
                receipt["cag_error_type"] = type(context_error).__name__
                logger.debug("CAG semantic-topic update unavailable: %s", context_error)

            # Write to semantic memory
            for c in concepts:
                concept_id = self._memory.upsert_concept(c, strength_boost=0.04)
                receipt["concept_upsert_calls_returned"] += 1
                if isinstance(concept_id, int) and concept_id >= 0:
                    receipt["concepts_persisted"] += 1
            # Keep interlocutor topics distinct from assistant prose and from
            # other interlocutors. FLUX may contribute shared concepts, but its
            # utterances must never qualify as human-originated goal evidence.
            is_peer = observation_role == "peer_topic"
            # Observations must describe the concepts accepted by this turn's
            # parser. Re-running the lexical fallback here silently re-added
            # surface words even when the LLM had already selected a smaller,
            # grounded semantic set.
            for c in dict.fromkeys(concepts):
                observation_persisted = self._memory.record_observation(
                    c,
                    source="peer_dialogue" if is_peer else "conversation",
                    role=observation_role,
                    confidence=0.8,
                    turn_id=turn_id,
                )
                receipt["observation_calls_returned"] += 1
                if observation_persisted is True:
                    receipt["observations_persisted"] += 1
            for rel in relations:
                relation_persisted = self._memory.upsert_relation(
                    rel["from"], rel["to"], rel["type"], weight_boost=0.05)
                receipt["relation_upsert_calls_returned"] += 1
                if relation_persisted is True:
                    receipt["relations_persisted"] += 1

            attempted_writes = sum(receipt[key] for key in (
                "concept_upsert_calls_returned",
                "observation_calls_returned",
                "relation_upsert_calls_returned",
            ))
            confirmed_writes = sum(receipt[key] for key in (
                "concepts_persisted", "observations_persisted", "relations_persisted",
            ))
            receipt["persistence_status"] = (
                "not_needed" if attempted_writes == 0 else
                "confirmed" if confirmed_writes == attempted_writes else
                "partial" if confirmed_writes else
                "unverified"
            )

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
                    receipt["workspace_status"] = "completed"
                except Exception as workspace_error:
                    receipt["workspace_status"] = "failed"
                    receipt["workspace_error_type"] = type(workspace_error).__name__

            receipt["status"] = (
                "partial" if "failed" in {
                    receipt["cag_status"], receipt["workspace_status"],
                } else "completed"
            )

            elapsed = time.time() - t0
            receipt["duration_ms"] = round(elapsed * 1000, 3)
            logger.info(
                f"[SemanticExtractor] {len(concepts)} concepts, "
                f"{len(relations)} relations — topic: '{topic}' in {elapsed*1000:.0f}ms"
            )
        except Exception as e:
            receipt["error_type"] = type(e).__name__
            if getattr(e, "semantic_learning_deferred", False):
                receipt.update({
                    "status": "deferred",
                    "learning_status": "deferred_provider_busy",
                })
            logger.debug(f"[SemanticExtractor] Error: {e}")
        return receipt

    def _parse(self, user_input: str, response: str
               ) -> Tuple[List[str], List[Dict], str, float, str]:
        """Try LLM extraction, fall back to keyword extraction."""

        # Durable graph evidence comes only from the authored input. If
        # assistant wording were folded into this graph, later recall and
        # associative thought could recycle Lumina's own claims as evidence.
        kw_concepts = list(self._keyword_extract(user_input))
        kw_relations = self._keyword_relations(kw_concepts)

        if not self._llm:
            # Lexical fallback can suggest concepts but cannot reliably select
            # a dominant semantic topic. Leave topic arbitration to a later
            # stage instead of promoting the first surface token.
            return kw_concepts, kw_relations, "", 0.3, "unclassified"

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
            # A valid model extraction is the semantic selection. Unioning it
            # with keyword candidates defeats that selection and lets prompt
            # wording (for example, an imperative verb) enter durable memory.
            concepts = input_llm_concepts[:8]
            relations = self._ground_relations(data.get("relations", []), concepts, input_source)
            topic_value = data.get("dominant_topic", "")
            topic = self._normalize_concept(topic_value)
            turn_kind = str(data.get("turn_kind") or "").strip().casefold()
            if turn_kind not in _TURN_KINDS:
                turn_kind = "unclassified"
            if turn_kind == "topic" and topic not in concepts and len(concepts) == 1:
                # A single grounded concept is an unambiguous dominant topic;
                # tolerate a formatting mismatch in the model's duplicate
                # dominant_topic field without promoting any new text.
                topic = concepts[0]
            elif topic not in concepts or turn_kind != "topic":
                topic = ""
            raw_load = float(data.get("cognitive_load", 0.3))
            cog_load = max(0.0, min(1.0, raw_load)) if math.isfinite(raw_load) else 0.3

            # A valid empty extraction means this message did not yield a
            # grounded topic. Do not turn lexical leftovers into a semantic
            # topic merely to force a workspace update.
            return concepts, relations, topic, cog_load, turn_kind

        except Exception as e:
            if getattr(e, "semantic_learning_deferred", False):
                raise
            logger.debug(f"[SemanticExtractor] LLM parse failed ({e}), using keywords")
            return kw_concepts, kw_relations, "", 0.3, "unclassified"

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
