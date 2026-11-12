"""Deterministic lexical retrieval used when vector embeddings are unavailable."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import List, Sequence, Tuple

_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
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
    prefixes = (
        r"^what\s+do\s+you\s+remember\s+about\s+",
        r"^what\s+have\s+we\s+discussed\s+about\s+",
        r"^(?:do\s+you\s+remember|can\s+you\s+recall)\s+",
        r"^(?:rappelle(?:-moi)?|souviens-toi|te\s+souviens-tu)\s+",
        r"^(?:remember|recall)\s+",
    )
    for pattern in prefixes:
        match = re.match(pattern, value, flags=re.IGNORECASE)
        if match:
            value = value[match.end():]
            break
    value = re.sub(r"^(?:(?:uniquement|seulement|just|only)\s+)*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^(?:ce\s+que|what\s+(?:i|we)\s+(?:asked|said|told\s+you))\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^(?:je\s+t['’]ai\s+(?:demandé|dit)|i\s+(?:asked|told\s+you))\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^(?:à\s+propos\s+de|au\s+sujet\s+de|concernant|sur|about|regarding)\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^(?:uniquement|seulement)\s+", "", value, flags=re.IGNORECASE)
    return value.strip(" \t\r\n?.,:;\"'«»") or str(text or "").strip()


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
