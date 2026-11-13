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
import re
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from threading import Lock
from typing import Any, Dict

logger = logging.getLogger(__name__)


def is_architecture_query(user_input: str) -> bool:
    """Identify requests about Lumina's implementation, for evidence routing only.

    This does not answer the request or assign module facts; it only enables the
    live module-tick manifest to be added to the model's evidence context.
    """
    text = " ".join(str(user_input or "").casefold().split())
    if is_runtime_execution_evidence_query(text):
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


def is_runtime_execution_evidence_query(user_input: str) -> bool:
    """Identify questions asking what current runtime receipts establish.

    Keep this separate from displayed UI Cognitive Trace questions: runtime
    evidence comes from the current server-side turn receipt and module
    manifest, while the UI trace is a different, client-supplied snapshot.
    """
    text = " ".join(str(user_input or "").casefold().split())
    refers_to_receipt = bool(re.search(
        r"\b(?:cognitive\s+(?:execution|exécution)\s+trace|"
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


def is_self_affect_query(user_input: str) -> bool:
    """Identify a request to report Lumina's own modeled affect state.

    Audit prompts are often imperative ("report your current affect signal")
    rather than interrogative, so requiring a question word misses them.
    This only selects closed-world affect evidence; it does not prescribe an
    answer or classify general questions about emotion.
    """
    text = " ".join(str(user_input or "").casefold().split())
    mentions_affect = bool(re.search(
        r"\b(?:emotions?|émotions?|feelings?|sentiments?|affect|feel|feeling|sens)\b",
        text,
    ))
    refers_to_self = bool(re.search(
        r"\b(?:you|your|yourself|toi|tu|ton|ta|tes|lumina|me|moi|mon|ma|mes)\b",
        text,
    ))
    return mentions_affect and refers_to_self


def affect_self_report_context(
    profile: Any,
    description: str = "",
    latest_event: Any = None,
) -> str:
    """Format the live affect snapshot with source and similarly named-drive limits."""
    allowed_channels = (
        "curiosity", "warmth", "anxiety", "satisfaction", "frustration",
        "enthusiasm", "surprise", "sadness", "relief", "disappointment",
        "anticipation",
    )
    values = profile if isinstance(profile, dict) else {}
    rows = []
    for name in allowed_channels:
        try:
            value = float(values[name])
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        if value != value or value in (float("inf"), float("-inf")):
            continue
        rows.append(f"{name}={max(0.0, min(1.0, value)):.3f}")
    channel_text = ", ".join(rows) if rows else "unavailable"
    state_text = str(description or "unavailable").replace("\n", " ").strip()[:500]
    event = latest_event if isinstance(latest_event, dict) else {}
    event_type = str(event.get("event_type") or "").strip()[:80]
    event_source = str(event.get("source") or "").strip()[:80]
    event_age = event.get("age_seconds")
    if event_type or event_source:
        latest_text = f"{event_type or 'event'} from {event_source or 'unspecified source'}"
        try:
            latest_text += f", {max(0.0, float(event_age)):.1f}s ago"
        except (TypeError, ValueError, OverflowError):
            pass
    else:
        latest_text = "none recorded"
    return (
        "━━ AFFECT SELF-REPORT EVIDENCE ━━\n"
        "Source: EmotionalStateManager.get_response_modifiers().affective_profile; "
        "these are live modeled affect channels, each on a 0–1 scale.\n"
        f"Affect channels: {channel_text}\n"
        f"State description: {state_text}\n"
        f"Latest recorded affect-changing appraisal: {latest_text}.\n"
        "For this self-report, use only these affect-channel values. In particular, "
        "the CuriosityEngine/DecisionPressure `Curiosity Drive` elsewhere in cognitive "
        "telemetry is a separate motivation signal; do not substitute it for the "
        "EmotionalStateManager `curiosity` channel. Identify the source when giving "
        "numbers. The appraisal is the latest logged event, not necessarily the sole "
        "cause of the whole state. These computational signals do not establish human-like "
        "subjective experience. If the relevant value is unavailable here, say so."
    )


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
        goals = snapshot.get("active_goals") if snapshot else None
        french = bool(re.search(r"\b(?:quels?|quelle|affichée?|preuve|tour|échec|étapes?)\b", normalized))
        if not snapshot:
            return (
                "Je n’ai pas reçu le snapshot Cognitive Trace affiché par l’interface. "
                "Je ne peux donc pas en déduire les étapes terminées, le dernier résultat ni leur lien avec ce tour."
                if french else
                "I did not receive the Cognitive Trace snapshot shown by the interface, so I cannot report its completed steps, last outcome, or link to this turn."
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
                "Aucun composant ne peut être confirmé comme exécuté pendant le tour à partir de ce panneau seul. "
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
            "This is displayed planner state; 'none' means no step is marked completed. The snapshot has no identifier "
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
            "Do not invent internal mechanisms, equations, or causal explanations that are not listed here.",
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
                "state=healthy does not prove its result is correct; quality=empty means no value was returned. "
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
                "Bounded, continuous epistemic-pressure bias on self-regulatory goals",
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
                "Falsifiable self-prediction about resolve_uncertainty's effectiveness",
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
                "Safety wrapper on the live autonomous self-modification path",
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
