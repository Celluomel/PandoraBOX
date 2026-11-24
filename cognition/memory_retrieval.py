"""Deterministic lexical retrieval used when vector embeddings are unavailable."""

from __future__ import annotations

import hashlib
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

# Bare basenames need a recognizable extension. Arbitrary extensions remain
# valid when the user-authored source includes an explicit path; this prevents
# prose such as "answer.my" from being promoted to a recalled filename.
_EXACT_VALUE_RECALL_PATTERN = re.compile(
    r"\b(?:marker|code|identifier|token|value|number|checksum|hash|reference)\b",
    re.IGNORECASE,
)

_COMMON_FILENAME_EXTENSIONS = frozenset(("""
7z aac ai apk avi bat bin bmp bz2 c cc cfg cjs class cmd conf cpp cs css csv cxx dat db diff dll doc docx dwg
email epub exe flac gif go gz h hpp htm html ico ini ino ipynb jar java jpeg jpg js json jsonl jsx kt log lua m4a
markdown md mdx mjs mkv mov mp3 mp4 mpeg mpg msi msp npy npz odp ods odt onnx otf patch pdf pem pfx php pkl png ppt
pptx ps1 py pyc pyd pyw r rar rb rs sass scss sh so sqlite sql svg swf tar tex tif tiff toml ts tsx ttf txt wav webp
whl woff woff2 xls xlsx xml yaml yml zip zipx zst
""").split())


_HISTORICAL_REQUEST_PATTERNS = (
    # Resolve the general relative-clause form "remind me [subject] we
    # discussed" / "rappelle-moi [sujet] dont nous avons parlé". This is a
    # grammatical history reference, not a fixed vocabulary of memory topics.
    re.compile(
        r"\bremind\s+me\s+(?P<topic>[^?!.]{1,100}?)\s+"
        r"(?:that\s+)?(?:we|i)\s+(?:discussed|talked\s+about|decided\s+on)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\brappelle(?:-moi)?\s+(?P<topic>[^?!.]{1,100}?)\s+"
        r"(?:dont|duquel|de\s+laquelle|sur\s+lequel|sur\s+laquelle)\s+"
        r"(?:nous|on)\s+(?:avons|a)\s+"
        r"(?:parl[ée]|discut[ée]|décid[ée]|évoqu[ée])\b",
        re.IGNORECASE,
    ),
    # Historical instructions are often framed as "what did I give you?"
    # rather than "what did I ask you?". Route that grammatical form through
    # source-backed recall so the current prompt cannot be quoted as history.
    re.compile(
        r"\bwhat\s+(?:(?:exact(?:ly)?|specific)\s+)?"
        r"(?:instructions?|directions?|guidance|requests?|wording|message|details?)\s+"
        r"(?:did|have|had)\s+i\s+(?:give|send|provide|tell|state|write)\s+"
        r"(?:you\s+)?(?P<topic>[^?!.]{1,100})",
        re.IGNORECASE,
    ),
    # Historical sensor readings and other facts are commonly asked as
    # "what value did I give you?" rather than as an instruction/request.
    # Route these to source-backed recall too; otherwise ordinary semantic
    # retrieval may find nearby records but the exact-recall gate is skipped.
    re.compile(
        r"\b(?:what|which)\s+(?P<topic>[^?!.]{1,100}?)\s+"
        r"(?:did|have|had)\s+i\s+"
        r"(?:give|gave|tell|told|provide|provided|share|shared|mention|mentioned|"
        r"state|stated|send|sent|write|wrote|report|reported)\s+"
        r"(?:you\s+)?",
        re.IGNORECASE,
    ),
    # Also recognize copular questions such as "what was the test marker I
    # gave you?". Without this form, it fell through to ordinary FAISS recall
    # and a nearby but unrelated user message could be presented as fact.
    re.compile(
        r"\bwhat\s+was\s+(?P<topic>[^?!.]{1,100}?)\s+"
        r"(?:that\s+)?i\s+(?:gave|give|told|tell|provided|provide|shared|share|"
        r"mentioned|mention|reported|report|sent|send|wrote|write)\s+(?:you\b)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:do|did|can|could)\s+you\s+(?:remember|recall)\s+"
        r"(?P<topic>[^?!.]{1,100}?)\s+"
        r"(?:i\s+(?:gave|give|told|tell|provided|provide|shared|share|"
        r"mentioned|mention|reported|report)\s+you)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bquel(?:le)?s?\s+(?P<topic>[^?!.]{1,100}?)\s+"
        r"(?:ai|avais|aurais)-je\s+"
        r"(?:donn[ée](?:e|s|es)?|fourni(?:e|s|es)?|indiqu[ée](?:e|s|es)?|"
        r"transmis(?:e|es)?|communiqu[ée](?:e|s|es)?|partag[ée](?:e|s|es)?|"
        r"mentionn[ée](?:e|s|es)?|rapport[ée](?:e|s|es)?|dit(?:e|es)?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bquel(?:le)?s?\s+(?P<topic>[^?!.]{1,100}?)\s+"
        r"je\s+t['’]ai\s+"
        r"(?:donn[ée](?:e|s|es)?|fourni(?:e|s|es)?|indiqu[ée](?:e|s|es)?|"
        r"transmis(?:e|es)?|communiqu[ée](?:e|s|es)?|partag[ée](?:e|s|es)?|"
        r"mentionn[ée](?:e|s|es)?|rapport[ée](?:e|s|es)?|dit(?:e|es)?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bquel(?:le)?s?\s+(?P<topic>[^?!.]{1,100}?)\s+"
        r"t['’]ai-je\s+"
        r"(?:donn[ée](?:e|s|es)?|fourni(?:e|s|es)?|indiqu[ée](?:e|s|es)?|"
        r"transmis(?:e|es)?|communiqu[ée](?:e|s|es)?|partag[ée](?:e|s|es)?|"
        r"mentionn[ée](?:e|s|es)?|rapport[ée](?:e|s|es)?|dit(?:e|es)?)\b",
        re.IGNORECASE,
    ),
    # Questions whose grammatical subject is "I" followed by an object of
    # ask/request. Unlike the older "what outcome did I ask for" form, the
    # object follows the verb here: "what did I ask you to fix about X?".
    # Recognize the whole source topic so it is routed through explicit recall
    # and cannot fall back to a generic semantic-memory answer.
    re.compile(
        r"\bwhat\s+(?:exactly\s+)?(?:did|have|had)\s+i\s+"
        r"(?:ask(?:ed)?|request(?:ed)?)\s+(?:you\s+)?(?:to\s+)?"
        r"(?P<topic>[^?!.]{1,100})",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bqu['’]est-ce\s+que\s+je\s+t['’]ai\s+"
        r"(?:demand[ée]|dit|formul[ée])\s+(?:de\s+)?"
        r"(?P<topic>[^?!.]{1,100})",
        re.IGNORECASE,
    ),
    # Imperative recall phrasing is common in French chat. Capture only the
    # historical subject after its framing so retrieval does not search for,
    # or later quote, a previous "remind me" request as if it were the answer.
    re.compile(
        r"\b(?:rappelle(?:-moi)?|rappeler)\s+"
        r"(?:(?:uniquement|seulement)\s+)?ce\s+que\s+"
        r"je\s+t['’]ai\s+(?:demand[ée](?:e|s|es)?|dit(?:e|es)?|"
        r"formul[ée](?:e|es)?)\s+"
        r"(?:concernant|sur|au\s+sujet\s+de|à\s+propos\s+de)\s+"
        r"(?P<topic>[^?!.]{1,100})",
        re.IGNORECASE,
    ),
    # When the user supplies a short description after a colon, use that
    # description as the retrieval focus while still excluding this current
    # recall prompt from the candidate pool.
    re.compile(
        r"\b(?:rappelle(?:-moi)?|rappeler)\s+"
        r"(?:(?:uniquement|seulement)\s+)?(?:la|le|les)\s+"
        r"(?:r[eè]gle|consigne|demande|instruction|formulation)\b"
        r".{0,100}?\b(?:donn[ée]e?|formul[ée]e?|demand[ée]e?)\s*"
        r"(?:[:;—-]\s*|(?:concernant|sur|au\s+sujet\s+de)\s+)"
        r"(?P<topic>[^?!.]{1,100})",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bquel(?:le)?s?\s+(?P<topic>[^?!.]{1,100}?)\s+"
        r"(?:ai|avais|aurais)-je\s+"
        r"(?:explicitement\s+)?(?:demand[ée](?:e|s|es)?|dit(?:e|es)?|"
        r"formul[ée](?:e|s|es)?|pos[ée](?:e|s|es)?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bquel(?:le)?s?\s+(?P<topic>[^?!.]{1,100}?)\s+"
        r"est-ce\s+que\s+j['’](?:ai|avais|aurais)\s+"
        r"(?:demand[ée](?:e|s|es)?|dit(?:e|es)?|"
        r"formul[ée](?:e|s|es)?|pos[ée](?:e|s|es)?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:what|which)\s+(?P<topic>[^?!.]{1,100}?)\s+"
        r"(?:did|have|had)\s+i\s+"
        r"(?:ask(?:ed)?|request(?:ed)?|say|said|tell\s+you|told\s+you)\b",
        re.IGNORECASE,
    ),
)

_MEMORY_STORE_INSTRUCTION_PATTERNS = (
    re.compile(
        r"\bremember\s+(?:that|this|the|a|an|my|our)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:keep|store)\s+(?:this|that|the|a|an|my|our)\b.{0,40}\b(?:memory|mind|remember)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:mémorise|memorize|enregistre)\b", re.IGNORECASE),
    re.compile(r"\bgarde\s+(?:cela|ça|ceci)\s+en\s+mémoire\b", re.IGNORECASE),
    re.compile(r"\bsouviens-toi\s+que\b", re.IGNORECASE),
)

_SOURCE_ONLY_RECALL_PATTERN = re.compile(
    r"\b(?:rappelle(?:-moi)?|rappeler)\s+"
    r"(?:uniquement|seulement)\s+(?:"
    r"ce\s+que\s+je\s+t['’]ai\s+(?:demand[ée](?:e|s|es)?|dit(?:e|es)?|formul[ée](?:e|es)?)\b|"
    r"(?:la|le|les)\s+(?:r[eè]gle|consigne|demande|instruction|formulation)\b"
    r".{0,100}?\b(?:donn[ée]e?|formul[ée]e?|demand[ée]e?)\s*"
    r"(?:[:;—-]|concernant|sur|au\s+sujet\s+de))",
    re.IGNORECASE,
)

_DIRECT_RECALL_PATTERNS = (
    re.compile(r"\b(?:do|did|can|could|will|would)\s+you\s+(?:remember|recall)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:do|did|have|has|can)\s+you\s+(?:remember|recall)\b", re.IGNORECASE),
    re.compile(r"\b(?:tu\s+te\s+rappelles|tu\s+te\s+souviens)\b", re.IGNORECASE),
    # Imperative requests to recall an earlier user instruction are themselves
    # recall prompts, not evidence for the historical instruction being asked
    # about. Exclude them from source retrieval to prevent prompt self-matches.
    re.compile(
        r"\b(?:rappelle(?:-moi)?|rappeler)\s+"
        r"(?:(?:uniquement|seulement)\s+)?(?:la|le|les|ce|cette|ces)\s+"
        r"(?:r[eè]gle|consigne|demande|instruction|formulation)\b.{0,120}\b"
        r"(?:donn[ée]e?|formul[ée]e?|demand[ée]e?|pos[ée]e?)\b",
        re.IGNORECASE,
    ),
    # A determiner-led noun phrase is a general grammatical form of direct
    # recall (e.g. "Rappelle-moi l'objectif principal de notre audit"). Keep
    # this structural so each domain does not need an expanding topic list.
    re.compile(
        r"\b(?:rappelle(?:-moi)?|rappeler)\s+"
        r"(?:(?:uniquement|seulement)\s+)?"
        r"(?:l['’](?=[\wÀ-ÖØ-öø-ÿ])|(?:la|le|les|mon|ma|mes|notre|nos|ton|ta|tes|votre|vos)\s+)"
        r"[\wÀ-ÖØ-öø-ÿ'-]+(?:\s+[\wÀ-ÖØ-öø-ÿ'-]+){0,11}",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:do\s+you\s+remember|can\s+you\s+recall)\b", re.IGNORECASE),
    # Exact filenames are historical identifiers in chat: route a direct
    # "what is the filename/name of the file" question through source-backed
    # recall so generation cannot substitute a plausible-looking name.
    re.compile(
        r"\bwhat\s+is\s+the\s+(?:exact\s+)?(?:(?:markdown|text)\s+)?(?:filename|file\s*name|"
        r"name\s+of\s+(?:the\s+)?(?:markdown\s+)?file)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bquel(?:le)?\s+est\s+le\s+nom\s+du\s+(?:fichier|document)\b",
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
        # Keep a short explicit scope ("For the audit, ...") but discard
        # narrative framing such as "from my historical exchanges" or
        # "dans l’échange historique". The latter is not the memory topic and
        # must not make any nearby record containing only "audit" eligible.
        scope = re.search(
            r"\b(?:for|pour)\s+([^,;:]{1,60})\s*[,;:]\s*$",
            leading_context,
            flags=re.IGNORECASE,
        )
        leading_context = scope.group(1).strip() if scope else ""
        leading_context = re.sub(
            r"\b(?:what|which|quel(?:le)?s?)\s*$", "", leading_context,
            flags=re.IGNORECASE,
        )
        topic = asked_match.group("topic").strip(" \t\r\n,;:«»\"'")
        topic = re.split(
            r"\b(?:answer|respond|reply|quote|cite|repeat|recite|"
            r"r[eé]ponds?|r[eé]pondre|cite|r[eé]p[eè]te|recite)\b",
            topic, maxsplit=1, flags=re.IGNORECASE,
        )[0].strip(" \t\r\n,;:«»\"'")
        # Keep short identifying context after the historical clause too.
        # E.g. "What phrase did I ask you to remember for this audit?" must
        # retrieve by both "phrase" and "audit"; dropping the suffix made
        # generic topics collide with unrelated memories.
        trailing_context = value[asked_match.end():]
        trailing_context = re.split(
            r"\b(?:answer|respond|reply|quote|cite|repeat|recite|"
            r"réponds?|répondre|cite|répète|recite)\b",
            trailing_context, maxsplit=1, flags=re.IGNORECASE,
        )[0]
        trailing_context = re.sub(
            r"^\s*(?:(?:you|me)\s+)?(?:to\s+)?(?:remember|recall|provide|give|tell|rappeler|fournir|dire)\b",
            "", trailing_context, flags=re.IGNORECASE,
        )
        extracted = " ".join(
            part.strip(" \t\r\n,;:?.!«»\"'")
            for part in (leading_context, topic, trailing_context)
            if part.strip(" \t\r\n,;:?.!«»\"'")
        )
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


def explicit_recall_search_term_groups(text: str, limit: int = 12) -> List[Tuple[str, ...]]:
    """Return bounded SQLite search terms, retaining accented spellings.

    Each group represents one lexical term and may contain its original and
    accent-folded forms. Keeping variants in one group lets SQL rank a source
    once per term while still matching older records with either spelling.
    """
    focus = _explicit_recall_focus(text)
    groups: List[Tuple[str, ...]] = []
    seen = set()
    for raw in re.findall(r"[\w'-]+", focus.casefold(), flags=re.UNICODE):
        normalized = "".join(
            ch for ch in unicodedata.normalize("NFKD", raw)
            if not unicodedata.combining(ch)
        )
        if len(normalized) <= 1 or normalized in _STOPWORDS or normalized in seen:
            continue
        seen.add(normalized)
        variants = tuple(dict.fromkeys((raw, normalized)))
        groups.append(variants)
        if len(groups) >= max(1, int(limit)):
            break
    return groups


def extract_user_authored_text(memory: dict) -> str:
    """Extract user-authored text from an episodic record when available."""
    text = str(memory.get("text", ""))
    if str(memory.get("memory_type", "")).casefold() == "user_message":
        return re.sub(r"^User message:\s*", "", text, flags=re.IGNORECASE).strip()
    match = re.search(
        r"\buser\s*:\s*(.*?)(?=\s*[|\n]\s*(?:lumina|assistant)\s*:|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    value = match.group(1).strip() if match else text
    return re.sub(r"\s*\(felt\s+[^)]*\)\s*$", "", value, flags=re.IGNORECASE).strip()


def is_explicit_memory_recall_query(text: str) -> bool:
    """Recognize explicit requests to retrieve earlier conversational facts."""
    value = " ".join(str(text or "").casefold().split())
    if _historical_request_match(value) or any(
        pattern.search(value) for pattern in _DIRECT_RECALL_PATTERNS
    ):
        return True
    # Memory-writing instructions often contain "remember"/"souviens" too.
    # Treating them as recall questions sends the source utterance through the
    # self-match filter, making the very fact the user asked us to retain
    # impossible to retrieve later.
    if any(pattern.search(value) for pattern in _MEMORY_STORE_INSTRUCTION_PATTERNS):
        return False
    return any(term in value for term in (
        "talked about", "on a parlé", "we discussed", "on a dit",
        "tu sais ce que", "t'en souviens",
    ))


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
    filename_lookup = bool(re.search(
        r"\b(?:filename|file\s*name|nom\s+du\s+fichier|nom\s+du\s+document)\b",
        str(query or ""),
        flags=re.IGNORECASE,
    ))
    filtered = []
    scored_user_sources = []
    for memory in memories:
        kind = str(memory.get("memory_type", "")).casefold()
        source_text = extract_user_authored_text(memory)
        # Historical recall is specifically about what the user previously
        # said. Internal summaries, assistant replies, and unrelated memory
        # tiers may be useful for ordinary generation, but cannot serve as
        # evidence for a remembered user statement.
        if kind not in {"user_message", "episodic"} and memory.get("source") != "legacy_episodic_user_source":
            continue
        if kind in {"user_message", "episodic"} and is_explicit_memory_recall_query(source_text):
            continue
        # A neighboring status question can share the broad subject words
        # (e.g. "audit" and "harness") without stating the historical result
        # being requested. For explicit historical recall, interrogative user
        # turns are prompts, not source evidence; prefer declarative requests
        # or statements that can actually substantiate the answer.
        if kind in {"user_message", "episodic"} and re.search(r"[?？]", source_text):
            continue
        overlap_count = 0
        if focus and kind in {"user_message", "episodic"}:
            source_terms = set(tokenize(source_text))
            overlap = focus & source_terms
            overlap_count = len(overlap)
            # A single broad shared word (for example "audit") is not enough
            # to treat a neighboring conversation as evidence for a specific
            # historical request. Require both multiple matching terms and a
            # minimum fraction of the identifying topic for longer queries.
            minimum_overlap = (
                min(len(focus), max(2, math.ceil(len(focus) * 0.5)))
                if not filename_lookup else 1
            )
            minimum_ratio = 0.0 if filename_lookup else 0.5
            if len(overlap) < minimum_overlap or len(overlap) / max(1, len(focus)) < minimum_ratio:
                continue
        if focus and kind in {"user_message", "episodic"}:
            scored_user_sources.append((overlap_count, memory))
        elif not focus:
            filtered.append(memory)

    # For an explicit historical question, several neighboring user turns can
    # share broad context words while only one actually identifies the asked
    # fact. Keep sources whose content match is close to the best match; this
    # prevents a weak neighbor from entering the prompt as competing evidence.
    if scored_user_sources:
        best_overlap = max(score for score, _ in scored_user_sources)
        minimum_relevant_overlap = (
            1 if filename_lookup else max(2, math.ceil(best_overlap * 0.7))
        )
        filtered.extend(
            memory for score, memory in scored_user_sources
            if score >= minimum_relevant_overlap
        )
    return filtered


def exact_filename_recall_result(
    query: str, memories: Sequence[dict],
) -> dict | None:
    """Answer an explicit filename-recall request only from user-authored evidence.

    This is a structural extraction, not a filename or answer dictionary: the
    value must occur in a retrieved user message (or the user segment of an
    older episodic record). Earlier assistant replies are never evidence.
    Returning an explicit abstention prevents the LLM from completing a missing
    exact identifier with a plausible-looking guess.
    """
    value = str(query or "")
    if not is_explicit_memory_recall_query(value):
        return None
    asks_filename = re.search(
        r"\b(?:file\s*name|filename|name\s+of\s+(?:the\s+)?file|"
        r"nom\s+(?:du\s+|de\s+(?:ce\s+)?)fichier|nom\s+du\s+document)\b",
        value,
        re.IGNORECASE,
    )
    if not asks_filename:
        return None

    evidence = filter_recall_query_records(memories, query=value)
    file_pattern = re.compile(
        r"(?<![\w.-])(?P<path>(?:[A-Za-z0-9_.:-]+[/\\])+)?"
        r"(?P<filename>[A-Za-z0-9][A-Za-z0-9_.-]*\."
        r"(?P<extension>[A-Za-z0-9]{1,12}))\b"
    )
    for memory in evidence:
        kind = str(memory.get("memory_type", "")).casefold()
        if kind not in {"user_message", "episodic"} and memory.get("source") != "legacy_episodic_user_source":
            continue
        source_text = extract_user_authored_text(memory)
        match = file_pattern.search(source_text)
        if not match:
            continue
        extension = match.group("extension").casefold()
        if not match.group("path") and extension not in _COMMON_FILENAME_EXTENSIONS:
            continue
        filename = match.group("filename").replace("\\", "/").rsplit("/", 1)[-1]
        try:
            relevance = max(0.0, min(1.0, float(memory.get("relevance", 0.0))))
        except (TypeError, ValueError, OverflowError):
            relevance = 0.0
        stable_key = str(memory.get("id") or memory.get("faiss_id") or source_text)
        return {
            "answer": f"`{filename}`",
            "status": "supported",
            "source_ref": hashlib.sha256(stable_key.encode("utf-8", errors="replace")).hexdigest()[:20],
            "source_type": kind or "legacy_episodic_user_source",
            "relevance": round(relevance, 4),
        }

    is_french = bool(re.search(r"\b(?:quel|quelle|rappelle|souviens|fichier|document)\b", value, re.IGNORECASE))
    return {
        "answer": "Je n’ai pas retrouvé de source utilisateur confirmant le nom du fichier." if is_french
        else "I couldn't retrieve a user-authored source confirming the filename.",
        "status": "abstained_no_source",
        "source_ref": None,
        "source_type": None,
        "relevance": None,
    }


def explicit_recall_source_result(
    query: str, memories: Sequence[dict],
) -> dict | None:
    """Return retrieved user text verbatim for exact-quote recall questions.

    This is intentionally extractive: the model must not paraphrase a phrase,
    quote, wording, or other exact textual value and accidentally alter it.
    It returns only a relevant user-authored source, never an assistant claim.
    """
    value = str(query or "")
    if not is_explicit_memory_recall_query(value):
        return None
    # Formatting instructions such as "answer in one phrase/sentence" do not
    # request a verbatim quote. Only inspect the historical-question clause,
    # before response-format instructions, for exact-text intent.
    recall_clause = re.split(
        r"\b(?:answer|respond|reply|r[eé]ponds?|r[eé]pondre)\b",
        value, maxsplit=1, flags=re.IGNORECASE,
    )[0]
    asks_exact_text = bool(re.search(
        r"\b(?:exact(?:ly)?\s+)?(?:phrase|wording|quote|quotation|text|word|marker|code|"
        r"identifier|token|value|number|checksum|hash|reference|instructions?|"
        r"directions?|phrase exacte|formulation exacte|citation|consignes?|texte exact|mot exact)\b",
        recall_clause, re.IGNORECASE,
    )) and bool(re.search(
        r"\b(?:exact|exactly|phrase|wording|quote|quotation|text|word|marker|code|identifier|"
        r"token|value|number|checksum|hash|reference|instruction|direction|exacte|citation|consigne|texte|mot)\b",
        recall_clause, re.IGNORECASE,
    ))
    # "Remind me only what I asked you" requests source-bounded recall even
    # when the user did not literally ask for an exact quote. Return the
    # retrieved user statement verbatim instead of letting generation invent
    # a polished paraphrase of a historical instruction.
    asks_source_only_recall = bool(_SOURCE_ONLY_RECALL_PATTERN.search(recall_clause))
    if not asks_exact_text and not asks_source_only_recall:
        return None

    evidence = filter_recall_query_records(memories, query=value)
    focus = set(tokenize(_explicit_recall_focus(value)))
    candidates = []
    for memory in evidence:
        kind = str(memory.get("memory_type", "")).casefold()
        if kind not in {"user_message", "episodic"} and memory.get("source") != "legacy_episodic_user_source":
            continue
        source_text = extract_user_authored_text(memory)
        source_terms = set(tokenize(source_text))
        overlap = len(focus & source_terms)
        if overlap < 2:
            continue
        if asks_source_only_recall:
            # Source-only recall needs stronger topic coverage than ordinary
            # semantic retrieval. A same-topic message that merely mentions
            # "audit / harness / cognitive" is not proof of the requested
            # instruction's content.
            required_overlap = min(
                len(focus), max(4, math.ceil(len(focus) * 0.5)),
            )
            if overlap < required_overlap:
                continue
        try:
            relevance = max(0.0, min(1.0, float(memory.get("relevance", 0.0))))
        except (TypeError, ValueError, OverflowError):
            relevance = 0.0
        candidates.append((overlap, relevance, memory, source_text))
    if not candidates:
        return None

    _, relevance, memory, source_text = max(candidates, key=lambda item: (item[0], item[1]))
    excerpt = re.sub(r"\s+", " ", source_text).strip()[:800]
    stable_key = str(memory.get("id") or memory.get("faiss_id") or source_text)
    is_french = bool(re.search(
        r"\b(?:quel(?:le)?s?|formulation|citation|texte|mot|demand[ée]s?|rappelle|"
        r"qu['’]est-ce|ai-je|dans\s+l['’]échange)\b",
        value, re.IGNORECASE,
    ))
    return {
        "answer": (
            f'Source utilisateur retrouvée (extrait exact) : « {excerpt} »'
            if is_french else
            f'Retrieved user-authored source (verbatim): “{excerpt}”'
        ),
        "status": "supported_verbatim_source",
        "source_ref": hashlib.sha256(stable_key.encode("utf-8", errors="replace")).hexdigest()[:20],
        "source_type": str(memory.get("memory_type") or "legacy_episodic_user_source"),
        "relevance": round(relevance, 4),
    }


def explicit_recall_abstention_result(
    query: str, memories: Sequence[dict],
) -> dict | None:
    """Fail closed when an explicit historical query has no source record.

    The LLM can interpret retrieved records, but must not invent a past user
    request from the error/topic named in the current question. This guard is
    based on source eligibility, not a dictionary of remembered answers.
    """
    if not is_explicit_memory_recall_query(query):
        return None
    if (
        _SOURCE_ONLY_RECALL_PATTERN.search(str(query or ""))
        or _EXACT_VALUE_RECALL_PATTERN.search(str(query or ""))
    ):
        if explicit_recall_source_result(query, memories) is None:
            is_french = bool(re.search(
                r"\b(?:quel(?:le)?s?|formulation|citation|texte|mot|checksum|"
                r"demand[ée]s?|rappelle|qu['’]est-ce|ai-je|historique)\b",
                str(query or ""), re.IGNORECASE,
            )) and bool(re.search(
                r"[àâçéèêëîïôùûüÿœ]|\b(?:quel(?:le)?s?|formulation|citation|"
                r"demand[ée]s?|rappelle|ai-je)\b",
                str(query or ""), re.IGNORECASE,
            ))
            return {
                "answer": (
                    "Je n’ai pas retrouvé de source utilisateur suffisamment précise pour restituer cette valeur sans l’inventer."
                    if is_french else
                    "I couldn't find a sufficiently specific user-authored source to retrieve that value without guessing."
                ),
                "status": "abstained_insufficient_source_match",
                "source_ref": None,
                "source_type": None,
                "relevance": None,
            }
    eligible = [
        item for item in memories
        if str(item.get("memory_type", "")).casefold() in {"user_message", "episodic"}
    ]
    if eligible:
        return None
    is_french = bool(re.search(
        r"\b(?:quel(?:le)?s?|qu['’]est-ce|ai-je|avais-je|demand[ée]s?|"
        r"rappelle|souviens|échange|historique)\b",
        str(query or ""), re.IGNORECASE,
    ))
    return {
        "answer": (
            "Je n’ai pas retrouvé de source utilisateur pertinente pour vérifier ce détail historique."
            if is_french else
            "I couldn't retrieve a relevant user-authored source to verify that historical detail."
        ),
        "status": "abstained_no_source",
        "source_ref": None,
        "source_type": None,
        "relevance": None,
    }


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
    seen_user_texts = set()

    def add(memory: dict) -> None:
        key = memory.get("id") or memory.get("faiss_id") or memory.get("text")
        if key in seen:
            return
        memory_type = str(memory.get("memory_type", "")).casefold()
        if memory_type in {"user_message", "episodic"} or memory.get("source") == "legacy_episodic_user_source":
            user_text = " ".join(extract_user_authored_text(memory).casefold().split())
            if user_text and user_text in seen_user_texts:
                return
            if user_text:
                seen_user_texts.add(user_text)
        seen.add(key)
        merged.append(memory)

    for memory in user_authored:
        if (
            memory.get("memory_type") == "user_message"
            or memory.get("source") == "legacy_episodic_user_source"
        ):
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
