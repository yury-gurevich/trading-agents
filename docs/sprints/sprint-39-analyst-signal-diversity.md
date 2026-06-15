<!-- Agent: planning | Role: sprint handover -->
# Sprint 39 — Analyst signal-diversity selection (surface the top, pillar-diverse signals)

**Status:** shipped · **Branch:** `sprint-39-analyst-signal-diversity` · **Build phase:** P11 · **Effort: S**

> Implemented directly by the planning agent on explicit request ("plan and execute"), not handed to a
> coding agent. Green at the full gate before merge.

## Goal

Port the reference **top-signal selection**: from a recommendation's per-signal sub-scores, surface a
small, **pillar-diverse** set of the most influential signals in the rationale. It is **explanatory** —
it does **not** change any score or confidence; it enriches `Recommendation.rationale.evidence_refs`.

## What shipped

- New pure module `agents/analyst/domain/signal_selection.py` (92L):
  - `Signal(name, pillar, score)` frozen value (0–100, 50 = neutral).
  - `technical_signals(metrics)` / `fundamental_signals(metrics)` — extract signals from the existing
    score-metrics dicts (technical via the `<name>_score` keys; fundamental via bare metric keys, minus
    `*_available` meta). No change to how scores are computed.
  - `select_top_signals(signals, weights, *, slack, max_signals)` — ranks by
    `|score − 50| · pillar_weight` (tie-break: raw distance from neutral), then walks the ranking
    preferring the top signal from a **not-yet-used pillar** whose contribution is within `slack` of the
    current best (so a strong-enough fresh-pillar signal is surfaced ahead of another from a pillar
    already shown). Capped at `max_signals`; an unweighted pillar contributes zero.
  - **Deviation from the reference (intentional):** no `"Data Limited"` padding to a hard minimum — v2
    already has explicit rejection paths, so we surface only real signals (up to the cap).
- Folded into `agents/analyst/domain/scoring.py`: `score_candidate` builds the signal list from the
  technical + fundamental sub-scores it already computes, selects, and stores names on
  `ScoreBreakdown.top_signals: tuple[str, ...]` (new field, default `()`).
- `agents/analyst/domain/recommend.py`: appends `analyst.signal.<name>` to the recommendation's
  `evidence_refs` — **additive**, so no existing test re-pinned (no test pinned the exact recommendation
  rationale; the one exact-match assertion is the separate `explain` capability).
- Two tunables on `AnalystSettings`: `signal_diversity_slack` (5.0) and `max_top_signals` (5).

## Verification

- New `agents/analyst/tests/test_signal_selection.py` (8 tests): extraction (score-key filtering,
  `*_available` drop), weighted ranking, the diversity lift within slack, the same-pillar fallback, the
  `max_signals` cap, empty input, and the unknown-pillar zero-weight path.
- Full gate green: **581 passed, 4 skipped, 100.00% coverage**; ruff/format/mypy/import-linter/module-
  size/headers all clean. No contract change (analyst 0.1.0); no new dependency; no existing value or
  rationale re-pinned. Every touched/new module < 200L.

## Notes / follow-ups

- When the **sentiment** pillar (S37) lands, add `"sentiment": settings.sentiment_weight` to the weights
  map in `score_candidate` so sentiment signals join the ranking; the selector already handles any pillar
  (unknown pillars just weight to zero until wired).
- The selected signals are surfaced in `evidence_refs` only; a richer rationale summary (naming the top
  signals in prose) is a later, optional cosmetic touch.
