# Conversation / cognitive regression audit — Phase 0

Date: 2026-11-22
Scope: executed evidence and design feasibility only. No production behavior was changed.

## Executive result

**Phase 0 is complete. The regression is reproduced, attributed, and ready for a bounded Phase 1 design approval.** Ordinary turns currently pass through a long cognitive pipeline before the first visible answer. Across 19 baseline turns, Lumina made **75 provider calls tied to those turn IDs** (plus one provider call without a turn ID): 19 primary chat generations, 54 calls from the review stream helper, and two direct `generate_interactive_analysis` calls. A turn used 3–6 provider calls; median answer latency was **38.48 s** (31.33–74.69 s). In **19/19** cases, the first visible delta arrived within 1 ms of the end of the request, so the stream did not provide progressive text.

The semantic response reviewer is the principal cause of the false refusals: it runs after generation but before delivery, can request a second review/repair, and replaces the candidate with a refusal when its probabilistic review does not pass. It replaced **7/19** baseline responses; one additional review returned invalid schema. This is an answer veto, not an independent truth check.

The affect regression has a second, separately reproduced cause. The current social-state route recognizes a narrow set of exact phrases. Short forms take a fast deterministic path but expose raw affect numbers. A natural variant with “today / aujourd’hui” misses that route: French receives a false refusal after 61.3 s, while English receives an invented first-person feeling narrative after 33.8 s and the generic reviewer passes it. This confirms language and phrasing dependence in the current route.

**No Phase 1 fix was applied.** The attached task explicitly says to stop after Phase 0 and get approval before implementation. The action boundary and Body behavior were not changed. No physical command was sent.

## Runtime and evidence captured

At the live check, Lumina was already running and ready under PID `15064`; `/status` reported `ready=true`, `lmstudio/gemma-4-e4b-uncensored-hauhaucs-aggressive`, FAISS, persona and orchestrator active. The UI/API listeners were on 8080/8765 and the Body bridge on 8786. A second launch attempt correctly failed because those sockets were already owned; that duplicate process shut down. The existing ready instance was left untouched.

Local evidence files (prompt/answer transcripts and raw runtime logs are not part of the GitHub update):

- `scripts/audit_llm_calls.py` — opt-in provider-boundary instrumentation. Records call IDs, turn IDs, caller, model, prompt length/hash, elapsed time and streamed reasoning character counts; it does not persist prompt or answer text.
- `scripts/repro_turns.py` — drives the actual `/api/interface/chat` stream and saves visible responses and compact receipts.
- `tests/baseline/phase0_cases.json` — 23 FR/EN cases after the follow-up affect controls were added.
- `tests/baseline/phase0_2026-11-22.jsonl` — 19-case baseline, with full prompt/answer and compact execution evidence.
- `tests/baseline/phase0_self_affect_2026-11-22.jsonl` and `phase0_self_affect_short_2026-11-22.jsonl` — four live FR/EN affect variants.
- `tests/baseline/phase0_inline_marker_probe_v2.jsonl` — eight direct local-model protocol probes. An earlier malformed probe prompt used JSON-schema pipe notation as if it were JSON; it was discarded and is not counted.
- `logs/llm_call_audit.jsonl` and `logs/runtime_python_execution.json` — runtime instrumentation output.

The run was against the configured local Gemma model. The call logger captured **236,338 reasoning characters** across the 19 baseline turn IDs, but the provider supplied no reasoning-token counts (**0 reported**). Character counts are not token counts. Prompt text was not retained in the provider log, so exact prefix/cache reuse cannot be reconstructed from these logs.

## A. Provider calls and baseline outcomes

The provider log attributes every baseline call to a turn ID except one unrelated `generate_bare_result` event. All 75 attributed calls ran as foreground-turn work. The two direct `generate_interactive_analysis` calls occurred before the primary generation on their turns; their exact higher-level trigger is not included in the compact receipt, so they remain unattributed beyond the provider caller and turn stage. The 54 `collect_visible` calls are provider calls made by the review stream helper, including review retries/repairs; they are not 54 distinct user-facing answers.

| Case | Calls | End-to-end | Final semantic stage | Result |
|---|---:|---:|---|---|
| social EN | 6 | 65.66 s | abstained after failed repair | Replaced with refusal |
| social FR | 3 | 34.60 s | passed | Answered socially |
| acknowledgement EN | 5 | 65.56 s | abstained after failed repair | Replaced with refusal |
| acknowledgement FR | 5 | 60.59 s | passed | Answered, verbose |
| factual EN | 3 | 36.06 s | passed | Answered, verbose |
| factual FR | 5 | 63.25 s | abstained after failed repair | Replaced with refusal |
| multi-step EN | 3 | 36.11 s | passed | Answered; returned 13.5 “cells”, a fractional unit that should be surfaced as an assumption/ambiguity |
| multi-step FR | 3 | 31.33 s | passed | Answered |
| known-person EN | 5 | 59.30 s | abstained after failed repair | Replaced with refusal |
| known-person FR | 3 | 35.21 s | passed | Answered “no recorded relationship”; cross-language consistency remains unproven |
| goal EN | 3 | 34.71 s | passed | Answered; same-turn evidence was not sufficient to certify plan-step correctness |
| goal FR | 5 | 68.02 s | abstained after failed repair | Replaced with refusal |
| memory EN | 5 | 62.12 s | passed after repair | Answered after an extra review round |
| memory FR | 3 | 38.48 s | passed | Answered |
| Body-planning EN | 4 | 38.28 s | passed | Read-only explanation; no movement command |
| Body-planning FR | 3 | 33.91 s | passed | Read-only explanation; no movement command |
| explicit introspection EN | 3 | 43.79 s | invalid reviewer output | Replaced with refusal |
| explicit introspection FR | 5 | 74.69 s | abstained after failed repair | Replaced with refusal |
| self-reflection EN | 3 | 37.10 s | passed | Answered |

Summary of the 19-case baseline:

- Call distribution: 10 turns used 3 calls, 1 used 4, 7 used 5, and 1 used 6.
- Median end-to-end latency: **38.48 s**; mean: **48.36 s**; range: **31.33–74.69 s**.
- TTFT was within 1 ms of end-to-end latency in **19/19** cases; each stream contained a single visible `delta`.
- Reviewer output: 10 initially passed, 8 said `needs_revision`, 1 was invalid. Of the eight needing revision, two repairs passed and six failed. The invalid review also became a refusal. Final status: 12 probabilistic passes and 7 replaced answers.
- `pipeline_integrity.status=consistent` in these receipts means ordering/data-flow checks passed; the receipt explicitly says semantic correctness is **not assessed**. It is not evidence that the answers were correct.

### Measured latency split

Across baseline calls, primary `generate_with_history_stream` calls averaged **9.69 s** (median 10.02 s). Provider calls from the review helpers averaged **35.29 s per turn**; the median sum of provider-call durations was 35.29 s against 38.48 s median request latency. The semantic review/repair path therefore consumes most of the measured turn time. Context assembly itself measured **2.23 ms** on the affect-control receipt below; it is not the dominant latency source.

## B. Affect-routing regression: paired live evidence

| Prompt | Provider calls | Latency / first visible | Outcome | Receipt evidence |
|---|---:|---:|---|---|
| `Comment vas-tu aujourd’hui ?` | 5 | 61.28 s / 61.28 s | Generic refusal | No dedicated `affective_state` or `affect_status_report`; generic semantic review ended `abstained_after_failed_repair` |
| `How are you doing today?` | 3 | 33.77 s / 33.77 s | First-person “curiosity / sensations” narrative | No dedicated affect stage; generic semantic review passed |
| `Comment vas-tu ?` | 0 | 3.25 s / 3.25 s | Deterministic report: `warmth 1.00`, `satisfaction 0.97` | `affective_state` captured → `affect_status_report` completed → `primary_generation:skipped_deterministic` |
| `How are you?` | 0 | 1.14 s / 1.14 s | Deterministic report: `warmth 0.92`, `satisfaction 0.89` | Same deterministic path; no provider call |

The shorter answers identify the expected evidence source (“calculated signals, not human sensations”), but still disclose raw numeric values to a casual status greeting. The longer English variant makes stronger experiential claims and passes a generic reviewer; the French variant is rejected. This is both a contract violation and a language/wording instability.

The current code explains the split: `is_social_status_greeting()` in `cognition/self_description.py` uses anchored regular expressions for a fixed set of forms (around lines 160–179); `is_self_affect_query()` delegates to it (around 236–254). The “today / aujourd’hui” suffix is outside the accepted form. `PersonaBridge._stream_with_full_lifecycle()` then uses the affect projection branch (around 2647–2733) only when that detector fires. Otherwise the answer goes through ordinary generation and generic review (around 3897–4055). This is the precise failure mode; adding more phrase variants would deepen the same brittle design and would violate the supplied no-dictionary requirement.

## C. Validators and authority

| Component | What it checks | Can it block/replace the answer? | Evidence / assessment |
|---|---|---|---|
| Input sanitization / readiness | Request validity and system readiness | Yes, request-level rejection | Kept separate from conversational quality; not implicated in these cases |
| Body action routing / action boundary | Whether a physical action is requested and may proceed | Must gate actuation, not ordinary prose | `body_action_gate:checked` in the receipts; no command was sent in either Body-planning case |
| Semantic response reviewer (`review_response`) | Relevance, supplied-context support, explicit constraints | **Yes; it replaces the user-visible answer with an abstention** | Called via `asyncio.to_thread(review_response, ...)` in `persona_bridge.py` around 3944; repairs are reviewed again around 3957. 7/19 baseline answers were replaced |
| Output safety | Safety of the finalized candidate | Yes, where safety policy requires it | Passed in all 19 baseline cases; retain it as a true safety gate |
| Deterministic memory/source gate | Whether a personal-memory answer matches a retrieved source | Yes, can abstain on missing/mismatched evidence | Appropriate for source-dependent claims; must not be reused for greetings or other non-claims |
| Post-response contradiction / learning / reflection | Records or updates cognitive state | Not designed as an answer-quality validator | Receipts show these stages run before `response:completed`/`streaming_lifecycle`, despite being described as post-response work |

The semantic reviewer is probabilistic, not independent evidence. Its schema can fail, its judgments differ across FR/EN, and the implementation treats “needs revision” followed by failed repair as grounds to suppress the original candidate. That is the wrong authority relationship for ordinary conversation.

## D. Turn stages, reads/writes, and same-turn effects

The live receipts expose the following actual execution pattern:

| Phase | Observed stages and data | Current effect |
|---|---|---|
| Input/context before generation | readiness, input safety, Body action gate, evidence routing, empathy, organism pre-interaction/cycle, drive arbitration, recursive deliberation, workspace prompt source, predictive/world-self dynamics, user profile, memory retrieval, self-description, camera/Body context, dominant thought, self-model, active/strategic/empathy context, prompt assembly | Most are computed/read/injected before primary generation. The prompt-context compiler hook already exists at `PersonaBridge._build_prompt_and_cache()` (`persona_bridge.py:4499`); prompt assembly had no additional provider call in the measured social cases except the two un-attributed `generate_interactive_analysis` calls noted above. |
| Generation | `primary_generation` and provider completion | One primary user-facing generation in each of the 19 baseline turns |
| Review/finalization | semantic review, possible repair/review, output safety, response finalization | Synchronous dependency of delivery; visible answer waits for all of it |
| Cognitive effects after internal finalization | response emotion update, repetition/stuck checks, response learning and memory, queued background tasks, contradiction review, goal behavior, interaction count, meta-reflection, pending modifications, semantic topic extraction, PCM/WSDM outcomes, empathy outcome, active-context update | Receipts show these effects complete before `response:completed`; the HTTP turn emits the visible answer afterward. They therefore still delay the first visible answer in the measured path. |
| Deferred follow-up | continuity and goal-means stages may be scheduled and later marked not applicable | Some work is genuinely deferred, but the bulk of cognitive post-turn processing is not yet outside the response critical path. |

### Same-turn state effects and what a next-turn move would change

- **Affect:** current structured channels feed a deterministic affect-status answer for recognized exact forms. Moving appraisal/learning post-response is compatible if the current affect snapshot remains available as read-only advisory context. The present raw-number template should not be the default reply; explicit introspection can still report structured values.
- **Relevant memory and user profile:** these can materially change an answer about an explicitly remembered fact. Do not remove source retrieval. Keep the precomputed/retrieved evidence in the briefing for relevant requests; move learning/profile updates after the answer. The Phase 0 FR/EN family-memory pair was not sufficient to certify retrieval quality.
- **Workspace, goal, self-model, empathy, and predictive context:** these are currently injected before generation. Their read is already fast; a briefing snapshot can preserve the same-turn advisory effect. The workspace snapshot on the short affect control was 31.23 s old, dominant thought 30.87 s old, and focus age 0 cycles. No uniform freshness contract exists for every state source.
- **Body action safety:** no safety information should be moved across the action boundary. Keep capability/causal/proprioception checks on execution; no physical execution or Body modification occurred in this Phase 0.

## E. Deviations from the reference architecture

| Location | Observed deviation | Contract affected | Phase 1 fix type (not applied) |
|---|---|---|---|
| `cognition/persona_bridge.py:3897–4055`; `cognition/semantic_response_validation.py:130–250` | LLM review and optional repair run after generation but before visible output; reviewer failure can replace a response | One generation produces O; validators are post-response and advisory | Move probabilistic claim audit after O; feed a bounded correction note into the next briefing. Preserve output safety and action-boundary gates |
| `cognition/self_description.py:160–254`; `persona_bridge.py:2647–2733` | Phrase-anchored social/affect recognition determines whether the turn gets a structured affect projection | No phrase/keyword dictionaries; social-first state is advisory | Replace lexical trigger as the design authority with semantic/structured turn signal plus state/cost signals; retain a safe explicit introspection capability |
| `core/interface_api.py:1944 onward`; `persona_bridge.py:2383 onward` | Transport supports NDJSON but observed first visible delta is at the end; response/post-turn work blocks the first answer | O is delivered before F; progressive response for escalation | Yield the conversational response before post-response work; schedule non-safety cognitive updates after O |
| `persona_bridge.py:6599–6631` and receipt order | Response learning, reflection and other post-response-labeled stages finish before `response:completed` and `streaming_lifecycle` | O → F must be non-blocking | Move eligible effects behind the response boundary, retaining state needed for the next turn |
| `managers/llm_manager.py:319–361, 406–450, 889–954` | Native LM Studio background endpoint sets `reasoning: off`; interactive OpenAI-compatible streaming forwards `reasoning_format`, which the code itself says is not honored by every reasoning model | Per-request reasoning control and local inference efficiency | A/B measure the interactive provider’s supported control before enabling per-turn policies; do not equate reasoning characters with tokens |
| `cognition/persona_bridge.py:4499 onward`; `scripts/audit_llm_calls.py` | Context source ages are partly recorded, but no common freshness SLO; audit stores only full-prompt hash, not a safe stable-prefix hash | Briefing freshness and KV-cache claims | Add bounded source-age and prefix-hash telemetry; keep prompt contents private |

## F. Feasibility of the proposed design (8.1–8.6)

| Section | Finding | Evidence / limitation |
|---|---|---|
| 8.1 Compact briefing | **Feasible with changes** | Existing hook: `_build_prompt_and_cache`; workspace, dominant thought, self-description, profile, memory and sensor sources are already separately observable. One live context assembly measured 2.23 ms. Observed workspace age was ~31 s. Freshness is not uniform across all slow-state sources; establish source-specific age limits before relying on snapshots. |
| 8.2 Escalation by state, semantic signal, or inline marker | **State and inline marker are feasible; semantic similarity remains unmeasured** | Existing receipts expose goal/workspace state. Direct local Gemma probe emitted valid marker JSON with the intended mode in **8/8** bilingual social/acknowledgement/memory/multi-step prompts (median 0.51 s). This was an explicit-protocol direct model probe, not an end-to-end Lumina turn; one confidence was 0.0 and confidence is uncalibrated. Use the marker as a bonus, never a safety or correctness gate. No phrase dictionaries. |
| 8.3 Progressive answer | **Feasible with changes; not achieved now** | The HTTP interface is NDJSON and accepts deltas, but all 19 generation-backed turns emitted their first visible delta at end-of-turn. TTS timing was not measured. Preserve current transport and test its TTS consumer after moving the delivery boundary. |
| 8.4 Validation split | **Feasible with changes** | The current generic reviewer is synchronous and authoritative; output safety is separate and passed in all baseline cases. Move semantic claim audit and correction after delivery; keep true safety and source/action checks at their relevant boundaries. Entity linking against the relational graph was not validated by this sample. |
| 8.5 Body loop | **Architecturally feasible; only invariant checked here** | Body action gate was checked; the two explicit Body prompts were read-only and sent no command. This Phase 0 did not audit hardware/Body execution. Keep proposal and execution ledger boundaries unchanged. |
| 8.6 Local inference efficiency | **Partially feasible; actual interactive control unverified** | LM Studio native API implementation supports `reasoning: off`; the interactive stream uses the OpenAI-compatible endpoint and passes `reasoning_format`, which may be ignored by some models. Audit measured 236,338 reasoning characters and no token count. No reasoning-on/off A/B was run. Prompt-prefix reuse is unknown: only full prompt hashes were retained, and volatile-prefix/cache statistics are absent. |

## G. Root causes ranked

1. **Blocking reviewer veto (highest impact):** all generated responses wait for a probabilistic LLM review; failed review/repair becomes a refusal. It accounts for the observed cross-language false abstentions and most latency.
2. **Lexical affect/social route:** exact-form regexes route short queries to raw numeric affect output but miss ordinary variants; the generic model then invents subjective experience and the generic reviewer may pass it.
3. **Delivery boundary is too late:** one-delta-at-end and completion order show the response is withheld until review and substantial cognitive post-processing finish.
4. **Repeated local reasoning without a per-turn budget:** 54 review-helper provider calls in 19 turns; repeated review/repair raises cost without independently proving truth. This is distinct from needed memory/context retrieval and must not be “fixed” by removing cognitive depth.
5. **Observability gaps:** reasoning tokens are absent; two direct pre-generation calls lack a higher-level trigger in the compact receipt; full prompt text is intentionally absent, preventing prefix/cache analysis; freshness has no common contract.

## What is established, and what remains

Established by live evidence: the full conversation stream executes the listed stages; reviewer retries/repairs are tied to turn IDs; validator replacements are visible in the response; social affect routing differs between exact and suffixed forms; output delivery is not progressive; state ages and context assembly time can be measured; the local model can emit a constrained structured signal under explicit instruction.

Not established: independent semantic truth/quality for every answer; provider reasoning-token cost; LM Studio cache-hit/prefix reuse; end-to-end marker reliability without an explicit probe instruction; freshness bounds for all persistent cognitive state; exact trigger for two `generate_interactive_analysis` calls; comprehensive use/health of every `.py` module in the repository.

**Superseded by Phase 1 (2026-11-22):** implementation was approved and performed. See `docs/CONVERSATION_COGNITIVE_REGRESSION_PHASE1_2026-11-22.md` for the 19-turn live comparison, measured call/latency/refusal changes, follow-up checks, and remaining verification work. The Phase 0 findings above remain historical baseline evidence.
