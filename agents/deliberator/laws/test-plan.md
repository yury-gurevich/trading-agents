# Deliberator Law Test Plan

Every clause starts gray in S153. Rows are present so no new law is invisible.

| Clause | Proof obligation | Test type | Test(s) | Status |
| --- | --- | --- | --- | --- |
| DLIB-IDN-01 | Single job is adversarial PM order review. | functional | _tbd_ | ⬜ |
| DLIB-IDN-02 | Owns `DeliberationRun`; writes shared `LLMCall`. | functional | _tbd_ | ⬜ |
| DLIB-IDN-03 | One image supports three bounded identities. | functional | _tbd_ | ⬜ |
| DLIB-IN-01 | Manager accepts `PMRun` with `OrderIntentSet`. | functional | _tbd_ | ⬜ |
| DLIB-IN-02 | Peers accept only manager `DebateTurnRequest`. | functional | _tbd_ | ⬜ |
| DLIB-IN-03 | Manager verdict accepts only manager caller. | functional | _tbd_ | ⬜ |
| DLIB-IN-04 | Malformed input records fault and avoids execution mutation. | functional | _tbd_ | ⬜ |
| DLIB-TRG-01 | Manager pulls PMRun nodes lacking `DELIBERATED_BY`. | functional | _tbd_ | ⬜ |
| DLIB-TRG-02 | Peers serve request/reply. | functional | _tbd_ | ⬜ |
| DLIB-TRG-03 | No self-trigger or external feed polling. | functional | _tbd_ | ⬜ |
| DLIB-OUT-01 | Exactly one append-only `DeliberationRun` per processed PMRun, linked by `PMRun -DELIBERATED_BY-> DeliberationRun`. | functional | `test_deliberator_agent.py::test_manager_reviews_pending_pmrun_with_two_peer_rounds_and_llm_costs` | 🟩 |
| DLIB-OUT-02 | Run records verdicts, vetoes, debates, models, narrative, time. | functional | `test_deliberator_agent.py::test_manager_reviews_pending_pmrun_with_two_peer_rounds_and_llm_costs`; `test_concurrent_reviews.py::test_concurrent_reviews_preserve_durable_order`; `test_concurrent_reviews.py::test_single_order_failure_is_isolated_under_concurrency` | 🟩 |
| DLIB-OUT-03 | LLM calls write attributable shared `LLMCall`. | functional | _tbd_ | ⬜ |
| DLIB-OUT-04 | Non-uphold only subtracts PM-approved orders. | functional | _tbd_ | ⬜ |
| DLIB-NEV-01 | Never originates an order. | functional | _tbd_ | ⬜ |
| DLIB-NEV-02 | Never resizes an order. | functional | _tbd_ | ⬜ |
| DLIB-NEV-03 | Never talks to broker. | functional | _tbd_ | ⬜ |
| DLIB-NEV-04 | Never fetches market data directly. | functional | _tbd_ | ⬜ |
| DLIB-NEV-05 | Never imports another agent or orchestration. | functional | _tbd_ | ⬜ |
| DLIB-NEV-06 | Never hides failed debate or peer call as clean veto. | functional | `test_fail_open_reason.py::test_manager_fail_open_records_visible_rationale`; `test_manager_preflight.py::test_unreachable_peer_preflight_leaves_pmrun_unconsumed`; `test_manager_preflight.py::test_one_bad_peer_preflight_records_no_half_debate`; `tests/test_deliberator_correlated_peer.py::test_reply_inbox_stashes_pending_sibling_without_dead_letter` | 🟩 |
| DLIB-STA-01 | Manager is stateless between polls. | functional | _tbd_ | ⬜ |
| DLIB-STA-02 | Graph effects append-only and idempotent by PM run id. | functional | _tbd_ | ⬜ |
| DLIB-STA-03 | Peers write only shared LLM call audit nodes. | functional | _tbd_ | ⬜ |
| DLIB-IDM-01 | Already deliberated PMRun is no-op. | functional | _tbd_ | ⬜ |
| DLIB-IDM-02 | LLM output bounds are stamped. | functional | _tbd_ | ⬜ |
| DLIB-IDM-03 | Manager writes use PM run id. | functional | _tbd_ | ⬜ |
| DLIB-ORD-01 | Defender then challenger order is preserved per round. | functional | `test_concurrent_reviews.py::test_concurrent_reviews_preserve_durable_order` | 🟩 |
| DLIB-ORD-02 | Independent PMRun nodes process independently. | functional | _tbd_ | ⬜ |
| DLIB-ORD-03 | Duplicate peer replies are ignored by idempotent write semantics. | functional | _tbd_ | ⬜ |
| DLIB-FAIL-01 | LLM or peer-call failure is fail-open and recorded. | functional | `test_fail_open_reason.py::test_manager_fail_open_records_visible_rationale`; `test_fail_open_reason.py::test_manager_fail_open_records_usage_limit_reason`; `test_concurrent_reviews.py::test_single_order_failure_is_isolated_under_concurrency` | 🟩 |
| DLIB-FAIL-02 | Graph-write failure records fault, no delete. | functional | _tbd_ | ⬜ |
| DLIB-FAIL-03 | Crash recovery retries runs lacking `DELIBERATED_BY`. | functional | _tbd_ | ⬜ |
| DLIB-TYP-01 | Bus payloads match `contracts/deliberator.py`. | functional | _tbd_ | ⬜ |
| DLIB-TYP-02 | PM input validates as `OrderIntentSet`. | functional | _tbd_ | ⬜ |
| DLIB-TYP-03 | Verdict rulings are constrained. | functional | _tbd_ | ⬜ |
| DLIB-SEC-01 | Holds only scoped graph, bus, and LLM credentials. | functional | _tbd_ | ⬜ |
| DLIB-SEC-02 | API key never logged, graphed, or returned. | functional | _tbd_ | ⬜ |
| DLIB-SEC-03 | Peer capabilities accept only manager. | functional | _tbd_ | ⬜ |
| DLIB-SEC-04 | Revocation leaves trading fail-open. | functional | _tbd_ | ⬜ |
| DLIB-DEP-01 | Uses `DEP-POSTGRES` correctly. | functional | _tbd_ | ⬜ |
| DLIB-DEP-02 | Uses `DEP-BUS` correctly. | functional | `tests/test_deliberator_correlated_peer.py::test_debate_turn_skips_stale_ahead_of_genuine_reply_and_faults`; `tests/test_deliberator_correlated_peer.py::test_reply_inbox_stashes_pending_sibling_without_dead_letter`; `tests/test_deliberator_correlated_peer.py::test_prompt_peer_reply_is_one_receive_no_dead_letter` | 🟩 |
| DLIB-DEP-03 | Uses `DEP-LLM` correctly. | functional | _tbd_ | ⬜ |
| DLIB-DEP-04 | Uses `DEP-CONFIG` correctly. | functional | `test_concurrent_reviews.py::test_debate_concurrency_is_bounded_tunable` | 🟩 |
| DLIB-OBS-01 | Debate audit reconstructable from `DeliberationRun`. | functional | `test_concurrent_reviews.py::test_concurrent_reviews_preserve_durable_order` | 🟩 |
| DLIB-OBS-02 | LLM spend attributable per calling agent. | functional | _tbd_ | ⬜ |
| DLIB-OBS-03 | Fail-open outcomes visible in rationale. | functional | `test_fail_open_reason.py::test_manager_fail_open_records_visible_rationale`; `test_fail_open_reason.py::test_manager_fail_open_records_usage_limit_reason` | 🟩 |
| DLIB-PERF-01 | `max_rounds` bounds peer turns. | functional | _tbd_ | ⬜ |
| DLIB-PERF-02 | Peer wait time is bounded. | functional | `tests/test_deliberator_cold_peer_timing.py::test_cold_peer_poll_interval_is_inside_manager_timeout`; `tests/test_deliberator_correlated_peer.py::test_reply_inbox_deadline_expires_before_receive` | 🟩 |
