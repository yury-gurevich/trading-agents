<!-- Agent: planning | Role: sprint handover -->
# Sprint 41 — Reporter: profit-factor and expectancy (P11)

**Status:** planned · **Branch:** `sprint-41-reporter-trade-outcomes` · **Build phase:** P11 · **Effort: S**

## Goal

Add two standard trading-performance metrics — **profit factor** and **trade expectancy** — to the
reporter's run snapshot. Both are computed as pure deterministic functions over the position and
close-decision nodes the reporter already reads from the provenance graph; no new graph traversal,
no new contract fields, no new dependencies.

This is the first of three small P11 completions (reporter, then scanner, then PM sector cap). All
are independent of the P12 sentiment sprints (S36/S37) running in parallel.

## Why (context)

- Read first: `docs/sprints/README.md` (guardrails); `docs/build-plan.md` §P11 (profit-factor +
  expectancy listed as committed reporter scope under "Reporter").
- **Shipped code you extend (read it):**
  - `agents/reporter/domain/metrics.py` (85L) — `collect_portfolio_metrics` and
    `collect_signal_metrics` are the pattern to mirror; your new function lives in a **sibling
    module** `domain/trade_outcomes.py`, not appended here (keeps each module focused).
  - `agents/reporter/result.py` (144L) — `build_snapshot` calls the domain functions and merges
    their dicts into the snapshot; you add one more import + one more merge call here.
  - `agents/reporter/domain/lineage.py` (172L) — `RunLineage` already carries `positions` and
    `close_decisions`; both are passed to `collect_portfolio_metrics` today. Your function takes
    the same two arguments. **Do not add to lineage.py** (it is near the 150L warn band).
  - `contracts/reporter.py` — `RunSnapshot.portfolio_metrics: dict[str, float]`. The new keys
    land there; no field or version change. CONTRACT stays `0.1.0`, `owns_graph` untouched.
  - `agents/reporter/settings.py` (30L) — no new tunables this sprint (the metrics are pure
    computation with no policy-sensitive parameters).

### Why paper-trading pnl is deterministic

The paper broker in this system exits a position **at the trigger price**:

- **stop trigger** → exit at `opened_price_cents × (1 − stop_pct)` → `pnl_pct = −stop_pct`
- **target trigger** → exit at `opened_price_cents × (1 + target_pct)` → `pnl_pct = +target_pct`
- **time trigger** → exit at the current market price, which is stored on `PositionCheck` (a
  separate graph node linked via CHECKS), **not** on `CloseDecision` or `Position`. Reaching it
  requires additional traversal outside this sprint's scope.

**Design decision — time exits are excluded from profit-factor and expectancy** (decided; read):
Only stop-trigger (loss) and target-trigger (win) closes contribute. Time exits carry no reliable
implied pnl from the data already in scope; excluding them is conservative and keeps the
computation pure. Add a `closed_trades_with_pnl` counter so the dashboard can show whether the
metrics are meaningful. Document this exclusion in the module header.

### Pairing positions with close decisions

`CloseDecision.props["position_id"]` equals `Position.key`. Build a lookup dict once:

```python
by_position: dict[str, Node] = {
    cd.props["position_id"]: cd
    for cd in close_decisions
    if "position_id" in cd.props
}
```

Then iterate positions; skip any without a matching close decision (still open) or whose trigger
is `"time"`.

### Formulas

```
wins  = [pnl_pct for each trade whose trigger == "target"]
losses = [abs(pnl_pct) for each trade whose trigger == "stop"]

profit_factor     = sum(wins) / sum(losses)  if sum(losses) > 0  else 0.0
expectancy_pct    = mean(all pnl_pct over wins + losses)         else 0.0
closed_trades_with_pnl = len(wins) + len(losses)
```

`pnl_pct` is already signed (`+target_pct` / `−stop_pct`). The `expectancy_pct` is the mean over
**all** signed pnls (wins and losses combined), so it can be negative.

Zero-sentinel convention: both metrics return `0.0` when there are no stop/target closes (mirrors
`approval_rate → 0.0` when no decisions in `collect_portfolio_metrics`). The `closed_trades_with_pnl`
counter tells callers whether the value is meaningful.

## Part A — New domain module

New `agents/reporter/domain/trade_outcomes.py` — ≤ 120L:

```python
"""Reporter trade-outcome metrics (profit-factor and expectancy).

Agent: reporter
Role: compute profit-factor and expectancy from paired Position and CloseDecision nodes.
External I/O: none.

Note: time-triggered exits are excluded because their implied pnl requires the exit
price from PositionCheck (a separate graph node not in scope here); only stop- and
target-triggered closes contribute to these metrics.
"""
```

- `_implied_pnl_pct(position: Node, close_decision: Node) -> float | None`:
  - trigger `"stop"` → `-_pct(position, "stop_pct")`
  - trigger `"target"` → `+_pct(position, "target_pct")`
  - anything else → `None` (time exits, or missing trigger)
  - helper `_pct(node, prop) -> float`: read float from props, return 0.0 on missing/bad value.

- `collect_trade_outcomes(positions: tuple[Node, ...], close_decisions: tuple[Node, ...]) -> dict[str, float]`:
  - Build the lookup dict, iterate positions, call `_implied_pnl_pct`, collect signed pnls.
  - Compute and return `{"profit_factor": ..., "expectancy_pct": ..., "closed_trades_with_pnl": ...}`.
  - Never raises; all edge cases return 0.0 / 0.

## Part B — Wire into the snapshot

`agents/reporter/result.py`:

- Import `collect_trade_outcomes` from `agents.reporter.domain.trade_outcomes`.
- In `build_snapshot`, after computing `portfolio` from `collect_portfolio_metrics`, merge the
  outcomes in:

```python
outcomes = collect_trade_outcomes(lineage.positions, lineage.close_decisions)
portfolio = {**portfolio, **outcomes}
```

- In `degraded_snapshot`, merge a zero outcomes dict as well (so callers always see the same keys):

```python
outcomes = collect_trade_outcomes((), ())
portfolio = {**portfolio, **outcomes}
```

Both calls guarantee `portfolio_metrics` always contains `profit_factor`,
`expectancy_pct`, and `closed_trades_with_pnl` — no KeyError for callers.

## Part C — Tests

### C1. `agents/reporter/tests/test_trade_outcomes.py` — ≤ 130L

Pure `_implied_pnl_pct` / `collect_trade_outcomes` tests with hand-built `Node` fixtures:

- A stop close: `pnl_pct == -stop_pct`; a target close: `pnl_pct == +target_pct`.
- Time close → excluded (`implied_pnl_pct` returns `None`); does not contribute.
- No closes (all open) → `profit_factor == 0.0`, `expectancy_pct == 0.0`,
  `closed_trades_with_pnl == 0`.
- Only losses → `profit_factor == 0.0` (no wins), `expectancy_pct < 0.0`.
- Only wins → `profit_factor == 0.0` (no losses, denominator zero guard).
- Mixed: two wins (`target_pct = 0.10`), one loss (`stop_pct = 0.05`):
  - wins sum = 0.20, loss sum = 0.05 → profit_factor = 4.0
  - expectancy = (0.10 + 0.10 − 0.05) / 3
  - `closed_trades_with_pnl == 3`
- Missing or bad `stop_pct`/`target_pct` props → 0.0 from `_pct` helper; never raises.
- Missing `position_id` on close_decision → position skipped; never raises.

### C2. Integration — result.py snapshot

Extend the existing snapshot builder tests (in `test_reporter_agent.py` or the metrics test file)
with one new case: a lineage that includes one target-close and one stop-close position → confirm
`RunSnapshot.portfolio_metrics["profit_factor"]` and `["expectancy_pct"]` are non-zero and
match the hand-computed values. One additional case: degraded snapshot → all three new keys
present and equal to `0.0`.

### C3. Regression

Existing `collect_portfolio_metrics` tests are **unchanged** (the new function is a sibling, not a
replacement). Existing snapshot tests that assert on `portfolio_metrics` keys other than the three
new ones should continue to pass untouched. Confirm with `make ci`.

## Steps

1. Branch `sprint-41-reporter-trade-outcomes` off `main`.
2. **A** — write `domain/trade_outcomes.py` (+ C1 unit tests).
3. **B** — wire `collect_trade_outcomes` into `result.py` (+ C2 integration case).
4. `make ci` (ruff, format, mypy, import-linter, size/header guards, pytest floor 100.00).
5. **C3** — confirm no existing test needed re-pinning.
6. `wc -l agents/reporter/domain/*.py agents/reporter/result.py` — all < 200L.
7. Push; hand back.

## Acceptance criteria

- `collect_trade_outcomes` returns `profit_factor`, `expectancy_pct`, and
  `closed_trades_with_pnl` from paired position + close_decision nodes; time exits are excluded;
  the function never raises.
- `RunSnapshot.portfolio_metrics` always contains the three new keys (including in the degraded
  path); no KeyError possible.
- All pnl values are derived from `stop_pct`/`target_pct` props on Position nodes — no new graph
  traversal, no new contract fields.
- **No contract change** (reporter CONTRACT 0.1.0, `owns_graph` untouched); **no new dependency**.
- Existing `collect_portfolio_metrics` callers and pinned values are **unchanged** (the function
  is a separate sibling — only new keys are added to the merged dict, no existing key renamed or
  removed).
- `make ci` green at/above floor 100.00; import-linter kept; every touched/new module < 200L.

## Out of scope (P11 remaining — plan separately)

- **Time-exit pnl** — requires traversing PositionCheck nodes for `current_price_cents` at the
  moment of close; plan as a targeted follow-up if the metric is operationally important.
- **Scanner: beta + earnings** — independent P11 completion (sprint 42, plan after this ships).
- **PM sector-concentration cap** — needs a `sector` field on positions/recommendations; larger,
  has contract/provider plumbing (sprint 43+).
- Any change outside the reporter package.

## Handback report (paste into PR / reply)

- Confirm no contract change (reporter 0.1.0) and no new dependency.
- One worked example: positions and close decisions you used to manually verify `profit_factor`
  and `expectancy_pct` in C1.
- Final line counts: `trade_outcomes.py`, `result.py`, `metrics.py` (should be unchanged).
- New coverage % and floor; total test count; confirmation no existing test needed re-pinning.

The planning agent reviews, merges to `main`, and plans sprint 42 — scanner beta + earnings.
