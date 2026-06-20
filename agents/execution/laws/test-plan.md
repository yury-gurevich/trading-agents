# Execution — Test plan (living)

Each row pins one law-ID to a **functional test** that proves it. This document is the
**master**: discovering a needed test with no law → add the law to `laws.md` first,
then add a row here. A test's docstring **must cite the law-ID** it proves (conventions §7).

Status: ⬜ gray (no passing test) · 🟩 green (≥1 passing test cites the ID)

**Precondition:** `DEP-BUS, DEP-NEO4J, DEP-BROKER` must be green first
(see `docs/laws/dependencies.md`).

## Inputs / triggers

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-IN-01 | Valid OrderIntentSet accepted; approved entries are submitted. | happy | `test_execution_agent.py::test_submit_records_fill_cents_and_executes_lineage` | 🟩 |
| EXEC-IN-02 | execute_close accepts a CloseDecisionSet; close entries submitted. | happy | `test_execution_agent.py::test_execute_close_stage_status_and_reconcile` | 🟩 |
| EXEC-IN-03 | portfolio.orders.ready claim-check resolved before submit. | pub/sub | `test_execution_pubsub.py::test_orders_ready_triggers_fills_ready` | 🟩 |
| EXEC-IN-04 | promote_stage confirmed=False is dry-run; no StageTransition written. | boundary | _tbd_ | ⬜ |
| EXEC-TRG-01 | RPC submit returns an ExecutionResult with stage, fills, submitted count. | happy | `test_execution_agent.py::test_submit_records_fill_cents_and_executes_lineage` | 🟩 |
| EXEC-TRG-02 | portfolio.orders.ready → submit → execution.fills.ready emitted. | pub/sub | `test_execution_pubsub.py::test_orders_ready_triggers_fills_ready` | 🟩 |
| EXEC-TRG-03 | RPC execute_close returns ExecutionResult from monitor-sourced closes. | happy | `test_execution_agent.py::test_execute_close_stage_status_and_reconcile` | 🟩 |
| EXEC-TRG-05 | RPC stage_status returns current stage without side effects. | read-only | `test_execution_agent.py::test_execute_close_stage_status_and_reconcile` | 🟩 |
| EXEC-TRG-06 | promote_stage with confirmed=True writes StageTransition. | gate | `test_promote_stage.py::test_promote_stage_confirmed_writes_transition_and_status_reads_graph` | 🟩 |

## Outputs

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-OUT-01 | ExecutionResult always returned with stage, fills, submitted, pm_run_id. | happy | `test_execution_agent.py::test_submit_records_fill_cents_and_executes_lineage` | 🟩 |
| EXEC-OUT-02 | Fill carries ticker, side, quantity, price (Decimal), broker_order_id, status. | schema | `test_execution_agent.py::test_submit_records_fill_cents_and_executes_lineage` | 🟩 |
| EXEC-OUT-03 | Stage not in {paper, broker_shadow} → submitted=0; no broker call. | gate | `test_promote_stage.py::test_submit_rejects_live_manual_without_broker_call` | 🟩 |
| EXEC-OUT-04 | reconcile returns ReconcileResult with matched count + discrepancies. | reconcile | `test_execution_agent.py::test_reconcile_reports_unrecorded_broker_fill` | 🟩 |
| EXEC-OUT-05 | promote_stage returns PromoteStageResult with from/to stage + evidence. | gate | `test_promote_stage.py::test_promote_stage_writes_flag_when_evidence_passes` | 🟩 |
| EXEC-OUT-06 | execution.fills.ready event is a claim-check ref; run_id in envelope. | pub/sub | `test_execution_pubsub.py::test_run_id_propagated_in_fills_ready_event` | 🟩 |

## Prohibitions

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-NEV-01 | Execution has no scoring or selection logic; executes approved intents only. | boundary | `test_execution_agent.py::test_broker_failure_records_rejected_fill_and_fault` | 🟩 |
| EXEC-NEV-02 | Fill.quantity equals OrderIntent.quantity (no override). | invariance | _tbd_ | ⬜ |
| EXEC-NEV-03 | Every broker submission includes a client_order_id; never omitted. | idempotency | `test_execution_agent.py::test_submit_is_idempotent_per_order_intent` | 🟩 |
| EXEC-NEV-04 | promote_stage without evidence gate passes → blocked. | gate | `test_promote_stage.py::test_promote_stage_blocked_without_evidence` | 🟩 |
| EXEC-NEV-05 | Credentials never appear in any response or graph node. | security | _tbd_ | ⬜ |

## State & effects

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-STA-01 | In-process _recorded dict rebuilt from graph Fill nodes on restart. | stateful | `test_execution_agent.py::test_reconcile_reports_unrecorded_broker_fill` | 🟩 |
| EXEC-STA-02 | Stage is graph-authoritative; latest StageTransition wins. | stateful | `test_stage_gate.py::test_current_stage_from_graph_falls_back_and_reads_latest_transition` | 🟩 |
| EXEC-STA-03 | Graph writes are append-only; no Fill modified after creation. | append-only | `test_execution_agent.py::test_submit_records_fill_cents_and_executes_lineage` | 🟩 |

## Determinism & idempotency

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-IDM-01 | Same OrderIntentSet replays identically; broker called once per intent. | idempotency | `test_execution_agent.py::test_submit_is_idempotent_per_order_intent` | 🟩 |
| EXEC-IDM-02 | client_order_id is stable across retries (derived from intent_id). | idempotency | `test_execution_pubsub.py::test_run_id_propagated_in_fills_ready_event` | 🟩 |

## Failure & recovery

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-FAIL-01 | Broker timeout on one order → Fill(rejected) recorded; next order proceeds. | partial | `test_execution_agent.py::test_broker_rejection_records_rejected_fill_and_fault` | 🟩 |
| EXEC-FAIL-02 | Broker total unavailability → all orders rejected; submitted=0; fault. | fault | `test_execution_agent.py::test_broker_failure_records_rejected_fill_and_fault` | 🟩 |
| EXEC-FAIL-03 | Graph write failure → fills still in-process; safe to retry. | fault | _tbd_ | ⬜ |

## Type alignment

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-TYP-01 | Fill.price is Decimal; broker string parsed before persisting. | schema | `test_execution_agent.py::test_submit_records_fill_cents_and_executes_lineage` | 🟩 |
| EXEC-TYP-02 | Fill.status ∈ {filled, partial, rejected, pending}; no other values. | schema | `test_execution_agent.py::test_broker_rejection_records_rejected_fill_and_fault` | 🟩 |
| EXEC-TYP-03 | ExecutionResult deserialises from graph node per contract schema. | schema | `test_execution_pubsub.py::test_execution_result_is_deserializable` | 🟩 |

## Security

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-SEC-01 | Credentials never appear in responses, graph nodes, or fault records. | security | _tbd_ | ⬜ |
| EXEC-SEC-03 | Unauthorized caller for submit is refused. | authz | _tbd_ | ⬜ |
| EXEC-SEC-04 | Stage gate blocks live* stage submissions without multi-step promotion. | gate | `test_promote_stage.py::test_submit_rejects_live_manual_without_broker_call` | 🟩 |

## Observability

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-OBS-01 | Fill, Reconciliation, and StageTransition nodes reconstructable from graph. | audit | `test_execution_agent.py::test_submit_records_fill_cents_and_executes_lineage` | 🟩 |
| EXEC-OBS-02 | Broker rejections and stage-gate rejections routed to central channel. | observable | `test_execution_agent.py::test_broker_rejection_records_rejected_fill_and_fault` | 🟩 |
