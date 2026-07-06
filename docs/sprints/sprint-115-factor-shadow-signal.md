<!-- Agent: planning | Role: sprint handover -->
# Sprint 115 — Factor shadow signal: approved factor → live shadow → scorecard (qlib Phase Q5, part B)

**Phase:** qlib workflow adoption (Q5 part B — closes the governed factor-mining loop, Moonshot #3)
**Branch:** `sprint-115-factor-shadow-signal`
**Status:** ready for handover — from `main` (S113 merged `3ec2d9e`, 0.57.00)
**Effort:** M

---

## Codex kickoff (paste this)

> Execute **Sprint 115 — Factor shadow signal** exactly as specified in this file
> (`docs/sprints/sprint-115-factor-shadow-signal.md`). It is a complete, self-contained handover.
>
> - **Start:** from `main` (`git pull`), `git checkout -b sprint-115-factor-shadow-signal` (delete any
>   stale local branch of that name first). Read the files under *Execution notes → read first* before
>   writing anything.
> - **Hard gate every commit:** `make ci` green — 9 steps, **100 % coverage**, modules **≤ 200 lines**,
>   `Agent:`/`Role:` headers. Bump `pyproject.toml` **0.57.00 → 0.58.00** (feat → MINOR zeroes the
>   patch) + `uv lock`.
> - **The governance invariant:** the factor shadow signal is **advisory-only and OFF by default**
>   (the Q2 Alpha158 `weight=0.00` precedent). Turning it on is an **operator settings action** taken
>   after approving a `FactorProposal` — never automatic. `ShadowPrediction.shadow` stays `True`;
>   **FORE-NEV-02 holds**: the forecaster never gates, vetoes, or sizes anything.
> - **Islands beat DRY:** the forecaster **duplicates** the three factor functions in its own domain —
>   it must NOT import `agents.researcher`. Same no-lookahead fence test as S113.
> - **Contract change is additive-only:** one new `forecast_factor` capability on the forecaster,
>   contract MINOR bump. No required-field changes, no consumer breaks.
> - **Locked laws:** forecaster `laws.md` is LOCKED — do **not** edit it. The new capability must
>   *comply* with existing clauses (cite FORE-NEV-02 in the shadow-only test docstring). If you find a
>   genuine law gap, flag it in the closeout — don't edit the law book.
> - **Reuse, don't rebuild:** the existing generic `_scorecard` (reads `ShadowPrediction`s by
>   `model_id`) must cover factor predictions with **zero or near-zero new scorecard code**. The S113
>   catalogue semantics (names, parameter bounds) must match exactly — same factor names, same bounds.
> - **Real-environment check** (sprint-close rule): with the factor enabled in a scratch env config
>   (never committed on), drive `forecast_factor` for real tickers against real bars on live Aura →
>   `ShadowPrediction` nodes written with the factor `model_id` and `shadow=true` → `scorecard` for
>   that `model_id` returns populated metrics → prove the **off-by-default** path (unset settings →
>   capability refuses cleanly / reports disabled, no crash). Record in
>   `docs/laws/functionality-checks.md`; tear down all stamped nodes to baseline; **no data files
>   committed.**
> - **Do NOT merge or push to `main`** — commit on the branch only, then stop for operator review.
> - Read *Session gotchas* before coding. When done, append a **Closeout evidence** block to this file.

---

## What this sprint is

S113 (part A) shipped the propose+evidence half: the LLM nominates an in-catalogue factor and it
arrives with deterministic walk-forward evidence. Part B closes the loop's **measure phase**:

> an operator-**approved** factor becomes a **live shadow signal** in the forecaster — emitted daily
> as `ShadowPrediction`s under its own `model_id`, accumulating a real out-of-sample track record that
> the existing scorecard reads. **Kill** = operator clears the setting. **Promote** = an operator
> decision on scorecard evidence, executed on the existing rails (P10 predictor registry
> `advisory → load_bearing`, stage gate) — not automated here.

This lands the factor at the same maturity as the Q1 LightGBM return shadow and the Q2 Alpha158
pillar: shipped, advisory, off by default, measured. That *is* the Q5 loop closed — every stage
governed, LLM never driving.

**Out of scope (flag, don't build):** wiring a promoted factor into analyst scoring weights (that is
a future sprint if a factor earns it on scorecard evidence); any automation of promote/kill; any
change to the S113 researcher catalogue or the S112 harness; any change to locked law books.

---

## Execution notes

### Read first (the seams you plug into)

- `agents/forecaster/agent.py` — **the pattern to mirror is `_forecast_return`** (settings-declared
  `model_id`/`model_ref`, `write_forecast(...)` provenance, `ShadowPrediction` out) and the generic
  `_scorecard` (reads predictions by `model_id` — your factor predictions get scorecards for free).
- `agents/forecaster/store.py` (or wherever `write_forecast`/`read_predictions` live) — the graph
  write/read seam. Reuse; extend only if a `model_kind` tag is needed (mirror how `"return"` is tagged).
- `agents/forecaster/settings.py` — where the new factor settings go (see *Build* step 2). Note how
  `return_model_id`/`return_model_ref` are declared.
- `agents/forecaster/domain/return_labels.py` + how `read_return` acquires bars for a subject
  (`agents/forecaster/domain/features.py` / the bus seam) — **reuse the same bars-acquisition path**
  for factor inputs; do not invent a new data path.
- `agents/researcher/domain/factors.py` + `factors_impl.py` — the S113 catalogue semantics you must
  duplicate exactly (names `momentum` / `mean_reversion` / `volatility_rank`, parameter bounds,
  no-lookahead discipline). **Read for semantics; do not import.**
- `contracts/forecaster.py` — `ShadowPrediction`, `Scorecard`, `ForecastRequest`, the `CONTRACT`
  block (capability list + version).
- `agents/forecaster/laws/laws.md` — LOCKED; read FORE-NEV-02 and the trigger/serving clauses so the
  new capability's tests can cite them. `agents/forecaster/laws/test-plan.md` may be extended.
- `docs/sprints/sprint-113-governed-factor-proposal.md` closeout — what part A proved, and the
  catalogue bounds the settings must enforce.

### Build

1. **Factor math — `agents/forecaster/domain/factor_signal.py`** (pure, island-clean). Duplicate the
   three factor functions from S113's catalogue with identical semantics and bounds (~80 lines; copy
   the tiny rolling-stat helpers too — do not import researcher). Include the same **no-lookahead
   fence test**: a factor value at *t* is unchanged when future bars are appended.
2. **Settings — `agents/forecaster/settings.py`** (additive):
   - `factor_name: str = ""` — empty = **disabled** (the default; the Q2 off-by-default precedent).
   - `factor_params: str = ""` — e.g. `"lookback=60"`; parsed + validated against the duplicated
     bounds (reject-not-clamp, mirroring S113's `validate_selection`).
   - `factor_model_id: str` — derived or declared, e.g. `"factor-momentum-60"`; this is the
     scorecard key.
   Numeric bounds via `kernel.tunable(..., why=...)` where applicable.
3. **Capability — `forecast_factor`** on the forecaster (additive; contract MINOR bump). Mirrors
   `_forecast_return`: validate `ForecastRequest` → if `factor_name` is empty or params invalid,
   return/raise the established "disabled/unsupported" shape **cleanly** (no crash — verify how the
   agent surfaces a refused capability today and match it) → else acquire bars via the existing
   features seam → compute the factor value for `subject_ref` → `write_forecast` with the factor
   `model_id` (tag `model_kind="factor"` if the store pattern wants it) → return `ShadowPrediction`
   (`shadow=True` always; cite FORE-NEV-02 in the compliance test docstring).
4. **Scorecard coverage** — prove with a test that `scorecard` for the factor `model_id` returns
   populated metrics over factor `ShadowPrediction`s, `promotion_eligible=False`. Target **zero new
   scorecard code**; if the store needs a `model_kind` filter tweak, keep it additive.
5. **Run-book — `agents/forecaster/mission.md`** (short section): the operator loop —
   approve a `FactorProposal` (S113 evidence) → set `FORECASTER_FACTOR_NAME`/`_PARAMS` → shadow
   accumulates → read `scorecard` → **promote** (existing registry/stage rails, operator-held) or
   **kill** (clear the setting). Keep it to ~10 lines; it documents governance, not new machinery.

### Contract / boundary

- Forecaster contract: one additive capability, MINOR bump. `owns_graph` unchanged
  (`ShadowPrediction`/`Model`/`ForecasterRun` already owned).
- No researcher import anywhere in forecaster. No change to researcher/S113 files.
- Locked `laws.md` untouched; tests cite existing clause IDs (e.g. `FORE-NEV-02`).

---

## Definition of done (verifiable success factors)

1. `make ci` green — 9 steps, **100 % coverage**, modules ≤ 200 lines, headers. Version `0.58.00`,
   `uv.lock` staged.
2. `factor_signal.py` duplicates the S113 catalogue exactly (names, bounds, semantics); no-lookahead
   fence test present; a semantics-parity test pins factor values to the same numbers S113's
   catalogue produces for a shared fixture (guards silent drift between the two copies).
3. `forecast_factor` capability shipped additively; disabled-by-default path proven by test (empty
   `factor_name` → clean refusal, no crash); `shadow=True` compliance test cites FORE-NEV-02.
4. Scorecard over the factor `model_id` proven by test with zero/near-zero new scorecard code;
   `promotion_eligible=False`.
5. Operator run-book section in `agents/forecaster/mission.md`.
6. **Real-environment functionality check passed and recorded** (see kickoff): live emission on Aura
   with real bars, scorecard populated, off-by-default proven, teardown to baseline, no data files.
7. Committed on the branch only. **Not** merged or pushed to `main`.

---

## Session gotchas (read before coding)

- **Parity, not import.** The forecaster's factor math must equal the researcher's — but via
  duplication + a parity test, never an import. If the two copies ever need to diverge, that is a
  design decision for the planning agent, not a code fix.
- **Off means off.** Default settings must produce a system indistinguishable from today's: no factor
  predictions, no new graph writes, every existing test untouched. The enable path is exercised only
  in tests and the live check's scratch env.
- **Match the refusal shape.** Look at how the forecaster surfaces an unavailable model today (e.g.
  the return model missing its artifact) and mirror that for "factor disabled" — do not invent a new
  error convention.
- **Bars come from the existing seam.** `read_return`'s features path already solves bar acquisition
  under the agent's laws. A second data path would be a boundary violation waiting to happen.
- **Scorecard is generic on purpose.** If you find yourself writing a factor-specific scorecard,
  stop — the `model_id`-keyed one is the design. At most an additive `model_kind` filter.
- **Locked laws.** Forecaster and researcher law books are LOCKED v1. Cite clauses; never edit. A
  perceived gap goes in the closeout notes.
- **The catalogue is versioned by S113.** If you think a bound or name should change, flag it — the
  two copies and the LLM prompt must stay in lockstep, and that's a planning decision.

---

## Why this closes Q5 (context, not scope)

R001's Q5 loop: *the researcher (LLM) proposes candidate factors; the Q3 harness scores them
deterministically; a human approves; shadow period; scorecard; promote or kill.* After S115 every
stage exists and is governed: propose+evidence (S113), approve (operator, S113's review queue),
shadow (this sprint, off-by-default emission under its own `model_id`), scorecard (existing generic
machinery over the factor's predictions), promote/kill (operator on existing P10/stage rails).
The LLM's only power remains nomination. This is Moonshot #3 made concrete at the same maturity bar
as every other signal in the system: **advisory until the evidence says otherwise.**

---

## Closeout evidence

<!-- Coding agent: fill this in on handback. Files changed, coverage %, the functionality-check row,
     the contract bump, any decisions/deviations, and the exact make ci summary line. Do not merge. -->
