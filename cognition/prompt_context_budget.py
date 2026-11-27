"""
cognition/prompt_context_budget.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PromptContextBudget — token-budgeted prompt assembly and admission telemetry.

Problem it solves
──────────────────
After the audit fixes, _build_prompt_additions() now assembles up to 15+
sections from different cognitive modules. Without a budget:

    memory + beliefs + narrative + skills + audit + immune + preferences
    + self_state + emotion + curiosity + pressure + ...

    → prompt grows unboundedly
    → signal-to-noise ratio falls
    → LLM context window fills with repeated state
    → PandoraBOX appears to use the "same state" regardless of input

And even with wiring fixed, there's no way to know which sections
actually entered the prompt vs were silently too long.

What this module does
──────────────────────
1. TOKEN BUDGET — each section category has a fixed token cap.
   Sections are assembled in priority order; when the budget for a
   category is exhausted, lower-priority items in that category drop.

2. CONTRIBUTION RECORD — every section that enters or is dropped is
   logged with: source, tokens, selected, reason.
   Persisted to data/persona/prompt_contributions.json (rolling 200).

3. ADMISSION SUMMARY — contribution_summary() returns per-source
   stats: mean tokens, admission rate, last_selected_at. This is prompt
   assembly telemetry, not a measure of model attention or response effect.
   Readable by brain.py /state endpoint and the audit engine.

Token budget (conservative — real tokenisation is ~4 chars/token):

    Category            Budget (tokens)   Priority
    ─────────────────────────────────────────────
    self_evidence       120               1  (verified claims and epistemic contract)
    self_state          180               2  (φ, coherence, experiential state)
    user_model           60               2  (compact inferred interaction model)
    identity            200               3  (narrative arc, values)
    cognitive_pressure  100               4  (tensions, energy, homeostasis)
    attention           80                5  (attention + curiosity)
    memory_active       150               6  (inner monologue)
    skills              120               7  (relevant competencies)
    preferences         80                8  (stable orientations)
    experimentation     100               9  (active experiment)
    meta_systems        120              10  (audit, immune, ripple, ethics)
    ─────────────────────────────────────────────
    TOTAL HARD CAP      900               (≈ 3600 chars / ~720 words)

Usage (in _build_prompt_additions):
    budget = PromptContextBudget()
    budget.add("identity", "narrative_identity", ni_frag)
    budget.add("skills",   "skill_registry",     skill_frag)
    ...
    final_text = budget.assemble()
    budget.save()
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ── Token budget per category ──────────────────────────────────────────────────
# Approximate: 4 characters ≈ 1 token
CHARS_PER_TOKEN = 4

CATEGORY_BUDGETS: Dict[str, Tuple[int, int]] = {
    # category → (token_budget, priority)  lower priority = higher priority number
    # A live planner self-report was measured at 425 estimated tokens. Keep
    # headroom for ordinary changes in active goals and provenance; priority 0
    # reserves it before lower-priority narrative context.
    "factual_telemetry":  (480, 0),
    # Keep open uncertainty origins independently available to the model. This
    # gets a reserved category because the former shared cognitive-pressure
    # slot was routinely exhausted by energy and arbitration before Workspace.
    "epistemic_context":  (240, 1),
    "self_evidence":      (120, 1),
    # Self-model, experiential signals, interrupts, and temporal context are
    # independent producers. Their compact forms need to coexist; the former
    # cap admitted only the self-model paragraph.
    "self_state":         (180, 2),
    # A compact, explicitly inferred interaction model is useful to tailor a
    # reply, but it is neither an explicit profile fact nor general memory.
    # Reserve a bounded slot after core self-state so the WorldModel section
    # is not routinely evicted by lower-priority narrative/attention text.
    "user_model":         (60,  2),
    # A correction rule is a turn-specific control signal; keep it separate
    # from the large meta-systems bundle so a relevant rule is not silently
    # displaced by unrelated telemetry.
    "self_correction":    (120, 1),
    "identity":           (200, 3),
    # The former cap routinely discarded arbitration after energy had taken
    # its share. Keep decision, workspace, and energy hand-offs eligible while
    # the global 900-token ceiling still bounds total prompt growth.
    "cognitive_pressure": (160, 4),
    "attention":          (80,  5),
    "memory_active":      (150, 6),
    "skills":             (120, 7),
    "preferences":        (80,  8),
    "experimentation":    (100, 9),
    "meta_systems":       (120, 10),
}

TOTAL_TOKEN_CAP = 900   # hard ceiling across all categories

MAX_CONTRIBUTION_LOG = 200


def fit_system_prompt_to_context(
    system_prompt: str,
    user_prompt: str,
    *,
    context_tokens: int,
    output_tokens: int,
    safety_tokens: int = 800,
    chars_per_token: float = 3.5,
    protected_tail: str = "",
) -> tuple[str, dict[str, int | float | str | bool]]:
    """Fit a fully assembled system prompt into the model's input budget.

    Preserve the beginning (identity and core instructions) and the ending
    (latest evidence/route contracts). Any route-specific protected tail is
    appended after trimming so it cannot be lost to an earlier truncation.
    The estimate deliberately follows the provider's existing character/token
    heuristic; it is a budget guard, not tokenizer-exact accounting.
    """
    original = str(system_prompt or "")
    tail = str(protected_tail or "").strip()
    marker = "\n[… contexte intermédiaire omis pour respecter la fenêtre du modèle …]\n"
    context_limit = max(512, int(context_tokens or 4096))
    output_reserve = max(int(safety_tokens), max(0, int(output_tokens or 0)))
    input_tokens = max(256, context_limit - output_reserve)
    total_input_chars = max(256, int(input_tokens * max(1.0, float(chars_per_token))))
    max_chars = max(128, total_input_chars - len(str(user_prompt or "")))
    base = original
    if tail:
        base = base.rstrip() + "\n\n" + tail

    fitted = base
    compacted = len(base) > max_chars
    if compacted:
        available = max(0, max_chars - len(marker))
        # Preserve a larger prefix for persona/core cognition and a substantial
        # suffix for current evidence, provenance and final response contracts.
        prefix_chars = min(len(base), int(available * 0.62))
        suffix_chars = available - prefix_chars
        fitted = base[:prefix_chars] + marker + (base[-suffix_chars:] if suffix_chars else "")

    receipt: dict[str, int | str | bool] = {
        "status": "compacted" if compacted else "within_budget",
        "original_chars": len(original),
        "protected_tail_chars": len(tail),
        "assembled_chars": len(base),
        "final_chars": len(fitted),
        "max_chars": max_chars,
        "user_prompt_chars": len(str(user_prompt or "")),
        "total_input_char_budget": total_input_chars,
        "context_tokens": context_limit,
        "output_reserve_tokens": output_reserve,
        "safety_tokens": max(0, int(safety_tokens)),
        "chars_per_token_estimate": float(chars_per_token),
        "strategy": "preserve_prefix_and_suffix",
        "protected_tail_preserved": bool(tail and fitted.endswith(tail)),
    }
    return fitted, receipt


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class SectionEntry:
    """One candidate section before budget decision."""
    category:  str
    source:    str        # e.g. "narrative_identity", "skill_registry"
    text:      str
    tokens:    int        # estimated
    selected:  bool = False
    reason:    str  = ""  # "budget_ok" | "category_full" | "total_cap" | "empty"


@dataclass
class ContributionRecord:
    """One prompt assembly's full record."""
    timestamp:    float
    total_tokens: int
    sections:     List[Dict]  # serialised SectionEntries
    turn_id:      Optional[str] = None


# ── Budget ────────────────────────────────────────────────────────────────────

class PromptContextBudget:
    """
    Assembles prompt sections respecting per-category and global token budgets.
    Records every decision for observability.

    Usage:
        b = PromptContextBudget()
        b.add("identity", "narrative_identity", text)
        b.add("skills",   "skill_registry",     text)
        result = b.assemble()   # priority-ordered, budget-capped string
        b.save()                # persist contribution record
    """

    def __init__(
        self,
        path: str = "data/persona/prompt_contributions.json",
        turn_id: Optional[str] = None,
    ) -> None:
        self._path     = Path(path)
        self._turn_id  = str(turn_id).strip() if turn_id else None
        self._entries:  List[SectionEntry] = []
        self._cat_used: Dict[str, int]     = {cat: 0 for cat in CATEGORY_BUDGETS}
        self._total_used = 0
        self._assembled  = False

    # ── Public API ────────────────────────────────────────────────────────────

    def add(self, category: str, source: str, text: str) -> None:
        """Register a candidate section. Call before assemble()."""
        if not text or not text.strip():
            self._entries.append(SectionEntry(
                category=category, source=source, text="",
                tokens=0, selected=False, reason="empty",
            ))
            return

        tokens = max(1, len(text) // CHARS_PER_TOKEN)
        self._entries.append(SectionEntry(
            category=category, source=source,
            text=text.strip(), tokens=tokens,
        ))

    def assemble(self) -> str:
        """
        Apply budget rules in priority order.
        Returns the assembled prompt string.
        Must be called once; subsequent calls return the same result.
        """
        if self._assembled:
            return self._get_selected_text()

        # Sort entries: by category priority, then registration order
        priority_map = {cat: p for cat, (_, p) in CATEGORY_BUDGETS.items()}
        def sort_key(e: SectionEntry) -> Tuple[int, int]:
            return (priority_map.get(e.category, 99), self._entries.index(e))

        ordered = sorted(self._entries, key=sort_key)

        for entry in ordered:
            if entry.reason == "empty":
                continue

            cat_budget = CATEGORY_BUDGETS.get(entry.category, (80, 99))[0]
            cat_used   = self._cat_used.get(entry.category, 0)

            if self._total_used + entry.tokens > TOTAL_TOKEN_CAP:
                entry.selected = False
                entry.reason   = "total_cap"
            elif cat_used + entry.tokens > cat_budget:
                entry.selected = False
                entry.reason   = "category_full"
            else:
                entry.selected = True
                entry.reason   = "budget_ok"
                self._cat_used[entry.category] = cat_used + entry.tokens
                self._total_used += entry.tokens

        self._assembled = True
        return self._get_selected_text()

    def save(self) -> None:
        """Append this assembly's record to the rolling contribution log."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            existing: List[Dict] = []
            try:
                if self._path.exists():
                    existing = json.loads(self._path.read_text())
            except Exception:
                existing = []

            record = ContributionRecord(
                timestamp    = time.time(),
                total_tokens = self._total_used,
                sections     = [asdict(e) for e in self._entries],
                turn_id      = self._turn_id,
            )
            existing.append(asdict(record))
            if len(existing) > MAX_CONTRIBUTION_LOG:
                existing = existing[-MAX_CONTRIBUTION_LOG:]
            self._path.write_text(json.dumps(existing, indent=2))
        except Exception:
            pass

    def selection_receipt(self, category: str, source: str) -> Dict[str, object]:
        """Return safe selection facts for one prompt source after assembly.

        This intentionally omits section text. Callers can attribute whether a
        candidate entered the prompt without searching the assembled prompt,
        which could otherwise mistake a duplicate fragment for this source.
        """
        entries = [
            entry for entry in self._entries
            if entry.category == category and entry.source == source
        ]
        if not self._assembled:
            return {"registered": bool(entries), "selected": False, "reason": "not_assembled", "tokens": 0}
        if not entries:
            return {"registered": False, "selected": False, "reason": "not_registered", "tokens": 0}

        selected = [entry for entry in entries if entry.selected]
        if selected:
            return {
                "registered": True,
                "selected": True,
                "reason": "budget_ok",
                "tokens": min(1_000_000, sum(max(0, entry.tokens) for entry in selected)),
            }

        reasons = {entry.reason for entry in entries}
        reason = next(
            (candidate for candidate in ("total_cap", "category_full", "empty") if candidate in reasons),
            "not_selected",
        )
        return {"registered": True, "selected": False, "reason": reason, "tokens": 0}

    def contribution_summary(self) -> Dict[str, Dict]:
        """
        Returns per-source selection stats from the persisted log.
        Usable by /state endpoint and CognitiveAuditEngine.

        Returns:
            {
                "narrative_identity": {
                    "appearances": 12,
                    "selected": 10,
                    "selection_rate": 0.83,
                    "mean_tokens": 42.1,
                    "last_selected_at": 1716000000.0,
                },
                ...
            }
        """
        try:
            if not self._path.exists():
                return {}
            records = json.loads(self._path.read_text())
            stats: Dict[str, Dict] = {}
            for rec in records:
                for sec in rec.get("sections", []):
                    src = sec.get("source", "unknown")
                    if src not in stats:
                        stats[src] = {
                            "appearances": 0, "selected": 0,
                            "total_tokens": 0, "last_selected_at": 0.0,
                        }
                    stats[src]["appearances"] += 1
                    if sec.get("selected"):
                        stats[src]["selected"] += 1
                        stats[src]["total_tokens"] += sec.get("tokens", 0)
                        stats[src]["last_selected_at"] = max(
                            stats[src]["last_selected_at"],
                            rec.get("timestamp", 0.0),
                        )
            # Compute derived fields
            for src, s in stats.items():
                n = s["appearances"]
                sel = s["selected"]
                s["selection_rate"] = round(sel / n, 3) if n else 0.0
                s["mean_tokens"]    = round(s["total_tokens"] / sel, 1) if sel else 0.0
            return stats
        except Exception:
            return {}

    def budget_report(self) -> str:
        """
        Human-readable budget usage for logging.
        Example:
            [PromptBudget] 312/900 tokens | selected=8/14
            identity=180 skills=80 meta_systems=52 ...
        """
        if not self._assembled:
            return "[PromptBudget] not assembled yet"
        selected = sum(1 for e in self._entries if e.selected)
        total    = len([e for e in self._entries if e.reason != "empty"])
        cats     = {cat: used for cat, used in self._cat_used.items() if used > 0}
        cat_str  = " ".join(f"{c}={v}" for c, v in sorted(cats.items()))
        return (
            f"[PromptBudget] {self._total_used}/{TOTAL_TOKEN_CAP} tokens "
            f"| selected={selected}/{total} | {cat_str}"
        )

    # ── Internal ──────────────────────────────────────────────────────────────

    def _get_selected_text(self) -> str:
        # Return sections in original registration order (not priority order)
        # so the prompt reads naturally
        return "\n\n".join(
            e.text for e in self._entries if e.selected
        )
