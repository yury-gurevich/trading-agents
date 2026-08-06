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

**Result:** Done. Execution now reads broker account facts at run start and writes
`account_cash_cents`, `account_equity_cents`, `account_buying_power_cents`,
`account_status`, and optional `account_stale_reason` as properties on the existing
execution-owned `BrokerPositionSnapshot`. No new label was added. Alpaca account payloads are parsed
to integer cents; `PaperBroker` exposes a deterministic account for local/tests. Account read failure
writes a stale snapshot and a `Fault`; a positions-read failure keeps the existing stale path.

### 2 · The PM sizes against what it actually has

`portfolio_from_graph` reads the account figures from the latest fresh snapshot for the run instead
of `settings.starting_cash`.

- `starting_cash` remains **only** as the seed for a genuinely fresh paper account with no snapshot
  — and its `why` must be rewritten to say exactly that, since the current one is false.
- The PM still may not call the broker. It reads a fact execution wrote. Same shape as S147.

**Result:** Done. `portfolio_from_graph` reads the run's latest execution-written
`BrokerPositionSnapshot` and uses fresh account equity as the PM sizing base. `starting_cash` remains
only the no-snapshot bootstrap seed and its tunable rationale was rewritten. The PM still has no
broker dependency; it reads graph facts only.

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

**Result:** Done. Chosen base: Alpaca `equity`. `PortfolioState.value` is now the selected account
value, not a synonym for raw cash. Buy availability subtracts already deployed position value and
same-run reserved cash, making repeated-run leverage impossible under normal account-backed sizing.

### 4 · A stale or unreadable account must not size silently

If the run has no fresh account figures, sizing against the last known number is exactly the
staleness S147 existed to remove.

- No fresh snapshot → the PM **does not approve new buys** and records a visible `Fault` naming the
  staleness. Exits are unaffected — **never block a sell**, for the same reason S147 chose
  fail-visible over fail-closed: a blocked run that cannot sell is an unbounded risk, while a
  blocked *buy* is merely a missed opportunity.
- This asymmetry is deliberate. Do not "simplify" it into blocking the whole run.

**Result:** Done. Missing, stale, or unreadable account facts make the PM reject new buys with
`account_unavailable` and record a visible staleness `Fault`. Sells bypass the account freshness
precheck and remain eligible against held positions.

### 5 · Do not unwind the existing over-commitment

The book is already at ~2× and **this sprint must not sell anything to fix that.**

- Selling to deleverage is a **trading decision** that belongs to DL-93 and the operator, not to a
  defect fix. `ADR-0017` governs exits and is not reversed here.
- The correct behaviour after this fix is simply that the PM **stops adding** — with equity
  $104,042 and $209,009 already deployed, `max_position_pct` should approve **no new buys** until
  the book shrinks. **That is the fix working, not a new bug.** Say so plainly in the closeout.
- Report the expected post-fix state so the operator is not surprised by another zero-approval run.

**Result:** Done. No sell/deleverage behaviour was added, and `max_positions` /
`max_position_pct` were not changed. The S161 2026-08 regression fixture proves equity
104,042.69 against deployed value 209,009.46 approves zero new buys.

### 6 · Declare every new prop in the vocabulary

The write guard is live on the fleet and **fails closed on the first write**.

- Add the new snapshot properties to
  [`orchestration/packs/trading_graph_vocabulary.json`](../../orchestration/packs/trading_graph_vocabulary.json).
- Re-run `scripts/vocabulary_coverage.py` and `scripts/vocabulary_signatures.py`; paste the output.
- ⚠️ **Image and pack move together at deploy** — a target on new code with a stale pack raises
  `VocabularyError` on its first write (the S148 stall, DL-85).

**Result:** Done. The new `BrokerPositionSnapshot` account properties are declared in
`orchestration/packs/trading_graph_vocabulary.json`. `scripts/vocabulary_coverage.py` and
`scripts/vocabulary_signatures.py` both exit 0 with no output.

### 7 · Prove the checks can fail (DL-70)

Every test plants the violation and requires the failure. **Watch each one fail before trusting it**
— an S160 test passed its own planted violation because the fixture was symmetric and proved nothing.

**Result:** Done. Controlled planted failures were observed before the final green run:
removing deployed-value subtraction made B2/B3 fail, and removing `account_equity_cents` from the
pack made the vocabulary guard fail closed. The tests were then restored to green.

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
| Execution run-start snapshot | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/dependencies.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `EXEC-IDN-01`; `EXEC-IDN-03`; `EXEC-TRG-07`; `EXEC-FAIL-02`; `EXEC-DEP-03`; `EXEC-DEP-04`; `EXEC-OBS-02`; `DEP-BROKER-01`; `DEP-BROKER-02` | Yes: `EXEC-IDN-03` already owns `BrokerPositionSnapshot`, so S161 must add properties to that existing execution-owned label, not introduce a new label. The broker CAP does not explicitly name account reads; recorded as `DRIFT-035`. |
| PM portfolio / sizing / risk gates | `agents/portfolio_manager/laws/laws.md`; `agents/portfolio_manager/laws/test-plan.md`; `docs/laws/dependencies.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `PM-IDN-01`; `PM-IDN-02`; `PM-OUT-01`; `PM-OUT-03`; `PM-OUT-06`; `PM-NEV-01`; `PM-NEV-04`; `PM-NEV-05`; `PM-STA-01`; `PM-STA-03`; `PM-FAIL-01`; `PM-FAIL-02`; `PM-OBS-01`; `PM-OBS-02` | Yes: PM must read execution-written graph account facts only; stale account data must block new buys visibly while leaving sells unaffected. The `starting_cash` PARAM rationale is stale for S161's account-backed sizing; recorded as `DRIFT-036`. |
| `trading_graph_vocabulary.json` | `docs/laws/conventions.md`; `docs/laws/drift-register.md` | conventions §3, §7, §9; `EXEC-IDN-03` | No contradiction: declare the added snapshot properties before the first guarded write, and prove the guard rejects an undeclared planted property. |

**Contradictions found between a law and this spec:**

None in clause text. Two locked-law gaps/stale declarations found and recorded below rather than edited in place.

**Laws found silent where a decision was needed** (each needs a `drift-register.md` row):

`DRIFT-035` — execution CAP/DEP text owns the snapshot label but does not explicitly declare broker account reads or account-state fields on that snapshot.
`DRIFT-036` — PM law PARAM text still describes `starting_cash` as the position-limit base, while S161 decides account-backed sizing with `starting_cash` only as a no-snapshot bootstrap seed.

**Clauses that were ⬜ and are now proven by this sprint's tests:**

`EXEC-IDN-03` and `EXEC-TRG-07` are now green and the execution law test-plan plus rollups were
updated. `EXEC-DEP-04` and `PM-OUT-06` remain intentionally gray because S161 adds account-specific
evidence, not full-clause proof for every broker-evidence effect or portfolio-state snapshot output.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_reconcile_run_start_records_account_state_on_snapshot` | `agents/execution/tests/test_account_snapshot.py` | passed | `EXEC-IDN-03`; `EXEC-TRG-07` |
| A2 | `test_reconcile_run_start_account_failure_writes_stale_snapshot` | `agents/execution/tests/test_account_snapshot.py` | passed | `EXEC-OBS-02`; `EXEC-TRG-07` |
| A3 | `test_reconcile_run_start_writes_only_execution_owned_snapshot_label`; `test_broker_evidence_labels_have_execution_only_writers` | `agents/execution/tests/test_account_snapshot.py`; `agents/execution/tests/test_broker_evidence_ownership.py` | passed | `EXEC-IDN-03` |
| B1 | `test_pm_sizes_against_snapshot_equity_not_starting_cash` | `agents/portfolio_manager/tests/test_account_sizing.py` | passed | `PM-IDN-01`; `PM-NEV-04` |
| B2 | `test_2026_08_margin_regression_approves_zero_new_buys` | `agents/portfolio_manager/tests/test_account_sizing.py` | passed | `PM-NEV-04`; `PM-OUT-03` |
| B3 | `test_leverage_is_impossible_across_repeated_runs` | `agents/portfolio_manager/tests/test_account_sizing.py` | passed | `PM-NEV-04`; `PM-STA-01` |
| B4 | `test_sell_is_not_blocked_by_stale_account` | `agents/portfolio_manager/tests/test_account_staleness.py` | passed | `PM-NEV-01`; `PM-NEV-04`; `ADR-0016` |
| B5 | `test_missing_account_figures_block_buys_visibly`; `test_pm_bus_rejects_buy_from_stale_snapshot_but_keeps_fault_visible` | `agents/portfolio_manager/tests/test_account_staleness.py` | passed | `PM-OBS-02`; `PM-NEV-04`; `PM-NEV-01` |
| C1 | `test_starting_cash_is_only_no_snapshot_bootstrap_seed` | `agents/portfolio_manager/tests/test_account_sizing.py` | passed | `PM-STA-01` |
| C2 | `test_broker_position_snapshot_account_props_are_declared_and_guarded` | `tests/test_broker_snapshot_vocabulary.py` | passed | `EXEC-IDN-03`; `DL-70` |

**Tests added beyond the plan:**

- `agents/execution/tests/test_alpaca_account.py::test_alpaca_account_reads_and_parses_account_endpoint`
- `agents/execution/tests/test_alpaca_account.py::test_alpaca_account_rejects_malformed_account_payloads`
- `agents/execution/tests/test_account_snapshot.py::test_account_snapshot_props_without_reason_are_stale_without_detail`
- `agents/execution/tests/test_broker_positions.py::test_paper_broker_account_tracks_cash_equity_and_buying_power`
- `agents/portfolio_manager/tests/test_account_sizing.py::test_position_values_fall_back_to_snapshot_holdings_safely`

---

## Closeout — evidence

**Tree the proofs ran in (and `.env` present?):**

Branch `sprint-161-pm-knows-what-it-paid`, based on `65b78cfc0a6f5f14842eb18f75ddcb139d24d477`.
`.env` present: yes. No secret values were printed or copied.

**Item 3 decision — sizing base chosen, and why:**

Chosen base: Alpaca `equity`. It is the account value that answers "how much portfolio do we
actually have", remains meaningful when cash is negative on margin, and makes `max_position_pct`
refer to a fraction of the real portfolio rather than a fixed nightly seed. S161 additionally
subtracts already deployed market value before approving buys, so repeated runs cannot keep adding
against the same equity.

Rejected: raw `cash` because the live account cash is -104,966.77 and would quietly block every buy;
`buying_power` because it authorises leverage without an operator decision; `starting_cash` because
it is a bootstrap seed, not broker truth; changing `max_positions` or `max_position_pct` because
DL-93 owns that policy decision after the account bug is fixed.

**Files changed:**

Execution account read/snapshot: `agents/execution/alpaca.py`, `agents/execution/alpaca_account.py`,
`agents/execution/broker.py`, `agents/execution/paper_broker.py`,
`agents/execution/paper_broker_math.py`, `agents/execution/reconciliation.py`,
`agents/execution/reconciliation_store.py`, `agents/execution/snapshot_account.py`.

PM sizing/staleness: `agents/portfolio_manager/agent.py`,
`agents/portfolio_manager/domain/gate_report.py`, `agents/portfolio_manager/domain/risk.py`,
`agents/portfolio_manager/graph_portfolio.py`, `agents/portfolio_manager/poll.py`,
`agents/portfolio_manager/portfolio.py`, `agents/portfolio_manager/run.py`,
`agents/portfolio_manager/settings.py`.

Tests, vocabulary, laws, and version: execution/PM account tests, `tests/test_broker_snapshot_vocabulary.py`,
`orchestration/packs/trading_graph_vocabulary.json`, execution law test-plan/rollups,
`docs/laws/drift-register.md`, this sprint file, `pyproject.toml`, and `uv.lock`.

**Proven (LAW-02):**

`uv lock`:

```text
Resolved 174 packages in 1.78s
Updated trading-agents v0.87.1 -> v0.88.0
```

Focused affected tests:

```text
uv run pytest agents\execution\tests\test_position_sync_poll.py agents\execution\tests\test_position_sync_work_items.py agents\execution\tests\test_broker_evidence_ownership.py agents\execution\tests\test_reconciliation.py agents\execution\tests\test_account_snapshot.py agents\execution\tests\test_alpaca_broker.py agents\execution\tests\test_alpaca_account.py agents\execution\tests\test_broker_positions.py agents\portfolio_manager\tests\test_account_sizing.py agents\portfolio_manager\tests\test_account_staleness.py agents\portfolio_manager\tests\test_graph_portfolio.py agents\portfolio_manager\tests\test_portfolio_manager_agent.py agents\portfolio_manager\tests\test_portfolio_manager_audit.py tests\test_broker_snapshot_vocabulary.py tests\test_graph_vocabulary_completeness.py tests\test_graph_vocabulary_properties.py --no-cov
77 passed in 14.39s
```

Scoped static/type checks:

```text
uv run ruff check agents\execution agents\portfolio_manager tests\test_broker_snapshot_vocabulary.py tests\test_graph_vocabulary_completeness.py tests\test_graph_vocabulary_properties.py
All checks passed!

uv run mypy agents\execution agents\portfolio_manager
Success: no issues found in 118 source files

uv run python scripts\check_law_coverage.py
exit 0; warnings only for existing no-row backlog

uv run python scripts\check_module_size.py kernel contracts agents orchestration surfaces tests
exit 0; warnings only, no hard block

uv run python scripts\vocabulary_coverage.py
exit 0; no output

uv run python scripts\vocabulary_signatures.py
exit 0; no output
```

Planted violations watched fail:

```text
# Temporary plant: removed deployed-value subtraction from PortfolioState.available_for_buys.
uv run pytest agents\portfolio_manager\tests\test_account_sizing.py -k "2026_08_margin_regression or leverage_is_impossible" --no-cov
2 failed: B2 approved one AAPL buy; B3 approvals became [1, 1, 1] instead of [1, 1, 0].

# Temporary plant: removed account_equity_cents from trading_graph_vocabulary.json.
uv run pytest tests\test_broker_snapshot_vocabulary.py --no-cov
1 failed: VocabularyError undeclared properties for label 'BrokerPositionSnapshot': ['account_equity_cents'].
```

Final full gate:

```text
make ci *> C:\Users\yury_\AppData\Local\Temp\s161-make-ci.log
make ci exit 0
TOTAL 14138 statements, 0 missed, 2998 branches, 0 partial, 100.00% coverage
2142 passed, 4 skipped in 158.35s
No known vulnerabilities found
Detect secrets...........................................................Passed
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 9 new file(s)
```

Remote gate / gate-ran / merge:

```text
git push -u origin sprint-161-pm-knows-what-it-paid
created origin/sprint-161-pm-knows-what-it-paid at 802b1c6

gh run watch 31085921455 --exit-status
CI success: quality passed in 39s; security passed in 2m13s; test passed in 1m8s.

gh run list --branch sprint-161-pm-knows-what-it-paid --limit 10
completed success Security Findings sprint-161-pm-knows-what-it-paid push 31085919993
completed success CI                sprint-161-pm-knows-what-it-paid push 31085921455

make gate-ran
GATE PROVEN for 802b1c64344e0899fb32aa827da4434ec720a53d:
  CI: success
  Security Findings: success
```

**Expected post-fix approval count, and why that is correct:**

Expected first post-fix scheduled run approval count for new buys: **zero**. With equity 104,042.69
and deployed market value 209,009.46, the account is already over the equity-backed buy budget. The
PM should stop adding until the book shrinks; that is the fix working, not a deleveraging action.

**Not met / verified failing:**

Not done in this branch-local sprint execution: fleet retag/deploy and first scheduled-run
functionality check. Those are post-merge/fleet steps in the sequencing block above. The closeout-doc
commit is pushed after the code gate evidence, and `make gate-ran` is rerun before the local merge.

---

## Return notes

- Sizing base decision: use account `equity`, not Alpaca `cash`, not `buying_power`, and not the
  historical `starting_cash` seed. Raw `cash` would reject all buys on the current margin account;
  `buying_power` would make leverage an implicit default; `starting_cash` is no longer broker truth.
- This sprint intentionally prevents **new** over-commitment only. It does not sell existing holdings
  or make DL-93's resize/deleverage decision.
- Account freshness is asymmetric by design: stale/unreadable account facts block buys and record a
  visible `Fault`; sells remain allowed so exit risk is not trapped behind the account read.
- The vocabulary pack and image must move together when deployed. A stale pack will fail closed on
  the first account-augmented `BrokerPositionSnapshot` write.
- `DRIFT-035` and `DRIFT-036` record locked-law gaps found during law-first reading. No `laws.md`
  file was edited.
