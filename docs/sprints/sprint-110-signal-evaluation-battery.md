<!-- Agent: planning | Role: sprint handover -->
# Sprint 110 — Forecaster signal evaluation battery (qlib Phase Q1b)

**Phase:** qlib workflow adoption (Q1b — R001 addendum 2026-07-04)
**Branch:** `sprint-110-signal-evaluation-battery`
**Status:** code complete on branch (`1777352`, `make ci` 100 %) — **live check pending**; data
source re-scoped to Tiingo (DL-37: reference Postgres decommissioned, verified 2026-07-04)
**Effort:** M

---

## Codex kickoff (paste this)

> Execute **Sprint 110 — Forecaster signal evaluation battery** exactly as specified in this file
> (`docs/sprints/sprint-110-signal-evaluation-battery.md`). It is a complete, self-contained handover.
>
> - **Start:** from `main` (`git pull`), `git checkout -b sprint-110-signal-evaluation-battery`. Read the
>   files named under *Execution notes* first.
> - **Hard gate every commit:** `make ci` green — 9 steps, **100 % coverage**, modules **≤ 200 lines**,
>   coding-agent `Agent:`/`Role:` headers. Bump `pyproject.toml` **0.52.00 → 0.53.00** (feat → MINOR) +
>   `uv lock`.
> - **Core rule:** all battery math is **pure Python, fully unit-tested**; only the CLI's booster-load /
>   file-I/O shell is `# pragma: no cover` (the S59 pattern). **No `pyqlib` import anywhere** — the
>   metrics are standard math; `lightgbm` stays behind the existing lazy-import pattern.
> - **Out-of-sample honesty:** the evaluation CLI reports **test-split dates only** by default; evaluating
>   in-sample requires an explicit, loudly-labelled flag.
> - **Real-environment check** (sprint-close rule): run the CLI against the real `price_cache` CSV export
>   plus a trained booster; capture the per-horizon table; record the row in
>   `docs/laws/functionality-checks.md`. Do **not** commit the CSV, the booster artifact, or the report
>   JSON.
> - **Do NOT merge or push to `main`** — commit on the branch only, and stop for operator confirmation.
> - Read the *Session gotchas* before writing code. When done, append a **Closeout evidence** block (like
>   S108's) with the `make ci` result + the live-check evidence, and set **Status** to shipped.

---

## Goal

Turn the S59 return scorecard's single pooled IC into a qlib-style **evaluation battery**, so every
signal in the system carries a published battery of evidence ("they did their homework"):

1. **On-bus (`return_scorecard` capability):** add rank IC and quantile group-return metrics to the
   existing metrics dict — additive keys only, no contract change (`Scorecard.metrics` is an open
   `dict[str, float]`).
2. **Offline (`scripts/evaluate_return_model.py`):** a multi-horizon evaluation CLI that rebuilds
   predictions from the price CSV via the trained booster and reports, per horizon: pooled IC, rank IC,
   hit rate, per-date cross-sectional IC series (mean / std / information ratio), quantile mean returns
   plus top-bottom spread and monotonicity, and day-over-day rank-autocorrelation (signal stability). This
   is the IC-decay curve across horizons — and the measurement Phase Q1c's retrain trigger will consume.

Why each metric earns its place: rank IC is invariant to the monotone 0-1 squash on predictions
(pooled Pearson is not); the IC information ratio distinguishes a stable signal from one lucky month;
quantile spread + monotonicity checks the signal works **in the tails**, where trades actually happen;
rank-autocorrelation flags a signal that churns its ranking daily (turnover eats alpha).

## Scope

### In

**Part A — `agents/forecaster/domain/statistics.py` (extend, stays pure):**

- `spearman(xs, ys) -> float | None`: Pearson over average ranks (ties → average rank; implement a
  small `_average_ranks(xs) -> list[float]` helper). Same undefined-rules as `pearson`: `None` when
  n < 2 or either rank series is constant. Never raises.

**Part B — `agents/forecaster/domain/evaluation.py` (new module, pure battery math):**

Operates on `list[ReturnObservation]` (import from `return_scorecard`; no new dataclass).

- `DEFAULT_QUANTILES = 5` — module constant (evaluation bucket count; reporting shape, not a
  processing input, so a named constant + CLI flag, not a `tunable()`).
- `rank_ic(observations) -> float | None` — `spearman(predicted, forward_return)`.
- `quantile_metrics(observations, *, quantiles=DEFAULT_QUANTILES) -> dict[str, float]` — sort by
  `predicted` ascending, split into `quantiles` contiguous buckets (sizes differ by ≤ 1; the larger
  buckets take the tail). Emit `q1_mean_ret` (lowest predictions) … `q{Q}_mean_ret` (highest),
  `top_bottom_spread = q{Q} − q1`, and `monotonic_fraction` = fraction of adjacent bucket pairs with
  `mean_ret[i+1] ≥ mean_ret[i]`. **Return `{}` when `len(observations) < 2 × quantiles`** (too small
  to bucket honestly).
- `ic_series_metrics(by_period: dict[str, list[ReturnObservation]]) -> dict[str, float]` — per-period
  cross-sectional Pearson IC (skip periods where `pearson` is `None`); emit `ic_mean`, `ic_std`
  (population, reuse `std`), `ic_ir = ic_mean / ic_std` (omit `ic_ir` when `ic_std == 0`), and
  `ic_periods` (count used). `{}` when no period yields an IC.
- `rank_autocorrelation(prev: dict[str, float], curr: dict[str, float]) -> float | None` — inner-join
  two `{subject_ref: predicted}` maps on ref, `spearman` over the aligned pairs; `None` when the
  intersection < 2 or degenerate.

**Part C — `agents/forecaster/domain/return_scorecard.py` (extend `return_scorecard_metrics`):**

- Merge `rank_ic` (key `rank_ic`, omitted when `None`) and `quantile_metrics(...)` (at
  `DEFAULT_QUANTILES`) into the returned dict. **All existing keys and their semantics unchanged**
  (`complete_cases`, `ic`, `hit_rate`, `mean_up_pred`, `mean_down_pred`). Import the math from
  `evaluation.py` — keep this module comfortably under 200 lines.

**Part D — `scripts/evaluate_return_model.py` (composition root, CLI):**

- Inputs: `--input` price_cache CSV (same format + loader approach as
  `scripts/train_lgbm_return.py`: columns `date,ticker,close,volume`; factor the CSV loader so both
  scripts share it rather than copy-pasting — e.g. move `_load_csv` into a small
  `scripts/price_csv.py` helper with a module header), `--model models/lgbm-return-v1.txt`,
  `--horizons 1,5,10,20` (comma list, default exactly that), `--quantiles 5`,
  `--train-fraction 0.7`, `--out <report.json>`, `--include-in-sample` (off by default).
- Pipeline per horizon `h`: build label rows via `build_label_rows(forward_days=h, ...)` (S59
  defaults for `horizons`/windows); split with `split_rows(train_fraction)` and **evaluate the test
  side only** (unless `--include-in-sample`, which must print a `WARNING: in-sample` banner and set
  `"in_sample": true` in the report); predict each test row's features with the loaded booster
  (lazy `lightgbm` via the existing `LightGBMModel`/importlib pattern); form `ReturnObservation`s;
  compute pooled `ic`/`hit_rate` (reuse `return_scorecard_metrics` on the observation list), the
  quantile metrics, `ic_series_metrics` grouped by `as_of_date`, and mean `rank_autocorrelation`
  over consecutive dates (key `stability_mean`, plus `stability_pairs` count).
- Output: JSON report `{model, generated_at, train_fraction, in_sample, horizons: {h: {metrics...}}}`
  **and** a printed markdown table (rows = horizons, columns = the headline metrics: cases, ic,
  rank_ic, ic_ir, hit_rate, top_bottom_spread, monotonic_fraction, stability_mean). The offline CLI
  reads **no graph** — predictions are rebuilt from the CSV, exactly like training.
- Coverage: the pure helpers (arg parsing of horizon lists, report assembly, table rendering,
  grouping by date) are tested; only `main()`'s booster-load/file-I/O shell is `# pragma: no cover`
  (mirror `train_lgbm_return.py`'s footprint).

### Out

- **No contract changes** — `ReturnScorecardRequest`, `Scorecard`, and the boundary map are untouched.
- **No retrain trigger / no champion swap** — that is Phase Q1c (needs this battery first).
- **No sentiment-scorecard changes** — this battery targets the return model only.
- **No `pyqlib`**, no new dependencies, no new tunables.
- **No committed artifacts** — CSV export, booster file, and report JSON stay out of git.

## Deliverables

- `spearman` in `agents/forecaster/domain/statistics.py`; new `agents/forecaster/domain/evaluation.py`;
  extended `return_scorecard_metrics`; `scripts/evaluate_return_model.py` (+ shared CSV loader helper).
- Unit tests: `spearman` (ties, constant series, n < 2, perfect monotone → 1.0);
  `quantile_metrics` (uneven buckets, monotonic + non-monotonic orderings, the `< 2×quantiles`
  omission rule, spread sign); `ic_series_metrics` (multi-period, skipped-period, zero-std,
  empty); `rank_autocorrelation` (join on refs, disjoint refs → `None`); extended
  `return_scorecard_metrics` (new keys present on a big-enough sample, absent on a small one,
  **existing keys byte-identical to pre-sprint behavior**); CLI pure helpers. `make ci` green,
  100 % coverage, modules ≤ 200 lines.

## Functionality check (sprint-close rule)

Live, against real data — unit-green ≠ works:

> **Re-scope (2026-07-04, DL-37):** the reference Postgres is decommissioned (host unresolvable;
> zero PG servers across all enabled subscriptions), so the `price_cache` export below is replaced
> by a **Tiingo** export — Tiingo is the ADR-0006 primary OHLCV feed and its key is live in `.env`.

1. Export real daily bars from **Tiingo** with a **scratch script** (not committed) over the
   in-tree client (`agents/provider/tiingo.py`): **≥ 100 S&P-500 tickers × ≥ 3 years**, written in
   the trainer's CSV format (`date,ticker,close,volume`, date-ascending per ticker). Reuse the
   universe list the S&P-500 acceptance run used; pace requests to respect the free-tier rate
   limits (a partial universe is fine — cross-sectional metrics need breadth ≥ 100, not all 507).
2. Retrain the booster from that CSV:
   `uv run --extra forecaster python scripts/train_lgbm_return.py --input <scratch>/tiingo_bars.csv`
   — the artifact is now **Tiingo-sourced**; say so in the functionality-checks row.
3. `uv run --extra forecaster python scripts/evaluate_return_model.py --input price_cache.csv
   --model models/lgbm-return-v1.txt --horizons 1,5,10,20 --out <scratch>/eval-lgbm-return-v1.json`
4. Evidence: paste the printed per-horizon markdown table into the
   `docs/laws/functionality-checks.md` row; sanity-expect `complete_cases` in the thousands
   (≥ 100 tickers × the test window) and every horizon column populated. A weak IC is a **valid result**
   (the battery's job is honest measurement) — record it plainly; only a crash, an empty report, or
   a missing metric is a failure.
5. Tear down: delete the scratch CSV/JSON; confirm `git status` shows no data files staged. Record
   the row in `docs/laws/functionality-checks.md`.

## Dependencies

- S58/S59 in-tree pieces: `build_label_rows`, `split_rows`, `LightGBMModel` (lazy import),
  `ReturnObservation`, `pearson`/`std`. The `forecaster` optional extra already carries
  `lightgbm>=4` — no dependency edits.
- Reference Postgres reachable for the CSV export (functionality check only).

## Version bump

New capability (evaluation battery + CLI). **0.52.00 → 0.53.00** (feat → MINOR).

## Execution notes (for the coding agent — cold-start handover)

**Start.** From `main` (`git pull`): `git checkout -b sprint-110-signal-evaluation-battery`. Read
`agents/forecaster/domain/{statistics,return_scorecard,return_labels}.py`,
`agents/forecaster/{model_trainer,return_model}.py`, `scripts/train_lgbm_return.py`,
`agents/forecaster/tests/{test_forecaster_return_scorecard_math,test_statistics}.py`, and R001's
§"For Coding Agents" invariants (`docs/research/qlib-integration/qlib-integration.md`) — all 7 bind
verbatim.

**Gate.** `make ci` green — 9 steps, **100 % coverage**, modules ≤ 200 lines, coding-agent headers.
Bump `pyproject.toml` 0.52.00 → 0.53.00 + `uv lock` (stage `uv.lock` with the bump).

**Boundaries.** Everything new lives in `agents/forecaster/domain/` (pure) or `scripts/` (composition
root). No qlib import; no contract edits; no other agent touched; import-linter must stay green.

**Commit.** Branch-per-sprint; commit only your own files; conventional message ending with
`Co-Authored-By: …`. Do **not** merge/push to `main` without operator confirmation.

**Session gotchas:**

1. **Predictions are squashed to 0-1** (`ShadowPrediction.value`); the offline booster emits raw
   returns. Rank-based metrics are invariant either way, but be explicit about which scale each
   code path sees: the on-bus scorecard sees squashed values; the CLI sees raw booster output —
   both are fine for the battery, don't "unsquash".
2. **`build_return_observations` keys by `subject_ref` — last write wins across runs.** That is why
   the CLI must rebuild predictions from the CSV instead of reading `ShadowPrediction` nodes; do
   not "fix" the graph-side dedupe in this sprint.
3. **Quantile bucketing must be deterministic under ties** — sort by `(predicted, subject_ref)` so
   equal predictions split reproducibly.
4. **`pearson` returns `None` on constant series** — a single-date test fixture where all forward
   returns are equal will silently drop that period in `ic_series_metrics`; cover that case
   explicitly rather than being surprised by it.
5. **mypy `--strict` covers `agents/**` tests**; annotate; `if TYPE_CHECKING:` for annotation-only
   imports. Agent test files need the `Agent:`/`Role:` header; root `tests/` and `scripts/` headers
   per `scripts/check_module_header.py` (it checks `scripts/` too — give the CLI and the shared
   loader proper headers, `Agent: tooling`).
6. **Module size:** `statistics.py` is 72 lines and `return_scorecard.py` 76 — additions fit, but
   if either approaches 150 (CI warning), move math into `evaluation.py` rather than growing them.
7. **Known non-blocking `pip-audit` warning** may appear (`diskcache` CVE, Makefile-ignored) — not
   yours to fix.

## Notes

First sprint of the R001 workflow addendum (2026-07-04): Q1b of the revised sequencing
Q1b → Q1c (rolling retrain + IC-decay trigger) → Q3 (self-built walk-forward harness) → Q5 (governed
factor-mining loop). The battery is deliberately measurement-only — it changes no decision path,
gates nothing, and exists so that every later promotion/retrain decision has published evidence to
point at.
