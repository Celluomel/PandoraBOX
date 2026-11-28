"""Scope and receipt helpers for learned behavioral user profiles."""

from __future__ import annotations

import re
import threading
from typing import Any


_PROFILE_LEARNING_OPTOUT_PATTERNS = (
    re.compile(
        r"\b(?:do\s+not|don't|never)\s+.{0,100}\b"
        r"(?:add|put|include|save|store|record|learn)\b.{0,80}\b"
        r"(?:to|in|into|on)\s+(?:my|the\s+user)\s+profile\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bne\s+(?:l['’])?(?:ajoute|mets|inscris|enregistre|"
        r"stocke|apprends|consigne)\b.{0,80}\bpas\b.{0,80}\b"
        r"(?:dans|à|sur)\s+(?:mon|notre)\s+profil\b",
        re.IGNORECASE,
    ),
)

_PROFILE_LOOKUP_EXAMPLES = (
    "What facts and preferences are explicitly stored in the named user profile?",
    "According to the saved user profile, which preferences or characteristics are recorded?",
    "Retrieve a provenance-backed fact from the person's persistent profile.",
    "Quelles préférences et caractéristiques sont explicitement enregistrées dans le profil utilisateur ?",
    "D'après les faits sauvegardés dans mon profil, quelles préférences sont enregistrées ?",
    "¿Qué hechos y preferencias están guardados explícitamente en el perfil de usuario?",
    "Welche Fakten und Präferenzen sind ausdrücklich im Benutzerprofil gespeichert?",
    "Welche Angaben über mich sind in meinem dauerhaften Nutzerprofil festgehalten?",
    "Nenne die Fakten, die ausdrücklich in meinem gespeicherten Benutzerprofil stehen.",
)
_HISTORY_RECALL_EXAMPLES = (
    "Recall a concern or fact that the user stated in an earlier conversation or chat.",
    "What did the user previously say in our past conversations? Retrieve that historical statement.",
    "Find an earlier user-authored message and report what it said, using conversation memory.",
    "Qu'est-ce que l'utilisateur a dit dans nos conversations précédentes ? Retrouve cette déclaration historique.",
    "Rappelle-moi un fait ou une préoccupation exprimée auparavant dans nos échanges.",
    "What concern had I raised in an earlier conversation about memory recall and how the user profile learns from exchanges?",
    "What did I previously say about memory recall and building my profile?",
    "Recall my earlier statement about memory recall and how the user profile is built.",
    "Quelle préoccupation avais-je exprimée lors de conversations antérieures concernant la mémoire et la construction du profil utilisateur ?",
    "Rappelle-moi ce que j'avais dit précédemment sur le rappel de mémoire et la façon dont mon profil utilisateur est construit.",
    "¿Qué preocupación expresé en conversaciones anteriores sobre la recuperación de memoria?",
    "¿Qué dije anteriormente sobre cómo se recuerda nuestra conversación?",
    "Welche Sorge habe ich in früheren Gesprächen über den Speicherabruf geäußert?",
    "Was habe ich zuvor über das Erinnern an unsere Gespräche gesagt?",
    "Rufe meine Aussage aus einem früheren Gespräch über das Gedächtnis ab.",
    "Was habe ich in unseren früheren Unterhaltungen zur Erinnerung gesagt? Suche meine damalige Aussage.",
)
_LAST_USER_QUESTION_EXAMPLES = (
    "What was the last question I asked you? Quote it exactly from our conversation.",
    "Which question did I ask most recently in this chat?",
    "Repeat my most recent question verbatim, not your previous answer.",
    "Quelle était la dernière question que je t'ai posée ? Cite-la exactement.",
    "¿Cuál fue la última pregunta que te hice? Cítala literalmente.",
    "Was war die letzte Frage, die ich dir gestellt habe? Zitiere sie wörtlich.",
    "Qual foi a última pergunta que fiz? Repita exatamente as minhas palavras.",
)
_OTHER_HISTORY_RECALL_EXAMPLES = (
    "What was my last message? Repeat the whole user message, whether it was a question or not.",
    "What did we discuss previously about the memory index? Summarize that topic.",
    "Rappelle-moi le sujet dont nous parlions avant, pas une question précise.",
    "¿Qué tema tratamos anteriormente? Resume la conversación.",
    "Was habe ich zuletzt gesagt? Wiederhole meine letzte Nachricht, auch wenn sie keine Frage war.",
)
_GENERAL_MEMORY_PROFILE_EXAMPLES = (
    "Explain conceptually how a user profile can be built from conversation exchanges.",
    "Describe the general process by which a system learns a user profile from dialogue.",
    "Comment un profil utilisateur peut-il se construire à partir des échanges, en général ?",
    "I have a concern about whether memory recall works and how my user profile is built from exchanges.",
    "I am concerned about whether memory retrieval and profile learning reflect what I say in conversation.",
    "Je m'inquiète du fonctionnement du rappel de mémoire et de la façon dont mon profil se construit à partir de nos échanges.",
    "Me preocupa si el sistema recuerda bien lo que digo y cómo construye mi perfil a partir de nuestras conversaciones.",
    "Ich mache mir Sorgen, ob das System meine Aussagen richtig erinnert und mein Profil aus unseren Gesprächen aufbaut.",
    "Erkläre allgemein, wie das Gesprächsgedächtnis funktioniert.",
)
_USER_SOURCE_STATEMENT_EXAMPLES = (
    "I doubt that the last memory retrieval found the right source; several explanations remain possible.",
    "I am concerned that my profile may not represent what I actually said in our conversations.",
    "My concern is that the conversation memory sometimes recalls a neighboring exchange instead of my statement.",
    "Je doute que le rappel ait retrouvé la bonne source ; plusieurs explications restent possibles.",
    "Je m’inquiète de la manière dont mon profil est construit à partir de nos échanges.",
    "Ma préoccupation est que le souvenir de nos échanges ne restitue pas toujours mes propos correctement.",
    "No estoy seguro de que el recuerdo haya encontrado la fuente correcta; hay varias explicaciones posibles.",
    "Me preocupa que el perfil no refleje correctamente lo que digo en nuestras conversaciones.",
    "Ich bezweifle, dass der Abruf die richtige Quelle gefunden hat; mehrere Erklärungen sind möglich.",
    "Ich mache mir Sorgen, dass mein Profil meine Aussagen aus den Gesprächen nicht korrekt wiedergibt.",
)
_HISTORICAL_RECALL_REQUEST_EXAMPLES = (
    "What concern did I raise in an earlier conversation about memory retrieval?",
    "Find my earlier user-authored statement and tell me what it said.",
    "From our previous conversations, what did I say about my profile?",
    "Quelle préoccupation ai-je exprimée dans un échange précédent au sujet du rappel mémoire ?",
    "Retrouve mon ancienne déclaration et dis-moi ce qu’elle disait.",
    "Qu’ai-je dit auparavant sur la construction de mon profil ?",
    "¿Qué preocupación expresé anteriormente sobre la recuperación de memoria?",
    "Encuentra mi mensaje anterior y dime qué decía.",
    "Welche Sorge habe ich früher über den Speicherabruf geäußert?",
    "Finde meine frühere Aussage und gib wieder, was ich gesagt habe.",
    "In our earlier conversations, what concern did I raise about memory recall and how my user profile is built from exchanges? Answer only from my own prior statements.",
    "From our previous conversations, what concern did I raise about your memory recall and how my user profile is built?",
    "What concern did I raise in an earlier conversation about memory retrieval, and what did I say about the profile?",
    "Rappelle uniquement ce que je t’ai demandé concernant la manière de conduire l’audit du harnais cognitif.",
    "Dans nos échanges précédents, qu’ai-je demandé concernant les filtres lexicaux et la prise en charge de plusieurs langues ?",
    "Quelles explications ai-je laissées ouvertes dans mon message utilisateur où je doutais que le rappel mémoire de la dernière étape ait retrouvé la bonne source ?",
    "What did I previously ask you about the accuracy of memory recall? Give only the earlier user message.",
)
_USER_UNCERTAINTY_EXAMPLES = (
    "I am uncertain whether the previous memory retrieval found the right source; several explanations remain possible.",
    "I do not know which of these explanations is correct, and the evidence does not resolve it.",
    "My current evidence cannot distinguish these competing hypotheses.",
    "Je doute que le rappel ait retrouvé la bonne source ; plusieurs explications restent possibles.",
    "Je ne sais pas encore laquelle de ces explications est correcte, les éléments ne permettent pas de trancher.",
    "No estoy seguro de cuál explicación es correcta; varias posibilidades siguen abiertas.",
    "Ich bin unsicher, welche Erklärung zutrifft; mehrere Möglichkeiten bleiben offen.",
)
_NO_EXPLICIT_UNCERTAINTY_EXAMPLES = (
    "What did I ask in the previous conversation about memory retrieval?",
    "Explain how the memory index retrieves earlier conversation messages.",
    "Summarize the evidence available about the memory retrieval process.",
    "Quels éléments ai-je mentionnés dans notre conversation précédente ?",
    "Explique comment fonctionne l'index de mémoire.",
    "¿Qué dije en la conversación anterior sobre la memoria?",
    "Erkläre, wie der Gesprächsspeicher frühere Nachrichten abruft.",
)
_CONTINUING_COMMITMENT_EXAMPLES = (
    "I am committed to continuing this project across future conversations; keep this as an ongoing objective.",
    "Please keep pursuing this goal with me beyond this exchange; this is an ongoing commitment.",
    "Je veux poursuivre ce projet avec toi dans les prochains échanges; c'est un engagement durable.",
    "Je m'engage à continuer ce travail et à revenir sur cet objectif dans nos prochaines conversations.",
    "Quiero continuar este proyecto en futuras conversaciones; es un compromiso que deseo mantener.",
    "Ich möchte dieses Vorhaben in künftigen Gesprächen weiterverfolgen; das ist ein dauerhaftes Ziel.",
)
_NO_CONTINUING_COMMITMENT_EXAMPLES = (
    "What goals are currently active?",
    "Explain how the system stores a user's goals.",
    "What uncertainties are you tracking in the Global Workspace?",
    "For this one-time question, what is the answer?",
    "Quels objectifs sont actuellement actifs ?",
    "Quelles incertitudes suis-tu dans le Global Workspace ?",
    "Explique comment le système enregistre les objectifs d'un utilisateur.",
    "¿Qué objetivos están activos ahora?",
    "Welche Ziele sind gerade aktiv?",
)

# These are semantic routing thresholds for Nomic v1.5 cosine centroids, not
# probabilities. Keep the positive floor to reject general-topic questions;
# use a small positive margin because the LLM's exact-quote evidence is checked
# independently downstream and a wide margin caused clear commitments to be
# dropped as durable intent.
_COMMITMENT_MIN_SIMILARITY = 0.66
_COMMITMENT_MIN_MARGIN = 0.02
_HISTORY_RECALL_MIN_GENERAL_MARGIN = 0.005
_COMMUNICATIVE_POSTURE_EXAMPLES = {
    "exploring": (
        "I am thinking aloud and exploring several possibilities without asking for a final answer yet.",
        "Je réfléchis à voix haute et j'explore plusieurs pistes sans chercher encore une réponse définitive.",
        "Estoy pensando en voz alta y explorando varias posibilidades, todavía sin pedir una respuesta final.",
        "Ich denke laut nach und erkunde mehrere Möglichkeiten, ohne schon eine endgültige Antwort zu erwarten.",
    ),
    "seeking_answer": (
        "Please give me a clear answer to this specific question.",
        "Je cherche une réponse claire à cette question précise.",
        "Necesito una respuesta clara a esta pregunta concreta.",
        "Ich möchte eine klare Antwort auf diese konkrete Frage.",
    ),
    "validating": (
        "Does my reasoning make sense? Please assess the idea I have proposed.",
        "Est-ce que mon raisonnement tient la route ? Évalue l'idée que je propose.",
        "¿Tiene sentido mi razonamiento? Evalúa la idea que propongo.",
        "Ist meine Überlegung nachvollziehbar? Bitte bewerte meinen Vorschlag.",
    ),
    "challenging": (
        "I disagree with that conclusion. Recheck the evidence and explain your reasoning.",
        "Je ne suis pas d'accord avec cette conclusion. Réexamine les éléments et explique ton raisonnement.",
        "No estoy de acuerdo con esa conclusión. Revisa las pruebas y explica tu razonamiento.",
        "Ich widerspreche dieser Schlussfolgerung. Prüfe die Belege erneut und erkläre deine Begründung.",
    ),
    "support_seeking": (
        "I am sharing something difficult and would like you to listen before offering advice.",
        "Je partage quelque chose de difficile et j'aimerais que tu m'écoutes avant de me conseiller.",
        "Estoy contando algo difícil y quisiera que me escucharas antes de darme consejos.",
        "Ich erzähle von etwas Belastendem und möchte, dass du erst zuhörst, bevor du Ratschläge gibst.",
    ),
    "playful": (
        "I am joking around and want to keep this exchange light.",
        "Je plaisante et je souhaite garder cet échange léger.",
        "Estoy bromeando y quiero que la conversación siga siendo ligera.",
        "Ich mache einen Scherz und möchte das Gespräch locker halten.",
    ),
    "brief": (
        "Keep your response short; I only need a brief acknowledgment.",
        "Réponds brièvement ; j'ai seulement besoin d'un court accusé de réception.",
        "Responde brevemente; solo necesito una confirmación corta.",
        "Antworte kurz; ich brauche nur eine knappe Bestätigung.",
    ),
}
_COMMUNICATIVE_POSTURE_MIN_SIMILARITY = 0.62
_COMMUNICATIVE_POSTURE_MIN_MARGIN = 0.025
_PROFILE_FACT_SCOPE_EXAMPLES = {
    "preference": (
        "Which preferences are explicitly recorded in the user's profile?",
        "What does the user prefer according to the saved profile?",
        "Quelles préférences sont explicitement enregistrées dans le profil ?",
        "¿Qué preferencias están registradas explícitamente en el perfil?",
        "Welche Vorlieben sind ausdrücklich im Profil gespeichert?",
    ),
    "dislike": (
        "Which dislikes or aversions are explicitly recorded in the user's profile?",
        "What does the user dislike according to the saved profile?",
        "Quelles aversions sont explicitement enregistrées dans le profil ?",
        "¿Qué cosas le disgustan al usuario según su perfil?",
        "Welche Abneigungen sind ausdrücklich im Profil gespeichert?",
    ),
    "interest": (
        "Which interests are explicitly recorded in the user's profile?",
        "What topics is the user interested in according to the saved profile?",
        "Quels centres d'intérêt sont explicitement enregistrés dans le profil ?",
        "¿Qué intereses están registrados explícitamente en el perfil?",
        "Welche Interessen sind ausdrücklich im Profil gespeichert?",
    ),
    "characteristic": (
        "Which user characteristics are explicitly recorded in the profile?",
        "What personal characteristics are recorded in the saved profile?",
        "Quelles caractéristiques de l'utilisateur sont explicitement enregistrées dans le profil ?",
        "¿Qué características personales están registradas en el perfil?",
        "Welche Eigenschaften der Person sind ausdrücklich im Profil gespeichert?",
    ),
}
_MEMORY_PROFILE_ROUTER_LOCK = threading.Lock()
_MEMORY_PROFILE_ROUTER_CENTROIDS: dict[str, tuple[Any, ...]] = {}
_MEMORY_SOURCE_ROLE_LOCK = threading.Lock()
_MEMORY_SOURCE_ROLE_CENTROIDS: dict[str, tuple[Any, Any]] = {}
_MEMORY_SOURCE_ROLE_MIN_SIMILARITY = 0.66
_MEMORY_SOURCE_ROLE_MIN_MARGIN = 0.015
_LAST_USER_QUESTION_MIN_SIMILARITY = 0.70
_LAST_USER_QUESTION_MIN_MARGIN = 0.03


def classify_memory_profile_intents(user_texts, *, embedder=None) -> list[dict[str, Any]]:
    """Batch-classify dialogue recall, profile lookup, and general questions."""
    texts = [" ".join(str(value or "").split()) for value in user_texts]
    if not texts:
        return []
    results: list[dict[str, Any] | None] = [
        ({"status": "empty_input", "intent": "uncertain", "reason_code": "empty_input"}
         if not text else None)
        for text in texts
    ]
    active_indices = [index for index, text in enumerate(texts) if text]
    if not active_indices:
        return [item for item in results if item is not None]
    try:
        if embedder is None:
            from utils.shared_embedder import get_quality_embedder
            embedder = get_quality_embedder()
        encoder = getattr(embedder, "encode_interactive_with_metadata", None)
        if not callable(encoder):
            raise RuntimeError("interactive quality embedding unavailable")

        cache_hint = str(
            getattr(embedder, "embedding_space_id", "")
            or getattr(embedder, "model_name", "")
        )
        with _MEMORY_PROFILE_ROUTER_LOCK:
            cached = _MEMORY_PROFILE_ROUTER_CENTROIDS.get(cache_hint)
        if cached is None:
            vectors, space_id = encoder([
                *_PROFILE_LOOKUP_EXAMPLES, *_HISTORY_RECALL_EXAMPLES,
                *_GENERAL_MEMORY_PROFILE_EXAMPLES,
                *_LAST_USER_QUESTION_EXAMPLES, *_OTHER_HISTORY_RECALL_EXAMPLES,
                *(
                    example
                    for category_examples in _PROFILE_FACT_SCOPE_EXAMPLES.values()
                    for example in category_examples
                ),
                *_USER_UNCERTAINTY_EXAMPLES,
                *_NO_EXPLICIT_UNCERTAINTY_EXAMPLES,
                *_CONTINUING_COMMITMENT_EXAMPLES,
                *_NO_CONTINUING_COMMITMENT_EXAMPLES,
                *(
                    example
                    for examples in _COMMUNICATIVE_POSTURE_EXAMPLES.values()
                    for example in examples
                ),
                *(texts[index] for index in active_indices),
            ])
            import numpy as np
            matrix = np.asarray(vectors, dtype="float64")
            prototype_count = (
                len(_PROFILE_LOOKUP_EXAMPLES) + len(_HISTORY_RECALL_EXAMPLES)
                + len(_GENERAL_MEMORY_PROFILE_EXAMPLES)
                + len(_LAST_USER_QUESTION_EXAMPLES)
                + len(_OTHER_HISTORY_RECALL_EXAMPLES)
            )
            category_example_count = sum(
                len(category_examples)
                for category_examples in _PROFILE_FACT_SCOPE_EXAMPLES.values()
            )
            uncertainty_positive_count = len(_USER_UNCERTAINTY_EXAMPLES)
            uncertainty_negative_count = len(_NO_EXPLICIT_UNCERTAINTY_EXAMPLES)
            commitment_positive_count = len(_CONTINUING_COMMITMENT_EXAMPLES)
            commitment_negative_count = len(_NO_CONTINUING_COMMITMENT_EXAMPLES)
            posture_example_count = sum(
                len(examples) for examples in _COMMUNICATIVE_POSTURE_EXAMPLES.values()
            )
            expected_rows = (
                prototype_count + category_example_count + uncertainty_positive_count
                + uncertainty_negative_count + commitment_positive_count
                + commitment_negative_count + posture_example_count + len(active_indices)
            )
            if matrix.ndim != 2 or matrix.shape[0] != expected_rows or not np.isfinite(matrix).all():
                raise ValueError("memory/profile router received invalid embeddings")
            normalized = matrix / np.maximum(
                np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12
            )
            profile_end = len(_PROFILE_LOOKUP_EXAMPLES)
            history_end = profile_end + len(_HISTORY_RECALL_EXAMPLES)
            general_end = history_end + len(_GENERAL_MEMORY_PROFILE_EXAMPLES)
            profile = normalized[:profile_end].mean(axis=0)
            history = normalized[profile_end:history_end].mean(axis=0)
            general = normalized[history_end:general_end].mean(axis=0)
            profile /= max(float(np.linalg.norm(profile)), 1e-12)
            history /= max(float(np.linalg.norm(history)), 1e-12)
            general /= max(float(np.linalg.norm(general)), 1e-12)
            last_question_end = general_end + len(_LAST_USER_QUESTION_EXAMPLES)
            last_user_question = normalized[general_end:last_question_end].mean(axis=0)
            last_user_question /= max(float(np.linalg.norm(last_user_question)), 1e-12)
            other_history_target = normalized[last_question_end:prototype_count].mean(axis=0)
            other_history_target /= max(float(np.linalg.norm(other_history_target)), 1e-12)
            category_centroids = {}
            category_offset = prototype_count
            for category, category_examples in _PROFILE_FACT_SCOPE_EXAMPLES.items():
                category_end = category_offset + len(category_examples)
                center = normalized[category_offset:category_end].mean(axis=0)
                center /= max(float(np.linalg.norm(center)), 1e-12)
                category_centroids[category] = center
                category_offset = category_end
            uncertainty_positive_end = category_offset + uncertainty_positive_count
            uncertainty_positive = normalized[category_offset:uncertainty_positive_end].mean(axis=0)
            uncertainty_positive /= max(float(np.linalg.norm(uncertainty_positive)), 1e-12)
            uncertainty_negative = normalized[
                uncertainty_positive_end:uncertainty_positive_end + uncertainty_negative_count
            ].mean(axis=0)
            uncertainty_negative /= max(float(np.linalg.norm(uncertainty_negative)), 1e-12)
            commitment_positive_start = uncertainty_positive_end + uncertainty_negative_count
            commitment_positive_end = commitment_positive_start + commitment_positive_count
            commitment_positive = normalized[
                commitment_positive_start:commitment_positive_end
            ].mean(axis=0)
            commitment_positive /= max(float(np.linalg.norm(commitment_positive)), 1e-12)
            commitment_negative = normalized[
                commitment_positive_end:commitment_positive_end + commitment_negative_count
            ].mean(axis=0)
            commitment_negative /= max(float(np.linalg.norm(commitment_negative)), 1e-12)
            posture_offset = commitment_positive_end + commitment_negative_count
            posture_centroids = {}
            for posture, examples in _COMMUNICATIVE_POSTURE_EXAMPLES.items():
                posture_end = posture_offset + len(examples)
                center = normalized[posture_offset:posture_end].mean(axis=0)
                center /= max(float(np.linalg.norm(center)), 1e-12)
                posture_centroids[posture] = center
                posture_offset = posture_end
            actual_space = str(space_id)
            if not actual_space.endswith(":text-embedding-nomic-embed-text-v1.5"):
                raise RuntimeError("memory/profile thresholds require Nomic v1.5")
            with _MEMORY_PROFILE_ROUTER_LOCK:
                _MEMORY_PROFILE_ROUTER_CENTROIDS[actual_space] = (
                    profile, history, general, last_user_question, other_history_target,
                    category_centroids,
                    uncertainty_positive, uncertainty_negative,
                    commitment_positive, commitment_negative, posture_centroids,
                )
            queries = normalized[
                prototype_count + category_example_count
                + uncertainty_positive_count + uncertainty_negative_count
                + commitment_positive_count + commitment_negative_count
                + posture_example_count:
            ]
        else:
            (profile, history, general, last_user_question, other_history_target,
             category_centroids, uncertainty_positive,
             uncertainty_negative, commitment_positive, commitment_negative,
             posture_centroids) = cached
            vectors, actual_space = encoder([texts[index] for index in active_indices])
            import numpy as np
            queries = np.asarray(vectors, dtype="float64")
            if queries.ndim != 2 or queries.shape != (len(active_indices), profile.size) or not np.isfinite(queries).all():
                raise ValueError("memory/profile query vector is incompatible")
            queries /= np.maximum(np.linalg.norm(queries, axis=1, keepdims=True), 1e-12)

        for index, query in zip(active_indices, queries):
            profile_score = float(query @ profile)
            history_score = float(query @ history)
            general_score = float(query @ general)
            last_question_score = float(query @ last_user_question)
            other_history_target_score = float(query @ other_history_target)
            last_question_margin = last_question_score - other_history_target_score
            uncertainty_positive_score = float(query @ uncertainty_positive)
            uncertainty_negative_score = float(query @ uncertainty_negative)
            uncertainty_margin = uncertainty_positive_score - uncertainty_negative_score
            uncertainty_candidate = bool(
                uncertainty_positive_score >= 0.66 and uncertainty_margin >= 0.035
            )
            commitment_positive_score = float(query @ commitment_positive)
            commitment_negative_score = float(query @ commitment_negative)
            commitment_margin = commitment_positive_score - commitment_negative_score
            commitment_candidate = bool(
                commitment_positive_score >= _COMMITMENT_MIN_SIMILARITY
                and commitment_margin >= _COMMITMENT_MIN_MARGIN
            )
            margin = profile_score - history_score
            # A strong, separated match for the specific "last user question"
            # target is itself an explicit history-recall request. Do not make
            # it pass the broader history centroid gate as well: live Nomic
            # scored this target at 0.7847 (margin 0.0434) while the broad
            # history route stayed at 0.6078 and was incorrectly left uncertain.
            last_user_question_recall = bool(
                last_question_score >= _LAST_USER_QUESTION_MIN_SIMILARITY
                and last_question_margin >= _LAST_USER_QUESTION_MIN_MARGIN
            )
            if last_user_question_recall:
                status, intent = "history_recall", "history_recall"
            elif profile_score >= 0.63 and margin >= 0.04 and profile_score - general_score >= 0.04:
                status, intent = "profile_lookup", "profile_lookup"
            elif (
                history_score >= 0.63
                and margin <= -0.04
                and history_score - general_score >= _HISTORY_RECALL_MIN_GENERAL_MARGIN
            ):
                status, intent = "history_recall", "history_recall"
            else:
                status, intent = "intent_uncertain", "uncertain"
            category_scores = {
                category: float(query @ center)
                for category, center in category_centroids.items()
            }
            ranked_categories = sorted(
                category_scores.items(), key=lambda item: item[1], reverse=True,
            )
            category_margin = ranked_categories[0][1] - ranked_categories[1][1]
            category_scope = (
                ranked_categories[0][0]
                if ranked_categories[0][1] >= 0.64 and category_margin >= 0.025
                else "all"
            )
            posture_scores = {
                posture: float(query @ center)
                for posture, center in posture_centroids.items()
            }
            ranked_postures = sorted(
                posture_scores.items(), key=lambda item: item[1], reverse=True,
            )
            posture_margin = ranked_postures[0][1] - ranked_postures[1][1]
            posture_classified = bool(
                ranked_postures[0][1] >= _COMMUNICATIVE_POSTURE_MIN_SIMILARITY
                and posture_margin >= _COMMUNICATIVE_POSTURE_MIN_MARGIN
            )
            communicative_posture = {
                "status": "classified" if posture_classified else "uncertain",
                "stance": ranked_postures[0][0] if posture_classified else "uncertain",
                "top_similarity": round(ranked_postures[0][1], 4),
                "margin": round(posture_margin, 4),
                "scores": {key: round(value, 4) for key, value in posture_scores.items()},
                "source": "cross_lingual_semantic_centroid",
                "embedding_space": actual_space,
                "score_semantics": "uncalibrated Nomic v1.5 cosine similarity; not a probability",
            }
            results[index] = {
                "status": status,
                "intent": intent,
                "profile_similarity": round(profile_score, 4),
                "history_similarity": round(history_score, 4),
                "general_similarity": round(general_score, 4),
                "last_user_question_recall": last_user_question_recall,
                "last_user_question_similarity": round(last_question_score, 4),
                "other_history_target_similarity": round(other_history_target_score, 4),
                "last_user_question_margin": round(last_question_margin, 4),
                "margin": round(margin, 4),
                "uncertainty_signal_candidate": uncertainty_candidate,
                "uncertainty_positive_similarity": round(uncertainty_positive_score, 4),
                "uncertainty_negative_similarity": round(uncertainty_negative_score, 4),
                "uncertainty_margin": round(uncertainty_margin, 4),
                "uncertainty_score_semantics": "uncalibrated Nomic v1.5 semantic centroid scores; not probabilities",
                "uncertainty_router_reason": (
                    "cross_lingual_semantic_centroid_margin"
                    if uncertainty_candidate else "below_uncertainty_signal_threshold"
                ),
                "continuing_commitment_candidate": commitment_candidate,
                "commitment_positive_similarity": round(commitment_positive_score, 4),
                "commitment_negative_similarity": round(commitment_negative_score, 4),
                "commitment_margin": round(commitment_margin, 4),
                "commitment_score_semantics": "uncalibrated Nomic v1.5 semantic centroid scores; not probabilities",
                "commitment_router_reason": (
                    "cross_lingual_semantic_centroid_margin"
                    if commitment_candidate else "below_commitment_signal_threshold"
                ),
                "score_semantics": "uncalibrated Nomic v1.5 cosine routing score; not a probability",
                "embedding_space": actual_space,
                "communicative_posture": communicative_posture,
                "reason_code": (
                    "semantic_last_user_question_target"
                    if last_user_question_recall
                    else "cross_lingual_semantic_centroid_margin"
                ),
                "profile_fact_scope": {
                    "scope": category_scope,
                    "status": "classified" if category_scope != "all" else "uncertain_includes_all",
                    "top_similarity": round(ranked_categories[0][1], 4),
                    "margin": round(category_margin, 4),
                    "scores": {
                        key: round(value, 4)
                        for key, value in category_scores.items()
                    },
                    "embedding_space": actual_space,
                    "score_semantics": "uncalibrated Nomic v1.5 cosine similarity; not a probability",
                },
            }
    except Exception as exc:
        for index in active_indices:
            results[index] = {
                "status": "router_unavailable",
                "intent": "uncertain",
                "reason_code": type(exc).__name__,
                "score_semantics": "unavailable; do not intercept the user's response",
                "uncertainty_signal_candidate": False,
                "uncertainty_router_reason": "router_unavailable",
                "continuing_commitment_candidate": False,
                "commitment_router_reason": "router_unavailable",
                "communicative_posture": {
                    "status": "unavailable", "stance": "uncertain",
                    "source": "router_unavailable",
                    "score_semantics": "unavailable; no posture inferred",
                },
            }
    return [item for item in results if item is not None]


def classify_memory_profile_intent(user_text: str, *, embedder=None) -> dict[str, Any]:
    """Classify one input through the batched, cross-lingual semantic router."""
    return classify_memory_profile_intents([user_text], embedder=embedder)[0]


def classify_memory_source_roles(user_texts, *, embedder=None) -> list[dict[str, Any]]:
    """Separate historical user statements from requests to retrieve history.

    This answers a different question from ``classify_memory_profile_intents``:
    topic intent (history/profile/general) must not decide whether a persisted
    user-authored utterance is a source. Source role is estimated semantically
    with Nomic v1.5; ambiguous or unavailable results remain explicit instead
    of being silently treated as either role. Scores are similarities, not
    probabilities.
    """
    texts = [" ".join(str(value or "").split()) for value in user_texts]
    if not texts:
        return []
    results: list[dict[str, Any] | None] = [
        ({"status": "empty_input", "role": "uncertain", "reason_code": "empty_input"}
         if not text else None)
        for text in texts
    ]
    active_indices = [index for index, text in enumerate(texts) if text]
    if not active_indices:
        return [item for item in results if item is not None]
    try:
        if embedder is None:
            from utils.shared_embedder import get_quality_embedder
            embedder = get_quality_embedder()
        encoder = getattr(embedder, "encode_interactive_with_metadata", None)
        if not callable(encoder):
            raise RuntimeError("interactive quality embedding unavailable")
        cache_hint = str(
            getattr(embedder, "embedding_space_id", "")
            or getattr(embedder, "model_name", "")
        )
        with _MEMORY_SOURCE_ROLE_LOCK:
            cached = _MEMORY_SOURCE_ROLE_CENTROIDS.get(cache_hint)
        if cached is None:
            vectors, space_id = encoder([
                *_USER_SOURCE_STATEMENT_EXAMPLES,
                *_HISTORICAL_RECALL_REQUEST_EXAMPLES,
                *(texts[index] for index in active_indices),
            ])
            import numpy as np
            matrix = np.asarray(vectors, dtype="float64")
            source_count = len(_USER_SOURCE_STATEMENT_EXAMPLES)
            request_count = len(_HISTORICAL_RECALL_REQUEST_EXAMPLES)
            expected_rows = source_count + request_count + len(active_indices)
            if matrix.ndim != 2 or matrix.shape[0] != expected_rows or not np.isfinite(matrix).all():
                raise ValueError("memory source-role router received invalid embeddings")
            if not str(space_id).endswith(":text-embedding-nomic-embed-text-v1.5"):
                raise RuntimeError("memory source-role thresholds require Nomic v1.5")
            normalized = matrix / np.maximum(
                np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12
            )

            def centroid(rows):
                value = rows.mean(axis=0)
                return value / max(float(np.linalg.norm(value)), 1e-12)

            source_center = centroid(normalized[:source_count])
            request_center = centroid(normalized[source_count:source_count + request_count])
            with _MEMORY_SOURCE_ROLE_LOCK:
                _MEMORY_SOURCE_ROLE_CENTROIDS[str(space_id)] = (
                    source_center, request_center,
                )
            queries = normalized[source_count + request_count:]
            actual_space = str(space_id)
        else:
            source_center, request_center = cached
            vectors, actual_space = encoder([texts[index] for index in active_indices])
            import numpy as np
            queries = np.asarray(vectors, dtype="float64")
            if (
                queries.ndim != 2
                or queries.shape != (len(active_indices), source_center.size)
                or not np.isfinite(queries).all()
            ):
                raise ValueError("memory source-role query vector is incompatible")
            queries /= np.maximum(
                np.linalg.norm(queries, axis=1, keepdims=True), 1e-12
            )

        for index, query in zip(active_indices, queries):
            source_score = float(query @ source_center)
            request_score = float(query @ request_center)
            margin = source_score - request_score
            if (
                source_score >= _MEMORY_SOURCE_ROLE_MIN_SIMILARITY
                and margin >= _MEMORY_SOURCE_ROLE_MIN_MARGIN
            ):
                role = "user_source_statement"
            elif (
                request_score >= _MEMORY_SOURCE_ROLE_MIN_SIMILARITY
                and margin <= -_MEMORY_SOURCE_ROLE_MIN_MARGIN
            ):
                role = "historical_retrieval_request"
            else:
                role = "uncertain"
            results[index] = {
                "status": "classified" if role != "uncertain" else "uncertain",
                "role": role,
                "source_similarity": round(source_score, 4),
                "request_similarity": round(request_score, 4),
                "margin": round(margin, 4),
                "embedding_space": actual_space,
                "score_semantics": "uncalibrated Nomic v1.5 cosine similarity; not a probability",
            }
    except Exception as exc:
        for index in active_indices:
            results[index] = {
                "status": "router_unavailable",
                "role": "uncertain",
                "reason_code": type(exc).__name__,
                "score_semantics": "unavailable; no source-role claim",
            }
    return [item for item in results if item is not None]


def is_explicit_named_profile_query(
    user_text: str, *, intent_result: dict[str, Any] | None = None, embedder=None,
) -> bool:
    """Return true only for a confident semantic named-profile lookup."""
    result = intent_result or classify_memory_profile_intent(user_text, embedder=embedder)
    return result.get("intent") == "profile_lookup"


def classify_profile_fact_scope(user_text: str, *, embedder=None) -> dict[str, Any]:
    """Semantically select a requested profile category; uncertainty includes all.

    The scope affects which provenance-backed facts are displayed, never which
    facts are considered true. An uncertain or unavailable classifier returns
    ``all`` so it cannot silently hide relevant categories.
    """
    result = classify_memory_profile_intent(user_text, embedder=embedder)
    scope = result.get("profile_fact_scope")
    if isinstance(scope, dict):
        return scope
    return {
        "scope": "all",
        "status": "router_unavailable_includes_all",
        "reason_code": str(result.get("reason_code") or result.get("status") or "unavailable"),
        "score_semantics": "unavailable; include all provenance-backed categories",
    }


def render_explicit_profile_facts(
    facts: list[dict], user_text: str, *, requested_categories=None,
) -> dict[str, object]:
    """Render a direct answer from provenance-backed profile values only."""
    text = str(user_text or "").casefold()
    french = bool(
        re.search(r"\b(?:mon|ma|notre|votre|quelle|quelles|selon|enregistr[eé])\b", text)
        or re.search(r"[àâçéèêëîïôùûüÿœ]", text)
    )
    selected_categories = (
        {str(value) for value in requested_categories}
        if requested_categories is not None else None
    )
    eligible = [
        item for item in facts
        if isinstance(item, dict)
        and isinstance(item.get("value"), str)
        and item.get("category") in {"preference", "dislike", "interest", "characteristic"}
        and (selected_categories is None or item.get("category") in selected_categories)
    ]
    if not eligible:
        answer = (
            "Le profil utilisateur nommé ne contient aucun fait explicite avec une provenance utilisateur pour cette demande."
            if french else
            "The named user profile contains no provenance-backed explicit fact for that request."
        )
        return {"answer": answer, "fact_count": 0, "categories": [], "status": "empty"}

    labels = {
        "preference": "préférence" if french else "preference",
        "dislike": "aversion" if french else "dislike",
        "interest": "centre d’intérêt" if french else "interest",
        "characteristic": "caractéristique" if french else "characteristic",
    }
    grouped: dict[str, list[str]] = {}
    for item in eligible:
        grouped.setdefault(str(item["category"]), []).append(str(item["value"]))
    details = [
        f"{labels[category]}: " + "; ".join(values)
        for category, values in grouped.items()
    ]
    answer = (
        "Dans le profil utilisateur nommé, les faits explicitement enregistrés sont : "
        + ". ".join(details) + "."
        if french else
        "The explicitly recorded facts in the named user profile are: "
        + ". ".join(details) + "."
    )
    return {
        "answer": answer,
        "fact_count": len(eligible),
        "categories": sorted(grouped),
        "status": "rendered_from_provenance_backed_profile",
    }


def has_explicit_profile_learning_opt_out(user_text: str) -> bool:
    """Recognize an explicit request not to add this turn to a user profile."""
    text = " ".join(str(user_text or "").split())
    return any(pattern.search(text) for pattern in _PROFILE_LEARNING_OPTOUT_PATTERNS)


def update_behavioral_user_profile(
    world_model: Any,
    *,
    user_id: str,
    user_text: str,
    response: str,
    emotion: str,
    human_interaction: bool,
    learn_semantic_profile: bool = True,
) -> dict:
    """Update a human profile and return a safe receipt; never learn from peer turns."""
    if not human_interaction:
        return {"status": "skipped_by_scope", "changed": False}
    if has_explicit_profile_learning_opt_out(user_text):
        return {
            "status": "skipped_explicit_opt_out",
            "changed": False,
            "persisted": False,
            "learning_scope": "none",
            "extracted_count": 0,
            "categories_updated": [],
        }
    if world_model is None or not callable(getattr(world_model, "update_from_interaction", None)):
        return {"status": "unavailable", "changed": False}
    try:
        update_with_receipt = getattr(
            world_model, "update_from_interaction_with_receipt", None,
        )
        if callable(update_with_receipt):
            profile, update_receipt = update_with_receipt(
                user_id=user_id,
                user_text=user_text,
                response=response,
                emotion=emotion,
                learn_semantic_profile=learn_semantic_profile,
            )
            update_receipt = update_receipt if isinstance(update_receipt, dict) else {}
            if profile is None:
                return {
                    **update_receipt,
                    "status": "persistence_failed",
                    "changed": True,
                    "persisted": False,
                }
            return {
                **update_receipt,
                "status": "updated",
                "changed": True,
                "persisted": True,
                "learning_scope": update_receipt.get("learning_scope"),
                "interaction_count": getattr(profile, "interaction_count", None),
            }

        profile = world_model.update_from_interaction(
            user_id=user_id, user_text=user_text,
            response=response, emotion=emotion,
        )
        if profile is None:
            return {
                "status": "persistence_failed",
                "changed": True,
                "persisted": False,
            }
        return {
            "status": "updated" if profile is not None else "no_profile_returned",
            "changed": profile is not None,
            "persisted": True,
            "interaction_count": getattr(profile, "interaction_count", None),
        }
    except Exception as exc:
        return {"status": "failed", "changed": False, "error_type": type(exc).__name__}
