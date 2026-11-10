# Lumina Brain workflow audit — 2026-11-09

**Scope:** Brain application and cognitive workflow only. This report excludes the Body runtime and hardware implementation. It combines source tracing with focused offline tests. No live Lumina process or provider call was available for runtime confirmation.

## Summary

- Catalogued **279 Brain-side Python modules/files** (cognition, core, managers, pages, reasoning/physiology/psychology utilities, Brain visualizer, and the `app.py` / `brain.py` entrypoints).
- AST parsing succeeded for all catalogued files. Static import edges show likely reachability, not proof that a module executes or works. Runtime conditionals, route registration and optional subsystem initialization must be observed separately.
- The active conversational path is `pages/main_page.handle_send` → security/input handling → optional Brain-PC vision capture → `PersonaBridge.get_response_stream` → `_stream_with_full_lifecycle` → primary or deterministic response → output checks → post-turn processing. `PersonaBridge.get_last_turn_trace()` now records per-stage outcomes; `/interface/status` exposes the latest trace.
- The cognitive organism also runs an internal thought loop; the autonomous orchestrator is initialized and started by both launch paths. Previously, regular typed turns did not deliver their text into that orchestrator event queue. This has been fixed in the current worktree.

## Brain workflow, end to end

1. **Startup:** `start.bat` runs `app.py`; `BrainOnly.bat` runs `brain.py`. Both initialize the shared `core.state.state` and its LLM, PersonaBridge, CognitiveOrganism, memory and optional managers. The full app registers NiceGUI pages and starts the interface; Brain-only starts its API and background services.
2. **Input boundary:** `pages/main_page.py:handle_send` rejects empty input, rate-limits and sanitizes text, and updates presence state. Network-dialogue handling may consume the turn.
3. **Perception:** when configured and the Brain-PC camera is active, the UI captures a frame once and passes the result into the turn. The camera manager can also supply its latest working-memory context. The turn path distinguishes this Brain-PC evidence from other sources in `PersonaBridge`.
4. **Cognitive pre-turn:** `PersonaBridge.get_response_stream` applies input safety and routes physical-action intents through its separate guarded path. Ordinary turns enter `_stream_with_full_lifecycle`, which evaluates temporal and quantitative questions, checks goal-means follow-up state, reads human empathy context, runs `CognitiveOrganism` pre-interaction/update/arbitration and recursive deliberation, retrieves appropriate memory, adds conditional inner-monologue/epistemic/relational/research context, prepares PCM/WSM predictions plus prospective deliberation, and builds the prompt. Applicability and failures are visible in the turn trace.
5. **Generation:** an eligible simple human turn may be answered by the optional fast first-pass model. Otherwise `LLMManager.generate_stream` is the user-facing stream; deterministic constraints can bypass provider generation. Reasoning-tag handling and the quantitative/goal-means output guard run before finalization. Background bare generation is reserved for internal tasks.
6. **Post-turn:** output safety, final-answer recovery (when required), response sanitization, empathy/abstract-reasoning/active-context outcomes, and the cognitive post-turn step finish before the serialized turn releases. Human turns retain memory/profile/background-learning updates. Peer turns still undergo cognitive evaluation and predictive learning but do not enter the human episodic/personal memory, human interaction count, or human profile learner.
7. **Between turns:** `InternalThoughtLoop` runs scheduled cognitive cycles; `AutonomousOrchestrator` consumes queued user/external events and advances its drives/workspace/execution cycle. Before this change, the web path queued only a blank voice-start event, not the actual text turn.

## FLUX / child conversation path

- **Master Lumina speaking to FLUX:** opening, replies, topic pivots, and generated dialogue summaries all use `PersonaBridge.get_response_stream()` through a peer-scoped user ID, transcript, and identity prompt. The current FLUX message is kept separate from prior history, and Body actions are disabled. This path does **not** call `AgentController`.
- **FLUX sending a message to master Lumina:** `LuminaNetwork.receive_from_child()` routes the inbound message through `PersonaBridge.get_response_stream(user_id="lumina_child_<id>")`. This uses the same PersonaBridge conversation lifecycle with a child-specific user identity; it does **not** call `AgentController`.
- **Master messages arriving at the FLUX Brain (`/lumina-network/chat`):** this endpoint now uses `PeerConversationStore` and the same peer-scoped PersonaBridge lifecycle (`record_history=False`, `peer_name`, `allow_body_actions=False`). Each sender/conversation pair has its own bounded transcript. It does not write the exchange to shared FAISS or human LLM history, and provider failure returns HTTP 503 rather than a false empty success.
- **Why `AgentController` is not the child-chat controller:** its `process()` / `process_stream()` signatures do not accept the child-specific `user_id` and its implementation reads the active human user from `user_manager`. Routing FLUX through it as-is would risk assigning child dialogue to the human user’s memory and relationship state. The source has no production call site from `LuminaNetwork` to `AgentController`.
- Shared FAISS episodic/personal/visual/event recall, session camera visuals, configured human location, global third-party relationship graph, human profile learning, and human-only post-turn memory are excluded from peer prompts/updates. Peer transcript and pair-specific relational memory remain available. The peer cognition is also submitted to the Global Workspace with `peer_cognition` provenance.
- Outbound peer exchanges remain in `LuminaNetwork._history` and the pair-specific relational model; they are not written to shared FAISS memory, which is queried by human turns.
- The removed page/app `AgentController` objects were unused allocations; removing them does not remove either FLUX route. The class and `core` export remain intact.

## Fixes applied in this worktree

- **Vision attachment order:** the persona starts its organism before `AppState` creates the vision manager. The old attachment attempt occurred too early and was skipped. A single `_wire_vision_to_cognition()` now runs after vision creation and after vision reload; it attaches the manager to the loop/organism and records success.
- **Truthful core readiness:** `AppState.ready` was set from `bool(llm)` alone. It now requires both the LLM manager and a ready `PersonaBridge`, and is set after initialization wiring completes. Failed core startup remains degraded instead of falsely opening the readiness gate.
- **Real orchestrator input:** accepted human text is now queued through `AppState.notify_user_turn()` at the main page, `/interface/chat`, Brain-only `/chat`, and the Brain CLI. Empty turns are ignored; FLUX peer turns and proactive/internal generations do not masquerade as operator input. The prior empty voice-start event remains an activity signal; recognized text arrives separately through the accepted-turn path.
- **Deferred cognition on every interactive entrypoint:** continuity review and structured goal-means analysis now share `AppState.schedule_deferred_cognitive_stages()`. The main page, interface API, Brain-only streaming/non-streaming REST, and Brain CLI schedule these only after a successful visible answer, off the response path; one deferred stage raising does not suppress the other.
- **One declared chat route:** unused `AgentController` instances were being constructed in `app.py` and UI pages while chat went directly through `PersonaBridge`. Those dead instances/imports were removed; the standalone `core/agent_controller.py` implementation remains available for a deliberate future migration. Comments now describe the real PersonaBridge path.
- **Workflow observability:** `/interface/status` now includes `brain_workflow`, exposing readiness, active response pipeline, PersonaBridge/chat stage, organism, internal loop/thread/cycle count, global workspace, memory, Brain-PC vision attachment/camera state, and orchestrator availability/running state. This is read-only and does not trigger cognitive work.
- **Cognitive loop health evidence:** workflow status now distinguishes initialized organism/loop modules from execution. It reports internal fast/slow cycle timestamps and error counts, plus orchestrator task liveness, cycles, last successful cycle time and error count/type. These are runtime indicators; module initialization alone is not evidence that every module's behavior is correct.
- **FLUX full cognitive path:** master openings/replies/topic pivots/summary and child messages use the same PersonaBridge lifecycle. Pair history is passed separately from human LLM history; failed scoped generation fails closed. Tests assert no Body action routing, no shared human history writes, transcript continuity, and summary routing.
- **FLUX receiver-side isolation:** the receiving Brain’s `/lumina-network/chat` previously called PersonaBridge as an ordinary user and then persisted peer dialogue in shared FAISS and the LLM’s human history. It now uses a dedicated bounded per-pair transcript, the peer cognitive scope and fail-closed HTTP status; these shared human writes were removed.
- **FLUX identity keying:** master-side `LuminaNetwork._history` was keyed only by `conversation_id`, allowing two child peers that reused an ID to read each other’s turns. It is now keyed by `(peer_id, conversation_id)`, and the dialogue inspection route supplies the peer ID. Legacy lookup returns a transcript only if the ID resolves to exactly one peer; ambiguous IDs return no transcript.
- **Peer learning boundary:** peer turns no longer update human affect as though a person arrived, record human profile facts, or append peer dialogue to the human episodic memory. Outbound FLUX transcripts are not stored in the shared FAISS index. Cognitive post-response evaluation remains active and receives `human_interaction=False`, so response-length heuristics do not report human-help satisfaction.
- **Peer live-evidence boundary:** a source review found that camera and Body observations were still appended to every prompt even though memory/history were scoped. Prompt assembly now injects Brain-PC camera/face evidence and live Body telemetry only for human turns; peer turns explicitly trace both sources as `skipped_by_scope`. Peer-supplied Brain-PC vision input is rejected before it can enter the pending prompt or session visual buffer. Peer turns also skip human empathy read/outcome updates while retaining the shared cognitive and peer-evaluation stages. Unit tests assert that FLUX cannot call either live evidence provider and that human turns still receive both sources.
- **Peer cognitive-prompt scope and role consistency:** the global Active Cognitive Context contains unscoped human topics, presence and visual summaries, while the concrete self-model block could expose the latest global thought and count of Brain-camera scenes. Peer prompt assembly now omits the unscoped ACC and EmpathyEngine fragments, hides the human-scoped thought/visual count, and does not reuse the human chat's last-turn age as FLUX continuity. A direct prompt contradiction that called every sender human is replaced with an explicit human-vs-AI-peer role instruction; memory guidance now tells a peer to use its pair transcript rather than claiming no prior memory. Shared self-model, personality, strategic posture and pair-keyed abstract reasoning remain eligible. Each fragment is traced as injected, empty, unavailable, failed or skipped by scope; human prompts retain ACC and empathy. FLUX response-length heuristics no longer nudge Lumina's global emotional state. Tests cover both peer and human prompt fragment behavior and role text.
- **Per-source evidence trace:** Body runtime observations, Global Workspace Body cache records and Brain-PC camera status now have privacy-safe age/freshness summaries in the per-turn trace. These summaries contain counts and ages, not sensor values, scene descriptions, face names or dialogue text. Metric collection is non-blocking and cannot mark already-injected evidence as failed.
- **Peer working-context write isolation:** a follow-up audit found a prompt/write asymmetry: although peer turns no longer read the human Active Cognitive Context, their post-turn response was still merged into its global topic store. Peer turns now skip that global write; human turns continue updating ACC. A regression test asserts both behaviors.
- **Predictive FLUX transition isolation:** network latency previously allowed a peer exchange to share PCM/WSDM single-slot `_pending` state with a human turn. FLUX now records detached, pair-scoped before/after snapshots; its transition cannot clear another turn's pending state. Peer exchanges without an explicit evaluator stay neutral instead of receiving a positive/negative label from response length or punctuation.
- **WSDM slow-cycle race:** the periodic internal thought loop could consume WSDM's pending response context before the reply completed. WSDM outcomes are now finalized only in the matching per-response post-interaction path, consistent with PCM; the slow cycle still initializes WSDM but no longer closes a chat turn.
- **Predictive calibration target:** PCM/WSDM calibration previously compared predicted energy direction with the interaction's `outcome` label, which the post-turn path derives from global emotional valence. These are different signals. Calibration now compares the prediction to the measured cognitive-energy delta (`state_after[0] - state_before[0]`); the valence label remains record metadata and cannot masquerade as measured energy change.
- **Autonomous peer opener scope:** opening messages no longer receive the global emotion, latest ARE open question, or workspace winner, because those values are not scoped to the peer conversation. The opener uses the requested seed topic and pair-specific relational state; PersonaBridge supplies the shared self-model/personality context. A regression test checks the three human-derived fields are absent.
- **Predictive pre-turn stages on the actual stream:** static call-site tracing showed that production chat uses `PersonaBridge` streaming and never calls `CognitiveOrganism._call_ai_system`; consequently its PCM action recording/advisory, WSM context/narrative and prospective deliberation were absent before generation even though post-turn attempted to resolve pending predictions. `CognitiveOrganism.prepare_response_context()` now owns those pre-response stages and is called by prompt assembly for both human and peer turns. It adds available advisory/narrative context to the prompt and traces each module as prepared, unavailable or failed. The old `_call_ai_system` still has its compatibility path; peer endpoint-specific PCM/WSM recording and response-length/question-mark outcome heuristic were removed so inbound FLUX uses the same cognitive lifecycle and outcome source as other PersonaBridge turns.
- **Failure transcript hygiene:** scoped-generation failures and HTTP/child transport errors remain status conditions; they are no longer appended as assistant/peer utterances to either side's conversation transcript.
- **FLUX same-thread ordering:** simultaneous inbound or outbound turns for one `(peer_id, conversation_id)` are serialized with a bounded event-loop-local lock. This prevents two generations from reading the same stale transcript and committing answers out of order; distinct peers/conversations remain concurrent and isolated. A concurrency regression test verifies the later prompt sees the completed earlier exchange.
- **Post-turn cognitive trace accuracy:** required post-response stages now record success/failure in the per-turn trace. If response learning/memory or background-task scheduling raises, the wrapper no longer reports `cognitive_post_turn` or the whole turn as cleanly completed; peer post-turn evaluation has its own status and still avoids human-learning side effects.
- **Per-turn stage trace:** the latest turn trace has a turn ID, scope, start/end timestamps and explicit stage states for safety, empathy, temporal/quantitative/goal-means analysis, organism cycle/arbitration/deliberation, memory retrieval, generation, output safety/recovery, post-turn modules, and finalization. The status snapshot returns a detached copy and never includes prompt or message text.
- **Previously dormant structured goal-means analysis:** the source contained `analysis_prompt()` and `parse_analysis()` but no caller, so practical choices only received a generic prompt contract and follow-up state was never populated. The Brain now schedules the bounded JSON analysis after the visible answer, validates/parses it, stores it by user/pair ID for up to three follow-up turns, and exposes its status through `brain_workflow`. It does not add a second generation before the user-facing response.
- **Practical FLUX turns now run the structured goal-means stage too:** the stream had explicitly marked this stage `contract_only_peer_scope`. A practical peer turn now queues the same bounded analysis after the visible reply and stores follow-up state under `peer:<child_id>:<conversation_id>`, so neither another peer nor a new conversation can consume it. Human turns continue to use the shared AppState post-answer scheduler, avoiding a duplicate second analysis call. Turn traces distinguish `scheduled_by_entrypoint`, `completed`, `deferred`, `unavailable`, invalid output, and failure.
- **Cognitive-stage reliability telemetry:** `/interface/status.brain_workflow.components.persona_bridge.last_turn` now includes privacy-safe `stage_health`: per-stage observation/status counts, last status/time, last successful time, and last error summary. No prompt, user text, or sensor payload is stored in this health summary. Invalid structured output and unavailable required analysis now prevent the turn trace from being reported as fully successful.
- **Orchestrator health truthfulness:** `brain_workflow_status()` previously reported `running` from the orchestrator's requested `_running` flag alone. If its asyncio task had exited unexpectedly, the health page could still say it was running. It now reports effective `running` only when both the requested state is true and the task is alive, while exposing `requested_running` separately. Regression tests cover dead-task and stopped-but-live-task cases.
- **Read-only Body question routing:** factual Body questions previously invoked the Body action-intent classifier before returning to the ordinary LLM path. That unnecessary classification could misroute a sensor, battery, GPS, or capability question and added a second chance for the wrong handler to answer. Such read-only questions now continue through the full PersonaBridge cognitive turn and its timestamped Body/camera provenance; explicit destination locomotion requests remain on the guarded planner/classifier path. The specific autonomy-audit request uses its existing evidence-bounded audit response directly. Tests verify Body sensor/battery/GPS questions bypass the action classifier and destination movement still reaches it.
- **Read-only diagnostic route consistency:** a legacy test expected the Body diagnostic classifier to return a fixed sensor digest directly. The implementation intentionally returns `None` so the accepted turn continues into the main cognitive prompt, where the LLM can analyze timestamped evidence. Updated the stale assertion to test that routing and verify no motor-plan assessment occurs.
- **Pytest-safe diagnostic scripts:** two scripts under `scripts/` performed work at import time. The camera diagnostic could open physical cameras during pytest collection, and the reloop verifier called `sys.exit()` during collection. Both now run their procedural checks only under `if __name__ == "__main__"`; this keeps direct-script behavior while making test discovery side-effect free.
- **Current simulator-context contract:** updated the world-model context test to assert the current `BODY WORLD-MODEL CONTEXT` heading and safety wording instead of the obsolete pre-migration header.

## Remaining Brain-side work to complete a reliable evaluation

1. **Live run evidence:** run a real human turn and a real FLUX turn in Lumina, then inspect `/interface/status.brain_workflow.components.persona_bridge.last_turn`. Offline tests cannot confirm installed provider health, runtime-only optional modules, or UI event completion.
2. **Context provenance/freshness:** direct Body observations, the Body workspace cache and Brain-PC camera now have privacy-safe age/status summaries. Cognitive prompt modules such as self-model, strategic context, empathy, abstract reasoning and memory still expose invocation outcomes rather than their own source age/record counts.
3. **Subsystem lifecycle visibility:** optional cognitive modules still need `enabled`, `initialized`, `last_success`, `last_error` and skip-reason snapshots outside the per-turn stages. Static imports remain insufficient evidence.
4. **Other entrypoints:** the NiceGUI page, `/interface/chat`, proactive messages, and internal thought loop do not all share identical turn semantics. The interactive chat paths share PersonaBridge, while proactive/internal work is deliberately not a human turn. Continue testing each entry point separately.

## Latest verification

- Brain cognitive workflow set: **177 passed, 12 subtests passed** across 24 targeted suites, including human/FLUX lifecycle, goal-means, predictive context, command-safety routing, interface and workflow status. New coverage verifies deferred-stage results attach to the originating turn even after a newer turn starts.
- The standalone contradiction/reloop cognitive verifier still works when explicitly run: **14/14 checks passed**.
- Repository-wide run after the test-discovery fixes: **692 passed, 28 failed, 2 skipped, 86 subtests passed**. The 28 remaining failures are in Body host/perception/runtime, FNK/IMU, camera/depth, and Quest HUD/VR suites; they are outside this Brain-only audit and have not been changed here. There was no collection error after guarding the scripts.
- `py_compile` and `git diff --check` pass for the changed Brain/test/report files. `git diff --check` prints Git LF→CRLF conversion notices for modified worktree files; these are not whitespace errors.
- Local ports 8765 and 8786 were not listening during the check. Process command-line inspection was denied by Windows CIM access, so no live Brain/provider turn or start.bat runtime status is claimed.

## Current limits

- The changes are source-level fixes; no live Lumina process was queried and no conversational run was observed.
- The latest integrated focused run passed **177 tests across 24 suites, plus 12 subtests**. Coverage includes the end-to-end interface API, workflow status, PersonaBridge streaming, predictive context, peer/FLUX routing and scoping, memory fallback/retrieval/reliability, identity, goal-means, cognitive streams, fast-round, Body factual routing/context, Body route memory, quantitative reasoning, evidential self-model, goal completion, intention planning, goal semantics cache, PCM/WSDM concurrent-turn isolation, measured-delta calibration, and deferred-result turn attribution. These remain offline tests, not live provider or peer-network evidence.
- The prior repository-wide run found **692 passed, 28 failed, 2 skipped, and 86 subtests passed**. It has not been rerun since the latest Brain changes. The 28 recorded failures were in Body/VR/host/perception/camera areas; do not interpret the whole repository as green.
- The report does not label every cognitive module “working”: that requires runtime stage evidence, not static imports.

## Brain-side module inventory

| File | Static production importers | Classification |
|---|---:|---|
| `app.py` | 0 | runtime entrypoint |
| `brain.py` | 0 | runtime entrypoint |
| `brain_visualizer/brain_visualizer.py` | 1 | visualization utility / optional tool |
| `brain_visualizer/convert_brain.py` | 0 | visualization utility / optional tool |
| `brain_visualizer/debug_bridge.py` | 1 | visualization utility / optional tool |
| `brain_visualizer/download_brain.py` | 0 | visualization utility / optional tool |
| `brain_visualizer/example.py` | 0 | visualization utility / optional tool |
| `brain_visualizer/lumina_brain_bridge.py` | 1 | visualization utility / optional tool |
| `brain_visualizer/network_mapping.py` | 0 | visualization utility / optional tool |
| `brain_visualizer/obj_loader.py` | 0 | visualization utility / optional tool |
| `brain_visualizer/particles.py` | 0 | visualization utility / optional tool |
| `brain_visualizer/shaders.py` | 0 | visualization utility / optional tool |
| `brain_visualizer/test_renderer.py` | 0 | visualization utility / optional tool |
| `cognition/__init__.py` | 6 | statically referenced; runtime activation still conditional |
| `cognition/ablation.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `cognition/abstract_reasoning_engine.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/active_cognitive_context.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/active_empathy.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/advanced_thought_evaluator.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/ai_identity.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/ai_system.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/arbitration.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/arbitration_learning.py` | 5 | statically referenced; runtime activation still conditional |
| `cognition/aspirational_self.py` | 3 | statically referenced; runtime activation still conditional |
| `cognition/aspirational_synthesis_engine.py` | 4 | statically referenced; runtime activation still conditional |
| `cognition/attention_system.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/attractor_system.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/autonomous_curiosity_resolver.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/autonomous_experimentation.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/autonomous_reflection.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/behavioral_conditioning.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/belief_bootstrapper.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/body_capability_learning.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/body_plan_compiler.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/body_runtime/__init__.py` | 8 | statically referenced; runtime activation still conditional |
| `cognition/body_runtime/__main__.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `cognition/body_runtime/bridge.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `cognition/body_runtime/home_assistant_plugin.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/body_runtime/remote.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/body_runtime/robot_capabilities.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/body_runtime/runtime.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/body_runtime/self_model.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/body_runtime/standalone.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/calibration_engine.py` | 4 | statically referenced; runtime activation still conditional |
| `cognition/capability_development.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/causal_ledger.py` | 3 | statically referenced; runtime activation still conditional |
| `cognition/causal_mechanism_model.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/cognitive_attention_engine.py` | 3 | statically referenced; runtime activation still conditional |
| `cognition/cognitive_audit_engine.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/cognitive_behavior_gate.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/cognitive_dissonance_engine.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/cognitive_flux_engine.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/cognitive_immune_system.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/cognitive_observatory.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/cognitive_organism.py` | 6 | statically referenced; runtime activation still conditional |
| `cognition/cognitive_preprocessor.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/cognitive_resource_economy.py` | 3 | statically referenced; runtime activation still conditional |
| `cognition/cognitive_restructuring_engine.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/cognitive_stack.py` | 3 | statically referenced; runtime activation still conditional |
| `cognition/cognitive_validator.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/communication_calibrator.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/consequence_tracker.py` | 3 | statically referenced; runtime activation still conditional |
| `cognition/contextual_attention_memory.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/contradiction_belief_reviser.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/contradiction_handler.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/counterfactual_simulator.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/creative_divergence.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/cross_layer_feedback.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/curiosity_engine.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/decision_commitment.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/decision_policy.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/decision_pressure.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/dominant_thought_selector.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/dream_synthesis.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/emergence_metrics.py` | 7 | statically referenced; runtime activation still conditional |
| `cognition/emotional_memory.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/emotional_state.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/empathy_engine.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/epistemic_efficacy_model.py` | 5 | statically referenced; runtime activation still conditional |
| `cognition/epistemic_integrity_engine.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/ethical_reasoning_engine.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/executive_arbitration.py` | 5 | statically referenced; runtime activation still conditional |
| `cognition/experiential_learning.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/flux_mind_model.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/generative_aspiration_engine.py` | 4 | statically referenced; runtime activation still conditional |
| `cognition/genuine_choice.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/global_workspace.py` | 3 | statically referenced; runtime activation still conditional |
| `cognition/goal_action_executor.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/goal_completion.py` | 3 | statically referenced; runtime activation still conditional |
| `cognition/goal_consolidator.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/goal_engine.py` | 4 | statically referenced; runtime activation still conditional |
| `cognition/goal_means_reasoning.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/goal_quality_filter.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/goal_semantics.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/goal_system.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/grounded_introspection.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/identity_boundary.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/identity_constraint.py` | 5 | statically referenced; runtime activation still conditional |
| `cognition/identity_grounding.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/inner_monologue_engine.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/inner_monologue_engine_old.py` | 0 | legacy candidate; confirm before removal |
| `cognition/intention_reasoner.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/internal_cognitive_state.py` | 6 | statically referenced; runtime activation still conditional |
| `cognition/introspective_observer.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/life_stage_prompting.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/long_horizon_planner.py` | 4 | statically referenced; runtime activation still conditional |
| `cognition/loop_observability.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/lumina_network.py` | 3 | statically referenced; runtime activation still conditional |
| `cognition/memory_breadth_audit.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/memory_intrusion.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/memory_retrieval.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/meta_cognition.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/meta_learning_audit.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/meta_reflection.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/meta_thread_evaluator.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/metacognitive_interrupt.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/motivational_field.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/multilingual_affect.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/narrative_arc_writer.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/narrative_compression.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/narrative_identity.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/narrative_synthesizer.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/persistent_executive_loop.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/persona_bridge.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/personality_evolution.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/phenomenal_binder.py` | 3 | statically referenced; runtime activation still conditional |
| `cognition/predictive_consequence_model.py` | 4 | statically referenced; runtime activation still conditional |
| `cognition/predictive_mind.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/preference_engine.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/presence_engine.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/pressure_system.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/priority_engine.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/proactive_outreach.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/prompt_context_budget.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/prospective_deliberation.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/quantitative_reasoning.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/recursive_deliberation.py` | 4 | statically referenced; runtime activation still conditional |
| `cognition/recursive_deliberation_old.py` | 0 | legacy candidate; confirm before removal |
| `cognition/reflection_absorber.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/reflection_controller.py` | 5 | statically referenced; runtime activation still conditional |
| `cognition/reflection_proposal_bridge.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/relational_knowledge_graph.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/relational_memory.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/reply_guard.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/research_mcp/__init__.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/research_mcp/claude_search.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `cognition/research_mcp/controller.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/research_mcp/evaluator.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/research_mcp/memory_integrator.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/research_mcp/planner.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/research_mcp/rac.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/research_mcp/rss_registry.py` | 4 | statically referenced; runtime activation still conditional |
| `cognition/research_mcp/schemas.py` | 8 | statically referenced; runtime activation still conditional |
| `cognition/research_mcp/search_providers.py` | 3 | statically referenced; runtime activation still conditional |
| `cognition/research_mcp/stealth_browser.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/research_mcp/synthesizer.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/research_mcp/web_agent.py` | 5 | statically referenced; runtime activation still conditional |
| `cognition/resolution_engine.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/safety_constraints.py` | 3 | statically referenced; runtime activation still conditional |
| `cognition/self_concept.py` | 3 | statically referenced; runtime activation still conditional |
| `cognition/self_concept_synchronizer.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/self_correction_engine.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/self_description.py` | 6 | statically referenced; runtime activation still conditional |
| `cognition/self_model.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/self_model_influence.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/self_model_moment.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/self_modification.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/self_revision_engine.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/semantic_consolidator.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/semantic_extractor.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/semantic_graph_cleaner.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/semantic_memory.py` | 3 | statically referenced; runtime activation still conditional |
| `cognition/simple_thought_evaluator.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/skill_registry.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/societal_awareness.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/strategic_cognitive_engine.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/structural_coupling.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/symbol_system.py` | 9 | statically referenced; runtime activation still conditional |
| `cognition/temporal_anchor.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/temporal_projection.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/temporal_reasoning.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/temporal_self_projection.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/temporal_weave.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/tension_engine.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/tension_topics.py` | 3 | statically referenced; runtime activation still conditional |
| `cognition/thought_goal_linker.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/thought_stream.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/thought_thread_engine.py` | 5 | statically referenced; runtime activation still conditional |
| `cognition/thread_identity_linker.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/thread_lifecycle_manager.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/thread_resolver.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/threat_response.py` | 4 | statically referenced; runtime activation still conditional |
| `cognition/topic_quality.py` | 4 | statically referenced; runtime activation still conditional |
| `cognition/unified_revision_gateway.py` | 5 | statically referenced; runtime activation still conditional |
| `cognition/universal_connector/__init__.py` | 7 | statically referenced; runtime activation still conditional |
| `cognition/universal_connector/connector.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/universal_connector/event.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/workspace_bias.py` | 6 | statically referenced; runtime activation still conditional |
| `cognition/workspace_competition.py` | 3 | statically referenced; runtime activation still conditional |
| `cognition/workspace_state_sync.py` | 2 | statically referenced; runtime activation still conditional |
| `cognition/world_model.py` | 1 | statically referenced; runtime activation still conditional |
| `cognition/world_self_dynamics_model.py` | 2 | statically referenced; runtime activation still conditional |
| `components/__init__.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `core/__init__.py` | 2 | statically referenced; runtime activation still conditional |
| `core/agent_controller.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `core/agent_state.py` | 2 | statically referenced; runtime activation still conditional |
| `core/body_bridge.py` | 2 | statically referenced; runtime activation still conditional |
| `core/body_bridge_config.py` | 1 | statically referenced; runtime activation still conditional |
| `core/body_bridge_listener.py` | 2 | statically referenced; runtime activation still conditional |
| `core/body_bridge_server.py` | 2 | statically referenced; runtime activation still conditional |
| `core/bootstrap.py` | 2 | statically referenced; runtime activation still conditional |
| `core/cognitive_event_bus.py` | 6 | statically referenced; runtime activation still conditional |
| `core/cognitive_governor.py` | 2 | statically referenced; runtime activation still conditional |
| `core/connection.py` | 7 | statically referenced; runtime activation still conditional |
| `core/data/__init__.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `core/data/access.py` | 21 | statically referenced; runtime activation still conditional |
| `core/data/migrator.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `core/data/schemas.py` | 11 | statically referenced; runtime activation still conditional |
| `core/execution/__init__.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `core/execution/actuator_interface.py` | 1 | statically referenced; runtime activation still conditional |
| `core/interface_api.py` | 4 | statically referenced; runtime activation still conditional |
| `core/internal_loop.py` | 1 | statically referenced; runtime activation still conditional |
| `core/internal_loop_old.py` | 0 | legacy candidate; confirm before removal |
| `core/llm_scheduler.py` | 26 | statically referenced; runtime activation still conditional |
| `core/orchestrator/__init__.py` | 1 | statically referenced; runtime activation still conditional |
| `core/orchestrator/activity_selector.py` | 1 | statically referenced; runtime activation still conditional |
| `core/orchestrator/autonomous_orchestrator.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `core/orchestrator/cognitive_clock.py` | 1 | statically referenced; runtime activation still conditional |
| `core/orchestrator/drive_system.py` | 2 | statically referenced; runtime activation still conditional |
| `core/orchestrator/event_system.py` | 3 | statically referenced; runtime activation still conditional |
| `core/orchestrator/execution_layer.py` | 1 | statically referenced; runtime activation still conditional |
| `core/perception/__init__.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `core/perception/unified_perception_hub.py` | 1 | statically referenced; runtime activation still conditional |
| `core/phase1_integration.py` | 2 | statically referenced; runtime activation still conditional |
| `core/phase2_integration.py` | 2 | statically referenced; runtime activation still conditional |
| `core/planning/__init__.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `core/planning/multi_step_planner.py` | 1 | statically referenced; runtime activation still conditional |
| `core/sleep_cycle.py` | 1 | statically referenced; runtime activation still conditional |
| `core/state.py` | 34 | statically referenced; runtime activation still conditional |
| `goals/__init__.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `goals/goal_ecology.py` | 1 | statically referenced; runtime activation still conditional |
| `managers/__init__.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `managers/audio_manager.py` | 8 | statically referenced; runtime activation still conditional |
| `managers/codex_app_server_provider.py` | 1 | statically referenced; runtime activation still conditional |
| `managers/conversational_audio.py` | 8 | statically referenced; runtime activation still conditional |
| `managers/fluid_voice.py` | 1 | statically referenced; runtime activation still conditional |
| `managers/llm_manager.py` | 8 | statically referenced; runtime activation still conditional |
| `managers/memory_manager.py` | 8 | statically referenced; runtime activation still conditional |
| `managers/messaging_manager.py` | 1 | statically referenced; runtime activation still conditional |
| `managers/security_manager.py` | 9 | statically referenced; runtime activation still conditional |
| `managers/session_manager.py` | 6 | statically referenced; runtime activation still conditional |
| `managers/settings_manager.py` | 38 | statically referenced; runtime activation still conditional |
| `managers/speech_sanitizer.py` | 2 | statically referenced; runtime activation still conditional |
| `managers/user_manager.py` | 13 | statically referenced; runtime activation still conditional |
| `managers/vision_manager.py` | 10 | statically referenced; runtime activation still conditional |
| `pages/__init__.py` | 1 | statically referenced; runtime activation still conditional |
| `pages/cognitive_dashboard_page.py` | 2 | UI route / page (registered through pages package) |
| `pages/cognitive_dashboard_page_old.py` | 0 | UI route / page (registered through pages package) |
| `pages/llm_page.py` | 0 | UI route / page (registered through pages package) |
| `pages/lumina_page.py` | 0 | UI route / page (registered through pages package) |
| `pages/main_page.py` | 0 | UI route / page (registered through pages package) |
| `pages/orchestrator_page.py` | 0 | UI route / page (registered through pages package) |
| `pages/research_page.py` | 0 | UI route / page (registered through pages package) |
| `pages/rss_management_page.py` | 0 | UI route / page (registered through pages package) |
| `pages/settings_page.py` | 0 | UI route / page (registered through pages package) |
| `pages/shared.py` | 10 | UI route / page (registered through pages package) |
| `pages/vision_page.py` | 0 | UI route / page (registered through pages package) |
| `physiology/__init__.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `physiology/cognitive_energy.py` | 1 | statically referenced; runtime activation still conditional |
| `psychology/__init__.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `psychology/homeostasis.py` | 1 | statically referenced; runtime activation still conditional |
| `utils/__init__.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `utils/add_confidence.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `utils/css.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `utils/enhanced_css.py` | 9 | statically referenced; runtime activation still conditional |
| `utils/helpers.py` | 0 | no static inbound edge; inspect dynamic/CLI use before classifying |
| `utils/organism_ui.py` | 7 | statically referenced; runtime activation still conditional |
| `utils/shared_embedder.py` | 8 | statically referenced; runtime activation still conditional |
| `utils/user_switcher_ui.py` | 7 | statically referenced; runtime activation still conditional |
# Addendum — 2026-11-09: isolamento des conséquences FLUX

## Défaut trouvé et correction

Les modèles `PredictiveConsequenceModel` (PCM) et `WorldSelfDynamicsModel` (WSDM) stockent chacun une seule interaction dans un champ global `_pending`. `LuminaNetwork.send_to_child()` attend la réponse distante avant d’enregistrer l’effet de l’échange. Pendant cette attente, un tour humain pouvait remplacer ou consommer ce même état en attente : l’apprentissage du tour risquait alors d’être attribué au mauvais échange. Le chemin FLUX WSDM inversait aussi le texte entrant et la réponse dans ses arguments de contexte.

Le chemin FLUX capture désormais ses propres états avant/après et écrit une transition explicite, sans utiliser ni vider `_pending`. Il ne résout pas une prédiction de calibration globale qui appartient potentiellement à un tour humain. WSDM utilise un identifiant de contexte propre à l’enfant (`lumina_child_<id>`), avec la réponse distante comme réponse et le prompt sortant comme entrée. Les API historiques `record_action`/`record_outcome` restent disponibles pour les interactions qui possèdent réellement leur prédiction en attente. L’échange n’est plus classé « positif » ou « négatif » à partir de la longueur de la réponse ou d’un point d’interrogation : sans juge dédié, la valence enregistrée reste neutre.

## Vérification

- Régression dédiée : PCM et WSDM préservent un `_pending` humain tout en enregistrant une transition de pair; la calibration humaine n’est pas consommée.
- Test d’intégration FLUX : un échange HTTP réussi enregistre les deux transitions pair-scopées, ne passe pas par `record_action`/`record_context` partagés, et garde un résultat neutre en l’absence d’évaluation explicite.
- Le cycle lent n’est plus propriétaire de la clôture WSDM; le post-traitement par réponse est l’unique chemin de résolution pour l’interaction active.
- Tests PCM/WSDM : la calibration suit le signe du delta d’énergie mesuré, même si l’étiquette d’issue fournie est opposée.
- Suites Brain ciblées, relancées hors sandbox parce que le sandbox Windows bloquait `asyncio.socketpair` : **177 passed, 12 subtests passed** (24 suites).
- Les tests comprennent les tours FLUX, l’isolation de l’historique, la mémoire peer, les états d’erreur réseau, le contexte prédictif, le raisonnement sur objectifs, l’interface Brain et le pont de confirmation Body.
- Les suites de l’application complète ne sont pas déclarées vertes : le relevé précédent compte 28 échecs hors du périmètre Brain (Body/VR/host/perception/caméra).
- Aucun test runtime live n’a été possible pendant ce relevé : les ports locaux 8765 et 8786 ne sont pas à l’écoute. Aucun service Lumina ni Body n’a été démarré.

# Addendum — 2026-11-09: rattachement des étapes cognitives différées

## Défaut trouvé et correction

Les vérifications de continuité et de raisonnement objectif/moyens étaient bien planifiées après la réponse, mais leurs résultats n’étaient pas attachés au tour qui les avait déclenchées. En cas de tours rapprochés, la trace `last_turn` pouvait déjà désigner le tour suivant lorsque les tâches différées terminaient.

Les métadonnées finales de `PersonaBridge` transportent maintenant un `turn_id` et le `cognitive_scope_id` exacts. Les points d’entrée UI, API, Brain-only et CLI les transmettent au planificateur différé. `PersonaBridge` conserve un historique borné de 24 traces et permet à une tâche de compléter la trace d’origine après le démarrage d’un nouveau tour. Le statut global des étapes reste agrégé; l’historique récent expose les statuts, horodatages et identifiants, sans le détail textuel des échanges. Le raisonnement objectif/moyens reçoit également la portée cognitive du tour au lieu de retomber implicitement sur l’utilisateur par défaut.

## Vérification

- Test ciblé : **36 passed, 3 subtests passed** pour `test_brain_workflow_status.py`, `test_lumina_network_peer_turns.py` et `test_streaming_predictive_context.py`.
- Lot intégré : **177 passed, 12 subtests passed** sur 24 suites Brain.
- `py_compile` réussit pour `PersonaBridge`, `AppState`, les trois points d’entrée et les tests modifiés.
- Aucun runtime Lumina n’est joignable localement pendant ce relevé (ports 8765 et 8786 fermés); le résultat live reste à confirmer quand l’utilisateur démarre Lumina.

# Addendum — 2026-11-09: provenance et fraîcheur des preuves du prompt

Le statut des étapes indiquait auparavant que la caméra locale et les observations Body étaient « injectées », sans résumer la fraîcheur des sources fournies au LLM. La trace de tour contient maintenant des résumés non sensibles pour `brain_pc_camera`, `body_runtime`, `global_workspace_body_cache` et le cache caméra Brain-PC du workspace: état actif, âge de frame, nombres frais/périmés, âge du plus ancien enregistrement et types de sources. Aucun contenu de capteur, de scène ou d'identité faciale n'est copié dans ces résumés. Les détails d'erreur bruts des étapes ne sont plus exposés par `/interface/status`. La collecte des métriques est non bloquante et ne peut pas transformer un contexte déjà injecté en échec.

Après correction d'un cas où une panne de métriques marquait à tort le contexte Body comme absent, le lot intégré passe à **177 passed, 12 subtests passed** sur 24 suites Brain; les tests ciblés trace/provenance passent (**33 passed, 3 subtests passed**). `py_compile` passe sur les points d’entrée et fichiers de test modifiés. `git diff --check` ne signale pas d'erreur d'espacement; Git affiche seulement ses avis habituels de conversion LF→CRLF.

## État de livraison

Les modifications et le rapport restent dans le worktree local. Aucun commit, push GitHub ou déploiement Ventuno n’a été effectué.

# Addendum — 2026-11-09: corrections issues du log d'introspection

## Défauts corrigés

- L'extraction sémantique ignore maintenant les formes françaises relevées (`toujours`, `quelles`, `savoir`, `curieux`, `sois`, etc.) et les noms génériques (`chose(s)`, `truc(s)`). Une observation isolée de l'utilisateur ne suffit plus à promouvoir un sujet en but autonome : deux observations de conversation distinctes sont requises.
- GoalEngine rejette les fragments mono-mot et mots vides avant l'appel d'embeddings. La génération échoue fermée si le filtre sémantique échoue; une erreur ne contourne plus le filtre. `arxchiv` et les termes relevés sont rejetés explicitement.
- TTE restaure `iteration_count`, garde les champs connus, et ignore un enregistrement invalide sans perdre les autres threads valides. Le fichier persisté n'est pas réécrit pendant la migration de lecture.
- L'introspection omet l'orientation si la seule valeur disponible est le label de repli `other`/`unknown`.
- Le score de cohérence SelfConcept est désormais une moyenne pondérée des confidences par catégories reconnues. Le bonus de diversité a été retiré car le nombre de catégories ne prouve pas la cohérence. Le rapport distingue maintenant le nombre admissible issu d'identity, le nombre synchronisé, les suppressions dues au plafond et le total conservé.
- L'apprentissage du profil ignore le lead-in temporaire « je suis curieux de savoir… » au lieu de le persister comme caractéristique durable.
- Le journal InnerMonologue annonce le vrai chemin actif : directive de raisonnement inline, une seule génération de réponse.

## Vérification

- 7 régressions dédiées passent : filtres FR, répétition de sujets, admission des buts, migration TTE, label `other`, métrique de cohérence et apprentissage de profil.
- Les tests mémoire et présence existants passent également : 20 tests.
- `pytest` n'est pas installé dans Python global. Les tests ciblés ont été exécutés avec `body_venv\Scripts\python.exe -m unittest`.
- Le log source confirme les erreurs TTE et le plafond SCS rapportés. `EpistemicIntegrity` affiche zéro validation à son initialisation, mais le log ne prouve pas qu'il n'en a fait aucune ensuite : l'initialisation seule n'est pas un constat de panne. `self_description` est utilisé dans le pont de propositions de réflexion; son absence du prompt de chat n'est pas corrigée ici, car son manifeste ne décrit actuellement que quatre modules et ne constitue pas un inventaire complet vérifié du cerveau.
- Les états `valence=0.64` et `0.91` proviennent de chemins de calcul distincts; le log seul n'établit pas qu'ils mesurent exactement le même signal. La configuration `web_search=always` est un réglage explicite dans les deux premiers tours, puis passe à `off` après sauvegarde; ce n'est pas attribué à un gate cassé.
- Aucun runtime Lumina live n'a été modifié ni relancé. La validation live, le commit, le push GitHub et le déploiement restent à faire.

## Relance locale des correctifs

- La limite SCS est maintenant appliquée avant la fusion : seuls les 40 candidats les mieux classés, avec départage stable par nom, sont admis. Les catégories `semantic_concept` brutes ne deviennent pas des croyances de self-concept. Le compteur `beliefs_synced` ne compte que les modifications qui survivent effectivement au plafond. Une régression vérifie que le deuxième cycle identique ne réintroduit ni ne supprime les mêmes 20 candidats.
- Le test de régression dédié passe maintenant à **8/8**; les suites mémoire et présence passent **20/20**. `py_compile` passe sur les fichiers Brain corrigés.
- Une tentative de relancer ensemble les 24 suites intégrées n'a pas produit de résultat exploitable : le chargement des modules bloque dans le premier test d'interface dans cet environnement Windows. La première tentative avec `body_venv` était invalide pour ces modules, car cette installation n'a pas `pydantic`. Je ne compte donc pas cette relance comme un passage ni comme des échecs de assertions.
- `git diff --check` ne relève pas d'erreur d'espacement. Lumina n'est pas démarrée et aucun test live, commit, push ou déploiement n'a été effectué.

# Addendum — 2026-11-09: introspection ancrée sur le registre d’architecture

## Lecture du nouveau log

- Le modèle chargé est bien `lmstudio/gemma-4-e4b-uncensored-hauhaucs-aggressive`, selon le bloc `LOADED CONFIGURATION`. Les réponses d’introspection du log ne démontrent pas un accès au mécanisme interne; elles mélangent des valeurs de télémétrie exactes avec des métaphores et des causalités non vérifiées. Le modèle « abliterated » peut être un facteur de style, mais le log seul ne permet pas d’en établir la causalité.
- `web search mode='always'` explique les recherches déclenchées pendant ces tours. Après `Saved settings to config.json`, le mode `off` est constaté. Le résultat `good evening` est cohérent avec le réglage `always`; le gate de classification ne saurait empêcher la recherche quand ce mode la force.
- Le message TTE `iteration_count` figure dans cet ancien relevé; la source courante accepte ce champ et filtre les champs persistés inconnus avant de construire les dataclasses. Le test de migration confirme le chargement d’un enregistrement valide et l’isolement d’un enregistrement mal formé.
- `Two-pass architecture enabled` est une trace provenant du module archivé `inner_monologue_engine_old.py`; le chemin actif est à appel unique. Le démarrage courant annonce maintenant explicitement `single-call directive enabled` ou `disabled`.
- Le chemin Body dans le `config.json` journalisé est une configuration locale distincte du cœur cognitif; aucun changement de cette configuration n’est inclus ici.

## Correction apportée

`cognition.self_description` était bien initialisé et consulté par la boucle interne, mais son registre n’était pas injecté dans le prompt conversationnel. Il fournit maintenant un bloc de prompt borné, factuel et explicitement partiel. Le modèle reçoit l’instruction de ne pas transformer l’absence d’une entrée en preuve d’un mécanisme, ni d’inventer des équations, sensations ou causalités. `PersonaBridge` injecte ce bloc à chaque tour et inscrit l’étape `self_description_context` dans le statut du tour; si le registre est indisponible, le prompt le dit explicitement.

Les problèmes GoalEngine/SemanticExtractor, le bruit `other` en introspection, le churn SelfConcept et la migration TTE avaient déjà été traités dans les correctifs précédents; les tests de régression correspondants restent verts.

## Vérification de cette correction

- `tests/test_cognitive_log_regressions.py`: **11 tests réussis**.
- `py_compile` sur `self_description.py`, `persona_bridge.py` et le test: réussi.
- `git diff --check`: réussi; avertissements de conversion de fins de ligne CRLF uniquement.
- `pytest` n’est pas installé dans l’environnement Python global; l’exécution a été faite avec `unittest` dans le venv du projet.
- Aucun service Brain local n’écoute sur 8765 et aucun pair Body bridge n’écoute sur 8786 au relevé; l’injection ne peut donc pas encore être validée dans une réponse live.

# Addendum — 2026-11-09: reprise des preuves du workflow FLUX

## Chemin vérifié

Le chemin FLUX traverse `LuminaNetwork._generate_peer_turn` → `PersonaBridge.get_response_stream` → génération + post-traitement de persona. `AgentController` n’est pas appelé ici, intentionnellement : son contrat porte sur un échange humain (profil humain, affect, vision et mémoire utilisateur). Le détourner pour FLUX réintroduirait précisément les fuites de contexte que la frontière peer doit empêcher.

Le récepteur Brain passe par `PeerConversationStore.generate_reply`: le transcript est indexé par `(sender_id, conversation_id)`, transmis comme historique de provider sans l’écrire dans l’historique partagé, et n’est commis qu’après une réponse cognitive non vide. Les actions Body sont désactivées. Les ouvertures, pivots et messages entrants de FLUX utilisent un `cognitive_scope_id` par pair/conversation. Les transitions PCM/WSDM peer-scopées ne consomment pas la prédiction humaine en attente.

## Résultats des suites FLUX/Brain

Après la correction du registre d’architecture injecté au prompt, les suites ciblées ont été relancées :

- `test_lumina_network_peer_turns.py`: **25 réussis**.
- `test_peer_conversation_store.py`: **4 réussis**.
- `test_peer_predictive_outcomes.py`: **4 réussis**.
- `test_streaming_predictive_context.py`: **3 réussis**.
- `test_brain_workflow_status.py`: **8 réussis**.
- `test_cognitive_log_regressions.py`: **11 réussis**.

Le sandbox Windows bloquait `asyncio` lors de la création du `socketpair`; la suite FLUX a été exécutée avec l’escalade autorisée et a terminé avec succès. Quelques erreurs d’encodage CP1252 ont été émises par les logs emoji de tests, sans échec de test.

## Limite restante

Ces tests prouvent le routage, la séparation de portée, l’historique, le post-traitement et les transitions prédictives en environnement contrôlé. Ils ne prouvent pas encore une conversation réseau réelle entre deux instances en cours d’exécution. Au dernier relevé, aucun listener local ne répondait sur 8765 (API Brain) ni 8786 (Body bridge); je n’ai pas démarré Lumina. La validation runtime de la réponse FLUX, des traces de stades et de la persistance lors d’un vrai échange reste ouverte.

# Addendum — 2026-11-09: endpoints FLUX disponibles dans le lancement complet

## Blocage trouvé et corrigé

Le lancement `start.bat` exécute `app.py`, alors que `/lumina-network/chat`, `/receive`, `/children` et `/epistemic` n’étaient déclarés que dans `brain.py`. La configuration complète initialisait pourtant `LuminaNetwork` : une instance lancée via l’interface complète ne pouvait donc pas recevoir les messages pairs au protocole réseau attendu.

Les quatre routes sont maintenant centralisées dans `core/lumina_peer_api.py` et montées à la fois dans l’application NiceGUI (`app.py`) et dans le runner headless (`brain.py`). Le traitement chat conserve le `PeerConversationStore`, le scope pair et l’échec fermé déjà en place; les snapshots de workspace et mises à jour épistémiques conservent leur traitement dédié.

## Vérification

- `test_lumina_network_peer_turns.py`: **25 réussis** après le déplacement des routes.
- `test_peer_conversation_store.py`: **5 réussis**, dont la présence des quatre routes sur l’application montée et le montage depuis les deux points d’entrée.
- Compilation Python (`py_compile`) des deux launchers, du routeur partagé et du test : réussie.
- `git diff --check` : réussi, avec seulement les avertissements de fins de ligne déjà présents.
- Aucun service ne répond sur 8765/8786; la communication réelle entre instances n’a pas pu être observée. La configuration actuelle conserve les binds loopback; l’accès depuis une autre machine exige un bind et une URL de rappel réseau configurés explicitement. Je n’ai pas exposé ces endpoints au réseau.

# Addendum — 2026-11-09: revue des nouvelles constatations du log

## Constatations corroborées

- Le modèle indiqué par le log est `gemma-4-e4b-uncensored-hauhaucs-aggressive`, pas Qwen2.5-7b. Le réglage de recherche web est bien passé de `always` à `off` après l'enregistrement de `config.json`; les recherches sociales du premier état relèvent du mode forcé `always`, pas d’un défaut du gate.
- `toujours`, `quelles`, `arxchiv`, les amorces conversationnelles et le label de repli `other` avaient des chemins capables de les promouvoir en topics ou croyances. Les correctifs déjà présents filtrent le lexique FR/EN à l’extraction, imposent une validation sémantique à l’admission des buts, exigent des observations utilisateur répétées pour un topic durable, et n’exposent pas `other` comme orientation réelle.
- Le chargement TTE filtre les champs inconnus, restaure `iteration_count` et isole les lignes invalides sans effacer les threads valides. Le synchroniseur de concept ne traite plus le nombre de catégories comme preuve de cohérence et ne rapporte pas le churn supprimé par le plafond comme une synchronisation durable.
- La valeur `total_validations=0` au log d’initialisation est seulement un compteur au démarrage; elle ne prouve pas qu’aucune validation ne se produit ensuite. Les valeurs valence 0.64 et 0.91 viennent de deux signaux/modules distincts; sans contexte temporel et définition identiques, elles ne sont pas directement contradictoires.
- L’architecture de dialogue courante est explicitement en mode une génération avec directive de réflexion intégrée; l’ancien « two-pass enabled » provient d’un ancien chemin/module, pas d’une preuve que le chemin courant fasse deux appels.
- Le manifeste `self_description` décrit volontairement un registre partiel, pas l’ensemble vérifié du cerveau. Le prompt l’indique maintenant et interdit au LLM d’inventer les mécanismes absents.

## Correction supplémentaire

Le filtre de profil empêchait déjà d’enregistrer « je suis curieux de savoir… », mais laissait passer certaines variantes (« curieux de comprendre… », « curious about whether… »). Il exclut maintenant ces amorces épistémiques de la catégorie « caractéristique durable », avec quatre formulations couvertes par un test.

Le log signalait également une URL Body `https://127.0.0.1` sans port alors que `BODY_PORT=8766`. Le client utilisait silencieusement le port HTTPS par défaut (443). Le runtime complète désormais une URL hôte seule avec `BODY_PORT`; un port explicitement présent reste prioritaire. Je n’ai pas modifié `config.json`, le protocole TLS ni l’adresse configurée. Le test vérifie `https://127.0.0.1:8766` et la conservation d’un port explicite.

## Vérifications après cette revue

- `test_cognitive_log_regressions.py`: **11 réussis**.
- `test_peer_conversation_store.py`: **6 réussis**, dont exécution réelle du handler avec un faux routeur, sans dépendre de FastAPI installé dans l’interpréteur global.
- `test_body_runtime_url_config.py`: **2 réussis**.
- `test_peer_predictive_outcomes.py`: **4 réussis**.
- `test_streaming_predictive_context.py`: **3 réussis**.
- `test_brain_workflow_status.py`: **8 réussis**.
- `test_lumina_network_peer_turns.py`: **25 réussis** hors sandbox. Dans le sandbox Windows, son test asyncio/socket reste bloqué; hors sandbox il termine, avec des erreurs de rendu emoji CP1252 dans les logs mais sans échec.
- `py_compile` des launchers, routeur et fichiers ajustés: réussi. `git diff --check`: réussi (avertissements CRLF seulement).

Ces résultats sont des tests hors ligne. Aucun lancement de Lumina ni conversation réseau réelle avec FLUX n’a été effectué dans cette revue.

## Addendum — 2026-11-09: API Brain aussi en mode application complète

`app.py` sert toujours l’interface NiceGUI sur `NICEGUI_PORT` (8080 par défaut), mais démarre maintenant aussi la même API FastAPI que `brain.py` sur `BRAIN_API_HOST:BRAIN_API_PORT` (127.0.0.1:8765 par défaut). Le montage des routes FLUX/peer est partagé par les deux entrées. Le serveur API est démarré avant le préchauffage cognitif et arrêté pendant le shutdown. Le pont Body reste distinct sur 8786; son validateur refuse désormais la collision avec le port de l’API Brain.

Vérification hors ligne : **51 tests réussis et 12 sous-tests réussis** sur les neuf suites ciblées (cycle de vie API, routes peer, configuration réseau, pont Body, régressions cognitives, statut du workflow Brain, résultats prédictifs peer, contexte de streaming et URL Body). `py_compile` et `git diff --check` réussissent; Git affiche uniquement ses avertissements habituels de conversion LF/CRLF.

Vérification runtime : aucun processus n’écoute actuellement sur 8080, 8765 ou 8786. Il faut redémarrer Lumina avec `start.bat` pour constater l’écoute réelle; aucun service n’a été lancé ni déployé pendant cette vérification. Le bind de l’API reste loopback par défaut, conformément à `config.json`; cela permet aux clients du même PC d’utiliser 8765 sans exposer l’API au LAN.

## Addendum — audit live et continuité peer

Après le redémarrage demandé par l’utilisateur, `GET http://127.0.0.1:8765/status` renvoie HTTP 200 avec `ready=true`, persona disponible, orchestrateur actif et provider configuré. `GET /lumina-network/children` répond sur 8765 et le routeur NiceGUI expose aussi les routes peer sur 8080. Le peer configuré est `Flux` sur `http://192.168.0.28:8765`; son ping retourne `online=false`, `turn_count=0`. Aucun message de génération n’a donc été envoyé et aucun échange réel Lumina↔FLUX n’est confirmé.

Un défaut de continuité a été trouvé dans le bouton manuel **Ask** : il appelait `send_to_child` sans `conversation_id`, et la méthode générait un nouvel UUID à chaque message. Chaque question de suivi repartait donc sans historique côté FLUX. Les messages manuels réutilisent maintenant un fil stable par peer durant le processus; un dialogue explicite démarre un fil neuf ou respecte l’identifiant fourni. Les files d’injection utilisateur sont maintenant indexées par peer + conversation; une injection ambiguë est refusée au lieu d’être dirigée vers un autre dialogue, et l’UI traite alors le message comme un tour humain normal.

`core/agent_controller.py` est un pipeline legacy sans appelant actif. L’UI et le dialogue peer utilisent `PersonaBridge`; pour FLUX, cette voie passe par `get_response_stream` et `_stream_with_full_lifecycle`, avec `peer_name`, `cognitive_scope_id`, transcript dédié, actions Body interdites et apprentissage humain exclu. L’ancienne classe `AgentController` n’a pas ces frontières; son en-tête précise désormais qu’il ne faut pas l’insérer dans le chemin peer.

Les quatre nouveaux tests isolés de routage des conversations passent. Les neuf suites de régression déjà exécutées totalisaient **51 réussites et 12 sous-tests** avant ce dernier ajout. La suite historique `test_lumina_network_peer_turns.py` a provoqué une exception native Windows pendant l’import SWIG de FAISS dans ce contexte; une exécution antérieure hors sandbox avait réussi 25 cas, mais elle doit être relancée dans un environnement stable pour valider le dernier changement. Le processus Lumina actuellement observé a été redémarré avant la correction de continuité; il faudra un autre redémarrage pour charger ces derniers changements. Les échanges sont encore conservés en mémoire de processus et ne survivent pas à un redémarrage.

## Addendum — après le redémarrage Lumina signalé par l’utilisateur

Le service vivant répond maintenant sur `127.0.0.1:8765/status` (HTTP 200, `ready=true`, persona et orchestrateur actifs) et expose `/lumina-network/children`. La même route est également joignable sur l’interface complète `127.0.0.1:8080`. Le peer `Flux` reste déclaré à `http://192.168.0.28:8765`, mais `online=false`; aucun prompt de conversation n’a été envoyé.

Après ce démarrage, les tests locaux des changements récents passent : **4 tests** de continuité/routage et **51 tests + 12 sous-tests** des neuf suites de régression; `py_compile` passe. `git diff --check` ne signale que des avertissements de conversion LF/CRLF.

Ordre des événements : le redémarrage de Lumina a précédé le dernier correctif du fil Ask peer. Les endpoints actifs prouvent que le service complet et l’API Brain sont démarrés, mais cette version du processus ne contient pas encore le correctif stable des identifiants de conversation. Un redémarrage supplémentaire sera nécessaire pour le charger. La validation de bout en bout avec FLUX reste ouverte tant que le peer est hors ligne.

Un nouveau ping applicatif après ce redémarrage renvoie toujours `online=false`; la lecture directe de `http://192.168.0.28:8765/status` reçoit un refus TCP. Cela confirme que le blocage d’échange est actuellement côté disponibilité/adresse de FLUX, et non une erreur de génération que l’on pourrait diagnostiquer sans joindre ce service.

## Addendum — réconciliation des adresses Body et peer

À la question sur `standalone Body host is not reachable at https://127.0.0.1:8766`, l’inspection de `config.json` montre `BODY_HOST=192.168.0.14` et `BODY_PORT=8766`, mais aussi `BODY_URL=https://127.0.0.1`. Le code donne priorité à `BODY_URL`; il ignore donc le bon `BODY_HOST` et tente le loopback du PC. L’accès est réessayé avec un délai de 15 secondes, ce qui correspond aux lignes INFO périodiques observées. Si Ventuno est éteint, l’échec est attendu; s’il est en marche, cette URL locale reste une mauvaise cible et doit être remplacée par l’URL HTTPS du Ventuno avec une identité TLS/certificat valide. La configuration n’a pas été modifiée pendant ce diagnostic.

La même vérification confirme que l’entrée `LUMINA_CHILDREN` dans `config.json` porte le commentaire explicite « Remove this example entry and fill in real child details », et configure néanmoins `Flux` vers `http://192.168.0.28:8765`. `ipconfig` identifie `192.168.0.28` comme l’adresse du PC courant; le serveur Brain est configuré pour écouter seulement sur `127.0.0.1`. Ainsi cette entrée exemple n’est pas la preuve d’un Flux disponible : elle vise l’interface LAN du Brain local, où la connexion est refusée. Le chargeur ignore maintenant les entrées marquées `_comment`, les objets mal formés et les entrées sans URL; le compteur UI utilise le nombre réellement chargé.

La réponse de `/lumina-network/chat` inclut maintenant une trace compacte du tour peer (`turn_id`, scope, statuts des stages et sources de contexte), sans texte de prompt ni détails d’exception. Le Brain master valide et conserve cette trace sous `last_cognitive_trace` dans `/lumina-network/children`; une portée `human` ou invalide est rejetée. Les échanges peer ne sont plus inscrits comme positifs par défaut dans la mémoire relationnelle : le valence est neutre en l’absence d’un évaluateur.

Un test confirme que le placeholder est ignoré et qu’un peer réel est conservé; les tests couvrent aussi le transport et la rédaction des traces, leur conservation côté master, et l’absence de fuite de détails. Vérifications finales : **6 tests de routage**, **8 tests de l’API/store peer**, **45 tests + 12 sous-tests** de régression; `py_compile` et `git diff --check` réussissent (avertissements LF/CRLF uniquement). Aucun endpoint Flux distinct n’a été identifié; il faut une vraie adresse/port du peer avant de prétendre valider un dialogue réseau.

## Addendum — aller-retour peer complet et contrôle d’accès

Un défaut de sécurité réseau a été confirmé : les requêtes sortantes incluaient parfois une clé, mais les routes entrantes ne la vérifiaient pas. Les routes `/lumina-network/chat`, `/receive`, `/children` et `/epistemic` exigent maintenant `LUMINA_NETWORK_API_KEY` pour les requêtes non-loopback. En loopback, le mode local reste utilisable sans clé; dès qu’un secret est configuré, toute requête doit le présenter (JSON `api_key`, `x-lumina-api-key` ou Bearer). La clé est enregistrée comme secret (`.venv/.env` ou variable d’environnement), pas comme valeur versionnée de `config.json`.

Le test d’intégration hors ligne enchaîne le transport `LuminaNetwork.send_to_child` avec le vrai handler `/lumina-network/chat` et `PeerConversationStore`, puis vérifie le transcript des deux côtés, le scope peer, le refus des actions Body, la trace retournée et conservée par le parent, et l’absence de modification de la mémoire humaine. La suite historique `test_lumina_network_peer_turns.py` a maintenant été relancée hors sandbox après son erreur native Windows : **25 réussis**. Vérifications finales : **7 tests de routage**, **10 tests API/store peer**, **25 tests de tours complets**, **45 tests + 12 sous-tests** de régression; `py_compile` et `git diff --check` réussissent. Ce test d’intégration utilise un transport en mémoire : l’inférence réelle de FLUX et la connexion réseau inter-machine demeurent non vérifiées, car aucune cible FLUX distincte n’est configurée.

## Correction live — Lumina principal et FLUX secondaire sur le même PC

La conclusion précédente sur un conflit du port 8765 était erronée. L’audit direct a interrogé les deux adresses séparément : `http://127.0.0.1:8765/status` répond avec le modèle Gemma de Lumina, tandis que `http://192.168.0.28:8765/status` répond avec Qwen de FLUX. Les deux processus sont donc joignables sur des adresses d’écoute distinctes malgré le même numéro de port. Lumina est le principal; FLUX est le Brain secondaire. Le canal prévu est l’initiative Lumina→FLUX, sans lancement autonome de dialogue par FLUX.

Le `/lumina-network/children` live de Lumina indique FLUX `online=true` et `turn_count=16`, ce qui prouve des réponses peer réussies avant le dernier redémarrage. L’entrée réelle dans `config.json` conservait toutefois un `_comment` d’exemple; le chargeur actuel l’ignore volontairement. Le marqueur a été retiré localement, tout en gardant `http://192.168.0.28:8765`, afin qu’un redémarrage charge l’instance réelle plutôt que de la filtrer. La configuration `config_Flux.json` reste sur son port 8765; aucun nouveau port ni lanceur distinct n’est requis pour l’architecture observée.

Le code et les tests de scope peer, d’historique isolé et de trace cognitive sont dans le worktree local. L’instance principale live a été démarrée avant les dernières modifications de code; elle doit être relancée par l’utilisateur pour charger les derniers fichiers. Le peer FLUX live est joignable, mais une nouvelle requête `network/action` n’a pas encore été confirmée depuis le processus principal rechargé.

### Preuve live complémentaire

L’API effective de l’interface complète est préfixée `/api/interface`. `GET http://127.0.0.1:8080/api/interface/network` a confirmé `enabled=true`, FLUX `online=true`, et un compteur de tours croissant. Un appel de test non-actuant à `POST /api/interface/network/action` a traversé `LuminaNetwork.send_to_child` et l’API FLUX réelle; réponse observée : « Flux here. Received your message, Lumina-Master. How can I assist you today? ». Le compteur parent est passé à 30 après l’échange. Cela valide le transport réel Lumina→FLUX et la génération de FLUX.

Le processus live ne renvoie pas encore `last_cognitive_trace` dans `/lumina-network/children`, tandis que le code local récent le transmet et le filtre par scope. Les fichiers ont été modifiés après le démarrage du processus; la preuve live confirme le flux de base, pas encore les nouvelles traces/history du code non rechargé. Aucun changement de port n’est nécessaire : les deux API sont distinctes par leur adresse d’écoute, et le même port 8765 est vérifié sur chacune.

## Rôles de déploiement et contrôle de direction

Le code commun accepte maintenant `LUMINA_NETWORK_ROLE=master|child|standalone`. Le master seul instancie `LuminaNetwork` et peut déclencher `send`/`dialogue`; le child sert `/lumina-network/chat`, vérifie `sender_id` contre `LUMINA_MASTER_ID`, et ne crée aucun réseau sortant. L’API de push enfant→master est refusée par défaut, et le master n’envoie plus d’URL callback dans ses requêtes. Les profils de référence sont dans `docs/lumina_network_roles.md`; `config.json` reste local et ignoré par Git pour ne pas publier les secrets.

Les tests ciblés après ce changement passent : **60 tests**, **9 avertissements de dépendances/dépréciation** et **5 sous-tests**. `py_compile`, `git diff --check` et la lecture des trois configurations JSON locales passent. Le bac à sable Windows ne permet pas au testeur de créer son `socketpair`; l’exécution autorisée hors bac à sable a terminé correctement.

Dernier relevé runtime : Lumina `127.0.0.1:8765/status` et FLUX `192.168.0.28:8765/status` répondent tous deux HTTP 200, avec Gemma côté Lumina et Qwen côté FLUX. Le compteur parent est à 63 échanges réussis. Le processus live ne publie pas encore le champ `role` ni la trace récente, ce qui confirme qu’il n’a pas rechargé les dernières modifications locales. Le prochain test runtime des garde-fous de rôle et de la trace nécessite le redémarrage de Lumina et FLUX avec leurs configurations respectives.

## Addendum — journal de ticks et analyse bornée des sorties

L’état `initialized` ne prouvait pas qu’un module cognitif avait réellement tourné. `InternalThoughtLoop` instrumente maintenant les points d’entrée connus des modules de ses cycles : chaque appel incrémente un compteur et conserve l’heure, la durée, la dernière méthode, le dernier statut, le type d’erreur et un résumé structurel borné de la sortie. Les modules conditionnels restent `initialized_unobserved` tant que leur seuil ne les a pas déclenchés; ils ne sont pas artificiellement appelés pour l’audit. Les exceptions restent visibles sans conserver leur texte.

L’analyse de sortie signale les résultats vides, la forme (type, clés ou types d’éléments), et les champs numériques non finis. Elle ne conserve jamais le texte retourné. Un nombre NaN/Inf dégrade l’état du module. L’API `brain_workflow_status` publie `module_ticks` et un agrégat (`module_tick_analysis`: couverture, exécutions, ticks, erreurs et qualité des dernières sorties). Cette vérification est structurelle : elle ne prétend pas prouver la vérité sémantique d’une sortie.

La fin de chaque tour vérifie aussi la présence des sept étapes essentielles, le format des statuts, l’ordre temporel prompt → génération → contrôle de sortie → finalisation → réponse, et les frontières de scope d’un tour FLUX. Les étapes conditionnelles sont rapportées séparément; une étape manquante, mal formée, dans le mauvais ordre ou hors scope donne `incomplete_evidence`.

Vérifications locales ciblées : `test_module_tick_log.py` (**4 réussis**), `test_brain_workflow_status.py` (**8 réussis**), et les tests d’intégrité de trace dans `test_lumina_network_peer_turns.py` (**3 réussis**); `py_compile` et `git diff --check` réussissent. La suite complète des tours peer n’a pas fini dans le temps du sandbox et a été interrompue; aucune conclusion positive n’en est tirée. Le processus Lumina actuellement lancé ne peut pas exposer ces nouveaux champs avant son redémarrage. Le contrôle live du port local 8080 était refusé par le sandbox, donc les nouveaux compteurs n’ont pas encore de preuve runtime après chargement.

## Addendum — premier relevé live des ticks et sorties après redémarrage

Après le redémarrage, l’API a chargé `module_tick_analysis`. Le premier cycle profond observé a compté **30 modules exécutés, 48 ticks, 0 exception** (relevé ultérieur : 30 modules, 80 ticks, 0 exception). Les résumés de sorties indiquent six retours avec une forme utile (listes TTE/CDE, résultat DTS/MTE, sortie narrative et rapport Phase 1) et 24 appels qui renvoient `None`. Ces 24 cas sont des méthodes à effets de bord : leur exécution est prouvée, mais leur résultat métier n’est pas directement retourné; ils ne doivent pas être interprétés comme 24 erreurs ni comme des sorties valides sémantiquement. À ce stade, le journal établit forme et absence d’exception, pas qualité cognitive.

Au dernier relevé, 13 modules étaient initialisés mais sans tick observé. L’inspection des callsites révèle quatre faux « non observés » dus à des noms d’instrumentation incorrects : `GoalActionExecutor.run_tick`, `PersistentExecutiveLoop.review`, `ArbitrationLearning.review` et `CognitiveGovernor.begin_cycle`. Le mapping est corrigé localement. Les autres absences correspondent à des branches périodiques/seuils non échus après seulement deux cycles post-redémarrage : périodes de 5, 7, 8, 10, 15, 18, 20 ou 50 cycles, consolidation, ou présence d’un gagnant du workspace. Ils sont initialisés, non prouvés comme en panne.

Un tour humain de contrôle a terminé avec 59 étapes. Les sept étapes essentielles étaient présentes et ordonnées; caméra et Body ont été incluses dans le scope humain. Une étape différée `continuity_analysis_post_response` a toutefois échoué après finalisation. L’ancien bilan `pipeline_integrity` est resté « consistent » car il n’était pas recalculé à la réception des étapes différées. Ce défaut est maintenant corrigé : les échecs tardifs rendent la trace `completed_with_stage_failures` et l’intégrité `incomplete_evidence`. Le correctif ainsi que les mappings de méthodes passent les tests ciblés; un redémarrage supplémentaire est nécessaire pour les voir en live. Le lecteur SSE de ce test a d’abord rencontré une erreur locale bytes/str; l’API confirme néanmoins le tour terminé. La cause de l’échec différé n’est pas établie par les détails de trace, volontairement non conservés.

Après ces corrections : `test_module_tick_log.py` (**5 tests**), `test_brain_workflow_status.py` (**8 tests**), tests d’intégrité/pipeline et différés (**5 tests**) passent; `py_compile` et `git diff --check` passent. La suite entière des tours peer reste non validée dans le sandbox, comme indiqué dans l’addendum précédent.

La prochaine trace différée expose aussi uniquement le type d’exception (par exemple `ValueError`), jamais son message, afin de diagnostiquer `continuity_analysis_post_response` sans fuite de texte de conversation. Ce point, les probes corrigées et la mise à jour tardive de l’intégrité sont inclus dans le correctif local testé; ils demandent tous le redémarrage suivant pour une validation live.

## Addendum — défaut Phase 2 confirmé par le nouveau tick log

Le redémarrage avec la télémétrie corrigée a révélé une erreur réelle dans `phase2_orchestrator.synthesize_narrative` : `AttributeError`. La lecture du chemin montre que `InternalThoughtLoop` passait directement l’objet `EmotionalStateManager`; `NarrativeSynthesizer._get_dominant_emotion` attend un mapping et appelle `.items()`. Le pont Phase 2 normalise désormais les deux formes acceptées (manager ou dictionnaire) en `{nom: valeur_float}`, filtre les valeurs non numériques/non finies et transmet ce contrat au synthétiseur. Aucun autre module n’est modifié.

Le test d’intégration local exécute le vrai `NarrativeSynthesizer` avec la forme d’émotions du manager, et vérifie que la sortie narrative est produite. Les trois tests Phase 2, cinq tests du tick log et huit tests de statut workflow passent; `py_compile` et `git diff --check` passent également. Le processus live actuel a encore l’ancienne version de Phase 2; un redémarrage après commit sera nécessaire pour confirmer que son compteur Phase 2 reste sans erreur et qu’une narration est produite.

## Addendum — audit live après le redémarrage du 10 novembre

Le nouveau processus répond sur l’API locale, avec PersonaBridge prêt, boucle cognitive et orchestrateur actifs. Après son premier cycle lent, le registre affichait **7 modules exécutés, 34 initialisés sans tick observé, 2 absents et 0 erreur**. À 417 s d’uptime, le relevé avait évolué à **40 modules exécutés sur 43, 3 initialisés sans tick observé, 0 absent, 0 erreur et 168 ticks**. Les qualités de dernière sortie étaient **12 `present`, 1 `present_redacted`, 27 `empty`**. `empty` établit seulement qu’un appel instrumenté n’a rien retourné; les méthodes à effets de bord doivent être auditées selon leur contrat, sans les déclarer sémantiquement valides par défaut.

Un tour de falsification sur l’auto-description a montré `self_description_context=injected`, `memory_retrieval=completed`, et une réponse présentant une liste de modules, de nombreux chiffres et une inférence sur l’utilisateur. Les quatre noms d’architecture cités correspondent aux quatre composants actuellement enregistrés dans `SelfDescription`; ils ne prouvent pas que le registre couvre toute l’architecture. Les chiffres issus de l’état et de la mémoire ont été mêlés sans provenance claire, et une inférence personnelle non nécessaire a été ajoutée. Le tour avait néanmoins `completed_with_stage_failures`, `pipeline_integrity=incomplete_evidence`, car `continuity_analysis_post_response` a échoué. La trace live n’exposait pas le type d’exception : `run_deferred_analysis` absorbait l’exception et renvoyait seulement `"failed"`.

Corrections locales en cours : le registre expose maintenant le tick snapshot process-local (état, nombre d’appels, erreurs, qualité et méthodes observées) lors des questions sur l’architecture; le prompt précise que `healthy` n’est pas une validation sémantique, qu’un retour vide n’est pas une preuve de résultat, et que la mémoire historique n’atteste pas l’état logiciel courant. Les échecs différés renvoient uniquement le nom de classe de l’exception, jamais son message, puis l’ajoutent à la trace. Aucun texte d’inférence privée n’est conservé dans ces métriques.

Tests locaux ciblés après ces changements : registre d’architecture **3/3**, propagation sûre du type d’erreur **1/1**, journal de ticks **6/6**, Phase 2 **3/3**, statut du workflow Brain **9/9**; compilation Python et `git diff --check` réussissent. La suite complète `test_lumina_network_peer_turns.py` est restée bloquée pendant l’exécution et a été interrompue; seul son test ciblé de type d’erreur est validé. Le processus live en service a été redémarré avant les dernières corrections; leur preuve runtime exige un prochain redémarrage. Pas de déploiement Ventuno.

## Addendum — conservation de la provenance des erreurs de tick

Le relevé live suivant a confirmé **2 erreurs historiques** dans `phase1_orchestrator`, de type `UnboundLocalError`, alors que ses ticks les plus récents réussissaient. L’ancienne télémétrie effaçait `last_error_type` après une réussite et ne gardait ni méthode ni emplacement; l’origine de ces deux exceptions ne peut donc pas être reconstruite à partir du processus courant. Les compteurs globaux de cycle restaient à zéro, car les erreurs étaient capturées à l’intérieur du sous-cycle Phase 1.

Le journal conserve maintenant le dernier échec même après une reprise réussie, avec type, méthode, horodatage et fichier/ligne/fonction du dernier cadre de pile. Il n’enregistre toujours ni message d’exception ni sortie textuelle. L’agrégat précise aussi le nombre de modules ayant connu au moins une erreur. Ainsi, `last_status=completed` indique que le dernier appel a réussi tandis que `last_error` garde une erreur antérieure; le nombre d’erreurs historiques reste distinct de l’état du dernier appel.

Le snapshot comptait aussi beaucoup de sorties `None`, alors que nombre de points d’entrée `tick` déclarent explicitement `-> None` et produisent leurs effets par mutation/écriture d’état. Le résumé les distingue maintenant sous `side_effect_only`, à partir de l’annotation de retour de la méthode observée. Les `None` sans contrat explicite restent `empty`; aucune exécution artificielle ni hypothèse de réussite métier n’est ajoutée. `semantic_graph_cleaner` est un cas initialisé mais non observé : son callsite exige à la fois 50 slow cycles et le mode `exploratory` du CognitiveGovernor, donc son absence d’exécution est cohérente si le mode actif reste structuré.

Vérification locale ciblée : **21 tests** (`test_module_tick_log.py`, `test_brain_workflow_status.py`, `test_self_description_prompt.py`) passent; compilation de `core/module_tick_log.py` et `core/internal_loop.py`, ainsi que `git diff --check`, passent. Le processus vivant a comptabilisé deux erreurs Phase 1, mais l’explication précise reste indéterminée. Les nouveaux champs d’erreur et la distinction `side_effect_only` seront visibles après redémarrage de Lumina; ils ne peuvent pas recréer rétroactivement les piles perdues.

## Addendum — filtre lexical partagé avec GoalQualityFilter

Le nouveau relevé joint signale des sujets parasites qui réapparaissent après leur rejet initial. Le code confirme un second chemin : `GoalQualityFilter` rescored les buts persistés avec un score souple et pouvait préserver un sujet bruité pour maintenir quatre buts actifs. Il n’utilisait pas la règle dure du `GoalEngine`.

`GoalQualityFilter._score_goal` réutilise maintenant `GoalEngine._is_lexical_noise_topic`; un sujet rejeté reçoit un score nul et une raison explicite. Le filtre le marque `low_quality` même si cela fait descendre le pool sous quatre buts actifs. Les objectifs simplement faibles conservent l’ancien plancher de quatre. Un test vérifie qu’un fragment `soory` reste rejeté malgré priorité, origine et pensées d’appui élevées, tandis qu’une phrase réelle passe le garde-fou.

Vérifications ciblées : **30 tests**, dont les régressions de bruit lexical, les ticks, et le statut de workflow, passent; compilation Python et `git diff --check` passent. Le processus live ne peut charger ce changement avant son prochain redémarrage. Les autres observations de la pièce jointe sur les métriques saturées, les modules sans effet vérifiable, le recall mémoire vide et les dérives des indicateurs restent des axes d’audit à établir avec leurs fichiers d’état et contrats d’écriture; les snapshots de forme ne suffisent pas à les confirmer.

## Addendum — verdict live après redémarrage du 10 novembre

Le relevé après redémarrage a d’abord observé **38 modules exécutés sur 43, 61 ticks, zéro exception instrumentée**. Après deux tours de vérification non-actuants, il en observait **41/43, 213 ticks et zéro exception**. Les deux modules sans tick étaient `semantic_graph_cleaner` (garde exploratoire et cadence de 50 cycles) et `persistent_executive_loop` (cadence de 10 cycles, non échue pendant la fenêtre observée). Cela confirme une exécution étendue, pas que chaque module est exécuté à chaque cycle ni que les deux modules conditionnels sont défectueux.

Les dernières qualités d’output étaient **12 `present`, 1 `present_redacted`, 28 `side_effect_only`**. Ce dernier état signifie que la méthode observée déclare `None` et est donc probablement à effets de bord; il ne confirme pas que l’effet attendu a atteint son destinataire. Les sorties structurées ont été inspectées pour leur forme, mais aucun validateur général ne prouve leur justesse cognitive. Le compteur d’exceptions à zéro prouve seulement qu’aucune exception n’a été enregistrée par l’instrumentation dans cette fenêtre.

Le test live le plus important a demandé à Lumina de distinguer exécution, traçabilité et justesse. Bien que le manifeste d’architecture du runtime ait été injecté dans le prompt, la réponse a affirmé sans preuve qu’un score supérieur à `0.80` rendait un résultat « hautement probable », a utilisé des scores de capacités sans lien démontré avec la validité des sorties de modules, et a présenté un état `healthy` comme garantie de qualité. **Le harness n’a donc pas respecté son propre contrat de preuve lors de ce test.** C’est un échec de qualité de réponse, pas un échec d’exécution des modules.

Les deux tours ont aussi fini avec `completed_with_stage_failures` et `pipeline_integrity=incomplete_evidence`, car `continuity_analysis_post_response` échouait. La cause était perdue lorsque `PersonaBridge.run_deferred_analysis` réduisait les statuts fournisseur à `failed`. Le code local conserve maintenant une classe de statut bornée (`EmptyProviderOutput`, `ProviderError` ou statut inattendu), sans enregistrer le texte ou la raison du fournisseur. Les tests ciblés correspondants passent (**3 tests** avec le statut du workflow), ainsi que `py_compile` et `git diff --check`. La nouvelle télémétrie doit être confirmée après le prochain redémarrage; le processus ayant servi au test n’a pas rechargé cette correction.

**Efficacité : résultat provisoire, pas de verdict global.** Sur le premier cycle observé, `long_horizon_planner` a pris environ **4,14 s** et `goal_quality_filter` **2,19 s**; plusieurs modules mesurés étaient sous 56 ms. Ce n’est qu’un échantillon de démarrage, insuffisant pour séparer coût normal, cache froid et régression. Le slow cycle est cadencé à 120 s : le débit prévu est faible pour ces tâches de fond, mais le temps total d’un cycle n’a pas montré de blocage dans la fenêtre observée.

**Conclusion d’audit :** l’instrumentation et l’exécution de la majorité des modules sont désormais observables; l’usage de tous les modules n’est pas démontré dans chaque fenêtre, les effets de bord ne sont pas confirmés de bout en bout, et l’efficacité n’est que partiellement mesurée. Surtout, le test live révèle que la réponse du Brain transforme encore des métriques d’exécution en certitude sémantique. Le système n’atteint donc pas encore le niveau attendu d’un harnais cognitif fiable : il faut relier chaque sortie importante à sa provenance, à un critère d’acceptation spécifique et, lorsque pertinent, à une preuve d’effet en aval; puis faire échouer ou nuancer la réponse si ces preuves manquent.

## Addendum — log reçu et cause des erreurs Phase 1

Le log partagé affiche des états numériques cohérents avec les plages attendues, mais ne valide pas à lui seul leur sens psychométrique. En particulier, la pression d’objectif est reproductible : `total_quality=0.69`, divisée par le pool de référence `8 × 0.5 = 4`, donne `0.1725`, arrondi à `0.17`. Curiosité `0.75`, stress d’identité `0.68`, valence `0.91` et pression relationnelle `0.49` sont des variables internes; aucun étalonnage contre une référence indépendante n’est montré par cet extrait. Les logs indiquent aussi 50 pensées évaluées, huit sujets passés par l’embedding, puis trois fragments rejetés ensuite. Le rejet final empêche leur promotion, mais ces termes devraient être filtrés plus tôt.

Une lecture live plus récente de `/api/interface/status` corrige le précédent instantané : **43 modules enregistrés, 42 exécutés, 5 947 ticks, 30 erreurs historiques, un module avec erreurs**. L’unique module concerné est `phase1_orchestrator`; son dernier type d’erreur est `UnboundLocalError`, capturé dans `simple_thought_evaluator.py`, ligne 109, fonction `evaluate_recent_thoughts`. Le dernier appel Phase 1 avait néanmoins réussi, d’où son état récent `healthy`; l’historique de 30 erreurs reste le signal pertinent. Cette lecture montre également `body_bridge.connected=false`, aucune observation Body, et la caméra PC inactive : les sorties live de perception ne sont donc pas actuellement alimentées par ces sources.

La cause de l’exception est confirmée statiquement : `datetime` était importé au niveau du module, puis réimporté localement seulement dans le chemin d’une pensée déjà évaluée. En Python, ce second import rend le nom local à toute la fonction. Une nouvelle pensée qui génère un candidat pouvait alors appeler `datetime.now()` avant l’exécution de cet import. Le code conserve désormais l’import global et n’importe localement que `timezone`. Une régression reproduisant une pensée neuve et un candidat de but couvre ce chemin.

Le lexique GoalEngine rejette maintenant `module` et `modules`, et le log répétitif de rejet est ramené au niveau `DEBUG` et dédoublonné par lot. Les mots adjectivaux « cognitive/cognitif » ne sont pas mis en liste noire, afin de préserver les sujets pertinents comme « cognitive architecture » ou « harnais cognitif ». Vérification ciblée : `tests/test_cognitive_log_regressions.py` **13/13 passent** (9 avertissements de dépendances/dépréciation). Les 30 erreurs déjà comptées sont historiques et ne disparaîtront pas dans ce processus; le prochain redémarrage devra confirmer qu’aucune nouvelle erreur Phase 1 n’est ajoutée.

Un relevé live ultérieur, avant redémarrage avec le correctif, a porté le compteur Phase 1 à **32 erreurs** (contre 30 au relevé précédent), sur **6 217 ticks** au total. Le dernier `enhanced_cycle` durait **2 685 ms**, et le dernier tick de `goal_action_executor` **360 ms**. Ce sont des maxima/dernières mesures ponctuelles, pas des moyennes; ils justifient un profilage séparé mais ne suffisent pas à conclure à une inefficacité systématique. L’appel Phase 1 est prévu toutes les deux slow cycles et l’évaluation des pensées tous les cinq cycles Phase 1. Le processus observé n’avait pas rechargé le correctif local, ce qui explique que l’erreur ait continué à augmenter.

### Preuve d’exécution au niveau des fichiers Python

Le registre cognitif suit 43 composants, pas tous les fichiers Python. Le dépôt contient **489 fichiers `.py` suivis par Git**; tests, scripts ponctuels, code Body et composants conditionnels ne sont pas censés tous s’exécuter dans chaque processus Brain. Un profilage opt-in est ajouté à `start.bat`: dans la même fenêtre de commande, exécuter `set LUMINA_MODULE_EXECUTION_AUDIT=1`, puis `start.bat`. Le profileur produit `logs/runtime_python_execution.json` toutes les 30 secondes et à l’arrêt propre. Il conserve seulement chemins, compteurs d’appels et indicateurs de corps de module, jamais code source, prompts, variables locales ou valeurs retournées. La session ajoute du coût de profilage; ne l’activer que pour l’audit.

Le rapport sépare les fichiers exécutés des non observés et distingue tests/outils, fichiers du code Body et Brain/bibliothèques partagées. Les catégories classent les chemins sources : tout chemin listé a exécuté du code dans le processus `app.py` et ses threads; cela ne prouve pas que le service Body distant tourne. Les sous-processus ne sont pas couverts. « Exécuté » prouve un événement d’exécution Python, pas l’exactitude de la sortie. L’essai de fumée a confirmé le comptage sur un fichier contrôlé (**1 fichier exécuté sur 489**).

### Résultats live de la session profilée du 10 novembre

Après redémarrage avec le profilage activé, le processus Brain était prêt et le rapport était écrit sous le PID `17992`. À **393 s d’uptime**, le profil signalait **284 fichiers exécutés sur 489** : **253 fichiers Brain/bibliothèques partagées**, **31 fichiers sous `body_runtime_host/` importés dans le processus Brain**, aucun test ou outil; **205 fichiers** restaient non observés dans cette session. Parmi ces derniers, **131** sont des tests/scripts/outils, **35** appartiennent au code Body, et **39** sont d’autres fichiers applicatifs ou bibliothèques, dont plusieurs modules anciens, visualisation, migration ou chemins optionnels. Les libellés sont calculés à partir des chemins sources; les 31 fichiers Body ont bien été appelés dans le processus Brain courant, ce qui ne prouve pas que le service Body distant est actif.

Le tick log live comptait **37 composants exécutés sur 43, 132 ticks et zéro erreur**. `phase1_orchestrator` avait deux ticks réussis, et `phase2_orchestrator` un tick réussi. Cela confirme en runtime que le correctif de `datetime` est chargé et que l’`UnboundLocalError` ne s’est pas reproduit sur les deux appels Phase 1 observés. Six composants restaient sans tick, tous déclarés conditionnels : `goal_quality_filter`, `goal_consolidator`, `semantic_graph_cleaner`, `persistent_executive_loop`, `cognitive_flux_engine` et `cognitive_attention_engine`. Leurs cadences respectives vont jusqu’à 50 cycles et plusieurs exigent des seuils de mode/budget; leur absence dans une session d’environ six minutes n’établit pas un défaut.

Le tour de diagnostic est néanmoins `completed_with_stage_failures`: `continuity_analysis_post_response` a échoué avec `EmptyProviderOutput`, et le traceur a conservé cette cause bornée. L’intégrité du tour reste `incomplete_evidence`; la correction de diagnostic révèle l’échec sans le résoudre. La caméra PC était inactive et le pont Body déconnecté, donc aucune perception live de ces sources n’était disponible.

**Conclusion de couverture :** la preuve répond à « quels fichiers ont exécuté du code dans ce démarrage ? », mais ne confirme pas que les 489 fichiers devraient tous être exécutés. Les exclusions incluent les tests, les outils, les services distincts, l’ancien code et les composants gardés par cadence ou scénario. Pour affirmer que chaque module requis est utilisé, il faut définir un manifeste des modules attendus par profil et scénario, puis comparer chaque scénario à ce manifeste. La preuve de justesse des outputs nécessite encore des assertions/critères fonctionnels par flux; les événements de profilage et les ticks ne la fournissent pas.
