"""
PANDORABOX — IDENTITY GROUNDING LAYER
=================================
Grounds PandoraBOX's self-concept in *demonstrated* capability evidence — i.e.
what the causal outcome loop actually proved it can do — rather than only in
aspirations or self-reported success counts.

It is a CONSUMER of the two prior layers, not a new loop:

    consequence tracker  ->  efficacy[(goal|action)] = {eff, n}   (demonstrated)
    workspace bias       ->  override_rate, focus_stability        (holds focus)
    self_model.json      ->  capabilities (existing self-report)
    aspirational_self    ->  aspirations (who I want to be)

       └────────────►  IDENTITY GROUNDING  ◄────────────┘
                        (fuses demonstrated + aspirational)

WHAT IT PRODUCES
  - demonstrated  : capabilities with real trials + high efficacy (CITED)
  - developing    : capabilities with real trials + low efficacy  (CITED)
  - untried       : no meaningful evidence — NEVER claimed as capability
  - focus         : stability + override-rate (how well I hold a focus)
  - gaps          : aspirations with no demonstrated evidence yet
  - statement     : a prompt-ready, first-person grounded self-description

HONESTY RULE (the one that matters most):
  A capability is only CLAIMED when n >= MIN_TRIALS. Zero-trial goals are
  reported as "untried", never as "I'm good at X". No fabricated competence.

Stores:  data/persona/identity_grounding.json
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from cognition.consequence_tracker import get_consequence_tracker
except Exception:  # pragma: no cover
    get_consequence_tracker = None  # type: ignore

try:
    from cognition.workspace_bias import get_workspace_bias
except Exception:  # pragma: no cover
    get_workspace_bias = None  # type: ignore


MIN_TRIALS   = 3      # a capability needs >= this many trials to be claimed
STRONG_EFF   = 0.65   # >= this efficacy  -> "demonstrated"
WEAK_EFF     = 0.45   # <= this efficacy  -> "developing"
FOCUS_GOOD   = 0.70   # focus_stability >= this -> "holds focus well"
OVERRIDE_LOW = 0.25   # override_rate  <= this  -> "follows its focus"
MAX_TIMELINE_EVENTS = 160
CORRECTION_VERIFY_EVIDENCE = 3
CORRECTION_VERIFY_SUCCESSES = 2


class IdentityGrounding:
    def __init__(self, organism: Any = None, persona_dir: Optional[str] = None,
                 enabled: bool = True, tracker: Any = None, wb: Any = None):
        self.persona_dir = Path(persona_dir) if persona_dir else Path("data/persona")
        self.persona_dir.mkdir(parents=True, exist_ok=True)
        self._organism = organism
        self.enabled = enabled
        # optional injected sources (for hermetic ablation / tests); else the
        # process singletons are used at gather time
        self._tracker = tracker
        self._wb = wb
        self.path = self.persona_dir / "identity_grounding.json"
        self._lock = threading.RLock()

    # ── 1. GATHER (consume the prior layers) ────────────────────────────────
    def gather_evidence(self) -> Dict[str, Any]:
        ev: Dict[str, Any] = {
            "efficacy": {},          # goal|action -> {eff, n}
            "focus": {},             # override_rate, focus_stability, mean_similarity
            "capabilities": {},      # self_model.capabilities (self-report)
            "aspirations": [],       # aspirational_self.aspirations
            "closure": {},           # consequence tracker closure report
            "planning": {},          # current goals and operational plan
            "corrections": {},       # learned response policies and outcomes
            "restructuring": {},     # multi-causal correction experiment
            "calibration": {},       # predicted confidence vs outcomes
            "narrative_chapters": [],
            "total_interactions": 0,
        }
        # consequence tracker (demonstrated efficacy) — injected ref first
        ct = self._tracker
        if ct is None and get_consequence_tracker is not None:
            try:
                ct = get_consequence_tracker(self._organism,
                                             persona_dir=str(self.persona_dir))
            except Exception:
                ct = None
        if ct is not None:
            try:
                ev["efficacy"] = {k: dict(v) for k, v in ct._efficacy.items()}
                ev["closure"] = ct.closure_report()
            except Exception:
                pass
        # workspace bias (focus stability) — injected ref first
        wb = self._wb
        if wb is None and get_workspace_bias is not None:
            try:
                wb = get_workspace_bias(self._organism, str(self.persona_dir))
            except Exception:
                wb = None
        if wb is not None:
            try:
                ev["focus"] = wb.override_rate()
            except Exception:
                pass
        # existing self-model capabilities (self-report, for context)
        try:
            sm = json.loads((self.persona_dir / "self_model.json").read_text(encoding="utf-8"))
            ev["capabilities"] = sm.get("capabilities", {})
            ev["total_interactions"] = int(sm.get("total_interactions", 0))
        except Exception:
            pass
        # aspirations
        try:
            asp = json.loads((self.persona_dir / "aspirational_self.json").read_text(encoding="utf-8"))
            ev["aspirations"] = asp.get("aspirations", [])
        except Exception:
            pass
        # Live agency: this is what the organism is actually pursuing now,
        # separate from aspirations and from whatever the user is discussing.
        try:
            loop = getattr(self._organism, "_loop", None)
            planner = getattr(loop, "_long_horizon_planner", None)
            if planner is not None and hasattr(planner, "factual_self_report_snapshot"):
                ev["planning"] = planner.factual_self_report_snapshot()
        except Exception:
            pass
        # Self-correction is only a capability once repeated outcome evidence
        # exists. The raw rule count is not treated as competence.
        try:
            correction = getattr(self._organism, "_self_correction", None)
            if correction is not None and hasattr(correction, "status"):
                ev["corrections"] = correction.status()
        except Exception:
            pass
        try:
            restructuring = getattr(self._organism, "_cognitive_restructuring", None)
            if restructuring is not None and hasattr(restructuring, "status"):
                ev["restructuring"] = restructuring.status()
        except Exception:
            pass
        # Read the live calibration engine when available. No synthetic
        # confidence is created when the model has not resolved enough trials.
        try:
            loop = getattr(self._organism, "_loop", None)
            pcm = getattr(loop, "_consequence_model", None)
            if pcm is None:
                ai = getattr(self._organism, "ai_system", None)
                for attr in ("_consequence_model", "consequence_model", "predictive_consequence_model"):
                    pcm = getattr(ai, attr, None) if ai is not None else None
                    if pcm is not None:
                        break
            calibration = getattr(pcm, "_calibration_engine", None) if pcm is not None else None
            if calibration is not None and hasattr(calibration, "summary"):
                ev["calibration"] = calibration.summary()
        except Exception:
            pass
        try:
            narrative = getattr(self._organism, "narrative_identity", None)
            chapters = list(getattr(narrative, "life_story", []) or [])[-8:]
            ev["narrative_chapters"] = [
                chapter.to_dict() if hasattr(chapter, "to_dict") else dict(chapter)
                for chapter in chapters
            ]
        except Exception:
            pass
        return ev

    # ── 2. GROUND (fuse demonstrated + aspirational into identity) ──────────
    def ground(self, evidence: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.enabled:
            return {"disabled": True}
        ev = evidence if evidence is not None else self.gather_evidence()

        demonstrated: List[Dict[str, Any]] = []
        developing:   List[Dict[str, Any]] = []
        untried:      List[Dict[str, Any]] = []

        for key, row in (ev.get("efficacy") or {}).items():
            eff = float(row.get("eff", 0.5))
            n   = int(row.get("n", 0))
            goal, _, action = str(key).partition("|")
            item = {"goal": goal, "action": action, "eff": round(eff, 3), "n": n,
                    "citation": f"efficacy[{key}].eff={eff:.2f}, n={n}"}
            if n < MIN_TRIALS:
                untried.append(item)
            elif eff >= STRONG_EFF:
                demonstrated.append(item)
            elif eff <= WEAK_EFF:
                developing.append(item)
            else:
                # enough trials, middling efficacy -> developing (honest middle)
                developing.append(item)
        demonstrated.sort(key=lambda x: -x["eff"])
        developing.sort(key=lambda x: x["eff"])

        # focus stability
        focus = ev.get("focus") or {}
        focus_stability = float(focus.get("focus_stability", 1.0))
        override_rate   = float(focus.get("override_rate", 0.0))
        focus_checks = int(focus.get("checks_total", 0))
        holds_focus = (
            focus_checks >= MIN_TRIALS
            and focus_stability >= FOCUS_GOOD
            and override_rate <= OVERRIDE_LOW
        )

        # aspiration <-> demonstration gap (is there evidence behind each wish?)
        gaps = self._aspiration_gaps(ev, demonstrated)

        identity = {
            "demonstrated": demonstrated,
            "developing":   developing,
            "untried":      untried,
            "focus": {
                "stability": round(focus_stability, 3),
                "override_rate": round(override_rate, 3),
                "checks": focus_checks,
                "holds_focus": holds_focus,
                "status": "verified" if holds_focus else (
                    "developing" if focus_checks >= MIN_TRIALS else "unmeasured"
                ),
                "citation": f"workspace_bias.focus_stability={focus_stability:.2f}, "
                            f"override_rate={override_rate:.2f}, checks={focus_checks}",
            },
            "gaps": gaps,
            "statement": self._statement(demonstrated, developing,
                                         focus_stability, override_rate, holds_focus,
                                         focus_checks, gaps),
            "claim_ledger": self._build_claim_ledger(
                demonstrated, developing, untried, focus, ev.get("corrections") or {}
            ),
            "agency": self._agency_snapshot(ev.get("planning") or {}, ev.get("aspirations") or []),
            "metacognition": self._metacognitive_snapshot(
                ev.get("calibration") or {}, ev.get("capabilities") or {}
            ),
            "self_correction": self._correction_snapshot(ev.get("corrections") or {}),
            "restructuring": ev.get("restructuring") or {},
            "narrative_chapters": ev.get("narrative_chapters") or [],
            "epistemic_contract": {
                "observation": "Directly recorded state may be stated as current fact.",
                "inference": "Derived interpretations must be labelled as tentative.",
                "aspiration": "Desired futures are not current capabilities or active actions.",
                "unknown": "Missing or stale evidence must be reported as unknown.",
            },
            "evidence_base": {
                "n_efficacy_rows": len(ev.get("efficacy") or {}),
                "total_interactions": ev.get("total_interactions", 0),
                "n_aspirations": len(ev.get("aspirations") or []),
                "focus_checks": focus_checks,
                "calibration_resolutions": sum(
                    int(module.get("total_resolved", 0))
                    for module in (ev.get("calibration") or {}).get("modules", {}).values()
                    if isinstance(module, dict)
                ),
            },
            "ts": datetime.now().isoformat(timespec="seconds"),
        }
        self._persist(identity)
        return identity

    @staticmethod
    def _aspiration_gaps(ev: Dict[str, Any], demonstrated: List[Dict]) -> List[Dict]:
        """Surface aspirations that have NO demonstrated capability behind them
        (the growth drive) vs those with evidence."""
        gaps: List[Dict] = []
        demo_text = " ".join((d.get("goal", "") + " " + d.get("action", "")).lower()
                             for d in demonstrated)
        for a in ev.get("aspirations") or []:
            if not isinstance(a, dict):
                continue
            stmt = (a.get("statement", "") + " " + a.get("domain", "")).lower()
            # crude evidence link: does any demonstrated goal/action share a token
            # with the aspiration? (honest, weak signal — flagged as "weak link")
            tokens = {w for w in stmt.split() if len(w) > 4}
            link = any(t in demo_text for t in tokens)
            gaps.append({
                "id": a.get("id", ""),
                "domain": a.get("domain", ""),
                "statement": a.get("statement", "")[:120],
                "urgency": a.get("urgency", 0.5),
                "has_evidence": link,
                "evidence_strength": "weak_link" if link else "none",
            })
        # gaps = the ones WITHOUT evidence, most urgent first
        return sorted([g for g in gaps if not g["has_evidence"]],
                      key=lambda g: -float(g.get("urgency", 0.5)))

    def _statement(self, demonstrated, developing, focus_stability,
                   override_rate, holds_focus, focus_checks, gaps) -> str:
        parts = []
        if demonstrated:
            top = demonstrated[0]
            parts.append(
                f"I have demonstrated the ability to {top['goal']} "
                f"({top['n']} trials, efficacy {top['eff']:.2f})."
            )
            if len(demonstrated) > 1:
                others = ", ".join(d["goal"] for d in demonstrated[1:4])
                parts.append(f"Other demonstrated capabilities: {others}.")
        else:
            parts.append("I have not yet accumulated enough trials to claim "
                         "a demonstrated capability — I will not pretend otherwise.")
        if developing:
            dev = developing[0]
            parts.append(f"I am still developing {dev['goal']} "
                         f"({dev['n']} trials, efficacy {dev['eff']:.2f}).")
        # focus
        if focus_checks < MIN_TRIALS:
            parts.append("I do not yet have enough observations to claim reliable focus.")
        elif holds_focus:
            parts.append(f"I hold my focus well (stability {focus_stability:.2f}, "
                         f"override rate {override_rate:.2f}).")
        else:
            parts.append(f"My focus is not yet reliable (stability {focus_stability:.2f}, "
                         f"override rate {override_rate:.2f}) — I know this is an edge to close.")
        if gaps:
            g = gaps[0]
            parts.append(f"My strongest open aspiration is to {g['statement'][:90]} "
                         f"({g['domain']}), and I have no demonstrated evidence behind it yet.")
        return " ".join(parts)

    @staticmethod
    def _build_claim_ledger(demonstrated, developing, untried, focus, corrections) -> List[Dict[str, Any]]:
        claims: List[Dict[str, Any]] = []
        for status, rows in (("verified", demonstrated), ("developing", developing),
                             ("unverified", untried)):
            for row in rows:
                key = f"{row.get('goal', '')}|{row.get('action', '')}"
                claims.append({
                    "id": f"capability:{key}",
                    "kind": "capability",
                    "statement": f"Can advance {row.get('goal', '')} through {row.get('action', '')}",
                    "status": status,
                    "confidence": float(row.get("eff", 0.5)),
                    "evidence_count": int(row.get("n", 0)),
                    "evidence_refs": [row.get("citation", "")],
                    "source": "consequence_tracker",
                })
        checks = int((focus or {}).get("checks_total", 0))
        if checks:
            stable = (
                float(focus.get("focus_stability", 0.0)) >= FOCUS_GOOD
                and float(focus.get("override_rate", 1.0)) <= OVERRIDE_LOW
            )
            claims.append({
                "id": "ability:maintain_focus",
                "kind": "capability",
                "statement": "Can maintain an active cognitive focus",
                "status": "verified" if checks >= MIN_TRIALS and stable else "developing",
                "confidence": float(focus.get("focus_stability", 0.0)),
                "evidence_count": checks,
                "evidence_refs": [
                    f"workspace_bias checks={checks}, override_rate={float(focus.get('override_rate', 0.0)):.2f}"
                ],
                "source": "workspace_bias",
            })
        for rule in (corrections or {}).get("top_rules", []):
            evidence = int(rule.get("evidence", 0))
            successes = int(rule.get("successful_turns", 0))
            confidence = float(rule.get("confidence", 0.0))
            verified = (
                evidence >= CORRECTION_VERIFY_EVIDENCE
                and successes >= CORRECTION_VERIFY_SUCCESSES
                and confidence >= 0.70
            )
            claims.append({
                "id": f"correction:{rule.get('id', rule.get('rule', '')[:32])}",
                "kind": "learned_behavior",
                "statement": str(rule.get("rule", ""))[:240],
                "status": "verified" if verified else "developing",
                "confidence": confidence,
                "evidence_count": evidence + successes,
                "evidence_refs": [
                    f"self_correction evidence={evidence}, successful_turns={successes}"
                ],
                "source": "self_correction",
            })
        claims.sort(key=lambda item: (
            item.get("status") == "verified",
            float(item.get("confidence", 0.0)),
            int(item.get("evidence_count", 0)),
        ), reverse=True)
        return claims[:40]

    @staticmethod
    def _agency_snapshot(planning: Dict[str, Any], aspirations: List[Dict[str, Any]]) -> Dict[str, Any]:
        goals = list(planning.get("active_goals") or [])
        plan = planning.get("dominant_plan")
        return {
            "status": "active" if goals or plan else "idle",
            "active_goals": goals[:4],
            "dominant_plan": plan,
            "aspirations": [
                {
                    "id": item.get("id", ""),
                    "domain": item.get("domain", ""),
                    "statement": str(item.get("statement", ""))[:160],
                    "state": "desired_not_achieved",
                }
                for item in aspirations[:4] if isinstance(item, dict)
            ],
            "distinction": "Active goals and plans are current commitments; aspirations are desired directions.",
        }

    @staticmethod
    def _metacognitive_snapshot(calibration: Dict[str, Any], capabilities: Dict[str, Any]) -> Dict[str, Any]:
        modules = calibration.get("modules", {}) if isinstance(calibration, dict) else {}
        resolved = sum(
            int(row.get("total_resolved", 0))
            for row in modules.values() if isinstance(row, dict)
        )
        calibrated = {
            name: {"ece": row.get("ece"), "resolved": int(row.get("total_resolved", 0))}
            for name, row in modules.items()
            if isinstance(row, dict) and row.get("ece") is not None
        }
        reported_confidences = []
        for row in capabilities.values() if isinstance(capabilities, dict) else []:
            if isinstance(row, dict) and "score" in row:
                try:
                    reported_confidences.append(float(row["score"]))
                except (TypeError, ValueError):
                    pass
        return {
            "status": "calibrated" if calibrated else ("collecting_evidence" if resolved else "unmeasured"),
            "resolved_predictions": resolved,
            "pending_predictions": int(calibration.get("pending_count", 0)) if isinstance(calibration, dict) else 0,
            "calibrated_modules": calibrated,
            "self_reported_capability_mean": (
                round(sum(reported_confidences) / len(reported_confidences), 3)
                if reported_confidences else None
            ),
            "warning": (
                "Self-reported capability scores are not treated as verified competence."
            ),
        }

    @staticmethod
    def _correction_snapshot(corrections: Dict[str, Any]) -> Dict[str, Any]:
        rules = list(corrections.get("top_rules") or [])
        verified = [
            rule for rule in rules
            if int(rule.get("evidence", 0)) >= CORRECTION_VERIFY_EVIDENCE
            and int(rule.get("successful_turns", 0)) >= CORRECTION_VERIFY_SUCCESSES
            and float(rule.get("confidence", 0.0)) >= 0.70
        ]
        return {
            "status": "verified" if verified else ("developing" if rules else "unmeasured"),
            "rules_observed": int(corrections.get("rules", len(rules))),
            "verified_rules": len(verified),
            "note": "A stored correction is not a learned capability until later outcomes support it.",
        }

    # ── 3. PROMPT-READY + EVIDENCE EXPORT ───────────────────────────────────
    def identity_block(self) -> str:
        """Compact prompt-ready grounded-identity string (budget-friendly)."""
        if not self.enabled:
            return ""
        try:
            ident = self.ground()
        except Exception:
            return ""
        claims = ident.get("claim_ledger") or []
        verified = [item for item in claims if item.get("status") == "verified"]
        agency = ident.get("agency") or {}
        plan = agency.get("dominant_plan") or {}
        lines = [
            "[Evidence-backed self] Separate recorded observations, tentative inferences, "
            "aspirations, and unknowns. Never present an unverified inner narrative as fact."
        ]
        if verified:
            top = verified[0]
            lines.append(
                f"Verified: {top.get('statement', '')} "
                f"({top.get('evidence_count', 0)} observations, confidence "
                f"{float(top.get('confidence', 0.0)):.2f})."
            )
        else:
            lines.append("No capability currently has sufficient outcome evidence to be claimed as verified.")
        if plan:
            lines.append(
                f"Current recorded plan: {str(plan.get('objective', ''))[:80]} "
                f"({int(plan.get('steps_completed', 0))}/{int(plan.get('steps_total', 0))})."
            )
        return " ".join(lines)

    def record_interaction_evidence(
        self,
        user_input: str,
        response: str,
        validator_score: Optional[float] = None,
        correction: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record only consequential self-relevant events, not every chat turn."""
        if not self.enabled:
            return
        event: Optional[Dict[str, Any]] = None
        now = time.time()
        if correction:
            event = {
                "id": f"self_event_{int(now * 1000)}",
                "observed_at": now,
                "kind": "self_correction",
                "cause": "The user supplied corrective evidence.",
                "effect": f"Behavioral rule {correction.get('id', 'unknown')} entered validation.",
                "status": "developing",
                "confidence": float(correction.get("confidence", 0.0)),
                "evidence_refs": [f"self_corrections.json#{correction.get('id', '')}"],
                "summary": str(correction.get("rule", ""))[:240],
            }
        elif validator_score is not None and validator_score < 0.55:
            event = {
                "id": f"self_event_{int(now * 1000)}",
                "observed_at": now,
                "kind": "response_misalignment",
                "cause": "The response validator detected weak cognition-response alignment.",
                "effect": "The interaction is evidence of a capability gap, not success.",
                "status": "observed",
                "confidence": round(1.0 - float(validator_score), 3),
                "evidence_refs": [f"cognitive_validator score={float(validator_score):.3f}"],
                "summary": (user_input or "")[:180],
            }
        if event is not None:
            self._append_timeline_event(event)

    def snapshot(self) -> Dict[str, Any]:
        """Return the complete inspectable evidential self-state."""
        return self.ground()

    def capability_evidence(self) -> Dict[str, Any]:
        """Structured, citable capability evidence — the input the
        PhenomenalBinder A/B/C ablation will consume."""
        if not self.enabled:
            return {}
        ident = self.ground()
        return {
            "demonstrated": ident["demonstrated"],
            "developing": ident["developing"],
            "untried": ident["untried"],
            "focus": ident["focus"],
            "gaps": ident["gaps"],
            "evidence_base": ident["evidence_base"],
        }

    # ── persistence ─────────────────────────────────────────────────────────
    def _persist(self, identity: Dict[str, Any]):
        try:
            with self._lock:
                previous: Dict[str, Any] = {}
                if self.path.exists():
                    try:
                        previous = json.loads(self.path.read_text(encoding="utf-8"))
                    except Exception:
                        previous = {}
                timeline = list(previous.get("autobiographical_timeline") or [])
                prior_claims = {
                    item.get("id"): item for item in previous.get("claim_ledger", [])
                    if isinstance(item, dict) and item.get("id")
                }
                now = time.time()
                for claim in identity.get("claim_ledger", []):
                    prior = prior_claims.get(claim.get("id"))
                    if claim.get("status") == "verified" and (
                        prior is None or prior.get("status") != "verified"
                    ):
                        timeline.append({
                            "id": f"self_event_{int(now * 1000)}_{len(timeline)}",
                            "observed_at": now,
                            "kind": "capability_verified",
                            "cause": "Repeated outcome evidence crossed the verification threshold.",
                            "effect": claim.get("statement", ""),
                            "status": "verified",
                            "confidence": claim.get("confidence", 0.0),
                            "evidence_refs": claim.get("evidence_refs", []),
                            "summary": claim.get("statement", ""),
                        })
                prior_plan = (previous.get("agency") or {}).get("dominant_plan") or {}
                plan = (identity.get("agency") or {}).get("dominant_plan") or {}
                if plan and (
                    plan.get("objective") != prior_plan.get("objective")
                    or plan.get("steps_completed") != prior_plan.get("steps_completed")
                ):
                    timeline.append({
                        "id": f"self_event_{int(now * 1000)}_plan",
                        "observed_at": now,
                        "kind": "agency_transition",
                        "cause": "The operational planner changed state.",
                        "effect": (
                            f"{plan.get('objective', '')}: "
                            f"{plan.get('steps_completed', 0)}/{plan.get('steps_total', 0)}"
                        ),
                        "status": "observed",
                        "confidence": float(plan.get("reasoning_confidence", 0.0)),
                        "evidence_refs": ["long_horizon_planner.factual_self_report_snapshot"],
                        "summary": str(plan.get("decision_summary", ""))[:240],
                    })
                identity["autobiographical_timeline"] = timeline[-MAX_TIMELINE_EVENTS:]
                identity["version"] = 2
                temp_path = self.path.with_suffix(".json.tmp")
                temp_path.write_text(
                    json.dumps(identity, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                temp_path.replace(self.path)
        except Exception:
            pass

    def _append_timeline_event(self, event: Dict[str, Any]) -> None:
        try:
            with self._lock:
                current: Dict[str, Any] = {}
                if self.path.exists():
                    current = json.loads(self.path.read_text(encoding="utf-8"))
                timeline = list(current.get("autobiographical_timeline") or [])
                timeline.append(event)
                current["autobiographical_timeline"] = timeline[-MAX_TIMELINE_EVENTS:]
                current["version"] = 2
                temp_path = self.path.with_suffix(".json.tmp")
                temp_path.write_text(
                    json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                temp_path.replace(self.path)
        except Exception:
            pass


_ig: Optional[IdentityGrounding] = None
def get_identity_grounding(organism: Any = None,
                           persona_dir: Optional[str] = None) -> IdentityGrounding:
    global _ig
    if _ig is None:
        _ig = IdentityGrounding(organism=organism, persona_dir=persona_dir)
    elif organism is not None:
        _ig._organism = organism
    return _ig
