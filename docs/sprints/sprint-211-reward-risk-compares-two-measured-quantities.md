<!-- Agent: planning | Role: sprint handover -->
# Sprint 211 — `reward_risk` compares two measured quantities

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-211-reward-risk-measured-quantities`
**Status:** MERGED `7d3ff51` (`0.98.08`, tag `v0.98.08`) · **DEPLOYED `s211`** 2026-09-17 — 17/17 targets on `:s211`, all `Succeeded` · **LIVE CHECK DISCHARGED** 2026-09-18 on `sched-2026-09-17`: three distinct `reward_risk` values (AMZN 0.8136, USB 0.8479, WFC 0.9484) against a constant 2.00 before, `comparison=DISCLOSURE_ONLY` at `threshold=0.0` throughout, zero `reward_risk_below_min` rejections, zero `STRUCTURALLY_DETERMINED`, evidence named as `target_basis=trailing_favorable_excursion` (horizon 10 d, sample 120). Recorded in [`docs/laws/functionality-checks.md`](../laws/functionality-checks.md). 🟠 **Still owed:** no `DeployRecord` was written for `s211` (work-queue item **72**).
**Version:** *next available PATCH at merge* — **do not pin a number**
**Effort:** L — two agents, a `contracts/` change, and **two law cycles**. The queue's old "small either way" was wrong.
**Decisions:** [ADR-0027](../decisions/0027-reward-risk-compares-measured-upside-against-measured-downside.md) · [ADR-0025](../decisions/0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md) · DL-172 · DRIFT-066 · closes work-queue item **60**

> **Why this bump kind.** PATCH. `reward_risk` already claims to bound reward against risk and cannot —
> it divides two constants. Nothing gains a capability it did not advertise; one gate starts doing what
> its clause already says. No new agent, endpoint or dimension.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/analyst/laws/laws.md` | The analyst's **locked constitution** (LOCKED **v1.4**, rollup **25 / 48**) | **Read-only** except the amendment this sprint owes |
| `agents/portfolio_manager/laws/laws.md` | The PM's **locked constitution** (LOCKED **v1.6**, rollup **30 / 49**) | Same |
| both `laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read before trusting any clause |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`ANLZ-OBS`**, **`ANLZ-TYP`**, **`PM-NEV`**, **`PM-OBS`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read each `test-plan.md` alongside its `laws.md`.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It is already answered **Yes, twice**.
5. **Write the Law reading record** **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered **YES**, in both agents

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**`contracts/` — YES.** `StopTargetEvidence` (`contracts/analyst.py:30`) has no field for a measured
excursion, its window, or its sample count. The new derivation must record its inputs or the target
becomes unauditable. **This is the S183 trap the template exists to prevent** — a contract shape change
shipped under a LOCKED law book without a clause. Do not let it recur here.

**A guarantee changes in the analyst — YES.** The analyst begins deriving `target_pct` from a measured
per-name quantity rather than from a regime constant. `ANLZ-OBS-05` (`laws.md:214`) governs the
*realised adverse* excursion and its horizon; nothing governs a *decision-time favourable* estimate.

**A guarantee changes in the PM — YES.** `min_reward_risk_ratio` moves 1.5 → 0 **and** the gate defaults
to disclosure-only while still rejecting when a positive floor is explicitly configured. `PM-OBS-04`
already requires that *"a data-varying gate must not be labelled structurally fixed"* — so
`reward_risk_detail.py:76` returning `STRUCTURALLY_DETERMINED` becomes a **violation** the moment the
target varies.

**Therefore this sprint owes two full law cycles in the same unit of work:** analyst `laws.md`
**v1.4 → v1.5**, PM `laws.md` **v1.6 → v1.7**, both with Changelog lines, `test-plan.md` rows per clause
touched, clause IDs cited in test docstrings, and the rollups recomputed in **both**
[`docs/laws/ledger.md`](../laws/ledger.md) (analyst line 40, PM line 42) **and**
[`docs/laws/INDEX.md`](../laws/INDEX.md) (analyst line 41, PM line 43).

🪤 **The rollup is derived, not declared.** `make ci` recomputes it. A new proven clause in each agent
should move each by **+1**; let the gate say so rather than hand-editing to match this guess.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/analyst/domain/stop_target.py` (**:86** `_scaled_target`) | analyst `laws.md` + `test-plan.md` | the pinning lives here |
| `agents/analyst/domain/stop_target_outcome.py` (**:29**) | same | `ANLZ-OBS-05`; the mirror of this function is the new input |
| `contracts/analyst.py` (**:30** `StopTargetEvidence`) | same, plus ADR-0027 | contract shape → law cycle mandatory |
| `agents/portfolio_manager/settings.py` (**:67** `min_reward_risk_ratio`) | PM `laws.md` + `test-plan.md` | the threshold is a declared PARAM |
| `agents/portfolio_manager/domain/reward_risk_detail.py` (**:76**) | same | `PM-OBS-04` — a varying gate must not be labelled structural |

⚠️ **The invariant: the stop must not move.** This sprint changes the **target** leg only.
`_scaled_stop` (`stop_target.py:74`) and every stop percentage stay exactly as they are — the stop is
what protects capital, and S150/S163 evidence rests on it. If your diff changes a stop value, stop and
report.

---

## Goal

`reward_risk` divides a measured per-name upside estimate by the stop risk S211 keeps unchanged, so its
value varies across candidates and is disclosed in every gate report. The default floor is **0**:
disclosure-only, with rejection enabled only by an explicit positive floor. The gate no longer reports
`comparison=STRUCTURALLY_DETERMINED`, because it no longer is. Stops are unchanged.

## Why (context)

`_scaled_target = flat_target × (scaled_stop / flat_stop)`, so `target / stop ≡ flat_target / flat_stop`
in **both** modes — identically `base_take_profit_pct / base_stop_loss_pct` = 2.00. Measured: **one
distinct value across 294 recordings, never once rejecting.** The full reasoning, the rejected
alternatives, and why the floor moves with the derivation are in
[ADR-0027](../decisions/0027-reward-risk-compares-measured-upside-against-measured-downside.md).
**Read it before designing; this spec does not restate its arguments.**

### Measured, 2026-09-16 — read these before designing

Live Neon spine, `MarketData` snapshots. **You do not need to reproduce these; a worktree has no `.env`.**

| Claim | Value | How it was measured |
| --- | --- | --- |
| `reward_risk` distinct values | **1** across **294** recordings | *[measured]* every `gate_report` in every `PMRun` |
| …rejections, all time | **0** | *[measured]* same |
| Independent ratio, 98 names, 10-session horizon | **min 0.60 · p25 1.04 · median 1.35 · p75 1.66 · max 3.00** | *[measured 2026-09-16 snapshot]* median favourable ÷ median adverse excursion, ~110 rolling windows each |
| …distinct values | **74 of 98** (2026-08-14 snapshot) | *[measured]* |
| …below the **old** 1.5 floor | **62 %** | *[measured]* shipping the derivation without moving the floor rejects most of the book |
| …with the returned **positive floor** | **median 49 % per night historically** | *[EXP-011, measured on 47,485 historical decisions]* rejects heavily without predictive return value |
| …default floor | **0, disclosure-only** | *[ADR-0027 Correction 2 / EXP-011]* the ratio is recorded but cannot reject until positive-floor evidence exists |
| Distribution drift | median **1.14 → 1.35** in one month; three recent snapshots agree to 2 dp | *[measured]* 2026-08-14 vs 09-14/15/16 — stable week-to-week, regime-dependent month-to-month |
| Analyst laws | LOCKED **v1.4**, rollup **25 / 48** | *[measured]* `laws.md:3`, `ledger.md:40` |
| PM laws | LOCKED **v1.6**, rollup **30 / 49** | *[measured]* `ledger.md:42` |
| 🚨 `recommend.py` | **193 lines** — **7 from the hard block** | *[measured]* `wc -l`; warn 150, block 200 |
| other sizes | `stop_target.py` **96**, `stop_target_outcome.py` **57**, `outcome_backfill.py` **102**, analyst `settings.py` **152**, PM `settings.py` **133**, `reward_risk_detail.py` **111** | *[measured]* |

---

## Scope — and what is deliberately NOT here

1. **🎯 Plant the failing tests first.** Two reds, pasted, before implementing: (a) two candidates with
   different excursion profiles produce **different** `reward_risk` values — today both are 2.00;
   (b) a low-ratio candidate passes by default as `DISCLOSURE_ONLY`, while a positive configured floor
   still rejects below-floor ratios.
2. **Add the decision-time favourable-excursion estimate.** The mirror of
   `observed_drawdown` (`stop_target_outcome.py:29`): `max(bar.high)` instead of `min(bar.low)`,
   measured over **prior** windows from bars the run already fetched.
3. **Derive `target_pct` from it** in `resolve_stop_target`, replacing `_scaled_target`'s
   stop-times-base-ratio formula. **The stop leg is untouched.**
4. **Extend `StopTargetEvidence`** with the estimate, its window and its sample count, so the target is
   auditable. This is the `contracts/` change; it is in scope **because** the law cycle is.
5. **Move `min_reward_risk_ratio` 1.5 → 0** with the `why=` restated: it records the built
   target_pct ÷ stop_pct ratio without rejecting by default; positive values re-enable rejection and
   need evidence first.
6. **Stop labelling the gate structural.** `reward_risk_detail.py:76` must no longer return
   `STRUCTURALLY_DETERMINED` for `reward_risk`. `PM-OBS-04`'s existing data-varying test is the tripwire.
7. **Both law cycles**, in full, as itemised above.

### Out of scope (do NOT build this sprint)

- **Do not touch the stop leg.** See the invariant.
- **Do not use `observed_drawdown` / the backfill as the decision input.** It is computed *after* the
  horizon settles (`outcome_backfill.py`) and is not available for today's decision. It is the
  **check** on the estimate, not the estimate. Wiring it in as an input is look-ahead bias.
- **Do not make the floor relative** (a percentile of the live distribution). ADR-0027 §3 rejects this
  explicitly and says changing it requires a new ADR.
- **Do not condition the estimate on the buy signal.** ADR-0027 records the estimate as
  *unconditional* — what a name typically does, not what it does when the analyst likes it. Closing
  that gap is later work; this sprint must **disclose** the limitation, not hide or half-fix it.
- **No volatility-scaled sizing.** ADR-0025 Decision B, separate.
- **No ADR reversal.** An ADR is reversed by a new ADR, never by a sprint.

### The road not taken (LAW-06)

ADR-0027 carries the full record — **read it rather than re-deriving**. The ones most likely to tempt
you mid-build: giving the target its own ATR multiple (rejected — both legs scale with the same ATR, so
the ratio is constant again), and scaling the target by analyst confidence (rejected — confidence is a
blended score measured as weakly discriminating; the referee noted the confidence floor *"rejected 0 of
29"* on `sched-2026-09-15`).

---

## The design decisions this sprint has to make

**Record in `docs/design-log.md` with rejected alternatives BEFORE implementing (LAW-06).**

1. **The lookback for the estimate.** `stop_target_drawdown_horizon_days` (`10`) is the *forward*
   horizon for the realised backfill, and its PARAM row says so. How many **prior** windows the
   decision-time estimate samples is a different quantity. **Reusing that tunable overloads a declared
   PARAM whose description would then be wrong** — either add a tunable with its own `why=`, or reuse
   and correct the PARAM row. Pick one and say why.
2. **The estimator.** Median of per-window excursions is what the ADR measured. Mean or a percentile
   would give different numbers. If you choose differently from the ADR, the measured table no longer
   describes what you shipped — say so.
3. **What happens when the estimate is unavailable** (too few bars). `PM-NEV-09`'s shape says an
   un-evaluable gate is `NOT_EVALUATED`, never passed. Decide whether the analyst falls back to the old
   constant target or declines to propose, and make the evidence say which.

🪤 **Take `DL-172` and `DRIFT-066`** — 171 and 065 are spent by S210. **Re-check both at merge.**

---

## Blast radius — measured 2026-09-16

| What | Detail |
| --- | --- |
| Files changed | `contracts/analyst.py` (**:30**), `agents/analyst/domain/stop_target.py` (**96**), `stop_target_outcome.py` (**57**), `agents/analyst/domain/recommend.py` (**193** 🚨), analyst + PM `laws.md`/`test-plan.md`, `agents/portfolio_manager/settings.py` (**133**), `reward_risk_detail.py` (**111**), `docs/laws/{ledger,INDEX,drift-register}.md`, `docs/design-log.md`, `docs/work-queue.md`, `pyproject.toml` |
| Agents affected | `analyst` **and** `portfolio_manager` — confirm neither imports the other |
| Contract change? | **YES** — `StopTargetEvidence`. Both law cycles are mandatory |
| Graph vocabulary change? | **Check before assuming.** New `Recommendation`/evidence properties may move `trading_graph_vocabulary.json`. If the pack moves, **the deploy is a full `up`, not a retag** |
| New env keys / tunables | Possibly one (design decision 1) — a new tunable also forces a full `up` |
| Deploy implication | **Decide from the two rows above and state it.** Do not assume retag |

🚨 **`recommend.py` has 7 lines of headroom.** If the wiring needs more, **split the module**; do not
grow it and do not `# noqa`.

---

## Steps, in order

1. **Read the laws** (MUST RULE) and write the Law reading record.
2. **Read ADR-0027 and ADR-0025.**
3. **Record the design decisions** in `docs/design-log.md`.
4. **Plant the failing tests first** and watch them fail. Paste the red output.
5. **Implement** — analyst derivation, contract field, PM threshold, structural label.
6. **Both law cycles** — clauses, versions, Changelog lines, test-plan rows, docstring citations, all
   four rollup lines, `DRIFT-066` if you find drift.
7. **Prove the guards can fail (DL-70)** — break each guard, watch it go red, restore.
8. **`make ci` green** — all 12 steps, **redirected to a file, never piped**.
9. **Fill the handback sections.**

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 the gate varies across candidates | two names with different excursion profiles | two **different** `reward_risk` values — today both are exactly 2.00 |
| A2 | 🎯 a poor-reward candidate is rejected when a positive floor is configured | measured upside below a positive configured fraction of stop risk | `outcome == FAILED` against an explicit positive floor |
| A3 | 🪤 the stop leg is unchanged | any candidate | `stop_pct` identical to the pre-change value, flat and scaled modes both |
| A4 | 🪤 the gate is no longer labelled structural | any evaluated candidate | `detail` does **not** contain `STRUCTURALLY_DETERMINED`; `PM-OBS-04`'s data-varying assertion holds |
| A5 | the target is auditable | any candidate | `StopTargetEvidence` carries the estimate, its window and its sample count |
| A6 | 🪤 no look-ahead | a candidate whose forward window has not settled | the estimate uses only bars **at or before** the decision day; the backfill value is never an input |
| A7 | insufficient bars | fewer bars than the window needs | the outcome of design decision 3, whichever way it was decided, and the evidence says which |
| A8 | the floor is the declared PARAM | `min_reward_risk_ratio` | the gate reads the tunable, not a literal — changing it to 2.0 changes the verdict |

🪤 **A3 and A6 are the two that catch real damage** — moving the stop, and leaking future information
into a decision. Neither is optional.

---

## Success factors

- [ ] `reward_risk` produces **more than one distinct value** across a multi-candidate fixture, and A1
      proves it.
- [ ] A candidate can be **rejected** by the gate when a positive floor is configured, and A2 proves it.
- [ ] Stop percentages are **byte-identical** to pre-change in both modes (A3).
- [ ] No `STRUCTURALLY_DETERMINED` for `reward_risk`; `PM-OBS-04` still green (A4).
- [ ] The decision-time estimate uses only bars at or before the decision day (A6).
- [ ] `min_reward_risk_ratio` is **0** with a restated `why=` and disclosure-only default.
- [ ] `StopTargetEvidence` records estimate, window and sample count.
- [ ] Analyst `laws.md` **v1.4 → v1.5**, PM **v1.6 → v1.7**, both with Changelog lines.
- [ ] All **four** rollup lines recomputed by the gate; report the numbers it gives.
- [ ] The unconditional-estimate limitation is **stated** in the handback, not papered over.
- [ ] Deploy implication (retag vs full `up`) **determined and stated**, with the pack diff as evidence.
- [ ] Every touched module **< 200** lines; report `recommend.py`'s new count.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The backfill is not the input.** `observed_drawdown` is computed after the horizon settles. Using
it to set today's target is look-ahead bias and would make every backtest look excellent and every live
run disappoint. A6 exists for this.

🪤 **`recommend.py` is at 193 of 200.** Split, don't grow.

🪤 **Changing the target changes the *stop* if you touch the shared helper.** `_scaled_target` currently
takes `scaled_stop` as an argument — removing that coupling is the point, but the stop path runs
through the same function's caller. A3 is the guard.

🪤 **A contract field can move the vocabulary pack.** If it does, the deploy is a **full `up`**, not a
retag — an image-only retag against a stale pack stalls the run mid-cascade, fail-closed (S148/DL-85).
**Check the pack hash; do not assume.**

🪤 **`DL-171` and `DRIFT-065` are spent.** Take 172 and 066, re-check at merge.

🪤 **`make ci | tail` reports `tail`'s exit code.** Redirect to a file and read the file.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current: `recommend.py` **193** 🚨, analyst `settings.py` **152** 🚨, PM `settings.py` **133**,
  `reward_risk_detail.py` **111**, `outcome_backfill.py` **102**, `stop_target.py` **96**,
  `stop_target_outcome.py` **57**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**, redirected to a file.
- Version bump **PATCH**, `uv.lock` staged. **Do not pin the digits.**
- Secrets never through the worktree — a worktree has **no `.env`**. 🟩 Every test here is in-memory;
  the live numbers are quoted above. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** — it ignores a `SHA=`
   argument. **Check the printed SHA against `git rev-parse HEAD`.**
2. Merge to `main` locally and push.
3. **Post-merge CodeQL** — `codeql.yml` runs only on `main`.
4. **Deploy per the blast-radius determination** — retag *or* full `up`, on the pack evidence.
5. **The live check.** After the next scheduled run, read the `reward_risk` details across the run's
   candidates and confirm **more than one distinct value**, at least one value away from 2.00, and no
   `STRUCTURALLY_DETERMINED`. Record in
   [`docs/laws/functionality-checks.md`](../laws/functionality-checks.md).
   🪤 **A run where every candidate happens to pass proves only that the gate was evaluated.** The
   evidence is the **spread of values**, not the verdicts. Quote them.

---

## Handover — paste this to Codex

```text
Branch `sprint-211-reward-risk-measured-quantities` off main. Never commit to main.

THE CLAIM: reward_risk compares two measured quantities.

READ FIRST, BEFORE ANY CODE:
  - docs/decisions/0027-reward-risk-compares-measured-upside-against-measured-downside.md
  - docs/decisions/0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md
  - agents/analyst/laws/laws.md           (WHOLE FILE, LOCKED v1.4)
  - agents/portfolio_manager/laws/laws.md (WHOLE FILE, LOCKED v1.6)
  - both laws/test-plan.md, docs/laws/conventions.md, docs/laws/drift-register.md
Then fill the "Law reading record" in the spec BEFORE your first code change.
If a law contradicts this spec, STOP and report - the law is more likely right.

THE DEFECT. agents/analyst/domain/stop_target.py:86:
    def _scaled_target(flat_stop, flat_target, scaled_stop):
        return min(flat_target * (scaled_stop / flat_stop), _MAX_PCT)
So target/stop == flat_target/flat_stop in BOTH modes - identically
base_take_profit_pct / base_stop_loss_pct = 2.00. Measured on the live spine: ONE distinct
value across 294 recordings, ZERO rejections ever. The target carries no per-name information;
reward_risk is a config check wearing a gate's clothes.

THE FIX:
1. Add a DECISION-TIME favourable-excursion estimate: the mirror of observed_drawdown
   (agents/analyst/domain/stop_target_outcome.py:29) - max(bar.high) instead of min(bar.low) -
   measured over PRIOR windows from bars the run already fetched.
2. Derive target_pct from it in resolve_stop_target, replacing _scaled_target's
   stop-times-base-ratio formula.
3. Extend StopTargetEvidence (contracts/analyst.py:30) with the estimate, its window and its
   sample count, so the target is auditable.
4. min_reward_risk_ratio (agents/portfolio_manager/settings.py:67) 1.5 -> 0, why= restated:
   it now records the BUILT target_pct / stop_pct ratio without rejecting by default.
5. reward_risk_detail.py:76 must stop returning STRUCTURALLY_DETERMINED for reward_risk.

WHY 0 AND NOT 0.80 OR 1.0: ADR-0027 Correction 2 / EXP-011 replayed 47,485 historical decisions and
found the built target_pct / stop_pct ratio does not predict returns (passed - rejected +0.03%,
confidence interval spanning zero). The returned positive floor would reject a median 49% of names
per night without improving selection. Operator ruled disclosure-only: record the ratio, do not reject
on it by default.

DO NOT:
  - DO NOT touch the stop leg. This sprint changes the TARGET only. _scaled_stop
    (stop_target.py:74) and every stop percentage stay exactly as they are. Test A3 is the guard.
    If your diff changes a stop value, stop and report.
  - DO NOT use observed_drawdown / the backfill as the decision input. It is computed AFTER the
    horizon settles (outcome_backfill.py). Using it is look-ahead bias. It is the CHECK on the
    estimate, never the estimate. Test A6 is the guard.
  - DO NOT make the floor relative (a percentile of the live distribution). ADR-0027 section 3
    rejects it explicitly and says changing it needs a NEW ADR.
  - DO NOT condition the estimate on the buy signal. The estimate is unconditional - what a name
    typically does, not what it does when the analyst likes it. DISCLOSE that limitation in the
    handback; do not hide or half-fix it.

ORDER OF WORK - failing tests FIRST. Two reds, pasted, before implementing:
  (a) two candidates with different excursion profiles produce DIFFERENT reward_risk values
      (today both are exactly 2.00);
  (b) a low-ratio candidate PASSES at the default with comparison=DISCLOSURE_ONLY, and the same
      class of candidate is REJECTED when an explicit positive floor is configured.

TWO LAW CYCLES ARE OWED - THIS IS HALF THE SPRINT:
  - contracts/ CHANGES (StopTargetEvidence). That alone makes both cycles mandatory. This is the
    S183 trap: a contract shape shipped under a LOCKED law book with no clause.
  - Analyst: a guarantee is new - target_pct now derives from a measured per-name quantity.
    ANLZ-OBS-05 (laws.md:214) governs the REALISED ADVERSE excursion and its horizon; nothing
    governs a decision-time FAVOURABLE estimate. laws.md v1.4 -> v1.5 + Changelog.
  - PM: the threshold moves AND the gate stops being structurally fixed. PM-OBS-04 already says
    "a data-varying gate must not be labelled structurally fixed", so leaving the label in place
    becomes a violation the moment the target varies. laws.md v1.6 -> v1.7 + Changelog.
  - test-plan.md rows for every clause touched; clause IDs in every new test docstring.
  - Let `make ci` recompute ALL FOUR rollup lines: docs/laws/ledger.md line 40 (analyst, now
    25/48) and line 42 (PM, now 30/49), docs/laws/INDEX.md line 41 and line 43. Report what the
    gate gives; do not hand-edit to match.

THREE DESIGN DECISIONS - record in docs/design-log.md with rejected alternatives BEFORE coding:
  1. The lookback for the estimate. stop_target_drawdown_horizon_days (10) is the FORWARD horizon
     for the realised backfill and its PARAM row says so. How many PRIOR windows the decision-time
     estimate samples is a different quantity. Reusing that tunable overloads a declared PARAM
     whose description would then be wrong. Either add a tunable with its own why=, or reuse and
     correct the PARAM row. Pick one and say why.
  2. The estimator. The ADR measured MEDIAN of per-window excursions. Mean or a percentile gives
     different numbers. If you choose differently, the ADR's measured table no longer describes
     what you shipped - say so.
  3. What happens when there are too few bars. PM-NEV-09's shape says an un-evaluable gate is
     NOT_EVALUATED, never passed. Decide whether the analyst falls back to the old constant target
     or declines to propose, and make the evidence say which.

TRAPS, named because a trap you do not write down gets hit:
  - recommend.py is 193 lines against a 200 HARD BLOCK - 7 lines of headroom. SPLIT, don't grow.
    analyst/settings.py is 152, also in the warn zone.
  - _scaled_target currently TAKES scaled_stop as an argument. Removing that coupling is the
    point, but the stop path runs through the same caller. A3 is the guard.
  - A CONTRACT FIELD CAN MOVE THE VOCABULARY PACK. If orchestration/packs/
    trading_graph_vocabulary.json moves, the deploy is a FULL `up`, NOT an image-only retag - a
    new image against a stale pack stalls the run mid-cascade, fail-closed (S148/DL-85). CHECK THE
    PACK HASH and state the deploy implication in the handback. Do not assume retag.
  - DL-171 and DRIFT-065 are spent by S210. Take DL-172 and DRIFT-066, re-check both at merge.
  - make ci | tail reports tail's exit code. Redirect to a FILE and read the file.

Everything here is in-memory; a worktree has no .env and you do not need one.
Version: next available PATCH. DO NOT PIN THE DIGITS. Stage uv.lock with the bump.
Fill the Handback contract: Law reading record, Test plan results, Closeout evidence with REAL
pasted output (red runs first, then green), Return notes, Status: BUILT. A placeholder left
unfilled is returned, not repaired.
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

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| Analyst stop/target derivation: `agents/analyst/domain/stop_target.py`, `stop_target_outcome.py`, `settings_stop_target.py` | `agents/analyst/laws/laws.md` LOCKED v1.4; `agents/analyst/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md`; ADR-0027 | `ANLZ-OUT-07`, `ANLZ-OUT-08`, `ANLZ-TYP-01`, `ANLZ-TYP-02`, `ANLZ-OBS-03`, `ANLZ-OBS-05`, PARAM rows for stop/target settings | Yes. `ANLZ-OUT-07` currently asserts lockstep target scaling, so the target change must amend the law rather than hide under the old clause. The adverse-outcome clause is adjacent only; a new decision-time favourable-estimate clause is needed. |
| Analyst recommendation graph evidence: `contracts/analyst.py`, `agents/analyst/recommendation_props.py`, vocabulary pack | Same analyst laws/test-plan plus `docs/laws/INDEX.md` and `docs/laws/ledger.md` rollup rows | `ANLZ-TYP-01`, `ANLZ-OBS-03`, `ANLZ-OBS-05`, conventions §§3, 7, 7a | Yes. The contract field change is in scope and forces the law cycle; new Recommendation properties also force vocabulary-pack proof and deploy-path disclosure. |
| PM reward-risk gate and PARAM: `agents/portfolio_manager/settings.py`, `domain/gate_report.py`, `domain/reward_risk_detail.py` | `agents/portfolio_manager/laws/laws.md` LOCKED v1.6; `agents/portfolio_manager/laws/test-plan.md`; ADR-0027; ADR-0025 | `PM-NEV-04`, `PM-OBS-04`, `PM-TYP-03`, `PM-OUT-03`, PARAM row for `min_reward_risk_ratio`; `PM-NEV-09` as the tri-state evidence shape | Yes. Once the target varies, `STRUCTURALLY_DETERMINED` becomes false for current analyst evidence. The floor change belongs with the derivation and must stay a tunable read, not a literal. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?**

Yes, twice. `contracts/analyst.py` changes `StopTargetEvidence`, and the analyst adds a new guarantee:
decision-time target evidence is derived from measured trailing favourable excursion. PM behaviour also
changes because `min_reward_risk_ratio` moves to `0` and the reward-risk gate becomes disclosure-only by
default while still rejecting below a positive configured floor. Analyst laws move v1.4 -> v1.5; PM laws
move v1.6 -> v1.7.

**Contradictions found between a law and this spec:**

No blocking contradiction. The current analyst law `ANLZ-OUT-07` deliberately describes the old
lockstep target guarantee; S211 amends it because ADR-0027 supersedes that invariant. No locked law
forced a different target derivation or threshold than the sprint specifies.

**Laws found silent where a decision was needed:**

Analyst laws are silent on decision-time favourable-excursion target estimates: the existing
`ANLZ-OBS-05` governs realised adverse backfill only. S211 will add a new clause and test-plan row
rather than file separate drift. PM laws do not need a new silence row for structural disclosure:
`PM-OBS-04` already covers data-varying gates not being labelled structurally fixed.

**Clauses that were ⬜ and are now proven:**

`ANLZ-OBS-06` is new and green: decision-time favourable-excursion target evidence is measured from
prior settled windows, serialized, and missing evidence rejects instead of falling back to a constant
target. `PM-OBS-05` is new and green: reward-risk varies with measured target evidence, discloses the
target basis/sample inputs, defaults to disclosure-only, and still rejects below-floor built ratios when
a positive floor is explicitly configured.
Rollups now read
analyst **26 / 49** and PM **31 / 50** in both `docs/laws/ledger.md` and `docs/laws/INDEX.md`.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_reward_risk_varies_across_measured_excursion_profiles` | `agents/portfolio_manager/tests/test_reward_risk_measured_excursion.py` | 🟩 | `ANLZ-OBS-06`, `PM-OBS-05` |
| A2 | `test_positive_reward_risk_floor_still_rejects_below_floor` | `agents/portfolio_manager/tests/test_reward_risk_measured_excursion.py` | 🟩 | `ANLZ-TYP-02`, `ANLZ-OBS-06`, `PM-OBS-05`, `PM-NEV-04` |
| A3 | `test_measured_target_evidence_keeps_stop_values_unchanged` | `agents/analyst/tests/test_measured_stop_targets.py` | 🟩 | `ANLZ-OBS-06`, `ANLZ-TYP-01` |
| A4 | `test_positive_reward_risk_floor_is_informative_not_structural` | `agents/portfolio_manager/tests/test_reward_risk_measured_excursion.py` | 🟩 | `PM-OBS-04`, `PM-OBS-05` |
| A5 | `test_measured_target_evidence_keeps_stop_values_unchanged` | `agents/analyst/tests/test_measured_stop_targets.py` | 🟩 | `ANLZ-OBS-06`, `ANLZ-TYP-01` |
| A6 | `test_trailing_favorable_estimate_uses_only_prior_settled_windows` | `agents/analyst/tests/test_stop_target_outcome.py` | 🟩 | `ANLZ-OBS-06` |
| A7 | `test_trailing_favorable_estimate_is_absent_until_one_window_settles`; `test_unavailable_measured_target_is_rejected_not_flattened` | `agents/analyst/tests/test_stop_target_outcome.py`; `agents/analyst/tests/test_measured_stop_targets.py` | 🟩 | `ANLZ-OBS-06`, `ANLZ-OUT-03` |
| A8 | `test_default_reward_risk_floor_is_disclosure_only`; `test_low_measured_reward_risk_passes_by_default_as_disclosure`; `test_reward_risk_floor_is_read_from_the_tunable_value` | `agents/portfolio_manager/tests/test_reward_risk_measured_excursion.py` | 🟩 | `PM-NEV-04`, `PM-OBS-04`, `PM-OBS-05` |

**Tests added beyond the plan:**

- `agents/analyst/tests/test_p2_slice.py::test_full_p2_slice_produces_recommendation_with_complete_lineage`
  and `agents/portfolio_manager/tests/test_p3_slice.py::test_full_p3_slice_produces_order_intent_with_complete_lineage`
  were fixture-updated so the integration slices carry enough prior bars to produce measured target
  evidence.
- `tests/test_contract_required_payload_fields.py::test_analyst_payload_fields_required_by_law` and
  `tests/test_graph_vocabulary_completeness.py::test_recommendation_props_are_declared_in_trading_pack_vocabulary`
  now cover the new `StopTargetEvidence` fields and graph-vocabulary properties.

---

## Closeout — evidence

**Status:**

BRANCH-GATED; merge/deployment/live proof remain pending below.

**Tree the proofs ran in (and `.env` present?):**

`C:\Users\yury_\Downloads\project\trading-agents-sprint-211-reward-risk-measured-quantities`,
branch `sprint-211-reward-risk-measured-quantities`. `Test-Path .env` returned `False`.

**Result:**

`reward_risk` now divides measured target evidence by measured stop risk and records the ratio in every
gate report. Two measured profiles produce different `reward_risk` values; a low-ratio profile passes by
default with `comparison=DISCLOSURE_ONLY`; an explicit positive floor still rejects below-floor
ratios; non-positive stops still reject as `invalid_stop_loss`; the stop leg remains unchanged in both
flat and scaled modes.

**Files changed:**

Analyst stop/target derivation and evidence (`agents/analyst/domain/*`, `settings_stop_target.py`,
`recommendation_props.py`, analyst tests/laws), PM reward-risk detail/settings/tests/laws,
`contracts/analyst.py`, graph vocabulary, law rollups, design log, work queue, sprint handback, version
files.

**Design decisions:** recorded as `DL-172`

`DL-172` in `docs/design-log.md`: separate `stop_target_excursion_lookback_windows` tunable; median of
prior settled favourable-excursion windows; missing estimate rejects rather than falling back to the old
constant target; ADR-0027 Correction 2 / EXP-011 make the PM floor disclosure-only by default.

**Deploy implication (retag or full `up`), with the pack-hash evidence:**

Full `up` required. Evidence: `orchestration/packs/trading_graph_vocabulary.json` changed to add four
`stop_target_favorable_excursion_*` Recommendation properties, and two tunables changed/added:
`stop_target_excursion_lookback_windows` and `min_reward_risk_ratio=0`. A retag would ship a stale pack.

**Proof — the red runs first:**

```text
uv run pytest agents\portfolio_manager\tests\test_reward_risk_measured_excursion.py agents\portfolio_manager\tests\test_reward_risk.py --no-cov

FAILED agents/portfolio_manager/tests/test_reward_risk_measured_excursion.py::test_default_reward_risk_floor_is_disclosure_only
  assert 0.8 == 0.0
FAILED agents/portfolio_manager/tests/test_reward_risk_measured_excursion.py::test_low_measured_reward_risk_passes_by_default_as_disclosure
  IndexError: tuple index out of range
2 failed, 11 passed in 1.46s
```

**Proof — the green run:**

```text
uv run pytest agents\portfolio_manager\tests\test_reward_risk_measured_excursion.py agents\portfolio_manager\tests\test_reward_risk.py tests\test_param_law_sync.py --no-cov

18 passed in 1.39s

uv run pytest agents\analyst\tests agents\portfolio_manager\tests agents\execution\tests\test_p3_execution_slice.py agents\monitor\tests\test_p3_monitor_slice.py agents\reporter\tests\test_p3_reporter_slice.py orchestration\tests\test_batch_trace.py orchestration\tests\test_drop_sweep_cascade.py orchestration\tests\test_forecaster_stage.py orchestration\tests\test_graph_pull_e2e.py orchestration\tests\test_p4_celery_parity.py orchestration\tests\test_p4_daily_loop.py orchestration\tests\test_pm_rejection_rendering.py orchestration\tests\test_trading_acceptance_deliberation.py orchestration\tests\test_trading_acceptance_outcomes.py orchestration\tests\test_trading_observatory.py orchestration\tests\test_unified_decision_run.py orchestration\tests\test_veto_stage.py surfaces\tests\test_dashboard_bundle.py surfaces\tests\test_dashboard_projections.py tests\test_contract_required_payload_fields.py tests\test_graph_vocabulary_completeness.py tests\test_contract_values.py tests\test_param_law_sync.py --no-cov

639 passed in 12.66s

uv run ruff check agents\portfolio_manager\settings.py agents\portfolio_manager\domain\reward_risk_detail.py agents\portfolio_manager\domain\gate_report.py agents\portfolio_manager\tests\test_reward_risk_measured_excursion.py agents\portfolio_manager\tests\test_reward_risk.py
All checks passed!

uv run python scripts\check_law_coverage.py
exit 0

uv run python scripts\check_module_size.py
exit 0
```

**Guards planted:**

Red-first A1/A2 reward-risk guards, A3 stop-unchanged guard, A4 non-structural reward-risk detail guard,
A5 evidence serialization guard, A6 no-lookahead favourable-excursion guard, A7 missing-estimate rejection
guard, A8 disclosure-default and tunable-floor guards, plus the explicit-positive-floor guard proving a
configured floor still rejects below it.

**Module line counts:**

`recommend.py` 166; `scoring.py` 162; `target_excursion_metrics.py` 34; `stop_target.py` 122;
`stop_target_outcome.py` 89; `reward_risk_detail.py` 117;
`test_reward_risk_measured_excursion.py` 146; `test_reward_risk.py` 132.

**`make ci`:** redirected to `C:\Users\yury_\AppData\Local\Temp\s211-disclosure-make-ci.log`.
Exit code `0`.

```text
make ci *> C:\Users\yury_\AppData\Local\Temp\s211-disclosure-make-ci.log
exit=0

Success: no issues found in 917 source files
Contracts: 4 kept, 0 broken.
Required test coverage of 100.0% reached. Total coverage: 100.00%
2796 passed, 6 skipped in 87.37s (0:01:27)
No known vulnerabilities found
Detect secrets...........................................................Passed
detect-secrets (untracked): no untracked files to scan
```

**`make gate-ran`:**

Completed from this S211 worktree after push. Exact final SHA proof is reported in the chat handback
because committing that printed SHA would move the SHA being proven.

**Not met / verified failing:**

Merge, deployment, and live scheduled-run proof are not done in this branch handback. The below-floor
policy remains unconditional by ADR-0027 design: the target estimate is not
conditioned on the analyst buy signal, and this limitation is disclosed rather than hidden.
---

## Merge and deploy — planning agent, 2026-09-17

**Merge:** `make gate-ran` from the S211 worktree printed `GATE PROVEN for
5dc9d1c9e8852048751c159aba21b5ceabedf489` (CI + Security Findings success), matching `git rev-parse HEAD`.
Merged `--no-ff` to `main` as `7d3ff519c06fd7df9ad38da38508e41b506dbb12` (`0.98.08`, tag `v0.98.08`).
Post-merge CodeQL: success on `7d3ff51`.

**Images:** manual `build-images.yml` run `35217747046`, dispatched on ref `v0.98.08` (= `7d3ff51`) with
`image_tag=s211`: 15/15 jobs success.

**Deploy:** `pwsh -NoProfile -File infra\deploy-agents.ps1 up -Tag s211` exited `0`:

- preflight: per-target DSNs 17/17, Service Bus SAS 16/16, GHCR images 15/15;
- env preserved on all 17 targets; `alembic upgrade head`; served topics and subscriptions;
- master, 15 agents and `dispatcher-cron` (`30 22 * * 1-5` UTC) all `[OK]`.

Readback: pre-deploy 16/16 apps on `s210`; post-deploy **16/16 apps on `s211`, all `Succeeded`**, and
`dispatcher-cron` on `s211`, `Succeeded`.

🟠 **No `DeployRecord` was written.** `scripts/record_deploy.py` refused (*"GitHub build evidence is required"*)
because its reader only accepts image-build runs on branch `main`
(`surfaces/dashboard/github_builds.py`, `_successful_main_image_runs`). This build was dispatched on the tag
ref at the same SHA. Rebuilding from `main` would have stamped the later docs commit `c035592` as the
deployed SHA, which is less truthful than no record. Next time, dispatch the `s<NN>` build on `main` while
`main` still equals the merge commit.

**Still owed: the live check** (Sequencing step 5), on the first scheduled run on `s211`
(`sched-2026-09-17`, 22:30 UTC):

- more than one distinct `reward_risk` value across candidates;
- `comparison=DISCLOSURE_ONLY` at threshold 0;
- no rejection reason `reward_risk_below_min`;
- no `STRUCTURALLY_DETERMINED` on measured evidence.
Record it in `docs/laws/functionality-checks.md`.

## Return notes

- The target estimate is unconditional recent behaviour, not evidence conditioned on the analyst liking the
  name. That is the known limitation ADR-0027 accepted.
- The graph vocabulary and tunables moved, so deployment is full `up`; do not retag an image against the old
  pack.
- Work-queue item 60 is closed as built by S211; deployment/live proof still remains a separate state.
- ADR-0027 Correction 2 / EXP-011 supersede the returned `0.80` default: the default is disclosure-only,
  and a positive floor needs new predictive evidence before it is enabled again.
