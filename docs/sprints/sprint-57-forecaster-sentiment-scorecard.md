# Sprint 57 — Forecaster: sentiment scorecard harness

**Phase:** P12 (sentiment champion–challenger) — the comparison machinery.
**Status:** shipped (implemented directly — no coding agent this cycle).
**Version:** forecaster CONTRACT `0.1.0 → 0.2.0`; project `feat` `0.5.0 → 0.6.0`.

## Goal

Build the champion–challenger **scorecard harness** (ADR-0002 §4): quantitatively
compare the three sentiment scorers — lexicon (champion), provider, FinBERT —
against forward returns, so a keep/drop/distill decision on the advisory
challengers rides on evidence. Data-runway-gated (live news must accrue before a
real verdict), so the **machinery** is built and tested against fixtures now.

## What shipped

New forecaster capability **`sentiment_scorecard`**.

- **Pure stats domain** (deterministic, no numpy):
  - `agents/forecaster/domain/statistics.py` — `pearson` (None when < 2 points or
    a constant series), population `std`, and `ols2` (closed-form 2-regressor OLS
    on centred series; None when < 3 points or the regressors are collinear).
  - `agents/forecaster/domain/scorecard.py` — `Observation` + `comparison_metrics`:
    `complete_cases`, pairwise `corr_*`, each scorer's `ic_*` (IC on forward
    returns), the OLS of FinBERT on provider+lexicon (`finbert_alpha`,
    `finbert_beta_provider`, `finbert_beta_lexicon`, `finbert_residual_std`), and
    **`incremental_ic_finbert`** = the IC of FinBERT's residual after regressing
    out the other two (its marginal predictive value). Each metric is **omitted
    when undefined**, so a present key is always meaningful.
- **Alignment** — `agents/forecaster/comparison.py` reads `SentimentReading`
  (analyst-owned: lexicon + provider) and `ShadowPrediction` (forecaster-owned:
  FinBERT) from the graph and **inner-joins** complete cases by
  `{analyst_run_id}:{ticker}`.
- **Injected returns** — forward returns are never a runtime dependency; the
  request (`SentimentScorecardRequest`) carries them, so the offline harness
  supplies realized returns for the observations it wants scored.

## Boundaries kept

- **Advisory only** — the handler emits the existing `Scorecard` with
  `promotion_eligible=False`; it never gates. Promotion stays the curator's P10
  predictor-registry gate.
- **Single-writer intact** — the forecaster only *reads* the analyst's
  `SentimentReading` label; `owns_graph` is unchanged. The `Scorecard.metrics`
  dict is free-form, so the response is unchanged — only a new inbound payload +
  capability bump the contract.

## Tests

- `test_statistics.py` — Pearson/OLS/std known values + the undefined (None) edges.
- `test_scorecard_math.py` — empty, single-case, collinear+constant (omitted
  metrics + omitted regression), constant-returns (omitted ICs), and a full case
  (regression + incremental IC present).
- `test_sentiment_scorecard.py` — graph alignment of complete cases, skipping
  incomplete refs and other models, the empty-returns case, and never-promotes.

756 tests (was 739; +17), coverage floor 100.00; every module < 200 lines.

## Follow-on

P12 is now **code-complete**. The only remaining work is **operational**: accrue
real headlines live (the S36 feed scored forward), then run `sentiment_scorecard`
against `price_cache` forward returns to produce the actual verdict and decide
provider/FinBERT promotion via the P10 gate. Per the agreed order, **P14
(inter-agent comms re-architecture) is next.**
