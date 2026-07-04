<!-- Agent: planning | Role: sprint handover -->
# Sprint 111 — Rolling retrain + IC-decay trigger (qlib Phase Q1c)

**Phase:** qlib workflow adoption (Q1c — R001 addendum 2026-07-04)
**Branch:** `sprint-111-rolling-retrain`
**Status:** packaged (handover ready)
**Effort:** M

---

## Codex kickoff (paste this)

> Execute **Sprint 111 — Rolling retrain + IC-decay trigger** exactly as specified in this file
> (`docs/sprints/sprint-111-rolling-retrain.md`). It is a complete, self-contained handover.
>
> - **Start:** from `main` (`git pull`), `git checkout -b sprint-111-rolling-retrain`. Read the files
>   named under *Execution notes* first.
> - **Hard gate every commit:** `make ci` green — 9 steps, **100 % coverage**, modules **≤ 200 lines**,
>   coding-agent `Agent:`/`Role:` headers. Bump `pyproject.toml` **0.53.00 → 0.54.00** (feat → MINOR) +
>   `uv lock`.
> - **Core rules:** all decision math (decay trigger, champion-vs-challenger verdict) is **pure,
>   deterministic, fully unit-tested** in `agents/forecaster/domain/`. The swap **never happens without
>   `--apply`** (default dry-run — the S108 pattern; `--apply` *is* the operator approval). The incumbent
>   artifact is **archived, never deleted**. No `pyqlib` import anywhere.
> - **Tiingo preflight is mandatory:** read `docs/laws/tiingo-usage-limits.md` before any live Tiingo
>   call, pace requests, and **reuse the S110 ticker list** (500-unique-symbols/month budget is shared).
> - **Real-environment check** (sprint-close rule): fresh Tiingo export via the new committed exporter →
>   full pipeline dry-run with `--force` → `--apply` proven against a **scratch copy** of the model tree.
>   Record the row in `docs/laws/functionality-checks.md`. Do **not** commit bars CSVs, boosters, or
>   report JSONs.
> - **Do NOT merge or push to `main`** — commit on the branch only, and stop for operator confirmation.
> - Read the *Session gotchas* before writing code. When done, append a **Closeout evidence** block (like
>   S110's) with the `make ci` result + the live-check evidence, and set **Status** to shipped.

---

## Goal

Turn the S110 battery from a snapshot into a **self-improvement loop**. A train-once model silently
decays as the market moves; qlib's online-serving workflow retrains on a rolling window and swaps the
champion only when a challenger beats it on evidence. This sprint builds the operator-run version of
that loop (the dispatcher cron, S103, will schedule it later):

1. **Measure decay:** evaluate the incumbent booster on the trailing `retrain_window_days` of data
   and compare against its reference (held-out history) battery — a deterministic
   `should_retrain` verdict with a reason.
2. **Retrain + compare:** when triggered (or `--force`), train a challenger on the rolling history and
   battery **both models on the identical recent window** — a side-by-side table plus a deterministic
   `compare_models` verdict.
3. **Swap on evidence, with the operator in the loop:** `--apply` archives the incumbent (datestamped,
   never deleted) and installs the challenger at `ForecasterSettings.return_model_path`. Dry-run is the
   default; the printed recommendation is the handoff to the human.

S110's baseline (best at h=20: IC 0.017, rank-IC 0.023, IC-IR 0.27 — see the S110 row in
`docs/laws/functionality-checks.md`) is the first reference this loop measures against.

## Scope

### In

**Part A — `scripts/export_tiingo_bars.py` (committed exporter — formalizes S110's scratch script):**

- Exports daily bars from Tiingo via the in-tree client (`agents/provider/tiingo.py`) into the trainer
  CSV format (`date,ticker,close,volume`, date-ascending per ticker).
- Flags: `--tickers <file>` (one symbol per line — the S110 list), `--years` (default 4), `--out`,
  `--pace-seconds` (default sized from `docs/laws/tiingo-usage-limits.md`: 50 requests/hour → ≥ 72 s
  between calls; make the default honor that).
- **Resumable:** tickers already complete in the output CSV are skipped on re-run (the free-tier hour
  cap makes multi-session exports normal).
- Module header declares the External I/O; the mandatory-preflight note (like `tiingo.py`'s) points at
  `docs/laws/tiingo-usage-limits.md`.

**Part B — `agents/forecaster/domain/retrain_policy.py` (new module, pure decision math):**

- `RetrainDecision` (frozen): `retrain: bool`, `reason: str`, `recent: float | None`,
  `reference: float | None`.
- `should_retrain(recent: dict[str, float], reference: dict[str, float], *, metric_key: str = "ic_ir",
  trigger_fraction: float, min_cases: float) -> RetrainDecision`. Rules (each its own tested branch):
  - recent `complete_cases` < `min_cases` → `retrain=False`, reason `"insufficient recent cases"`
    (never churn on thin evidence);
  - `metric_key` missing from **either** map → `retrain=False`, reason `"metric undefined"` (fail-safe:
    an undefined IC is not evidence of decay);
  - reference value ≤ 0 → `retrain=True`, reason `"reference non-positive"` (the incumbent never
    demonstrated signal; retraining is advisable, and harmless — the swap gate still applies);
  - otherwise → `retrain = recent_value < trigger_fraction × reference_value`, reason states the
    comparison with both numbers.
- `CompareVerdict` (frozen): `swap: bool`, `reason: str`, `primary_delta: float | None`,
  `secondary_delta: float | None`.
- `compare_models(incumbent: dict[str, float], challenger: dict[str, float], *,
  primary: str = "rank_ic", secondary: str = "ic_ir") -> CompareVerdict`:
  - challenger must be **≥ incumbent on BOTH** primary and secondary to earn `swap=True`;
  - a metric missing on the challenger side → `swap=False` (fail-safe);
  - missing on the incumbent side but present ≥ some value on the challenger → `swap=True`, reason
    `"incumbent metric undefined"`.

**Part C — `agents/forecaster/settings.py` (four new tunables, `FORECASTER_`-prefixed):**

- `retrain_window_days = tunable(60, why="Trailing distinct-date evaluation window for the rolling
  IC-decay check.", ge=20, le=252, unit="trading days")`
- `retrain_trigger_fraction = tunable(0.5, why="Fraction of the reference metric below which a retrain
  is recommended.", gt=0.0, le=1.0)`
- `retrain_horizon_days = tunable(20, why="Forward-return horizon the decay trigger and champion
  comparison score at — S110 baseline is strongest at h=20 (IC-IR 0.27).", ge=1, le=60, unit="days")`
- `retrain_min_cases = tunable(500, why="Minimum aligned recent-window observations before a decay
  verdict is meaningful.", ge=50)`

**Part D — `scripts/retrain_return_model.py` (pipeline CLI, composition root):**

- Flags: `--input` (bars CSV), `--model` (default `ForecasterSettings().return_model_path`),
  `--window-days` / `--trigger-fraction` / `--horizon` / `--min-cases` (defaults from
  `ForecasterSettings()`), `--force` (retrain regardless of the trigger), `--apply` (perform the swap;
  **default is dry-run**), `--out` (report JSON).
- Pipeline (per the configured horizon only — this is the decay loop, not the full battery):
  1. Build label rows (`build_label_rows`, S110 feature constants). Partition by **distinct
     `as_of_date`**: *recent* = rows in the last `window_days` dates; *history* = everything before.
  2. **Reference metrics:** incumbent battery over the held-out test split of *history*
     (`split_rows(history, train_fraction=0.7)` → test side), reusing
     `scripts/evaluate_return_model.py` helpers (`evaluate_label_rows` etc. — import, don't duplicate).
  3. **Recent metrics:** incumbent battery over the *recent* rows (pure OOS by time).
  4. `should_retrain(recent, reference, ...)` → print the decision + reason.
  5. If `retrain` or `--force`: train the challenger on *history* rows via `train_and_save`
     (`train_fraction=0.7`) to `models/candidates/lgbm-return-<YYYYMMDD>.txt`; battery the challenger
     on the **same recent rows**; print the incumbent-vs-challenger side-by-side markdown table
     (reuse/extend `render_markdown_table`).
  6. `compare_models(...)` → verdict printed with reason.
  7. `--apply` **and** `verdict.swap`: move the incumbent to
     `models/archive/lgbm-return-<UTC-stamp>.txt` (create dirs; **never delete**), copy the challenger
     to the active `--model` path, print `PROMOTED`. Any other combination prints `KEPT` + why.
- Report JSON: `{model, generated_at, config, decision, verdict, reference, recent_incumbent,
  recent_challenger?}`. The swap/archive file operations live in a pure, unit-testable helper
  (`plan_swap(...) -> list[(src, dst)]` + a tiny executor) so coverage holds without touching real
  artifacts; only `main()`'s shell is `# pragma: no cover`.

### Out

- **No scheduling** — S103 (dispatcher cron) will invoke this CLI later; building any scheduler here
  is out of scope.
- **No auto-swap** — a swap without `--apply` must be impossible by construction.
- **No graph/`model_id` versioning** — the artifact under `return_model_path` changes; the graph
  `model_id` stays `lgbm-return-v1` (family id). Provenance of *which* booster made a prediction is a
  known gap — note it in the closeout as a design follow-up, do not solve it here.
- **No forecaster runtime changes** beyond the Part C settings; no contract changes; no sentiment-side
  work.
- **No committed data** — bars CSVs, boosters (candidates/archive included), and report JSONs stay out
  of git (`models/` is already ignored beyond its README).

## Deliverables

- `scripts/export_tiingo_bars.py` (paced, resumable) · `agents/forecaster/domain/retrain_policy.py` ·
  four `ForecasterSettings` tunables · `scripts/retrain_return_model.py` (+ any small shared-helper
  extraction from `evaluate_return_model.py`, kept import-compatible).
- Unit tests: every `should_retrain` branch (thin cases / missing metric / non-positive reference /
  decayed / healthy, with exact reasons); every `compare_models` branch (both-better, primary-only,
  secondary-only, missing-on-challenger, missing-on-incumbent); date-window partition math (exact
  boundary, fewer dates than window); swap planning (paths, archive naming, no-delete invariant);
  exporter resume logic + pacing arithmetic (pure parts); settings defaults/bounds. `make ci` green,
  100 % coverage, modules ≤ 200 lines.

## Functionality check (sprint-close rule)

Live, against real data — unit-green ≠ works. **Preflight `docs/laws/tiingo-usage-limits.md` first;
reuse the S110 100-ticker list** (unique-symbol budget is monthly and shared).

1. **Fresh export via the NEW committed exporter** (not a scratch script): the S110 ticker list,
   `--years 4`, paced; prove resumability by interrupting once and re-running.
2. **Pipeline dry-run with `--force`** against the real export + a freshly trained incumbent (retrain
   via `scripts/train_lgbm_return.py` if no local artifact): capture the decay decision + reason and
   the incumbent-vs-challenger side-by-side table. Either verdict is a **valid result** — the loop's
   job is honest measurement; only a crash or a missing verdict is a failure.
3. **Swap mechanics on a scratch copy:** point `--model` at a copied artifact in a scratch dir, run
   with `--apply` (if the verdict is `swap=False`, use a deliberately weakened incumbent copy so the
   swap path executes): verify the incumbent landed in `archive/` (original bytes intact) and the
   challenger became the active file. The real local artifact is never touched by the check.
4. Evidence: paste the decision line, the side-by-side table, and the swap proof into the
   `docs/laws/functionality-checks.md` row (state Tiingo-sourced, DL-37).
5. Teardown: delete scratch CSV/JSONs/scratch model tree; `git status` shows no data files.

## Dependencies

- S110 in-tree pieces: `evaluation.py`, `evaluate_return_model.py` helpers, `price_csv.py`,
  `train_lgbm_return.py`, the LightGBM NumPy fix, `docs/laws/tiingo-usage-limits.md`. The `forecaster`
  extra (`lightgbm>=4`) — no dependency edits.
- Live Tiingo credential in `.env` (S108-verified).

## Version bump

New capability (retrain loop + exporter). **0.53.00 → 0.54.00** (feat → MINOR).

## Execution notes (for the coding agent — cold-start handover)

**Start.** From `main` (`git pull`): `git checkout -b sprint-111-rolling-retrain`. Read
`scripts/{evaluate_return_model,train_lgbm_return,price_csv}.py`,
`agents/forecaster/domain/{evaluation,return_scorecard,return_labels}.py`,
`agents/forecaster/{model_trainer,lightgbm_model,settings}.py`, `agents/provider/tiingo.py`,
`docs/laws/tiingo-usage-limits.md`, and the S110 rows in `docs/laws/functionality-checks.md` +
S110's Closeout. R001 §"For Coding Agents" invariants bind verbatim.

**Gate.** `make ci` green — 9 steps, **100 % coverage**, modules ≤ 200 lines, coding-agent headers.
Bump 0.53.00 → 0.54.00 + `uv lock` (stage `uv.lock`).

**Boundaries.** Decision math in `agents/forecaster/domain/` (pure); CLIs in `scripts/` (may import
agents); no qlib; no contract edits; import-linter stays green.

**Commit.** Branch-per-sprint; commit only your own files; conventional message ending with
`Co-Authored-By: …`. Do **not** merge/push to `main` without operator confirmation.

**Session gotchas (carried from S110):**

1. **LightGBM wants NumPy input** — already fixed in `lightgbm_model.py`; don't regress it, and reuse
   `LightGBMModel` rather than calling the booster directly.
2. **`return_scorecard_metrics` now takes `neutral_prediction` + `quantiles` kwargs** (S110 signature)
   — the offline path uses `neutral_prediction=0.0` (raw booster output), the on-bus path 0.5.
3. **Tiingo free tier:** 50 requests/hour is the binding constraint — a 100-ticker export spans ≥ 2
   hours; that is *why* the exporter must be resumable. 500 unique symbols/month is a shared budget:
   **same ticker list as S110, always.**
4. **`split_rows` sorts by `as_of_date` string** — dates are ISO, so lexicographic = chronological;
   keep the recent/history partition on distinct dates, not row counts (tickers have unequal history).
5. **`models/` is gitignored** beyond README — `candidates/` and `archive/` subdirs need no gitignore
   edits, but verify nothing under `models/` ever shows in `git status` during the check.
6. **mypy `--strict` covers `agents/**` tests**; annotate; `Agent:`/`Role:` headers on agent test
   files and on both new scripts (`Agent: tooling`).
7. **detect-secrets** false-positives near `key`/`token` fixture strings — neutral names or
   `# pragma: allowlist secret`.
8. **Fail-safe posture throughout:** undefined metrics never trigger a retrain, a missing challenger
   metric never earns a swap, and nothing is ever deleted — mirror DL-36's "test before you trust,
   one shot, human decides."

## Notes

Q1c of the R001 addendum sequencing (Q1b ✅ S110 → **Q1c** → Q3 self-built walk-forward harness → Q5
governed factor mining). This sprint makes "self-improving" mechanically true for the first model:
decay is measured (not assumed), retraining is triggered by evidence, and promotion requires the
challenger to beat the incumbent on the same window — with the operator holding the `--apply` pen.
The same policy module is deliberately generic (metric maps in, verdict out) so later models
(FinBERT, Alpha158 weights, Q5 candidate factors) can reuse it unchanged.

## Closeout evidence

*(appended by the coding agent at completion)*
