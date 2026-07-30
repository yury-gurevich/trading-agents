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

**Result:** Done. `OrderIntent` now carries optional/defaulted `decision_atr_pct`; legacy payloads
without the field still validate. The PM copies the existing analyst `QuantMetric(name="atr_pct")`
value unchanged through `agents/portfolio_manager/domain/volatility.py` into buy and sell
`OrderIntent`s, and leaves `None` when the metric is absent. Analyst code was read and left
unchanged.

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

**Result:** Done. `ExecutionSettings.order_price_tolerance_mode` defaults to `flat`, preserving the
S148 `order_price_tolerance_bps=50` path. The opt-in `scaled` challenger resolves
`round_half_up(atr_pct * 100 * k)` with `k=0.50`, then clamps to `floor_bps=25` and
`ceiling_bps=250`; all three scaled knobs are `kernel.tunable(...)` values with bounds and `why`
metadata. Resolution is deterministic and feeds the same bounded limit-order payload builder.

### 3 · A missing volatility degrades to flat — it never blocks a decision

- `decision_atr_pct` is `None` (no ATR: a short history, a new listing, a held position with no
  fresh recommendation) → fall back to the flat tolerance and **record that the fallback happened**.
- **Never** block, skip, or drop a decision because volatility is missing. A missing input is a
  degraded input, not a veto (`EXEC-FAIL-*`, DL-57).
- The floor and ceiling are the safety rails: **no ticker may end up with a tolerance so wide that
  ADR-0018 stops meaning anything**, and none so narrow that it can never trade. Prove both clamps.

**Result:** Done. `decision_atr_pct=None`, negative values, and NaN fall back to the flat 50 bps
champion and set `order_volatility_fallback=True`; they do not skip, reject, or drop the order.
Very small valid ATR clamps to 25 bps and absurdly high ATR clamps to 250 bps.

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

**Result:** Done. Every submitted/rejected Fill with order-tolerance evidence records the applied
mode, counterfactual mode, decided price, both tolerances, both limit prices, volatility presence,
and fallback flag. Replays append a new Fill attempt instead of rewriting the old one.
`scripts/compare_order_tolerances.py` reads those Fill facts and reports both modes; it never writes
or promotes a mode flip.

### 5 · Keep the S148 guarantees intact

- **Resting broker stops stay exempt.** They are not decisions and this sprint must not touch
  `submit_stop`, `stop_order_body`, or the drop sweep's stop exemption. Re-run S148's stop-safety
  tests unchanged and confirm they still pass.
- The drop sweep, `dropped` counting, and the reporter's dropped-vs-rejected handling are unchanged.
- `time_in_force` stays `day`.

**Result:** Done. Resting broker stops stay outside the tolerance path: `submit_stop` and the stop
payload remain `type=stop`, `time_in_force=gtc`, and the drop sweep's stop exemption still passes.
Bounded entry/exit orders still use `time_in_force=day`.

### 6 · Declare any new prop or edge in the vocabulary

- New props/edges go in [`trading_graph_vocabulary.json`](../../orchestration/packs/trading_graph_vocabulary.json).
- Re-run `scripts/vocabulary_coverage.py` and `scripts/vocabulary_signatures.py`; paste the output.

**Result:** Done. The new Fill tolerance evidence props are declared in
`orchestration/packs/trading_graph_vocabulary.json`. The same stricter property guard exposed
previously-declared-but-not-property-listed broker-stop Fill props (`position_ref`,
`stop_order_key`, `stop_pct`, `stop_pct_source`), so those are declared too. Final vocabulary
scripts:

```text
uv run python scripts/vocabulary_coverage.py
# exit 0, no stdout

uv run python scripts/vocabulary_signatures.py
# exit 0, no stdout
```

### 7 · Prove the checks can fail (DL-70)

Plant the violation and require the failure — the test plan specifies the violation for each test.

**Result:** Done. Planned tests plant violations with `pytest.raises(AssertionError)` or explicit
guard rejection: fabricated missing-ATR defaults, unclamped absurd ATR, one-sided counterfactual
evidence, missing-drop behavior, invalid mode strings, bare non-tunable settings, and undeclared
Fill props all fail when planted.

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
| `agents/portfolio_manager/` — carrying `atr_pct` | `agents/portfolio_manager/laws/laws.md`; `agents/portfolio_manager/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/dependencies.md`; `docs/laws/drift-register.md` | `PM-IDN-01`, `PM-IDN-02`, `PM-OUT-01`, `PM-OUT-02`, `PM-NEV-01`, `PM-NEV-04`, `PM-TYP-03`, `PM-OBS-01` | No - the PM remains a courier. It may copy the analyst's existing metric onto the intent, but must not compute, smooth, clamp, or interpret execution tolerance. |
| `contracts/portfolio_manager.py` — the new field | `agents/portfolio_manager/laws/laws.md`; `agents/portfolio_manager/laws/test-plan.md`; `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `PM-IDN-02`, `PM-OUT-02`, `PM-TYP-03`, `EXEC-IN-01`, `EXEC-NEV-01`, `EXEC-NEV-02`, `EXEC-TYP-03` | No - make the field optional/defaulted for old payload compatibility, and keep execution as the only component that resolves a tolerance from it. |
| `agents/analyst/` (read-only) | `agents/analyst/laws/laws.md`; `agents/analyst/laws/test-plan.md`; `docs/laws/conventions.md` | `ANLZ-OUT-01`, `ANLZ-OUT-02`, `ANLZ-NEV-01`, `ANLZ-STA-02`, `ANLZ-TYP-01`, `ANLZ-OBS-01` | No - the analyst law confirms it owns Recommendation output and must not size/order. `atr_pct` will be consumed from declared `quant_metrics`; analyst code stays untouched. |
| `agents/execution/settings.py` — mode + tunables | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `EXEC-IDN-01`, `EXEC-PARAM`, `EXEC-IDM-01`, `EXEC-IDM-02`, `EXEC-FAIL-01`, `EXEC-TYP-03`, `EXEC-OBS-01` | Yes - the `PARAM` section is silent on S148/S149 tolerance controls, so the implementation must keep the locked law read-only and add DRIFT-027 instead of editing `laws.md`. |
| `agents/execution/alpaca_orders.py` + resolution | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/dependencies.md`; `docs/laws/drift-register.md`; ADR-0018 | `EXEC-IDN-01`, `EXEC-NEV-01`, `EXEC-NEV-02`, `EXEC-NEV-03`, `EXEC-IDM-01`, `EXEC-IDM-02`, `EXEC-FAIL-01`, `EXEC-FAIL-02`, `EXEC-OBS-01`, `DEP-BROKER-01`, `DEP-BROKER-02` | Yes - missing or nonsensical volatility must degrade to flat and still submit; only broker failure/stage gates may reject. Stops remain outside tolerance handling. |
| the comparison script | `docs/laws/conventions.md`; `docs/laws/dependencies.md`; ADR-0013; ADR-0018 | `DEP-POSTGRES-03`, `DEP-CLOCK-01`; ADR-0013 gated promotion; ADR-0018 same-session decision validity | No - script must be read/report only, use append-only graph evidence, and never mutate settings or promote a challenger. |
| `trading_graph_vocabulary.json` | `docs/laws/conventions.md`; `docs/laws/drift-register.md` | conventions §§2, 3, 7, 9; S143/S144 vocabulary declaration rule | No - any new durable props must be declared and then proven by the vocabulary scripts. |

**Contradictions found between a law and this spec** (a contradiction is a success — name it):

None found. The spec fits the locked laws if the PM only carries a pre-existing analyst metric, execution owns tolerance resolution, and missing volatility degrades rather than blocks.

**Laws found silent where a decision was needed** (each needs a `drift-register.md` row):

`DRIFT-027` opened: execution's locked law is silent on S149's selectable order-tolerance mode, the scaled-tolerance tunables, and the counterfactual evidence props required to measure the challenger.

**Clauses that were ⬜ unproven in `test-plan.md` and are now proven by this sprint's tests:**

This sprint adds cited tests for PM volatility passthrough (`PM-IDN-01`, `PM-OUT-02`,
`PM-NEV-01`, `PM-OBS-01`, `PM-TYP-03`) and execution tolerance behavior/evidence
(`EXEC-IN-01`, `EXEC-NEV-01`, `EXEC-NEV-02`, `EXEC-NEV-03`, `EXEC-IDM-01`,
`EXEC-IDM-02`, `EXEC-FAIL-01`, `EXEC-OBS-01`, `EXEC-STA-03`, `EXEC-TYP-01`, plus
`EXEC-PARAM` as the local parameter-governance heading used by existing tests). Analyst clauses
remain read-only/out of scope; no analyst test status changed.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_pm_carries_atr_pct_onto_order_intent_unchanged` | `agents/portfolio_manager/tests/test_order_volatility.py` | PASS | `PM-IDN-01` / `PM-OUT-02` / `PM-NEV-01` / `PM-TYP-03` |
| A2 | `test_pm_missing_atr_pct_yields_none_not_a_guess` | `agents/portfolio_manager/tests/test_order_volatility.py` | PASS | `PM-IDN-01` / `PM-NEV-01` / `PM-OBS-01` |
| A3 | `test_order_intent_decision_atr_pct_is_optional_and_round_trips` | `tests/test_order_intent_contract.py` | PASS | `PM-TYP-03` / `EXEC-IN-01` |
| B1 | `test_flat_mode_ignores_volatility_and_matches_s148_payload` | `agents/execution/tests/test_scaled_order_tolerance.py` | PASS | `EXEC-NEV-01` / `EXEC-IDM-01` |
| B2 | `test_scaled_mode_resolves_exact_volatile_and_quiet_tolerances` | `agents/execution/tests/test_scaled_order_tolerance.py` | PASS | `EXEC-IDM-01` / `EXEC-NEV-01` |
| B3 | `test_scaled_mode_resolves_exact_volatile_and_quiet_tolerances` | `agents/execution/tests/test_scaled_order_tolerance.py` | PASS | `EXEC-IDM-01` / `EXEC-NEV-01` |
| B4 | `test_scaled_mode_floor_and_ceiling_clamps` | `agents/execution/tests/test_scaled_order_tolerance.py` | PASS | `EXEC-FAIL-01` / `EXEC-IDM-01` |
| B5 | `test_scaled_mode_floor_and_ceiling_clamps` | `agents/execution/tests/test_scaled_order_tolerance.py` | PASS | `EXEC-FAIL-01` / `EXEC-IDM-01` |
| B6 | `test_resolution_is_deterministic_for_same_intent_and_settings` | `agents/execution/tests/test_scaled_order_tolerance.py` | PASS | `EXEC-IDM-01` / `EXEC-IDM-02` |
| B7 | `test_scaled_tolerance_knobs_are_declared_tunables_and_mode_is_bounded` | `agents/execution/tests/test_scaled_order_tolerance.py` | PASS | `EXEC-PARAM` / `ADR-0013` |
| B8 | `test_scaled_tolerance_knobs_are_declared_tunables_and_mode_is_bounded` | `agents/execution/tests/test_scaled_order_tolerance.py` | PASS | `EXEC-PARAM` / `ADR-0013` |
| C1 | `test_missing_volatility_scaled_mode_falls_back_and_still_submits` | `agents/execution/tests/test_scaled_order_tolerance.py` | PASS | `EXEC-FAIL-01` / `EXEC-NEV-01` / `EXEC-OBS-01` |
| C2 | `test_missing_volatility_scaled_mode_falls_back_and_still_submits` | `agents/execution/tests/test_scaled_order_tolerance.py` | PASS | `EXEC-FAIL-01` / `EXEC-NEV-01` / `EXEC-OBS-01` |
| C3 | `test_nonsensical_volatility_is_missing_or_clamped_not_trusted` | `agents/execution/tests/test_scaled_order_tolerance.py` | PASS | `EXEC-FAIL-01` / `EXEC-IDM-01` |
| D1 | `test_flat_mode_fill_records_scaled_counterfactual` | `agents/execution/tests/test_tolerance_evidence.py` | PASS | `EXEC-OBS-01` / `EXEC-IDM-01` |
| D2 | `test_scaled_mode_fill_records_flat_counterfactual` | `agents/execution/tests/test_tolerance_evidence.py` | PASS | `EXEC-OBS-01` / `EXEC-NEV-01` |
| D3 | `test_tolerance_evidence_replay_appends_without_rewriting` | `agents/execution/tests/test_tolerance_evidence.py` | PASS | `EXEC-STA-03` / `EXEC-OBS-01` |
| D4 | `test_comparison_script_reports_both_modes_when_limits_differ` | `tests/test_compare_order_tolerances.py` | PASS | `EXEC-OBS-01` / `ADR-0013` |
| D5 | `test_comparison_script_never_writes_or_promotes` | `tests/test_compare_order_tolerances.py` | PASS | `EXEC-NEV-01` / `ADR-0013` |
| E1 | `test_sweep_exempts_resting_stops_and_prefixless_stop` | `agents/execution/tests/test_drop_sweep.py` | PASS | `EXEC-NEV-01` / `EXEC-NEV-03` |
| E2 | `test_stop_order_body_builds_exact_gtc_stop_payload` | `agents/execution/tests/test_alpaca_stop_orders.py` | PASS | `EXEC-NEV-03` / `EXEC-IDM-02` |
| E3 | `test_order_body_rounds_half_cent_up_and_keeps_day_tif` | `agents/execution/tests/test_order_tolerance.py` | PASS | `EXEC-IDM-01` / `EXEC-TYP-01` |
| E4 | `test_fill_tolerance_props_are_declared_and_unknown_prop_fails` | `tests/test_graph_vocabulary_completeness.py` | PASS | `EXEC-OBS-01` / `DL-70` |

**Tests added beyond the plan:**

- `test_partial_tolerance_evidence_omits_absent_optional_prices`
  (`agents/execution/tests/test_tolerance_evidence.py`) covers sparse/legacy tolerance evidence so
  absent optional money fields are omitted rather than serialized as fake prices.
- `orchestration/tests/test_graph_vocabulary_e2e.py::test_declared_vocabulary_admits_the_broker_native_stop_path`
  was re-run after the stricter Fill property guard exposed missing broker-stop Fill property
  declarations; this protects the S148/S142 stop path under S149's stricter vocabulary check.
---

## Closeout — evidence

**Files changed:**

- Portfolio manager contract/courier path:
  `contracts/portfolio_manager.py`,
  `agents/portfolio_manager/domain/volatility.py`,
  `agents/portfolio_manager/domain/gate_report.py`,
  `agents/portfolio_manager/domain/exits.py`,
  `agents/portfolio_manager/store.py`.
- Execution tolerance path:
  `agents/execution/settings.py`, `agents/execution/order_tolerance.py`,
  `agents/execution/domain/orders.py`, `agents/execution/domain/submit.py`,
  `agents/execution/run.py`, `agents/execution/agent.py`, `agents/execution/poll.py`,
  `agents/execution/broker.py`, `agents/execution/alpaca.py`,
  `agents/execution/paper_broker.py`, `agents/execution/store.py`,
  `agents/execution/tolerance_store_props.py`.
- Graph/vocabulary/reporting:
  `kernel/graph_vocabulary.py`, `kernel/graph_guarded.py`,
  `orchestration/packs/trading_graph_vocabulary.json`,
  `scripts/compare_order_tolerances.py`.
- Tests and fixtures:
  `agents/portfolio_manager/tests/test_order_volatility.py`,
  `agents/execution/tests/test_scaled_order_tolerance.py`,
  `agents/execution/tests/test_tolerance_evidence.py`,
  `tests/test_order_intent_contract.py`, `tests/test_compare_order_tolerances.py`,
  `tests/test_graph_vocabulary.py`, `tests/test_graph_vocabulary_completeness.py`,
  plus execution fake-broker signature updates in existing tests/helpers.
- Governance/versioning:
  `docs/laws/drift-register.md`, this sprint document, `pyproject.toml`, `uv.lock`.

**Proven (LAW-02):**

Precondition and branch:

```text
branch=sprint-149-volatility-scaled-tolerance
HEAD=e8bcca1
origin/main=e8bcca1
S148_73f0132_ancestor_of_origin_main=yes
```

Version/lock:

```text
uv lock
Resolved 170 packages in 3.43s
Updated trading-agents v0.82.0 -> v0.83.0
```

Focused and affected test evidence:

```text
uv run pytest agents/portfolio_manager/tests/test_order_volatility.py agents/execution/tests/test_order_tolerance.py agents/execution/tests/test_scaled_order_tolerance.py agents/execution/tests/test_tolerance_evidence.py tests/test_compare_order_tolerances.py tests/test_graph_vocabulary.py tests/test_graph_vocabulary_completeness.py tests/test_contract_values.py tests/test_order_intent_contract.py agents/execution/tests/test_execution_domain.py agents/execution/tests/test_drop_sweep.py agents/execution/tests/test_alpaca_stop_orders.py --no-cov
============================= 70 passed in 8.47s ==============================

uv run pytest agents/execution/tests agents/portfolio_manager/tests tests/test_contract_values.py tests/test_order_intent_contract.py tests/test_compare_order_tolerances.py tests/test_graph_vocabulary.py tests/test_graph_vocabulary_completeness.py orchestration/tests/test_realized_pnl_graph_pull.py --no-cov
============================ 233 passed in 11.08s =============================

uv run pytest agents/execution/tests/test_scaled_order_tolerance.py agents/execution/tests/test_tolerance_evidence.py orchestration/tests/test_graph_vocabulary_e2e.py tests/test_graph_vocabulary_completeness.py --no-cov
============================= 23 passed in 7.31s ==============================
```

Final local `make ci` (exit 0):

```text
uv run ruff check . --output-format=github
uv run ruff format --check .
851 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
Success: no issues found in 713 source files
uv run lint-imports
Contracts: 4 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests
# warnings only; no FAIL rows
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run pytest
================= 1950 passed, 5 skipped in 164.08s (0:02:44) =================
Required test coverage of 100.0% reached. Total coverage: 100.00%
uv run pip-audit
No known vulnerabilities found
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 9 new file(s)
```

Vocabulary scripts:

```text
uv run python scripts/vocabulary_coverage.py
# exit 0, no stdout

uv run python scripts/vocabulary_signatures.py
# exit 0, no stdout
```

Comparison script against the real configured graph, read-only (`.env` loaded, DSN not printed):

```text
PostgresGraphStore
mode	orders	would_have_filled	drop_rate_pct	avg_slippage_bps
flat	0	0	0.00	n/a
scaled	0	0	0.00	n/a
```

Synthetic report proving the modes can differ:

```text
mode	orders	would_have_filled	drop_rate_pct	avg_slippage_bps
flat	2	1	50.00	40.00
scaled	2	2	0.00	80.00
```

Planted-violation evidence:

- A2 plants a fabricated missing-ATR default and requires `None`.
- B5 plants the unclamped absurd-ATR result (`4950`) and requires the 250 bps ceiling.
- B7 plants bare literal scaled settings and requires tunable metadata to be present.
- B8 plants invalid mode `wide` and requires settings validation failure.
- C2 plants missing-volatility blocking (`submitted == 0`) and requires the order still submit.
- D2 plants one-sided evidence and requires the two-sided assertion to fail.
- E4 plants misspelled `order_tolerence_mode` and requires `VocabularyError`.

Remote gates:

```text
Pending until branch push; this line must be updated after the first remote run.
```

**The `k`, floor and ceiling shipped, and why:**

- `scaled_order_price_tolerance_atr_multiplier = 0.50`, bounded `ge=0.0`, `le=2.0`,
  unit `ratio`. Why: "Measure a challenger band near half of decision-time daily ATR; overnight
  gaps observed for S149 cluster around 0.3-0.6x ATR."
- `scaled_order_price_tolerance_floor_bps = 25`, bounded `ge=0`, `le=500`, unit `bps`.
  Why: "Keep the volatility-scaled challenger from becoming so narrow that quiet names cannot
  trade at all."
- `scaled_order_price_tolerance_ceiling_bps = 250`, bounded `ge=0`, `le=500`, unit `bps`.
  Why: "Keep the volatility-scaled challenger narrow enough that ADR-0018 still rejects materially
  unevaluated opens."
- The champion remains `order_price_tolerance_mode = "flat"` and `order_price_tolerance_bps = 50`.

**Not met / verified failing:**

- No local success factor is verified failing.
- The fleet was not retagged and the challenger was not enabled; that is deliberate non-goal scope.
- There are no production S149 tolerance rows yet; the real Postgres comparison report correctly
  returns zero orders until runs accumulate after merge/deploy.
- Remote gates are pending until this branch is pushed.

---

## Return notes

- Law reading changed the execution approach only where expected: the locked execution law is
  silent on S148/S149 tolerance details, so `DRIFT-027` was opened rather than changing `laws.md`.
  The PM/analyst boundary stayed clean: analyst unchanged, PM courier-only, execution owns the
  policy.
- `atr_pct` is a good enough proxy for this sprint because its unit is already percent of last
  close and it already crosses the analyst boundary as a typed `QuantMetric`. It is not proven
  superior to flat tolerance; the experiment exists to measure that.
- The stricter Fill property guard found a nearby defect: broker-stop Fill props were used by code
  but not declared in the new property vocabulary. Fixed here because S149's guard would otherwise
  break the stop path, but no stop semantics were changed.
- Deliberately not done: no analyst change, no default-on scaled mode, no tuning to a target drop
  rate, no per-ticker stop work, no fleet retag, no broker submission/live trade, and no automatic
  promotion.
- The flat-`stop_pct` finding already exists as `DL-76` on main, so I did not create a duplicate
  design-log thread.
- `origin/main` was fetched at closeout and remained `e8bcca1`, matching this branch base; no main
  merge was needed.
