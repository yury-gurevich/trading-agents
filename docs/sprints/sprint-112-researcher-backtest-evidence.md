<!-- Agent: planning | Role: sprint handover -->
# Sprint 112 — Researcher backtest evidence: self-built walk-forward harness (qlib Phase Q3)

**Phase:** qlib workflow adoption (Q3 — R001 addendum 2026-07-04, re-scoped self-built)
**Branch:** `sprint-112-researcher-backtest-evidence`
**Status:** packaged (handover ready) — **UNBLOCKED**: S111 is merged (`45f6c34`); the committed
Tiingo exporter is on `main`
**Effort:** M

---

## Codex kickoff (paste this)

> Execute **Sprint 112 — Researcher backtest evidence** exactly as specified in this file
> (`docs/sprints/sprint-112-researcher-backtest-evidence.md`). It is a complete, self-contained
> handover.
>
> - **Start:** from `main` (`git pull`; S111 is merged — verify `scripts/export_tiingo_bars.py`
>   exists), `git checkout -b sprint-112-researcher-backtest-evidence` (delete any stale local branch
>   of that name first). Read the files named under *Execution notes* first.
> - **Hard gate every commit:** `make ci` green — 9 steps, **100 % coverage**, modules **≤ 200 lines**,
>   coding-agent `Agent:`/`Role:` headers. Bump `pyproject.toml` **0.54.01 → 0.55.00** (feat → MINOR
>   zeroes the patch) + `uv lock`.
> - **Core rules:** the walk-forward harness is **pure, deterministic, no-lookahead by construction**
>   (fills at the NEXT close after a score date; slippage charged on turnover) and lives in
>   `agents/researcher/domain/` — **no qlib, no pandas/numpy dependency in the domain module, no
>   imports from any other agent** (duplicate the two tiny stat helpers; islands beat DRY across
>   agents). Evidence generation runs **only** in the composition root (`scripts/`) — the researcher's
>   `external_io=()` law is untouched.
> - **Contract change is additive-optional only:** `BacktestEvidence` + an optional `backtest` field on
>   `ParameterChangeProposal`, contract version 0.1.0 → 0.2.0; no required-field changes, no consumer
>   breaks. Update whatever boundary/contract tests assert the researcher's shape.
> - **Fail-open on evidence:** an unsupported parameter means "no evidence generated", never a blocked
>   proposal — evidence is additive, its absence is not an error.
> - **Real-environment check** (sprint-close rule): real Tiingo bars (S110 ticker list via the S111
>   exporter; preflight `docs/laws/tiingo-usage-limits.md`) → incumbent-vs-proposed side-by-side run →
>   `BacktestEvidence.model_validate` round-trip proven. Record the row in
>   `docs/laws/functionality-checks.md`. No data files committed.
> - **Do NOT merge or push to `main`** — commit on the branch only, and stop for operator confirmation.
> - Read the *Session gotchas* before writing code. When done, append a **Closeout evidence** block
>   (like S110's) with the `make ci` result + the live-check evidence, and set **Status** to shipped.

---

## Goal

Give every researcher parameter proposal a **prospective** evidence dimension: "this change, applied
to historical data, would have produced these metrics" — alongside the retrospective provenance-graph
evidence the researcher already mines. This is the "decisions based on ALL available evidence" claim
made concrete for the review queue, and the harness is the **prerequisite for Q5** (governed factor
mining: candidate factors get scored by this same simulator before a human ever sees them).

Re-scope context (R001 addendum + DL-37): qlib's own backtest engine is unavailable on Python 3.13
and vendoring was ruled out; this is the **thin self-built walk-forward simulator** — deliberately
small, deterministic, and fully owned.

## Scope

### In

**Part A — contract (`contracts/researcher.py`, additive):**

- `BacktestEvidence(_Frozen)`: `sharpe: float` (annualized, √252), `ic_mean: float`,
  `max_drawdown: float`, `turnover: float` (mean per rebalance), `n_days: int`,
  `window_start: str`, `window_end: str` (ISO dates), `holdout_sharpe: float | None`,
  `holdout_ic_mean: float | None`, `slippage_bps: float`, `engine: str = "walkforward-v1"`.
- `ParameterChangeProposal` gains `backtest: BacktestEvidence | None = None`.
- Contract `version` 0.1.0 → 0.2.0. Update the researcher boundary/contract tests accordingly.

**Part B — harness (`agents/researcher/domain/backtest.py`, pure — the heart of the sprint):**

- Inputs: `scores: dict[str, dict[str, float]]` (as-of date → ticker → score),
  `closes: dict[str, list[tuple[str, float]]]` (ticker → date-ascending (date, close)), and keyword
  params `top_k`, `slippage_bps`, `holdout_fraction`.
- **Simulation semantics (no lookahead by construction):** iterate score dates in order; at each
  score date `t`, the portfolio = top-`k` tickers by score, equal weight; the position is **entered
  at the next available close after `t`** and held to the next rebalance's fill; per-rebalance
  return = mean of member returns between consecutive fills; slippage = `slippage_bps × turnover`
  deducted, where turnover = fraction of the portfolio replaced vs the previous holding (1.0 on the
  first). A ticker missing a fill price drops out of that leg (no fabricated fills).
- Outputs: `BacktestResult` (frozen dataclass) carrying the per-rebalance return series + metrics:
  annualized `sharpe`, `max_drawdown` (on the compounded curve), mean `turnover`, `ic_mean`
  (per-date cross-sectional Pearson of score vs realized next-leg return, averaged; skip undefined
  dates), `n_days`, `window_start/end`, and the same metrics recomputed on the **final
  `holdout_fraction` of rebalance dates** (`holdout_*` — the OOS consistency view; the tunable's
  floor enforces ≥ 30 %).
- Tiny private stat helpers (`_pearson`, `_std`) local to the module — deliberate duplication of
  ~20 lines rather than a cross-agent import; comment says so.
- `to_evidence(result, *, slippage_bps) -> BacktestEvidence` — the one place the domain touches the
  contract type (agents may import contracts).

**Part C — settings (`agents/researcher/settings.py`, three tunables):**

- `backtest_top_k = tunable(20, why="Portfolio breadth for walk-forward proposal evidence; equal-
  weight top-K by score.", ge=5, le=100)`
- `backtest_slippage_bps = tunable(10.0, why="Per-unit-turnover cost charged in the walk-forward
  simulator; keeps evidence honest about churn.", ge=0.0, le=100.0, unit="bps")`
- `backtest_holdout_fraction = tunable(0.3, why="Trailing fraction of the window reported separately
  as out-of-sample consistency (R001 risk register: OOS ≥ 30%).", ge=0.3, le=0.5)`

**Part D — evidence generator (`scripts/backtest_proposal.py`, composition root):**

- Flags: `--parameter <name>`, `--current <float>`, `--proposed <float>`, `--input <bars CSV>`,
  `--out <evidence JSON>`, plus overrides for the three tunables (defaults from
  `ResearcherSettings()`).
- **Bounded signal catalogue** (the S106 pattern — vetted list, not free-form): a registry mapping
  supported parameter names → a builder that computes `{date → {ticker → score}}` from bars under a
  given parameter value. `scripts/` may import agent domain code, so builders reuse the **analyst's
  own indicator functions** — never reimplement them. Ship **two entries**: pick two analyst
  technical parameters that are (a) real entries in
  `docs/research/parameter-inventory/` and (b) computable from close/volume series alone (momentum
  and volatility window-style parameters are the expected candidates — verify exact names in-tree
  and cite them in the closeout). Unknown parameter → print `no signal builder for <name> — evidence
  not generated` and exit 0 (**fail-open**).
- Pipeline: build incumbent scores (parameter = `--current`) and proposed scores (= `--proposed`)
  from the same bars → run the Part B harness on each with identical settings → print a
  **side-by-side markdown table** (full-window + holdout columns for both variants, plus deltas) →
  write the proposed-variant `BacktestEvidence` JSON (`model_dump`) to `--out`.
- A round-trip unit test proves `ParameterChangeProposal(..., backtest=BacktestEvidence(...))`
  validates and serializes — the schema the review queue will consume.

### Out

- **No researcher runtime/agent changes** — the agent cannot run backtests (`external_io=()` is law);
  live attachment of evidence to on-bus proposals is a later sprint once an evidence hand-off
  pattern is designed. The contract field ships now so the schema is settled.
- **No law edits** — researcher laws are LOCKED v1; the OOS ≥ 30 % rule is enforced by the tunable's
  bound, not a law change.
- **No new data source** — bars come from the S111 exporter's CSV; no graph reads in the script.
- **No optimizer/parameter search** — one incumbent vs one proposed value per run; sweeps are CI-6
  territory (ADR-0013, deferred).
- **No qlib, no committed data files.**

## Deliverables

- `BacktestEvidence` + optional `backtest` field (contract 0.2.0) · `agents/researcher/domain/
  backtest.py` · three `ResearcherSettings` tunables · `scripts/backtest_proposal.py` with a
  two-entry signal catalogue.
- Unit tests: harness no-lookahead property (a score spike on date `t` cannot affect the return of
  the leg ending at `t`'s fill — construct the counterexample), fill-at-next-close alignment,
  slippage/turnover arithmetic (first-rebalance turnover = 1.0, partial replacement fractions),
  max-drawdown on a known curve, holdout split boundary, missing-price dropout, `ic_mean` undefined-
  date skip; catalogue dispatch + fail-open path; contract round-trip; settings bounds. `make ci`
  green, 100 % coverage, modules ≤ 200 lines (split the harness if it approaches 150).

## Functionality check (sprint-close rule)

Live, real data — unit-green ≠ works. **Preflight `docs/laws/tiingo-usage-limits.md`; reuse the S110
ticker list** (shared monthly unique-symbol budget); export via `scripts/export_tiingo_bars.py`
(S111) — resumable, paced.

1. Run `scripts/backtest_proposal.py` on one catalogue parameter with its real in-tree current value
   vs a plausibly-bounded proposed value, over ≥ 3 years × ≥ 100 tickers.
2. Evidence: paste the side-by-side table (full + holdout, both variants, deltas) into the
   `docs/laws/functionality-checks.md` row. Sanity: `n_days` in the hundreds, every metric populated,
   holdout columns present. **Either direction of result is valid** — evidence generation is the
   deliverable, not a favorable delta; only a crash, an empty table, or a missing metric fails.
3. Validate the written JSON: `BacktestEvidence.model_validate(json.load(...))` in a scratch check.
4. Teardown: delete scratch CSV/JSON; `git status` clean of data files. Record the row (state
   Tiingo-sourced, DL-37).

## Dependencies

- **S111 shipped** (`scripts/export_tiingo_bars.py`, 0.54.00) — hard prerequisite.
- S110 pieces: `scripts/price_csv.py` loader, `docs/laws/tiingo-usage-limits.md`.
- Analyst domain indicator functions (imported by `scripts/` only). Live Tiingo credential in `.env`.

## Version bump

New capability (harness + contract field + evidence CLI). **0.54.01 → 0.55.00** (feat → MINOR
zeroes the patch).

## Execution notes (for the coding agent — cold-start handover)

**Start.** From `main` (`git pull`; verify S111 is merged): `git checkout -b
sprint-112-researcher-backtest-evidence`. Read `contracts/researcher.py`,
`agents/researcher/{agent,settings,store}.py` + `domain/{evidence,proposal}.py`,
`agents/analyst/domain/` (find the two catalogue indicators + their parameter names in
`docs/research/parameter-inventory/`), `scripts/{price_csv,export_tiingo_bars}.py`, and R001
§"For Coding Agents" + §"Addendum (2026-07-04)" (`docs/research/qlib-integration/qlib-integration.md`).

**Gate.** `make ci` green — 9 steps, **100 % coverage**, modules ≤ 200 lines, headers. Bump
0.54.00 → 0.55.00 + `uv lock`.

**Boundaries.** Harness in `agents/researcher/domain/` imports only stdlib + `contracts` + `kernel`
— **never another agent**. Analyst imports happen in `scripts/` only. import-linter stays green.

**Commit.** Branch-per-sprint; commit only your own files; conventional message ending with
`Co-Authored-By: …`. Do **not** merge/push to `main` without operator confirmation.

**Session gotchas (carried from S110/S111):**

1. **Contract tests assert shape** — `agents/researcher/tests/test_researcher_boundary.py` (and the
   boundary meta-test) will notice the contract change; update assertions deliberately, citing the
   0.2.0 bump, not by loosening them.
2. **`_Frozen` models are frozen** — construct `BacktestEvidence` once, fully; no mutation.
3. **Dates are ISO strings** — lexicographic sort = chronological; the fill-alignment logic must use
   each ticker's own date sequence (tickers have unequal calendars; missing dates are normal).
4. **Tiingo pacing** — 50 req/hour; the exporter is resumable for exactly this reason; same ticker
   list as S110/S111, always.
5. **detect-secrets / mypy strict / module headers** — as S110/S111; both scripts get
   `Agent: tooling` headers.
6. **Fail-open vs fail-closed:** evidence generation fails **open** (no builder → no evidence, exit
   0) because evidence is additive; the harness math fails **honest** (undefined metric → omitted,
   never fabricated) — mirror the S110 battery's omission discipline.

## Notes

Q3 of the R001 addendum sequencing (Q1b ✅ S110 → Q1c 📦 S111 → **Q3** → Q5 governed factor mining).
The harness is deliberately generic — scores in, evidence out — because Q5 reuses it verbatim: a
candidate factor is just another score series to this simulator. The reviewer-facing intent from the
original R001 Q3 is unchanged: humans see simulated Sharpe/IC alongside provenance evidence before
approving any parameter change.

## Closeout evidence

Appended by the coding agent at completion.
