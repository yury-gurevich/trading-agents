<!-- Agent: planning | Role: sprint handover -->
# Sprint 113 — Governed factor proposal: LLM proposes, harness scores (qlib Phase Q5, part A)

**Phase:** qlib workflow adoption (Q5 — R001 addendum 2026-07-04, governed factor-mining loop = Moonshot #3)
**Branch:** `sprint-113-governed-factor-proposal`
**Status:** ready for handover — from `main` (S112 merged `feb7f87`, S109 re-run merged `b60fc6f`)
**Effort:** M

---

## Codex kickoff (paste this)

> Execute **Sprint 113 — Governed factor proposal** exactly as specified in this file
> (`docs/sprints/sprint-113-governed-factor-proposal.md`). It is a complete, self-contained handover.
>
> - **Start:** from `main` (`git pull`), `git checkout -b sprint-113-governed-factor-proposal` (delete
>   any stale local branch of that name first). Read the files under *Execution notes → read first*
>   before writing anything.
> - **Hard gate every commit:** `make ci` green — 9 steps, **100 % coverage**, modules **≤ 200 lines**,
>   coding-agent `Agent:`/`Role:` headers. Bump `pyproject.toml` **0.56.00 → 0.57.00** (feat → MINOR
>   zeroes the patch) + `uv lock`.
> - **The governance invariant (this is the whole point of Q5):** the LLM **only ever proposes a factor
>   from a bounded catalogue**. It never computes a score, never emits a trade, never applies anything.
>   Deterministic harness scores it; a human approves later. Preserve it exactly.
> - **`external_io=()` is untouched.** The researcher domain stays pure and island-clean: **no LLM call,
>   no network, no imports from any other agent** (duplicate any tiny math; islands beat DRY). Every
>   live-model call runs **only** in the composition root (`scripts/`), exactly as S112 did for evidence.
> - **Contract change is additive-only:** new `ProposedFactor` + `FactorProposal` types, researcher
>   contract **0.2.0 → 0.3.0**. No required-field change on any existing type, no consumer breaks.
> - **Fail-open, enum-guarded (mirror S106):** an off-catalogue or malformed LLM selection means "no
>   proposal generated", never a crash and never an out-of-bounds factor. Bounds are `kernel.tunable`.
> - **Reuse the S112 harness as-is** (`run_walkforward` / `to_evidence`) — do not modify it. A factor is
>   just a pure `bars → scores` function feeding the same harness.
> - **Real-environment check** (sprint-close rule): real Tiingo bars (S110 ticker list via the S111
>   exporter `scripts/export_tiingo_bars.py`; preflight `docs/laws/tiingo-usage-limits.md`) → LLM
>   proposes an in-catalogue factor → walk-forward evidence populated → `FactorProposal.model_validate`
>   round-trip → **and** prove the guardrail: a forced off-menu selection fails open (no proposal, no
>   crash). Record the row in `docs/laws/functionality-checks.md`. **No data files committed.**
> - **Do NOT merge or push to `main`** — commit on the branch only, then stop for operator review.
> - Read *Session gotchas* before coding. When done, append a **Closeout evidence** block to this file.

---

## What this sprint is

Q5 is the governed factor-mining loop: **propose → backtest → approve → shadow → scorecard →
promote/kill**. The tail (approve → … → promote) already exists as governance rails. This sprint builds
**part A only — the propose+evidence half**, mirroring the S106→S107 "propose then execute" split:

> the researcher proposes a candidate **factor** drawn from a **bounded catalogue**; the existing S112
> walk-forward harness scores it deterministically; the result is emitted as a governed `FactorProposal`
> carrying `BacktestEvidence`, ready for the human-review queue.

**Explicitly out of scope (that is S115, part B):** turning an approved factor into a live shadow
signal, the scorecard over shadow performance, and promote/kill through the P10 predictor registry.
Anything touching the forecaster/analyst shadow-emitter, a new graph label, a bus event, or a new agent
capability handler belongs to S115 — **flag it, don't build it.**

### Why a "factor" is small here

The S112 harness (`agents/researcher/domain/backtest.py :: run_walkforward`) is **factor-agnostic**: it
consumes a `scores` dict (`date → {ticker → value}`) and a `closes` dict, and returns a `BacktestResult`.
So a candidate factor is nothing more than a **pure deterministic function `bars → scores`**. The bounded
catalogue is a small, named set of such functions with `tunable`-bounded parameters. This is the same
shape as the `CATALOGUE` already in `scripts/backtest_proposal.py` (which maps `analyst.rsi_period` /
`analyst.bollinger_window` to signal builders) — S113 generalizes it into a researcher-owned, LLM-
selectable factor catalogue.

---

## Execution notes

### Read first (the seams you plug into)

- `agents/researcher/domain/backtest.py` — `run_walkforward(scores, closes, *, top_k, slippage_bps,
  holdout_fraction)` and `to_evidence(result, *, slippage_bps)`. **Reuse unchanged.** Note the `scores`
  and `closes` shapes — your factor functions produce `scores`.
- `agents/researcher/domain/backtest_types.py` — `BacktestResult`, `_Series`. Reference only.
- `contracts/researcher.py` — `BacktestEvidence`, `ProposedChange`, `ParameterChangeProposal` (the shape
  your new types sit beside), `CONTRACT` (version + `owns_graph`).
- `scripts/backtest_proposal.py` — the **driver template** to mirror: `CATALOGUE` dispatch, `close_series`,
  incumbent-vs-proposed run, JSON out, fail-open on unknown parameter. Your `scripts/mine_factors.py`
  follows this structure but the *selection* comes from the LLM, not CLI args.
- `scripts/deliberate.py` — copy the **bounded-LLM adapter pattern**: `_provider_llm`, `_OpenAIText`
  (now reasoning-budget-correct after S109 re-run — honors `max_tokens`), `.env` loading. The unit test
  `tests/test_deliberate_script.py` shows how to fake the adapter for 100 % coverage with no live call.
- `agents/master/remediation.py` + `remediation_gate.py` — the **S106 enum-guardrail / fail-open**
  reference: LLM picks from a bounded catalogue; off-menu or malformed → safe default, never a crash.

### Build

1. **Factor catalogue — `agents/researcher/domain/factors.py`** (pure, island-clean, no other-agent
   import). A small **named** catalogue (start with **exactly three**, to stay well under 200 lines and
   fully covered):
   - `momentum` — trailing return over `lookback` bars.
   - `mean_reversion` — negative z-score of close vs a `window` moving average.
   - `volatility_rank` — inverse realized volatility over `window` (a low-vol tilt).

   Each is a pure `Callable[[Bars, Params], Scores]` producing `date → {ticker → value}`, no lookahead
   (a score at date *t* uses only bars up to and including *t*). Duplicate any tiny rolling-stat math
   locally — **do not import `agents.analyst`.** Declare each parameter's bounds with
   `kernel.tunable(..., why=...)` (e.g. `momentum.lookback ∈ [5, 120]`). Expose:
   - `CATALOGUE: Mapping[str, FactorSpec]` — name → spec (the callable + its parameter bounds). This is
     the **enum guardrail**: a factor name not in `CATALOGUE` cannot be proposed.
   - `validate_selection(name, params) -> FactorSelection | None` — pure: returns a validated selection
     if `name` is in the catalogue and every param is within its declared bound; otherwise `None`
     (**fail-open** — the caller treats `None` as "no proposal").
   - `score(selection, bars) -> Scores` — dispatch to the validated factor.

   If this file approaches 150 lines, split the primitives into `factors_impl.py` and keep the
   catalogue and validation in `factors.py`. Prefer small.

2. **Contract types — `contracts/researcher.py`** (additive; bump `version` **0.2.0 → 0.3.0**):
   - `ProposedFactor(_Frozen)`: `name: str`, `params: tuple[tuple[str, float], ...]` (sorted, hashable),
     `rationale: Explanation`.
   - `FactorProposal(_Frozen)`: `proposal_id: str`, `factor: ProposedFactor`, `provenance: Provenance`,
     `backtest: BacktestEvidence | None = None`. Docstring: *"Lands in the human-review queue. The
     researcher never applies it itself."* (same discipline as `ParameterChangeProposal`).
   - **No** new `Capability`, **no** `emits` entry, **no** new `owns_graph` label in this sprint — those
     are the S115 promotion surface. Keep the change to types only, exactly as S112 added `BacktestEvidence`
     without touching capabilities. Update any boundary/contract test that snapshots the researcher shape.

3. **Proposal builder — `agents/researcher/domain/factor_proposal.py`** (pure): `build_factor_proposal(
   selection, evidence, provenance, proposal_id) -> FactorProposal`. Mirrors `domain/proposal.py`. No I/O.

4. **Driver — `scripts/mine_factors.py`** (`Agent: tooling`; the *only* place the LLM is called):
   - Load bars (Tiingo CSV via `scripts/price_csv.py` / the S111 exporter output).
   - Build the **bounded prompt**: present the catalogue (names + parameter bounds) and ask the model for
     **one** JSON selection `{"name": ..., "params": {...}, "rationale": ...}`. Parse defensively.
   - `validate_selection(...)` → `None` ⇒ print "off-catalogue selection — no proposal generated" and
     exit 0 (**fail-open**, like S112's unsupported-parameter path).
   - Else `score()` → `run_walkforward()` → `to_evidence()` → `build_factor_proposal()` → write JSON →
     `FactorProposal.model_validate(...)` round-trip. Reuse the `_provider_llm`/`_OpenAIText` adapter
     pattern from `scripts/deliberate.py` (import or duplicate a thin helper — scripts may share).
   - A `--factor`/`--params` manual override (bypassing the LLM) is welcome for a deterministic unit path
     and offline runs, but the live check must exercise the **LLM** selection.

### Contract / boundary

- Researcher `external_io=()` **unchanged** — proven by the LLM living only in `scripts/`.
- `import-linter` unchanged: `factors.py`, `factor_proposal.py` import only `kernel` + `contracts`.
- Additive contract bump 0.2.0 → 0.3.0; no required field added to an existing type.

---

## Definition of done (verifiable success factors)

1. `make ci` green — 9 steps, **100 % coverage**, all modules ≤ 200 lines, headers present. Version
   `0.57.00`, `uv.lock` staged.
2. Three catalogue factors implemented, each pure and no-lookahead, each parameter `tunable`-bounded;
   unit tests cover every factor, every `validate_selection` branch (in-catalogue ok, unknown name,
   out-of-bounds param), and the fail-open path — all with **fakes, no live model**.
3. `ProposedFactor` + `FactorProposal` added; contract 0.3.0; boundary/contract tests updated and green.
4. `scripts/mine_factors.py` runs end to end and round-trips a `FactorProposal` through
   `model_validate`; an off-catalogue selection fails open (exit 0, no proposal, no traceback).
5. **Real-environment functionality check passed and recorded** in `docs/laws/functionality-checks.md`
   (see below); no data files committed (`git status` clean of CSVs/JSON exports).
6. Committed on the branch only. **Not** merged or pushed to `main`.

### Real-environment functionality check (sprint-close rule)

- Preflight `docs/laws/tiingo-usage-limits.md`; export real bars for the S110 100-ticker list via
  `scripts/export_tiingo_bars.py` (Tiingo = DL-37 raw-history source; Alpaca stays primary runtime feed).
- Run `scripts/mine_factors.py` with a live model (`--extra llm`): capture the model's in-catalogue
  selection, the populated `BacktestEvidence` (full + holdout), and the `model_validate` round-trip.
- Force the guardrail: a run where the model's selection is off-catalogue (or inject one) → prove
  fail-open (no proposal, no crash).
- Tear down every scratch CSV/JSON; record the row (intent · environment · proven result · teardown).

---

## Session gotchas (read before coding)

- **The `external_io=()` trap.** It is tempting to have the researcher agent call the LLM. Do not — that
  breaks the researcher law and the boundary test. The LLM lives in `scripts/` only; the agent domain
  stays a pure catalogue + validator + builder. This is the same split S112 used for evidence.
- **Islands over DRY.** `factors.py` must not import `agents.analyst` even though analyst has indicator
  math. Duplicate the few lines you need; the module-boundary meta-test will fail an cross-agent import.
- **No-lookahead is on you.** A factor score stamped at date *t* may read bars only up to *t*; the harness
  then fills at the *next* close. If a factor peeks forward, the walk-forward "no-lookahead by
  construction" guarantee is silently broken. Add a test that a factor value at *t* is unchanged when
  future bars are appended.
- **Bounded means bounded.** The LLM prompt must enumerate the catalogue and the parameter ranges, and
  `validate_selection` must reject anything outside them. Treat the model output as hostile (S106): parse
  a single JSON object, ignore extra prose, reject unknown keys, clamp nothing silently — reject and
  fail open.
- **Reasoning-model budget (post-S109).** If you use `gpt-5`/a reasoning model for the selection, remember
  `max_completion_tokens` is a shared reasoning+output pool — use the S109-fixed adapter (honors
  `max_tokens`); a tight cap returns empty content (`finish_reason=length`). `gpt-5.5` is the default
  debater/selector and is fine.
- **Don't touch the harness.** `run_walkforward`/`to_evidence` are frozen S112 API. If you feel the urge
  to modify them, you are probably doing part B (S115) — stop and flag it.
- **Coverage of the script.** `scripts/` is outside the coverage *source* (no 100 % floor there), but any
  logic you can move into the covered domain (`factors.py`, `factor_proposal.py`) should live there and be
  fully tested; keep the script a thin composition root.

---

## Why this ordering (context, not scope)

Part A ships the governed *proposal* with prospective evidence — the LLM now contributes candidate
factors under a hard bounded-catalogue guardrail, and every candidate arrives with deterministic
walk-forward evidence for a human to weigh. Part B (S115) then wires an approved factor into a live
shadow signal and the promote/kill scorecard. Splitting here keeps each slice inside the 200-line /
100 %-coverage regime and preserves the "LLM never drives trading decisions" policy at every step:
here it only *nominates* something to measure. See the R001 addendum (`docs/research/qlib-integration/`)
and DL-39 (`docs/design-log.md`) — the graded rationale from these proposals is the eventual training
source for "which parameters carry the decision load."

---

## Closeout evidence

<!-- Coding agent: fill this in on handback. Files changed, coverage %, the functionality-check row,
     any decisions/deviations, and the exact make ci summary line. Do not merge. -->

Completed on branch `sprint-113-governed-factor-proposal` for operator review; not merged or pushed.

- Files changed: `agents/researcher/domain/factors.py`, `factors_impl.py`, `factor_proposal.py`;
  `contracts/researcher.py`; `scripts/mine_factors.py`, `mine_factors_prompt.py`;
  `agents/researcher/tests/test_factors.py`, `tests/test_mine_factors.py`,
  `tests/test_contract_values.py`; `pyproject.toml`, `uv.lock`,
  `docs/laws/functionality-checks.md`, and this sprint handover.
- Contract/version: researcher contract bumped `0.2.0 -> 0.3.0`; project version
  `0.56.00 -> 0.57.00`; `uv lock` refreshed. Added only `ProposedFactor` and
  `FactorProposal`; no new capability, emit, graph label, or required field on existing types.
- Governance invariant: LLM selection is enum-guarded by the three-factor catalogue
  (`momentum`, `mean_reversion`, `volatility_rank`). The researcher domain remains pure;
  `external_io=()` is unchanged. Live model access exists only in `scripts/mine_factors.py`;
  `run_walkforward` / `to_evidence` were reused unchanged.
- Functionality-check row: added to `docs/laws/functionality-checks.md` for S113 on
  2026-07-05. Real Tiingo export used the S110 100-ticker list: 25,000 rows, 250 bars/ticker,
  2025-07-07..2026-07-02, zero duplicate `(ticker,date)` keys. OpenAI `gpt-5.5` selected
  `momentum` with `lookback=60`; `FactorProposal.model_validate` round-tripped; forced
  `invented_factor` failed open with no output JSON.
- Teardown: deleted `data/s113-live-bars.csv` and `data/s113-live-proposal.json`; the off-menu
  check wrote no file. No data CSV/JSON artifacts are staged.
- Gate: `make ci` green after implementation and script split: `1358 passed, 5 skipped`,
  `Required test coverage of 100.0% reached. Total coverage: 100.00%`; import-linter kept,
  module hard block kept, headers check passed, detect-secrets passed, and pip-audit reported
  no known vulnerabilities (torch skipped because the CPU wheel is not on PyPI).
