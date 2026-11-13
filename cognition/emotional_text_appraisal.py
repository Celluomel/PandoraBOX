"""Small, deterministic appraisal of explicit affect in an utterance.

This is an input signal for the persistent affect model, not an emotion model
or a substitute for the cognitive event appraisals produced by the harness.
"""
from __future__ import annotations

import re
import unicodedata


_POSITIVE = {
    "happy", "glad", "joy", "joyful", "love", "loving", "wonderful",
    "great", "amazing", "fantastic", "excellent", "thank", "thanks", "grateful", "beautiful",
    "good", "nice", "pleased", "delight", "delighted", "excited", "awesome",
    "brilliant", "perfect", "superb", "helpful", "useful", "fascinating",
    "enjoy", "enjoying", "enjoyed", "appreciate", "appreciated", "satisfied",
    "peaceful", "merci", "heureux", "heureuse", "ravi", "ravie", "joie",
    "super", "genial", "formidable", "excellent", "excellente", "bon", "bonne",
    "bien", "calme", "content",
    "contente", "satisfait", "satisfaite", "reconnaissant", "reconnaissante",
}

_NEGATIVE = {
    "sad", "bad", "terrible", "awful", "horrible", "hate", "hated", "angry",
    "pain", "hurt", "broken", "fail", "failed", "failure", "wrong", "mistake",
    "frustrated", "frustration", "worried", "worry", "anxious", "anxiety",
    "scared", "confused", "confusing", "useless", "pointless", "boring",
    "disappointed", "disappointment", "lost", "stuck", "problem", "issue",
    "incorrect", "missing", "crash", "bug", "error", "upset", "triste",
    "terrible", "mauvais", "mauvaise", "inquiet", "inquiete", "angoisse",
    "anxieux", "anxieuse", "frustre", "frustree", "decu", "decue", "fache",
    "fachee", "peur", "douleur", "bloque", "bloquee", "inutile", "faux",
    "fausse", "erreur", "probleme", "mal", "inquietant", "inquietante", "mecontent",
    "mecontente",
}

_HIGH_AROUSAL = {
    "thrilled", "ecstatic", "furious", "terrified", "shocked", "urgent",
    "incredible", "unbelievable", "extraordinary", "panic", "crisis",
    "emergency", "furieux", "furieuse", "terrife", "terrifee", "panique",
    "urgence", "catastrophe", "incroyable", "terrifie", "terrifiee",
}

_NEGATORS = {"not", "no", "never", "dont", "doesnt", "isnt", "arent", "cant", "cannot", "pas", "jamais", "aucun", "aucune"}
_CONTRAST = {"but", "however", "mais", "pourtant", "cependant"}


def _normalize(text: str) -> str:
    text = (text or "").casefold().replace("’", "'")
    # Expand common English contractions before tokenization. French negation
    # is handled by its explicit "pas/jamais/aucun" token.
    for contraction, expanded in (
        ("don't", "do not"), ("doesn't", "does not"), ("isn't", "is not"),
        ("aren't", "are not"), ("can't", "cannot"), ("won't", "will not"),
        ("didn't", "did not"), ("n'est", "ne est"), ("n'ai", "ne ai"),
    ):
        text = text.replace(contraction, expanded)
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def appraise_emotional_text(text: str) -> dict[str, str]:
    """Return coarse valence/arousal from explicit words and punctuation.

    Negation flips the next affect word when it occurs within three tokens.
    Ordinary questions raise arousal to medium; a question alone is not treated
    as evidence of high arousal. Neutral instructions such as "please help" do
    not imply negative affect.
    """
    normalized = _normalize(text)
    tokens = re.findall(r"[a-z]+", normalized)
    positive = negative = high = 0
    recent: list[str] = []
    for token in tokens:
        if token in _CONTRAST:
            recent.clear()
        polarity = 1 if token in _POSITIVE else (-1 if token in _NEGATIVE else 0)
        if polarity:
            if any(word in _NEGATORS for word in recent[-3:]):
                polarity *= -1
            if polarity > 0:
                positive += 1
            else:
                negative += 1
        if token in _HIGH_AROUSAL:
            high += 1
        recent.append(token)

    valence = "Positive" if positive > negative else (
        "Negative" if negative > positive else "Neutral"
    )
    question_count = normalized.count("?")
    exclamation_count = normalized.count("!")
    if high or exclamation_count >= 2:
        arousal = "High"
    elif positive or negative or question_count or exclamation_count:
        arousal = "Medium"
    else:
        arousal = "Low"
    return {"valence": valence, "arousal": arousal}
