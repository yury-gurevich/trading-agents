# R001 · Microsoft Qlib — integration vision

**Status:** ✅ Adopted · **Date:** 2026-06-19

Whether and how this project adopts Microsoft Qlib — across which agents and in what order.

- **[qlib-integration.md](qlib-integration.md)** — full integration vision. The §"For Coding
  Agents" invariants bind sprint work verbatim (S58, S59, S68, S110). The
  §"Addendum (2026-07-04)" is the workflow-level pass and holds the **revised phasing**.

**Answers:** Can this project benefit from qlib? Which agents, which components, in what order?
Which qlib *workflows* (not components) serve "did the homework / all evidence / self-improving"?

**Outcome:** Q1 complete (S58–S59: LightGBM shadow + IC scorecard) · Q2 complete (S68: Alpha158
pillar) · **Q1b complete** ([sprint-110](../../sprints/sprint-110-signal-evaluation-battery.md),
shipped 0.53.00 2026-07-04 with a live Tiingo check — baseline best at h=20: IC 0.017, rank-IC
0.023, IC-IR 0.27) · **Q1c complete** ([sprint-111](../../sprints/sprint-111-rolling-retrain.md),
rolling retrain + IC-decay trigger with dry-run default and scratch-proven apply). **Q3 complete**
([sprint-112](../../sprints/sprint-112-researcher-backtest-evidence.md), shipped 0.55.00
2026-07-05 — self-built no-lookahead walk-forward harness + `BacktestEvidence` contract field +
bounded signal-catalogue CLI, live Tiingo check). **Q5 part A complete**
([sprint-113](../../sprints/sprint-113-governed-factor-proposal.md), shipped 0.57.00 2026-07-06 —
bounded factor catalogue, LLM proposes in-catalogue only (enum-guarded, fail-open), S112 harness
scores, `FactorProposal` 0.3.0; live check: GPT-5.5 picked `momentum lookback=60`, off-menu failed
open). **Q5 part B complete** ([sprint-115](../../sprints/sprint-115-factor-shadow-signal.md),
shipped 0.58.00 2026-07-07 — `forecast_factor` shadow emitter, parity-pinned, off-by-default; live
Aura check). **The Q5 governed factor-mining loop is CLOSED — every planned qlib workflow phase is
shipped except Q4**, which stays parked behind its 60-day live-data prerequisite.
