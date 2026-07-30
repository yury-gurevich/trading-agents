<!-- Agent: planning | Role: sprint handover -->
# Sprint 150 — The same 5 % stop is 2.4 ATRs for BAC and 0.6 for MRVL

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-150-volatility-scaled-stops`
**Status:** SPEC — measured challenger to the flat stop distance; **ships OFF by default**
**Version:** feat → **0.84.00** (MINOR; `0.83.00` is S149)
**Effort:** M
**Depends on:** **S149 must be merged first.** It adds the PM-side `atr_pct` extraction this sprint
builds on, and the two would otherwise collide in the portfolio manager.
**Decisions:** [ADR-0013](../decisions/0013-continuous-improvement-system.md) **(an ADR-0013
experiment: measured, never auto-promoted)** ·
[ADR-0015](../decisions/0015-exit-lifecycle-and-stop-ownership.md) the broker enforces the stop ·
[ADR-0017](../decisions/0017-exit-authority-alpha-proposes-risk-disposes.md) **alpha proposes, risk
disposes — this sprint changes a *proposal*, not the disposal** · [DL-76](../design-log.md) the
flat-band finding · [DL-70](../design-log.md) plant violations ·
[DL-57](../design-log.md)/[DL-59](../design-log.md) intent ≠ outcome

> **This sprint does not change how the fleet trades.** The challenger ships **off**; promotion is
> an operator config flip after measured evidence. That matters more here than in S149 — this is a
> **risk** parameter, and a stop that changes width without evidence is not an improvement, it is a
> different bet.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

### What the law folders are

This repo is governed by a **law book** — not documentation, not advisory. It is the constitution the
code must satisfy, and it outranks this sprint document.

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** — clause IDs `<AGENT>-<SECTION>-<NN>` | **LOCKED v1. Read-only. Never edit.** A clause you believe is wrong is a drift-register row plus a report |
| `agents/<name>/laws/test-plan.md` | The clause-by-clause test map: proven (🟩) vs unproven (⬜) | Read it to learn whether what you are changing is *proven* or merely asserted |
| `docs/laws/*.md` | The **umbrella laws** — conventions, dependencies, drift register, ledger, functionality checks | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Clause **sections**: `IDN` · `IN` · `TRG` · **`OUT`** · **`NEV`** · `STA` · **`IDM`** · `ORD` ·
**`FAIL`** · `TYP` · `SEC` · `DEP` · `OBS` · `PERF` · `CAP` · **`PARAM`**.

For **this** sprint the binding sections are **`OUT`** (the analyst owns `suggested_stop_pct` — is
making it volatility-aware still within its declared output, or does it become a risk decision?),
**`NEV`** (the analyst must not start disposing risk; the PM must not start deciding alpha),
**`PARAM`**, and **`IDM`**.

**Read `ADR-0017` before you decide where the scaling lives.** "Alpha proposes, risk disposes" is the
line this sprint runs along, and getting it wrong is a boundary violation, not a style choice.

### The rule

1. **Before writing code**, for **every** element below, open and read its law file(s) in full.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Also read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Write the Law reading record** (template near the bottom) **before** your first code change.
5. **If a law contradicts this spec, STOP and report.** **A contradiction you surface is a success.**
   This spec proposes the analyst as the home for the scaling; **if the laws say it belongs to the
   PM, say so and stop** — that is exactly the kind of finding this gate exists for.
6. **If a law is silent** where you must decide, record it and add a `drift-register.md` row.
7. Every test for behaviour a clause governs **must cite the clause ID in its docstring**.

### Element → law map (read all of these)

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/analyst/domain/recommend.py` — `suggested_stop_pct` / `suggested_target_pct` (items 1, 2) | `agents/analyst/laws/laws.md` + `test-plan.md` + ADR-0017 | `ANLZ-OUT-*` declares what the analyst emits; `ANLZ-NEV-*` — a volatility-aware stop suggestion must stay a *proposal* |
| `agents/analyst/settings*.py` — mode + tunables (items 1, 2) | `agents/analyst/laws/laws.md` (**`PARAM` section**) + `docs/laws/conventions.md` | Four sprints running, execution's `PARAM` section has lagged its code (DRIFT-024/025/026/027). **Check the analyst's before you assume it is better** |
| `agents/portfolio_manager/domain/gate_report.py` — the RR gate (**item 3, the trap**) | `agents/portfolio_manager/laws/laws.md` + `test-plan.md` | `PM-NEV-04` and the risk gates. **This is where a naive change silently stops trading volatile names** |
| `contracts/analyst.py` (**read-only unless genuinely required**) | `agents/analyst/laws/laws.md` | `suggested_stop_pct` already exists and is already optional; you very likely need no contract change |
| `agents/monitor/` + `contracts/positions.py` (**read-only — see non-goals**) | `agents/monitor/laws/laws.md` | `MON-IDN-02` owns `Position`. Existing positions keep their recorded `stop_pct`; **this sprint must not re-price a live stop** |
| `orchestration/packs/trading_graph_vocabulary.json` (item 6) | `docs/laws/conventions.md` | Any new prop must be declared. **Note S149 extended the guard to enforce node *properties* for `Fill`** — check whether your new props land on a property-enforced label |

### What the trial is measuring

The law-first rule has run four times ([DL-74](../design-log.md)): DRIFT-024 (S146), DRIFT-025 plus a
reporter defect caught pre-code (S147), DRIFT-026 (S148), DRIFT-027 (S149). Answer honestly per
element: **did reading the law change what you were going to do?** "No — the intended approach
already complied" is a good answer. A record that is vague, or written after the code, defeats the
trial (DL-48).

---

## Why this sprint

Every position in the book gets the **same** stop distance.
[`recommend.py:172`](../../agents/analyst/domain/recommend.py#L172) sets
`suggested_stop_pct = regime.base_stop_loss_pct` for every buy — a single global tunable, currently
**5 %**. The PM's fallback is the same number.

I measured what that actually means. For each held name plus AMD and MRVL, over ~65 sessions: the
14-day ATR as a percent of price, and how often the day's low fell more than 5 % below the prior
close — i.e. **how often a flat 5 % stop is touched**:

| Ticker | ATR % | Flat 5 % stop touched | 2 × ATR stop touched | 2 × ATR width |
| --- | --- | --- | --- | --- |
| BAC | 2.1 % | 0.0 % | 0.0 % | 4.1 % |
| USB | 2.1 % | 0.0 % | 0.0 % | 4.1 % |
| WFC | 2.3 % | 0.0 % | 3.0 % | 4.7 % |
| SCHW | 2.5 % | 1.5 % | 1.5 % | 4.9 % |
| ABT | 2.5 % | 0.0 % | 0.0 % | 5.1 % |
| CSCO | 3.2 % | 6.1 % | 1.5 % | 6.4 % |
| **HPE** | **5.5 %** | **19.7 %** | 0.0 % | 11.0 % |
| **AMD** | **6.4 %** | **36.4 %** | 1.5 % | 12.8 % |
| **MRVL** | **8.5 %** | **39.4 %** | 1.5 % | 17.1 % |

**A 5 % stop on MRVL is 0.6 ATRs — inside a single day's normal range.** It is touched on ~39 % of
days by ordinary noise. That is not a protective floor; it is a near-certainty that any MRVL position
exits within days regardless of thesis. The same 5 % on BAC is **2.4 ATRs** and is touched on 0 % of
days.

So "5 % stop" is not one policy. It is a different risk appetite per ticker, chosen by accident.
A 2 × ATR stop equalises it: every name lands at 0–3 %, with the *width* varying from 4.1 % to
17.1 % — which is what holding risk constant actually looks like.

### An honest check that did not support the story

The obvious narrative is that MRVL's 07-27 forced stop (−$1,330.12, the ADR-0018 trigger) was a
noise stop-out caused by exactly this defect. **I checked, and it was not.** MRVL closed at
`$189.28` on 07-27, `$174.36` on 07-28, and `$163.39` on 07-29 — **16.6 % below the `$195.98` exit**.
That stop was correct and it saved money.

The statistical finding stands on its own without that anecdote, and the sprint is not justified by
it. Recorded here because a convenient story that fails its check is worth more than one that was
never tested (DL-70's spirit).

---

## 🚨 The trap: the reward-risk gate is coupled to the stop

**Read this before writing any code.**

[`gate_report.py:125`](../../agents/portfolio_manager/domain/gate_report.py#L125) computes:

```python
ratio = 0.0 if stop_pct <= 0.0 else target_pct / stop_pct
passed = stop_pct > 0.0 and ratio >= min_ratio
```

`suggested_target_pct` comes from `regime.base_take_profit_pct` — **also flat**. So if you widen
`stop_pct` for volatile names and leave `target_pct` alone, the ratio collapses exactly where the
stop widened most, and **AMD, MRVL and HPE silently stop passing the reward-risk gate and stop being
traded at all.**

That failure is invisible: no error, no fault, no dropped decision — just approvals quietly ceasing
for the names whose stops you "improved". The tests would pass. The book would slowly become
low-volatility-only, and nobody would know why.

**Both must scale together**, and the RR ratio must be **provably invariant** to the mode when
target and stop scale by the same factor (test C1). If you find a reason they should *not* scale
together, that is a finding — report it, do not implement it silently.

---

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it. Results go in this file.

### 1 · A selectable, volatility-scaled stop proposal

- Add a mode: **`flat`** (champion, **the default**) | **`scaled`** (challenger). Nothing about
  production changes until an operator flips it.
- `flat` → exactly today's behaviour, `regime.base_stop_loss_pct`. Do not alter it.
- `scaled` → `clamp(k × atr_pct, floor_pct, ceiling_pct)`, with **`k`, `floor_pct`, `ceiling_pct`
  each a `kernel.tunable(..., why=..., ge=..., le=..., unit=...)`** — never literals.
- Calibration from the table above: **2 × ATR** equalises touch rates across the book. Start there
  or nearby, and **say what you chose and why** in the closeout. Do not tune to a target.
- **Where this lives:** this spec proposes the **analyst**, because it already owns
  `suggested_stop_pct` and already computes `atr_pct`, and because ADR-0017 makes the analyst the
  *proposer* while the PM disposes. **Verify that against the laws first** (MUST RULE step 5). If
  the constitutions put it on the PM, stop and report.
- The PRD risk cap still binds: `base_stop_loss_pct` is bounded `le=0.08` today. **A scaled stop
  must not silently exceed the maximum risk the system is allowed to take** — that is what
  `ceiling_pct` is for, and it is a safety rail, not a tuning knob.

**Result:**
Implemented in the analyst proposal path, behind `AnalystSettings.stop_target_mode` with default
`flat`. `flat` keeps the existing `regime.base_stop_loss_pct` and
`regime.base_take_profit_pct` behaviour. `scaled` resolves
`clamp(k * atr_pct, floor_pct, ceiling_pct)` through `kernel.tunable` settings:
`scaled_stop_atr_multiplier=2.0`, `scaled_stop_floor_pct=0.025`,
`scaled_stop_ceiling_pct=0.08`. The scaling lives in the analyst as a proposal; PM gates still
dispose risk. `DRIFT-028` records the analyst law silence around the new mode/tunables/evidence.

### 2 · Scale the target in lockstep — or the RR gate becomes a volatility filter

- When the mode is `scaled`, `suggested_target_pct` scales by **the same factor** applied to the
  stop, so `target_pct / stop_pct` is unchanged.
- The reward-risk gate must therefore reach **the same verdict in both modes** for the same
  recommendation. That is the invariant, and it is what stops item 1 from quietly killing the
  volatile half of the book.

**Result:**
Implemented in lockstep: the target is multiplied by the same factor as the stop whenever scaled
mode is active, preserving `target_pct / stop_pct`. The PM RR gate was not changed; new PM tests
prove the same recommendation reaches the same reward-risk verdict in flat and scaled modes, and
that stop-only scaling is the planted failure.

### 3 · A missing ATR degrades to flat — it never blocks a recommendation

- No `atr_pct` (short history, new listing, a name with too few bars) → fall back to the flat stop
  and **record that the fallback happened**.
- **Never** suppress, skip or reject a recommendation because volatility is missing. A missing input
  is a degraded input, not a veto (`ANLZ-FAIL-*`, DL-57).
- A nonsensical `atr_pct` (zero, negative, absurd) is clamped or treated as missing — never
  produces a nonsense stop.

**Result:**
Implemented. Missing, zero, negative, and non-finite `atr_pct` degrade to the flat stop/target and
record `volatility_fallback=True`; they do not suppress or downgrade a recommendation. Extreme ATR
values clamp at the configured floor/ceiling.

### 4 · Record the counterfactual — this is what makes it an experiment

- On every buy recommendation, record **both** stop/target pairs: the applied one and the one the
  *other* mode would have produced, plus the mode in force and the `atr_pct` used. Append; never
  rewrite.
- Record whether the ATR was present or fell back.
- Extend or add a comparison script (`scripts/`, alongside `compare_order_tolerances.py`) that
  reports per mode: proposed stop width distribution, RR-gate pass rate, and — where the outcome is
  known — how often each stop **would have been touched**. That output is the evidence an operator
  promotes on.
- The script **reports**; it never promotes and never writes a settings change (ADR-0013).

**Result:**
Implemented as an additive optional `Recommendation.stop_target_evidence` contract field and
persisted `Recommendation` graph properties. Every buy records applied and counterfactual
stop/target pairs, mode, counterfactual mode, ATR value, and fallback flags. The comparison script
`scripts/compare_stop_targets.py` reads only and reports flat/scaled stop-width distribution,
RR pass rate, known outcome counts, and would-touch rate where `stop_target_observed_drawdown_pct`
is present. It performs no settings writes and no promotion.

### 5 · Do not touch a live position's stop

- Existing `Position` nodes keep their recorded `stop_pct`. **This sprint must not re-price,
  cancel, or replace any resting broker stop** — nine are live right now and they are the floor
  ADR-0018 depends on.
- The change applies to **new** proposals only. Prove it: an existing position with a recorded
  `stop_pct` is unaffected by a mode flip.

**Result:**
Proven without changing monitor or position contracts. S150 adds no live-position repricing path:
existing `Position.stop_pct` and `BrokerStopOrder` rows remain untouched under a scaled-mode
analyst run. The S148 drop-sweep stop-safety test was rerun verbatim and continues to exempt
resting broker stops.

### 6 · Declare any new prop in the vocabulary

- New props go in [`trading_graph_vocabulary.json`](../../orchestration/packs/trading_graph_vocabulary.json).
- **Note:** S149 extended the guard to enforce declared **node properties** (currently for `Fill`
  only). If your new props land on a property-enforced label, an undeclared one now throws. Re-run
  `scripts/vocabulary_coverage.py` and `scripts/vocabulary_signatures.py`; paste the output.

**Result:**
Declared the durable `Recommendation` stop-target evidence props in
`orchestration/packs/trading_graph_vocabulary.json` and extended the completeness test so an
undeclared `stop_targt_mode` typo is rejected. Both vocabulary scripts exited 0 with no output;
`tests/test_graph_vocabulary_completeness.py` passed 8/8.

### 7 · Prove the checks can fail (DL-70)

Plant the violation and require the failure — the plan below specifies the violation for each test.

**Result:**
Done. The tests plant the failure modes the sprint names: stop-only scaling fails the RR gate,
sub-floor and absurd ATR values must clamp, bare literal settings fail tunable metadata checks,
missing ATR cannot suppress the recommendation, one-sided evidence is caught, read-only comparison
fakes fail on writes, live-position repricing is detected, and undeclared graph props are rejected.

---

## Test plan — every test I want, and why

**Ground rules.** Every test cites its clause ID(s) and **plants the violation**. Names are
descriptive, not prescriptive. **If a test is wrong or untestable, say so with a reason.**

### A · The scaled proposal

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | `flat` mode is unchanged | mode `flat`, any `atr_pct` | `suggested_stop_pct == regime.base_stop_loss_pct` exactly; **the ATR is ignored entirely** |
| A2 | `scaled` widens a volatile name | `atr_pct` ≈ MRVL's 8.5 % | stop equals `k × atr_pct` exactly (assert the value, not just "bigger") |
| A3 | `scaled` narrows a quiet name | `atr_pct` ≈ BAC's 2.1 % | stop is smaller than A2's; assert the exact value |
| A4 | the floor clamps | `atr_pct` near zero | stop == `floor_pct`. Plant a sub-floor value and require the clamp |
| A5 | 🚨 the ceiling clamps below the risk cap | an absurd `atr_pct` | stop == `ceiling_pct` **and** never exceeds the PRD/`base_stop_loss_pct` maximum. Plant a value that would blow past it |
| A6 | the knobs are declared tunables | — | `k`, `floor_pct`, `ceiling_pct` each a `kernel.tunable` with `why`/`ge`/`le`/`unit`. Plant a bare literal and require rejection |
| A7 | resolution is deterministic | same inputs twice | identical stop and target (`ANLZ-IDM-*`) |
| A8 | the mode is bounded | an invalid mode string | rejected at settings validation, not silently treated as flat |

### B · Degradation

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| B1 | missing ATR falls back to flat | mode `scaled`, no `atr_pct` metric | the flat stop is used, the recommendation is **still produced**, the fallback is recorded |
| B2 | 🚨 a missing ATR never suppresses a recommendation | mode `scaled`, no ATR | the recommendation is not dropped, downgraded or rejected. **Plant the suppressing behaviour and require the failure** |
| B3 | a nonsensical ATR is clamped, not trusted | zero / negative / absurd `atr_pct` | clamped or treated as missing; never a nonsense stop |
| B4 | sells are unaffected | a sell recommendation | `suggested_stop_pct` stays `None` for sells, both modes — today's behaviour |

### C · 🚨 The reward-risk gate

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| C1 | 🚨 **the RR verdict is mode-invariant** | the same recommendation under both modes | `target_pct / stop_pct` and the gate verdict are **identical**. **This is the test that stops the sprint silently killing the volatile half of the book** — if one test here survives a refactor, make it this one |
| C2 | 🚨 a volatile name still passes the gate | `atr_pct` ≈ MRVL's, mode `scaled` | the RR gate **passes**. Plant a stop-only scaling (target left flat) and **require this test to fail** — that is the trap, planted and caught |
| C3 | the PM fallback still works | a recommendation with `suggested_stop_pct=None` | the PM's `default_stop_pct` path is unchanged |
| C4 | RR threshold behaviour is untouched | a genuinely poor RR setup | still rejected, both modes — the sprint must not weaken the gate |

### D · The counterfactual record

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| D1 | both stop/target pairs are recorded | one recommendation, `flat` mode | applied **and** counterfactual stop/target, the mode, and the `atr_pct` used |
| D2 | the record is symmetric | the same under `scaled` | the flat counterfactual is recorded. **Plant a one-sided implementation and require the failure** |
| D3 | the record is append-only | re-record for the same recommendation | no in-place rewrite |
| D4 | the comparison script reports both modes | a window with both modes | stop-width distribution, RR pass rate, and touch counts per mode. Plant a window where the modes differ and require the difference to show |
| D5 | the script never promotes | run it | no settings write, no mode flip (ADR-0013) |

### E · Live positions and vocabulary

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| E1 | 🚨 an existing position keeps its stop | a `Position` with a recorded `stop_pct`, then flip the mode | the position's `stop_pct` is **unchanged** and no stop is re-priced, cancelled or replaced |
| E2 | 🚨 no resting broker stop is disturbed | S148's stop fixture, mode flipped | every resting stop survives untouched. **Re-run S148's stop-safety test verbatim** |
| E3 | new props are declared | the new evidence props | the vocabulary guard accepts them, **and** an undeclared one is rejected |

---

## Explicit non-goals

- **No default-on.** The challenger ships `flat`.
- **No re-pricing of live stops.** Nine resting stops are the floor ADR-0018 depends on.
- **No tuning to a target touch rate.** Ship conservative bounds; moving `k` is the experiment.
- **No change to the RR threshold** (`min_reward_risk_ratio`) — item 2 keeps the *ratio* invariant
  rather than adjusting the gate.
- **No new volatility model.** Use the `atr_pct` that already exists.
- **No change to the monitor's exit evaluation or to broker stop placement.**
- **No `laws.md` edits.** Findings go to `drift-register.md`.

### The road not taken (LAW-06)

- **Just raise the flat stop to 8 %** (the current `le` bound). One number, no plumbing. Rejected:
  it makes BAC's stop 3.8 ATRs — a stop so far away it is decorative — while MRVL's is still under
  1 ATR. It moves the problem without changing the shape, and it raises the risk cap for names that
  never needed it.
- **Scale by realized downside gap instead of ATR.** More directly on target — it measures the
  thing the stop must survive. Rejected for now: nothing computes that statistic, whereas `atr_pct`
  is already on the recommendation. **Deferred, not rejected.**
- **Put the scaling in the PM instead of the analyst.** Defensible — the stop is a risk instrument
  and the PM disposes risk. Proposed as the analyst's on ADR-0017's "alpha proposes" reading and
  because the analyst already owns the field. **If the laws disagree, the law wins** — this is
  flagged as a live question in the MUST RULE, not a settled one.
- **Let the monitor re-price stops as volatility changes.** A trailing, volatility-aware stop.
  Rejected as scope: it means mutating live risk instruments on a schedule, which is a much larger
  safety question than choosing a stop at entry.
- **Do nothing, because the flat stop has not visibly cost anything.** The honest counter — MRVL's
  stop was correct, and no measured loss is yet attributable to the flat band. Rejected because the
  exposure is structural and measurable in advance (39 % touch rate on MRVL), and waiting for it to
  cost money is how the ADR-0018 gap went unnoticed for months.

---

## Sequencing after merge

1. **S149 must be merged first.** If it is not, stop and say so.
2. `make ci` green locally, branch pushed, **all four remote gates green before merging locally**
   (DL-56).
3. Build + retag the fleet at `:s150`. **Behaviour does not change** — the mode ships `flat`.
4. Let runs accumulate with the counterfactual recorded, alongside S149's tolerance experiment.
5. Run the comparison script and bring the numbers to the operator. **Promotion is their call.**
6. Record the functionality check in [`docs/laws/functionality-checks.md`](../laws/functionality-checks.md).

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds, never a bare literal.
- Faults, not silent failure — `kernel.fault_boundary`, errors redirected with provenance.
- `make ci` all 9 steps green, **100.00 % coverage floor**, before handback. Never lower the floor.
- Version bump in `pyproject.toml` to **0.84.00** (feat → MINOR), `uv.lock` staged with it.
- Any law clause your tests cover cites the clause ID in the test docstring.
- If `main` has moved when you finish: merge `main` into the branch, resolve, re-run `make ci`, and
  **say so in the return notes** (DL-48).
- Secrets never through the worktree — chat or gitignored `.env` only.

---

## Handback contract — MANDATORY

**Append your results INSIDE this file, at the bottom, in the placeholder sections below.**

1. Fill the **Law reading record** *before* your first code change — including your answer on
   **where the scaling belongs** and what the laws said about it.
2. Fill the `**Result:**` line under **each** of the seven spec items, in place.
3. Fill the **Test plan results** table — one row per planned test. A test you chose not to write
   needs a reason, not a blank.
4. Fill the **Closeout — evidence** block with real command output.
5. Fill the **Return notes**, including **the `k`, floor and ceiling you chose and why**.
6. State any success factor you did **not** meet plainly, as "verified failing" or "not done"
   (LAW-02).

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? (yes + what / no) |
| --- | --- | --- | --- |
| `recommend.py` — stop/target proposal | `agents/analyst/laws/laws.md`; `agents/analyst/laws/test-plan.md`; `docs/decisions/0017-exit-authority-alpha-proposes-risk-disposes.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `ANLZ-OUT-01`, `ANLZ-OUT-02`, `ANLZ-NEV-01`, `ANLZ-IDM-01`, `ANLZ-FAIL-03`, `ANLZ-TYP-02`, ADR-0017 alpha-proposes/risk-disposes | No contradiction. Reading confirmed the analyst is allowed to propose `suggested_stop_pct` / `suggested_target_pct` but must not size, approve, submit, or dispose risk. Approach: keep scaling in analyst as proposal math, keep PM as gate/disposal. |
| analyst settings — mode + tunables | `agents/analyst/laws/laws.md`; `agents/analyst/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md`; `docs/decisions/0013-continuous-improvement-system.md` | `ANLZ-IDM-01`, `ANLZ-TYP-02`, analyst `PARAM`, conventions §§3/7, ADR-0013 | Yes. Analyst `PARAM` is silent on a selectable stop-scaling mode, scaled tunables, and counterfactual proposal evidence, so `DRIFT-028` is opened. Tunables stay bounded with `why`; default remains `flat`. |
| `gate_report.py` — the RR gate | `agents/portfolio_manager/laws/laws.md`; `agents/portfolio_manager/laws/test-plan.md`; ADR-0017 | `PM-IDN-01`, `PM-NEV-04`, `PM-OUT-03`, `PM-OBS-01`, `PM-IDM-01`, `PM-TYP-02` | Yes. The laws make PM the risk gate owner, so the implementation must prove the RR verdict is invariant instead of weakening or bypassing the gate. Stop-only scaling is a planted failure. |
| `contracts/analyst.py` | `agents/analyst/laws/laws.md`; `agents/analyst/laws/test-plan.md`; ADR-0017 | `ANLZ-OUT-02`, `ANLZ-TYP-01`, `ANLZ-TYP-02`, `ANLZ-STA-02` | Yes. The applied `suggested_*` fields already exist, but the spec requires both applied and counterfactual pairs on every buy; that durable evidence is not representable without an additive optional contract field. |
| monitor / `contracts/positions.py` (read-only) | `agents/monitor/laws/laws.md`; `agents/monitor/laws/test-plan.md`; `docs/decisions/0015-exit-lifecycle-and-stop-ownership.md`; ADR-0017 | `MON-IDN-01`, `MON-IDN-02`, `MON-NEV-05`, `MON-STA-01`, `MON-STA-02`, ADR-0015 broker-enforced stop ownership | No. Existing `Position.stop_pct` is a recorded fact for live positions. S150 applies only to new analyst proposals; monitor/position paths stay read-only except tests proving mode flips do not mutate them. |
| the comparison script | `docs/decisions/0013-continuous-improvement-system.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md`; DL-57/DL-59/DL-70/DL-77 in `docs/design-log.md` | ADR-0013 configurable-not-settable; LAW-02 proof discipline; conventions §7 | No. The script must read/report only: per-mode stop width distribution, RR pass rate, and touched counts where outcomes are known. It must never write settings or promote the challenger. |
| `trading_graph_vocabulary.json` | `docs/laws/conventions.md`; `docs/laws/drift-register.md`; S144/S149 vocabulary guard context | Conventions §§2/3/9; vocabulary guard requires declared graph labels/edges/properties | No. Any new durable recommendation evidence props must be declared in the pack vocabulary; property enforcement may not cover `Recommendation` today, but the declaration prevents another trailing-indicator gap. |

**Where does the scaling belong — analyst or PM? What did the laws say?**

The scaling belongs in the analyst as a proposal. `ANLZ-OUT-02` already declares
`suggested_stop_pct` and `suggested_target_pct` as analyst output, while `ANLZ-NEV-01` forbids
sizing, price and dollar decisions but not a bounded stop/target proposal. ADR-0017's
"alpha proposes, risk disposes" line matches this split: analyst proposes the entry stop/target
shape, PM applies the RR gate and other risk gates, and broker/monitor live-stop ownership remains
unchanged. A PM implementation would mix proposal generation into the risk disposer and make the
RR-trap harder to surface.

**Contradictions found between a law and this spec** (a contradiction is a success — name it):

None found. The spec's proposed analyst home is compatible with `ANLZ-OUT-02` / `ANLZ-NEV-01`,
PM law keeps the RR gate binding, and monitor law plus ADR-0015/0017 forbid repricing live stops.

**Laws found silent where a decision was needed** (each needs a `drift-register.md` row):

`DRIFT-028` opened: analyst `PARAM` / `OUT` / `OBS` are silent on a selectable stop-scaling mode,
bounded volatility-scaled stop/target tunables, and durable applied-vs-counterfactual proposal
evidence.

**Clauses that were ⬜ unproven in `test-plan.md` and are now proven by this sprint's tests:**

`ANLZ-IDM-01`, `ANLZ-TYP-02`, and `PM-IDM-01`. The analyst law map now records 26 / 43 green
clauses, and the portfolio-manager map records 24 / 43.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_flat_mode_applied_stop_and_target_ignore_atr` | `agents/analyst/tests/test_scaled_stop_targets.py` | PASS | `ANLZ-OUT-02`, `ANLZ-IDM-01` |
| A2 | `test_scaled_mode_resolves_quiet_and_volatile_exact_values` | `agents/analyst/tests/test_scaled_stop_targets.py` | PASS; exact 2x ATR asserted on a volatile under-cap case because MRVL-like 8.5% correctly hits A5's risk ceiling | `ANLZ-OUT-02`, `ANLZ-IDM-01` |
| A3 | `test_scaled_mode_resolves_quiet_and_volatile_exact_values` | `agents/analyst/tests/test_scaled_stop_targets.py` | PASS | `ANLZ-OUT-02`, `ANLZ-IDM-01` |
| A4 | `test_scaled_mode_floor_and_risk_ceiling_clamp` | `agents/analyst/tests/test_scaled_stop_targets.py` | PASS | `ANLZ-TYP-02`, `ANLZ-FAIL-03` |
| A5 | `test_scaled_mode_floor_and_risk_ceiling_clamp` | `agents/analyst/tests/test_scaled_stop_targets.py` | PASS | `ANLZ-TYP-02`, `ANLZ-FAIL-03` |
| A6 | `test_scaled_stop_knobs_are_tunables_and_mode_is_bounded` | `agents/analyst/tests/test_scaled_stop_targets.py` | PASS | `ANLZ-PARAM`, ADR-0013 |
| A7 | `test_resolution_is_deterministic_for_same_inputs` | `agents/analyst/tests/test_scaled_stop_targets.py` | PASS | `ANLZ-IDM-01` |
| A8 | `test_scaled_stop_knobs_are_tunables_and_mode_is_bounded` | `agents/analyst/tests/test_scaled_stop_targets.py` | PASS | `ANLZ-PARAM`, ADR-0013 |
| B1 | `test_missing_atr_falls_back_to_flat_without_suppressing_recommendation` | `agents/analyst/tests/test_scaled_stop_targets.py` | PASS | `ANLZ-FAIL-03`, `ANLZ-OUT-01`, DL-57 |
| B2 | `test_missing_atr_falls_back_to_flat_without_suppressing_recommendation` | `agents/analyst/tests/test_scaled_stop_targets.py` | PASS | `ANLZ-FAIL-03`, `ANLZ-OUT-01`, DL-57 |
| B3 | `test_nonsensical_atr_is_missing_or_clamped_not_trusted` | `agents/analyst/tests/test_scaled_stop_targets.py` | PASS | `ANLZ-FAIL-03`, `ANLZ-TYP-02` |
| B4 | `test_sells_are_unchanged_under_scaled_mode` | `agents/analyst/tests/test_scaled_stop_targets.py` | PASS | `ANLZ-NEV-01`, `ANLZ-OUT-02` |
| C1 | `test_reward_risk_verdict_is_mode_invariant_when_both_values_scale` | `agents/portfolio_manager/tests/test_scaled_stop_rr_gate.py` | PASS | `PM-IDM-01`, `PM-NEV-04` |
| C2 | `test_volatile_scaled_name_still_passes_and_stop_only_scaling_fails` | `agents/portfolio_manager/tests/test_scaled_stop_rr_gate.py` | PASS | `PM-NEV-04`, `PM-OUT-03` |
| C3 | `test_pm_default_stop_target_fallback_is_unchanged` | `agents/portfolio_manager/tests/test_scaled_stop_rr_gate.py` | PASS | `PM-NEV-04`, `PM-TYP-02` |
| C4 | `test_reward_risk_threshold_still_rejects_poor_setups` | `agents/portfolio_manager/tests/test_scaled_stop_rr_gate.py` | PASS | `PM-NEV-04`, `PM-OUT-03` |
| D1 | `test_flat_mode_records_applied_and_counterfactual_stop_target_pairs` | `agents/analyst/tests/test_stop_target_evidence.py` | PASS | `ANLZ-STA-02`, `ANLZ-OBS-01`, ADR-0013 |
| D2 | `test_scaled_mode_records_flat_counterfactual_symmetrically` | `agents/analyst/tests/test_stop_target_evidence.py` | PASS | `ANLZ-STA-02`, `ANLZ-OBS-01`, ADR-0013 |
| D3 | `test_stop_target_record_is_append_only_for_repeated_recommendations` | `agents/analyst/tests/test_stop_target_evidence.py` | PASS | `ANLZ-STA-02`, `ANLZ-IDM-02` |
| D4 | `test_comparison_script_reports_both_modes_and_touch_difference` | `tests/test_compare_stop_targets.py` | PASS | `ANLZ-OBS-01`, ADR-0013 |
| D5 | `test_comparison_script_never_writes_or_promotes` | `tests/test_compare_stop_targets.py` | PASS | `ANLZ-NEV-01`, ADR-0013 |
| E1 | `test_scaled_mode_does_not_reprice_existing_position_or_resting_stop` | `agents/analyst/tests/test_stop_target_live_positions.py` | PASS | `MON-IDN-02`, `MON-STA-02`, ADR-0015 |
| E2 | `test_sweep_exempts_resting_stops_and_prefixless_stop` | `agents/execution/tests/test_drop_sweep.py` | PASS | `EXEC-NEV-01`, `EXEC-NEV-03` |
| E3 | `test_recommendation_stop_target_props_are_declared_and_unknown_prop_fails` | `tests/test_graph_vocabulary_completeness.py` | PASS | `ANLZ-OBS-01`, conventions |

**Tests added beyond the plan:**

- `test_zero_flat_stop_keeps_target_defined_when_scaled` covers the defensive no-divide path when
  a zero flat stop is supplied.
- `test_stop_target_evidence_is_optional_and_round_trips` also proves legacy recommendations
  serialize without synthetic stop-target evidence props.

---

## Closeout — evidence

**Files changed:**

Code and contracts:
`agents/analyst/domain/analyze.py`, `agents/analyst/domain/recommend.py`,
`agents/analyst/domain/recommend_text.py`, `agents/analyst/domain/stop_target.py`,
`agents/analyst/recommendation_props.py`, `agents/analyst/settings.py`,
`agents/analyst/store.py`, `contracts/analyst.py`, `scripts/compare_stop_targets.py`,
`orchestration/packs/trading_graph_vocabulary.json`, `pyproject.toml`, `uv.lock`.

Tests and law maps:
`agents/analyst/tests/test_scaled_stop_targets.py`,
`agents/analyst/tests/test_stop_target_evidence.py`,
`agents/analyst/tests/test_stop_target_live_positions.py`,
`agents/portfolio_manager/tests/test_scaled_stop_rr_gate.py`,
`tests/test_compare_stop_targets.py`, `tests/test_contract_values.py`,
`tests/test_graph_vocabulary_completeness.py`, `agents/analyst/laws/test-plan.md`,
`agents/portfolio_manager/laws/test-plan.md`, `docs/laws/INDEX.md`,
`docs/laws/drift-register.md`, `docs/laws/ledger.md`, `docs/STATE.md`, this sprint doc.

**Proven (LAW-02):**

Branch and dependency gate:

```text
origin/main=79027e9
S149 1b471c4 is an ancestor of origin/main
branch=sprint-150-volatility-scaled-stops
uv lock:
Resolved 170 packages in 1.49s
Updated trading-agents v0.83.0 -> v0.84.0
```

Focused compilation:

```text
uv run python -m py_compile agents\analyst\domain\recommend.py agents\analyst\domain\recommend_text.py agents\analyst\domain\stop_target.py agents\analyst\settings.py contracts\analyst.py agents\analyst\store.py agents\analyst\recommendation_props.py
exit 0
```

Focused S150 suite:

```text
uv run pytest agents/analyst/tests/test_scaled_stop_targets.py agents/analyst/tests/test_stop_target_evidence.py agents/analyst/tests/test_stop_target_live_positions.py agents/portfolio_manager/tests/test_scaled_stop_rr_gate.py tests/test_compare_stop_targets.py tests/test_graph_vocabulary_completeness.py --no-cov
collected 28 items
28 passed in 6.53s
```

Affected suite including S148 stop safety:

```text
uv run pytest agents/analyst/tests agents/portfolio_manager/tests agents/execution/tests/test_drop_sweep.py tests/test_compare_stop_targets.py tests/test_graph_vocabulary.py tests/test_graph_vocabulary_completeness.py tests/test_contract_values.py --no-cov
collected 485 items
485 passed in 12.59s
```

Static gates:

```text
uv run ruff check .
All checks passed!

uv run ruff format --check .
860 files already formatted

uv run mypy kernel contracts agents orchestration surfaces
pyproject.toml: note: unused section(s): module = ['azure.core', 'azure.identity.*', 'azure.keyvault', 'celery.*', 'redis', 'redis.*']
Success: no issues found in 720 source files
```

Vocabulary:

```text
uv run python scripts\vocabulary_coverage.py
exit 0, no stdout

uv run python scripts\vocabulary_signatures.py
exit 0, no stdout

uv run pytest tests/test_graph_vocabulary_completeness.py --no-cov
collected 8 items
8 passed in 5.75s
```

Real comparison-script read against configured graph:

```text
uv run python scripts\compare_stop_targets.py --env-file .env
mode	recommendations	stop_min_pct	stop_median_pct	stop_max_pct	rr_pass_rate_pct	known_outcomes	would_touch_rate_pct
flat	0	n/a	n/a	n/a	0.00	0	n/a
scaled	0	n/a	n/a	n/a	0.00	0	n/a
```

Synthetic comparison-script report proving mode-visible differences:

```text
mode	recommendations	stop_min_pct	stop_median_pct	stop_max_pct	rr_pass_rate_pct	known_outcomes	would_touch_rate_pct
flat	2	5.00	5.00	5.00	100.00	2	50.00
scaled	2	4.20	6.10	8.00	100.00	2	0.00
```

Full local `make ci`:

```text
uv run ruff check . --output-format=github
uv run ruff format --check .
860 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
pyproject.toml: note: unused section(s): module = ['azure.core', 'azure.identity.*', 'azure.keyvault', 'celery.*', 'redis', 'redis.*']
Success: no issues found in 720 source files
uv run lint-imports
Contracts: 4 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests
[WARN] agents\analyst\domain\recommend.py: 196 lines (warn 150, hard block 200)
[WARN] agents\analyst\tests\test_scaled_stop_targets.py: 198 lines (warn 150, hard block 200)
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run pytest
TOTAL                                                13049      0   2768      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
================= 1971 passed, 5 skipped in 159.07s (0:02:39) =================
uv run pip-audit
No known vulnerabilities found
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 9 new file(s)
```

Remote branch gates for implementation commit `3fa9496`:

```text
gh run watch 30520713599 --exit-status
✓ sprint-150-volatility-scaled-stops CI · 30520713599
✓ security in 1m48s (ID 90800231988)
✓ quality in 35s (ID 90800232062)
✓ test in 58s (ID 90800339095)

gh run list --branch sprint-150-volatility-scaled-stops --limit 10
completed success feat: add volatility-scaled stop challenger Security Findings sprint-150-volatility-scaled-stops push 30520713598
```

**The `k`, floor and ceiling shipped, and why:**

Shipped `k=2.0`, `floor_pct=0.025`, `ceiling_pct=0.08`. `k=2.0` matches the measured challenger in
the handover table and is not tuned to a target. The 2.5% floor prevents near-zero ATR readings from
creating decorative stops that will be touched by noise; the 8% ceiling keeps the existing PRD risk
cap binding. The MRVL-like 8.5% ATR case therefore clamps at 8% instead of producing a 17% stop,
which is the intended safety rail.

**Not met / verified failing:**

No sprint success factor is currently verified failing.

---

## Return notes

The scaling belongs in the analyst as a proposal. That matches `ANLZ-OUT-02`, stays inside
`ANLZ-NEV-01`, and preserves ADR-0017's split: alpha proposes the stop/target shape, PM disposes
risk through gates, and broker/monitor ownership of live stops is untouched.

The important surprise was that the most intuitive exact MRVL test conflicts with the PRD risk cap:
2 × 8.5% ATR is 17%, so a correct implementation must clamp it. I proved exact `k * ATR` on an
under-cap volatile case and proved the MRVL-like/absurd cases through the ceiling test. `atr_pct`
is good enough for an ADR-0013 challenger because it is already present on the analyst score and
gives a deterministic, measurable counterfactual, but it is not promoted by this sprint.

Deliberately not done: no default-on flip, no PM gate weakening, no live stop repricing, no broker
orders, no monitor exit changes, and no law edits. `origin/main` was `79027e9` at branch creation
and S149 `1b471c4` was verified as an ancestor before work began; main movement will be checked
again before handback.
