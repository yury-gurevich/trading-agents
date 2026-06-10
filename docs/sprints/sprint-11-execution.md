# Sprint 11 — Execution agent (the idempotent broker boundary, paper stage)

**Status:** active · **Branch:** `sprint-11-execution` · **Build phase:** P3 (decision loop) · **Effort: L**

## Goal

Implement the **`execution`** agent — the system's single boundary to the broker and the first
agent that *acts*. It takes the PM's approved `OrderIntentSet`, submits each intent to a **paper
broker** under an **idempotency key** (so re-submitting the same intent never creates a duplicate
order), records `Fill`s, answers `reconcile` / `stage_status`, and writes `Fill -[:EXECUTES]->
OrderIntent` — extending the chain to `Fill → OrderIntent → Recommendation → Candidate → ScanRun →
MarketSnapshot`. **Idempotency is the headline requirement** (PRD §8.2: broker submission must be
idempotent before live-adjacent stages). Stage = **paper** only this sprint; the gated promotion
to shadow/live is P8.

## Why (context)

- The PM decides; `execution` is the only agent allowed to touch the broker (`external_io =
  alpaca_broker`). Getting idempotency right *now*, on paper, is what makes live-adjacent stages
  safe later.
- It's the next link in the provenance chain and the first to record an *outcome* (`Fill`).
- Read first: `docs/sprints/README.md` (guardrails + gate); **`contracts/execution.py`** (THE
  contract — `Fill`/`ExecutionResult`/`ReconcileResult`/`StageStatus`, the four capabilities,
  `ExecutionStage`; implement exactly) and the payloads it builds on —
  `contracts/portfolio_manager.py` (`OrderIntentSet`/`OrderIntent`), `contracts/monitor.py`
  (`CloseDecisionSet` for `execute_close`), `contracts/common.py` (`Money`, `Provenance`);
  the **PM** as the pattern to copy — `agents/portfolio_manager/agent.py`,
  `agents/portfolio_manager/store.py` (cross-agent lineage + **money as integer cents** + the
  idempotent `merge_node`); `kernel/agent.py`, `kernel/bus.py`, `kernel/graph.py`,
  `kernel/config.py`; `docs/decisions/0001-neo4j-primary-store.md` (append-only, money as cents);
  `agents/execution/mission.md`; `docs/PRD.md` §8.2 (control plane / idempotency).
- Porting source: v1 `src/trading_v2/` execution — the paper-fill model + idempotency. Port the
  *logic* into <200-line modules.

## Key design constraints (do not break)

- **Implement `contracts/execution.py` exactly** — all **four** capabilities (`AgentBase.bind`
  requires a handler for each `consumes`): `submit(OrderIntentSet) -> ExecutionResult`,
  `execute_close(CloseDecisionSet) -> ExecutionResult`, `reconcile(ReconcileRequest) ->
  ReconcileResult`, `stage_status(StageStatusRequest) -> StageStatus`. Don't change the contract.
- **The one rule.** `agents/execution/` imports `kernel` + `contracts` only. It is the **sole**
  broker holder; all broker calls go through an injected `Broker` port. **Never** decide what to
  trade, size/override risk, or **skip the idempotency key** (contract `never`).
- **Idempotency is mandatory and end-to-end.** Derive a **stable** idempotency key per intent
  (e.g. `f"{order_set.run_id}:{ticker}:{side}"`). The `Broker` dedupes by it (re-submit returns
  the existing order), and the `Fill` node is keyed by it (`merge_node` → one node). Submitting
  the **same `OrderIntentSet` twice yields one order and one `Fill` per ticker** — a test must
  prove this.
- **Paper stage only.** `ExecutionSettings.stage` defaults to `"paper"`; the paper broker is
  deterministic and in-process (no external broker, no keys → gate stays infra-free). Stage
  promotion/demotion + the real Alpaca client are **out of scope** (P8 / live stages).
- **Money as integer cents in the graph; append-only; faults not silent.** `Fill.price` is
  `Money` in the payload; store cents in the graph. Wrap broker calls in `fault_boundary`; a
  rejected/failed submission is recorded as a `rejected` `Fill`/count with a reason, never a crash.
- **Provenance.** Write `Fill` + `Reconciliation` nodes and `Fill -[:EXECUTES]-> OrderIntent`
  (reconstruct the `OrderIntent` node key from `OrderIntentSet.provenance.graph_node_id`
  (`"PMRun:<id>"`) + ticker → `f"{pm_run_id}:{ticker}"` → `get_node("OrderIntent", key)` →
  `add_edge`; skip gracefully if absent).
- **Small files, headers, < 200 lines**; justified tunables; no magic numbers.

## Deliverables

1. **`agents/execution/broker.py`** — a `Broker` Protocol (`submit(idempotency_key, ticker, side,
   quantity, limit_price) -> BrokerFill`) and a deterministic **`PaperBroker`** that fills at a
   modelled price and **de-dupes by idempotency key** (re-submit returns the recorded order, never
   a new one). This is the paper-stage runtime broker *and* the test broker. (The real Alpaca
   client for live stages is a later sprint — flag it.)

2. **`agents/execution/settings.py`** — `ExecutionSettings(AgentSettings)`, `env_prefix=
   "EXECUTION_"`. Justified tunables: `stage` (default `"paper"`), a fill/slippage model knob
   (e.g. `slippage_bps`), and any partial-fill policy. Real broker creds (Alpaca) are secrets
   (`repr=False`) — declared but unused this sprint.

3. **`agents/execution/domain/`** — deterministic logic: build the idempotency key + the broker
   order from an `OrderIntent`; map a `BrokerFill` → contract `Fill`; the reconcile comparison
   (recorded fills vs broker state → matched count + discrepancies).

4. **`agents/execution/store.py`** — `Fill` nodes (idempotency-keyed; money as cents) +
   `Reconciliation` nodes, with `Fill -[:EXECUTES]-> OrderIntent` lineage; return `Provenance`.

5. **`agents/execution/agent.py`** — `ExecutionAgent(AgentBase)` (inject `graph`, `broker`,
   `settings`, `sink`) with all four handlers. `submit`: for each approved `OrderIntent`, submit
   idempotently → record `Fill` → return `ExecutionResult(stage, fills, submitted, rejected,
   provenance)`. `execute_close`: same broker path for `CloseDecisionSet` sells (implemented but
   not yet driven — `monitor` lands next). `reconcile`: matched/discrepancies. `stage_status`:
   the active stage + `idempotent=True`.

6. **`agents/execution/__init__.py`** — export `ExecutionAgent`. Update
   `agents/execution/mission.md`: replace the stale **Postgres** ownership line with the graph
   model (ADR-0001).

7. **`agents/execution/tests/`** — infra-free (`InProcessBus` + `InMemoryGraphStore` + `PaperBroker`):
   - **Idempotency (headline):** calling `submit` twice with the same `OrderIntentSet` yields one
     broker order and one `Fill` node per ticker; the result is stable.
   - `submit` records `filled` `Fill`s with `Money` price + `EXECUTES` lineage; a broker rejection
     → a `rejected` fill/count with a reason, no crash, fault recorded.
   - `execute_close` (a `CloseDecisionSet` fixture) submits sells; `reconcile` reports matched/
     discrepancies; `stage_status` returns `paper` + `idempotent=True`.
   - **Full-pipeline lineage:** wire `provider + scanner + analyst + portfolio_manager + execution`
     on one bus; drive `run_scan → analyze → evaluate_orders → submit`; assert the chain `Fill
     -[:EXECUTES]-> OrderIntent -[:APPROVES]-> Recommendation -[:DERIVED_FROM]-> Candidate
     -[:SURVIVED]-> ScanRun -[:DERIVED_FROM]-> MarketSnapshot`, with no agent importing another.

8. **Coverage floor** — re-tune to the new measured value (ratchet from 99.5; never lower).

## Steps

1. Branch `sprint-11-execution` off `main`.
2. `broker.py` (`Broker` + `PaperBroker`); `settings.py`; `domain/`.
3. `store.py` (Fill/Reconciliation + cents + EXECUTES lineage); `agent.py` (four handlers);
   `__init__.py`; refresh `mission.md`.
4. Write the tests (idempotency + the four capabilities + the 5-agent pipeline).
5. Run the gate; re-tune the floor. Push; hand back. Do not merge to `main`.

## Acceptance criteria

- All four capabilities answer over the bus; `import-linter` "agents may not import one another"
  KEPT; boundary meta-test green.
- **Idempotency proven:** double-submit → one order + one `Fill` per ticker. Broker rejection →
  honest `rejected` result, no crash. Money stored as integer cents.
- `Fill -[:EXECUTES]-> OrderIntent` lineage written; the full-pipeline test asserts the complete
  chain to `MarketSnapshot`.
- Stage is `paper`; gate needs **no external infra** (PaperBroker in-process).
- All modules headered, < 200 lines; tunables justified; `make ci` green at/above the floor.

## Out of scope (do NOT build this sprint)

The real Alpaca broker client + live stages (`broker_shadow`/`live_manual`/`live_autopilot`) and
the **gated stage promotion/demotion** (P8); `monitor` (the driver of `execute_close` — next P3
sprint; `execute_close` is implemented here but exercised only via a fixture); position lifecycle
(monitor); the `reporter`; `fill_recorded`/`stage_transitioned` as real pub/sub messages (P4 —
record in provenance for now); MCP (`mcp.py`). Flag anything you think is needed earlier.

## Handback report (paste into the PR / reply)

- Files added/changed and final line counts; the `Broker` port + idempotency-key design; the
  paper fill model; how cents storage + the `EXECUTES` lineage are done.
- New coverage % and the re-tuned floor; confirmation the idempotency test and the full-pipeline
  lineage test pass.
- Any design decision worth recording or anything that felt out of scope.

The planning agent will review, merge to `main`, and update `docs/STATE.md` +
`docs/build-plan.md`. After this, P3 continues with `monitor`.
