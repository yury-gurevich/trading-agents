# R001 · Microsoft Qlib — integration vision

**Status:** 🚧 In progress · **Date:** 2026-06-19

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
rolling retrain + IC-decay trigger with dry-run default and scratch-proven apply). Remaining addendum
sequencing: **Q3** researcher backtest evidence, re-scoped **self-built** walk-forward harness
(**[sprint-112](../../sprints/sprint-112-researcher-backtest-evidence.md) packaged**, execute after
S111) → **Q5** governed factor-mining loop (Moonshot #3); Q4 unchanged behind its 60-day live-data
prerequisite.
