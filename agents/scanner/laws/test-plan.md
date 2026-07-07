# Scanner — Test plan (living)

Each row pins one law-ID to a **functional test** that proves it. This document is the
**master**: discovering a needed test with no law → add the law to `laws.md` first,
then add a row here. A test's docstring **must cite the law-ID** it proves (conventions §7).

Status: ⬜ gray (no passing test) · 🟩 green (≥1 passing test cites the ID)

**Precondition:** `DEP-BUS, DEP-POSTGRES` must be green first (see `docs/laws/dependencies.md`).

## Inputs / triggers

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| SCAN-IN-01 | Valid ScanRequest accepted; ranked candidates returned. | happy | `test_scanner_agent.py::test_run_scan_calls_provider_and_returns_ranked_candidates` | 🟩 |
| SCAN-IN-02 | run.trigger event derives ScanRequest and invokes run_scan. | pub/sub | `test_scanner_pubsub.py::test_run_trigger_publishes_candidates_ready` | 🟩 |
| SCAN-IN-03 | Empty universe → empty CandidateSet with explanation, no crash. | boundary | _tbd_ | ⬜ |
| SCAN-TRG-01 | RPC run_scan returns a CandidateSet to the caller. | happy | `test_scanner_agent.py::test_run_scan_calls_provider_and_returns_ranked_candidates` | 🟩 |
| SCAN-TRG-02 | run.trigger → run_scan → scan.candidates.ready emitted with claim-check ref. | pub/sub | `test_scanner_pubsub.py::test_run_trigger_publishes_candidates_ready` | 🟩 |
| SCAN-TRG-03 | No trigger → zero provider calls, zero graph writes. | negative | _tbd_ | ⬜ |

## Outputs

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| SCAN-OUT-01 | CandidateSet always returned; never null, never raises. | happy | `test_scanner_agent.py::test_run_scan_calls_provider_and_returns_ranked_candidates` | 🟩 |
| SCAN-OUT-02 | FilterTrace accounts for every ticker (universe_size == evaluated + dropped). | accounting | `test_scanner_agent.py::test_run_scan_calls_provider_and_returns_ranked_candidates` | 🟩 |
| SCAN-OUT-03 | Provider degraded → empty CandidateSet + fault recorded; no crash. | degraded | `test_scanner_agent.py::test_degraded_provider_path_returns_empty_explained_result` | 🟩 |
| SCAN-OUT-04 | Pub/sub event carries claim-check ref only, not CandidateSet payload. | pub/sub | `test_scanner_pubsub.py::test_run_trigger_publishes_candidates_ready` | 🟩 |
| SCAN-OUT-05 | explain_filter returns Explanation; no provider call, no graph write. | read-only | `test_scanner_agent.py::test_explain_filter_returns_grounded_explanation` | 🟩 |

## Prohibitions

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| SCAN-NEV-01 | Scanner never calls a data feed directly; all data through provider on the bus. | boundary | `test_scanner_agent.py::test_run_scan_calls_provider_and_returns_ranked_candidates` | 🟩 |
| SCAN-NEV-02 | Ranking uses no fundamental or sentiment logic. | invariance | _tbd_ | ⬜ |
| SCAN-NEV-03 | No result is produced without an explanation (never silent). | negative | `test_scanner_agent.py::test_degraded_provider_path_returns_empty_explained_result` | 🟩 |

## State & effects

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| SCAN-STA-01 | Two independent scans do not share state (second run is independent). | stateless | _tbd_ | ⬜ |
| SCAN-STA-02 | run_scan writes a ScanRun node to the graph; prior runs are unchanged. | append-only | `test_scanner_pubsub.py::test_scan_result_node_written_to_graph` | 🟩 |

## Determinism & idempotency

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| SCAN-IDM-01 | Same market data + same settings → same CandidateSet. | determinism | _tbd_ | ⬜ |
| SCAN-IDM-02 | run_id from trigger threaded to scan.candidates.ready event. | provenance | `test_scanner_pubsub.py::test_run_id_propagated_in_ready_event` | 🟩 |

## Ordering & concurrency

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| SCAN-ORD-01 | Two consecutive scans produce independent CandidateSets. | ordering | _tbd_ | ⬜ |

## Failure & recovery

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| SCAN-FAIL-01 | Provider bus timeout → empty CandidateSet + fault; no exception to caller. | fault | `test_scanner_agent.py::test_degraded_provider_path_returns_empty_explained_result` | 🟩 |
| SCAN-FAIL-02 | Per-ticker filter error → that ticker dropped; others proceed. | partial | _tbd_ | ⬜ |

## Type alignment

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| SCAN-TYP-01 | CandidateSet validates against contracts/scanner.py CONTRACT schema. | schema | `test_scanner_pubsub.py::test_scan_result_node_candidates_are_deserializable` | 🟩 |
| SCAN-TYP-02 | Candidate.rank ≥ 1; FilterTrace counts are non-negative integers. | schema | `test_scanner_agent.py::test_run_scan_calls_provider_and_returns_ranked_candidates` | 🟩 |

## Security

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| SCAN-SEC-02 | Unauthorized caller is refused by the capability gate. | authz | _tbd_ | ⬜ |

## Observability

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| SCAN-OBS-01 | ScanRun node in graph is reconstructable into the CandidateSet. | audit | `test_scanner_agent.py::test_scan_provenance_links_candidates_to_provider_snapshot` | 🟩 |
| SCAN-OBS-02 | Fault recorded to sink on provider degradation; not silent. | observable | `test_scanner_agent.py::test_degraded_provider_path_returns_empty_explained_result` | 🟩 |
