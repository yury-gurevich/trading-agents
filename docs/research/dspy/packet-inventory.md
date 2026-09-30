# Everything computed about a trade, against what the deliberators receive

**Part of:** [R009 · DSPy](INDEX.md) · **Date:** 2026-09-30 · **Status:** inventory, measured; nothing
built.

> *"Whatever can be calculated about a trade should be given to deliberators. ALL OF IT. What we need
> is to determine if the agents understand fully what they are discussing. The instructions should
> be explicit."* (operator, 2026-09-30)

**Method.** The "in the packet" column comes from reading the packet builder:
`build_veto_context` in `agents/deliberator/context.py`, with `context_market.py`, `context_pm.py`
and `context_values.py`. It reads only the provider → scanner → analyst → PM lineage, plus the run's
`RegimeContext`. The "exists before the debate" column was measured on the live graph (read-only),
by comparing each node's `created_at` with the same day's `DeliberationRun`. Field lists come from
the contracts and from `orchestration/packs/trading_graph_vocabulary.json`.

## The inventory

| Computed fact about the trade | Where it lives | Exists before the debate | In the packet today |
| --- | --- | --- | --- |
| Analyst scores (confidence, technical, fundamental, sentiment), **47 quant metrics**, stop/target basis, rationale | `AnalystRun.recommendation_set` | yes | ✅ yes; metric meanings not explained |
| Analyst rejections for this ticker | same | yes | ✅ |
| Scanner filter trace, candidate metrics, verdict features | `ScanRun.candidate_set` | yes | ✅; units unexplained |
| Latest daily bar (OHLCV) | `MarketData.bars` | yes | ✅ latest bar only |
| Full price history | `MarketData.bars` | yes | ❌ only the indicators derived from it |
| Benchmark series | `MarketData.benchmark` | yes | ❌ |
| Fundamentals | `MarketData.fundamentals` | yes | ✅ under vendor key names, unexplained |
| Sentiment: lexicon score, article count, positive and negative words | `SentimentReading` (1,589 nodes, one scorer: `lexicon`), analyst `quant_metrics`, `MarketData.sentiment` | yes | ✅ |
| News | `MarketData.news` | yes | ✅ headlines only |
| Sector, next earnings date | `MarketData` | yes | ✅ |
| Earnings horizon in days | `MarketData.earnings_horizon_days` | yes | ❌ |
| Data quality (stale and anomalous tickers) | `MarketData.quality` | yes | ✅ |
| Regime label, VIX, base thresholds | `RegimeContext` | yes | ✅ |
| VIX status and as-of date (is the VIX stale?) | `RegimeContext.vix_status`, `vix_as_of` | yes | ❌ |
| PM order: quantity, estimated price, stop, target, rationale | `OrderIntent` | yes | ✅ |
| ATR at decision time, and which position an exit closes | `OrderIntent.decision_atr_pct`, `position_ref` | yes | ❌ |
| 8 PM gate outcomes with value, threshold and inputs | `OrderIntent.gate_report` | yes | ✅ |
| The other orders in the same batch, approved and rejected | `OrderIntentSet` | yes | ❌ counts only; the packet states *"sibling orders … unavailable"* |
| Current holdings, cash and equity | `BrokerPositionSnapshot`, `Position` | yes | ❌ partly, inside gate details (`held_issuers`, `deployed_portfolio_usd`); the packet states *"holdings, open positions … unavailable"* |
| **Barrier forecast:** probability the stop is hit first, the target first, or neither; horizon; simulated paths; GARCH fit | `BarrierForecast` | **yes: 10 of the 12 orders debated on 2026-09-28**, written at 22:42, debated at 23:00 | ❌ **never** |
| The forecaster's track record (Brier score, outcomes) | `BarrierSettlement` | yes | ❌ |
| Past trades in this ticker and their realised P&L | `Fill` | yes, for tickers traded before | ❌ |

**What the gap looks like.** For DE on 2026-09-28, the forecaster put the chance of hitting the stop
first at **0.373**, above the chance of hitting the target first (**0.325**). No deliberator was
told, and the order was approved and submitted.

## What blocks "all of it"

Most rows are simple omissions in the renderer: nothing prevents adding them. One row is blocked by a
law:

- 🚨 **Barrier forecasts and their track record meet `FORE-NEV-02`:** *"Never gates, vetoes, or
  blocks a recommendation, sizing, or exit."* The deliberation veto is **`binding`** on every recent
  run (`ExecutionRun.deliberation_posture`, measured). A forecast that informs a binding veto
  therefore takes part in gating. Adding it needs the operator's decision and a forecaster law cycle,
  not only a renderer change.
  **Decided 2026-09-30 (DL-250 amendment 4): held until the live `barrier_scorecard` reports
  `skill_lo > 0`** (work-queue 99). No live claim was settled when this was decided. Every other row goes in
  now (work-queue 98). `FORE-NEV-01` (forecasts stay `shadow=True`) is not affected: showing a
  forecast as evidence does not make it a signal.

**One design constraint follows from DSPy** ([concepts.md](concepts.md)). Each fact must arrive
*with its meaning*. Otherwise more data means more `source-owned-units-scope-unknown` blocks. The
explicit instructions belong in the generated glossary, which an optimiser can never rewrite (see
[three-roles-goal.md](three-roles-goal.md) for where it sits in the prompt). The instructions must
also say how to *use* each fact: for example, that `rsi_score` is contrarian, and what a
`p_stop_first` of 0.37 means against the order's own stop and target.

**Size.** Packets are already 3,837–9,860 characters. The full price history and benchmark series
are the only rows that could inflate them much. Their indicators are already present, so they are
the last candidates, not the first.
