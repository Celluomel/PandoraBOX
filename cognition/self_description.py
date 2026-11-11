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
    if re.search(r"\b(?:architecture|harness|harnais)\b", text):
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
            "result": text(outcome.get("result"), 200),
            "observed_at": number(outcome.get("observed_at")),
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
        outcome = plan.get("last_outcome") if isinstance(plan.get("last_outcome"), dict) else {}
        outcome_operation = str(outcome.get("operation") or "opération non précisée")[:80]
        outcome_result = str(outcome.get("result") or "détail absent")[:200]
        outcome_status = "échec" if outcome.get("success") is False else "succès" if outcome.get("success") is True else "statut absent"
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
                f"progression {steps_done}/{total}, étapes terminées : {complete_text}, prochaine opération : {next_operation}. "
                f"Dernier résultat enregistré : {outcome_operation} — {outcome_status} — {outcome_result}{time_note}.{capture_note} "
                "Cela décrit l’état affiché du plan; « aucune » signifie qu’aucune étape n’est marquée terminée. "
                "Aucun composant ne peut être confirmé comme exécuté pendant le tour à partir de ce panneau seul. "
                "Le snapshot ne fournit pas d’identifiant reliant ce résultat au message analysé, ni de journal par module : "
                "je ne peux donc pas établir que l’échec a été causé par ce tour ou vérifier indépendamment l’effet de l’opération."
            )
        complete_text = ", ".join(completed) if completed else "none"
        return (
            f"Facts in the transmitted UI snapshot: plan '{objective}', progress {steps_done}/{total}, "
            f"completed steps: {complete_text}, next operation: {next_operation}. "
            f"Last recorded outcome: {outcome_operation} — {outcome_status} — {outcome_result}.{capture_note} "
            "This is displayed planner state; 'none' means no step is marked completed. The snapshot has no identifier "
            "linking that outcome to the message being analyzed and no per-module execution journal, so no component execution "
            "can be confirmed for this turn from this panel alone, and I cannot attribute the failure to this turn or independently verify the operation's effect."
        )

    french = bool(re.search(
        r"\b(?:le|la|les|des|du|est|sont|explique|précisément|permettent|conclure|observé|exécuté)\b",
        normalized,
    ))
    module_tick_question = bool(
        re.search(r"\bmodules?\b", normalized)
        and re.search(r"\b(?:tick|exécut|observ|initialis|indisponible|compteur)", normalized)
    )
    prior_result_question = bool(re.search(
        r"\b(?:rappelle(?:-moi)?|précédent(?:e)?|précédemment|avant|juste avant|"
        r"dernier test|test précédent|résultat vérifié|previous(?:ly)?|earlier|"
        r"just before|last test|prior result)\b",
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
                "module. Do not infer particular mechanisms from an empty registry."
            ]
        else:
            lines = [
                "VERIFIED ARCHITECTURE (partial registry; this is not a complete process-flow audit):",
                "Use only the named roles/configuration below as verified self-description. "
                "Do not invent equations, physical sensations, or unlisted mechanisms.",
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
