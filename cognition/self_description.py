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


def render_affect_self_report(evidence: str, *, language: str = "en") -> str:
    """Render a short social status answer from the injected live affect block.

    This is intentionally a deterministic projection of measured software
    channels. It avoids asking the chat model to invent subjective sensations
    or sending the same simple greeting through generation and review passes.
    """
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
            return "Je ne peux pas confirmer mon état affectif actuel : aucun signal affectif exploitable n’est disponible."
        return "I can’t confirm my current affective state because no usable affect signal is available."

    top = sorted(channels, key=lambda item: (-item[1], item[0]))[:2]
    if str(language).casefold().startswith("fr"):
        signal_text = " et ".join(f"{name} {value:.2f}" for name, value in top)
        return (
            f"Mon état fonctionnel modélisé est surtout marqué par {signal_text}. "
            "Ce sont des signaux calculés, pas des sensations humaines."
        )
    signal_text = " and ".join(f"{name} {value:.2f}" for name, value in top)
    return (
        f"My modeled functional state is currently led by {signal_text}. "
        "These are computed signals, not human sensations."
    )


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
            f"{event_report} Ce sont des signaux calculés, pas des sensations humaines."
        )
    event_report = (
        "No recent affect-changing appraisal is recorded."
        if no_event
        else f"Latest recorded appraisal: {event_text}. It does not establish the cause of the overall state."
    )
    return (
        f"Modeled affect channels (0–1 scale): {channel_text}. "
        f"{event_report} These are computed signals, not human sensations."
    )


def render_affect_change_analysis(evidence: str, *, language: str = "en") -> str:
    """Summarize logged channel deltas without inventing a causal narrative."""
    event_lines = re.findall(r"^Recorded affect event: (.+)$", evidence, re.MULTILINE)
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
    safe_events = sanitize_affect_event_receipts(recent_events)
    event_lines = []
    for event in safe_events:
        age_text = (
            f", age={event['age_seconds']:.1f}s"
            if event.get("age_seconds") is not None else ""
        )
        delta_text = ", ".join(
            f"{name}={delta:+.3f}" for name, delta in sorted(event["changes"].items())
        ) or "no channel delta recorded"
        baseline_text = ", ".join(
            f"{name}={delta:+.3f}"
            for name, delta in sorted(event["baseline_changes"].items())
        )
        baseline_suffix = f", baseline=[{baseline_text}]" if baseline_text else ""
        event_lines.append(
            f"Recorded affect event: type={event['event_type']}, source={event['source']}"
            f"{age_text}, changes=[{delta_text}]{baseline_suffix}"
            f"{', turn=' + event['turn_id'] if event.get('turn_id') else ''}"
        )
    recent_text = "\n".join(event_lines) if event_lines else ""
    return (
        "━━ AFFECT SELF-REPORT EVIDENCE ━━\n"
        "Source: EmotionalStateManager.get_response_modifiers().affective_profile; "
        "these are live modeled affect channels, each on a 0–1 scale.\n"
        f"Affect channels: {channel_text}\n"
        f"State description: {state_text}\n"
        f"Latest recorded affect-changing appraisal: {latest_text}.\n"
        f"{recent_text + chr(10) if recent_text else ''}"
        "For this self-report, use only these affect-channel values. In particular, "
        "the CuriosityEngine/DecisionPressure `Curiosity Drive` elsewhere in cognitive "
        "telemetry is a separate motivation signal; do not substitute it for the "
        "EmotionalStateManager `curiosity` channel. Identify the source when giving "
        "numbers. The appraisal is the latest logged event, not necessarily the sole "
        "cause of the whole state. These computational signals do not establish human-like "
        "subjective experience. If the relevant value is unavailable here, say so."
    )


def sanitize_affect_event_receipts(recent_events: Any) -> list[dict[str, Any]]:
    """Expose only bounded event identifiers, ages, and known channel deltas."""
    allowed_channels = {
        "curiosity", "warmth", "anxiety", "satisfaction", "frustration",
        "enthusiasm", "surprise", "sadness", "relief", "disappointment",
        "anticipation",
    }
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
        for name, raw_delta in raw_changes.items():
            if name not in allowed_channels:
                continue
            try:
                delta = float(raw_delta)
            except (TypeError, ValueError, OverflowError):
                continue
            if math.isfinite(delta):
                changes[name] = max(-1.0, min(1.0, delta))
        raw_baselines = row.get("baseline_changes") if isinstance(row.get("baseline_changes"), dict) else {}
        baseline_changes = {}
        for name, raw_delta in raw_baselines.items():
            if name not in allowed_channels:
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

