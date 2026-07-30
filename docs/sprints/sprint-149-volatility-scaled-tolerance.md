<!-- Agent: planning | Role: sprint handover -->
# Sprint 149 — A flat band is the wrong shape: volatility-scaled order tolerance

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-149-volatility-scaled-tolerance`
**Status:** SPEC — measured challenger to S148's flat tolerance; **ships OFF by default**
**Version:** feat → **0.83.00** (MINOR; `0.82.00` is S148)
**Effort:** M
**Depends on:** **S148 must be merged first** — this sprint modifies the tolerance S148 introduces.
**Decisions:** [ADR-0013](../decisions/0013-continuous-improvement-system.md) **(this sprint is an
ADR-0013 experiment: a challenger is measured, never auto-promoted)** ·
[ADR-0018](../decisions/0018-decision-validity-same-session-or-dropped.md) the tolerance exists and
its width is *deliberately open* · [ADR-0016](../decisions/0016-one-run-one-evidence-both-directions.md)
one run, one evidence set · [DL-70](../design-log.md) plant violations ·
[DL-57](../design-log.md)/[DL-59](../design-log.md) intent ≠ outcome

> **This sprint does not change how the fleet trades.** It ships the challenger **off**. Promotion
> is a config flip the operator makes after seeing measured evidence — not a deploy, and not a
> judgement call inside this sprint. If you find yourself wanting to default it on, re-read
> ADR-0013 and stop.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

### What the law folders are

This repo is governed by a **law book**. It is not documentation and it is not advisory — it is the
constitution the code is required to satisfy, and it outranks this sprint document.

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** — clause IDs `<AGENT>-<SECTION>-<NN>` | **LOCKED v1. Read-only. Never edit.** A clause you believe is wrong is a drift-register row plus a report, never an edit |
| `agents/<name>/laws/test-plan.md` | The clause-by-clause test map: proven (🟩) vs unproven (⬜) | Read it to learn whether what you are changing is *proven* or merely asserted |
| `docs/laws/*.md` | The **umbrella laws** — conventions, dependencies, drift register, ledger, functionality checks | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Clause **sections**: `IDN` · `IN` · `TRG` · `OUT` · **`NEV`** · `STA` · **`IDM`** · `ORD` ·
**`FAIL`** · `TYP` · `SEC` · `DEP` · `OBS` · `PERF` · `CAP` · **`PARAM`**.

For **this** sprint the binding sections are **`PARAM`** (three new tunables and a mode selector),
**`NEV`** (this sprint moves a number *across two agent boundaries* — nothing may start deciding
what to trade), **`IDN`** (who owns `OrderIntent`), and **`FAIL`** (a missing volatility input must
degrade, never block).

### The rule

1. **Before writing code**, for **every** element in the map below, open and read its law file(s).
   Read the whole file the first time — not a keyword grep.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Also read [`docs/laws/conventions.md`](../laws/conventions.md),
   [`docs/laws/dependencies.md`](../laws/dependencies.md), and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Write the Law reading record** (template near the bottom) **before** your first code change.
5. **If a law contradicts this spec, STOP and report.** **A contradiction you surface is a success.**
6. **If a law is silent** where you must decide, record it and add a `drift-register.md` row.
7. Every test for behaviour a clause governs **must cite the clause ID in its docstring**.

### Element → law map (read all of these)

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/portfolio_manager/` — carry `atr_pct` onto `OrderIntent` (item 1) | `agents/portfolio_manager/laws/laws.md` + `test-plan.md` | **`PM-IDN-*` owns `OrderIntent`.** `PM-NEV-*` — passing a volatility number through must not become the PM deciding execution policy |
| `contracts/portfolio_manager.py` — one new optional field (item 1) | `agents/portfolio_manager/laws/laws.md` + `agents/execution/laws/laws.md` | A contract change touching two agents; confirm both constitutions still describe what they own |
| `agents/analyst/` (**read-only — it already emits what you need**) | `agents/analyst/laws/laws.md` | `ANLZ-OUT-*` — confirm for yourself that `quant_metrics` is a declared output and that reading `atr_pct` from it is using the contract as intended, not scraping it |
| `agents/execution/settings.py` — mode + three tunables (items 2, 3) | `agents/execution/laws/laws.md` (**`PARAM` section**) + `docs/laws/conventions.md` | **DRIFT-024/025/026 already record that execution's `PARAM`/`IDN` sections lag its code. Expect a fourth. Report it; do not edit the law** |
| `agents/execution/alpaca_orders.py` + tolerance resolution (items 2, 3, 4) | `agents/execution/laws/laws.md` + `docs/laws/dependencies.md` | `EXEC-NEV-*` (never decides what to trade), `EXEC-IDM-*` (same inputs → same payload), `DEP-BROKER` |
| `orchestration/packs/trading_graph_vocabulary.json` (item 6) | `docs/laws/conventions.md` | S143/S144: any new prop shape or edge must be declared |

### What the trial is measuring

The law-first rule has run three times ([DL-74](../design-log.md)): DRIFT-024 on S146, DRIFT-025 and
a reporter defect on S147, DRIFT-026 on S148. Answer honestly per element: **did reading the law
change what you were going to do?** "No — the intended approach already complied" is a good answer.
A record that is vague, or written after the code, defeats the trial (DL-48).

---

## Why this sprint

S148 shipped a **flat 50 bps** tolerance. I then measured it against 60 sessions of real overnight
gaps for the nine held names plus AMD and MRVL. The flat band is not neutral — it silently picks
winners:

| Ticker | Median overnight gap | Buys refused @ 50 bps |
| --- | --- | --- |
| SCHW | 42 bps | 25 % |
| USB | 47 bps | 30 % |
| WFC | 47 bps | 37 % |
| **HPE** | **132 bps** | **45 %** |
| **AMD** | **251 bps** | **52 %** |
| **MRVL** | **318 bps** | **48 %** |

Blended across the book, 50 bps refuses ≈ **35 % of buys and 23 % of sells**. That much is the
ADR working as intended. The problem is the **distribution**: 50 bps is roughly *one* median gap for
SCHW and *one fifth* of a median gap for MRVL. The same number means two completely different
policies depending on which ticker it lands on, and nobody chose that.

**The argument for scaling is about edge, not just volatility.** A tolerance says *how far from my
decided price I will still trade*. On a name whose typical move is 3 %, refusing a 0.5 % adverse gap
throws away trades whose edge dwarfs the slippage. On a name whose typical move is 0.5 %, that same
gap eats the entire edge. Volatility is the available proxy for edge size, so the band should scale
with it.

**This is a challenger, not a correction.** The flat band may well be right — see the road not
taken. The point of this sprint is to make the comparison *measurable* instead of arguable
(ADR-0013).

---

## What is already in place (read this before estimating)

Confirm each of these yourself:

- **The per-ticker volatility already exists and already crosses an agent boundary.** The analyst
  computes `atr_pct` — ATR as a percentage of the last close — in
  [`technical_rules_range.py:79-81`](../../agents/analyst/domain/technical_rules_range.py#L79-L81),
  and it lands in `Recommendation.quant_metrics`
  ([`contracts/analyst.py`](../../contracts/analyst.py)), which is a declared analyst output.
  **The analyst needs no change at all.**
- **The gap is PM → execution.** `OrderIntent` ([`contracts/portfolio_manager.py:27`](../../contracts/portfolio_manager.py#L27))
  carries `est_price`, `stop_pct`, `target_pct` — but no volatility. The PM holds the
  `Recommendation` when it builds the intent, so it can carry the number across. **That one optional
  field is the only contract change this sprint needs.**
- **S148 already resolves and applies a tolerance.** `ExecutionSettings.order_price_tolerance_bps`
  (50, `ge=0`, `le=500`) and `order_body` already build the bounded payload. You are changing *how
  the number is chosen*, not how it is applied.

So the mechanical work is small. **The care in this sprint goes into item 4** — recording the
counterfactual so the experiment can actually be judged later.

---

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it. Results go in this file.

### 1 · Carry the per-ticker volatility from the PM to execution

- Add **one optional field** to `OrderIntent` for the decision-time volatility (e.g.
  `decision_atr_pct: float | None`). Optional and defaulted, so nothing upstream breaks and old
  payloads still validate.
- The PM populates it from the recommendation's `atr_pct` quant metric when present, and leaves it
  `None` when absent. **The PM must not compute, smooth, or adjust it** — it is a courier here, not
  a decider (`PM-NEV-*`). If the metric is missing, `None` is the honest answer.
- **Do not change the analyst.** It already emits `atr_pct`.

**Result:**

### 2 · Resolve the tolerance through a selectable mode

- Add a mode to `ExecutionSettings`: **`flat`** (champion, **the default**) | **`scaled`**
  (challenger). Nothing about production behaviour changes until an operator flips it.
- `flat` → exactly S148's behaviour, `order_price_tolerance_bps`. Do not alter it.
- `scaled` → `clamp(k × atr_pct_in_bps, floor_bps, ceiling_bps)`, where **`k`, `floor_bps` and
  `ceiling_bps` are each a `kernel.tunable(..., why=..., ge=..., le=..., unit=...)`** — never
  literals.
- Choose a conservative starting `k` and **say in the closeout what you chose and why**. For
  calibration from the data above: overnight gaps run roughly 0.3–0.6 × daily ATR, so a `k` near
  that range keeps the band comparable to a typical gap. **Do not tune it to hit a target
  drop rate** — that is the experiment, not this sprint.
- The resolved tolerance must be **deterministic**: same intent + same settings → same tolerance →
  same payload (`EXEC-IDM-*`).

**Result:**

### 3 · A missing volatility degrades to flat — it never blocks a decision

- `decision_atr_pct` is `None` (no ATR: a short history, a new listing, a held position with no
  fresh recommendation) → fall back to the flat tolerance and **record that the fallback happened**.
- **Never** block, skip, or drop a decision because volatility is missing. A missing input is a
  degraded input, not a veto (`EXEC-FAIL-*`, DL-57).
- The floor and ceiling are the safety rails: **no ticker may end up with a tolerance so wide that
  ADR-0018 stops meaning anything**, and none so narrow that it can never trade. Prove both clamps.

**Result:**

### 4 · Record the counterfactual — this is what makes it an experiment

Without this the sprint is unmeasurable and therefore pointless.

- On every submitted order, record **both** tolerances and **both** resulting limit prices: the one
  applied and the one the *other* mode would have produced, plus the mode in force and the decided
  price. Append to the existing order/`Fill` evidence — **append, never rewrite** (S145).
- Record whether the volatility input was present or fell back (item 3).
- **A comparison script** — `scripts/` is the right home, alongside `audit_broker_graph.py` — that
  reads a window of runs and reports, per mode: order count, would-have-filled count against the
  actual open price, drop rate, and realized slippage vs the decided price. That output is the
  evidence an operator promotes on.
- The script **reports**; it never promotes and never writes a settings change (ADR-0013: the
  researcher never applies its own proposal).

**Result:**

### 5 · Keep the S148 guarantees intact

- **Resting broker stops stay exempt.** They are not decisions and this sprint must not touch
  `submit_stop`, `stop_order_body`, or the drop sweep's stop exemption. Re-run S148's stop-safety
  tests unchanged and confirm they still pass.
- The drop sweep, `dropped` counting, and the reporter's dropped-vs-rejected handling are unchanged.
- `time_in_force` stays `day`.

**Result:**

### 6 · Declare any new prop or edge in the vocabulary

- New props/edges go in [`trading_graph_vocabulary.json`](../../orchestration/packs/trading_graph_vocabulary.json).
- Re-run `scripts/vocabulary_coverage.py` and `scripts/vocabulary_signatures.py`; paste the output.

**Result:**

### 7 · Prove the checks can fail (DL-70)

Plant the violation and require the failure — the test plan specifies the violation for each test.

**Result:**

---

## Test plan — every test I want, and why

**Ground rules.** Every test cites its clause ID(s) in the docstring and **plants the violation**.
Names are descriptive, not prescriptive. **If a test is wrong or untestable, say so with a reason —
do not silently drop it.**

### A · Carrying the volatility

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | the PM carries `atr_pct` onto the intent | a recommendation whose `quant_metrics` include `atr_pct` | the built `OrderIntent` carries exactly that value — unmodified, not rounded, not rescaled |
| A2 | a missing metric yields `None`, not a guess | `quant_metrics` **without** `atr_pct` | the field is `None`. **Plant a fabricated default and require the test to fail** — inventing volatility is DL-57's failure mode |
| A3 | old payloads still validate | an `OrderIntent` JSON without the new field | validates, field defaults to `None`. Guards the optional-and-defaulted requirement |

### B · Resolving the tolerance

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| B1 | `flat` mode is byte-identical to S148 | mode `flat`, any `atr_pct` | the payload equals S148's. **The volatility must be ignored entirely in flat mode** |
| B2 | `scaled` widens a volatile name | `atr_pct` typical of AMD | tolerance is larger than flat, and equals `k × atr_pct` in bps exactly |
| B3 | `scaled` narrows a quiet name | `atr_pct` typical of SCHW | tolerance is smaller than the volatile case; assert the exact value, not just the ordering |
| B4 | the floor clamps | `atr_pct` near zero | tolerance == `floor_bps`, never below. Plant a sub-floor value and require the clamp |
| B5 | the ceiling clamps | an absurdly high `atr_pct` | tolerance == `ceiling_bps`. **This is the rail that stops the ADR being neutered** — plant a value that would blow past it |
| B6 | resolution is deterministic | same intent + settings, resolved twice | identical tolerance and identical payload (`EXEC-IDM-*`) |
| B7 | the three knobs are declared tunables | — | `k`, `floor_bps`, `ceiling_bps` each a `kernel.tunable` with `why`/`ge`/`le`/`unit`. Plant a bare literal and require the gate to reject it |
| B8 | the mode itself is bounded | an invalid mode string | rejected at settings validation, not silently treated as flat |

### C · Degradation

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| C1 | missing volatility falls back to flat | mode `scaled`, `decision_atr_pct=None` | the flat tolerance is used, the order is **still submitted**, and the fallback is recorded |
| C2 | 🚨 a missing input never drops a decision | mode `scaled`, `None` volatility | the decision is not dropped, skipped or rejected. **Plant the blocking behaviour and require the failure** — this is the clause that stops a data gap from halting trading |
| C3 | a nonsensical volatility is clamped, not trusted | negative / NaN / absurd `atr_pct` | clamped into the declared bounds or treated as missing; never produces a nonsense limit price |

### D · The counterfactual record (the experiment)

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| D1 | both tolerances are recorded | one order in `flat` mode | the evidence carries the applied tolerance **and** the scaled counterfactual, both limit prices, the mode, and the decided price |
| D2 | the record is symmetric | the same order in `scaled` mode | the flat counterfactual is recorded. **Plant a one-sided implementation and require the failure** — recording only the applied side makes the experiment unjudgeable |
| D3 | the record is append-only | re-record for the same order | no in-place rewrite; S145's rule holds |
| D4 | the comparison script reports both modes | a window with orders under both modes and known open prices | per-mode order count, would-have-filled count, drop rate, and realized slippage. Plant a run where the modes differ and require the difference to show |
| D5 | the script never promotes | run it | it writes **no** settings change and **no** mode flip — read-and-report only (ADR-0013) |

### E · S148 guarantees and vocabulary

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| E1 | 🚨 resting stops are still exempt | S148's stop-safety fixture, unchanged | all stops survive the drop sweep. **Re-run S148's C1 verbatim** — a tolerance change must not weaken the floor |
| E2 | stops never get a tolerance | a stop submission under `scaled` mode | `stop_order_body` output is unchanged: still `type: stop`, `tif: gtc`, no limit band |
| E3 | `time_in_force` stays `day` on bounded orders | — | still `day`; a change to `gtc` fails |
| E4 | new props/edges are declared | the new evidence props | the vocabulary guard accepts them, **and** an undeclared one is rejected |

---

## Explicit non-goals

- **No default-on.** The challenger ships `flat`. Promotion is an operator config flip after evidence.
- **No tuning to a target drop rate.** Ship conservative bounds; moving `k` is the experiment.
- **No change to the analyst.** It already emits `atr_pct`.
- **No change to S148's drop sweep, stop exemption, dropped counting, or reporter handling.**
- **No new volatility model.** Use the `atr_pct` that already exists. Do not add EWMA, realized
  overnight vol, or implied vol — all interesting, all a different sprint.
- **No per-ticker `stop_pct`.** See the finding below. Related, real, and **out of scope**.
- **No `laws.md` edits.** Findings go to `drift-register.md`.

### A finding to record, not to fix (LAW-06)

While tracing the volatility path I found that **`suggested_stop_pct` is not per-ticker at all**:
[`recommend.py:172`](../../agents/analyst/domain/recommend.py#L172) sets it to
`regime.base_stop_loss_pct` for every buy. So **every position in the book gets the same stop
distance regardless of volatility** — SCHW (median overnight gap 42 bps) and MRVL (318 bps) carry an
identically-sized floor.

That is the same flat-band problem as this sprint's, one layer over, and it is about *risk* rather
than *execution price* — so it is arguably more consequential. **Do not fix it here.** Record it as
a design-log thread (see the sequencing section) so it is not silently dropped, and let the operator
decide whether it becomes its own sprint.

### The road not taken (LAW-06)

Ruled out — record any further options you rule out:

- **Just widen the flat band to 150 bps.** One number, no new plumbing, drops fall to ~11 %.
  Rejected as the *primary* answer because it does not fix the shape — it makes SCHW's band three
  median gaps wide while MRVL's is still half of one. **But it is the honest baseline the challenger
  must beat**, so the comparison script must make that visible.
- **Keep the flat band and simply do not trade high-gap names after close.** Genuinely defensible:
  the flat band already achieves this implicitly, and refusing to trade blind where blind is most
  expensive may be *correct*. Rejected as an unexamined default rather than on evidence — which is
  exactly what this sprint produces. **If the measurement says the flat band wins, this is the
  outcome, and that is a real result.**
- **Scale by realized overnight gap instead of ATR.** More directly on-target — it measures the
  exact risk being bounded. Rejected for now: it needs a new per-ticker statistic and a history
  window that nothing computes today, whereas `atr_pct` already crosses the boundary for free.
  **Deferred, not rejected** — a natural follow-up if ATR proves a poor proxy.
- **Let the PM decide the tolerance.** It holds the recommendation and the risk context. Rejected:
  the tolerance is an *execution* policy about broker submission, and `PM-NEV-*`/`EXEC-IDN-01` put
  that on execution's side of the line. The PM carries the input; execution decides the band.
- **Auto-promote when the challenger wins on N runs.** Rejected: ADR-0013 requires gated promotion,
  and a fleet that retunes its own trading band without a human is a different system than the one
  the operator agreed to.

---

## Sequencing after merge

1. **S148 must be merged first.** If it is not, stop and say so.
2. `make ci` green locally, branch pushed, **all four remote gates green before merging locally**
   (DL-56).
3. Build + retag the fleet at `:s149`. **Behaviour does not change** — the mode ships `flat`.
4. **Let runs accumulate under `flat` with the counterfactual recorded.** The experiment needs data
   before anyone flips anything.
5. Run the comparison script and bring the numbers to the operator. **Promotion is their call.**
6. Record the functionality check in [`docs/laws/functionality-checks.md`](../laws/functionality-checks.md).
7. Add a `docs/design-log.md` thread for the flat-`stop_pct` finding above (next free number is
   **DL-76** unless something else has claimed it — check before writing).

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds, never a bare literal.
- Faults, not silent failure — `kernel.fault_boundary`, errors redirected with provenance.
- `make ci` all 9 steps green, **100.00 % coverage floor**, before handback. Never lower the floor.
- Version bump in `pyproject.toml` to **0.83.00** (feat → MINOR), `uv.lock` staged with it.
- Any law clause your tests cover cites the clause ID in the test docstring.
- If `main` has moved when you finish: merge `main` into the branch, resolve, re-run `make ci`, and
  **say so in the return notes** (DL-48).
- Secrets never through the worktree — chat or gitignored `.env` only.

---

## Handback contract — MANDATORY

**Append your results INSIDE this file, at the bottom, in the placeholder sections below.**

1. Fill the **Law reading record** *before* your first code change.
2. Fill the `**Result:**` line under **each** of the seven spec items, in place.
3. Fill the **Test plan results** table — one row per planned test. A test you chose not to write
   needs a reason, not a blank.
4. Fill the **Closeout — evidence** block with real command output.
5. Fill the **Return notes**, including **the `k`, floor and ceiling you chose and why**.
6. State any success factor you did **not** meet plainly, as "verified failing" or "not done"
   (LAW-02 — a proven failure is a valid handback, a silent gap is not).

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? (yes + what / no) |
| --- | --- | --- | --- |
| `agents/portfolio_manager/` — carrying `atr_pct` | | | |
| `contracts/portfolio_manager.py` — the new field | | | |
| `agents/analyst/` (read-only) | | | |
| `agents/execution/settings.py` — mode + tunables | | | |
| `agents/execution/alpaca_orders.py` + resolution | | | |
| the comparison script | | | |
| `trading_graph_vocabulary.json` | | | |

**Contradictions found between a law and this spec** (a contradiction is a success — name it):

**Laws found silent where a decision was needed** (each needs a `drift-register.md` row):

**Clauses that were ⬜ unproven in `test-plan.md` and are now proven by this sprint's tests:**

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | | | | |
| A2 | | | | |
| A3 | | | | |
| B1 | | | | |
| B2 | | | | |
| B3 | | | | |
| B4 | | | | |
| B5 | | | | |
| B6 | | | | |
| B7 | | | | |
| B8 | | | | |
| C1 | | | | |
| C2 | | | | |
| C3 | | | | |
| D1 | | | | |
| D2 | | | | |
| D3 | | | | |
| D4 | | | | |
| D5 | | | | |
| E1 | | | | |
| E2 | | | | |
| E3 | | | | |
| E4 | | | | |

**Tests added beyond the plan:**

---

## Closeout — evidence

**Files changed:**

_(fill in)_

**Proven (LAW-02):**

_(paste real command output: `make ci` counts and coverage, remote gate job IDs and results,
planted-violation runs, vocabulary script output, and a sample comparison-script report)_

**The `k`, floor and ceiling shipped, and why:**

_(fill in — the values, their bounds, and the `why` strings)_

**Not met / verified failing:**

_(fill in)_

---

## Return notes

_(fill in: what surprised you; whether `atr_pct` turned out to be a good proxy or a poor one; what
you deliberately did not do; whether the flat-`stop_pct` finding got its design-log thread; and
whether `main` had moved when you finished)_
