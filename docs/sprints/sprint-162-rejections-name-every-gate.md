<!-- Agent: planning | Role: sprint handover -->
# Sprint 162 — A rejection names one gate and hides the rest

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-162-rejections-name-every-gate`
**Status:** SPEC — makes the S161 sizing gate provable in production
**Version:** feat → **0.89.00** (MINOR: new evidence carried on an existing contract)
**Effort:** M
**Decisions:** [S161](sprint-161-pm-knows-what-it-paid.md) the sizing fix this makes provable ·
[S160](sprint-160-shadow-book.md) the shadow book that reads these reasons ·
[DL-93](../design-log.md) sizing/cap/sell-policy · [DL-70](../design-log.md) plant the violation ·
[LAW-02](../../ops/laws/LAW-02-proof.md) success is proven, never assumed

> **Why MINOR.** This is a fix in motivation — the system could not prove its own gate — but the
> mechanism is **new evidence recorded on an existing contract**, which is new capability by the
> CLAUDE.md rule. Same call S147 and S161 made. `0.88.00` → **`0.89.00`**. If you disagree after
> reading the rule, say so in the return notes.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED v1. Read-only. Never edit.** A clause you believe is wrong is a `drift-register.md` row plus a report |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`OUT`** (what a `RejectedOrder` carries), **`IDN`** (who owns `PMRun`),
**`OBS`** (reconstructability).

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read each agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Also read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Write the Law reading record** (template at the bottom) **before** your first code change.
5. **If a law contradicts this spec, STOP and report.** A contradiction you surface is a success —
   this happened on S160 and produced a better design.
6. **If a law is silent**, that silence is a finding: record it and add a `drift-register.md` row.
7. Every test for behaviour a clause governs **cites the clause ID in its docstring**.

### 🚨 Read `PM-OUT-03` first — it is the clause this sprint is arguing with

Measured on `main`, `PM-OUT-03` reads:

> Each `RejectedOrder` carries the original recommendation plus a `reason` string that names the
> gate that blocked it (`"max_positions"`, `"sector_cap"`, `"reward_risk_below_floor"`,
> `"provider_degraded"`, etc.). **Silence is always attributed.**

Two things follow, and you must decide both before coding:

- **This sprint is arguably completing `PM-OUT-03`, not extending it.** "Silence is always
  attributed" is precisely what fails today when two gates block and only one is named. Read the
  clause and say in the reading record whether you agree.
- Unlike `PM-OUT-02` (which enumerates a closed field list for `OrderIntent`), `PM-OUT-03` names no
  closed list — it says "the original recommendation plus a `reason`". Adding an **additive,
  defaulted** field is very likely lawful. **If you conclude otherwise, stop and report** — that is
  a law-amendment cycle, not something to smuggle in (the S160 wall).

📌 **Measured discrepancy, already found for you — do not re-investigate, just file it.**
`PM-OUT-03`'s illustrative reason strings do not match what the code emits. The law says
`"sector_cap"` and `"reward_risk_below_floor"`; the code emits `"sector_concentration"`
([`risk.py:179`](../../agents/portfolio_manager/domain/risk.py#L179)) and `"reward_risk_below_min"`
([`gate_report.py:149`](../../agents/portfolio_manager/domain/gate_report.py#L149)). The clause says
"etc.", so the list is illustrative and this is **not** a contradiction — but it **is** drift, and it
needs a `drift-register.md` row. Do not rename the code to match the law; the reason strings are
consumed by S160's shadow book.

### Element → law map (read all of these)

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `contracts/portfolio_manager.py` — `RejectedOrder` (item 1) | `agents/portfolio_manager/laws/laws.md` + `test-plan.md` | `PM-OUT-01` the `OrderIntentSet` shape; `PM-OUT-03` what a rejection carries (see 🚨 above); `PM-OUT-02` for the precedent — `OrderIntent.gate_report` already exists and is the shape to copy |
| `agents/portfolio_manager/domain/{gate_report,risk,exits,concentration}.py` (item 2) | `agents/portfolio_manager/laws/laws.md` + `test-plan.md` | `PM-IDN-01` sole job; `PM-NEV-*` what it must never do; the sizing/risk-gate clauses |
| `agents/portfolio_manager/poll.py`, `result.py` (item 3) | same, plus `docs/laws/conventions.md` | `PM-IDN-02` exclusive ownership of `PMRun`; `PM-OBS-01` every `PMRun` is fully reconstructable — **this sprint makes that clause more true, so read it and say whether it is currently ⬜** |
| `orchestration/batch_trace.py`, `orchestration/packs/trading_observatory_views.py` (item 4) | `docs/laws/conventions.md` | Read-only renderers; no agent law owns them |

---

## Why this sprint

**On 2026-08-07 the pipeline produced exactly the right answer and could not prove it.**

Run `sched-2026-08-06` (fired 22:30 UTC, the first scheduled run on the `:s161` fleet) completed
**8/8 stages, ACCEPTANCE PASS**, zero faults, flags or escalations. S161's closeout named three
success factors for that run. Measured against the graph:

| S161 success factor | Result |
| --- | --- |
| `account_equity_cents` non-null and fresh on the snapshot | ✅ **proven** — `10314991` (`$103,149.91`), `account_status="fresh"` |
| Zero new buy approvals | ⚠️ **observed, but not attributable to the fix** |
| Sells never blocked | ❌ **never exercised** — monitor `checked=10 closes=0 holds=10`; no sell was proposed |

The analyst produced one `buy` (MSFT, conf 0.64). The PM rejected it, and the trace says:

```text
[pm]
  approved=0  rejected=11
  MSFT   SKIP  max_positions
```

`max_positions` — the ten-slot cap — not the account-backed cash gate S161 shipped. Both blocked it.
Only one was recorded.

### Why only one

[`position_outcomes`](../../agents/portfolio_manager/domain/gate_report.py#L32) eagerly computes
**all four** gates for a buy — `sizing`, `min_order_quantity`, `max_positions`, `cash_available` —
and returns them as a tuple. Then
[`position_rejection`](../../agents/portfolio_manager/domain/gate_report.py#L94) walks that tuple and
returns on the **first** failure with a mapped reason:

```python
reasons = {
    "min_order_quantity": "below_min_quantity",
    "max_positions": "max_positions",
    "cash_available": "insufficient_cash",
}
for outcome in outcomes:
    reason = reasons.get(outcome.name)
    if reason is not None and not outcome.passed:
        return RejectedOrder(ticker=ticker, reason=reason)
```

`max_positions` is checked before `cash_available`, so it claims the rejection. The `cash_available`
outcome — **already computed, sitting in the same tuple** — is discarded, because
[`RejectedOrder`](../../contracts/portfolio_manager.py#L45) has only two fields:

```python
class RejectedOrder(_Frozen):
    ticker: Ticker
    reason: str
```

Meanwhile [`OrderIntent`](../../contracts/portfolio_manager.py#L42) — the **approved** path — already
carries `gate_report: tuple[GateOutcome, ...] = ()`. **The asymmetry is the defect: we keep the full
evidence when we say yes, and one word when we say no.** An approval is the case where you least
need the reasoning; a rejection is where you most need it.

### What that cost, concretely

Measured on the same run: equity `$103,149.91`, deployed market value `$208,116.69` across ten
holdings — **2.02×**, cash `−$104,966.77`. `available_for_buys` = equity × (1 − buffer) − deployed
is deeply negative, so `cash_available` **certainly** failed. But "certainly" is a derivation I did
by reading the source, not a fact the system recorded. **LAW-02 says a proven result, and there
isn't one.** S161's central behaviour has been running in production for a day with no evidence it
has ever fired.

**Waiting does not fix this.** While the book sits at 10/10, `max_positions` shadows the sizing gate
on every future run too. A monitor close is the only thing that frees a slot, and today all ten
holdings are rated `hold`. The system cannot answer the question until it is taught to record it.

### The second consumer

S160's shadow book classifies each recommendation from
`PMRun.order_intent_set.rejected[].reason`, and its 🎯 headline cut is `taken` vs
`blocked_capacity`. From the `:s161` fleet onward, a buy that fails **both** `max_positions` and
`cash_available` is labelled `blocked_capacity` — implying the counterfactual "we would have taken it
with a free slot", which is **false**; we could not have afforded it either.

⚠️ **Scope this claim precisely.** S160's two measured `blocked_capacity` dispositions
(`sched-2026-08-04/05`) were on the `:s158` fleet, where the PM still believed it had a fictional
`$100,000` and `cash_available` genuinely passed. Those two are correctly labelled. It is
**2026-08-06 onward** that is contaminated. Item 5 records this; it does not fix it.

---

## 🪤 The traps that will bite you

**1 · Every module you need to touch is nearly at the hard block.** Measured on `main`:

| File | Lines | Headroom to the 200-line block |
| --- | --- | --- |
| `orchestration/packs/trading_observatory_views.py` | 197 | **3** |
| `agents/portfolio_manager/domain/gate_report.py` | 192 | **8** |
| `orchestration/batch_trace.py` | 187 | 13 |
| `agents/portfolio_manager/domain/risk.py` | 180 | 20 |
| `agents/portfolio_manager/domain/concentration.py` | 163 | 37 |

**You will have to split modules, and that is the real work of this sprint.** Plan the split before
you write the feature, not after `make ci` blocks you. No `# noqa`.

**2 · Not every entry in the report is a gate that can block.** Do not describe the field as "the
gates that were checked" without qualification:

- `sizing` has **no mapped reason** in `position_rejection` and cannot reject anything.
  [`size_quantity`](../../agents/portfolio_manager/domain/sizing.py) derives the quantity from
  `portfolio_value × max_position_pct / price`, so `cost ≤ max_position_pct × value` holds by
  construction — `sizing` is an *observation*, not a gate.
- On the **sell** path, [`exit_outcomes`](../../agents/portfolio_manager/domain/exits.py#L35)
  hardcodes `passed=True` for `sizing`, `max_positions` and `cash_available`. Only
  `min_order_quantity` can fail a sell.

So `passed=False` reliably means "this blocked it", but `passed=True` does **not** uniformly mean "a
real gate approved it". Say this in the field's docstring.

**3 · A partial report must never read as "everything else passed."** Evaluation short-circuits (see
item 3), so gates *after* the rejection point were never computed and are simply absent. An absent
gate is unknown, not passing. If you cannot make that unambiguous in the data, make it unambiguous
in the docstring and the renderer.

**4 · This does not answer 2026-08-07 retroactively.** The graph is append-only and existing `PMRun`
nodes carry no gate report. **Do not backfill, do not recompute, do not edit a stored
`order_intent_set`.** This sprint makes the *next* run answerable. Say so plainly in the closeout so
nobody expects the history to fill in.

**5 · Old data must still parse.** [`batch_trace.py:134`](../../orchestration/batch_trace.py#L134)
does `OrderIntentSet.model_validate(pm_node.props["order_intent_set"])` over **historical** runs.
The new field must be **defaulted** (`= ()`), exactly like `OrderIntent.gate_report`, or every
pre-S162 run stops rendering.

**6 · No vocabulary change is needed — measured, do not add one.** `PMRun` appears in the pack's
`labels` list but **not** in `properties` (only **5** labels are property-enforced), and
[`poll.py:76`](../../agents/portfolio_manager/poll.py#L76) writes the whole set as a single JSON
prop:

```python
graph.merge_node("PMRun", result.run_id, {"order_intent_set": result.model_dump(mode="json")})
```

Nested fields inside that JSON are not guarded. **This sprint therefore has no pack/image coupling
and cannot repeat the S148 stall (DL-85).** If you believe a declaration is needed, say why in the
return notes before adding one.

---

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it.

### 1 · `RejectedOrder` carries the gate outcomes that were evaluated

Add `gate_report: tuple[GateOutcome, ...] = ()` to
[`RejectedOrder`](../../contracts/portfolio_manager.py#L45), mirroring `OrderIntent.gate_report`.

- **Defaulted, additive, never required** — trap 5.
- Give it a docstring that states the semantics decided in item 3 and the caveat in trap 2.

**Result:**

### 2 · Every rejection site attaches what it actually computed

| Site | File | Attach |
| --- | --- | --- |
| Position/exit gates | `domain/gate_report.py::position_rejection` | the full `outcomes` tuple it already receives — **this is the one that answers the MSFT question** |
| Reward/risk | `domain/gate_report.py::reward_risk_rejection` | the position gates (all passed) **plus** the failing `reward_risk` outcome |
| Sector | `domain/risk.py::_sector_rejection` and `domain/concentration.py` | position gates + `reward_risk` + the sector outcomes |
| Pre-gate | `domain/risk.py::_precheck` | `()` — nothing was evaluated, and that emptiness is honest |
| Portfolio-level | `result.py::reject_all` | `()` — same reason |

⚠️ `_sector_rejection` in `risk.py` and the rejection builder in `concentration.py` emit the **same
two reason strings** from two places. Reconcile or deliberately leave both — but say which, and why,
in the return notes.

**Result:**

### 3 · 🎯 Decide the reporting semantics explicitly, and write down why

This is the judgement call of the sprint. **State the decision and the rejected option in the return
notes** (LAW-06).

| Option | What it means | Consequence |
| --- | --- | --- |
| **Report what was evaluated** (short-circuit preserved) | attach the outcomes computed up to the rejection point | no behaviour change, no new failure modes; the report is partial by design — **recommended** |
| Evaluate every gate, always | drop the short-circuit, compute all gates, then reject | a complete picture, but gates would run on inputs the earlier gate already rejected (e.g. sector cost derived from a quantity that failed sizing), inventing new failure modes inside a defect fix |

**Recommended: report what was evaluated.** The MSFT case is already answered by it —
`position_outcomes` computes all four gates eagerly, so a rejection at `max_positions` still carries
the failing `cash_available`. The extra risk of the second option buys gates that were, by
definition, not part of the decision.

**Non-negotiable:** whichever you choose, an absent gate must not be readable as a passing gate
(trap 3), and the decision must be stated in the contract docstring — not only in this file.

**Result:**

### 4 · The evidence is visible where the question is actually asked

The point is answering "how did we go" without a graph query. Both read-only renderers must show the
other failing gates:

- [`orchestration/batch_trace.py:144`](../../orchestration/batch_trace.py#L144) — currently
  `MSFT   SKIP  max_positions`
- [`orchestration/packs/trading_observatory_views.py:149`](../../orchestration/packs/trading_observatory_views.py#L149)
  — the same row in the observatory view

Keep it compact and glance-first; a rejection with one failing gate must not get noisier. Something
of the shape `MSFT SKIP max_positions (also failed: cash_available)` — the exact wording is yours.

⚠️ `trading_observatory_views.py` has **3 lines** of headroom (trap 1). Split first.

**Result:**

### 5 · Record what this means for the shadow book — do not change it

S160's `blocked_capacity` disposition becomes ambiguous the moment two gates fail together (see *The
second consumer*).

- Add a **[`docs/design-log.md`](../design-log.md)** entry recording it: the disposition is read from
  a single `reason`, the gate report now shows when that reason was not the only blocker, and the
  `taken` vs `blocked_capacity` cut must be read with that caveat from **2026-08-06 onward**
  (`sched-2026-08-04/05` are unaffected — they ran on `:s158`).
- **Do not re-classify dispositions and do not touch the scorecard.** That is a shadow-book change
  with its own evidence question; this sprint records the finding so it is not lost (LAW-06).

**Result:**

### 6 · Prove the checks can fail (DL-70)

Every test plants the violation and requires the failure. **Watch each one fail before trusting it** —
an S160 test passed its own planted violation because the fixture was symmetric and proved nothing,
and an S151 assertion measured the fake's own storage rather than the behaviour.

**Result:**

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 **the 2026-08-07 regression** | equity `$103,149.91`, deployed `$208,116.69`, ten holdings, one MSFT `buy` | the rejection reason stays `max_positions` **and** the gate report contains `cash_available` with `passed=False`. **Name the date in the docstring** — this is the run that could not prove itself |
| A2 | a rejection reports only what was evaluated | a buy failing `min_order_quantity` | gates computed by `position_outcomes` are present; `reward_risk` and the sector gates are **absent**, not `passed=True` |
| A3 | reward/risk rejection carries the passing position gates | a buy passing position gates, failing reward/risk | report holds four passing position gates **plus** the failing `reward_risk` |
| A4 | sector rejection carries everything before it | a buy failing `max_names_per_sector` | position gates + `reward_risk` + the failing sector outcome |
| A5 | pre-gate rejections carry an empty report | a `hold` recommendation | `reason="hold_recommendation"`, `gate_report=()`. **Assert emptiness explicitly** so a future change cannot silently start half-filling it |
| A6 | the portfolio-level path is unchanged | provider unavailable | `reject_all` rejects every recommendation with `gate_report=()` |
| B1 | 🪤 **historical runs still parse** | a stored `order_intent_set` JSON with **no** `gate_report` key on its rejections | `OrderIntentSet.model_validate` succeeds and yields `()`. **Use a real pre-S162 shape**, not one produced by the new code — a round-trip through the new model proves nothing |
| B2 | sells still carry their report | a sell rejected on `min_order_quantity` | the exit gates are attached; the sell path is otherwise untouched |
| C1 | the trace renders the extra gates | a rejection failing two gates | both appear in `batch_trace` output |
| C2 | the trace stays quiet on a single failure | a rejection failing one gate | output is unchanged from today — no new noise |
| C3 | the observatory view matches the trace | the same rejection | the observatory row names the same gates |

---

## Explicit non-goals

- **No backfill, no recompute, no edit of any stored `order_intent_set`.** Trap 4.
- **No disposition or scorecard change in the shadow book.** Item 5 records; it does not fix.
- **No `max_positions` / `max_position_pct` / `cash_buffer_pct` change.** DL-93 owns those, and
  changing one here would confound the evidence fix with the policy decision it exists to inform.
- **No change to which orders are approved or rejected.** If any approval count moves, you have
  changed behaviour — stop and report. This sprint changes *what is recorded*, nothing else.
- **No selling, no deleveraging.** Unchanged from S161 item 5; ADR-0017 is not reversed.
- **No `laws.md` edits.** LOCKED v1. Findings go to `drift-register.md`.

### The road not taken (LAW-06)

- **Reorder `position_rejection` so `cash_available` is checked before `max_positions`.** One-line
  diff, and rejected: it swaps which single gate is hidden. The next question ("was it *also* over
  the slot cap?") becomes unanswerable instead, and the reason strings S160 consumes would shift
  meaning underneath it.
- **Derive the missing gates read-only, S160-style, from the stored `PMRun` snapshot and
  recommendations.** Genuinely tempting — it would answer 2026-08-07 retroactively and write
  nothing. Rejected for this sprint: it reimplements the gate logic in a second place, so the
  derivation and the PM can disagree, and a disagreement would be undetectable. Recording at the
  source is the version that cannot drift. **Worth reconsidering as a one-off diagnostic** if the
  history ever needs answering.
- **Log the failing gates to a `Fault` instead of the contract.** Rejected: a rejection is a normal
  outcome, not a fault, and `PM-OBS-02` routes faults for degradation and errors. It would also make
  the evidence unreachable from the `PMRun` that produced it (`PM-OBS-01`).
- **Widen `reason` into a tuple of reasons.** Rejected: it breaks S160's consumer and the `PM-OUT-03`
  contract for a strictly weaker result — reason strings carry no `value`, `threshold` or `detail`,
  which is exactly what makes "how badly did it fail" answerable.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**, then merge to `main` and push.
2. **A fleet retag IS required** — this changes what agents record. **No vocabulary pack change is
   involved** (trap 6), so unlike S161 this is an image move only; confirm that reading before
   relying on it.
3. **Watch the first scheduled run.** Expect **approved=0 / rejected=11 again with identical reason
   strings** — the approval decisions must not move (non-goal 4). What changes is that the MSFT row
   now names `cash_available` alongside `max_positions`. **That is the deliverable.**
4. Record the functionality check in [`docs/laws/functionality-checks.md`](../laws/functionality-checks.md),
   and state plainly whether S161's sizing gate is now **proven** to have fired in production —
   which was the open question this sprint exists to close.
5. Then DL-93's resize decision has the evidence it has been waiting on.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass. **Read trap 1 —
  five of the files you will touch are between 163 and 197 lines.**
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 11 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — redirect to a file and read the file (row S).
- Version bump to **0.89.00**, `uv.lock` staged with it.
- Money in integer cents. Never floats.
- If `main` has moved: merge it in, re-run `make ci`, and **say so in the return notes** (DL-48).
- Secrets never through the worktree — a worktree has **no `.env`**, so any proof needing live data
  is vacuous there. State which tree you ran in.

---

## Handback contract — MANDATORY

Append results **inside this file**, in the placeholders below.

1. Fill the **Law reading record** *before* your first code change.
2. Fill the `**Result:**` line under **each** of the six items.
3. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
4. Fill **Closeout — evidence** with real pasted output: `make ci`, `make gate-ran`, remote gates,
   the planted-violation runs, and **the module line counts after your splits**.
5. Fill **Return notes**, including the item-3 semantics decision and its rejected option.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02).

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? (yes + what / no) |
| --- | --- | --- | --- |
| `RejectedOrder` contract | | | |
| PM rejection sites | | | |
| `PMRun` persistence | | | |
| Read-only renderers | | | |

**Do you agree this sprint completes `PM-OUT-03` rather than extending it?** (see the 🚨 block)

**Contradictions found between a law and this spec:**

**Laws found silent where a decision was needed** (each needs a `drift-register.md` row):

**Drift row filed for the `PM-OUT-03` reason-string mismatch** (row ID):

**Clauses that were ⬜ and are now proven by this sprint's tests:**

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | | | | |
| A2 | | | | |
| A3 | | | | |
| A4 | | | | |
| A5 | | | | |
| A6 | | | | |
| B1 | | | | |
| B2 | | | | |
| C1 | | | | |
| C2 | | | | |
| C3 | | | | |

**Tests added beyond the plan:**

---

## Closeout — evidence

**Tree the proofs ran in (and `.env` present?):**

**Item 3 decision — reporting semantics chosen, and why:**

**Module splits made, with before/after line counts:**

**Files changed:**

**Proven (LAW-02):**

**Planted violations watched fail:**

**Final full gate:**

**Remote gate / gate-ran / merge:**

**Confirmation that no approval decision moved:**

**Not met / verified failing:**

---

## Return notes
