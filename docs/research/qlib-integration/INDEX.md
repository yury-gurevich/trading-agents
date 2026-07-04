# R001 · Microsoft Qlib — integration vision

**Status:** 🚧 In progress · **Date:** 2026-06-19

Whether and how this project adopts Microsoft Qlib — across which agents and in what order.

- **[qlib-integration.md](qlib-integration.md)** — full integration vision. The §"For Coding
  Agents" invariants bind sprint work verbatim (S58, S59, S68, S110). The
  §"Addendum (2026-07-04)" is the workflow-level pass and holds the **revised phasing**.

**Answers:** Can this project benefit from qlib? Which agents, which components, in what order?
Which qlib *workflows* (not components) serve "did the homework / all evidence / self-improving"?

**Outcome:** Q1 complete (S58–S59: LightGBM shadow + IC scorecard) · Q2 complete (S68: Alpha158
pillar). Addendum 2026-07-04 re-sequenced the rest: **Q1b** signal evaluation battery (packaged —
[sprint-110](../../sprints/sprint-110-signal-evaluation-battery.md)) → **Q1c** rolling retrain +
IC-decay trigger → **Q3** researcher backtest evidence (re-scoped to a **self-built** walk-forward
harness; pyqlib still has no cp313 wheel) → **Q5** governed factor-mining loop (Moonshot #3);
Q4 unchanged behind its 60-day live-data prerequisite.
