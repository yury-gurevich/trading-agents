# Sprints — handover to the coding agent

This folder holds **self-contained sprint plans**. Each is a handover a cold-start
coding agent can execute end to end without further context.

## Roles

- **Planning agent (owner of this folder, the PRD, the build plan, and STATE).**
  Decides *what* to build next and *why*, writes the sprint handover, reviews the
  result, and updates `docs/STATE.md` + `docs/build-plan.md` progress. Does not
  write production code.
- **Coding agent.** Executes exactly one active sprint plan: writes the code and
  tests, keeps the quality gate green, and hands back a short report. Stays within
  the sprint's scope; anything out of scope goes back to the planning agent.

## How a sprint runs

1. Planning agent writes `sprint-NN-<slug>.md` here and marks it active in STATE.
2. Coding agent branches `sprint-NN-<slug>`, implements the steps, gets the gate
   green, pushes, and reports back (files changed, coverage %, decisions/notes).
3. Planning agent reviews, merges to `main`, and updates STATE + build-plan status.

## Non-negotiable guardrails (every sprint)

These hold regardless of the sprint's specifics:

- **The one rule.** No agent imports another agent. The kernel imports nothing from
  `contracts`/`agents`. Agents talk only via typed messages. `import-linter` enforces.
- **Small files.** Every module < 200 lines (warn at 150). Split, don't grow.
- **Coding-agent header.** Every module's docstring declares `Agent:` and `Role:`
  (and `External I/O:` where relevant). Enforced by `scripts/check_module_header.py`.
- **No magic numbers.** Any value influencing processing or a forecast is declared
  with `kernel.tunable(..., why="...")` — justified and bounded — never a bare literal.
- **Faults, not silent failure.** Wrap fallible work in `kernel.fault_boundary`;
  errors are redirected with provenance, never swallowed.
- **Green before handback.** `make ci` must pass (ruff, format, mypy, import-linter,
  size + header guards, pytest at/above the coverage floor). Never lower the floor;
  raise it if measured coverage climbs.
- **Stay in scope.** Build only what the active sprint plan lists. Flag anything else.

## Validation (the gate)

```bash
make ci          # full local gate, mirrors GitHub CI
# or individually:
uv run ruff check . && uv run ruff format --check .
uv run mypy kernel contracts agents orchestration surfaces
uv run lint-imports
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests
uv run python scripts/check_module_header.py kernel contracts agents scripts
uv run pytest
```

## Index

| Sprint | Goal | Status |
| --- | --- | --- |
| [sprint-01](sprint-01-kernel-runtime.md) | Kernel runtime: in-process bus + AgentBase | **shipped** |
| [sprint-02](sprint-02-persistence.md) | Relational persistence adapter + migrations | **shipped** (superseded by ADR-0001) |
| [sprint-03](sprint-03-neo4j-store.md) | Neo4j GraphStore: retire relational adapter, graph spine | **shipped** |
| [sprint-04](sprint-04-provider-agent.md) | Provider agent: first real agent (data boundary + provenance) | **shipped** |
| [sprint-05](sprint-05-scanner-agent.md) | Scanner agent: first agent-to-agent call (universe → ranked candidates) | **shipped** |
| [sprint-06](sprint-06-analyst-agent.md) | Analyst agent: scored recommendations (closes the P2 slice) | **shipped** |
| [sprint-07](sprint-07-distributed-bus.md) | Distributed (Celery) bus: second MessageBus backend (P1 exit) | **shipped** |
| [sprint-08](sprint-08-observability-adapter.md) | Observability: kernel metrics adapter (throughput/latency/fault-rate) | **shipped** |
| [sprint-09](sprint-09-portfolio-manager.md) | Portfolio manager: sized, risk-checked order intents (starts P3) | **shipped** |
| [sprint-10](sprint-10-hardening.md) | Audit-truth & rigor hardening (rejection evidence, contract validators, graph/Neo4j rigor) | **shipped** |
| [sprint-11](sprint-11-execution.md) | Execution agent: idempotent broker boundary (paper stage, fills) | **shipped** |
| [sprint-12](sprint-12-monitor.md) | Monitor agent: open positions from fills, stop/target/time exits | **shipped** |
| [sprint-13](sprint-13-reporter.md) | Reporter agent: run snapshot + per-trade narrative (P3 exit) | **shipped** |
| [sprint-14](sprint-14-dispatcher.md) | Dispatcher: event-driven daily loop on both bus backends (P4 begins) | **shipped** |
| [sprint-15](sprint-15-supervisor.md) | Scheduler + supervisor message lineage (P4 exit) | **shipped** |
| [sprint-16](sprint-16-operator.md) | Operator agent: intent parsing + model-call ledger (P5 begins) | **shipped** |
| [sprint-17](sprint-17-supervisor-gate.md) | Supervisor capability gate + hard-NO surface (P5 exit) | **shipped** |
| [sprint-18](sprint-18-surfaces-cli.md) | Surfaces foundation + CLI: resolve_flag fix, query projections, terminal interface (P6 begins) | **shipped** |
| [sprint-19](sprint-19-list-nodes-lifecycle.md) | GraphStore list_nodes (Neo4j gap fix) + position lifecycle + pending-flags view (P6 continues) | **shipped** |
| [sprint-20](sprint-20-narrative-approve.md) | Trade narrative display + approve command (cli narrative + cli approve, P6 continues) | **shipped** |
| [sprint-21](sprint-21-incidents-explain-p6-exit.md) | Incident view + explain on demand + P6 exit test (P6 closes) | **shipped** |
| [sprint-22](sprint-22-mcp-tool-binding.md) | MCP tool-binding: operator + supervisor tools over Model Control Protocol (P1 closes) | **shipped** |
| [sprint-23](sprint-23-p7-researcher.md) | Researcher agent: propose bounded parameter changes + proposals surface + P7 exit test (P7 begins) | **shipped** |
| [sprint-24](sprint-24-p8-stage-gate.md) | Stage gate machinery: evidence-based promotion, StageTransition nodes, read-only cli stage (P8 begins) | **shipped** |
| [sprint-25](sprint-25-p8-market-pack.md) | Stage command wiring (cli stage promote → supervisor gate) + MarketPack abstraction + P8 exit test (P8 closes) | **shipped** |
| [sprint-26](sprint-26-p9-observability.md) | MeteredFaultSink wiring + P9 exit test + observability.md docs (P9 closes) | **shipped** |
| [sprint-27](sprint-27-p10-curator-datasets.md) | Curator agent: dataset assembly by provenance traversal, versioned splits, cli datasets (P10 begins) | **shipped** |
| [sprint-28](sprint-28-p10-training-trigger.md) | Curator training trigger: deterministic baseline predictor + frozen evidence, advisory-only, cli predictors (P10 training half) | **shipped** |
| [sprint-29](sprint-29-p10-predictor-registry.md) | Curator predictor registry: promote_predictor evidence gate + operator approval + PredictorPromotion audit (P10 exit) | **shipped** |
| [sprint-30](sprint-30-p11-analyst-technical-core.md) | Analyst technical scoring core: pure-Python RSI/MACD/Bollinger/SMA/EMA + band rules + composite (P11 begins) | **shipped** |
| [sprint-31](sprint-31-p11-analyst-oscillators.md) | Analyst oscillators + volatility: ATR/Stochastic/Williams %R/Choppiness folded into the composite (P11 cont.) | **shipped** |
| [sprint-32](sprint-32-p11-analyst-volume-event.md) | Analyst volume/event: OBV + golden cross + RSI-2 folded into the composite (P11 cont.) | **shipped** |
| [sprint-33](sprint-33-p11-analyst-patterns.md) | Analyst patterns/smoothing/calendar: Nadaraya-Watson kernel + geometric patterns + turnaround → composite up to 15 indicators (P11 cont.) | **shipped** |
| [sprint-34](sprint-34-provider-fundamentals.md) | Provider fundamentals feed: Finnhub /stock/metric → MarketData.fundamentals (unblocks analyst fundamental scoring) (P11 cont.) | **shipped** |
| [sprint-35](sprint-35-analyst-fundamental-scoring.md) | Analyst fundamental scoring: 8-metric pillar blended with technical into the confidence gate (P11 cont.) | **shipped** |
| [sprint-36](sprint-36-provider-news-feed.md) | Provider news feed: Finnhub /company-news → MarketData.news per-ticker headlines (feeds the analyst sentiment pillar) (P12) | **shipped** |
| [sprint-37](sprint-37-analyst-sentiment-pillar.md) | Analyst sentiment pillar: deterministic Loughran–McDonald lexicon as the binding third pillar in the renormalised blend (P12 champion) | **planned** |
| [sprint-38](sprint-38-analyst-relative-strength.md) | Analyst relative strength: benchmark-relative momentum blended into the technical pillar (0.8/0.2); separate fault-tolerant benchmark fetch (P11) | **shipped** |
| [sprint-39](sprint-39-analyst-signal-diversity.md) | Analyst signal-diversity selection: surface the top pillar-diverse signals in the recommendation rationale (explanatory, no score change) (P11) | **shipped** |
| [sprint-40](sprint-40-pm-reward-risk.md) | Portfolio manager reward/risk gate: reject orders whose target_pct/stop_pct is below min_reward_risk_ratio (P11) | **shipped** |
| [sprint-41](sprint-41-reporter-trade-outcomes.md) | Reporter: profit-factor and expectancy over stop/target-closed positions; new `domain/trade_outcomes.py` (P11) | **planned** |
| [sprint-43](sprint-43-monitor-realized-pnl.md) | Monitor realized PnL on close (`pnl_cents` on CloseDecision) — accuracy upgrade so the reporter can use real $ PnL across all triggers (P11) | **queued** (after S41) |
| [sprint-44](sprint-44-provider-tiingo-feed.md) | Provider Tiingo OHLCV feed: `TiingoDataSource` (full-S&P-500 live, ADR-0006) → re-point `market_source_from_settings` + `bindings.py` default off broken Stooq (closes DRIFT-009) | **shipped** |
| [sprint-45](sprint-45-execution-alpaca-broker.md) | Execution Alpaca paper broker: `AlpacaBroker` behind the `Broker` port (real fills, client_order_id idempotency) + `broker_from_settings` default swap (ADR-0006, DEP-BROKER) | **planned** |
