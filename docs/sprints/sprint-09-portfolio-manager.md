# Sprint 09 — Portfolio manager (starts P3, the decision loop)

**Status:** shipped (merged to `main` @ `6a36a3a`; audit-truth follow-ups → hardening sprint) · **Branch:** `sprint-09-portfolio-manager` · **Build phase:** P3 (decision loop)

## Goal

Implement the **`portfolio_manager`** (PM): take the analyst's `RecommendationSet` and decide
which become **sized, risk-checked order intents** under current policy and portfolio state,
recording exactly why each was approved or rejected. It calls `provider` over the bus for the
estimated price and the regime, applies deterministic sizing + risk checks against a portfolio,
and writes `OrderIntent -[:APPROVES]-> Recommendation` provenance — extending the lineage to
`OrderIntent → Recommendation → Candidate → ScanRun → MarketSnapshot`. This is the **first
agent that handles money** and **maintains portfolio state**, so it establishes both patterns.

## Why (context)

- P2 produced explained recommendations. P3 turns them into a daily decision loop; the PM is
  step one (`portfolio_manager → execution → monitor → reporter`).
- It is the second agent to call `provider` over the bus and the next link in the cross-agent
  provenance chain. It also forces the ADR-0001 **money discipline** (integer minor units in
  the graph) for the first time, since `OrderIntent` carries a price.
- Read first: `docs/sprints/README.md` (guardrails + gate); **`contracts/portfolio_manager.py`**
  (THE contract — `OrderIntent`/`RejectedOrder`/`OrderIntentSet`, implement exactly) and the
  payloads it builds on — `contracts/analyst.py` (`RecommendationSet`/`Recommendation`),
  `contracts/provider.py` (`DataRequest`/`MarketData`, `RegimeRequest`/`RegimeContext`),
  `contracts/common.py` (`Action`, `Money`, `Explanation`, `Provenance`); the **analyst** as
  the exact pattern to copy — `agents/analyst/agent.py` + `agents/analyst/provider_client.py`
  (the two provider bus calls) + `agents/analyst/store.py` (cross-agent lineage by parsing
  `provenance.graph_node_id`); `kernel/agent.py`, `kernel/bus.py`, `kernel/graph.py`,
  `kernel/config.py`; `docs/decisions/0001-neo4j-primary-store.md` (**money as integer minor
  units**, append-only); `agents/portfolio_manager/mission.md`.
- Porting source: v1 `src/trading_v2/` PM sizing + risk logic (`STARTING_CASH`,
  `MAX_POSITIONS`, `CASH_BUFFER_PCT`, `PORTFOLIO_MANAGER_MAX_POSITION_PCT` are the reference
  defaults). Port the *logic* into <200-line modules.

## Key design constraints (do not break)

- **Implement `contracts/portfolio_manager.py` exactly** — `evaluate_orders(RecommendationSet)
  -> OrderIntentSet` and `explain_decision(RecommendationSet) -> Explanation`. Don't change the
  contract or the boundary map.
- **The one rule.** `agents/portfolio_manager/` imports `kernel` + `contracts` only — never
  another agent. Reach `provider` via `self.bus.request(...)` (two calls: `get_market_data` for
  est. price, `get_regime` for policy). **Never** call the broker, call a market-data API, or
  promote an execution stage (contract `never`).
- **Money as integer minor units in the graph (ADR-0001).** `OrderIntent.est_price` is `Money`
  (`Decimal`) in the *payload*; when writing to the graph, store monetary values as **integer
  cents** (`int(amount * 100)`), never float. Sizing math uses `Decimal`, not float.
- **Deterministic sizing + explainable rejections.** Process recommendations in a deterministic
  order (e.g. confidence desc, ticker tiebreak). Size each to a policy fraction of portfolio
  value; **reject** (with a portfolio-level reason: `insufficient_cash`, `max_positions`,
  `below_min_quantity`, …) when a check fails. `OrderIntentSet.explanation` states why these
  or why none.
- **Faults, not silent failure.** Wrap the provider calls + sizing in `fault_boundary`; a
  degraded/failed provider yields an honest explained result (e.g. all rejected with a reason),
  never a crash.
- **Provenance lineage.** Write `PMRun` + `OrderIntent` nodes and the
  `OrderIntent -[:APPROVES]-> Recommendation` edge — reconstruct each `Recommendation` node key
  from the incoming `RecommendationSet.provenance.graph_node_id` (`"AnalystRun:<id>"`) + ticker
  → `f"{analyst_run_id}:{ticker}"` → `get_node("Recommendation", key)` → `add_edge`. Skip
  gracefully if absent.
- **Small files, headers, < 200 lines**; justified tunables; no magic numbers.

## Deliverables

1. **`agents/portfolio_manager/provider_client.py`** — the two provider bus calls
   (`get_market_data` for latest close as est. price; `get_regime` for `base_*` policy),
   mirroring `agents/analyst/provider_client.py`. (Per-agent; agents can't share via import.)

2. **`agents/portfolio_manager/portfolio.py`** — a `PortfolioState` value object (cash +
   open positions) and a default source that is **fresh from settings** (`starting_cash`, no
   positions) for this slice. Tests can inject a portfolio with existing positions to exercise
   risk caps. (Real position tracking arrives with `execution`/`monitor` later in P3 — flag it.)

3. **`agents/portfolio_manager/settings.py`** — `PortfolioManagerSettings(AgentSettings)`,
   `env_prefix="PORTFOLIO_MANAGER_"`. Justified tunables: `starting_cash`, `max_position_pct`,
   `max_positions`, `cash_buffer_pct`, and a `min_order_quantity`. All via
   `kernel.tunable(why=..., bounds)`.

4. **`agents/portfolio_manager/domain/`** — deterministic logic:
   - `sizing.py`: quantity from (portfolio value × `max_position_pct`) ÷ est. price, in
     `Decimal`, floored to whole shares.
   - `risk.py`: the checks — available cash after `cash_buffer_pct`, `max_positions`,
     `min_order_quantity` — producing approve/reject with reasons. (Sector/correlation caps are
     out of scope — they need sector data + a correlation model.)

5. **`agents/portfolio_manager/store.py`** — `PMRun` + `OrderIntent` nodes (**money as integer
   cents**) and the `OrderIntent -[:APPROVES]-> Recommendation` edges; return `Provenance`.

6. **`agents/portfolio_manager/agent.py`** — `PortfolioManagerAgent(AgentBase)` (inject `graph`,
   `settings`, `portfolio`, `sink`). `evaluate_orders`: fetch est. prices + regime from
   provider → size + risk-check the recommendations against the portfolio → write provenance →
   return `OrderIntentSet`. `explain_decision`: a grounded `Explanation`.

7. **`agents/portfolio_manager/__init__.py`** — export `PortfolioManagerAgent`. Update
   `agents/portfolio_manager/mission.md`: replace the stale **Postgres** ownership line with the
   graph model (ADR-0001).

8. **`agents/portfolio_manager/tests/`** — infra-free (`InProcessBus` + `InMemoryGraphStore` +
   a real `ProviderAgent` on a `FakeDataSource`):
   - **Unit** (a `RecommendationSet` fixture): `evaluate_orders` sizes approved orders correctly
     (quantity, est_price as `Money`); risk-rejects with the right reason when cash/position
     limits bind; money is stored as integer cents in the graph; degraded provider → honest
     explained result, fault recorded.
   - **Pipeline lineage:** wire `provider + scanner + analyst + portfolio_manager` on one bus;
     drive `run_scan → analyze → evaluate_orders`; assert the chain `OrderIntent ->APPROVES->
     Recommendation ->DERIVED_FROM-> Candidate ->SURVIVED-> ScanRun ->DERIVED_FROM->
     MarketSnapshot` (traverse the graph), with no agent importing another.
   - `explain_decision` returns a grounded `Explanation`.

9. **Coverage floor** — re-tune in `pyproject.toml` (both places) to the new measured value.

## Steps

1. Branch `sprint-09-portfolio-manager` off `main`.
2. `provider_client.py`, `portfolio.py`, `settings.py`; `domain/sizing.py` + `domain/risk.py`.
3. `store.py` (graph + money-as-cents + APPROVES lineage); `agent.py`; `__init__.py`; refresh
   `mission.md`.
4. Write the tests (unit + the 4-agent pipeline lineage test).
5. Run the gate; re-tune the floor. Push; hand back. Do not merge to `main`.

## Acceptance criteria

- Both capabilities answer over the bus; the PM gets data **only** via `self.bus.request` to
  provider; `import-linter` "agents may not import one another" KEPT; boundary meta-test green.
- Deterministic sizing + risk checks with explainable rejections; degraded provider → honest
  result, no crash; **money stored as integer cents** in the graph.
- The pipeline lineage test passes, asserting `OrderIntent → Recommendation → Candidate →
  ScanRun → MarketSnapshot`.
- All modules headered, < 200 lines; tunables justified; no magic numbers.
- `make ci` green at/above the re-tuned floor; no external infra.

## Out of scope (do NOT build this sprint)

The `forecaster` advisory input (it doesn't exist yet and is shadow/optional — the PM works
without it; flag the integration point); sector/correlation risk caps (need sector data + a
correlation model); `execution`/`monitor` and real position tracking (the PM uses a fresh
portfolio for now — positions land with those agents); the operator approval queue / human
approval (P5); `orders_decided` as a real pub/sub message (no pub/sub until P4 — record in
provenance); MCP (`mcp.py`). Flag anything you think is needed earlier.

## Handback report (paste into the PR / reply)

- Files added/changed and final line counts; the sizing/risk model implemented; how the two
  provider calls, the money-as-cents storage, and the `APPROVES` lineage are done; how
  portfolio state is sourced.
- New coverage % and the re-tuned floor; confirmation the pipeline lineage test passes.
- Any design decision worth recording or anything that felt out of scope.

The planning agent will review, merge to `main`, and update `docs/STATE.md` +
`docs/build-plan.md`.
