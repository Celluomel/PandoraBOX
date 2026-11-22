# Conversation / cognitive regression — Phase 1

Date: 2026-11-22
Scope: restore the conversation as owner of ordinary answer delivery while preserving cognition and safety boundaries.

## Result

**The principal authority inversion is fixed and live-tested. Phase 1 is substantially verified, but the full post-fix 19-case rerun and a rapid-turn ordering check remain open.** The semantic reviewer no longer has authority to veto or replace ordinary delivered prose. Cognitive learning and reflection are retained and scheduled outside the response critical path. Output safety, evidence-sensitive memory behavior, and physical-action validation remain separate controls.

## Baseline and live comparison

The Phase 0 live corpus had 19 turns, 75 attributed foreground provider calls (19 primary generations, 54 reviewer/helper calls, plus two direct analyses), 7/19 answer replacements by refusal, and 38.48 s median end-to-end latency. The first visible answer delta arrived at the end of each turn.

The first Phase 1 live run covered the same 19 cases and showed an early improvement. After the final camera-routing, trace-label, and turn-correlation fixes, the complete saved corpus was run again against the restarted current process. The corpus now contains 23 cases; comparison below uses the 19 case IDs shared with Phase 0:

- Final live corpus: **23/23 completed**, all 23 pipeline-integrity receipts `consistent`, 28 attributed provider calls. The 19 shared cases used 24 calls versus 75 in Phase 0 (68% fewer); 19 primary responses remained one call each, and two state-signaled reviews ran after delivery. The two extra review turns used a non-stream call that returned no text and the existing stream fallback, so each review took two provider calls. One additional call was a bounded action-planning analysis.
- **0 reviewer-driven refusals or answer replacements.** Review receipts explicitly report `response_replaced=false`; an unavailable/invalid advisory receipt remains advisory and cannot suppress the answer.
- Median end-to-end latency / first visible token on the 19 shared cases: **11.78 s**, versus 38.48 s in Phase 0 (**69.4% lower**). p95 is about 29.26 s. Across all 23 Phase 1 cases the median was 11.61 s.
- The first visible delta still arrived at the end of every generated turn (19/19 shared cases and 23/23 final cases). This fix removes reviewer/post-response work from the critical path; it does not solve delayed token streaming or slow primary model generation.
- Pipeline integrity checks ordering/data flow, not semantic correctness.

The camera classifier was an unintended lexical route. It has since been removed from ordinary conversation routing. A live repeat of the exact “glad to see” social case completed with one foreground provider call and a `review_not_required_single_pass` receipt. Its answer was relevant but more verbose than ideal. A structured affect introspection request was also live-tested and returned numeric channels only when `debug_introspection=true`; it required zero provider calls.

The 19-case run found a `_displayed_trace` scope error on the first attempted launch. That run was retained as a failed artifact, the reference was corrected to the in-scope `displayed_cognitive_trace`, regression-tested, and the corrected app was restarted before the valid run. The final code was then reloaded and the complete 23-case corpus passed. The ordinary-camera route regression was absent in the final corpus; the explicit response “glad to see the system awake” used one primary call.

## Changes

- `cognition/persona_bridge.py`: ordinary prose uses one primary generation by default; semantic review is advisory after delivery and cannot alter the answer. Post-response learning/reflection work is retained as background tasks. Normal affect context is qualitative. The obsolete ordinary-conversation camera-keyword gateway was removed. Deferred-review provider activity now sets the originating turn ID in the execution context for attribution.
- `cognition/semantic_response_validation.py`: the review prompt now explicitly frames its role as a non-authoritative post-response advisor, not a quality gate.
- `cognition/self_description.py`: provides a qualitative private affect advisory; structured debug introspection is the explicit numeric route.
- `core/interface_api.py`, `core/state.py`: carry the explicit introspection flag, schedule advisory review after the visible response, and retain background receipts.
- `start.bat`: audit mode launches the combined provider-call and Python-module execution wrapper.
- Tests cover advisory-only semantics, async cognitive work, turn correlation, affect formatting, ordinary camera wording, trace status, scope regression, and audit launcher wiring.

No cognitive modules were removed. No phrase list was added as a routing solution. No Body or actuation code was changed.

## Verification

- Final live Phase 1 corpus: 23/23 completed; 0 reviewer vetoes; 28 provider calls; all pipeline receipts `consistent`. The 19-case matched comparison is 24 calls and median 11.78 s versus 75 calls and 38.48 s at baseline.
- Live receipts prove the two state-signaled semantic reviews were scheduled post-response. Their provider calls share the originating turn IDs. One retained live receipt ended `unavailable`; the answer remained delivered and the receipt says `response_replaced=false`.
- Explicit numeric affect introspection returned a structured result with zero provider calls. Ordinary social case used one foreground generation and reported `review_not_required_single_pass`.
- Offline tests on the current code: `venv\\Scripts\\python.exe -m pytest -q tests/test_conversation_authority_phase1.py tests/test_turn_execution_evidence.py` — **60 passed**, 10 dependency warnings; `PYTHONIOENCODING=utf-8 venv\\Scripts\\python.exe -m unittest discover -s tests -p test_interface_api.py` — **17 passed**; `git diff --check` passed (with repository-wide LF/CRLF informational warnings).
- The added focused test confirms deferred-review execution inherits the originating turn ID and resets context afterward.
- The aspirational <2 s first-token target is **not met**. The median is much better than baseline, but primary model generation still dominates and two turns exceeded 30 s.

## Remaining work

1. The final corpus included back-to-back goal turns and showed distinct provider-call and turn IDs; add a dedicated check for post-response reflection-state ordering if Phase 2 changes the collector again.
2. Improve true first-token latency and answer concision without reintroducing reviewer vetoes; current time-to-first-token equals end-of-generation time.
3. Continue the broader cognitive harness audit: this Phase 1 result does not establish correctness or usefulness for every module or scenario.

Raw per-turn JSONL, provider logs, and prompt/answer transcripts remain local and are not included in this GitHub change. The report publishes aggregate metrics only.

## Conclusion

The audit’s central diagnosis is supported: a probabilistic semantic reviewer had excessive authority and dominated latency. Removing that veto and moving non-safety post-response work off the delivery path produced a large measured improvement while preserving the cognitive modules and hard safety/action boundaries. This is a meaningful Phase 1 milestone, not a claim that all cognitive outputs are correct or that the entire harness audit is complete.
