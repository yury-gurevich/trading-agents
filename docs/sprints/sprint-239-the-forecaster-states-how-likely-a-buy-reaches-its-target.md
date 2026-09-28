<!-- Agent: planning | Role: sprint handover -->
# Sprint 239 — for every buy, the forecaster states how likely its target comes before its stop, and records the claim

**Phase:** Etalon-first continuous improvement (DL-19) · work-queue 92 (the book as a distribution), sprint A of the ledger
**Branch:** `sprint-239-the-forecaster-states-how-likely-a-buy-reaches-its-target`
**Status:** BUILT 2026-09-28 (Claude cloud session; branch pushed, unmerged; owed items in the Closeout)
**Version:** *next available MINOR at merge* (`0.118.00` on the branch)
**Effort:** M
**Decisions:** [DL-240](../design-log.md) (the direction, and its EXP-018 entry: the ledger is built on GARCH at ~3 years) · [EXP-018](../research/experiments/EXP-018-garch-history-depth.md) (the model and the evidence) · [EXP-017](../research/experiments/EXP-017-block-bootstrap-and-garch-barrier-probabilities.md) · ADR-0010 (shadow models are promoted only through the registry) · the builder's design decisions go to the **next free DL** (`DL-241` at spec time)

> **Why this bump kind.** The forecaster gains a capability it did not have: a stated probability for each
> of three outcomes of a buy, recorded as a claim that can be settled. That is new capability, so MINOR.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build**, except the forecaster amendment this spec names (law-cycle answer: Yes) |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections: **`FORE-IDN`** (01 the job, 02 the single-writer label list), **`FORE-IN-01/02`**,
**`FORE-TRG`**, **`FORE-OUT-01/02/05/06`**, **`FORE-NEV-01..04`**, **`FORE-STA`**, **`FORE-IDM-02`**,
**`FORE-FAIL-01..03`**, **`FORE-CAP`**, **`FORE-PARAM`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes, both.** `contracts/forecaster.py` gains a capability and an owned label, and the forecaster makes a
new guarantee. Owed in the same unit of work:

- **`FORE-IDN-02` amended**: the forecaster also writes `BarrierForecast`.
- **New `FORE-OUT-07`** (next free `OUT` ID; check it): for a buy with a stop and a target, the
  forecaster states P(stop first), P(target first) and P(neither) within 10 sessions (the low checked before
  the high), which sum to 1, and records them with the barriers, the history they came from and the model
  identity, as an append-only, advisory claim. You own the final wording.
- **New `FORE-FAIL-04`** (or the next free ID): a claim is recorded only from a successful fit on enough
  history; otherwise no claim, a fault, and the neutral reading of `FORE-OUT-06`. **A claim is never
  fabricated.**
- `CAP` gains the capability; `PARAM` gains every new setting with its type, bounds and tunability.
- Forecaster book **v1.3 → v1.4** with a Changelog line; a `test-plan.md` row per clause; clause IDs in test
  docstrings; the rollup in **both** `docs/laws/ledger.md` **and** `docs/laws/INDEX.md` (let `make ci` tell
  you the number); a `drift-register.md` row for anything the change slips under.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/forecaster/*` (new modules, `agent.py`, `poll.py`, `settings.py`) | `agents/forecaster/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `FORE-IDN`, `FORE-OUT`, `FORE-NEV`, `FORE-FAIL`, `FORE-IDM-02`, `PARAM` |
| `contracts/forecaster.py` | same, plus ADR-0010 | `FORE-CAP`; the capability list and `owns_graph` |
| `orchestration/packs/trading_graph_vocabulary.json` | the vocabulary pack's own notes; DL-85 (the fail-closed write guard) | an undeclared label raises `VocabularyError` on its first write |
| `pyproject.toml` (the `forecaster` extra) | this spec's Guardrails | `arch` joins the optional dependency; the unit gate never imports it |

⚠️ **The forecaster stays advisory.** Nothing it writes may reach the PM, execution or the monitor, and no
setting may make it binding (`FORE-NEV-01/02`). If your design needs the PM to read a `BarrierForecast`,
stop and report: that is a later sprint and the operator's capital-risk decision.

---

## Goal

At merge, every `buy` recommendation that carries a stop and a target gets a forecaster claim: the
probability that, over the next 10 sessions, the price reaches the stop first, the target first, or neither.
The claim comes from EXP-018's model (GARCH(1,1) with Student-t innovations, filtered historical simulation,
on ~3 years of the stock's own daily bars), is stored as an append-only `BarrierForecast` node with
everything sprint B needs to settle it, and changes nothing the fleet buys or sells.

## Why (context)

The operator set the direction on 2026-09-28 ([DL-240](../design-log.md)): manage the book as a
distribution, where every position carries its outcome probabilities and exits, trims and adds follow from
them. Nothing may size or exit on a probability until a **ledger** shows it comes true. Three experiments
settled the model:

- [EXP-016](../research/experiments/EXP-016-jev-barrier-probabilities.md): a language model (Jev) is not a
  forecaster here (Brier 0.84–0.85 against climatology's 0.616).
- [EXP-017](../research/experiments/EXP-017-block-bootstrap-and-garch-barrier-probabilities.md): GARCH is the
  only model with skill on short history; the plain bootstrap has none on the fleet's 203 bars.
- [EXP-018](../research/experiments/EXP-018-garch-history-depth.md): GARCH on **756 bars** clears the
  pre-registered bar: skill **+2.67 %** over climatology, 95 % interval [+1.88, +3.48], 0.39 % failed fits,
  near-diagonal calibration, an edge in every year 2019–2025.

This sprint states and records the claims. **Sprint B** (next) settles each claim ten sessions later and
puts the scorecard on the dashboard.

### Measured, 2026-09-28 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| GARCH skill at 756 bars | +2.67 % [+1.88, +3.48] over climatology, 37,587 decisions | *[measured]* EXP-018, the replay cache |
| Failed fits with boundary estimates accepted | 0.39 % at 756 bars; 4.4 % of fits hit the 0.999 persistence cap | *[measured]* EXP-018 |
| A live 756-session SIP fetch, 99 names + SPY | 8 pages, 75,200 bars, 8.3 MB, 19.1 s; **752** bars per name from a 1,097-calendar-day window | *[measured]* EXP-018 side measurement, provider code at `main` |
| One name, one run: bars needed | one provider request of ~760 bars (well under the 10,000-bar page) | *[derived]* from the above |
| The forecaster's `agent.py` | **199** lines (the block is 200); `settings.py` 152; `poll.py` 76 | *[measured]* `wc -l` at spec time |
| How the forecaster is triggered | graph-pull on each `AnalystRun`: `poll.forecast_analyst_node` fires one RPC per recommendation per capability in `_CAPABILITIES` | *[measured]* `agents/forecaster/poll.py` |
| A recommendation's barriers | `Recommendation.suggested_stop_pct` / `suggested_target_pct` (and `stop_target_evidence.applied_*`) | *[measured]* `contracts/analyst.py` |
| The live barriers equal EXP-018's barrier formula | S211's clamped 2 × ATR14 stop and median 10-session best rise target | *[ASSUMED]* S211 / ADR-0027 say so; the planner checks it on a live run (F2) |
| Production refits every run; EXP-018 refitted monthly | — | *[ASSUMED harmless]* the planner measures it on the test bed before merge (F1) |
| `arch` in the forecaster image | adds `arch`, `statsmodels`, `pandas`, `patsy` | *[ASSUMED size]* the planner measures the image before the deploy |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first** (A1–A9 below).
2. **The model, as pure code.** A module (for example `agents/forecaster/domain/barrier_garch.py`) that, given
   a stock's daily bars, a stop and a target, fitted GARCH parameters and a seed, returns the three
   probabilities by **filtered historical simulation** exactly as EXP-018's `garch_path_probs`: standardised
   residuals and each day's high and low (log distance from the prior close ÷ that day's σ) resampled together;
   the simulated σ follows the GARCH(1,1) recursion from the decision-day forecast; high and low never cross the
   simulated close; **1,000 paths × 10 sessions**; the low checked before the high. It may import numpy (the
   forecaster image has it, and the unit gate has it since chore-barrier-testbed). **Copy the logic from
   [EXP-018 Appendix S](../research/experiments/EXP-018-garch-history-depth.md)**, not from memory.
3. **The fit, behind a port.** An adapter that fits GARCH(1,1), constant mean, Student-t, on returns in percent
   with `arch`, imported lazily (the `agents/forecaster/lightgbm_model.py` pattern), returning `(mu, omega,
   alpha, beta)` and a status. **Acceptance rule, exactly EXP-018's:** accepted when converged with ω > 0,
   α ≥ 0, β ≥ 0 and α + β ≤ 1; when α + β > 0.999, α and β are scaled in proportion to sum to 0.999 (status
   `capped`); anything else is a failed fit. Tests use a fake fitter.
4. **The handler.** A new capability **`forecast_barrier`** (request `ForecastRequest`, response
   `ShadowPrediction`). `features` carries `stop_pct` and `target_pct`. The handler requests the stock's bars from
   the provider over the bus (`provider_client.request_prices`, `FORE-NEV-04`) for a window holding at least
   **`barrier_history_sessions`** (default **760**) sessions, keeps the last 760, fits, simulates, and:
   - on success: writes one **`BarrierForecast`** node and returns a `ShadowPrediction` with `model_id =
     "barrier-garch-v1"`, `value` = P(target first), `shadow = True`;
   - on a failed fit, fewer than **`barrier_min_history_sessions`** (default **700**) bars, or a provider
     error: **no node**, a fault, and the neutral reading of `FORE-OUT-06`.
5. **The claim record.** `BarrierForecast`, keyed so a second run on the same ticker and the same last bar
   **merges** rather than duplicates (for example `barrier:{ticker}:{as_of}`), with at least: `ticker`,
   `as_of` (the last bar's date), `entry_close` (that bar's close), `horizon_sessions` (10), `stop_pct`,
   `target_pct`, `p_stop_first`, `p_target_first`, `p_neither`, `model_id`, `model_version`, `history_bars`,
   `n_paths`, `seed`, `fit_status` (`accepted` | `capped`), the four fitted parameters, `created_at`, and
   `shadow: true`. Sprint B settles from exactly these fields.
6. **Determinism (`FORE-IDM-02`).** The seed is derived from `(ticker, as_of)` with a stable hash (not Python's
   salted `hash`), so the same bars give the same probabilities.
7. **The trigger.** `poll.forecast_analyst_node` also fires `forecast_barrier` for each recommendation whose
   `action` is `buy` and which carries both `suggested_stop_pct` and `suggested_target_pct`, passing them in
   `features`. Nothing else in the poll changes.
8. **Declarations.** `contracts/forecaster.py`: the capability and `BarrierForecast` in `owns_graph`; the
   vocabulary pack: the `BarrierForecast` label (and any edge you add, with its signature); `pyproject.toml`:
   `arch` in the `forecaster` extra.
9. **The law cycle** above, and the builder's decisions in `docs/design-log.md` under the next free DL.

### Out of scope (do NOT build this sprint)

- **Settlement and the scorecard.** Sprint B.
- **Held positions.** Daily re-reads of held names (for exits) come after the ledger proves out.
- **Any reader of `BarrierForecast` outside the forecaster**: PM, execution, monitor, dashboard. Sizing or exits
  on these probabilities are later sprints and the operator's decision.
- **The scanner / analyst history window** (`orchestration/history_window.py`, the dispatcher's declared
  window). The forecaster makes its own longer request; that file is a decision path (DL-238 D7).
- **Any change to the analyst's stop or target.** The claim uses the recommendation's barriers as they are.
- **Caching fitted parameters between runs.** Refit per call; the forecaster stays stateless (`FORE-STA-01`).

### The road not taken (LAW-06)

- **Reuse the `ShadowPrediction` label with extra properties.** Rejected: settlement and the scorecard need a
  record with a fixed shape and three probabilities; a one-number label stretched to carry them would make every
  later reader guess.
- **Fit GARCH without `arch` (our own likelihood with scipy).** Rejected: EXP-018 measured `arch`'s estimator; a
  different optimiser is an untested model. Parity with the experiment is the point of F1.
- **Fall back to the previous run's parameters on a failed fit** (EXP-018 reused the previous month's).
  Rejected: it needs state between runs (`FORE-STA-01`). No claim is recorded instead; failed fits were 0.39 %.
- **Lengthen the fleet's 203-bar window for everyone.** Rejected: it is a decision path, and would change what
  the scanner and analyst see.
- **Forecast only the PM's approved buys.** Rejected for now: the poll runs at the `AnalystRun`, before the PM;
  forecasting every buy recommendation gives the ledger more claims, and sprint B can split approved from not.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Where the new code lives, given `agent.py` is at 199 lines.** Registering one more handler will not fit
   without moving something out. Say what you moved and why.
2. **The `BarrierForecast` key and whether it carries an edge** (to the `AnalystRun` or the `ForecasterRun`), and
   if so its vocabulary signature.
3. **How the request window is sized** to guarantee at least 760 bars (EXP-018 measured 752 from 1,097 calendar
   days; add a margin and keep the last 760).
4. **`ShadowPrediction.confidence` for this model**, and the final wording of the new clauses.

🪤 **Take the next free DL number, then re-check it at merge.** `DL-241` is free at spec time.

---

## Blast radius — measured 2026-09-28

| What | Detail |
| --- | --- |
| Files changed | `agents/forecaster/agent.py` (**199**), `settings.py` (152), `poll.py` (76), new modules for the model, the fit adapter and the handler; `contracts/forecaster.py`; `orchestration/packs/trading_graph_vocabulary.json`; `pyproject.toml` (+ `uv.lock`, owed to the planner); tests under `agents/forecaster/tests/`; `agents/forecaster/laws/{laws,test-plan}.md`, `docs/laws/{ledger,INDEX,drift-register}.md`, `docs/design-log.md` |
| Agents affected | forecaster only. No agent imports another. |
| Contract change? | **Yes** (`contracts/forecaster.py`): the law cycle above is mandatory. 🪤 `contracts/` is also on the S237 fidelity check's decision-path list, see Sequencing. |
| Graph vocabulary change? | **Yes**, a new label: the deploy is a **full `up`**, not a retag. |
| New env keys / tunables | `barrier_history_sessions` (760), `barrier_min_history_sessions` (700), `barrier_paths` (1,000), each a `tunable` with bounds and a PARAM row. The horizon (10) and the persistence cap (0.999) are **constants**: they define the model EXP-018 measured. |
| Deploy implication | **Full `up`**, the operator's call. It changes nothing the fleet trades. |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Plant the failing tests first** (A1–A9) and watch them fail. Paste the red output.
4. **Implement.**
5. **Law cycle**: amended `FORE-IDN-02`, the new `OUT` and `FAIL` clauses, `CAP`, `PARAM`, v1.4 + Changelog,
   test-plan rows, docstring citations, both rollups, drift row if owed.
6. **Prove the guards can fail (DL-70)** — plant each, watch it go red, restore: the stop checked after the
   target (A1 red); the persistence cap removed (A3 red); a claim written on a failed fit (A5 red); the seed from
   Python's `hash` (A6 red, or say why it cannot be caught); `forecast_barrier` fired for a `sell` (A8 red).
7. **`make ci` green**: every step of the `ci:` target, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 The simulation states three probabilities that sum to 1, low before high (`FORE-OUT-07`) | synthetic bars; fixed parameters and seed | a rising history gives target-first ≈ 1; a falling one stop-first ≈ 1; a flat one with wide barriers neither ≈ 1; a path touching both in one session counts as stop |
| A2 | The simulation equals EXP-018's `garch_path_probs` | the same bars, parameters and seed through both | identical probabilities (copy the experiment's function into the test as the oracle) |
| A3 | The fit's acceptance rule is EXP-018's | fake fitter returning α + β = 0.95, = 1.0, > 1, not converged, ω ≤ 0 | accepted; capped to 0.999 in proportion; failed; failed; failed |
| A4 | 🎯 A successful call writes one `BarrierForecast` with every field sprint B needs (`FORE-OUT-07`, `FORE-IDN-02`) | fake bus serving 760 bars; fake fitter | the node's fields, `shadow: true`; the response is a `ShadowPrediction` with `value` = P(target first) |
| A5 | 🪤 No claim is fabricated (`FORE-FAIL-04`) | a failed fit; 650 bars; a provider error | no `BarrierForecast`; a fault; the neutral `ShadowPrediction` (`FORE-OUT-06`) |
| A6 | Same bars, same probabilities (`FORE-IDM-02`) | the same call twice, in two processes if you can | identical probabilities and seed; the second write merges into the same node |
| A7 | The request is for the stock's own long history, through the provider (`FORE-NEV-04`) | a recording fake bus | one `get_market_data` request, `fields=("ohlcv",)`, a window holding ≥ 760 sessions |
| A8 | The poll fires `forecast_barrier` only for buys with both barriers | an `AnalystRun` with a buy, a buy without a target, a sell, a hold | one `forecast_barrier` request, for the first, with `stop_pct` and `target_pct` in `features` |
| A9 | 🪤 Nothing reaches the decision path (`FORE-NEV-02`) | a full poll + handler pass on a fake graph | no node written with a PM, execution or monitor label; no message to those agents |

---

## Success factors

- [ ] Every `buy` recommendation with both barriers gets one `BarrierForecast` claim per ticker and last bar,
      or a fault and no claim (A4, A5, A8).
- [ ] The simulation equals EXP-018's, probability for probability (A2).
- [ ] Nothing reaches the PM, execution or monitor (A9); no decision path touched except `contracts/forecaster.py`
      (see Sequencing).
- [ ] Law cycle done; design decisions recorded under a free DL.
- [ ] Every DL-70 plant in step 6 planted, watched to fail, restored — stated per plant.
- [ ] Every touched module < 200 lines; `agent.py` below 200 after the change.
- [ ] `make ci` exit 0, 100.00 % coverage.
- [ ] **Planner, before merge (live data):**
  - **F1, parity with the experiment**: the forecaster's model run over the barrier test bed
    (`scripts/barrier_testbed.py`, the replay cache) with the real `arch` fitter reproduces EXP-018's 756-bar
    skill within noise (**≥ +2.0 %**, interval above zero), refitted monthly as in the experiment **and** per
    decision as in production, on a pre-stated subsample, so the per-run refit is measured, not assumed.
  - **F2, live barriers**: on the latest scheduled run's `AnalystRun`, each buy's `suggested_stop_pct` /
    `suggested_target_pct` equals the test bed's `barriers()` on the same bars (EXP-018's formula), or the
    difference is named.
  - **F3, live call**: the handler, run from the branch's worktree with `main`'s `.env` for one live ticker,
    fetches ≥ 760 SIP bars, fits and states three probabilities that sum to 1; the record it would write is
    printed, not written.
  - **Image size** of the forecaster image with `arch` against `s238`.
- [ ] **Owed after the operator's full `up` (F4)**: the first scheduled run writes one `BarrierForecast` per buy
      recommendation (or a named fault), and no other agent's behaviour changes.

---

## Traps

🪤 **A clean fit is not a calibrated claim.** The test that matters is A2 (the experiment's own function as the
oracle) and F1 (the skill on ten years). A green unit suite with a different simulation is a different model.
🪤 **Daily bars are stamped 04:00Z or 05:00Z.** Use the last bar's *date* for `as_of`, never a clock.
🪤 **`agent.py` is at 199 lines.** One more handler line blocks `make ci`. Move code out; do not compress.
🪤 **The unit gate must not import `arch`.** Import it lazily inside the adapter; tests use a fake fitter; the
adapter's body is the only `pragma: no cover` code (the `lightgbm_model.py` pattern).
🪤 **Python's `hash()` is salted per process.** A seed from it breaks `FORE-IDM-02` across runs.
🪤 **The vocabulary guard is fail-closed.** A label missing from the pack raises `VocabularyError` on its first
write in production, and unit tests with an in-memory graph will not see it. Test against the pack.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass a rule.
  📌 Current sizes: `agent.py` **199**, `settings.py` **152**, `poll.py` **76**, `provider_client.py` **89**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: `kernel.tunable(..., why=...)` with bounds for the three settings; the horizon and the cap are
  named constants citing EXP-018.
- Faults, not silent failure: `kernel.fault_boundary`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a pipe.**
- Version bump: MINOR in `pyproject.toml`. 🪤 A cloud session cannot re-resolve `uv lock` (`download.pytorch.org`
  is blocked, DL-228): add `arch` to the `forecaster` extra, leave `uv.lock` untouched and say so; the planner
  re-locks. Your `make ci` runs without the extra, which is why tests use a fake fitter.
- Secrets never through the tree. The cloud session has **no `.env`, no `gh` and no Azure**: state which
  environment you ran in, and leave F1–F3 to the planner.

---

## Sequencing after merge

1. The cloud session: `make ci` green in its environment, the branch pushed, then it stops.
2. The planner, locally: re-lock (`arch`), `make ci` on Windows, **`make gate-ran`** from a worktree whose
   `HEAD` is the pushed commit (check the printed SHA), F1–F3, the image size, and the branch ref's open CodeQL
   alerts.
3. 🪤 **DL-237's first fidelity verdict (due after `sched-2026-10-01`) must be run from a worktree at the last
   `main` commit before this sprint merges**, or run before it merges: `contracts/` is on the fidelity check's
   decision-path list, so after this merge every earlier session reads non-clean against `main`. (Item 91 carries
   the same note.)
4. Merge to `main` locally and push; post-merge CodeQL on `main`.
5. **Deploy: a full `up`** (the vocabulary pack moved), the operator's call. Then F4 on the next scheduled run.

---

## Handover — paste this to the Claude cloud session

```text
Sprint 239 — for every buy, the forecaster states how likely its target comes before its stop, and
records the claim. Spec: docs/sprints/sprint-239-the-forecaster-states-how-likely-a-buy-reaches-its-target.md
on main (read ALL of it, then CLAUDE.md). Repo: yury-gurevich/trading-agents.

Branch: sprint-239-the-forecaster-states-how-likely-a-buy-reaches-its-target, cut from main. Never
main. If your session forces another branch name, use it and name it in the handback.
You have NO .env, NO gh, NO Azure and no route to download.pytorch.org. Every proof is a unit test.
You cannot run `make gate-ran`: it is owed to the planner. Add `arch` to the forecaster extra, leave
uv.lock untouched and say so; the planner re-locks. A run result read through the GitHub connector is
an observation, never GATE PROVEN. Take DL-241 (re-check it is still free on main).

What and why: the operator's direction (DL-240) is to manage the book as a distribution. EXP-018
found the model: GARCH(1,1), Student-t, filtered historical simulation on ~3 years (756 bars) of a
stock's own daily bars, +2.67 % Brier skill over climatology [+1.88, +3.48]. This sprint makes the
forecaster state, for each buy recommendation, P(stop first), P(target first), P(neither) within 10
sessions (low checked before high) and record it as an append-only BarrierForecast claim. It is
advisory: nothing reads it outside the forecaster. Sprint B settles the claims later.

MUST RULE before any code: read agents/forecaster/laws/laws.md and test-plan.md whole (FORE-IDN,
IN, TRG, OUT, NEV, STA, IDM, FAIL, CAP, PARAM), docs/laws/conventions.md,
docs/laws/drift-register.md. Fill the Law reading record in the spec first.

Law-cycle answer: YES (contracts/forecaster.py changes; a new guarantee). Amend FORE-IDN-02
(also writes BarrierForecast); new OUT clause (the three probabilities, sum 1, the claim's fields,
advisory, append-only); new FAIL clause (no claim without a successful fit on enough history:
fault + FORE-OUT-06 neutral reading, never a fabricated claim); CAP; PARAM rows; v1.3 -> v1.4 +
Changelog; test-plan rows; clause IDs in docstrings; rollups in docs/laws/ledger.md AND
docs/laws/INDEX.md; drift row if owed.

Build:
1. The model, pure: copy EXP-018's garch_path_probs (docs/research/experiments/EXP-018-garch-
   history-depth.md, Appendix S) into the forecaster (e.g. agents/forecaster/domain/barrier_garch.py).
   1,000 paths x 10 sessions; numpy allowed. Do not rewrite it from memory.
2. The fit, behind a port: an arch adapter (GARCH(1,1), constant mean, t, returns in %), imported
   lazily like agents/forecaster/lightgbm_model.py; tests use a fake fitter. Acceptance exactly
   EXP-018's: converged, omega > 0, alpha >= 0, beta >= 0, alpha + beta <= 1; if > 0.999 scale both
   to sum 0.999 (status capped); else failed.
3. Capability forecast_barrier (ForecastRequest -> ShadowPrediction); features carries stop_pct and
   target_pct. The handler asks the provider over the bus (request_prices) for >= 760 sessions
   (tunable barrier_history_sessions 760; EXP-018 got 752 bars from 1,097 calendar days, so add a
   margin and keep the last 760), fits, simulates. Success: one BarrierForecast node (ticker,
   as_of = last bar DATE, entry_close, horizon_sessions 10, stop_pct, target_pct, p_stop_first,
   p_target_first, p_neither, model_id barrier-garch-v1, model_version, history_bars, n_paths, seed,
   fit_status, the four params, created_at, shadow true), keyed per ticker + as_of so a rerun merges;
   response ShadowPrediction value = P(target first). Failure (failed fit, < 700 bars via tunable
   barrier_min_history_sessions, provider error): no node, a fault, the FORE-OUT-06 neutral reading.
   Seed from a stable hash of (ticker, as_of), never Python's hash().
4. poll.forecast_analyst_node also fires forecast_barrier for each recommendation with action buy
   and both suggested_stop_pct and suggested_target_pct. Nothing else changes.
5. Declare: contracts/forecaster.py (capability + BarrierForecast in owns_graph); the vocabulary pack
   orchestration/packs/trading_graph_vocabulary.json (the label, and any edge with its signature);
   pyproject.toml (arch in the forecaster extra); MINOR version bump.

Order: DL-241 -> red tests A1-A9 (paste) -> implement -> law cycle -> DL-70 plants (stop checked
after target; cap removed; claim on a failed fit; seed from hash(); forecast_barrier fired for a
sell: each must go red, paste, restore) -> make ci redirected to a file, exit 0, 100.00 %.

DO NOT:
- let anything outside the forecaster read or act on BarrierForecast (PM, execution, monitor,
  dashboard): FORE-NEV-02. If your design needs it, stop and report.
- change orchestration/history_window.py, the scanner or analyst window, or the analyst's barriers.
- write a claim on a failed fit, on short history, or from cached parameters of an earlier run.
- reimplement the simulation or the fit differently from EXP-018 (A2 uses the experiment's function
  as the oracle; the planner's F1 checks the skill on ten years).
- import arch at module import time, or anywhere the unit gate loads it.
- grow agent.py (199 lines) past 200: move code out. No # noqa to bypass a rule.
- let any test reach the network.
- claim a live proof or GATE PROVEN: F1-F3, the image size and the gate are the planner's.
- pin a version: MINOR, next available at merge.

Handback — the planner returns it if ANY of these is missing:
[ ] Law reading record filled, including the law-cycle answer and contradictions/silences found.
[ ] Test plan results: A1-A9, each with final test name, file, PASS, clause IDs cited.
[ ] Closeout: the red run pasted before the fix; the green run after.
[ ] Each of the five DL-70 plants: what was planted, its red output, restored.
[ ] Where the code moved out of agent.py, and its final line count.
[ ] Module line counts for every file touched (all < 200).
[ ] make ci: the file, exit code, passed/skipped, coverage 100.00 %, dependency audit, detect-secrets.
[ ] Exactly how uv.lock was touched (untouched and owed, or re-resolved).
[ ] The design decisions under DL-241 with rejected alternatives.
[ ] Return notes: scope held or moved; what you disagreed with after reading the laws; what sprint B
    (settlement + scorecard) should know.
[ ] Status: BUILT on the spec, and this sprint's README.md row leads with BUILT, in the same commit.
[ ] Owed items named: uv lock, make gate-ran, Windows make ci, F1-F3, image size.
Commit on the branch and PUSH it, then stop: no merge. Anything not met: "not done", never a
Result: for work not done.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

*Filled 2026-09-28 by the builder (Claude cloud session) before the first code change. Read whole, first
time: `agents/forecaster/laws/laws.md` (v1.3, 211 lines), `agents/forecaster/laws/test-plan.md` (17 / 45),
`docs/laws/conventions.md`, `docs/laws/drift-register.md` (last ID `DRIFT-080`), ADR-0010, EXP-018 §5–§8 and
Appendix S, and the code the clauses govern (`agent.py`, `poll.py`, `provider_client.py`, `store.py`,
`settings.py`, `lightgbm_model.py`, `contracts/forecaster.py`, `kernel/graph_support.py`,
`kernel/graph_vocabulary.py`, the vocabulary pack).*

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `agents/forecaster/*` new modules (model, fit port, handler) | forecaster `laws.md` + `test-plan.md`; `conventions.md` | `FORE-IDN-01/02`, `FORE-OUT-01/02/05/06`, `FORE-NEV-01/02/04`, `FORE-STA-01/02`, `FORE-IDM-02`, `FORE-FAIL-01/02/03`, `FORE-TYP-02` | **Yes, three ways.** (1) `FORE-STA-02` (⬜) says writes are append-only, and the kernel enforces it: `kernel/graph_support._append_props` raises `property … cannot be overwritten`. A rerun that merges a fresh `created_at` would be refused, so a rerun reuses the first claim's `created_at`, and a rerun that would state a *different* claim is refused with a fault: the first claim stands. (2) `FORE-IDM-02` is about the **return model** only; citing it for the barrier model would narrow a clause to fit a test (§7a). Determinism gets its own clause (`FORE-IDM-04`) and A6 cites that, not `IDM-02`. (3) `FORE-FAIL-01` says a scoring failure still writes a neutral prediction node; the new failure clause writes **no** node, so it is scoped to `forecast_barrier` by name so the two cannot be read against each other. |
| `agents/forecaster/agent.py`, `poll.py`, `settings.py` | same | `FORE-TRG-01/02` (🟩), `FORE-NEV-02` (🟩), `FORE-PARAM` | `FORE-TRG-02`: the poll fires the RPC, the handler never self-triggers. The PARAM table is checked against `settings.py` by `check_param_law_sync.py`, so the horizon (10), the persistence cap (0.999) and the model id stay **named constants** in the model module, not settings. |
| `agents/forecaster/provider_client.py` (reused) | same | `FORE-NEV-04` (🟩), `FORE-FAIL-02` (🟩), `FORE-DEP-01` (⬜) | The bars come only through `request_prices` over the bus. Its fault boundary already records a provider error; the handler adds its own fault only for the cases that helper cannot see (short history, failed fit). |
| `contracts/forecaster.py` | same, ADR-0010 | `FORE-CAP`, `FORE-TYP-01` (🟩), `FORE-NEV-03` | The capability joins `consumes`, `BarrierForecast` joins `owns_graph`; `ShadowPrediction`'s fields are untouched, so `FORE-TYP-01`'s required-field test keeps holding. Contract version `0.5.0` → `0.6.0` (a capability added; DRIFT-060). ADR-0010 concerns LLM prompts; it binds only in that nothing here is promoted. |
| `orchestration/packs/trading_graph_vocabulary.json` | DL-85; `tests/test_graph_vocabulary_*.py` | the fail-closed write guard | The label **and its property names** are declared, so the guard also refuses a misspelt claim field; a test runs the handler through `GuardedGraphStore` built from the pack (the spec's trap: an in-memory graph alone would not see it). No edge is added (DL-241 D2). |
| `pyproject.toml` | this spec's Guardrails | — | `arch` joins the `forecaster` extra only; `uv.lock` is left untouched (cannot re-resolve here). |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **Yes, both.**
`contracts/forecaster.py` gains `forecast_barrier` and `BarrierForecast`, and the forecaster makes a new
guarantee. Owed and done in this unit of work: `FORE-IDN-02` amended; new `FORE-IN-07` (the capability's
input: the first capability to read `features`), `FORE-OUT-07` (the claim), `FORE-IDM-04` (determinism and
rerun merge), `FORE-FAIL-04` (no fabricated claim); `CAP`; three `PARAM` rows; v1.3 → v1.4 + Changelog;
test-plan rows; both rollups; `DRIFT-081`. `IN-07` and `IDM-04` go beyond the two clauses the spec names:
the spec lets the builder own the wording, and neither guarantee fits honestly inside `OUT-07` (conventions
§1 files determinism under `IDM` and inputs under `IN`).

**Contradictions found between a law and this spec:** none that forces a stop. One citation in the spec's
test plan is not honest under §7a: **A6 names `FORE-IDM-02`**, whose text is *"Return model output is
deterministic given the same OHLCV bars"*. A barrier test proves nothing about the return model, so A6 cites
the new `FORE-IDM-04` and `FORE-IDM-02` stays ⬜.

**Laws found silent where a decision was needed** (recorded as `DRIFT-081`, OPEN, for the planner):

- **`FORE-IDN-01`** names the forecaster's job as running *"the sentiment model … and the return model"*. The
  factor leg (Q5) was added without amending it, and the barrier model is a third unnamed model. The spec
  names only `IDN-02` for amendment, so `IDN-01` is left as it is and the gap is registered.
- **`FORE-OBS-01`** says *"A `ShadowPrediction` node is written per prediction"*. The barrier model's
  prediction is recorded as a `BarrierForecast` and writes no `ShadowPrediction` node (the spec's design).
  `FORE-OUT-07` states this explicitly; the literal `OBS-01` reading is registered.
- **`FORE-IDN-02`** never listed `ForecasterRun`, which the poll writes and the contract's `owns_graph`
  declares. Not this sprint's to fix; registered with the other two.
- **No input clause governed `features`** until now (`FORE-IN-02` says the return model ignores them).
  `FORE-IN-07` covers the new capability; malformed barriers fail closed.

**Clauses that were ⬜ and are now proven** *(result, at handback)*: `FORE-IDN-02` (amended; cited by
`test_a_successful_call_writes_one_complete_claim` and `test_the_claim_passes_the_packs_vocabulary_guard`,
both passing). The new `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` are 🟩 on their citing
tests; `check_law_coverage.py` derives the forecaster at **22 / 49** (was 17 / 45). `FORE-STA-02`, `FORE-IDM-02`, `FORE-OBS-01`, `FORE-IN-06` stay ⬜: the new tests touch only the
barrier leg of each, which §7a says leaves a general clause gray.

---

## Test plan results — fill at handback

All in `agents/forecaster/tests/`; every row PASS in the final `make ci` run (see Closeout).

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a_rising_history_reaches_the_target_first`, `test_a_falling_history_reaches_the_stop_first`, `test_a_flat_history_with_wide_barriers_reaches_neither`, `test_a_session_touching_both_barriers_counts_as_the_stop` (+ `test_the_earlier_session_wins_whichever_barrier_it_is`, `test_the_simulation_reads_only_the_segment_it_is_given`) | `test_barrier_garch.py` | PASS | `FORE-OUT-07` |
| A2 | `test_the_simulation_equals_exp018` ×3 (+ `test_the_oracle_is_the_experiments_code`, `test_daily_moves_are_the_experiments`) | `test_barrier_garch_oracle.py` | PASS | `FORE-OUT-07` |
| A3 | `test_a_fit_is_accepted_or_capped_as_exp018_did` ×3, `test_the_boundary_tolerance_is_exp018s`, `test_every_other_fit_fails` ×6 | `test_barrier_garch.py` | PASS | `FORE-FAIL-04`, `FORE-OUT-07` |
| A4 | `test_a_successful_call_writes_one_complete_claim`, `test_the_claim_passes_the_packs_vocabulary_guard` | `test_barrier_claim.py` | PASS | `FORE-OUT-07`, `FORE-IDN-02` |
| A5 | `test_a_failed_fit_records_no_claim`, `test_a_fitter_exception_records_no_claim`, `test_short_history_records_no_claim_and_never_fits` (650 bars), `test_a_degraded_provider_records_no_claim`, `test_a_provider_error_records_no_claim`, `test_without_arch_the_default_fitter_records_no_claim` | `test_barrier_refusals.py` | PASS | `FORE-FAIL-04` (+ `FORE-NEV-04`, `FORE-FAIL-02` where the provider is the cause) |
| A6 | `test_the_same_bars_give_the_same_claim_merged_into_one_node`, `test_a_different_claim_for_the_same_last_bar_is_refused`, `test_the_seed_is_stable_across_processes` (a child interpreter with `PYTHONHASHSEED=random`, plus the pinned value `3333665949` for `AAPL:2026-09-25`) | `test_barrier_claim.py` | PASS | `FORE-IDM-04` — **not** `FORE-IDM-02`, which is about the return model (Law reading record) |
| A7 | `test_the_history_is_one_long_ohlcv_request_to_the_provider` | `test_barrier_refusals.py` | PASS | `FORE-NEV-04`, `FORE-IN-07` |
| A8 | `test_the_poll_asks_for_a_claim_only_for_buys_with_both_barriers` | `test_barrier_poll.py` | PASS | `FORE-IN-07`, `FORE-TRG-01` |
| A9 | `test_a_full_pass_never_reaches_the_decision_path` | `test_barrier_poll.py` | PASS | `FORE-NEV-02`, `FORE-OUT-07` |

**Tests added beyond the plan:** `test_malformed_barriers_record_no_claim` ×5 (`FORE-IN-07`: a missing, zero,
negative or >1 barrier is refused before any provider request); `test_a_different_claim_for_the_same_last_bar_is_refused`
(`FORE-IDM-04`: the append-only graph refuses a changed rerun, the first claim stands);
`test_a_degraded_provider_records_no_claim` (the provider absorbs a source failure and answers with no bars, so
the forecaster sees short history, not a bus error: measured while writing A5);
`test_the_reference_lfilter_is_scipys_where_scipy_exists` (**SKIPPED in the gate**, no scipy; run with
`uv run --with scipy==1.18.1` it passes, below). `test_forecaster_boundary.py::test_contract_declares_never_clauses_and_no_external_io`
was updated for the new contract version `0.6.0` and `owns_graph`.

---

## Closeout — evidence

**Status:** BUILT 2026-09-28. Branch pushed; not merged (the planner merges).

**Tree the proofs ran in (and `.env` present?):** a claude.ai cloud container, Linux, Python 3.13, a clone of
`yury-gurevich/trading-agents` on branch `sprint-239-the-forecaster-states-how-likely-a-buy-reaches-its-target`
cut from `main` `e753543` and rebased, before the first push, onto `8a05938` (S240's docs-only spec; conflicts in `STATE.md` and the sprint `README` / `INDEX` rows only). **No `.env`**, no `gh`, no Azure, no route to `download.pytorch.org`. Every `uv run`
ran with `UV_FROZEN=1` (the bumped `pyproject.toml` cannot be re-locked here). No test reaches the network: the
provider is `FakeDataSource`, the fitter `FakeGarchFitter`, and the one child process runs `barrier_seed` only.

**Result:** For a `buy` with both barriers, `forecast_barrier` asks the provider for one 1,125-day OHLCV window,
keeps the last 760 bars, fits GARCH(1,1)-t through the fitter port, applies EXP-018's acceptance rule, simulates
1,000 × 10 filtered-historical-simulation paths and writes one `BarrierForecast` (21 fields, key
`barrier-garch-v1:{ticker}:{as_of}`), returning a shadow prediction of P(target first). A failed fit, <700 bars,
a provider error, malformed barriers or an absent `arch` write no claim, record a named fault and return the
neutral reading; a changed rerun is refused and the first claim stands. The poll fires it only for buys with both
barriers. All of this is proven by unit tests with a fake fitter; **nothing here proves the skill on real data**
(F1) or a live fetch (F3).

**Files changed:** new `agents/forecaster/domain/barrier_garch.py` (the model, copied from EXP-018),
`barrier_fit.py` (port, fake, lazy `arch` adapter), `barrier_forecast.py` (the handler), `barrier_store.py` (the
claim), `scorecards.py` (moved out of `agent.py`); `agent.py`, `poll.py`, `settings.py`; `contracts/forecaster.py`
(capability, `owns_graph`, version `0.6.0`); `orchestration/packs/trading_graph_vocabulary.json` (label + 21
properties, no edge); `pyproject.toml` (`arch>=8.0.0` in the `forecaster` extra, `0.118.00`); tests: six new files
(`barrier_fixture.py`, `barrier_helpers.py`, `test_barrier_{garch,garch_oracle,claim,refusals,poll}.py`) and
`test_forecaster_boundary.py`; laws: forecaster `laws.md` (v1.4) and `test-plan.md`, `docs/laws/{ledger,INDEX,drift-register}.md`;
`docs/design-log.md` (DL-241), `docs/STATE.md`, `docs/sprints/{README,INDEX}.md`, this file.

**Design decisions:** [DL-241](../design-log.md), D1–D8 with their rejected alternatives, plus two findings
(the provider's pooled 8σ guard over a 3-year window; no deployed process fires the poll).

**Proof — the red run first** (the five new test files before any implementation, `pytest --no-cov`):

```text
E   ModuleNotFoundError: No module named 'agents.forecaster.domain.barrier_garch'
E   ModuleNotFoundError: No module named 'agents.forecaster.domain.barrier_garch'
E   ModuleNotFoundError: No module named 'agents.forecaster.barrier_fit'
E   ImportError: cannot import name 'barrier_fit' from 'agents.forecaster' (/home/user/trading-agents/agents/forecaster/__init__.py)
E   ModuleNotFoundError: No module named 'agents.forecaster.barrier_fit'
ERROR agents/forecaster/tests/test_barrier_garch.py
ERROR agents/forecaster/tests/test_barrier_garch_oracle.py
ERROR agents/forecaster/tests/test_barrier_claim.py
ERROR agents/forecaster/tests/test_barrier_refusals.py
ERROR agents/forecaster/tests/test_barrier_poll.py
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
5 errors in 0.80s
```

**Proof — the green run** (the same five files on the final tree):

```text
.....................s...................                                [100%]
=========================== short test summary info ============================
SKIPPED [1] agents/forecaster/tests/test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
40 passed, 1 skipped in 1.29s
```

With real scipy layered on (`UV_FROZEN=1 uv run --with scipy==1.18.1 pytest … test_barrier_garch_oracle.py`, lock
untouched): `6 passed in 2.86s` — the oracle ran the experiment's own `lfilter`, and the reference recurrence the
gate uses matched it bit for bit. *Local observations, not gate proofs* (scratch environment, `arch` 8.0.0 as in
EXP-018): EXP-018's `garch_fit`, extracted from Appendix S, and `ArchGarchFitter` + `accept_fit` gave identical
parameters and status on **18 / 18** synthetic series; the loop variance filter equals `scipy.signal.lfilter` on
**2,000 / 2,000** random series (0 mismatches). The A2 golden values were produced by the experiment's function
with real scipy.

**Guards planted** (DL-70; each planted on the final tree, run, and restored from a copy, `cmp` byte-identical):

1. **Stop checked after the target** (`barrier_probs`: `fs < ft` / `ft <= fs`) → **A1 red**:
   `FAILED test_a_session_touching_both_barriers_counts_as_the_stop` — `assert (0.0, 1.0, 0.0) == (1.0, 0.0, 0.0)`;
   1 failed, 20 passed. A2 stayed green: its fixtures never touch both barriers in one session, so only A1's
   crafted case can see the tie rule. Restored.
2. **Persistence cap removed** (the `alpha + beta > 0.999` branch deleted) → **A3 red**: 3 failed
   (`test_a_fit_is_accepted_or_capped_as_exp018_did[raw1/raw2]`: `GarchParams(…status='accepted') ==
   GarchParams(…status='capped')`; `test_the_boundary_tolerance_is_exp018s`: `'accepted' == 'capped'`). Restored.
3. **A claim written on a failed fit** (`params = accept_fit(raw) or GarchParams(raw…, "accepted")`) → **A5 red**:
   `FAILED test_a_failed_fit_records_no_claim` — `assert (Node(label='BarrierForecast', …),) == ()`. Restored.
   🪤 **The first attempt at this plant stayed green** (11 passed): it referenced `GarchParams` without importing
   it, the resulting `NameError` was caught by the handler's fault boundary, and "no claim, some fault" still
   held. A5 could not tell a refusal from a crash. Every refusal test now names its fault's type and message
   (`BarrierClaimRefusedError` "fit failed", "650 bars <", `ConfigurationError` "arch is not installed", …);
   the plant above is the re-run on that stricter test, with the import.
4. **Seed from Python's `hash()`** (`hash((ticker, as_of)) & 0xFFFFFFFF`) → **A6 red**:
   `FAILED test_the_seed_is_stable_across_processes` — `assert 3681878691 == 3373718167` (the child
   interpreter's salt against this one's). The in-process rerun test stays green, as it must: one process, one
   salt. Restored.
5. **`forecast_barrier` fired for a sell** (the `action != "buy"` condition removed) → **A8 red**:
   `FAILED test_the_poll_asks_for_a_claim_only_for_buys_with_both_barriers` — `assert 3 == 1` (AAPL, the NVDA
   sell and the AMZN hold). Restored.

**Module line counts** (all < 200): `agent.py` **165** (was 199), `poll.py` 102, `settings.py` 182,
`barrier_fit.py` 78, `barrier_forecast.py` 176, `barrier_store.py` 85, `domain/barrier_garch.py` 172,
`scorecards.py` 83, `contracts/forecaster.py` 131; tests: `barrier_fixture.py` 39, `barrier_helpers.py` 123,
`test_barrier_claim.py` 186, `test_barrier_garch.py` 182, `test_barrier_garch_oracle.py` 184,
`test_barrier_poll.py` 119, `test_barrier_refusals.py` 169, `test_forecaster_boundary.py` 51. Code moved out of
`agent.py`: the three scorecard handlers and `_scorecard_metrics` → `scorecards.py`, bound with
`functools.partial` (DL-241 D1).

**`make ci`:** `UV_FROZEN=1 make ci > <session scratchpad>/ci-final.txt 2>&1; echo $?` → **exit 0**, run on the
final, rebased tree in this container: every step of the `ci:` target; ruff and format clean, mypy `no issues found in
1071 source files`, import-linter clean, module size, headers, law coverage, PARAM sync, sprint status, markdown
links, version scheme; pytest **3,522 passed, 7 skipped**, coverage **100.00 %**; dependency audit `No unaccepted
vulnerabilities; 1 accepted advisory re-checked`; detect-secrets `Passed` over all files; untracked scan `no untracked files to scan` (the new files are committed; the pre-commit run scanned the same 12 while they were untracked: `Passed`).
🪤 The audit reads `uv.lock`, which does not yet contain `arch` or its dependencies: it has **not** checked them.
The planner's re-lock and its own audit run do.

**`uv.lock`:** **untouched and owed.** `pyproject.toml` gains `arch>=8.0.0` in the `forecaster` extra and the
`0.118.00` bump; `git diff --stat uv.lock` is empty. A re-lock cannot run here (`download.pytorch.org` is
blocked, DL-228), so the planner re-locks: it should add `arch` 8.0.0 with its dependencies (`statsmodels`,
`pandas`, `patsy`; `scipy` and `numpy` are already in the lock) and move `trading-agents` to `0.118.0`.

**`make gate-ran`:** *(planner: local worktree, full SHA, output)* — **not run here** (no `gh`); owed.

**Planner live checks (F1–F3, image size):** *(planner, before merge)* — **not done here**; owed.

**Not met / verified failing:**

- **F4 cannot pass as built — not done, and not doable within this spec.** In the deployed fleet nothing calls
  `poll.forecast_analyst_node`: only `orchestration/local_pipeline.py` runs it, the forecaster's entrypoint only
  serves requests, and nothing else sends it one (DL-80's forecaster half, still true; DL-241 "Found while
  building"). After a full `up`, the first scheduled run will write **no** `BarrierForecast`. Wiring a trigger
  means breaching `FORE-TRG-01/02` (a forecaster pull loop) or changing another agent's choreography: the
  planner's decision.
- **Owed to the planner:** `uv lock` (and its audit of `arch`), Windows `make ci`, `make gate-ran` for the pushed
  SHA, F1–F3, the forecaster image size with `arch`.

---

## Return notes

- **Scope held**, with three additions inside it: `FORE-IN-07` and `FORE-IDM-04` (clauses beyond the two the spec
  named, because the input and determinism guarantees had no honest home in `OUT-07`), the refusal on a changed
  rerun (the graph's append-only rule forced a decision: DL-241 D5), and `DRIFT-081` for three silences. No reader
  of `BarrierForecast` exists outside the forecaster; no decision path is touched except `contracts/forecaster.py`.
- **Disagreed with, after reading the laws:** A6 cited `FORE-IDM-02`, which is about the return model; citing it
  would have narrowed a clause to fit a test (§7a), so A6 cites `FORE-IDM-04` and `IDM-02` stays ⬜. The spec's
  "a fault" on a provider error splits in two: the provider absorbs a *source* failure and answers with no bars
  (the forecaster sees short history, one fault), while a *bus* error adds the provider client's own fault (two).
  And the spec's measured trigger ("graph-pull on each `AnalystRun`") is true of the code in `poll.py`, but no fleet
  process runs that poll: see *Not met*.
- **For sprint B (settlement + scorecard):**
  - Settle from the node alone: `as_of` is the last bar's **date** and `entry_close` its close; the barriers are
    fractions of `entry_close`; the horizon is the 10 sessions **after** `as_of`; the outcome rule is EXP-018's
    (low first within a session). `p_neither` is `1 − p_stop − p_target` computed in floating point, so it can
    differ from a decimal literal in the last digit.
  - One claim per `barrier-garch-v1:{ticker}:{as_of}`; a rerun on the same bar reuses it. A missing claim for a buy
    is a named fault (short history, failed fit, provider, malformed barriers, a changed rerun), never a silent gap.
    Count faults by type before reading a missing claim as the model failing: a single-ticker 760-bar request
    passes through the provider's pooled 8σ open-to-close guard, and one qualifying day in three years excludes
    the ticker (DL-241).
  - The fit is per call, not per month as in EXP-018, and 760 bars are 759 moves where EXP-018 fitted 756: F1 is
    what measures whether either matters.
  - `confidence` on the response is history coverage (`history_bars ÷ 760`), not calibration; the scorecard is
    what measures calibration.
  - Nothing will be recorded in the fleet until someone decides what fires the poll (*Not met*).
