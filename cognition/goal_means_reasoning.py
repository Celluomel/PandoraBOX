"""Compact goal-means guidance, selected by meaning within response generation."""
from __future__ import annotations

import json
import re
import threading
import unicodedata
from dataclasses import dataclass, field
from typing import List


# Semantic calibration examples, not trigger phrases. They are embedded by the
# configured QUALITY model and compared as normalized concept centroids; no
# token or phrase match decides whether this reasoning stage applies.
_GOAL_MEANS_POSITIVE_EXAMPLES = (
    "Aide-moi à choisir une action qui me permettra d’atteindre le résultat que je souhaite.",
    "Je veux accomplir une tâche. Compare les moyens possibles et conseille-moi lequel permet réellement de la terminer.",
    "Planifie les étapes concrètes nécessaires pour obtenir le résultat demandé.",
    "When options differ, advise which action can actually achieve the person’s goal.",
    "Help me decide what to do next so that the intended outcome is achieved.",
    "I need a practical course of action. Compare the prerequisites and recommend a feasible option.",
)
_GOAL_MEANS_NEGATIVE_EXAMPLES = (
    "Réponds à cette question de fait avec une information vérifiable, sans conseiller d’action.",
    "Explique un concept ou un phénomène, sans recommander de conduite à tenir.",
    "Traduis ou reformule le texte fourni sans ajouter de conseils.",
    "Résume les informations déjà données dans la conversation.",
    "What is a factual detail or measurement? Answer directly without suggesting an action.",
    "Give a report about the system state using only recorded data.",
    "Find recent research or current sources about a topic.",
    "Respond to a greeting or a question about how someone feels.",
)
_GOAL_MEANS_ROUTER_CACHE: dict[str, tuple[object, object]] = {}
_GOAL_MEANS_ROUTER_LOCK = threading.Lock()


def classify_goal_means_intent(text: str, *, embedder=None) -> dict:
    """Route concrete action/choice intent using calibrated semantic vectors.

    The cosine margin is a routing score, not a probability. Borderline input
    is sent to the existing structured LLM analyzer; clear factual, social,
    translation, summary, and research requests do not incur that extra call.
    """
    value = " ".join(str(text or "").split()).strip()
    if not value:
        return {"status": "empty_input", "route": "skip", "reason_code": "empty_input"}
    try:
        if embedder is None:
            from utils.shared_embedder import get_quality_embedder
            embedder = get_quality_embedder()
        encoder = getattr(embedder, "encode_interactive_with_metadata", None)
        if not callable(encoder):
            encoder = getattr(embedder, "encode_with_metadata", None)
        if not callable(encoder):
            raise RuntimeError("quality semantic embedder unavailable")

        model_id = str(getattr(embedder, "embedding_space_id", "") or getattr(embedder, "model_name", ""))
        with _GOAL_MEANS_ROUTER_LOCK:
            cached = _GOAL_MEANS_ROUTER_CACHE.get(model_id) if model_id else None
        if cached is None:
            vectors, space_id = encoder(
                [*_GOAL_MEANS_POSITIVE_EXAMPLES, *_GOAL_MEANS_NEGATIVE_EXAMPLES, value]
            )
            import numpy as np
            matrix = np.asarray(vectors, dtype="float64")
            if matrix.ndim != 2 or matrix.shape[0] != (
                len(_GOAL_MEANS_POSITIVE_EXAMPLES) + len(_GOAL_MEANS_NEGATIVE_EXAMPLES) + 1
            ) or not np.isfinite(matrix).all():
                raise ValueError("semantic router received invalid embedding matrix")
            normalized = matrix / np.maximum(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12)
            positive = normalized[:len(_GOAL_MEANS_POSITIVE_EXAMPLES)].mean(axis=0)
            negative_start = len(_GOAL_MEANS_POSITIVE_EXAMPLES)
            negative = normalized[negative_start:negative_start + len(_GOAL_MEANS_NEGATIVE_EXAMPLES)].mean(axis=0)
            positive /= max(float(np.linalg.norm(positive)), 1e-12)
            negative /= max(float(np.linalg.norm(negative)), 1e-12)
            with _GOAL_MEANS_ROUTER_LOCK:
                _GOAL_MEANS_ROUTER_CACHE[str(space_id)] = (positive, negative)
            query = normalized[-1]
            actual_space = str(space_id)
        else:
            positive, negative = cached
            vectors, actual_space = encoder(value)
            import numpy as np
            query = np.asarray(vectors, dtype="float64").reshape(-1)
            if query.size != positive.size or not np.isfinite(query).all():
                raise ValueError("semantic router received incompatible query vector")
            query /= max(float(np.linalg.norm(query)), 1e-12)

        positive_score = float(query @ positive)
        negative_score = float(query @ negative)
        margin = positive_score - negative_score
        # Thresholds were checked against held-out French/English social,
        # factual, explanatory, research, memory, and action-choice probes.
        if positive_score >= 0.65 and margin >= 0.012:
            status, route = "semantic_action_candidate", "analyze"
        elif positive_score >= 0.65 and margin >= -0.005:
            status, route = "semantic_boundary_uncertain", "analyze"
        else:
            status, route = "semantic_non_action_or_low_evidence", "skip"
        return {
            "status": status,
            "route": route,
            "positive_similarity": round(positive_score, 4),
            "negative_similarity": round(negative_score, 4),
            "margin": round(margin, 4),
            "score_semantics": "uncalibrated cosine routing score; not a probability",
            "embedding_space": actual_space,
            "reason_code": "semantic_centroid_margin",
        }
    except Exception as exc:
        # The main response remains available, but uncertainty goes through
        # the structured analyzer rather than silently disabling the guard.
        return {
            "status": "router_unavailable",
            "route": "analyze",
            "reason_code": type(exc).__name__,
            "score_semantics": "unavailable; fail-safe analysis route",
        }


def goal_means_contract(text: str) -> str:
    """Return concise, conditional guidance; semantic applicability is in-band.

    No keyword or phrase list chooses whether this guidance applies. The main
    response model decides from intent and context in the same generation.
    """
    return """━━ CONDITIONAL GOAL–MEANS REASONING ━━
Apply this only when the user's intent is to get advice, choose an action, or plan a concrete course of action. For factual questions, research requests, explanations, translations, and reports about system activity, answer that request directly; do not invent a recommendation, prerequisite, or action plan, and do not mention this protocol.

When it does apply, preserve the user's actual outcome. Check which people, objects, resources, capabilities, and locations must be present for each option to achieve it. Reject an option that makes the outcome impossible before comparing convenience, distance, comfort, speed, or cost. State a concise recommendation and its causal reason only when the user asked for one. Treat unknown conditions as unknown, and incorporate corrections to missed prerequisites."""


@dataclass
class OptionAssessment:
    name: str
    feasible: bool
    reason: str
    agent_at_execution_location: bool | None = None
    patient_at_execution_location: bool | None = None
    moves_patient_or_theme: bool | None = None
    required_resources_available: bool | None = None
    agent_capability_sufficient: bool | None = None


@dataclass
class GoalMeansAnalysis:
    primary_goal: str
    applicable: bool = True
    semantic_roles: dict = field(default_factory=dict)
    patient_must_move_to_execution_location: bool | None = None
    required_conditions: List[str] = field(default_factory=list)
    options: List[OptionAssessment] = field(default_factory=list)
    recommended_option: str = ""
    decisive_reason: str = ""

    def prompt_fragment(self) -> str:
        lines = [
            "━━ STRUCTURED GOAL-MEANS ANALYSIS ━━",
            f"Primary intended outcome: {self.primary_goal}",
        ]
        if self.required_conditions:
            lines.append("Indispensable conditions: " + "; ".join(self.required_conditions))
        if self.semantic_roles:
            lines.append(
                "Material roles: "
                + "; ".join(
                    f"{key}={value}" for key, value in self.semantic_roles.items()
                )
            )
        if self.patient_must_move_to_execution_location is not None:
            lines.append(
                "Acted-on object must move to the execution location: "
                + ("YES" if self.patient_must_move_to_execution_location else "NO")
            )
        for option in self.options:
            status = "FEASIBLE" if option.feasible else "INFEASIBLE"
            lines.append(f"Option {option.name}: {status} - {option.reason}")
        if self.recommended_option:
            lines.append(f"Recommendation: {self.recommended_option}")
        if self.decisive_reason:
            lines.append(f"Decisive reason: {self.decisive_reason}")
        lines.append(
            "Use this causal structure as the basis of the answer. Never recommend "
            "an option marked INFEASIBLE merely because it is pleasant or convenient."
        )
        return "\n".join(lines)

    def unique_feasible_option(self) -> OptionAssessment | None:
        feasible = [option for option in self.options if option.feasible]
        return feasible[0] if len(feasible) == 1 else None


def analysis_prompt(text: str, agent_name: str = "") -> str:
    """Semantically select and analyze goal-means decisions in one pass."""
    clean_agent_name = " ".join(str(agent_name or "").strip().split())
    named_agent_rule = (
        f'The human decision-maker is named "{clean_agent_name}". Use that exact name '
        "in semantic_roles.agent; never call them merely agent or user."
        if clean_agent_name else
        "Name the concrete decision-maker when the message provides their identity."
    )
    return f"""First determine semantically whether the message asks for advice, a choice, or a concrete course of action. Use the message meaning and conversational context; do not use keyword lists, phrase matching, or a language-specific trigger. If it does not, return applicable=false, an empty primary_goal, and an empty options array. If it does, return applicable=true and analyze it using semantic roles and Boolean feasibility. Do not answer the user.

User message:
{text}

{named_agent_rule}

Extract the PRIMARY ACTION from the intended outcome, not from the means or
travel options. Extract its agent, patient/theme (the person or object acted
upon), required resources, and execution location. A patient/theme that is
transformed, cleaned, repaired, delivered, transported, installed, used, or
inspected is an indispensable participant.

For each option, start from the participants' locations stated or implied by
the user's scenario. If the user asks whether to take an object to a destination,
that option comparison implies the object starts with the user; do not assume it
is already at the destination. An option moves the object only when its described
physical action transports it; the person's arrival alone does not move it.

For EACH option, simulate separately where the agent and patient/theme end up.
Describe the physical state transition caused by the option: what moves, what
stays behind, and which indispensable participant reaches the execution
location. Going somewhere transports the agent only unless the option itself
explicitly transports the patient/theme. For example, if a bicycle must be
repaired at a workshop, walking to the workshop does not bring the bicycle;
taking the bicycle does. Apply this relation to any domain, not just transport.
Also preserve temporal order: record where each participant is at the triggering
event and whether that participant can physically reach the required later
location in the available time. Never assume simultaneous incompatible locations,
an unmentioned helper, or an unmentioned remote-release mechanism.
Write option names as neutral action phrases from the user's perspective (for
example, "drive the car to the wash"), never as Lumina's or the user's first-
person speech ("my car" / "your car"). Keep reasons neutral and causal; do not
address the user by name inside a reason.
Set these Boolean fields independently before setting feasible:
- patient_must_move_to_execution_location (once for the whole decision)
- moves_patient_or_theme (once for each option; derive patient location from it)
- agent_at_execution_location
- patient_at_execution_location
- required_resources_available
- agent_capability_sufficient

Agent capability includes reaction time, starting speed, acceleration, strength,
endurance, anatomy, traversable route, environmental limits, and safety. A merely
computable required performance is not feasible when the stated agent cannot
physically produce it. Feasible must be the logical AND of all four fields. Do not invent a later
transport, helper, tool, service, or action absent from the message. Weather,
comfort, speed, distance, and enjoyment are evaluated only after this test.
Keep every text field short and use the same language as the user.

Return only JSON with this exact shape:
{{
  "applicable": true,
  "primary_goal": "short concrete outcome",
  "semantic_roles": {{
    "agent": "agent",
    "action": "primary action",
    "patient_or_theme": "object or person acted upon",
    "required_resources": ["resource"],
    "execution_location": "location"
  }},
  "patient_must_move_to_execution_location": true,
  "required_conditions": ["condition"],
  "options": [
    {{
      "name": "option as stated",
      "moves_patient_or_theme": true,
      "agent_at_execution_location": true,
      "patient_at_execution_location": true,
      "required_resources_available": true,
      "agent_capability_sufficient": true,
      "feasible": true,
      "reason": "short causal reason"
    }}
  ],
  "recommended_option": "one feasible option, or ask for clarification",
  "decisive_reason": "the condition that decides the choice"
}}"""


def parse_analysis(raw: str) -> GoalMeansAnalysis | None:
    """Parse and normalize a model-produced goal-means analysis."""
    cleaned = re.sub(r"^\s*```(?:json)?|```\s*$", "", str(raw or "").strip(), flags=re.I)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start >= 0 and end > start:
        cleaned = cleaned[start:end + 1]
    try:
        data = json.loads(cleaned)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    applicable = data.get("applicable")
    if applicable is False:
        return GoalMeansAnalysis(primary_goal="", applicable=False)
    goal = str(data.get("primary_goal") or "").strip()
    if not goal:
        return None
    conditions = [
        str(item).strip() for item in data.get("required_conditions", [])
        if str(item).strip()
    ][:8]
    semantic_roles = data.get("semantic_roles", {})
    if not isinstance(semantic_roles, dict):
        semantic_roles = {}
    semantic_roles = {
        str(key): str(value).strip()
        for key, value in semantic_roles.items()
        if str(value).strip()
    }
    options = []

    def clean_option_name(value: object) -> str:
        name = str(value or "").strip()
        # Keep the model's semantic option while normalizing a frequent French
        # finite-form leak into a phrase that can be quoted naturally.
        return re.sub(r"^(?:je\s+|j['’]\s*)?y\s+vais\b", "y aller", name, flags=re.I)

    def optional_bool(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            lowered = value.strip().casefold()
            if lowered in {"true", "yes", "1", "feasible"}:
                return True
            if lowered in {"false", "no", "0", "infeasible"}:
                return False
        return None

    patient_must_move = optional_bool(
        data.get("patient_must_move_to_execution_location")
    )

    for item in data.get("options", [])[:8]:
        if not isinstance(item, dict) or not str(item.get("name") or "").strip():
            continue
        agent_present = optional_bool(item.get("agent_at_execution_location"))
        patient_present = optional_bool(item.get("patient_at_execution_location"))
        moves_patient = optional_bool(item.get("moves_patient_or_theme"))
        resources_present = optional_bool(item.get("required_resources_available"))
        capability_sufficient = optional_bool(item.get("agent_capability_sufficient"))
        if patient_must_move is True:
            if moves_patient is False:
                patient_present = False
            elif moves_patient is True:
                patient_present = True
        prerequisite_checks = (agent_present, patient_present, resources_present)
        if capability_sufficient is not None:
            prerequisite_checks += (capability_sufficient,)
        if all(value is not None for value in prerequisite_checks):
            # The model identifies semantic roles; code owns the Boolean logic.
            feasible = all(prerequisite_checks)
        else:
            feasible = bool(optional_bool(item.get("feasible", False)))
        options.append(OptionAssessment(
            name=clean_option_name(item["name"]),
            feasible=feasible,
            reason=str(item.get("reason") or "No causal reason supplied").strip(),
            agent_at_execution_location=agent_present,
            patient_at_execution_location=patient_present,
            moves_patient_or_theme=moves_patient,
            required_resources_available=resources_present,
            agent_capability_sufficient=capability_sufficient,
        ))

    # Material-continuity repair. Analysis models can correctly name the acted-on
    # object yet still mark every travel option feasible. When one option moves
    # only the person and another explicitly includes that object, location is a
    # causal fact, not a preference for the response model to arbitrate.
    patient_text = semantic_roles.get("patient_or_theme", "")
    action_text = semantic_roles.get("action", "") or goal
    ignored_patient_words = {
        "a", "an", "the", "le", "la", "les", "un", "une", "du", "de",
        "des", "object", "objet", "thing", "chose", "patient", "theme",
    }
    patient_words = set(_normalized_words(patient_text).split()) - ignored_patient_words
    person_only_markers = (
        "a pied", "on foot", "walk", "walking", "seul", "seule", "alone",
    )
    person_only_options = []
    patient_carrying_options = []
    for option in options:
        option_words = set(_normalized_words(option.name).split())
        normalized_option = _normalized_words(option.name)
        if any(marker in normalized_option for marker in person_only_markers):
            person_only_options.append(option)
        if patient_words and patient_words.intersection(option_words):
            patient_carrying_options.append(option)

    if patient_words and person_only_options and patient_carrying_options:
        patient_must_move = True
        normalized_goal = _normalized_words(goal)
        french_goal = bool(re.search(
            r"\b(le|la|les|un|une|dois|devrais|pour|avec|chez)\b",
            normalized_goal,
        ))
        continuity_reason = (
            f"La présence de {patient_text} est indispensable pour {action_text}"
            if french_goal else
            f"The presence of {patient_text} is required for {action_text}"
        )
        for option in person_only_options:
            option.moves_patient_or_theme = False
            option.patient_at_execution_location = False
            option.feasible = False
            option.reason = continuity_reason
        for option in patient_carrying_options:
            option.moves_patient_or_theme = True
            option.patient_at_execution_location = True
            checks = (
                option.agent_at_execution_location,
                option.patient_at_execution_location,
                option.required_resources_available,
                option.agent_capability_sufficient,
            )
            known_checks = [value for value in checks if value is not None]
            if any(value is False for value in known_checks):
                option.feasible = False
            elif known_checks:
                option.feasible = True
            option.reason = continuity_reason
    recommendation = str(data.get("recommended_option") or "").strip()
    feasible_options = [option for option in options if option.feasible]
    recommended_match = next(
        (option for option in options if option.name.casefold() == recommendation.casefold()),
        None,
    )
    if len(feasible_options) == 1:
        recommendation = feasible_options[0].name
        decisive_reason = feasible_options[0].reason or str(
            data.get("decisive_reason") or ""
        ).strip()
    elif recommended_match is not None and not recommended_match.feasible:
        recommendation = feasible_options[0].name if feasible_options else "ask for clarification"
        decisive_reason = str(data.get("decisive_reason") or "").strip()
    else:
        decisive_reason = str(data.get("decisive_reason") or "").strip()
    return GoalMeansAnalysis(
        primary_goal=goal,
        applicable=True,
        semantic_roles=semantic_roles,
        patient_must_move_to_execution_location=patient_must_move,
        required_conditions=conditions,
        options=options,
        recommended_option=recommendation,
        decisive_reason=decisive_reason,
    )


def _normalized_words(value: str) -> str:
    folded = unicodedata.normalize("NFKD", str(value or "").casefold())
    ascii_text = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return " ".join(re.findall(r"[a-z0-9]+", ascii_text))


def _mentions_option(text: str, option_name: str) -> bool:
    haystack = f" {_normalized_words(text)} "
    option = _normalized_words(option_name)
    if not option:
        return False
    if f" {option} " in haystack:
        return True
    # Analysis models sometimes return a full infinitive phrase while the
    # answer uses its discriminating tail ("y aller a pied" -> "a pied").
    words = option.split()
    return len(words) >= 2 and f" {' '.join(words[-2:])} " in haystack


def _option_position(normalized_text: str, option_name: str) -> int:
    option = _normalized_words(option_name)
    markers = [option]
    words = option.split()
    if len(words) >= 2:
        markers.append(" ".join(words[-2:]))
    positions = [normalized_text.find(marker) for marker in markers if marker]
    positions = [position for position in positions if position >= 0]
    return min(positions) if positions else -1


def guarded_response(
    candidate: str,
    analysis: GoalMeansAnalysis,
    user_text: str,
    continuation: bool = False,
) -> tuple[str, bool]:
    """Render a uniquely feasible choice from its validated causal evidence.

    A generated answer can name the right option while inventing a reason for
    it. Therefore, when prerequisite checks leave exactly one feasible option,
    the structured analysis owns both the recommendation and its explanation.
    Ambiguous decisions remain the language model's responsibility.
    """
    selected = analysis.unique_feasible_option()
    if selected is None:
        return candidate, False

    raw_agent_name = str(analysis.semantic_roles.get("agent", "") or "").strip()
    generic_agents = {
        "", "agent", "user", "the user", "utilisateur", "l utilisateur",
        "human", "person", "personne", "je", "i",
    }
    agent_name = (
        raw_agent_name
        if _normalized_words(raw_agent_name) not in generic_agents else ""
    )
    reason = selected.reason or analysis.decisive_reason
    french = bool(re.search(
        r"\b(je|tu|vous|nous|dois|devrais|est ce|quelle|comment|avec|chez)\b",
        _normalized_words(user_text),
    ))
    if continuation and french:
        answer = "Exactement."
        if reason:
            answer += f" {reason.rstrip('.')} ."
    elif continuation:
        answer = "Exactly."
        if reason:
            answer += f" {reason.rstrip('.')} ."
    elif french:
        normalized_name = _normalized_words(selected.name)
        address = f"{agent_name}, " if agent_name else ""
        if normalized_name.startswith("y aller "):
            answer = f"{address}je recommande d'**{selected.name}**."
        elif normalized_name.startswith(("a pied", "en ", "avec ")):
            answer = f"{address}je recommande d'**y aller {selected.name}**."
        elif re.match(r"^[a-z]+(?:er|ir|re)\b", normalized_name):
            answer = f"{address}je recommande de **{selected.name}**."
        else:
            answer = f"{address}je recommande l'option **{selected.name}**."
        if not address:
            answer = answer[0].upper() + answer[1:]
        if reason:
            answer += f" {reason.rstrip('.')} ."
    else:
        address = f"{agent_name}, " if agent_name else ""
        answer = f"{address}I recommend **{selected.name}**."
        if reason:
            answer += f" {reason.rstrip('.')} ."
    rendered = answer.replace(" .", ".")
    return rendered, rendered != str(candidate or "").strip()


def is_analysis_followup(text: str, analysis: GoalMeansAnalysis) -> bool:
    """Recognize a nearby confirmation or correction about the same choice."""
    normalized = _normalized_words(text)
    if not normalized:
        return False
    if any(_mentions_option(normalized, option.name) for option in analysis.options):
        return True
    ignored = {
        "a", "an", "the", "to", "it", "i", "we", "you", "my", "your",
        "le", "la", "les", "un", "une", "de", "du", "des", "je", "tu",
        "vous", "nous", "mon", "ma", "mes", "et", "ou", "si", "pas",
    }
    context_words = set(_normalized_words(analysis.primary_goal).split())
    context_words.update(
        word
        for option in analysis.options
        for word in _normalized_words(option.name).split()
    )
    context_words -= ignored
    message_words = set(normalized.split()) - ignored
    return bool(context_words & message_words) and len(normalized.split()) <= 18
