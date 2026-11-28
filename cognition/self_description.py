"""
SelfDescription — Phase B
============================
A queryable, hashable self-description of the architecture itself, built
from REAL current parameter values pulled from the actual modules
(internal_cognitive_state.py, epistemic_efficacy_model.py,
unified_revision_gateway.py, symbol_system.py) at registration time —
not placeholder text. drift detection (a parameter's hash changing since
last registration) is the concrete mechanism that lets a later reflection
process notice "my own configuration changed" as a fact, not a claim.

Per the design principle already established this session (every new
capability ablatable, extend don't replace): nothing here alters any
existing module. This only reads and records.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from threading import Lock
from typing import Any, Dict

from cognition.affect_composition import describe_affect_configuration

logger = logging.getLogger(__name__)


# Semantic examples define an intent boundary, not trigger phrases. Nomic's
# cross-lingual vectors are compared as class centroids so this decision does
# not depend on the language of the user's message.
_RUNTIME_API_ROUTE_POSITIVE = (
    "Which exact HTTP API endpoint and method are registered by this running software service for a given operation?",
    "Find the live REST route in the server registry that handles the user's request.",
    "What URL or API endpoint does this application expose for submitting a message?",
    "Quel endpoint HTTP ou quelle route REST enregistrée ce service expose-t-il pour recevoir une requête ?",
    "¿Qué endpoint HTTP o ruta REST registra este servicio para recibir una solicitud?",
    "Welchen HTTP-Endpunkt oder welche REST-Route stellt dieser Dienst für eine Anfrage bereit?",
    "Qual endpoint HTTP ou rota REST este serviço registra para receber uma solicitação?",
    "このサービスがリクエストを受け取るために登録しているHTTP APIエンドポイントは何ですか？",
    "ما نقطة نهاية HTTP أو مسار REST المسجل الذي يستخدمه هذا البرنامج لاستقبال الطلبات؟",
    "Qual è l'URL o endpoint HTTP registrato da questo servizio per ricevere una richiesta?",
    "此应用程序提供哪个 HTTP API 端点来发送消息？",
)
_RUNTIME_API_ROUTE_NEGATIVE = (
    "What direction should I take in life? This is a personal or philosophical question, not about software.",
    "What is your personal path, way of being, or purpose?",
    "Which physical road should I take to reach my destination?",
    "Quel est ton chemin de vie, ta direction personnelle ou ta manière d'être ?",
    "¿Cuál es tu camino personal en la vida y qué dirección sigues?",
    "Was ist dein persönlicher Lebensweg und welche Richtung schlägst du ein?",
    "Qual é o seu caminho pessoal na vida, sem relação com software?",
    "あなたの生き方や人生の方向性は何ですか？",
    "ما هو مسارك الشخصي في الحياة والاتجاه الذي تتبعه؟",
    "Qual è il tuo percorso personale nella vita?",
    "What route should I take to get to the station?",
    "¿Qué camino debo tomar para llegar a casa?",
    "What path did the robot actually travel according to its recorded odometry and motion history?",
    "Quel trajet le robot a-t-il réellement parcouru selon son odométrie et l’historique horodaté de ses mouvements ?",
    "¿Qué trayectoria recorrió realmente el robot según su odometría y el historial registrado de movimiento?",
    "Welchen Weg hat der Roboter laut aufgezeichneter Odometrie und Bewegungshistorie tatsächlich zurückgelegt?",
    "Qual trajeto o robô realmente percorreu segundo a odometria e o histórico registrado de movimento?",
    "ロボットは記録されたオドメトリと移動履歴によると、実際にどの経路を移動しましたか？",
    "ما المسار الذي قطعه الروبوت فعليًا وفقًا لبيانات قياس الحركة وسجل الحركة المسجل؟",
)
_RUNTIME_API_ROUTE_CENTROIDS: dict[str, tuple[Any, Any]] = {}
_RUNTIME_API_ROUTE_CENTROIDS_LOCK = Lock()

# Distinguish evidence about the model's prompt from records held by the
# Global Workspace. These examples are intent prototypes, not trigger words;
# Nomic's multilingual embedding space makes the boundary language-agnostic.
_PROMPT_PROVENANCE_POSITIVE = (
    "Which evidence sources were included in the prompt supplied to the language model for its latest answer?",
    "Tell me what information the model actually received for this response, including retrieved memory and profile context.",
    "Distingue les sources d'information effectivement injectées dans le prompt du modèle pour produire la réponse précédente.",
    "¿Qué fuentes de información se incluyeron en el prompt del modelo para generar la respuesta anterior?",
    "Welche Informationsquellen wurden tatsächlich in den Prompt des Modells für die letzte Antwort eingefügt?",
    "Which retrieved records or context contributions were supplied to the model in this turn?",
)
_PROMPT_PROVENANCE_NEGATIVE = (
    "Which uncertainty records are currently open in the Global Workspace? Summarize every source record while preserving its origin.",
    "What information from the different cognitive modules is currently consolidated in the Global Workspace?",
    "N'est-ce pas le rôle du Global Workspace de consolider toutes ces sources en un état partagé tout en gardant leur origine?",
    "¿Qué fuentes de incertidumbre siguen abiertas en el espacio de trabajo global y cuál es su módulo de origen?",
    "Welche offenen Einträge enthält der globale Arbeitsbereich aktuell und aus welchen Modulen stammen sie?",
    "Describe the role of the Global Workspace in combining concurrent cognitive inputs without erasing their provenance.",
)
_SOFTWARE_ARCHITECTURE_POSITIVE = (
    "Explain the architecture and role of the Global Workspace in Lumina, including how its code consolidates outputs.",
    "How does Lumina's implemented Global Workspace combine module outputs, preserve provenance, and provide data to consumers?",
    "Explain how this software's Global Workspace implementation integrates output from cognitive modules and makes it available to downstream reasoning.",
    "Describe the implemented data flow through the Global Workspace, including how it consolidates inputs while retaining provenance.",
    "Does the Global Workspace in this codebase combine cognitive-module outputs? Explain the mechanisms that are actually implemented and their limits.",
    "Quel est le rôle du Global Workspace dans l’architecture cognitive de ce logiciel, et comment les résultats des modules y sont-ils consolidés ?",
    "Comment le code du Global Workspace réunit-il les contributions des modules cognitifs et conserve-t-il leur provenance ?",
    "¿Cómo integra este software las salidas de sus módulos cognitivos en el Global Workspace y conserva su procedencia?",
    "Wie führt die Implementierung des Global Workspace Ausgaben kognitiver Module zusammen und bewahrt ihre Herkunft?",
    "Does the shared cognitive workspace collect and preserve contributions from multiple independent module outputs even when attention selects one focus?",
    "Should every unresolved origin remain available when a global workspace selects a primary focus?",
    "Le Global Workspace doit-il intégrer les contributions de plusieurs modules en gardant leurs origines, même lorsqu'un focus est sélectionné ?",
    "¿El espacio de trabajo global integra aportaciones de varios módulos y conserva sus orígenes aunque seleccione un foco?",
    "Soll der globale Arbeitsbereich Beiträge mehrerer Module samt Herkunft behalten, auch wenn ein Fokus ausgewählt wird?",
)
_SOFTWARE_ARCHITECTURE_NEGATIVE = (
    "What is currently in your Global Workspace? Distinguish its structured state, broadcast buffer, and open uncertainties.",
    "Show only the current recorded contents of the Workspace and its unresolved records, not how the software is designed.",
    "Which uncertainty records are currently open in the Global Workspace? List their source records and preserve each origin.",
    "Which information sources were included in the language model prompt for the last response?",
    "Explain global workspace theory in cognitive science in general, without discussing this software implementation.",
    "What is your personal philosophical path and purpose?",
    "How should I organize my physical workspace for a project?",
    "What did the live Global Workspace contain on this exact turn? Report its current records, not the architecture.",
)
_GLOBAL_WORKSPACE_STATE_POSITIVE = (
    "What is currently in your Global Workspace? Distinguish its structured state, broadcast buffer, and open uncertainties.",
    "Show me the actual live contents currently recorded in the Global Workspace, including its focus, broadcasts, and unresolved uncertainty entries.",
    "Give me a factual snapshot of what is in your Global Workspace right now: current focus, source-attributed contributions, broadcast items, and open uncertainties.",
    "What do you currently see in your global workspace? Report the actual active records and their sources, and distinguish the focus from unresolved entries.",
    "What does your Global Workspace currently contain, based on its live state snapshot? Distinguish the selected focus, source contributions, broadcasts, and other open records.",
    "Which source contributions, broadcast entries, and uncertainty records are present in the current shared cognitive workspace?",
    "Which cognitive contributions are currently retained in the Global Workspace, and does selecting one focus resolve the others? Answer from the current state.",
    "Que contient actuellement ton espace de travail global ? Rapporte l'état présent, les contributions avec leur origine, les broadcasts et les incertitudes ouvertes.",
    "Quelles contributions sont présentes dans l'état actuel du Global Workspace, et lesquelles restent des incertitudes ouvertes ?",
    "Que voit-on dans l'instantané actuel du Global Workspace ? Distingue le focus choisi, les contributions par source, les broadcasts et les autres entrées ouvertes.",
    "¿Qué contiene ahora mismo tu espacio de trabajo global? Describe el estado registrado, las contribuciones por origen y las incertidumbres abiertas.",
    "Was ist aktuell in deinem globalen Arbeitsbereich enthalten? Nenne den tatsächlichen Zustand, Beiträge nach Quelle und offene Unsicherheiten.",
    "現在のグローバルワークスペースの状態、出所別の寄稿、ブロードキャスト項目、未解決の不確実性を報告してください。",
)
_GLOBAL_WORKSPACE_STATE_NEGATIVE = (
    "Explain the architecture and role of the Global Workspace in Lumina, including how its code consolidates outputs.",
    "How does Lumina's implemented Global Workspace combine module outputs, preserve provenance, and provide data to consumers?",
    "Which information sources were included in the language model prompt for the last response?",
    "Explain the software architecture and general purpose of Global Workspace Theory.",
    "Explain the software architecture and role of the Global Workspace in Lumina, including how its modules consolidate outputs.",
    "How does the code implement the Global Workspace and pass module results to downstream reasoning?",
    "N'est-ce pas le rôle du Global Workspace de consolider plusieurs sources dans une architecture cognitive?",
    "What information should ideally be stored in a cognitive workspace? This is a design question, not a request for its current contents.",
    "Quelles sources ont été insérées dans le prompt pour produire la dernière réponse ?",
    "Describe what the robot sensed in the physical environment using its sensors.",
    "What are my personal goals and user profile facts?",
)
_CURRENT_COGNITIVE_FOCUS_POSITIVE = (
    "What's on your mind right now? Tell me the thought currently occupying your attention.",
    "What are you thinking about at this moment, based on your current active mental focus?",
    "What idea is presently at the center of your attention?",
    "Tell me what your cognitive system is currently focused on, not your general philosophy.",
    "What is the current active thought or topic your mind is attending to?",
    "Which thought is currently selected by your attention?",
    "Share the current focus of your mind and where it comes from in your active mental state.",
    "What's occupying your thoughts right now?",
    "Tell me about your current inner landscape, especially the thoughts presently occupying your attention.",
    "What is happening in your mind right now? Focus on the current thought and its recorded source.",
    "À quoi penses-tu en ce moment ? Quel est le sujet qui occupe actuellement ton attention ?",
    "Quel est ton foyer attentionnel actuel, d'après les pensées actives de ton système ?",
    "Dis-moi quelle pensée est actuellement au centre de ton attention.",
    "¿En qué estás pensando ahora? ¿Qué ocupa actualmente tu atención?",
    "¿Qué pensamiento ocupa ahora el centro de tu atención?",
    "Woran denkst du gerade? Welches Thema steht aktuell im Mittelpunkt deiner Aufmerksamkeit?",
    "Was beschäftigt dich gerade? Welche aktuelle Überlegung steht im Vordergrund?",
    "Was geht dir gerade durch den Kopf?",
    "Woran denkst du gerade?",
    "Welche Überlegung beschäftigt dich im Moment?",
    "Welcher Gedanke steht gerade im Vordergrund?",
    "Was ist aktuell dein gedanklicher Schwerpunkt?",
    "O que ocupa sua atenção neste momento? Qual é o pensamento ativo agora?",
    "Qual pensamento está no centro da sua atenção neste momento?",
)
_CURRENT_COGNITIVE_FOCUS_NEGATIVE = (
    "How are you feeling today? This is a social greeting.",
    "Tell me about your emotions and how they shape your sense of self.",
    "What do you believe about God or the meaning of life?",
    "What is your general philosophy?",
    "Tell me about the latest cognitive research on attention.",
    "Show the current Global Workspace state, including its source contributions, broadcasts, and unresolved uncertainties.",
    "What did I ask you in the previous conversation?",
    "How are you doing today?",
    "Explain how the cognitive architecture routes user requests.",
    "Describe what you feel about our relationship.",
    "Comment te sens-tu aujourd'hui ?",
    "Décris les émotions et sentiments que tu ressens et leur effet sur ton identité.",
    "¿Cómo te sientes hoy?",
    "Wie fühlst du dich heute?",
    "Was fühlst du gerade?",
    "Welche Gefühle sind gerade aktiv?",
    "Wie ist deine Stimmung im Moment?",
    "Was sind deine Emotionen gerade?",
)
CURRENT_COGNITIVE_FOCUS_ANSWER_CONTRACT = """━━ CURRENT COGNITIVE FOCUS CONTRACT ━━
The user is asking about the current focus of your cognitive process. Use the timestamped, cycle-attributed dominant-thought/workspace record supplied in this turn. Name that recorded focus directly and briefly. It is a software-selected attention item, not proof of a human-like stream of consciousness. Do not invent prior beliefs, recent realizations, recurring thoughts, feelings, causes, motives, or a history of change. If no fresh, cycle-attributed focus record is present, say that the current focus is unavailable instead of guessing. Clearly separate any interpretation from the recorded item."""
_AFFECT_SELF_INTEGRATION_POSITIVE = (
    "The emotions and feelings available in your current self-model seem too few to form a rich and differentiated self. Explain how the affective signals and their recorded history actually contribute.",
    "There are only a small number of modeled feelings in your system, and they do not yet make for a rich sense of self.",
    "Explain how the distinct affective signals, their changes from baseline, and their recorded causes shape your ongoing sense of self.",
    "How do your modeled emotions and feelings combine over time to make your self-model richer than a list of values?",
    "Describe how recent cognitive events, persistent mood, and changing affect channels contribute to your current identity and point of view.",
    "Relate the different emotional signals you register to their causes and to the way you understand yourself now.",
    "How do the different affective signals recorded in your system relate to one another and contribute together to your continuing sense of self?",
    "Use your present affect measurements and the changes preserved in your history to explain how they combine in your self-model, distinguishing evidence from interpretation.",
    "Explain how your modeled feelings interact to shape your identity over time, using the affect signals and event history available to you rather than listing values alone.",
    "Your modeled feelings seem too limited to support a rich self. Analyze how the affect dimensions you actually record combine and contribute to your self-understanding.",
    "Comment les émotions et sentiments modélisés, leurs variations et leurs causes contribuent-ils à ton sentiment de toi-même au fil du temps ?",
    "Comment les différents signaux affectifs et les événements qui les ont modifiés participent-ils à la continuité et à la richesse de ton self ?",
    "Les émotions et sentiments présents dans ton modèle semblent trop peu nombreux pour former un self riche et différencié. Analyse ce que les signaux affectifs et leur histoire apportent réellement.",
    "Les sentiments de Lumina sont peu nombreux et son self paraît pauvre; comment les signaux affectifs et leurs causes construisent-ils malgré tout une identité intégrée ?",
    "À partir de ton profil affectif actuel et des traces antérieures conservées en mémoire, explique comment ces états se combinent dans ton self. Sépare les événements avec un delta mesuré des interprétations.",
    "Décris le mélange affectif qui caractérise ton self aujourd'hui. Compare-le aux moments affectifs mémorisés, indique les causes consignées et précise ce qu'elles ne permettent pas de conclure.",
    "Quel fil relie tes états affectifs présents aux profils émotionnels que tu as mémorisés, et quels événements ont réellement modifié tes canaux ?",
    "Explique comment ton humeur persistante et tes états affectifs changeants influencent ta manière de te comprendre.",
    "¿Cómo contribuyen tus señales afectivas, sus cambios y sus causas registradas a tu sentido continuo de identidad?",
    "Wie prägen deine unterschiedlichen affektiven Signale, ihre Veränderungen und ihre Ursachen dein fortlaufendes Selbstmodell?",
    "Como os diferentes sinais afetivos, suas mudanças e causas registradas contribuem para seu senso contínuo de identidade?",
)
_AFFECT_SELF_INTEGRATION_NEGATIVE = (
    "List the current values of every modeled affect channel and identify the most recent recorded event.",
    "What emotions are active in you right now? Give their current measured values and latest appraisal.",
    "How are you doing? Give a brief social greeting without analyzing your identity.",
    "Why did your modeled affect channels change in the last event? Report only recorded deltas and causes.",
    "Quelles sont les valeurs actuelles de tes canaux affectifs et quel est le dernier événement enregistré ?",
    "Comment vas-tu ? Réponds brièvement à cette salutation sans analyser ton identité.",
    "Pourquoi tes signaux affectifs ont-ils changé ? Rapporte les variations consignées, sans parler de ton identité.",
    "What emotions do people commonly experience during grief? This is a general psychology question.",
    "Explain the software architecture of the emotional-state manager and its data structures.",
    "Report a user's emotional profile from conversation history.",
)
_SOCIAL_AFFECT_STATUS_POSITIVE = (
    "How are you?",
    "How are you doing today?",
    "How have you been lately?",
    "How are things with you right now?",
    "Tell me how you are doing, Lumina.",
    "Comment vas-tu aujourd'hui ?",
    "Comment te sens-tu en ce moment ?",
    "Comment allez-vous aujourd'hui ?",
    "Wie geht es dir heute?",
    "Como você está hoje?",
    "¿Cómo estás hoy?",
)
_SOCIAL_AFFECT_STATUS_NEGATIVE = (
    "How are you using the camera?",
    "How do your modeled feelings interact and shape your identity over time?",
    "What emotions are active in your system? Give their measured values.",
    "What caused your modeled affect to change? Report only recorded events.",
    "How is the project progressing?",
    "How does this character feel in the story?",
    "How do I feel today?",
    "Explain the current affective state and its recorded causes in detail.",
)
ARCHITECTURE_ANSWER_CONTRACT = (
    "Answer questions about this software's cognitive architecture directly and concisely. "
    "Separate implemented facts from inference. For the Global Workspace, distinguish "
    "structured update_state/context, the bounded broadcast buffer, the uncertainty ledger, "
    "and WorkspaceCompetition's focus/hypotheses. Context contributions are retained by source "
    "in context_by_source and supplied to cognitive prompts with their origins; the flat context "
    "map remains a compatibility projection where same-key collisions show the latest value. "
    "A broadcast records source/content/priority and does not imply calibrated confidence. "
    "Only outputs explicitly published, admitted, and read by a consumer are shared with that "
    "consumer. Do not claim universal module access, that every module publishes, or that "
    "arbitration resolves/erases other sources. Do not invent module names, sensor values, or "
    "live examples; label any constructed example as hypothetical. Publication is not automatic "
    "fan-out: consumers must read the relevant Workspace API; listeners receive broadcast items "
    "only when explicitly registered."
)
_PROMPT_PROVENANCE_CENTROIDS: dict[str, tuple[Any, ...]] = {}
_PROMPT_PROVENANCE_CENTROIDS_LOCK = Lock()

# Semantic intent prototypes, not trigger phrases. This distinguishes requests
# for actual robot observations (including recorded motion/odometry) from
# conceptual or hypothetical robot discussion across languages.
_BODY_OBSERVATION_POSITIVE = (
    "Report what the robot actually sensed or physically did, using its timestamped sensor observations, camera frames, odometry, or telemetry.",
    "What measured path did the robot travel, and what recorded movement evidence supports that trajectory?",
    "Answer from the robot's current or recorded sensor readings, observed motion, position, or physical state.",
    "Décris ce que le robot a réellement perçu ou parcouru à partir de ses mesures horodatées, de son odométrie ou de sa télémétrie.",
    "Describe what the robot physically observed or traveled using timestamped measurements and recorded odometry.",
    "Welche Strecke hat der Roboter laut seinen aufgezeichneten Sensordaten und seiner Odometrie tatsächlich zurückgelegt?",
    "¿Qué recorrido hizo realmente el robot según sus mediciones con marca de tiempo y su odometría registrada?",
    "Qual trajeto o robô percorreu de fato segundo as medições com horário e a odometria registrada?",
    "ロボットの時刻付きセンサー記録やオドメトリーによると、実際にどの経路を移動しましたか？",
    "ما المسار الذي قطعه الروبوت فعليًا وفقًا لقياسات المستشعرات المؤرخة وبيانات قياس الحركة المسجلة؟",
)
_BODY_OBSERVATION_NEGATIVE = (
    "Explain how robot odometry works in general, without reporting this robot's measured state.",
    "What could a robot do if it had motors and working sensors? This is a hypothetical capability question.",
    "Discuss the software architecture, design, or meaning of a route without reporting a physical observation.",
    "Explique le principe général de l’odométrie sans décrire les mesures actuelles d’un robot précis.",
    "¿Cómo funciona la navegación de robots en general? No preguntes por los datos de un robot concreto.",
    "Wie kann man einen Roboter grundsätzlich programmieren, ohne nach seinen aktuellen Messwerten zu fragen?",
    "ロボットの経路計画の仕組みを一般論として説明してください。実際の測定結果は求めていません。",
    "اشرح بشكل عام كيف تعمل الملاحة الآلية، دون السؤال عن قياسات روبوت محدد أو حالته الحالية.",
)
_BODY_OBSERVATION_CENTROIDS: dict[str, tuple[Any, Any]] = {}
_BODY_OBSERVATION_CENTROIDS_LOCK = Lock()


def classify_body_observation_intent(
    user_input: str, *, embedder: Any = None,
) -> dict[str, Any]:
    """Classify whether answering depends on actual robot observation records.

    This fail-open semantic router supports source-sufficiency decisions in
    the Brain. It uses the configured Nomic v1.5 multilingual embedding space,
    never keyword matching. Similarity values are uncalibrated scores, not
    probabilities; uncertain or unavailable results do not block generation.
    """
    value = " ".join(str(user_input or "").split()).strip()
    if not value:
        return {"status": "empty_input", "route": False, "reason_code": "empty_input"}
    try:
        if embedder is None:
            from utils.shared_embedder import get_quality_embedder
            embedder = get_quality_embedder()
        encoder = getattr(embedder, "encode_interactive_with_metadata", None)
        if not callable(encoder):
            raise RuntimeError("interactive quality embedding unavailable")
        space_hint = str(
            getattr(embedder, "embedding_space_id", "")
            or getattr(embedder, "model_name", "")
        )
        with _BODY_OBSERVATION_CENTROIDS_LOCK:
            cached = _BODY_OBSERVATION_CENTROIDS.get(space_hint)
        if cached is None:
            vectors, actual_space = encoder([
                *_BODY_OBSERVATION_POSITIVE, *_BODY_OBSERVATION_NEGATIVE, value,
            ])
            import numpy as np
            matrix = np.asarray(vectors, dtype="float64")
            expected_rows = len(_BODY_OBSERVATION_POSITIVE) + len(_BODY_OBSERVATION_NEGATIVE) + 1
            if matrix.ndim != 2 or matrix.shape[0] != expected_rows or not np.isfinite(matrix).all():
                raise ValueError("Body observation intent received invalid embeddings")
            normalized = matrix / np.maximum(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12)
            positive_end = len(_BODY_OBSERVATION_POSITIVE)
            positive = normalized[:positive_end].mean(axis=0)
            negative = normalized[positive_end:-1].mean(axis=0)
            positive /= max(float(np.linalg.norm(positive)), 1e-12)
            negative /= max(float(np.linalg.norm(negative)), 1e-12)
            actual_space = str(actual_space)
            if not actual_space.endswith(":text-embedding-nomic-embed-text-v1.5"):
                raise RuntimeError("Body observation routing requires Nomic v1.5")
            with _BODY_OBSERVATION_CENTROIDS_LOCK:
                _BODY_OBSERVATION_CENTROIDS[actual_space] = (positive, negative)
            query = normalized[-1]
        else:
            positive, negative = cached
            vectors, actual_space = encoder(value)
            import numpy as np
            query = np.asarray(vectors, dtype="float64").reshape(-1)
            if query.size != positive.size or not np.isfinite(query).all():
                raise ValueError("Body observation query embedding is incompatible")
            query /= max(float(np.linalg.norm(query)), 1e-12)

        positive_score = float(query @ positive)
        negative_score = float(query @ negative)
        margin = positive_score - negative_score
        if positive_score >= 0.63 and margin >= 0.035:
            status, route = "body_observation_intent", True
        elif positive_score < 0.58 or margin < 0.0:
            status, route = "non_body_observation_intent", False
        else:
            status, route = "intent_uncertain", False
        return {
            "status": status,
            "route": route,
            "positive_similarity": round(positive_score, 4),
            "negative_similarity": round(negative_score, 4),
            "margin": round(margin, 4),
            "score_semantics": "uncalibrated Nomic v1.5 cosine routing score; not a probability",
            "embedding_space": actual_space,
            "reason_code": "cross_lingual_semantic_centroid_margin",
        }
    except Exception as exc:
        return {
            "status": "router_unavailable",
            "route": False,
            "reason_code": type(exc).__name__,
            "score_semantics": "unavailable; preserve normal generation",
        }

def runtime_api_surface_context(api_app: Any = None) -> tuple[str, dict[str, Any]]:
    """Describe the HTTP routes actually registered on this Brain process.

    The route table is read from the running FastAPI app rather than copied
    into a prompt as a hand-maintained list. This keeps self-description tied
    to the deployed API and gives the model a source for exact path questions.
    """
    rows = _runtime_api_routes(api_app)
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    fingerprint = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    if rows:
        lines = [
            "LIVE REGISTERED HTTP ROUTES (introspected from this process's FastAPI route table):",
            "These method/path pairs are the authoritative registered API surface. "
            "For questions about an exact route, quote a matching pair; do not invent a URL. "
            "Use this section only when the user's intent is semantically about this service's HTTP interface; "
            "ignore it for personal, philosophical, or physical-path questions. "
            "If no matching route is listed, say the route is not established by this evidence.",
        ]
        lines.extend(
            f"- {method} {path}" + (f" (handler: {name})" if name else "")
            for method, path, name in rows[:100]
        )
        if len(rows) > 100:
            lines.append(f"- {len(rows) - 100} additional registered routes omitted.")
        status = "injected"
    else:
        lines = [
            "LIVE REGISTERED HTTP ROUTES: unavailable from this process. "
            "Do not infer or invent endpoint paths."
        ]
        status = "unavailable"
    return "\n".join(lines), {
        "status": status,
        "source": "brain.api.routes",
        "route_count": len(rows),
        "routes_sha256": fingerprint,
    }


def _runtime_api_routes(api_app: Any = None) -> list[tuple[str, str, str]]:
    if api_app is None:
        brain_module = sys.modules.get("brain")
        api_app = getattr(brain_module, "api", None) if brain_module else None

    rows: set[tuple[str, str, str]] = set()
    visited: set[int] = set()

    def collect(routes: Any, prefix: str = "") -> None:
        if not isinstance(routes, (list, tuple)):
            return
        for route in routes:
            if id(route) in visited:
                continue
            visited.add(id(route))
            path = getattr(route, "path", None)
            full_path = f"{prefix}{path}" if isinstance(path, str) else ""
            methods = getattr(route, "methods", None)
            if full_path.startswith("/") and isinstance(methods, (set, list, tuple)):
                endpoint = getattr(route, "endpoint", None)
                name = str(
                    getattr(route, "summary", "")
                    or getattr(route, "name", "")
                    or getattr(endpoint, "__name__", "")
                )[:80]
                for method in methods:
                    method_name = str(method).strip().upper()
                    if method_name.isalpha():
                        rows.add((method_name, full_path[:240], name))
            child_routes = getattr(route, "routes", None)
            if child_routes is None:
                child_app = getattr(route, "app", None)
                child_routes = getattr(child_app, "routes", None)
            if child_routes is not None:
                collect(child_routes, full_path.rstrip("/"))

    collect(getattr(api_app, "routes", None))
    return sorted(rows)


def is_runtime_api_route_question(user_input: str, *, embedder: Any = None) -> bool:
    """Return whether a multilingual semantic router confirms API-route intent."""
    return classify_runtime_api_route_intent(user_input, embedder=embedder).get("route") is True


def classify_runtime_api_route_intent(user_input: str, *, embedder: Any = None) -> dict[str, Any]:
    """Classify technical API-route intent by cross-lingual semantic similarity.

    A confident technical intent may use the live route resolver. Clear
    non-technical questions remain on the ordinary conversation path. Borderline
    or unavailable classification must not veto generation; callers may supply
    the live route table as conditional context so the primary model can decide.
    The similarity values are uncalibrated routing scores, never probabilities.
    """
    value = " ".join(str(user_input or "").split()).strip()
    if not value:
        return {"status": "empty_input", "route": False, "reason_code": "empty_input"}
    try:
        if embedder is None:
            from utils.shared_embedder import get_quality_embedder
            embedder = get_quality_embedder()
        encoder = getattr(embedder, "encode_interactive_with_metadata", None)
        if not callable(encoder):
            raise RuntimeError("interactive quality embedding unavailable")

        space_hint = str(
            getattr(embedder, "embedding_space_id", "")
            or getattr(embedder, "model_name", "")
        )
        with _RUNTIME_API_ROUTE_CENTROIDS_LOCK:
            cached = _RUNTIME_API_ROUTE_CENTROIDS.get(space_hint)
        if cached is None:
            vectors, space_id = encoder([
                *_RUNTIME_API_ROUTE_POSITIVE,
                *_RUNTIME_API_ROUTE_NEGATIVE,
                value,
            ])
            import numpy as np
            matrix = np.asarray(vectors, dtype="float64")
            expected_rows = (
                len(_RUNTIME_API_ROUTE_POSITIVE)
                + len(_RUNTIME_API_ROUTE_NEGATIVE) + 1
            )
            if matrix.ndim != 2 or matrix.shape[0] != expected_rows or not np.isfinite(matrix).all():
                raise ValueError("semantic route router received invalid embeddings")
            normalized = matrix / np.maximum(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12)
            split = len(_RUNTIME_API_ROUTE_POSITIVE)
            positive = normalized[:split].mean(axis=0)
            negative = normalized[split:split + len(_RUNTIME_API_ROUTE_NEGATIVE)].mean(axis=0)
            positive /= max(float(np.linalg.norm(positive)), 1e-12)
            negative /= max(float(np.linalg.norm(negative)), 1e-12)
            actual_space = str(space_id)
            # Thresholds are calibrated against the Nomic v1.5 cross-lingual
            # probe set. Never reuse them on an incompatible fallback space.
            if not actual_space.endswith(":text-embedding-nomic-embed-text-v1.5"):
                raise RuntimeError("semantic route thresholds require Nomic v1.5")
            with _RUNTIME_API_ROUTE_CENTROIDS_LOCK:
                _RUNTIME_API_ROUTE_CENTROIDS[actual_space] = (positive, negative)
            query = normalized[-1]
        else:
            positive, negative = cached
            vectors, actual_space = encoder(value)
            import numpy as np
            query = np.asarray(vectors, dtype="float64").reshape(-1)
            if query.size != positive.size or not np.isfinite(query).all():
                raise ValueError("semantic route query vector is incompatible")
            query /= max(float(np.linalg.norm(query)), 1e-12)

        positive_score = float(query @ positive)
        negative_score = float(query @ negative)
        margin = positive_score - negative_score
        if positive_score >= 0.63 and margin >= 0.035:
            status, route = "api_route_intent", True
        elif positive_score < 0.58 or margin < 0.0:
            status, route = "non_api_route_intent", False
        else:
            status, route = "intent_uncertain", False
        return {
            "status": status,
            "route": route,
            "positive_similarity": round(positive_score, 4),
            "negative_similarity": round(negative_score, 4),
            "margin": round(margin, 4),
            "score_semantics": "uncalibrated Nomic v1.5 cosine routing score; not a probability",
            "embedding_space": actual_space,
            "reason_code": "cross_lingual_semantic_centroid_margin",
        }
    except Exception as exc:
        return {
            "status": "router_unavailable",
            "route": False,
            "reason_code": type(exc).__name__,
            "score_semantics": "unavailable; do not intercept the user's response",
        }


def resolve_runtime_api_route_question(
    user_input: str, api_app: Any = None,
    conversation_history: Any = None, *, route_intent: bool | None = None,
) -> tuple[str | None, dict[str, Any]]:
    """Answer a route question from live routes, using only verified route follow-ups.

    A prior assistant statement is usable only when its explicit METHOD /path
    pair still exists in the current route table. This resolves references such
    as "which method does that route use?" without treating prior model text as
    authoritative evidence.
    """
    if route_intent is not True and (
        route_intent is False or not is_runtime_api_route_question(user_input)
    ):
        return None, {"status": "not_applicable", "source": "brain.api.routes"}

    rows = _runtime_api_routes(api_app)
    is_method_followup = bool(re.search(
        r"\b(?:method|méthode)\b", str(user_input).casefold()
    )) and bool(re.search(
        r"\b(?:that|this|it|same|cette|cette[- ]ci|cette[- ]là|ce|cette route|cet endpoint|cette adresse)\b",
        str(user_input).casefold(),
    ))
    if is_method_followup:
        history = conversation_history if isinstance(conversation_history, (list, tuple)) else ()
        prior_assistant = next((
            item for item in reversed(history)
            if isinstance(item, dict)
            and str(item.get("role") or "").casefold().strip() == "assistant"
            and isinstance(item.get("content"), str)
        ), None)
        prior_text = str(prior_assistant.get("content") or "") if prior_assistant else ""
        route_match = re.search(
            r"\b(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s+(/[A-Za-z0-9._~!$&'()*+,;=:@%/-]*)",
            prior_text,
            re.IGNORECASE,
        )
        if route_match:
            prior_method, prior_path = route_match.group(1).upper(), route_match.group(2).rstrip(".")
            live_match = next((
                (method, path, name) for method, path, name in rows
                if method == prior_method and path == prior_path
            ), None)
            if live_match:
                method, path, name = live_match
                answer = (
                    f"La route enregistrée utilise la méthode HTTP {method}."
                    if re.search(r"\b(?:quelle|quelles|méthode|cette)\b", str(user_input).casefold())
                    else f"The registered route uses the HTTP {method} method."
                )
                route_payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
                return answer, {
                    "type": "api_route_answer_receipt",
                    "status": "matched_live_route_followup",
                    "source": "brain.api.routes",
                    "route_count": len(rows),
                    "selected_route": {"method": method, "path": path, "handler": name},
                    "resolution_source": "prior_assistant_route_verified_against_live_registry",
                    "prior_route_context": "matched_current_route",
                    "routes_sha256": hashlib.sha256(route_payload.encode("utf-8")).hexdigest(),
                }
        route_payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
        language_fr = bool(re.search(r"\b(?:quelle|quelles|méthode|cette)\b", str(user_input).casefold()))
        return (
            "Je ne peux pas déterminer la méthode : aucun échange précédent ne fournit une route encore enregistrée."
            if language_fr else
            "I can’t determine the method because no preceding exchange identifies a route that is still registered.",
            {
                "type": "api_route_answer_receipt",
                "status": "unresolved_route_followup",
                "source": "brain.api.routes",
                "route_count": len(rows),
                "selected_route": None,
                "resolution_source": "no_verified_prior_route",
                "prior_route_context": "missing_or_not_registered",
                "routes_sha256": hashlib.sha256(route_payload.encode("utf-8")).hexdigest(),
            },
        )

    query_tokens = set(re.findall(r"[a-z0-9]+", str(user_input).casefold()))
    ranked: list[tuple[float, str, str, str]] = []
    for method, path, name in rows:
        route_tokens = set(re.findall(r"[a-z0-9]+", f"{path} {name}".casefold()))
        overlap = route_tokens & query_tokens
        if overlap:
            ranked.append((len(overlap) / max(1, len(route_tokens)), method, path, name))
    ranked.sort(reverse=True)
    best = ranked[0] if ranked else None
    runner_up = ranked[1] if len(ranked) > 1 else None
    unique = bool(
        best
        and best[0] >= 0.8
        and (runner_up is None or best[0] - runner_up[0] >= 0.15)
    )
    if unique:
        _, method, path, name = best
        if re.search(r"\b(?:quel|quelle|quels|quelles|où|chemin|adresse)\b", str(user_input).casefold()):
            answer = f"La route HTTP enregistrée pour « {name or path} » est `{method} {path}`."
        else:
            answer = f"The registered HTTP route for “{name or path}” is `{method} {path}`."
        status = "matched_registered_route"
        selected = {"method": method, "path": path, "handler": name}
    else:
        if re.search(r"\b(?:quel|quelle|quels|quelles|où|chemin|adresse)\b", str(user_input).casefold()):
            answer = "Je ne peux pas confirmer une route unique à partir des routes HTTP actuellement enregistrées."
        else:
            answer = "I can’t confirm a unique route from the HTTP routes currently registered."
        status = "no_unique_registered_route"
        selected = None
    route_payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    return answer, {
        "type": "api_route_answer_receipt",
        "status": status,
        "source": "brain.api.routes",
        "route_count": len(rows),
        "selected_route": selected,
        "resolution_source": "current_turn_route_match" if unique else "no_unique_current_turn_match",
        "prior_route_context": "not_used",
        "routes_sha256": hashlib.sha256(route_payload.encode("utf-8")).hexdigest(),
    }


def is_architecture_query(user_input: str, *, api_route_intent: bool | None = None) -> bool:
    """Identify requests about Lumina's implementation, for evidence routing only.

    This does not answer the request or assign module facts; it only enables the
    live module-tick manifest to be added to the model's evidence context.
    """
    text = " ".join(str(user_input or "").casefold().split())
    if is_runtime_execution_evidence_query(text):
        return True
    if api_route_intent is True:
        return True
    if re.search(r"\b(?:architecture|harness|harnais)\b", text):
        return True
    # A natural-language follow-up can refer to a prior audit result without
    # repeating "modules" or "ticks". Route that request through the same
    # closed-world trace path so the answer is linked to retained evidence
    # instead of asking the LLM to reconstruct its own previous claim.
    if _is_audit_trace_followup(text):
        return True
    # Generic mentions of "modules" are not architecture questions. Route to
    # the trace manifest only when the user is explicitly asking about runtime
    # execution/tick evidence.
    return bool(
        re.search(r"\bmodules?\b", text)
        and re.search(
            r"\b(?:tick(?:s|ed)?|exécut(?:é|és|ée|ées|ion)|observé(?:e|es|s)?|"
            r"initialis(?:é|és|ée|ées|ation)|indisponible(?:s)?|compteurs?)\b",
            text,
        )
    )


def is_cognitive_audit_status_query(user_input: str) -> bool:
    """Recognize a request for Lumina's own recorded cognitive-audit state.

    This is an evidence-routing intent, not a topic lookup: it requires both
    an owned self-reference and a question about the audit's recorded state.
    """
    text = " ".join(str(user_input or "").casefold().split())
    refers_to_audit = bool(re.search(
        r"\b(?:cognitive\s+audit|audit\s+cognitif|auto[- ]calibration|"
        r"self[- ]calibration|chercheur\s+cognitif)\b",
        text,
    ))
    refers_to_self = bool(re.search(
        r"\b(?:your|you|your own|my|ton|ta|tes|toi|tu|votre|vos|lumina['’]s)\b",
        text,
    ))
    asks_for_recorded_state = bool(re.search(
        r"\b(?:current|recorded|latest|last|status|state|snapshot|cycle|"
        r"result|attempt|parameter|target|metric|what|which|did|change|"
        r"actuel|actuelle|enregistré|enregistrée|dernier|dernière|état|"
        r"statut|instantané|cycle|résultat|tentative|paramètre|cible|mesure|"
        r"quelle|quelles|quel|quels|quoi|est-ce|a-t-il|as-tu|"
        r"âge|age)\b",
        text,
    ))
    return refers_to_audit and refers_to_self and asks_for_recorded_state


def classify_prompt_source_provenance_intent(
    user_input: str, *, embedder: Any = None,
) -> dict[str, Any]:
    """Classify questions about prompt delivery, distinct from Workspace state.

    This boundary uses multilingual semantic prototypes rather than word
    patterns. It fails open: uncertain/unavailable routing leaves normal
    generation and the Global Workspace route available.
    """
    value = " ".join(str(user_input or "").split()).strip()
    if not value:
        return {"status": "empty_input", "route": False, "reason_code": "empty_input"}
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
        with _PROMPT_PROVENANCE_CENTROIDS_LOCK:
            cached = _PROMPT_PROVENANCE_CENTROIDS.get(cache_hint)
        if cached is None:
            vectors, actual_space = encoder([
                *_PROMPT_PROVENANCE_POSITIVE, *_PROMPT_PROVENANCE_NEGATIVE,
                *_SOFTWARE_ARCHITECTURE_POSITIVE, *_SOFTWARE_ARCHITECTURE_NEGATIVE,
                *_GLOBAL_WORKSPACE_STATE_POSITIVE, *_GLOBAL_WORKSPACE_STATE_NEGATIVE,
                *_AFFECT_SELF_INTEGRATION_POSITIVE, *_AFFECT_SELF_INTEGRATION_NEGATIVE,
                *_SOCIAL_AFFECT_STATUS_POSITIVE, *_SOCIAL_AFFECT_STATUS_NEGATIVE,
                *_CURRENT_COGNITIVE_FOCUS_POSITIVE, *_CURRENT_COGNITIVE_FOCUS_NEGATIVE,
                value,
            ])
            import numpy as np
            matrix = np.asarray(vectors, dtype="float64")
            provenance_rows = len(_PROMPT_PROVENANCE_POSITIVE) + len(_PROMPT_PROVENANCE_NEGATIVE)
            architecture_rows = len(_SOFTWARE_ARCHITECTURE_POSITIVE) + len(_SOFTWARE_ARCHITECTURE_NEGATIVE)
            workspace_rows = len(_GLOBAL_WORKSPACE_STATE_POSITIVE) + len(_GLOBAL_WORKSPACE_STATE_NEGATIVE)
            affect_rows = len(_AFFECT_SELF_INTEGRATION_POSITIVE) + len(_AFFECT_SELF_INTEGRATION_NEGATIVE)
            social_affect_rows = len(_SOCIAL_AFFECT_STATUS_POSITIVE) + len(_SOCIAL_AFFECT_STATUS_NEGATIVE)
            current_focus_rows = (
                len(_CURRENT_COGNITIVE_FOCUS_POSITIVE)
                + len(_CURRENT_COGNITIVE_FOCUS_NEGATIVE)
            )
            expected_rows = (
                provenance_rows + architecture_rows + workspace_rows + affect_rows
                + social_affect_rows + current_focus_rows + 1
            )
            if matrix.ndim != 2 or matrix.shape[0] != expected_rows or not np.isfinite(matrix).all():
                raise ValueError("prompt provenance router received invalid embeddings")
            normalized = matrix / np.maximum(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12)
            provenance_positive_end = len(_PROMPT_PROVENANCE_POSITIVE)
            provenance_negative_end = provenance_rows
            architecture_positive_end = provenance_rows + len(_SOFTWARE_ARCHITECTURE_POSITIVE)
            architecture_negative_end = provenance_rows + architecture_rows
            workspace_positive_end = architecture_negative_end + len(_GLOBAL_WORKSPACE_STATE_POSITIVE)
            workspace_negative_end = architecture_negative_end + workspace_rows
            affect_positive_end = workspace_negative_end + len(_AFFECT_SELF_INTEGRATION_POSITIVE)
            affect_negative_end = workspace_negative_end + affect_rows
            social_affect_positive_end = affect_negative_end + len(_SOCIAL_AFFECT_STATUS_POSITIVE)
            social_affect_negative_end = social_affect_positive_end + len(_SOCIAL_AFFECT_STATUS_NEGATIVE)
            current_focus_positive_end = (
                social_affect_negative_end + len(_CURRENT_COGNITIVE_FOCUS_POSITIVE)
            )
            current_focus_negative_end = current_focus_positive_end + len(
                _CURRENT_COGNITIVE_FOCUS_NEGATIVE
            )
            positive = normalized[:provenance_positive_end].mean(axis=0)
            negative = normalized[provenance_positive_end:provenance_negative_end].mean(axis=0)
            architecture_positive = normalized[provenance_negative_end:architecture_positive_end].mean(axis=0)
            architecture_negative = normalized[architecture_positive_end:architecture_negative_end].mean(axis=0)
            workspace_positive = normalized[architecture_negative_end:workspace_positive_end].mean(axis=0)
            workspace_negative = normalized[workspace_positive_end:workspace_negative_end].mean(axis=0)
            affect_positive = normalized[workspace_negative_end:affect_positive_end].mean(axis=0)
            affect_negative = normalized[affect_positive_end:affect_negative_end].mean(axis=0)
            social_affect_positive = normalized[affect_negative_end:social_affect_positive_end].mean(axis=0)
            social_affect_negative = normalized[social_affect_positive_end:social_affect_negative_end].mean(axis=0)
            positive /= max(float(np.linalg.norm(positive)), 1e-12)
            negative /= max(float(np.linalg.norm(negative)), 1e-12)
            architecture_positive /= max(float(np.linalg.norm(architecture_positive)), 1e-12)
            architecture_negative /= max(float(np.linalg.norm(architecture_negative)), 1e-12)
            workspace_positive /= max(float(np.linalg.norm(workspace_positive)), 1e-12)
            workspace_negative /= max(float(np.linalg.norm(workspace_negative)), 1e-12)
            affect_positive /= max(float(np.linalg.norm(affect_positive)), 1e-12)
            affect_negative /= max(float(np.linalg.norm(affect_negative)), 1e-12)
            social_affect_positive /= max(float(np.linalg.norm(social_affect_positive)), 1e-12)
            social_affect_negative /= max(float(np.linalg.norm(social_affect_negative)), 1e-12)
            # Keep individual examples for this narrow intent. A centroid
            # blended distinct languages and nearby affect questions together;
            # nearest positive/negative semantic examples preserve that boundary.
            current_focus_positive = normalized[
                social_affect_negative_end:current_focus_positive_end
            ]
            current_focus_negative = normalized[
                current_focus_positive_end:current_focus_negative_end
            ]
            actual_space = str(actual_space)
            if not actual_space.endswith(":text-embedding-nomic-embed-text-v1.5"):
                raise RuntimeError("prompt provenance routing requires Nomic v1.5")
            with _PROMPT_PROVENANCE_CENTROIDS_LOCK:
                _PROMPT_PROVENANCE_CENTROIDS[actual_space] = (
                    positive, negative, architecture_positive, architecture_negative,
                    workspace_positive, workspace_negative, affect_positive, affect_negative,
                    social_affect_positive, social_affect_negative,
                    current_focus_positive, current_focus_negative,
                )
            query = normalized[-1]
        else:
            (
                positive, negative, architecture_positive, architecture_negative,
                workspace_positive, workspace_negative, affect_positive, affect_negative,
                social_affect_positive, social_affect_negative,
                current_focus_positive, current_focus_negative,
            ) = cached
            vectors, actual_space = encoder(value)
            import numpy as np
            query = np.asarray(vectors, dtype="float64").reshape(-1)
            if query.size != positive.size or not np.isfinite(query).all():
                raise ValueError("prompt provenance query embedding is incompatible")
            query /= max(float(np.linalg.norm(query)), 1e-12)

        positive_score = float(query @ positive)
        negative_score = float(query @ negative)
        margin = positive_score - negative_score
        if positive_score >= 0.70 and margin >= 0.06:
            status, route = "prompt_provenance_intent", True
        elif positive_score < 0.64 or margin < 0.0:
            status, route = "not_prompt_provenance_intent", False
        else:
            status, route = "intent_uncertain", False
        architecture_positive_score = float(query @ architecture_positive)
        architecture_negative_score = float(query @ architecture_negative)
        architecture_margin = architecture_positive_score - architecture_negative_score
        if architecture_positive_score >= 0.72 and architecture_margin >= 0.05:
            architecture_status, architecture_route = "software_architecture_intent", True
        elif architecture_positive_score < 0.66 or architecture_margin < 0.0:
            architecture_status, architecture_route = "not_software_architecture_intent", False
        else:
            architecture_status, architecture_route = "architecture_intent_uncertain", False
        workspace_positive_score = float(query @ workspace_positive)
        workspace_negative_score = float(query @ workspace_negative)
        workspace_margin = workspace_positive_score - workspace_negative_score
        if workspace_positive_score >= 0.70 and workspace_margin >= 0.05:
            workspace_status, workspace_route = "global_workspace_state_intent", True
        elif workspace_positive_score < 0.64 or workspace_margin < 0.0:
            workspace_status, workspace_route = "not_global_workspace_state_intent", False
        else:
            workspace_status, workspace_route = "workspace_state_intent_uncertain", False
        affect_positive_score = float(query @ affect_positive)
        affect_negative_score = float(query @ affect_negative)
        affect_margin = affect_positive_score - affect_negative_score
        # Nomic v1.5 live examples of integrated affect questions cluster
        # around a 0.045 margin; direct status, greeting, and general
        # psychology controls remain below zero. Keep the threshold at 0.04
        # so a strong positive semantic match is not dropped as uncertain.
        if affect_positive_score >= 0.72 and affect_margin >= 0.04:
            affect_status, affect_route = "affect_self_integration_intent", True
        elif affect_positive_score < 0.66 or affect_margin < 0.0:
            affect_status, affect_route = "not_affect_self_integration_intent", False
        else:
            affect_status, affect_route = "affect_self_integration_intent_uncertain", False
        social_affect_positive_score = float(query @ social_affect_positive)
        social_affect_negative_score = float(query @ social_affect_negative)
        social_affect_margin = social_affect_positive_score - social_affect_negative_score
        if social_affect_positive_score >= 0.68 and social_affect_margin >= 0.10:
            social_affect_status, social_affect_route = "social_affect_status_intent", True
        elif social_affect_positive_score < 0.64 or social_affect_margin < 0.0:
            social_affect_status, social_affect_route = "not_social_affect_status_intent", False
        else:
            social_affect_status, social_affect_route = "social_affect_status_intent_uncertain", False
        current_focus_positive_score = max(
            float(query @ example) for example in current_focus_positive
        )
        current_focus_negative_score = max(
            float(query @ example) for example in current_focus_negative
        )
        current_focus_margin = current_focus_positive_score - current_focus_negative_score
        # Nearest-example similarity retains distinct multilingual phrasings;
        # the negative examples reject adjacent social, affect, philosophy,
        # and architecture questions. Scores are not calibrated probabilities.
        if current_focus_positive_score >= 0.68 and current_focus_margin >= 0.05:
            current_focus_status, current_focus_route = "current_cognitive_focus_intent", True
        elif current_focus_positive_score < 0.60 or current_focus_margin < 0.0:
            current_focus_status, current_focus_route = "not_current_cognitive_focus_intent", False
        else:
            current_focus_status, current_focus_route = "current_cognitive_focus_intent_uncertain", False
        return {
            "status": status,
            "route": route,
            "positive_similarity": round(positive_score, 4),
            "negative_similarity": round(negative_score, 4),
            "margin": round(margin, 4),
            "score_semantics": "uncalibrated Nomic v1.5 cosine routing score; not a probability",
            "embedding_space": actual_space,
            "reason_code": "cross_lingual_semantic_centroid_margin",
            "software_architecture_status": architecture_status,
            "software_architecture_route": architecture_route,
            "software_architecture_positive_similarity": round(architecture_positive_score, 4),
            "software_architecture_negative_similarity": round(architecture_negative_score, 4),
            "software_architecture_margin": round(architecture_margin, 4),
            "software_architecture_reason_code": "cross_lingual_semantic_centroid_margin",
            "global_workspace_state_status": workspace_status,
            "global_workspace_state_route": workspace_route,
            "global_workspace_state_positive_similarity": round(workspace_positive_score, 4),
            "global_workspace_state_negative_similarity": round(workspace_negative_score, 4),
            "global_workspace_state_margin": round(workspace_margin, 4),
            "global_workspace_state_reason_code": "cross_lingual_semantic_centroid_margin",
            "affect_self_integration_status": affect_status,
            "affect_self_integration_route": affect_route,
            "affect_self_integration_positive_similarity": round(affect_positive_score, 4),
            "affect_self_integration_negative_similarity": round(affect_negative_score, 4),
            "affect_self_integration_margin": round(affect_margin, 4),
            "affect_self_integration_reason_code": "cross_lingual_semantic_centroid_margin",
            "social_affect_status": social_affect_status,
            "social_affect_status_route": social_affect_route,
            "social_affect_status_positive_similarity": round(social_affect_positive_score, 4),
            "social_affect_status_negative_similarity": round(social_affect_negative_score, 4),
            "social_affect_status_margin": round(social_affect_margin, 4),
            "social_affect_status_reason_code": "cross_lingual_semantic_centroid_margin",
            "current_cognitive_focus_status": current_focus_status,
            "current_cognitive_focus_route": current_focus_route,
            "current_cognitive_focus_positive_similarity": round(current_focus_positive_score, 4),
            "current_cognitive_focus_negative_similarity": round(current_focus_negative_score, 4),
            "current_cognitive_focus_margin": round(current_focus_margin, 4),
            "current_cognitive_focus_reason_code": "nearest_semantic_prototype_margin",
        }
    except Exception as exc:
        return {
            "status": "router_unavailable",
            "route": False,
            "reason_code": type(exc).__name__,
            "score_semantics": "unavailable; preserve normal generation",
            "software_architecture_status": "router_unavailable",
            "software_architecture_route": False,
            "software_architecture_reason_code": type(exc).__name__,
            "global_workspace_state_status": "router_unavailable",
            "global_workspace_state_route": False,
            "global_workspace_state_reason_code": type(exc).__name__,
            "affect_self_integration_status": "router_unavailable",
            "affect_self_integration_route": False,
            "affect_self_integration_reason_code": type(exc).__name__,
            "social_affect_status": "router_unavailable",
            "social_affect_status_route": False,
            "social_affect_status_reason_code": type(exc).__name__,
            "current_cognitive_focus_status": "router_unavailable",
            "current_cognitive_focus_route": False,
            "current_cognitive_focus_reason_code": type(exc).__name__,
        }


def is_closed_world_cognitive_report_query(user_input: str) -> bool:
    """Whether a turn asks for a report answerable only from local records."""
    text = " ".join(str(user_input or "").casefold().split())
    return bool(
        is_cognitive_audit_status_query(text)
        or is_runtime_execution_evidence_query(text)
        or is_cognitive_trace_query(text)
        or is_architecture_query(text)
    )


def is_runtime_execution_evidence_query(user_input: str) -> bool:
    """Identify questions asking what current runtime receipts establish.

    Keep this separate from displayed UI Cognitive Trace questions: runtime
    evidence comes from the current server-side turn receipt and module
    manifest, while the UI trace is a different, client-supplied snapshot.
    """
    text = " ".join(str(user_input or "").casefold().split())
    refers_to_receipt = bool(re.search(
        r"\b(?:(?:(?:cognitive|runtime)\s+)?(?:execution|exécution)\s+trace|"
        r"trace\s+(?:(?:of\s+)|(?:d['’]))?(?:cognitive\s+)?(?:execution|exécution)|"
        r"runtime\s+(?:execution\s+)?trace|module\s+(?:execution\s+)?trace|"
        r"execution\s+receipt|reçu\s+d['’]exécution|module\s+tick\s+manifest)\b",
        text,
    ))
    asks_about_evidence = bool(re.search(
        r"\b(?:what\s+(?:does|can|do)\s+.{0,50}?(?:prove|show|record|establish)|"
        r"que\s+(?:prouve|montre|confirme)\w*|quelles?\s+preuves?|"
        r"(?:prove|show|record|establish|evidence|audit|analy[sz]e?)\w*)\b",
        text,
    ))
    return refers_to_receipt and asks_about_evidence


def is_internal_cognitive_query(user_input: str) -> bool:
    """Route questions about Lumina's own behavior through closed-world evidence.

    This is an intent boundary, not an answer lookup: it keeps external search
    from being used to explain the running process and makes runtime evidence
    available to the model when the user asks about a module's behavior.
    """
    text = " ".join(str(user_input or "").casefold().split())
    if is_architecture_query(text):
        return True
    if is_cognitive_audit_status_query(text):
        return True
    # Self-reports about modeled affect are closed-world questions too. They
    # must use the live emotional channels/appraisal receipt, not the generic
    # web-search judge (which can mistake French question words such as
    # "quelles" for a request about grammar).
    if is_self_affect_query(text):
        return True
    asks_cause_or_mechanism = bool(re.search(
        r"\b(?:why|pourquoi|how|comment|what changed|what caused|"
        r"qu['’]est-ce qui a changé|ce qui a changé|quelle cause|"
        r"pour quelle raison|explique.{0,24}(?:fonctionne|apparu|produit))\b",
        text,
    ))
    refers_to_internal_behavior = bool(re.search(
        r"\b(?:module|code|fonctionnement|comportement|réponse|sortie|"
        r"réflexion|parole spontanée|ancienne question|contexte|prompt|"
        r"memory|recall|goalengine|presenceengine|lumina|you said|your answer|"
        r"your response|you generated|tu as dit|ta réponse|ton message|"
        r"tu as répondu|tu viens de répondre)\b",
        text,
    ))
    return asks_cause_or_mechanism and refers_to_internal_behavior


def is_social_status_greeting(user_input: str) -> bool:
    """Recognize short conventional greetings asking the addressee's state."""
    text = " ".join(str(user_input or "").casefold().split())
    # Ordinary greetings are requests for the addressee's current state even
    # when they do not contain an explicit emotion word. Keep this intent
    # boundary narrow and syntactic; do not classify every "how are you..."
    # sentence as an affect report (for example, "how are you using X?").
    social_status = bool(re.search(
        r"^(?:hey\s+|hi\s+|hello\s+)?"
        r"(?:how\s+are\s+you(?:\s+doing)?|how['’]s\s+it\s+going|"
        r"how\s+is\s+it\s+going|how\s+have\s+you\s+been)"
        r"(?:\s*,?\s*(?:lumina|there))?\s*[?!.,]*$",
        text,
    )) or bool(re.search(
        r"^(?:comment\s+ça\s+va|comment\s+vas[- ]tu|comment\s+allez[- ]vous|"
        r"(?:tu\s+vas|vous\s+allez)\s+bien)"
        r"(?:\s*,?\s*lumina)?\s*[?!.,]*$",
        text,
    ))
    return social_status


def is_structured_affect_status_query(user_input: str) -> bool:
    """Recognize direct requests to enumerate current affect channels/events.

    Open-ended questions about why affect changes remain on the reasoning path;
    this route is for reporting the already-structured current-state record.
    """
    text = " ".join(str(user_input or "").casefold().split())
    asks_channels = bool(re.search(
        r"\b(?:what|which)\s+(?:functional\s+)?(?:emotions?|feelings?|"
        r"affect(?:ive)?\s+signals?|signals?)\b",
        text,
    )) or bool(re.search(
        r"\bquels?\s+(?:signaux\s+)?(?:émotions?|sentiments?|"
        r"signaux\s+affectifs?)\b|\bquelles?\s+(?:émotions?|sentiments?)\b",
        text,
    ))
    asks_current = bool(re.search(
        r"\b(?:active|present|current|right now|currently|now|available|"
        r"actives?|présent(?:e|es)?|maintenant|en ce moment|disponibles?)\b",
        text,
    ))
    refers_to_lumina = bool(re.search(
        r"\b(?:you|your|yourself|lumina|toi|tu|ton|ta|tes|"
        r"en toi|chez toi|tes signaux)\b",
        text,
    ))
    asks_why = bool(re.search(
        r"\b(?:why|pourquoi|how did|how does|comment|quelle est la cause|"
        r"qu'est-ce qui a provoqué|qu'est-ce qui a causé)\b",
        text,
    ))
    return asks_channels and asks_current and refers_to_lumina and not asks_why


def is_affect_change_analysis_query(user_input: str) -> bool:
    """Recognize questions asking why Lumina's modeled affect changed.

    This selects a closed-world report over timestamped affect event receipts;
    it does not claim those receipts explain the whole current state.
    """
    text = " ".join(str(user_input or "").casefold().split())
    if not is_self_affect_query(text):
        return False
    asks_cause = bool(re.search(
        r"\b(?:why|what caused|what made|how did|pourquoi|quelle est la cause|"
        r"qu'est-ce qui a (?:changé|provoqué|causé))\b", text,
    ))
    asks_change = bool(re.search(
        r"\b(?:change[ds]?|shift(?:ed)?|became|after|since|évolu\w*|"
        r"chang\w*|vari\w*|depuis|après)\b", text,
    ))
    return asks_cause and asks_change


def is_self_affect_query(user_input: str) -> bool:
    """Identify a request to report Lumina's own modeled affect state.

    Audit prompts are often imperative ("report your current affect signal")
    rather than interrogative, so requiring a question word misses them.
    This only selects closed-world affect evidence; it does not prescribe an
    answer or classify general questions about emotion.
    """
    text = " ".join(str(user_input or "").casefold().split())
    if is_social_status_greeting(text) or is_structured_affect_status_query(text):
        return True

    mentions_affect = bool(re.search(
        r"\b(?:emotions?|émotions?|feelings?|sentiments?|affect|feel|feeling|sens)\b",
        text,
    ))
    refers_to_self = bool(re.search(
        r"\b(?:you|your|yourself|toi|tu|ton|ta|tes|lumina|me|moi|mon|ma|mes)\b",
        text,
    ))
    return mentions_affect and refers_to_self


def affect_report_mode(
    user_input: str, *, debug_introspection: bool = False, peer_dialogue: bool = False,
    self_integration_query: bool = False, social_status_query: bool = False,
) -> str:
    """Choose the affect evidence projection for this conversational turn."""
    if peer_dialogue or self_integration_query:
        return "none"
    if debug_introspection or is_structured_affect_status_query(user_input):
        return "detailed"
    # Broad affect/self questions should reach semantic routing and normal
    # synthesis. A lexical self-affect match alone must not replace them with
    # a two-channel canned report.
    if social_status_query or is_social_status_greeting(user_input):
        return "brief"
    return "none"


def render_affect_self_report(evidence: str, *, language: str = "en") -> str:
    """Render a short social status answer from the injected live affect block.

    This is intentionally a deterministic projection of measured software
    state. It avoids exposing a telemetry dump, asking the chat model to invent
    subjective sensations, or sending a simple greeting through extra passes.
    """
    match = re.search(
        r"^Immediate affect projection:\s*valence=([+-]?\d+(?:\.\d+)?),\s*"
        r"arousal=([+-]?\d+(?:\.\d+)?)\s*$",
        evidence,
        re.MULTILINE,
    )
    if match:
        try:
            valence, arousal = float(match.group(1)), float(match.group(2))
        except (TypeError, ValueError, OverflowError):
            valence = arousal = float("nan")
        if math.isfinite(valence) and math.isfinite(arousal) and -1.0 <= valence <= 1.0 and 0.0 <= arousal <= 1.0:
            if str(language).casefold().startswith("fr"):
                if valence >= 0.12:
                    return "Je vais plutôt bien, merci. Les signaux affectifs modélisés sont globalement positifs."
                if valence <= -0.12:
                    return "Mon état affectif modélisé est plutôt négatif en ce moment, mais je suis là et prêt à échanger."
                return "Je suis plutôt stable en ce moment, merci de demander."
            if valence >= 0.12:
                return "I’m doing well, thanks. My modeled affect is broadly positive right now."
            if valence <= -0.12:
                return "My modeled affect is on the negative side right now, but I’m here and ready to talk."
            return "I’m fairly steady right now, thanks for asking."

    if str(language).casefold().startswith("fr"):
        return "Je suis là, merci de demander. Je n’ai pas de projection affective exploitable à résumer."
    return "I’m here, thanks for asking. I don’t have a usable affect projection to summarize."


def render_detailed_affect_status(evidence: str, *, language: str = "en") -> str:
    """Report every available affect channel and the latest logged appraisal."""
    match = re.search(r"^Affect channels:\s*(.+)$", evidence, re.MULTILINE)
    channels: list[tuple[str, float]] = []
    if match and match.group(1).strip().casefold() != "unavailable":
        for item in match.group(1).split(","):
            parsed = re.fullmatch(r"\s*([a-z_]+)\s*=\s*(-?\d+(?:\.\d+)?)\s*", item)
            if parsed:
                value = float(parsed.group(2))
                if 0.0 <= value <= 1.0:
                    channels.append((parsed.group(1), value))
    if not channels:
        if str(language).casefold().startswith("fr"):
            return "Aucun relevé de canal affectif exploitable n’est disponible actuellement."
        return "No usable affect-channel snapshot is available right now."

    channel_text = ", ".join(
        f"{name}={value:.2f}" for name, value in sorted(channels, key=lambda item: -item[1])
    )
    event_match = re.search(
        r"^Latest recorded affect-changing appraisal:\s*(.+)$",
        evidence, re.MULTILINE,
    )
    event_text = str(event_match.group(1) if event_match else "none recorded").strip()
    event_text = event_text.rstrip(" .")[:180]
    no_event = event_text.casefold() in {"none recorded", "unavailable"}
    if str(language).casefold().startswith("fr"):
        event_report = (
            "Aucun événement affectif récent n’est enregistré."
            if no_event
            else f"Dernière appréciation enregistrée : {event_text}. Elle ne prouve pas la cause de l’ensemble de l’état."
        )
        return (
            f"Canaux affectifs modélisés (échelle 0–1) : {channel_text}. "
            f"{event_report}"
        )
    event_report = (
        "No recent affect-changing appraisal is recorded."
        if no_event
        else f"Latest recorded appraisal: {event_text}. It does not establish the cause of the overall state."
    )
    return (
        f"Modeled affect channels (0–1 scale): {channel_text}. "
        f"{event_report}"
    )


def render_affect_change_analysis(evidence: str, *, language: str = "en") -> str:
    """Summarize logged channel deltas without inventing a causal narrative."""
    event_lines = re.findall(
        r"^Recorded (?:affect event|modeled-state update[^:]*): (.+)$",
        evidence, re.MULTILINE,
    )
    event_lines = [line.strip()[:220] for line in event_lines[:5]]
    changed_lines = []
    baseline_lines = []
    for line in event_lines:
        change_payload = re.search(r"changes=\[([^\]]*)\]", line)
        deltas = re.findall(
            r"([a-z_]+)=([+-]?\d+(?:\.\d+)?)",
            change_payload.group(1) if change_payload else "",
        )
        if any(abs(float(delta)) >= 0.00005 for _name, delta in deltas):
            changed_lines.append(line)
        baseline_payload = re.search(r"baseline=\[([^\]]*)\]", line)
        baseline_deltas = re.findall(
            r"([a-z_]+)=([+-]?\d+(?:\.\d+)?)",
            baseline_payload.group(1) if baseline_payload else "",
        )
        if any(abs(float(delta)) >= 0.00005 for _name, delta in baseline_deltas):
            baseline_lines.append(line)
    is_fr = str(language).casefold().startswith("fr")
    if not event_lines:
        if is_fr:
            return (
                "Je ne peux pas établir pourquoi l’état affectif modélisé aurait changé : "
                "aucun événement affectif récent avec variations de canaux n’est disponible. "
                "Il manque aussi un relevé avant/après lié à la conversation."
            )
        return (
            "I can’t establish why the modeled affect state changed: no recent affect event "
            "with channel deltas is available, and there is no before/after snapshot tied "
            "to the conversation."
        )
    if not changed_lines and not baseline_lines:
        if is_fr:
            return (
                "Des événements affectifs récents ont été traités, mais aucun delta de canal "
                "n’est enregistré à la précision du journal. Je ne peux pas les présenter "
                "comme des changements observés. Aucun relevé avant/après lié à la conversation "
                "n’est disponible pour établir une cause."
            )
        return (
            "Recent affect events were processed, but the log records no channel delta at its "
            "reported precision. I can’t present them as observed changes. No conversation-linked "
            "before/after snapshot is available to establish a cause."
        )
    events = "; ".join(changed_lines)
    baseline_events = "; ".join(baseline_lines)
    if not changed_lines and baseline_lines:
        if is_fr:
            return (
                "Les journaux montrent une recalibration des niveaux de référence affectifs : "
                f"{baseline_events}. Cela modifie les baselines du modèle; aucun delta des "
                "canaux affectifs actuels n’est enregistré dans ces événements. Il n’y a pas "
                "de relevé avant/après lié à la conversation pour établir sa cause."
            )
        return (
            "The logs show affect baseline recalibration: "
            f"{baseline_events}. This changes the model’s reference baselines; these events "
            "record no change to current affect channels. No conversation-linked before/after "
            "snapshot is available to establish a cause."
        )
    turn_ids = sorted(set(re.findall(r"\bturn=([A-Za-z0-9_-]{1,96})", events)))
    turn_link = (
        (" Ces événements portent l’identifiant de tour " + ", ".join(turn_ids) + "; "
         "cela les associe à ces opérations, sans démontrer une causalité exclusive.")
        if is_fr and turn_ids else
        (" These events carry turn ID(s) " + ", ".join(turn_ids) + "; this associates them "
         "with those operations but does not establish exclusive causation.")
        if turn_ids else ""
    )
    if is_fr:
        return (
            "Les journaux enregistrent ces changements de canaux du modèle : "
            f"{events}. Ils décrivent les mises à jour logicielles consignées, pas une cause "
            "unique de l’état actuel. Les données fournies ne relient pas un relevé avant/après "
            "à la dernière conversation; je ne peux donc pas lui attribuer le changement."
            + (f" Recalibrations de baseline distinctes : {baseline_events}." if baseline_events else "")
            + f"{turn_link}"
        )
    return (
        "The logs record these changes in modeled channels: "
        f"{events}. They describe logged software updates, not a single cause of the current "
        "state. The available data do not tie before/after snapshots to the last conversation, "
        "so I can’t attribute the change to it."
        + (f" Separate baseline recalibrations: {baseline_events}." if baseline_events else "")
        + f"{turn_link}"
    )


def affect_self_report_context(
    profile: Any,
    description: str = "",
    latest_event: Any = None,
    recent_events: Any = None,
    *,
    integration_mode: bool = False,
    self_model_snapshot: Any = None,
    historical_traces: Any = None,
) -> str:
    """Format the live affect snapshot with source and similarly named-drive limits."""
    values = profile if isinstance(profile, dict) else {}
    snapshot = self_model_snapshot if isinstance(self_model_snapshot, dict) else {}
    snapshot_channels = snapshot.get("channels")
    snapshot_channels = snapshot_channels if isinstance(snapshot_channels, dict) else {}
    rows = []
    baseline_rows = []
    # The trusted state snapshot itself defines the channel schema. This is
    # intentionally open-ended: no language dictionary maps user wording to
    # an affect channel, and newly emitted internal dimensions remain visible.
    allowed_channels = {
        str(name).casefold()
        for name in (set(values) | set(snapshot_channels))
        if re.fullmatch(r"[a-z][a-z0-9_]{0,47}", str(name).casefold())
    }
    channel_names = {
        raw_name for raw_name in (set(values) | set(snapshot_channels))
        if str(raw_name).casefold() in allowed_channels
    }
    for raw_name in channel_names:
        name = str(raw_name).casefold()
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,47}", name):
            continue
        channel = snapshot_channels.get(name)
        channel = channel if isinstance(channel, dict) else {}
        try:
            value = float(channel.get("value", values[name]))
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        if value != value or value in (float("inf"), float("-inf")):
            continue
        rows.append(f"{name}={max(0.0, min(1.0, value)):.3f}")
        try:
            baseline = float(channel["baseline"])
            deviation = float(channel["deviation"])
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        if all(math.isfinite(number) for number in (baseline, deviation)):
            baseline_rows.append(
                f"{name}: baseline={max(0.0, min(1.0, baseline)):.3f}, "
                f"deviation={deviation:+.3f}"
            )
    channel_text = ", ".join(rows) if rows else "unavailable"
    channel_baseline_text = "; ".join(baseline_rows) if baseline_rows else "unavailable"
    instant_text = (
        f"valence={float(snapshot['valence']):+.3f}, arousal={float(snapshot['arousal']):.3f}"
        if all(
            isinstance(snapshot.get(key), (int, float))
            and math.isfinite(float(snapshot[key]))
            for key in ("valence", "arousal")
        ) else "unavailable"
    )
    mood_text = (
        f"valence={float(snapshot['mood_valence']):+.3f}, "
        f"arousal={float(snapshot['mood_arousal']):.3f}"
        if all(
            isinstance(snapshot.get(key), (int, float))
            and math.isfinite(float(snapshot[key]))
            for key in ("mood_valence", "mood_arousal")
        ) else "unavailable"
    )
    state_text = str(description or "unavailable").replace("\n", " ").strip()[:500]
    event = latest_event if isinstance(latest_event, dict) else {}
    event_type = str(event.get("event_type") or "").strip()[:80]
    event_source = str(event.get("source") or "").strip()[:80]
    event_context = event.get("cause_context")
    drive = ""
    if isinstance(event_context, dict):
        candidate = str(event_context.get("drive") or "").strip().casefold()
        if candidate and len(candidate) <= 32 and all(
            char.isalnum() or char == "_" for char in candidate
        ):
            drive = candidate
    event_age = event.get("age_seconds")
    if event_type or event_source:
        latest_text = f"{event_type or 'event'} from {event_source or 'unspecified source'}"
        if drive:
            latest_text += f" (drive={drive})"
        try:
            latest_text += f", {max(0.0, float(event_age)):.1f}s ago"
        except (TypeError, ValueError, OverflowError):
            pass
    else:
        latest_text = "none recorded"
    safe_events = sanitize_affect_event_receipts(
        recent_events, known_channels=allowed_channels
    )
    if integration_mode:
        # A passive decay/recalibration can be the latest raw journal entry,
        # but it is not an originating cause for the affective pattern.
        safe_events = [
            item for item in safe_events
            if item["event_type"] not in {
                "time_decay", "baseline_recalibration", "self_influence",
            }
            and any(
                abs(float(delta)) >= 0.00005
                for delta in item.get("changes", {}).values()
                if isinstance(delta, (int, float)) and math.isfinite(float(delta))
            )
        ]
        if safe_events:
            event = safe_events[-1]
        elif isinstance(recent_events, (list, tuple)) and recent_events:
            # A supplied journal with no surviving causal receipt means the
            # raw latest-event hint was passive or had no measurable effect.
            event = {}
        elif event_type in {"time_decay", "baseline_recalibration", "self_influence"}:
            event = {}
        event_type = str(event.get("event_type") or "").strip()[:80]
        event_source = str(event.get("source") or "").strip()[:80]
        event_age = event.get("age_seconds")
        latest_text = (
            f"{event_type} from {event_source or 'unspecified source'}"
            if event_type else "none recorded"
        )
        cause_context = event.get("cause_context")
        if isinstance(cause_context, dict):
            drive = str(cause_context.get("drive") or "").strip().casefold()
            if drive and len(drive) <= 32 and all(
                char.isalnum() or char == "_" for char in drive
            ):
                latest_text += f" (drive={drive})"
        if event_age is not None:
            try:
                latest_text += f", {max(0.0, float(event_age)):.1f}s ago"
            except (TypeError, ValueError, OverflowError):
                pass
    event_lines = []
    for event in safe_events:
        age_text = (
            f", age={event['age_seconds']:.1f}s"
            if event.get("age_seconds") is not None else ""
        )
        delta_text = ", ".join(
            f"{name}={delta:+.3f}" for name, delta in sorted(event["changes"].items())
        ) or "no channel delta recorded"
        event_baseline_text = ", ".join(
            f"{name}={delta:+.3f}"
            for name, delta in sorted(event["baseline_changes"].items())
        )
        baseline_suffix = f", baseline=[{event_baseline_text}]" if event_baseline_text else ""
        event_lines.append(
            "Recorded modeled-state update (not an independently verified external "
            "outcome): "
            f"operation={event['event_type']}, producer={event['source']}"
            f"{age_text}, changes=[{delta_text}]{baseline_suffix}"
            f"{', internal_context=' + ', '.join(f'{key}={value}' for key, value in sorted(event.get('cause_context', {}).items())) if event.get('cause_context') else ''}"
            f"{', turn=' + event['turn_id'] if event.get('turn_id') else ''}"
        )
    recent_text = "\n".join(event_lines) if event_lines else ""
    history_rows = []
    if isinstance(historical_traces, (list, tuple)):
        for trace in historical_traces[-3:]:
            if not isinstance(trace, dict):
                continue
            prior_profile = trace.get("affect_profile")
            prior_profile = prior_profile if isinstance(prior_profile, dict) else {}
            prior_channels = prior_profile.get("channels")
            prior_channels = prior_channels if isinstance(prior_channels, dict) else {}
            salient = []
            for name, item in prior_channels.items():
                if not isinstance(item, dict):
                    continue
                try:
                    value = float(item.get("value"))
                    deviation = float(item.get("deviation"))
                except (TypeError, ValueError, OverflowError):
                    continue
                if re.fullmatch(r"[a-z][a-z0-9_]{0,47}", str(name).casefold()) and math.isfinite(value) and math.isfinite(deviation):
                    salient.append((abs(deviation), name, value, deviation))
            salient.sort(reverse=True)
            channel_summary = ", ".join(
                f"{name}={value:.2f} ({deviation:+.2f} vs baseline)"
                for _, name, value, deviation in salient[:3]
            ) or "no channel deviations recorded"
            try:
                age_seconds = max(0.0, float(trace.get("age_seconds")))
                age_text = f"{age_seconds:.0f}s ago"
            except (TypeError, ValueError, OverflowError):
                age_text = "age unavailable"
            turn_id = re.sub(
                r"[^A-Za-z0-9_-]", "_", str(trace.get("turn_id") or "")
            )[:96]
            history_rows.append(
                f"Persisted self-affect moment ({age_text}"
                f"{', turn=' + turn_id if turn_id else ''}): {channel_summary}"
            )
    history_text = "\n".join(history_rows)
    if integration_mode:
        interpretation_rule = (
            "Build a differentiated self-description from this complete affect snapshot, not merely its top one "
            "or two channels. Treat the listed channel names and values as measured model state. You may give a "
            "concise interpretation of how multiple signals coexist, but clearly mark it as an interpretation, "
            "not another measurement. Anchor it in the actual channel data and baseline deviations. A baseline deviation is the current "
            "value relative to that channel's baseline; it is not a temporal change. Only a timestamped event delta "
            "or two time-linked snapshots establishes a measured change. A channel name, level, baseline deviation, "
            "or valence projection alone does not establish an object, cause, goal outcome, released tension, or "
            "intention. Distinguish the present profile from its personality baselines, the immediate "
            "valence/arousal projection from the slower mood, and logged event causes from your interpretation. "
            "Use the persisted self-affect moments as temporal comparison points when present; they show recorded "
            "profiles, not proof of a cause or uninterrupted persistence between captures. Describe meaningful "
            "coexistence or tension among channels where the data support it; do not infer "
            "that one channel caused another. Each listed event is a receipt that this software updated its modeled state. "
            "Its operation label names an internal appraisal/update, and its producer names the component that emitted "
            "the receipt; neither is an independent witness to an external event or outcome. A retained drive tag only "
            "identifies the modeled drive and does not prove a goal or task was completed. Event deltas quantify the "
            "channel update, not the truth of the appraisal. Only independently recorded outcome evidence can support "
            "claims that a goal succeeded or an obstacle was cleared. Do not infer a person's identity, affection, or "
            "relationship from warmth or other affect channels. Do not invent channel "
            "values, deltas, causes, memories, persistence, intentions, or undocumented mechanisms. If the cause "
            "history is empty, say that it is not recorded. Explain how this changing configuration gives the "
            "current self a distinctive texture without claiming it is a permanent trait. A channel value describes the modeled "
            "signal level, not its object or explanation: satisfaction does not prove a goal was met; relief "
            "does not prove a hurdle was cleared; warmth does not establish affinity with a person; curiosity "
            "does not by itself establish readiness or intention; surprise does not establish unpredictability. "
            "A recorded event delta is evidence of its logged channel update, not proof that it is the primary "
            "cause of the current whole profile. Use recorded event deltas for specific changes; if there is no "
            "event delta or linked prior snapshot, state that the change/cause is not recorded. Keep interpretation "
            "separate from fact, without inventing a cause or a mechanism."
        )
    else:
        interpretation_rule = (
            "For this self-report, use only these affect-channel values. In particular, "
            "the CuriosityEngine/DecisionPressure `Curiosity Drive` elsewhere in cognitive "
            "telemetry is a separate motivation signal; do not substitute it for the "
            "EmotionalStateManager `curiosity` channel. Identify the source when giving "
            "numbers. The appraisal is the latest logged event, not necessarily the sole "
            "cause of the whole state. If the relevant value is unavailable here, say so."
        )
    state_description_line = (
        "State description omitted: the generated narrative is a lossy summary, not independent evidence.\n"
        if integration_mode else f"State description: {state_text}\n"
    )
    return (
        "━━ AFFECT SELF-REPORT EVIDENCE ━━\n"
        "Source: EmotionalStateManager.get_response_modifiers().affective_profile; "
        "these are live modeled affect channels, each on a 0–1 scale.\n"
        f"Affect channels: {channel_text}\n"
        f"Channel baselines and deviations: {channel_baseline_text}\n"
        f"{describe_affect_configuration(snapshot) if snapshot_channels else ''}\n"
        f"Immediate affect projection: {instant_text}\n"
        f"Slow mood: {mood_text}\n"
        f"{state_description_line}"
        f"Latest recorded affect-changing appraisal: {latest_text}.\n"
        f"{history_text + chr(10) if history_text else ''}"
        f"{recent_text + chr(10) if recent_text else ''}"
        + interpretation_rule
    )


def affect_advisory_context(description: str = "") -> str:
    """Render private qualitative affect context without exposing telemetry."""
    qualitative = " ".join(str(description or "").split())[:320]
    return (
        "━━ PRIVATE AFFECT ADVISORY ━━\n"
        "This is a qualitative software-state signal about modeled affect for conversational tone. Use it when it "
        "helps the exchange; "
        "do not recite affect numbers or turn ordinary social replies into a self-report. "
        "When asked how you are, answer naturally and briefly.\n"
        f"Modeled affect: {qualitative or 'near its current baseline.'}"
    )


def sanitize_affect_event_receipts(
    recent_events: Any, *, known_channels: set[str] | None = None
) -> list[dict[str, Any]]:
    """Expose only bounded event identifiers, ages, and known channel deltas."""
    result = []
    if not isinstance(recent_events, (list, tuple)):
        return result
    for row in recent_events[-5:]:
        if not isinstance(row, dict):
            continue
        event_type = re.sub(
            r"[^a-z0-9_.-]", "_", str(row.get("event_type") or "event").strip().casefold()
        )[:48] or "event"
        source = re.sub(
            r"[^a-z0-9_.-]", "_", str(row.get("source") or "unspecified").strip().casefold()
        )[:48] or "unspecified"
        try:
            if row.get("timestamp") is not None:
                age_seconds = max(0.0, time.time() - float(row.get("timestamp")))
            elif row.get("age_seconds") is not None:
                age_seconds = max(0.0, float(row.get("age_seconds")))
            else:
                age_seconds = None
            if age_seconds is not None and not math.isfinite(age_seconds):
                age_seconds = None
        except (TypeError, ValueError, OverflowError):
            age_seconds = None
        raw_changes = row.get("changes") if isinstance(row.get("changes"), dict) else {}
        changes = {}
        for raw_name, raw_delta in raw_changes.items():
            name = str(raw_name).casefold()
            if not re.fullmatch(r"[a-z][a-z0-9_]{0,47}", name):
                continue
            if known_channels is not None and name not in known_channels:
                continue
            try:
                delta = float(raw_delta)
            except (TypeError, ValueError, OverflowError):
                continue
            if math.isfinite(delta):
                changes[name] = max(-1.0, min(1.0, delta))
        raw_baselines = row.get("baseline_changes") if isinstance(row.get("baseline_changes"), dict) else {}
        baseline_changes = {}
        for raw_name, raw_delta in raw_baselines.items():
            name = str(raw_name).casefold()
            if not re.fullmatch(r"[a-z][a-z0-9_]{0,47}", name):
                continue
            if known_channels is not None and name not in known_channels:
                continue
            try:
                delta = float(raw_delta)
            except (TypeError, ValueError, OverflowError):
                continue
            if math.isfinite(delta):
                baseline_changes[name] = max(-1.0, min(1.0, delta))
        result.append({
            "event_type": event_type,
            "source": source,
            "turn_id": re.sub(
                r"[^A-Za-z0-9_-]", "_", str(row.get("turn_id") or "").strip()
            )[:96] or None,
            "age_seconds": round(age_seconds, 1) if age_seconds is not None else None,
            "changes": changes,
            "baseline_changes": baseline_changes,
            "cause_context": {
                "drive": str(row.get("cause_context", {}).get("drive") or "").casefold()
            } if isinstance(row.get("cause_context"), dict)
            and re.fullmatch(r"[a-z0-9_]{1,32}", str(row.get("cause_context", {}).get("drive") or "").casefold())
            else {},
        })
    return result


def _is_audit_trace_followup(normalized_text: str) -> bool:
    """Recognize a prior-turn audit reference by its discourse and subject."""
    prior_reference = bool(re.search(
        r"\b(?:précédent(?:e)?|précédemment|dernier|dernière|"
        r"viens\s+de\s+(?:te\s+)?demander|tour\s+précédent|"
        r"previous|earlier|last\s+(?:test|turn)|just\s+asked)\b",
        normalized_text,
    ))
    audit_subject = bool(re.search(
        r"\b(?:audit|trace|compteurs?|ticks?|exécution|execution|"
        r"modules?|initialisés?|instrumentation)\b",
        normalized_text,
    ))
    return prior_reference and audit_subject


def is_cognitive_trace_query(user_input: str) -> bool:
    """Detect questions about the UI's displayed Cognitive Trace snapshot."""
    text = " ".join(str(user_input or "").casefold().split())
    mentions_trace = bool(re.search(
        r"\b(?:cognitive\s+trace|trace\s+(?:cognitive|affichée?|visible)|"
        r"trace\s+displayed|trace\s+shown)\b", text,
    ))
    asks_analysis = bool(re.search(
        r"\b(?:analy[sz](?:e|ing|is)|analys(?:e|er|ons|er uniquement)|audit|preuve|causal|"
        r"exécut(?:ion|é|ée|és|ées)|completed|last\s+outcome|"
        r"résultat|effet|attribut|tour|message)\b", text,
    ))
    return mentions_trace and asks_analysis


def sanitize_displayed_cognitive_trace(value: Any) -> Dict[str, Any] | None:
    """Keep only bounded, display-level fields from the browser trace snapshot."""
    if not isinstance(value, dict):
        return None

    def text(item: Any, limit: int) -> str:
        return str(item or "").replace("\x00", "")[:limit]

    def number(item: Any, *, integer: bool = False) -> int | float | None:
        try:
            result = float(item)
            if result != result or result in (float("inf"), float("-inf")):
                return None
            result = max(0.0, min(1e12, result))
            return int(result) if integer else result
        except (TypeError, ValueError, OverflowError):
            return None

    sanitized: Dict[str, Any] = {"captured_at": number(value.get("captured_at"))}
    goals = value.get("active_goals")
    sanitized["active_goals"] = []
    if isinstance(goals, list):
        for goal in goals[:4]:
            if not isinstance(goal, dict):
                continue
            sanitized["active_goals"].append({
                "id": text(goal.get("id"), 80),
                "topic": text(goal.get("topic"), 120),
                "origin": text(goal.get("origin"), 40),
                "activation": number(goal.get("activation")),
                "energy": number(goal.get("energy")),
            })

    def sanitize_goal_plan(item: Any) -> Dict[str, Any] | None:
        if not isinstance(item, dict):
            return None
        outcome = item.get("last_outcome")
        outcome = outcome if isinstance(outcome, dict) else {}
        return {
            "goal_topic": text(item.get("goal_topic"), 120),
            "objective": text(item.get("objective"), 160),
            "status": text(item.get("status"), 24),
            "source_id": text(item.get("source_id"), 80),
            "steps_completed": number(item.get("steps_completed"), integer=True),
            "steps_total": number(item.get("steps_total"), integer=True),
            "next_operation": text(item.get("next_operation"), 80),
            "next_operation_status": text(item.get("next_operation_status"), 24),
            "next_operation_result": text(item.get("next_operation_result"), 200),
            "decision_summary": text(item.get("decision_summary"), 300),
            "last_outcome": {
                "operation": text(outcome.get("operation"), 80),
                "success": outcome.get("success") if isinstance(outcome.get("success"), bool) else None,
                "status": text(outcome.get("status"), 24),
                "result": text(outcome.get("result"), 200),
                "observed_at": number(outcome.get("observed_at")),
                "effect_measured": outcome.get("effect_measured") if isinstance(outcome.get("effect_measured"), bool) else None,
            } if outcome else None,
        }

    raw_goal_plans = value.get("active_goal_plans")
    if not isinstance(raw_goal_plans, list):
        legacy_plan = value.get("active_goal_plan")
        raw_goal_plans = [legacy_plan] if isinstance(legacy_plan, dict) else []
    sanitized["active_goal_plans"] = [
        goal_plan for item in raw_goal_plans[:4]
        if (goal_plan := sanitize_goal_plan(item)) is not None
    ]
    sanitized["active_goal_plan"] = (
        sanitized["active_goal_plans"][0]
        if sanitized["active_goal_plans"] else None
    )

    aspiration = value.get("background_aspiration")
    if isinstance(aspiration, dict):
        outcome = aspiration.get("last_outcome")
        outcome = outcome if isinstance(outcome, dict) else {}
        completed = aspiration.get("completed_operations")
        sanitized["background_aspiration"] = {
            "objective": text(aspiration.get("objective"), 160),
            "status": text(aspiration.get("status"), 24),
            "steps_completed": number(aspiration.get("steps_completed"), integer=True),
            "steps_total": number(aspiration.get("steps_total"), integer=True),
            "completed_operations": [
                text(item, 80) for item in completed[:8]
            ] if isinstance(completed, list) else [],
            "next_operation": text(aspiration.get("next_operation"), 80),
            "next_operation_status": text(aspiration.get("next_operation_status"), 24),
            "reasoning_confidence": number(aspiration.get("reasoning_confidence")),
            "decision_summary": text(aspiration.get("decision_summary"), 300),
            "decision_updated_at": number(aspiration.get("decision_updated_at")),
            "last_outcome": {
                "operation": text(outcome.get("operation"), 80),
                "success": outcome.get("success") if isinstance(outcome.get("success"), bool) else None,
                "status": text(outcome.get("status"), 24),
                "result": text(outcome.get("result"), 200),
                "observed_at": number(outcome.get("observed_at")),
            } if outcome else None,
        }
    else:
        sanitized["background_aspiration"] = None

    plan = value.get("dominant_plan")
    if not isinstance(plan, dict):
        sanitized["dominant_plan"] = None
        return sanitized
    completed = plan.get("completed_operations")
    completed = (
        [text(operation, 80) for operation in completed[:8]]
        if isinstance(completed, list) else []
    )
    outcome = plan.get("last_outcome")
    outcome = outcome if isinstance(outcome, dict) else {}
    sanitized["dominant_plan"] = {
        "objective": text(plan.get("objective"), 160),
        "status": text(plan.get("status"), 24),
        "source": text(plan.get("source"), 24),
        "selection_basis": text(plan.get("selection_basis"), 64),
        "next_operation_dispatch_path": text(plan.get("next_operation_dispatch_path"), 48),
        "steps_completed": number(plan.get("steps_completed"), integer=True),
        "steps_total": number(plan.get("steps_total"), integer=True),
        "completed_operations": completed,
        "next_operation": text(plan.get("next_operation"), 80),
        "next_operation_status": text(plan.get("next_operation_status"), 24),
        "next_operation_result": text(plan.get("next_operation_result"), 200),
        "reasoning_confidence": number(plan.get("reasoning_confidence")),
        "uncertainties": [
            text(item, 160) for item in plan.get("uncertainties", [])[:3]
        ] if isinstance(plan.get("uncertainties"), list) else [],
        "decision_summary": text(plan.get("decision_summary"), 300),
        "decision_revision": number(plan.get("decision_revision"), integer=True),
        "decision_updated_at": number(plan.get("decision_updated_at")),
        "last_outcome": {
            "operation": text(outcome.get("operation"), 80),
            "success": outcome.get("success") if isinstance(outcome.get("success"), bool) else None,
            "status": text(outcome.get("status"), 24),
            "result": text(outcome.get("result"), 200),
            "observed_at": number(outcome.get("observed_at")),
            "effect_measured": outcome.get("effect_measured") if isinstance(outcome.get("effect_measured"), bool) else None,
        } if outcome else None,
    }
    return sanitized


def trace_grounded_architecture_answer(
    user_input: str,
    trace: Dict[str, Any],
    displayed_cognitive_trace: Dict[str, Any] | None = None,
    prior_exchange_evidence: Dict[str, Any] | None = None,
) -> str:
    """Summarize only architecture evidence recorded for the current turn.

    Runtime traces prove stage execution, not semantic correctness or a
    component's purpose. Architecture answers therefore use observed stage
    names and statuses, and explicitly state that limit.
    """
    stages = trace.get("stages", {}) if isinstance(trace, dict) else {}
    context_sources = trace.get("context_sources", {}) if isinstance(trace, dict) else {}
    normalized = " ".join(str(user_input or "").casefold().split())
    manifest = context_sources.get("module_tick_manifest", {}) if isinstance(context_sources, dict) else {}
    if is_runtime_execution_evidence_query(user_input):
        selected_stages = (
            "turn_input", "input_safety", "self_description_context",
            "memory_retrieval", "cognitive_prompt_context", "prompt_assembly",
            "primary_generation", "provider_completion", "response_finalization",
            "response_learning_and_memory", "organism_post_interaction",
        )
        observed_stages = []
        if isinstance(stages, dict):
            for name in selected_stages:
                value = stages.get(name)
                status = value.get("status") if isinstance(value, dict) else None
                if status:
                    observed_stages.append(f"{name}={status}")
        french = bool(re.search(
            r"\b(?:quels?|quelle|que|prouve|prouver|montre|montrer|enregistr|exécution|ce tour|le manifeste)\b",
            normalized,
        ))
        manifest_text = ""
        if isinstance(manifest, dict) and manifest.get("status") == "injected":
            manifest_text = (
                f" Module manifest: {int(manifest.get('observed_count', 0) or 0)} of "
                f"{int(manifest.get('module_count', 0) or 0)} registered modules had observed ticks, "
                f"{int(manifest.get('tick_count', 0) or 0)} ticks, "
                f"{int(manifest.get('error_count', 0) or 0)} instrumented errors."
            )
        else:
            manifest_text = " No usable module-tick manifest was recorded for this turn."
        stage_text = ", ".join(observed_stages) if observed_stages else "no selected stage receipt"
        if french:
            return (
                f"Reçu du tour courant : étapes explicitement enregistrées — {stage_text}.{manifest_text} "
                "Cela prouve seulement que l’instrumentation a observé ces passages. Cela ne prouve ni la justesse "
                "sémantique de la réponse, ni la qualité cognitive des modules, ni un effet aval correct. "
                "Un module initialisé sans tick observé n’est pas la preuve qu’aucun de son code n’a tourné."
            )
        return (
            f"Current-turn receipt: explicitly recorded stages — {stage_text}.{manifest_text} "
            "This proves only that instrumentation observed those paths. It does not prove semantic answer accuracy, "
            "cognitive quality, or a correct downstream effect. A module initialized without an observed tick is not "
            "proof that none of its code ran."
        )
    if is_cognitive_trace_query(user_input):
        snapshot = displayed_cognitive_trace if isinstance(displayed_cognitive_trace, dict) else None
        plan = snapshot.get("dominant_plan") if snapshot else None
        active_goal_plans = snapshot.get("active_goal_plans") if snapshot else None
        if not isinstance(active_goal_plans, list):
            legacy_goal_plan = snapshot.get("active_goal_plan") if snapshot else None
            active_goal_plans = [legacy_goal_plan] if isinstance(legacy_goal_plan, dict) else []
        active_goal_plan = active_goal_plans[0] if active_goal_plans else None
        goals = snapshot.get("active_goals") if snapshot else None
        french = bool(re.search(r"\b(?:quels?|quelle|affichée?|preuve|tour|échec|étapes?)\b", normalized))
        if not snapshot:
            return (
                "Je n’ai pas reçu le snapshot Cognitive Trace affiché par l’interface. "
                "Je ne peux donc pas en déduire les étapes terminées, le dernier résultat ni leur lien avec ce tour."
                if french else
                "I did not receive the Cognitive Trace snapshot shown by the interface, so I cannot report its completed steps, last outcome, or link to this turn."
            )
        if not isinstance(plan, dict) and isinstance(active_goal_plan, dict):
            active_summaries = []
            for goal_plan in active_goal_plans[:4]:
                if not isinstance(goal_plan, dict):
                    continue
                objective = str(goal_plan.get("objective") or "objectif absent")[:100]
                progress = f"{_safe_int(goal_plan.get('steps_completed'))}/{_safe_int(goal_plan.get('steps_total'))}"
                next_operation = str(goal_plan.get("next_operation") or "aucune")[:60]
                next_status = str(goal_plan.get("next_operation_status") or "inconnu")[:20]
                active_summaries.append(f"{objective} {progress}, prochaine étape {next_operation} ({next_status})")
            active_summary = "; ".join(active_summaries)
            if french:
                return (
                    f"Faits du snapshot UI transmis : aucun plan d’aspiration enregistré; plans liés aux objectifs actifs : {active_summary}. "
                    "Le panneau ne fournit ni identifiant de tour lié à cette étape, ni journal par module; il ne prouve donc pas son exécution pendant le tour affiché."
                )
            return (
                f"Displayed snapshot facts: no persistent aspiration plan; active-goal plans: {active_summary}. The panel has no turn-linked step ID or per-module journal, "
                "so it does not prove execution during the displayed turn."
            )
        if not isinstance(plan, dict):
            return (
                "Faits affichés : aucun plan dominant n’est présent dans ce snapshot. "
                "La trace UI ne fournit donc ni étape terminée ni dernier résultat de plan à attribuer. "
                "Elle ne contient pas de journal d’exécution par module permettant d’établir un lien causal avec ce tour."
                if french else
                "Displayed facts: this snapshot has no dominant plan. It therefore provides no completed plan step or last plan outcome to attribute. The UI trace contains no per-module execution journal establishing causality with this turn."
            )

        objective = str(plan.get("objective") or "(objectif absent)")[:160]
        completed = plan.get("completed_operations")
        completed = [str(item)[:80] for item in completed[:8]] if isinstance(completed, list) else []
        total = _safe_int(plan.get("steps_total"))
        steps_done = _safe_int(plan.get("steps_completed"))
        next_operation = str(plan.get("next_operation") or "aucune")[:80]
        next_operation_status = str(plan.get("next_operation_status") or "inconnu")[:24]
        outcome = plan.get("last_outcome") if isinstance(plan.get("last_outcome"), dict) else {}
        outcome_operation = str(outcome.get("operation") or "opération non précisée")[:80]
        outcome_result = str(outcome.get("result") or "détail absent")[:200]
        outcome_status = str(outcome.get("status") or (
            "échec" if outcome.get("success") is False
            else "succès" if outcome.get("success") is True
            else "statut absent"
        ))[:24]
        persistent_plan_note = (
            (
                " Le plan affiché est une aspiration persistante de fond, pas la preuve d’un travail effectué pendant ce tour."
                if french else
                " The displayed plan is a persistent background aspiration, not evidence of work on this chat turn."
            ) if plan.get("source") == "aspiration" else ""
        )
        if active_goal_plans:
            plan_summaries = []
            for goal_plan in active_goal_plans[:4]:
                if not isinstance(goal_plan, dict):
                    continue
                objective = str(goal_plan.get("objective") or "objective absent")[:100]
                progress = f"{_safe_int(goal_plan.get('steps_completed'))}/{_safe_int(goal_plan.get('steps_total'))}"
                next_action = str(goal_plan.get("next_operation") or "none")[:60]
                plan_summaries.append(f"{objective} ({progress}; {next_action})")
            joined_plans = "; ".join(plan_summaries)
            active_plan_note = (
                f" Plans liés aux objectifs actifs : {joined_plans}."
                if french else f" Active-goal plans: {joined_plans}."
            )
        else:
            active_plan_note = (
                " Aucun plan n’est actuellement lié à un objectif actif."
                if french else " No plan is currently linked to an active goal."
            )
        effect_note = (
            " effet mesuré" if outcome.get("effect_measured") is True
            else " effet non mesuré" if outcome.get("effect_measured") is False
            else ""
        )
        captured_at = snapshot.get("captured_at")
        capture_note = ""
        try:
            age = max(0.0, time.time() - float(captured_at))
            capture_note = f" Snapshot capturé il y a {age:.0f} s." if french else f" Snapshot captured {age:.0f}s ago."
        except (TypeError, ValueError):
            pass
        if french:
            goal_count = len(goals) if isinstance(goals, list) else 0
            complete_text = ", ".join(completed) if completed else "aucune"
            outcome_time = outcome.get("observed_at")
            time_note = ""
            try:
                time_note = f" (horodaté {float(outcome_time):.0f})"
            except (TypeError, ValueError):
                pass
            return (
                f"Faits du snapshot UI transmis : {goal_count} objectif(s) actif(s); plan « {objective} », "
                f"progression {steps_done}/{total}, étapes terminées : {complete_text}, "
                f"prochaine opération : {next_operation} (état : {next_operation_status}). "
                f"Dernier résultat enregistré : {outcome_operation} — {outcome_status}{effect_note} — {outcome_result}{time_note}.{capture_note} "
                "Cela décrit l’état affiché du plan; « aucune » signifie qu’aucune étape n’est marquée terminée. "
                f"{active_plan_note}{persistent_plan_note} Aucun composant ne peut être confirmé comme exécuté pendant le tour à partir de ce panneau seul. "
                "Le snapshot ne fournit pas d’identifiant reliant ce résultat au message analysé, ni de journal par module : "
                "je ne peux donc pas établir que l’échec a été causé par ce tour ou vérifier indépendamment l’effet de l’opération."
            )
        complete_text = ", ".join(completed) if completed else "none"
        effect_note = (
            " effect measured" if outcome.get("effect_measured") is True
            else " effect not measured" if outcome.get("effect_measured") is False
            else ""
        )
        return (
            f"Facts in the transmitted UI snapshot: plan '{objective}', progress {steps_done}/{total}, "
            f"completed steps: {complete_text}, next operation: {next_operation} "
            f"(status: {next_operation_status}). "
            f"Last recorded outcome: {outcome_operation} — {outcome_status}{effect_note} — {outcome_result}.{capture_note} "
            f"This is displayed planner state; 'none' means no step is marked completed.{active_plan_note}{persistent_plan_note} The snapshot has no identifier "
            "linking that outcome to the message being analyzed and no per-module execution journal, so no component execution "
            "can be confirmed for this turn from this panel alone, and I cannot attribute the failure to this turn or independently verify the operation's effect."
        )

    french = bool(re.search(
        r"\b(?:le|la|les|des|du|est|sont|explique|précisément|permettent|conclure|observé|exécuté)\b",
        normalized,
    ))
    module_tick_question = bool(
        (
            re.search(r"\bmodules?\b", normalized)
            and re.search(r"\b(?:tick|exécut|observ|initialis|indisponible|compteur)", normalized)
        )
        or _is_audit_trace_followup(normalized)
    )
    prior_result_question = bool(re.search(
        r"\b(?:rappelle(?:-moi)?|précédent(?:e)?|précédemment|avant|juste avant|"
        r"dernier test|test précédent|résultat vérifié|previous(?:ly)?|earlier|"
        r"just before|last test|prior result|tour précédent|viens de demander)\b",
        normalized,
    ))
    if module_tick_question and prior_result_question:
        prior = prior_exchange_evidence if isinstance(prior_exchange_evidence, dict) else {}
        prior_text = str(prior.get("text") or "").strip()
        if prior_text:
            linked = bool(prior.get("trace_linked"))
            french = french or any(
                marker in normalized
                for marker in ("rappelle", "résultat", "précédent", "juste avant", "exécution")
            )
            if french:
                linkage = (
                    f"Cette réponse est liée au tour {str(prior.get('turn_id') or '')[:100]} terminé. "
                    if linked else
                    "Je retrouve cette réponse dans l’historique, mais je ne peux pas la relier à une trace de tour conservée. "
                )
                current = (
                    f"La trace de CE tour indique {int(manifest.get('observed_count', 0) or 0)} module(s) avec tick observé, "
                    f"{int(manifest.get('tick_count', 0) or 0)} ticks et {int(manifest.get('error_count', 0) or 0)} erreur(s) instrumentée(s). "
                    "Cela ne mesure ni la qualité sémantique des sorties ni l’effet aval."
                    if isinstance(manifest, dict) and manifest.get("status") == "injected" else
                    "Aucun manifeste de ticks exploitable n’est présent dans la trace de ce tour."
                )
                return (
                    f"Réponse du tour précédent : « {prior_text} » {linkage}"
                    f"{current} « Initialisé sans tick observé » ne prouve pas l’absence d’exécution; "
                    "et un tick ne prouve pas à lui seul un résultat cognitif correct."
                )
            linkage = (
                f"This answer is linked to completed turn {str(prior.get('turn_id') or '')[:100]}. "
                if linked else
                "I found this answer in history but cannot link it to a retained turn trace. "
            )
            current = (
                f"This turn's trace records {int(manifest.get('observed_count', 0) or 0)} modules with observed ticks, "
                f"{int(manifest.get('tick_count', 0) or 0)} ticks, and {int(manifest.get('error_count', 0) or 0)} instrumented errors. "
                "That does not measure semantic output quality or downstream effect."
                if isinstance(manifest, dict) and manifest.get("status") == "injected" else
                "This turn has no usable tick manifest."
            )
            return (
                f"Previous-turn answer: ‘{prior_text}’ {linkage}{current} "
                "An initialized module with no observed tick is not proof that no code ran; a tick alone does not prove a correct cognitive result."
            )
        return (
            "Je n’ai pas de réponse précédente disponible à relier à cette question. "
            "La trace actuelle ne peut pas reconstituer le résultat du test précédent; elle décrit uniquement les ticks observés pour ce tour."
            if french else
            "I have no previous answer available to link to this question. The current trace cannot reconstruct the prior test result; it reports only ticks observed for this turn."
        )
    if module_tick_question and (
        not isinstance(manifest, dict)
        or manifest.get("status") != "injected"
        or int(manifest.get("module_count", 0) or 0) <= 0
    ):
        return (
            "Je ne peux pas confirmer ces compteurs à partir de la trace de ce tour : "
            "aucun manifeste de ticks non vide n’y est disponible. Les chiffres cités dans la question "
            "ne deviennent pas des observations du processus. Il faut une trace runtime instrumentée "
            "pour distinguer modules tickés, initialisés sans tick observé et indisponibles."
        )
    if module_tick_question and isinstance(manifest, dict) and manifest.get("status") == "injected":
        module_count = int(manifest.get("module_count", 0) or 0)
        observed_count = int(manifest.get("observed_count", 0) or 0)
        tick_count = int(manifest.get("tick_count", 0) or 0)
        error_count = int(manifest.get("error_count", 0) or 0)
        initialized_unobserved = int(manifest.get("initialized_unobserved_count", 0) or 0)
        unavailable = int(manifest.get("unavailable_count", 0) or 0)
        french = bool(re.search(r"\b(?:le|la|les|des|du|est|sont|explique|précisément|permettent|conclure|observé|exécuté|modules?)\b", normalized))
        if french:
            return (
                f"Le manifeste de ce processus recense {module_count} modules : {observed_count} avec au moins un tick observé, "
                f"{tick_count} ticks et {error_count} erreurs instrumentées; {initialized_unobserved} sont initialisés sans tick observé "
                f"et {unavailable} sont indisponibles. Cela décrit uniquement ce que l’instrumentation a enregistré. "
                "`initialisé sans tick observé` ne prouve ni qu’aucun code du module n’a été exécuté, ni qu’il n’a produit aucun effet; "
                "`indisponible` décrit l’état du registre, pas nécessairement l’ensemble des fichiers Python. Ces compteurs ne valident pas la qualité cognitive des sorties."
            )
        return (
            f"This process manifest lists {module_count} modules: {observed_count} with at least one observed tick, "
            f"{tick_count} ticks and {error_count} instrumented errors; {initialized_unobserved} are initialized with no observed tick "
            f"and {unavailable} are unavailable. This reports only what instrumentation recorded. "
            "`initialized with no observed tick` does not prove that no code in the module ran or had side effects; "
            "`unavailable` describes the registry state, not necessarily every Python file. These counters do not validate the cognitive quality of outputs."
        )
    observed: list[str] = []

    for name in ("self_description_context", "prompt_assembly"):
        stage = stages.get(name) if isinstance(stages, dict) else None
        status = stage.get("status") if isinstance(stage, dict) else None
        if status:
            observed.append(f"`{name}={status}`")

    if isinstance(context_sources, dict):
        manifest = context_sources.get("module_tick_manifest")
        if isinstance(manifest, dict) and manifest.get("status"):
            observed.append(f"`module_tick_manifest={manifest['status']}`")

    generation = None
    if isinstance(stages, dict):
        for name in ("primary_generation", "fast_first_pass", "deterministic_reasoning"):
            stage = stages.get(name)
            if isinstance(stage, dict) and stage.get("status") in {
                "completed", "selected_direct", "delegated", "selected",
            }:
                generation = f"`{name}={stage['status']}`"
                break
    if generation:
        observed.append(generation)

    evidence = ", ".join(observed) if observed else "aucune étape d’architecture exploitable n’est enregistrée pour ce tour"
    french = bool(re.search(r"\b(?:comment|quels?|quelle|décris|décrire|harnais|fonctionnement|étapes?)\b", normalized))
    if french:
        return (
            f"Pour ce tour, la trace enregistre : {evidence}. Cela prouve le passage par ces étapes, "
            "pas le rôle sémantique de modules ni la justesse du raisonnement. Le manifeste de ticks "
            "indique quels appels ont été observés; il ne vérifie pas leurs résultats."
        )
    return (
        f"For this turn, the trace records: {evidence}. This proves those stages were traversed, "
        "not the semantic role of modules or the correctness of the reasoning. The tick manifest "
        "shows which calls were observed; it does not validate their results."
    )


def _safe_int(value: Any) -> int:
    try:
        return max(0, min(10000, int(value or 0)))
    except (TypeError, ValueError, OverflowError):
        return 0


@dataclass
class ComponentDesc:
    name: str
    module_path: str
    role: str
    key_parameters: Dict[str, Any]
    last_hash: str = ""
    notes: str = ""


class SelfDescription:
    def __init__(self, path: str = "data/persona/self_description.json") -> None:
        self._path = Path(path)
        self._lock = Lock()
        self.components: Dict[str, ComponentDesc] = {}
        self.last_updated: float = 0.0
        self._drift_events: list = []
        self._load()
        logger.info("[SelfDescription] initialised")

    def register_or_update(self, name: str, module_path: str, role: str,
                            key_parameters: Dict[str, Any], notes: str = "") -> bool:
        """Returns True if this registration is a genuine drift (params
        changed since the last registration of this component), False
        for a first-time registration or an unchanged re-registration."""
        param_str = json.dumps(key_parameters, sort_keys=True, default=str)
        h = hashlib.sha256(param_str.encode()).hexdigest()[:12]
        drifted = False
        with self._lock:
            prior = self.components.get(name)
            if prior is not None and prior.last_hash != h:
                drifted = True
                self._drift_events.append({
                    "t": time.time(), "component": name,
                    "old_hash": prior.last_hash, "new_hash": h,
                })
                self._drift_events = self._drift_events[-500:]
            self.components[name] = ComponentDesc(
                name=name, module_path=module_path, role=role,
                key_parameters=key_parameters, last_hash=h, notes=notes,
            )
            self.last_updated = time.time()
        self._save()
        return drifted

    def as_natural_language(self) -> str:
        lines = [
            "Verified architecture registry (partial; only registered components are listed).",
            "Treat these entries as evidence about named components and parameters, not as a complete inventory.",
            "Treat each role as the full verified scope; do not broaden conditional modules or infer unlisted inputs, probabilities, equations, or causal mechanisms.",
            "A turn trace proves recorded execution and supplied context, not why a sentence was generated. "
            "For a specific response's cause, use only linked prompt/output evidence; if absent, say the cause is unverified.",
        ]
        with self._lock:
            for c in self.components.values():
                lines.append(
                    f"- {c.name} ({c.module_path}): {c.role}. "
                    f"Observed configuration: {c.key_parameters}."
                )
        if len(lines) == 3:
            lines.append("- No architecture components are currently registered; do not infer details.")
        return "\n".join(lines)

    def prompt_context(
        self, module_tick_snapshot: Dict[str, Dict[str, Any]] | None = None,
    ) -> str:
        """Return a bounded, factual architecture block suitable for chat prompts."""
        with self._lock:
            components = list(self.components.values())
        if not components:
            lines = [
                "VERIFIED ARCHITECTURE: no components are registered in the self-description "
                "module. Do not infer particular mechanisms from an empty registry.",
                "A turn trace proves recorded execution and supplied context, not why a sentence was generated. "
                "For a specific response's cause, use only linked prompt/output evidence; if absent, say the cause is unverified.",
            ]
        else:
            lines = [
                "VERIFIED ARCHITECTURE (partial registry; this is not a complete process-flow audit):",
                "Use only the named roles/configuration below as verified self-description. "
                "Treat each role as the full verified scope: state its trigger, inputs, and effect only as listed. "
                "Do not broaden a conditional component into an always-active subsystem, infer unlisted inputs "
                "such as confidence/emotion/anticipation, or describe a bounded score multiplier as a probability. "
                "Do not invent equations, physical sensations, or unlisted mechanisms.",
                "A turn trace proves recorded execution and supplied context, not why a sentence was generated. "
                "For a specific response's cause, use only linked prompt/output evidence; if absent, say the cause is unverified.",
            ]
            for component in components[:12]:
                lines.append(
                    f"- {component.name} [{component.module_path}]: {component.role}; "
                    f"configuration={component.key_parameters}."
                )
            if len(components) > 12:
                lines.append(f"- {len(components) - 12} additional registered components omitted from this prompt block.")
        if module_tick_snapshot is not None:
            lines.extend([
                "RUNTIME MODULE TICK SNAPSHOT (this process since its latest start; not a full semantic audit):",
                "A tick proves the instrumented method returned without an observed exception. "
                "state=output_present_unvalidated means output shape was present, not that reasoning is correct; "
                "quality=empty or no_return_unverified means no usable value was returned. "
                "initialized_unobserved means no instrumented call was observed in this process window.",
            ])
            for name, entry in sorted(module_tick_snapshot.items()):
                if not isinstance(name, str) or not isinstance(entry, dict):
                    continue
                ticks = entry.get("tick_count", 0)
                errors = entry.get("error_count", 0)
                try:
                    ticks = max(0, int(ticks))
                except (TypeError, ValueError):
                    ticks = 0
                try:
                    errors = max(0, int(errors))
                except (TypeError, ValueError):
                    errors = 0
                state = str(entry.get("state", "unknown"))[:32]
                last_output = entry.get("last_output")
                quality = str(
                    last_output.get("quality", "not_observed")
                    if isinstance(last_output, dict) else "not_observed"
                )[:32]
                methods = entry.get("observed_methods", [])
                methods = ",".join(str(method)[:48] for method in methods[:4]) if isinstance(methods, list) else ""
                lines.append(
                    f"- {name}: state={state}; ticks={ticks}; errors={errors}; "
                    f"last_output_quality={quality}; observed_methods={methods or 'none'}."
                )
        return "\n".join(lines)

    def detect_drift(self, name: str, current_params: Dict[str, Any]) -> bool:
        param_str = json.dumps(current_params, sort_keys=True, default=str)
        h = hashlib.sha256(param_str.encode()).hexdigest()[:12]
        with self._lock:
            if name not in self.components:
                return True
            return h != self.components[name].last_hash

    def refreshed_prompt_context(
        self, module_tick_snapshot: Dict[str, Dict[str, Any]] | None = None,
    ) -> tuple[str, dict[str, int | str]]:
        """Refresh source-derived component roles before returning architecture context.

        The persisted registry may have been written by an older code version. A
        live architecture answer must use current source descriptions rather than
        waiting for a periodic internal-loop tick to refresh them.
        """
        drift_count = self.scan_known_components()
        with self._lock:
            component_count = len(self.components)
        return self.prompt_context(module_tick_snapshot), {
            "refresh_result": "refreshed",
            "registered_component_count": component_count,
            "parameter_drift_count": drift_count,
        }

    def recent_drift_events(self, limit: int = 20) -> list:
        with self._lock:
            return list(self._drift_events[-limit:])

    def scan_known_components(self) -> int:
        """
        Registers the real, current parameter values of every module
        built this session that exposes tunable module-level constants —
        not a generic/placeholder inventory. Returns the count of
        components that showed genuine drift since last scan (0 on a
        freshly-started process, since there's nothing to compare
        against yet — that's expected, not a bug).
        """
        drift_count = 0
        try:
            from cognition import internal_cognitive_state as ics
            if self.register_or_update(
                "InternalCognitiveState", "cognition/internal_cognitive_state.py",
                "On recursive-deliberation calls, records normalized epistemic pressure, its change, and prior-pressure prediction error. WorkspaceCompetition may add a bounded score bias only to active goals whose name/topic matches the self-regulatory goal set. It does not read confidence, emotion, or anticipation, and it does not bias every goal.",
                {"SELF_STATE_GOAL_WEIGHT": ics.SELF_STATE_GOAL_WEIGHT,
                 "MAX_INTERNAL_BIAS": ics.MAX_INTERNAL_BIAS,
                 "DELTA_SCALE": ics.DELTA_SCALE,
                 "ENABLED": ics.INTERNAL_STATE_PROJECTION_ENABLED},
            ):
                drift_count += 1
        except Exception as e:
            logger.debug(f"[SelfDescription] scan InternalCognitiveState failed: {e}")

        try:
            from cognition import epistemic_efficacy_model as eem
            if self.register_or_update(
                "EpistemicEfficacyModel", "cognition/epistemic_efficacy_model.py",
                "Tracks at most one pending prediction of epistemic-pressure drop, created only when resolve_uncertainty wins and its learned multiplier reaches the final focus. On a later cycle it compares predicted and observed pressure change and updates an effectiveness self-belief. The bounded confidence-derived multiplier scales that goal's score bias; it is not a calibrated success probability and does not score other goals.",
                {"PREDICTION_SCALE": eem.PREDICTION_SCALE,
                 "GOOD_PREDICTION_THRESHOLD": eem.GOOD_PREDICTION_THRESHOLD,
                 "MIN_MULTIPLIER": eem.MIN_MULTIPLIER, "MAX_MULTIPLIER": eem.MAX_MULTIPLIER},
            ):
                drift_count += 1
        except Exception as e:
            logger.debug(f"[SelfDescription] scan EpistemicEfficacyModel failed: {e}")

        try:
            from cognition import unified_revision_gateway as urg
            if self.register_or_update(
                "UnifiedRevisionGateway", "cognition/unified_revision_gateway.py",
                "Called only before applying eligible Liberty proposals to an existing personality trait or known goal priority (proposal confidence must exceed 0.6). It refuses protected/non-finite targets or clamps numeric values and step size, then logs the decision. It does not review chat answers or every cognitive update.",
                {"MAX_STEP": urg.MAX_STEP, "BOUNDS": urg.BOUNDS,
                 "PROTECTED_SUBSTRINGS": list(urg.PROTECTED_SUBSTRINGS)},
            ):
                drift_count += 1
        except Exception as e:
            logger.debug(f"[SelfDescription] scan UnifiedRevisionGateway failed: {e}")

        try:
            from cognition import symbol_system as ss
            if self.register_or_update(
                "SymbolSystem", "cognition/symbol_system.py",
                "Open symbol repertoire absorbing structured self-referential events",
                {"MIN_SIGNIFICANCE_TO_ABSORB": ss.MIN_SIGNIFICANCE_TO_ABSORB,
                 "MIN_CONFIDENCE_FOR_CANDIDATE": ss.MIN_CONFIDENCE_FOR_CANDIDATE},
            ):
                drift_count += 1
        except Exception as e:
            logger.debug(f"[SelfDescription] scan SymbolSystem failed: {e}")

        try:
            from cognition.global_workspace import GlobalWorkspace
            from cognition.workspace_competition import WorkspaceCompetition
            if self.register_or_update(
                "GlobalWorkspace", "cognition/global_workspace.py",
                "Shared cognitive state and broadcast buffer. update_state merges allowlisted fields; context_by_source retains each publisher's context values and the cognitive prompt receives these contributions with origins. The flat context map remains a compatibility view where same-key collisions show the latest value. record_uncertainty retains each open source with its type, module, reference, turn/cycle, question, evidence, salience, and status; resolving one record leaves peers unchanged. broadcast submits source/content/priority to a bounded buffer (default capacity 32, at most 4 items per source); recent semantic duplicates may be rejected and a full buffer may evict its lowest-priority item. WorkspaceCompetition writes the selected focus and up to three ranked candidates (including the winner) as active hypotheses. Publication is not automatic fan-out: consumers must explicitly read the appropriate Workspace API, or register a listener for broadcast items. Only outputs published through these interfaces, admitted by their gates, and later read by a consumer become available there. This does not establish universal access to every module output or calibrated confidence metadata on every broadcast.",
                {
                    "CAPACITY": GlobalWorkspace.CAPACITY,
                    "SOURCE_MAX": GlobalWorkspace.SOURCE_MAX,
                    "SIMILARITY_BLOCK": GlobalWorkspace.SIMILARITY_BLOCK,
                    "RECENCY_WINDOW": GlobalWorkspace.RECENCY_WINDOW,
                    "PRIORITY_OVERRIDE": GlobalWorkspace.PRIORITY_OVERRIDE,
                    "MAX_HYPOTHESES_TO_WORKSPACE": WorkspaceCompetition.MAX_HYPOTHESES_TO_WORKSPACE,
                },
            ):
                drift_count += 1
        except Exception as e:
            logger.debug(f"[SelfDescription] scan GlobalWorkspace failed: {e}")

        return drift_count

    # ── persistence ──────────────────────────────────────────────────────

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                payload = {"last_updated": self.last_updated,
                           "components": [asdict(c) for c in self.components.values()],
                           "drift_events": self._drift_events}
            self._path.write_text(json.dumps(payload, indent=2, default=str))
        except Exception as e:
            logger.debug(f"[SelfDescription] save failed (non-fatal): {e}")

    def _load(self) -> None:
        try:
            if not self._path.exists():
                return
            data = json.loads(self._path.read_text())
            self.last_updated = data.get("last_updated", 0.0)
            for c in data.get("components", []):
                self.components[c["name"]] = ComponentDesc(**c)
            self._drift_events = data.get("drift_events", [])
        except Exception as e:
            logger.warning(f"[SelfDescription] load failed (non-fatal): {e}")


_descriptions = {}


def get_self_description() -> SelfDescription:
    global _descriptions
    if "singleton" not in _descriptions:
        _descriptions["singleton"] = SelfDescription()
    return _descriptions["singleton"]

