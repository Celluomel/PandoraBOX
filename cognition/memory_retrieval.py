"""Deterministic lexical retrieval used when vector embeddings are unavailable."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import List, Sequence, Tuple

_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
_VISUAL_INTENT_TERMS = frozenset((
    "photo", "picture", "image", "see", "saw", "seeing", "room", "face",
    "camera", "vision", "visual", "see", "voir", "vois", "voit", "vu",
    "regarde", "regarder", "visage", "image", "photo", "caméra",
))
_STOPWORDS = frozenset(("""
a about after again all also am an and any are as at be been before but by can could did do does doing down during each
few for from further had has have having he her here hers herself him himself his how i if in into is it its itself
just me more most my myself no nor not of off on once only or other our ours ourselves out over own same she should so
some such than that the their theirs them themselves then there these they this those through to too under until up
very was we were what when where which while who whom why will with would you your yours yourself yourselves
a au aux avec ce ces dans de des du elle elles en et eux il ils je la le les leur lui ma mais me meme mes moi mon
ne nos notre nous on ou par pas pour qu que quel quelle qui sa sans se ses son sur ta te tes toi ton tu un une vos
votre vous y etre avoir faire suis sont doit dois
""").split())


_HISTORICAL_REQUEST_PATTERNS = (
    re.compile(
        r"\bquel(?:le)?s?\s+(?P<topic>[^?!.]{1,100}?)\s+"
        r"(?:ai|avais|aurais)-je\s+"
        r"(?:demand[ée]s?|dit|formul[ée]s?|pos[ée]s?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bquel(?:le)?s?\s+(?P<topic>[^?!.]{1,100}?)\s+"
        r"est-ce\s+que\s+j['’](?:ai|avais|aurais)\s+"
        r"(?:demand[ée]s?|dit|formul[ée]s?|pos[ée]s?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwhat\s+(?P<topic>[^?!.]{1,100}?)\s+"
        r"(?:did|have|had)\s+i\s+"
        r"(?:ask(?:ed)?|request(?:ed)?|say|said|tell\s+you|told\s+you)\b",
        re.IGNORECASE,
    ),
)


def _historical_request_match(text: str):
    value = str(text or "")
    for pattern in _HISTORICAL_REQUEST_PATTERNS:
        match = pattern.search(value)
        if match:
            return match
    return None


def faiss_l2_relevance(distance: float) -> float:
    """Map squared-L2 distance between unit vectors to non-negative cosine relevance.

    SentenceTransformer's configured all-MiniLM-L6-v2 pipeline includes a
    Normalize module, so FAISS IndexFlatL2 returns d² = 2 - 2*cosine.
    The old 1/(1+d²) transform was monotonic but not a similarity measure and
    gave unrelated candidates misleadingly positive scores.
    """
    try:
        squared_distance = float(distance)
    except (TypeError, ValueError, OverflowError):
        return 0.0
    if not math.isfinite(squared_distance):
        return 0.0
    return max(0.0, min(1.0, 1.0 - max(0.0, squared_distance) / 2.0))


def extract_explicit_recall_topic(text: str) -> str:
    """Remove the request framing from a memory question before retrieval.

    Keep the topic clause so the retriever searches for what the user wants
    remembered, rather than the current instruction about remembering it.
    """
    value = str(text or "").strip()
    # Historical-request questions are recall requests even without the
    # literal verbs "remember" or "recall". Keep only their subject clause.
    asked_match = _historical_request_match(value)
    if asked_match:
        leading_context = value[:asked_match.start()]
        leading_context = re.sub(
            r"^\s*(?:pour|for)\s+|[,;:]\s*$", "", leading_context,
            flags=re.IGNORECASE,
        )
        topic = asked_match.group("topic").strip(" \t\r\n,;:«»\"'")
        extracted = " ".join(part for part in (leading_context, topic) if part)
        return extracted[:180].strip() or value
    prefixes = (
        r"^what\s+do\s+you\s+remember\s+about\s+",
        r"^what\s+have\s+we\s+discussed\s+about\s+",
        r"^(?:do\s+you\s+remember|can\s+you\s+recall)\s+",
        r"^tu\s+te\s+rappelles(?:\s+de)?\s+",
        r"^tu\s+te\s+souviens(?:-tu)?(?:\s+de)?\s+",
        r"^(?:rappelle(?:-moi)?|souviens-toi|te\s+souviens-tu)\s+",
        r"^(?:remember|recall)\s+",
    )
    for pattern in prefixes:
        match = re.match(pattern, value, flags=re.IGNORECASE)
        if match:
            value = value[match.end():]
            break
    value = re.sub(r"^(?:(?:uniquement|seulement|just|only)\s+)*", "", value, flags=re.IGNORECASE)
    value = re.sub(
        r"^(?:what\s+(?:we\s+)?(?:discussed|talked\s+about|said)|"
        r"ce\s+qu['’]?(?:on|nous)\s+(?:a|avons)\s+"
        r"(?:discuté|parlé|dit))\s+",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"^(?:(?:on|nous)\s+(?:a|avons)\s+(?:discuté|parlé|dit)|"
        r"we\s+(?:have\s+)?(?:discussed|talked\s+about|said))\s+",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"^(?:de|du|des|d['’]|about)\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^(?:ce\s+que|what\s+(?:i|we)\s+(?:asked|said|told\s+you))\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^(?:je\s+t['’]ai\s+(?:demandé|dit)|i\s+(?:asked|told\s+you))\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^(?:à\s+propos\s+(?:de|du|des|d['’])|au\s+sujet\s+(?:de|du|des|d['’])|concernant|sur|about|regarding)\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^(?:uniquement|seulement)\s+", "", value, flags=re.IGNORECASE)
    return value.strip(" \t\r\n?.,:;\"'«»") or str(text or "").strip()


def _explicit_recall_focus(text: str) -> str:
    """Return the historical subject plus short context identifying its source."""
    # Include the short leading subject (e.g. "for the harness audit") as
    # well as the interrogative topic. Retrieval uses this context too, so
    # filtering only on the final phrase could discard the source statement.
    return extract_explicit_recall_topic(str(text or "").strip())


def _memory_user_text(memory: dict) -> str:
    """Extract user-authored text from an episodic record when available."""
    text = str(memory.get("text", ""))
    match = re.search(
        r"\buser\s*:\s*(.*?)(?=\s*[|\n]\s*(?:lumina|assistant)\s*:|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1).strip() if match else text


def is_explicit_memory_recall_query(text: str) -> bool:
    """Recognize explicit requests to retrieve earlier conversational facts."""
    value = " ".join(str(text or "").casefold().split())
    if any(term in value for term in (
        "rappelle", "souvien", "remember", "recall", "tu te rappelles",
        "te souviens", "talked about", "on a parlé", "we discussed",
        "on a dit", "tu sais ce que", "t'en souviens",
    )):
        return True
    return _historical_request_match(value) is not None


def filter_recall_query_records(
    memories: Sequence[dict], query: str | None = None,
) -> List[dict]:
    """Remove recall self-matches and sources unrelated to the requested focus.

    Historical recall questions are not evidence for the answer to a later
    recall question. Episodic records are evaluated using their user-authored
    segment, never the assistant's often fluent but potentially incorrect
    reply. When a query is supplied, unrelated source utterances are excluded
    before prompt injection; an empty result is preferable to a plausible
    answer assembled from a neighboring conversation topic.
    """
    focus = set(tokenize(_explicit_recall_focus(query))) if query else set()
    filtered = []
    for memory in memories:
        kind = str(memory.get("memory_type", "")).casefold()
        source_text = _memory_user_text(memory)
        if kind in {"user_message", "episodic"} and is_explicit_memory_recall_query(source_text):
            continue
        # A neighboring status question can share the broad subject words
        # (e.g. "audit" and "harness") without stating the historical result
        # being requested. For explicit historical recall, interrogative user
        # turns are prompts, not source evidence; prefer declarative requests
        # or statements that can actually substantiate the answer.
        if kind in {"user_message", "episodic"} and re.search(r"[?？]", source_text):
            continue
        if focus and kind in {"user_message", "episodic"}:
            source_terms = set(tokenize(source_text))
            if not (focus & source_terms):
                continue
        filtered.append(memory)
    return filtered


def tokenize(text: str) -> List[str]:
    """Normalize accents and remove common English/French function words."""
    folded = unicodedata.normalize("NFKD", str(text or "").casefold())
    plain = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return [term for term in _TOKEN_RE.findall(plain) if len(term) > 1 and term not in _STOPWORDS]


def rank_documents(query: str, documents: Sequence[str], limit: int = 5) -> List[Tuple[int, float]]:
    """Return (document index, normalized BM25 relevance), best first."""
    query_terms = Counter(tokenize(query))
    if not query_terms or not documents or limit <= 0:
        return []

    tokenized = [tokenize(document) for document in documents]
    document_frequency: Counter[str] = Counter()
    for terms in tokenized:
        document_frequency.update(set(terms))
    average_length = sum(map(len, tokenized)) / max(1, len(tokenized))
    if average_length <= 0:
        return []

    k1, b = 1.5, 0.75
    scored = []
    for index, terms in enumerate(tokenized):
        frequencies = Counter(terms)
        length = len(terms)
        score = 0.0
        for term, query_frequency in query_terms.items():
            frequency = frequencies.get(term, 0)
            if not frequency:
                continue
            df = document_frequency[term]
            inverse_frequency = math.log(1.0 + (len(tokenized) - df + 0.5) / (df + 0.5))
            saturation = frequency * (k1 + 1.0) / (
                frequency + k1 * (1.0 - b + b * length / average_length)
            )
            score += inverse_frequency * saturation * min(2, query_frequency)
        if score > 0:
            scored.append((index, score / (score + 1.0)))
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored[:limit]


def merge_user_authored_memories(
    primary: Sequence[dict], user_authored: Sequence[dict], limit: int
) -> List[dict]:
    """Keep one relevant source utterance in a bounded cross-source recall set.

    The primary retriever ranks all memory types together. Preserve the best
    separately retrieved user-authored record ahead of that pool so historical
    assistant wording cannot crowd out the source statement it may have
    answered incorrectly.
    """
    if limit <= 0:
        return []
    merged: List[dict] = []
    seen = set()

    def add(memory: dict) -> None:
        key = memory.get("id") or memory.get("faiss_id") or memory.get("text")
        if key in seen:
            return
        seen.add(key)
        merged.append(memory)

    for memory in user_authored:
        if memory.get("memory_type") == "user_message":
            add(memory)
            break
    for memory in primary:
        add(memory)
        if len(merged) >= limit:
            return merged
    for memory in user_authored:
        add(memory)
        if len(merged) >= limit:
            break
    return merged[:limit]


def filter_memories_by_modality(
    memories: Sequence[dict], *, include_visual: bool
) -> List[dict]:
    """Exclude visual records from text-only recall unless the query asks for vision."""
    if include_visual:
        return list(memories)
    return [
        memory for memory in memories
        if str(memory.get("memory_tier", "")).casefold() != "visual"
        and str(memory.get("memory_type", "")).casefold() != "visual_perception"
    ]


def is_visual_memory_query(query: str) -> bool:
    """Return whether the current utterance explicitly requests visual context.

    Learned vocabulary may help rank memories, but must not override the
    current utterance's modality and inject visual records into unrelated text
    recall. This is deliberately a routing signal, not a semantic classifier.
    """
    tokens = {token.casefold() for token in _TOKEN_RE.findall(str(query or ""))}
    return bool(tokens & _VISUAL_INTENT_TERMS)
