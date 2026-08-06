<!-- Agent: planning | Role: sprint handover -->
# Sprint 161 — The PM knows what it holds but not what it paid

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-161-pm-knows-what-it-paid`
**Status:** SPEC — closes the margin defect that gates every DL-93 decision
**Version:** feat → **0.88.00** (MINOR: new execution-recorded fact + new PM input)
**Effort:** M
**Decisions:** [DL-93](../design-log.md) sizing/cap/sell-policy · [DL-44](../design-log.md) broker is
truth for holdings · [ADR-0016](../decisions/0016-one-run-one-evidence-both-directions.md) one run,
one evidence set · [S147](sprint-147-fresh-book-before-decision.md) the head-of-run sync this extends ·
[DL-70](../design-log.md) plant the violation · [DL-73](../design-log.md) **(RETRACTED — read before
auditing any position)**

> **Why MINOR.** This fixes a defect, but the mechanism is a **new fact recorded by execution** plus a
> **new PM input** — new capability by the CLAUDE.md rule, the same call S147 made. `0.87.01` →
> **`0.88.00`**. If you disagree after reading the rule, say so in the return notes.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED v1. Read-only. Never edit.** A clause you believe is wrong is a `drift-register.md` row plus a report |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`IDN`** (who may write the new fact), **`NEV`**, **`DEP`** (the broker
boundary), **`IDM`**, **`FAIL`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read each agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Also read [`docs/laws/dependencies.md`](../laws/dependencies.md) (`DEP-BROKER` governs the Alpaca
   boundary), [`docs/laws/conventions.md`](../laws/conventions.md), and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Write the Law reading record** (template at the bottom) **before** your first code change.
5. **If a law contradicts this spec, STOP and report.** A contradiction you surface is a success —
   this happened on S160 and produced a better design.
6. **If a law is silent**, that silence is a finding: record it and add a `drift-register.md` row.
7. Every test for behaviour a clause governs **cites the clause ID in its docstring**.

### 🚨 Read this before anything else — S160 hit exactly this wall

**S160 was stopped at this gate** because no locked constitution owned the label it needed.
**Item 1 of this sprint has the same risk**, so resolve it *first*:

- Execution must record account cash. **Check `EXEC-IDN-02` before designing anything.** If it
  enumerates `BrokerPositionSnapshot`, adding **properties** to that existing snapshot is very
  likely lawful, while adding a **new label** may not be.
- **Strongly prefer extending the existing execution-owned snapshot** over inventing a label. It is
  written once per run at the head of the run (S147) — exactly where account state belongs.
- If you conclude a new label is genuinely required, **stop and report**. That is a law-amendment
  cycle, not a thing to smuggle in. DRIFT-034 already records that the book has no home for such a
  case.

### Element → law map (read all of these)

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| Execution's run-start snapshot (item 1) | `agents/execution/laws/laws.md` + `test-plan.md`; `docs/laws/dependencies.md` | `EXEC-IDN-01` **sole broker interface** — the PM may not call the broker; `EXEC-IDN-02` owned labels (**check whether `BrokerPositionSnapshot` is even declared** — DRIFT-025 says it was not); `EXEC-FAIL-02` degrade without crashing; `DEP-BROKER-01/02` |
| `agents/portfolio_manager/graph_portfolio.py`, `portfolio.py`, `domain/sizing.py`, `domain/risk.py` (items 2–4) | `agents/portfolio_manager/laws/laws.md` + `test-plan.md` | `PM-IDN-*` what the PM owns; `PM-NEV-*` what it must never do — **specifically whether it may touch the broker** (it must not); the sizing/risk-gate clauses |
| `orchestration/packs/trading_graph_vocabulary.json` | `docs/laws/conventions.md` | S143/S144: new props/labels must be declared or the guard throws **fail-closed on the first write** |

---

## Why this sprint

**The PM believes it has $100,000 of untouched cash at the start of every single run.**

Measured 2026-08-06 on the live Alpaca paper account:

```text
equity        104,042.69
cash         -104,966.77      <- negative
market value  209,009.46      <- 2.01x equity
```

The account is on **~2× margin**. The cause is three lines that are each individually harmless:

| # | Fact | Evidence |
| --- | --- | --- |
| 1 | The live portfolio reads **positions** from the graph but sets **cash to a constant** | [`graph_portfolio.py:27`](../../agents/portfolio_manager/graph_portfolio.py#L27) — `cash=Money(amount=starting_cash)` |
| 2 | "Portfolio value" **is** that cash | [`portfolio.py`](../../agents/portfolio_manager/portfolio.py) — `def value(self): return self.cash.amount` |
| 3 | The constant is a tunable whose own `why` has expired | [`settings.py:22`](../../agents/portfolio_manager/settings.py#L22) — `starting_cash = tunable(Decimal("100000.00"), why="Seed the first PM slice with a paper portfolio **before execution lands**.")` |

So `size_quantity = 100000 × max_position_pct / price` — **a fixed ~$10,000 budget per order, every
night, forever, regardless of what has already been spent.** `reserved_cash` starts at `Decimal("0")`
each run ([`domain/risk.py:52`](../../agents/portfolio_manager/domain/risk.py#L52)) and only
accumulates *within* that run, so yesterday's spend is invisible.

**The asymmetry is the whole defect: the PM knows what it holds, but not what it paid.** S147 taught
it to read the position book from broker truth; nobody ever taught it to read the cash.

**`cash_buffer_pct` is not broken.** It faithfully holds back 5% of a number that stopped being true
the day execution landed. Same shape as `max_positions` in [DL-93](../design-log.md) — a parameter
enforcing a justification that lapsed.

**Why this gates everything else.** DL-93 leaves open whether to resize parcels and raise the slot
count. **Both are unsafe while this is broken**: resizing on top of a fictional cash base would
produce a hundred small wrongly-sized positions instead of ten large ones.

---

## 🪤 The trap that will bite you at the end

**Do not simply set cash to Alpaca's `cash` field.** It is **−$104,966**. A negative cash figure
makes `available = cash × (1 − buffer) − reserved` negative, the cash gate rejects everything, and
the pipeline stops approving orders **entirely** — a new, quieter version of the same blockage
(DL-93 records that the PM already approves nothing, three nights running).

**The sizing base is a design decision this sprint must make explicitly** (item 3), not a field to
copy. Getting the fix "working" while leaving the pipeline dead is not a success.

---

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it.

### 1 · Execution records account state at run start — lawfully

Execution already writes a fresh `BrokerPositionSnapshot` at the head of every run (S147). Extend
**that existing write** to also carry the account's cash, equity and buying power in integer cents.

- **`EXEC-IDN-01` makes execution the sole broker interface** — this read belongs to execution and
  nowhere else. The PM may not call the broker; neither may anything in `contracts/`.
- **Read `EXEC-IDN-02` first** (see the 🚨 block above). Prefer new **properties on the existing
  snapshot** over a new label. **If only a new label works, stop and report.**
- Broker failure must degrade, not crash: reuse the existing `stale` snapshot path and record a
  `Fault`. **A run that cannot read the account must not size against a stale number silently** —
  see item 4.
- Money in integer cents, matching `BrokerPosition`'s existing convention.

**Result:**

### 2 · The PM sizes against what it actually has

`portfolio_from_graph` reads the account figures from the latest fresh snapshot for the run instead
of `settings.starting_cash`.

- `starting_cash` remains **only** as the seed for a genuinely fresh paper account with no snapshot
  — and its `why` must be rewritten to say exactly that, since the current one is false.
- The PM still may not call the broker. It reads a fact execution wrote. Same shape as S147.

**Result:**

### 3 · 🎯 Decide the sizing base explicitly, and write down why

This is the judgement call of the sprint. **State the decision and the rejected options in the
return notes** (LAW-06), because the next person will need to know why.

| Base | What it means | Consequence |
| --- | --- | --- |
| Alpaca `cash` | settled cash, currently **−$104,966** | approves nothing; pipeline dies quietly |
| **`equity`** | cash + market value, currently **$104,042** | sizing tracks the real account; **recommended** |
| `buying_power` | margin-inclusive, currently $165,359 | explicitly authorises leverage — do not choose this without an operator decision |

**Recommended: `equity`,** because it is the number that answers *"how much do I actually have"*,
it cannot go negative while positions are held, and it makes the existing `max_position_pct` mean
what its name says — a fraction of the portfolio. **If you pick differently, justify it against
these three.** Whatever you choose, `PortfolioState.value` must stop being a synonym for `cash`.

**Non-negotiable:** the chosen base must make **leverage impossible by construction** under normal
operation — the sum of position values must not be able to exceed equity through repeated runs.
Prove it with the multi-run test in the plan (B3).

**Result:**

### 4 · A stale or unreadable account must not size silently

If the run has no fresh account figures, sizing against the last known number is exactly the
staleness S147 existed to remove.

- No fresh snapshot → the PM **does not approve new buys** and records a visible `Fault` naming the
  staleness. Exits are unaffected — **never block a sell**, for the same reason S147 chose
  fail-visible over fail-closed: a blocked run that cannot sell is an unbounded risk, while a
  blocked *buy* is merely a missed opportunity.
- This asymmetry is deliberate. Do not "simplify" it into blocking the whole run.

**Result:**

### 5 · Do not unwind the existing over-commitment

The book is already at ~2× and **this sprint must not sell anything to fix that.**

- Selling to deleverage is a **trading decision** that belongs to DL-93 and the operator, not to a
  defect fix. `ADR-0017` governs exits and is not reversed here.
- The correct behaviour after this fix is simply that the PM **stops adding** — with equity
  $104,042 and $209,009 already deployed, `max_position_pct` should approve **no new buys** until
  the book shrinks. **That is the fix working, not a new bug.** Say so plainly in the closeout.
- Report the expected post-fix state so the operator is not surprised by another zero-approval run.

**Result:**

### 6 · Declare every new prop in the vocabulary

The write guard is live on the fleet and **fails closed on the first write**.

- Add the new snapshot properties to
  [`orchestration/packs/trading_graph_vocabulary.json`](../../orchestration/packs/trading_graph_vocabulary.json).
- Re-run `scripts/vocabulary_coverage.py` and `scripts/vocabulary_signatures.py`; paste the output.
- ⚠️ **Image and pack move together at deploy** — a target on new code with a stale pack raises
  `VocabularyError` on its first write (the S148 stall, DL-85).

**Result:**

### 7 · Prove the checks can fail (DL-70)

Every test plants the violation and requires the failure. **Watch each one fail before trusting it**
— an S160 test passed its own planted violation because the fixture was symmetric and proved nothing.

**Result:**

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | execution records account state on the run-start snapshot | a stub broker with known cash/equity | the values land in cents on the fresh snapshot, keyed to the run |
| A2 | broker failure degrades, never raises | `account()` raises | snapshot `status="stale"`, exactly one `Fault`, **no exception escapes** |
| A3 | the write stays inside execution's declared labels | run the sync | labels written ⊆ `EXEC-IDN-02`'s enumeration. **Cite the clause** |
| B1 | 🎯 **the PM sizes against the account, not the constant** | a snapshot whose equity ≠ `starting_cash` | order size follows the **snapshot**; assert it differs from the `starting_cash` answer, so the constant cannot silently satisfy the test |
| B2 | 🎯 **the 2026-08 regression** | equity $104,042 with $209,009 already deployed | **zero** new buys approved. Name the date in the docstring — this is the outage in miniature |
| B3 | 🪤 **leverage is impossible across runs** | run sizing repeatedly against a shrinking account | total deployed never exceeds equity. **The old code passes run 1 and fails by run 3** — assert across runs, never a single run |
| B4 | sells are never blocked by a stale account | no fresh snapshot + a sell recommendation | the sell still proceeds; only buys are withheld |
| B5 | missing account figures block buys visibly | no fresh snapshot | no new buys **and** a `Fault` naming the staleness |
| C1 | `starting_cash` is used only with no snapshot | fresh paper graph | seeds correctly; with a snapshot present it is **never** consulted |
| C2 | every new prop is declared | the new props | guard accepts; then **plant an undeclared prop and require rejection** |

---

## Explicit non-goals

- **No selling, no deleveraging, no broker orders of any kind.** Item 5.
- **No `max_positions` change and no `max_position_pct` change.** DL-93 decides those *after* this
  lands; changing them here would confound the fix with a policy change.
- **No ADR-0017 reversal.** "Sell what is losing" stays open in DL-93.
- **No PM broker access.** `EXEC-IDN-01`. The PM reads a fact; it does not call Alpaca.
- **No `laws.md` edits.** LOCKED v1. Findings go to `drift-register.md`.

### The road not taken (LAW-06)

- **Let the PM call the broker for its own cash.** Smallest diff, and rejected: `EXEC-IDN-01` makes
  execution the sole broker interface, and a second agent on that boundary doubles the credential
  surface and rate-limit budget for one read. Identical to S147's reasoning.
- **Keep `starting_cash` and decrement it as orders fill.** Rejected: it rebuilds broker state from
  our own bookkeeping, which is precisely what DL-44 says not to do — the broker is truth. It also
  drifts on any fill we did not author.
- **Size against `buying_power`.** Rejected as a default: it *authorises* leverage rather than
  preventing it, and that is an operator decision, not a defect fix.
- **Fix it by lowering `max_position_pct`.** Rejected: it makes the symptom smaller while leaving
  the PM blind to its own spending. The leverage would return at a slower rate.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**, then merge to `main` and push.
2. **A fleet retag IS required** — this changes agent behaviour. **Image and vocabulary pack must
   move together** (item 6). This is also the deploy that finally gives hardening **row Q** its
   end-to-end confirmation: expect `[OK]` on all 17 targets, and any `[XX]` should now carry stderr.
3. **Watch the first scheduled run closely.** Expect **zero new buys** (item 5) — that is the fix
   working. Confirm the account figures appear on the snapshot and that no `Fault` fires spuriously.
4. Record the functionality check in [`docs/laws/functionality-checks.md`](../laws/functionality-checks.md).
5. **Then, and only then, DL-93's resize decision becomes safe to make.**

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 11 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — redirect to a file and read the file (row S).
- Version bump to **0.88.00**, `uv.lock` staged with it.
- Money in integer cents. Never floats.
- If `main` has moved: merge it in, re-run `make ci`, and **say so in the return notes** (DL-48).
- Secrets never through the worktree — a worktree has **no `.env`**, so any proof needing live data
  is vacuous there. State which tree you ran in.

---

## Handback contract — MANDATORY

Append results **inside this file**, in the placeholders below.

1. Fill the **Law reading record** *before* your first code change.
2. Fill the `**Result:**` line under **each** of the seven items.
3. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
4. Fill **Closeout — evidence** with real pasted output: `make ci`, `make gate-ran`, remote gates,
   the planted-violation runs, the vocabulary scripts, and **the expected post-fix approval count**.
5. Fill **Return notes**, including the item-3 sizing-base decision and its rejected options.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02).

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? (yes + what / no) |
| --- | --- | --- | --- |
| Execution run-start snapshot | | | |
| PM portfolio / sizing / risk gates | | | |
| `trading_graph_vocabulary.json` | | | |

**Contradictions found between a law and this spec:**

**Laws found silent where a decision was needed** (each needs a `drift-register.md` row):

**Clauses that were ⬜ and are now proven by this sprint's tests:**

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
| C1 | | | | |
| C2 | | | | |

**Tests added beyond the plan:**

---

## Closeout — evidence

**Tree the proofs ran in (and `.env` present?):**

**Item 3 decision — sizing base chosen, and why:**

**Files changed:**

**Proven (LAW-02):**

**Expected post-fix approval count, and why that is correct:**

**Not met / verified failing:**

---

## Return notes
