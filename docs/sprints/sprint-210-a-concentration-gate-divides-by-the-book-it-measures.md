<!-- Agent: planning | Role: sprint handover -->
# Sprint 210 — a concentration gate divides by the book it measures

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-210-concentration-divides-by-the-book`
**Status:** SPEC
**Version:** *next available PATCH at merge* — **do not pin a number**, S209 is in flight and will move it
**Effort:** M — the code is small and touches three gates; the **PM law cycle is half the sprint**
**Decisions:** [ADR-0025](../decisions/0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md) · [ADR-0026](../decisions/0026-a-small-book-is-allowed-to-be-concentrated.md) · DL-171 · DRIFT-065 · closes work-queue item **65**

> **Why this bump kind.** PATCH. The gates already claim to bound concentration; they cannot. Nothing
> gains a capability it did not advertise — two gates start doing what their clause already says they
> do. No new agent, endpoint or dimension.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/portfolio_manager/laws/laws.md` | The PM's **locked constitution** (LOCKED **v1.5**, rollup **30 / 49**) | **Read-only during a build** — except the amendment this sprint owes, below |
| `agents/portfolio_manager/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it **before** trusting any clause — one of them is proven more narrowly than it reads |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`PM-NEV`**, **`PM-OBS`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read `agents/portfolio_manager/laws/test-plan.md` alongside its `laws.md`.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It is already answered **Yes**.
5. **Write the Law reading record** **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered **YES**

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**`contracts/` — expected NO.** The gates live in `agents/portfolio_manager/domain/`. **Verify it:
`git diff --stat contracts/` must come back empty.** If you find yourself needing a contracts change,
stop and report — that would make this a different sprint.

**A guarantee changes — YES, twice over.**

**(a) `PM-NEV-09` enumerates its not-evaluated triggers, and this sprint adds one.** Today
(`laws.md:107`) it reads:

> *"When the sector label is missing, or fewer than `min_correlation_bars` overlapping bars exist for
> a pair, the gate emits an explicit **not-evaluated** outcome naming the missing input."*

ADR-0026 adds a third trigger — **deployment below the derived floor**. A closed enumeration that
silently grows is drift, so the clause must be amended to carry it.

**(b) The denominator itself is a guarantee.** `PM-NEV-06` and `PM-NEV-08` describe what these gates
bound. "Bounded relative to the deployed book, not to total equity" is a statement about what the PM
promises, and it is not currently written anywhere in the law book.

**Therefore this sprint owes, in the same unit of work:** the `PM-NEV-09` amendment, a clause (new or
amended) stating the denominator, `laws.md` **v1.5 → v1.6** with a Changelog line, `test-plan.md` rows
for every clause touched, the clause ID cited in each new test docstring, the rollup recomputed in
**both** [`docs/laws/ledger.md`](../laws/ledger.md) (line 42) **and**
[`docs/laws/INDEX.md`](../laws/INDEX.md) (line 43), and **DRIFT-065** (see below).

🪤 **The rollup is derived, not declared.** `make ci` recomputes it. Let the gate tell you the number;
do not hand-edit it to match a number this spec guessed.

### 🪰 A drift row you are being asked to file, not to fix

`PM-OBS-04` (`laws.md:228`, added and proven by S208) opens:

> *"**Every** evaluated PM gate that renders a `PASSED` or `FAILED` verdict discloses whether the
> opposite verdict was reachable from the evidence it had."*

Its **test-plan row (`test-plan.md:113`) proves something narrower** — the structurally-fixed
stop/target case and the correlation-skip case. Measured 2026-09-16: `max_sector_pct` and
`correlated_cluster_pct` have rendered `PASSED` **93 times between them with `FAILED` unreachable**,
and disclose nothing about it.

**File this as `DRIFT-065`: the clause is general, its proof is narrow, and two gates sit in the gap.**
🪤 **Write it as a question, not an accusation** — a per-candidate reading of "reachable from the
evidence it had" can be defended, and this project has already paid for one confident false defect
([DL-73](../design-log.md)). State what was measured and let the next law cycle rule. **Do not
rewrite `PM-OBS-04` in this sprint.**

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `domain/sector_gate_outcomes.py` (`sector_exposure_outcome`, **:44–70**) | `agents/portfolio_manager/laws/laws.md` + `test-plan.md` | `PM-NEV-06` (label-bucket cap), `PM-NEV-09` (not-evaluated), `PM-OBS-04` |
| `domain/correlation.py` (**:58–95**) | same | `PM-NEV-08` (correlated-cluster weight), `PM-NEV-09` |
| `domain/position_gates.py` (sizing + disclosure, **:160–161**) | same | ⚠️ `sizing` **must not change** — see the invariant |
| `portfolio.py` (**:32–40**) | same | `value` / `deployed_value` are the two denominators |
| `agents/portfolio_manager/laws/laws.md` | itself, whole file | LOCKED v1.5 → the amendment above is the *only* permitted edit |

⚠️ **The one invariant this sprint must not break: `sizing` keeps the EQUITY denominator.**
ADR-0025 ruled this deliberately. If `sizing` moves to deployed capital, **every order fails**:
measured on `sched-2026-09-15`, AMZN's `sizing` value `0.009723` against a `0.01` cap becomes
`0.0458` at the 4.707× ratio. If your change touches `sizing`'s denominator, stop and report.

---

## Goal

`max_sector_pct` and `correlated_cluster_pct` divide by **deployed capital** — the book they are
measuring — instead of total equity. Below a floor derived from existing tunables they report
whole-gate `NOT_EVALUATED`, naming the floor and the actual deployment, and never `FAILED`. `sizing`
is unchanged. On today's book both gates are live, and every verdict on `sched-2026-09-15` is
unchanged.

## Why (context)

Two of the PM's eight gates have ever rejected anything. An equity-denominated cap is inert whenever
the cap exceeds the deployment ratio, and the book is 21.24 % deployed — so **the entire book
collapsed into one cluster reads 0.2124 and passes both a 0.30 and a 0.25 cap.** The full reasoning,
the alternatives rejected, and the bootstrap risk acceptance are in
[ADR-0025](../decisions/0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md)
and [ADR-0026](../decisions/0026-a-small-book-is-allowed-to-be-concentrated.md). **Read both before
designing; this spec does not restate their arguments.**

### Measured, 2026-09-16 — read these before designing

Live Neon spine + Alpaca paper account, from a checkout on `main`. **You do not need to reproduce
these; a worktree has no `.env`.**

| Claim | Value | How it was measured |
| --- | --- | --- |
| PM gates that have **ever** rejected | **2 of 8** — `sizing` (20), `max_names_per_sector` (17) | *[measured]* every `gate_report` in every `PMRun` |
| `correlated_cluster_pct` | **38 recordings, 38 passed, 0 rejected** | *[measured]* max value **0.0199** vs threshold 0.25 = **8 % of its own threshold** |
| `max_sector_pct` | **55 evaluated, 0 rejected** | *[measured]* max ever **0.2992**, recorded when the book was **2.02× deployed** (2026-08-07), not today |
| Book today | **$21,711.95 deployed / $102,208.78 equity = 21.24 %** | *[measured]* Alpaca positions + account; graph and broker agree on 23 positions |
| Whole book as one cluster | **0.2124 → PASSES both caps** | *[measured]* arithmetic on the two numbers above |
| Ratio equity ÷ deployed | **4.707×** | *[measured]* |
| Runs with a book **< 4 positions** | **8 of 58 = 14 %**; smallest ever **1** | *[measured]* `max_positions` gate `held_issuers` across all runs that recorded one |
| Derived floors | **10 %** of equity (sector), **12 %** (correlation) | *[derived]* `names_cap × max_position_pct ÷ pct_cap` = `3 × 0.01 ÷ 0.30` and `÷ 0.25` |
| Migration effect on `sched-2026-09-15` | **every verdict unchanged** | *[measured]* Banking `0.0383 → 0.1803`, Media `0.0274 → 0.1289`, Food `0.0196 → 0.0922`, WFC cluster `0.0097 → 0.0455`, MDLZ cluster `0.0097 → 0.0458` — all under cap |
| PM laws | LOCKED **v1.5**, rollup **30 / 49** | *[measured]* `laws.md:3`, `ledger.md:42` |
| Module sizes | `position_gates.py` **175** 🚨, `correlation.py` **131**, `sector_gate_outcomes.py` **128**, `settings.py` **133**, `portfolio.py` **63** | *[measured]* `wc -l`; warn 150, **hard block 200** |

---

## Scope — and what is deliberately NOT here

1. **🎯 Plant the failing tests first.** Two reds before any implementation: (a) the sector gate on a
   fixture reproducing `sched-2026-09-15`'s Banking book asserts **0.1803**, not `0.0383`; (b) a flat
   or near-flat book asserts **`NOT_EVALUATED`**, not `FAILED`. Watch both fail. Paste the output.
2. **Swap the denominator** in `sector_exposure_outcome` (`sector_gate_outcomes.py:44–70`) and in the
   correlation cluster gate (`correlation.py:58–95`) from `portfolio.value` to
   `portfolio.deployed_value`. **Both the reported `value` and the `PASSED`/`FAILED` comparison** —
   they are computed separately today, which is the next item.
3. **Fix the value/verdict contradiction.** The verdict uses a raw comparison
   (`total <= max_sector_pct * portfolio_value`) while the reported value uses a zero-safe helper
   returning `0.0` for a non-positive denominator (`sector_gate_outcomes.py:126–128`,
   `correlation.py:130–131`, `position_gates.py:160–161`). At `deployed = 0` the evidence reads
   **`value=0.0000` with `outcome=FAILED`**. After this sprint that state is unreachable — but make
   the two agree at the source, do not rely on the floor to hide it.
4. **The derived floor.** Below `names_cap × max_position_pct ÷ pct_cap` of equity, whole-gate
   `NOT_EVALUATED`. **Computed at evaluation time from the live tunables — not stored, not a new
   `tunable()`.** The `detail` names the floor, the actual deployment, and that the floor was the
   reason.
5. **Disclose the denominator** in both gates' `detail`, so a `0.18` that means "18 % of the book" is
   never mistakable for a `0.18` that means "18 % of equity". Same discipline as S208.
6. **The law cycle**, in full, as itemised above, plus **DRIFT-065**.

### Out of scope (do NOT build this sprint)

- **`sizing` — do not touch its denominator.** See the invariant. A naming fix to `portfolio.value`
  is welcome (below); a semantic change is not.
- **No new `tunable()`.** The floor is derived. Registering it as a tunable makes it a number someone
  can set inconsistently with the caps it is derived from, which is the whole point of deriving it.
- **No `PM-OBS-04` rewrite.** File `DRIFT-065` and stop.
- **No volatility-scaled sizing.** ADR-0025 Decision B ruled the *direction* and explicitly withheld
  implementation pending a champion–challenger measurement. Items 62 and 64 are not this sprint.
- **No threshold changes.** 0.30 and 0.25 stay. ADR-0025 fixed them deliberately so the migration
  rejects nothing retroactively.
- **No ADR reversal.** An ADR is reversed by a new ADR, never by a sprint.

### 🪤 The naming fix that is in scope

`portfolio.value` (`portfolio.py:32`) is documented *"the equity-backed portfolio value used for
sizing"* and returns `self.cash.amount`. It is correct only because equity is loaded into the `cash`
field. **Rename so the code says what it means** — the next reader will otherwise reasonably conclude
`sizing` divides by cash, and with two denominators now in play that misreading becomes expensive.
**Behaviour must not change; prove it with an unchanged `sizing` test.**

### The road not taken (LAW-06)

Both ADRs carry the full rejected-options record — **read them rather than re-deriving**. The ones
most likely to tempt you mid-build:

- **Floor the denominator (`max(deployed, X)`) instead of `NOT_EVALUATED`.** Rejected: it reports a
  number that is not true. A one-position book would read 20 % concentrated when it is 100 %
  concentrated.
- **Use a post-trade denominator (`deployed + this order`).** Rejected: the first order into a flat
  book is still 100 % of the post-trade book. It changes the arithmetic, not the conclusion.
- **Suppress by position count rather than deployment share.** Rejected: positions are not
  equal-sized (today `$156`–`$1,122`).

---

## The design decisions this sprint has to make

**Record in `docs/design-log.md` with rejected alternatives BEFORE implementing (LAW-06).**

1. **Where the floor is computed** — inside each gate, or once and passed in. Both gates need it with
   *different* caps (0.30 and 0.25), so a single shared constant is wrong; a single shared *helper*
   taking the cap is right.
2. **What `NOT_EVALUATED` carries in `detail`** so a reader can tell "suppressed by the floor" from
   "suppressed by a missing sector label" — `PM-NEV-09` requires the missing input be named, and
   there are now three different reasons.

🪤 **`DL-170` and `DRIFT-064` are S209's — take `DL-171` and `DRIFT-065`.** S209 is in flight in a
different tree as this spec is written. **Re-check both at merge**: the design log has historic
duplicates and is appended at the top *and* the bottom, and S209 will land between now and your merge.

---

## Blast radius — measured 2026-09-16

| What | Detail |
| --- | --- |
| Files changed | `domain/sector_gate_outcomes.py` (**128**), `domain/correlation.py` (**131**), `domain/position_gates.py` (**175** 🚨), `portfolio.py` (**63**), PM `laws.md` + `test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md`, `docs/design-log.md`, `docs/work-queue.md`, `pyproject.toml` |
| Agents affected | `portfolio_manager` only — confirm no agent imports another |
| Contract change? | **Expected none. Verify `git diff --stat contracts/` is empty** |
| Graph vocabulary change? | **No** new label or property — gate `detail` strings change, which is data, not vocabulary |
| New env keys / tunables | **None** — the floor is derived |
| Deploy implication | **Image-only retag** |

🚨 **`position_gates.py` is 175 lines against a 200 hard block — 25 lines of headroom.** If the
denominator disclosure needs more than that, **split the module**; do not grow it and do not `# noqa`.

---

## Steps, in order

1. **Read the laws** (MUST RULE) and write the Law reading record.
2. **Read both ADRs.** This spec deliberately does not restate their reasoning.
3. **Record the design decisions** in `docs/design-log.md`.
4. **Plant the failing tests first** and watch them fail. Paste the red output.
5. **Implement.**
6. **Law cycle** — `PM-NEV-09` amendment, denominator clause, v1.6 + Changelog, test-plan rows,
   docstring citations, both rollups, `DRIFT-065`.
7. **Prove the guards can fail (DL-70)** — break each guard, watch it go red, restore.
8. **`make ci` green** — all 12 steps, **redirected to a file, never piped**.
9. **Fill the handback sections.**

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 the sector gate divides by the book | `sched-2026-09-15` Banking: held `$1,915.80`, batch `$0`, order `$986.86`, deployed `$21,711.95`, equity `$102,208.78` | `value == 0.1803` (not `0.0383`), `outcome == PASSED` against 0.30 |
| A2 | 🎯 the cluster gate divides by the book | WFC cluster `$986.86`, same portfolio | `value == 0.0455` (not `0.0097`), `PASSED` against 0.25 |
| A3 | 🎯 below the floor the gate is NOT_EVALUATED, never FAILED | flat book (`deployed = 0`) and a 1-position book | `outcome == NOT_EVALUATED`; **assert it is not `FAILED`** explicitly; `detail` names the floor **and** the actual deployment |
| A4 | 🪤 above the floor the gate evaluates normally | today's 23-position book, 21.24 % deployed | both gates evaluated — **the floor must not suppress the current book** |
| A5 | 🪤 `sizing` still divides by equity | the AMZN `sched-2026-09-15` intent | `value == 0.009723…` against 0.01, `PASSED` — **unchanged**. This is the invariant |
| A6 | 🪤 the floor is derived, not constant | set `max_names_per_sector` 3 → 4, and `max_sector_pct` 0.30 → 0.20 | the floor moves to `4 × 0.01 ÷ 0.30` and `3 × 0.01 ÷ 0.20` — a hard-coded 0.10 fails this |
| A7 | 🪤 value and verdict never contradict | `deployed = 0` at the helper level, bypassing the floor | there is no state where `value == 0.0` and `outcome == FAILED` |
| A8 | 🪤 a NOT_EVALUATED gate is not a passing gate | a below-floor gate report | it is not counted as passed anywhere it is consumed (`PM-NEV-09`) |
| A9 | every verdict on `sched-2026-09-15` is unchanged | all five recorded subjects in the Measured table | approvals and rejections identical before and after — **the no-shock claim, asserted not assumed** |

🪤 **A5 and A9 are the tests that catch the two ways this sprint can do real damage** — moving
`sizing`, and silently changing what last night's run would have done. Neither is optional.

---

## Success factors

- [ ] Both concentration gates divide by `deployed_value`, in **both** the reported value and the verdict.
- [ ] `sizing` is unchanged and A5 proves it.
- [ ] Below the derived floor both gates report `NOT_EVALUATED`; **no path produces `FAILED` by floor**.
- [ ] The floor is computed from live tunables at evaluation time — **no new `tunable()`, no constant**.
- [ ] Gate `detail` names the denominator; a `NOT_EVALUATED` detail names the floor and the deployment.
- [ ] No state exists where `value == 0.0` and `outcome == FAILED`.
- [ ] A9 proves every `sched-2026-09-15` verdict unchanged.
- [ ] `git diff --stat contracts/` empty.
- [ ] `PM-NEV-09` amended; denominator stated in law; `laws.md` **v1.5 → v1.6** + Changelog.
- [ ] `test-plan.md` rows added/updated; clause IDs in every new test docstring.
- [ ] Rollup recomputed **by the gate** in `ledger.md` **and** `INDEX.md` — report the number it gives.
- [ ] `DRIFT-065` filed, written as a question, `PM-OBS-04` **not** rewritten.
- [ ] Every new guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module **< 200** lines; report `position_gates.py`'s new count.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **Moving `sizing` to deployed capital fails every order.** Measured: AMZN `0.009723 → 0.0458`
against a `0.01` cap. ADR-0025 kept `sizing` on equity deliberately, because a deployed denominator
is circular for a per-position cap — the first position of a run would be 100 % of deployed.

🪤 **`portfolio.value` returns `self.cash.amount`.** It is equity only because equity is loaded into
that field. Read it before you trust either denominator.

🪤 **The verdict and the value are computed by different code paths.** Changing only the `ratio(...)`
call leaves the `PASSED`/`FAILED` comparison on the old denominator, and every test that asserts on
`value` alone will pass while the gate still cannot reject. **Assert on `outcome`, not just `value`.**

🪤 **`max_sector_pct`'s historic max of 0.2992 was recorded at 2.02× deployment**, not today's 0.21×.
Do not read it as evidence the gate nearly binds now.

🪤 **`DL-170` / `DRIFT-064` belong to S209.** Take 171 / 065 and re-check at merge.

🪤 **A gate that returns `NOT_EVALUATED` is doing less than it did.** Below the floor, sector and
cluster value share are genuinely unenforced — `max_names_per_sector` and `sizing` are the only
controls. Anything downstream that treats a non-`FAILED` gate as evidence of bounded concentration is
now wrong, and A8 exists to catch it.

🪤 **`make ci | tail` reports `tail`'s exit code.** Redirect to a file and read the file.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current: `position_gates.py` **175** 🚨, `settings.py` **133**, `correlation.py` **131**,
  `sector_gate_outcomes.py` **128**, `portfolio.py` **63**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — and **the floor is derived, not a magic number and not a `tunable()`**.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**, redirected to a file.
- Version bump **PATCH**, `uv.lock` staged with it. **Do not pin the digits** — S209 moves them.
- Secrets never through the worktree — a worktree has **no `.env`**. 🟩 **Every test here is
  in-memory**; the live numbers are quoted above so you need none. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** — it resolves the SHA
   from the working directory and ignores a `SHA=` argument. **Check the printed SHA against
   `git rev-parse HEAD`.**
2. Merge to `main` locally and push. 🪤 A `git merge` from the branch's own worktree says *"Already up
   to date"* and merges nothing.
3. **Post-merge CodeQL** — `codeql.yml` runs only on `main`.
4. **Deploy:** image-only retag.
5. **The live check.** After the next scheduled run, read one `max_sector_pct` detail and one
   `correlated_cluster_pct` detail from the new `PMRun` and confirm the deployed denominator and the
   disclosed floor, then record it in [`docs/laws/functionality-checks.md`](../laws/functionality-checks.md).
   🪤 **A run in which both gates pass proves only that they were evaluated** — the numbers must be
   the ~4.7× larger ones. Quote them.

---

## Handover — paste this to Codex

```text
Branch `sprint-210-concentration-divides-by-the-book` off main. Never commit to main.

THE CLAIM: a concentration gate divides by the book it is measuring.

READ FIRST, BEFORE ANY CODE:
  - docs/decisions/0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md
  - docs/decisions/0026-a-small-book-is-allowed-to-be-concentrated.md
  - agents/portfolio_manager/laws/laws.md  (WHOLE FILE, it is LOCKED v1.5)
  - agents/portfolio_manager/laws/test-plan.md, docs/laws/conventions.md, docs/laws/drift-register.md
Then fill the "Law reading record" in
docs/sprints/sprint-210-a-concentration-gate-divides-by-the-book-it-measures.md BEFORE your first
code change. If a law contradicts this spec, STOP and report - the law is more likely right.

THE DEFECT. Measured on the live spine 2026-09-16: only 2 of the PM's 8 gates have ever rejected
anything. An equity-denominated cap is inert whenever the cap exceeds the deployment ratio. The
book is 21.24% deployed ($21,711.95 / $102,208.78), so the WHOLE BOOK as a single cluster reads
0.2124 and passes both a 0.30 sector cap and a 0.25 cluster cap. correlated_cluster_pct: 38
recordings, 38 passed, max value 0.0199 = 8% of its own threshold. max_sector_pct: 55 evaluated,
0 rejected.

THE FIX:
1. sector_exposure_outcome (agents/portfolio_manager/domain/sector_gate_outcomes.py:44-70) and the
   cluster gate (agents/portfolio_manager/domain/correlation.py:58-95) divide by
   portfolio.deployed_value (portfolio.py:37) instead of portfolio.value (portfolio.py:32).
   CHANGE BOTH the reported `value` AND the PASSED/FAILED comparison - they are separate code
   paths today. Thresholds stay 0.30 and 0.25.
2. Below a DERIVED floor, both gates report whole-gate NOT_EVALUATED, never FAILED:
       floor = max_names_per_sector * max_position_pct / <that gate's cap>
       sector:      3 * 0.01 / 0.30 = 10% of equity
       correlation: 3 * 0.01 / 0.25 = 12% of equity
   Computed at evaluation time from live tunables. NOT a new tunable(). NOT a constant.
   Reason: from flat the allowance is 0.30 x 0 = 0, so every order fails forever - a permanent
   deadlock. Measured: 14% of all runs had a book under 4 positions; smallest ever was 1; the book
   was deliberately flattened on 2026-08-07. ADR-0026 accepts that a small book may be
   concentrated, with max_names_per_sector (a count, no denominator, 17 real rejections) carrying
   concentration control below the floor.
3. detail names the denominator used; a NOT_EVALUATED detail names the floor AND actual deployment.
4. Fix the value/verdict contradiction: verdict uses a raw comparison, value uses a zero-safe helper
   returning 0.0 for a non-positive denominator (sector_gate_outcomes.py:126-128,
   correlation.py:130-131, position_gates.py:160-161). At deployed=0 that reads value=0.0000 with
   outcome=FAILED. Make them agree at the source; do not rely on the floor to hide it.
5. Rename portfolio.value - it is documented "equity-backed" but returns self.cash.amount. Naming
   only. Behaviour must not change.

DO NOT:
  - DO NOT touch sizing's denominator. It stays on EQUITY - ADR-0025 ruled that deliberately.
    Measured: on deployed capital, AMZN's sizing value 0.009723 becomes 0.0458 against a 0.01 cap
    and EVERY ORDER FAILS. This is the invariant. If you touch it, stop and report.
  - DO NOT change the 0.30 / 0.25 thresholds.
  - DO NOT rewrite PM-OBS-04. File DRIFT-065 about it (below) and stop.
  - DO NOT edit contracts/. `git diff --stat contracts/` must be empty.
  - DO NOT register the floor as a tunable().

ORDER OF WORK - failing tests FIRST. Two reds, pasted, before implementing:
  (a) sector gate on the sched-2026-09-15 Banking fixture (held $1,915.80, batch $0, order $986.86,
      deployed $21,711.95, equity $102,208.78) asserts value == 0.1803, not 0.0383.
  (b) a flat book asserts NOT_EVALUATED, not FAILED.

THE LAW CYCLE IS OWED AND IS HALF THIS SPRINT:
  - PM-NEV-09 (laws.md:107) ENUMERATES its not-evaluated triggers: "the sector label is missing, or
    fewer than min_correlation_bars overlapping bars exist". You are adding a THIRD trigger
    (deployment below the floor). A closed enumeration that silently grows is drift - amend it.
  - State the denominator in law. PM-NEV-06 and PM-NEV-08 describe these gates; "bounded relative to
    the deployed book, not total equity" is a guarantee not currently written anywhere.
  - laws.md v1.5 -> v1.6 with a Changelog line; test-plan.md rows for every clause touched; clause
    IDs cited in each new test docstring.
  - Let `make ci` recompute the rollup in BOTH docs/laws/ledger.md (line 42) and docs/laws/INDEX.md
    (line 43). Current is 30 / 49. Report what the gate gives; do not hand-edit it.
  - FILE DRIFT-065: PM-OBS-04 (laws.md:228) says "EVERY evaluated PM gate that renders PASSED or
    FAILED discloses whether the opposite verdict was reachable", but its test-plan row
    (test-plan.md:113) proves only the stop/target and correlation-skip cases. max_sector_pct and
    correlated_cluster_pct have rendered PASSED 93 times between them with FAILED unreachable and
    disclose nothing. WRITE IT AS A QUESTION, NOT AN ACCUSATION - a per-candidate reading of
    "reachable from the evidence it had" is defensible, and this project has already paid for one
    confident false defect (DL-73).

TRAPS, named because a trap you do not write down gets hit:
  - The verdict and the value are computed by DIFFERENT code paths. Change only the ratio() call and
    every test asserting on `value` passes while the gate still cannot reject. ASSERT ON OUTCOME.
  - portfolio.value returns self.cash.amount and is equity only because equity is loaded into that
    field. Read it before trusting either denominator.
  - max_sector_pct's historic max 0.2992 was recorded at 2.02x deployment (2026-08-07), not today's
    0.21x. It is not evidence the gate nearly binds now.
  - DL-170 and DRIFT-064 belong to sprint 209, which is in flight. Take DL-171 and DRIFT-065, and
    RE-CHECK BOTH AT MERGE - S209 will land in between.
  - position_gates.py is 175 lines against a 200 hard block. Split rather than grow. No # noqa.
  - make ci | tail reports tail's exit code. Redirect to a FILE and read the file.

ALSO PROVE: (A5) sizing is unchanged - AMZN still 0.009723 against 0.01, PASSED. (A9) every verdict
on sched-2026-09-15 is unchanged after the swap: Banking 0.0383->0.1803, Media 0.0274->0.1289, Food
0.0196->0.0922, WFC cluster 0.0097->0.0455, MDLZ cluster 0.0097->0.0458, all still under cap.
(A6) the floor is derived - change max_names_per_sector to 4 and max_sector_pct to 0.20 and the
floor must move; a hard-coded 0.10 fails this.

Everything here is in-memory; a worktree has no .env and you do not need one.
Version: next available PATCH. DO NOT PIN THE DIGITS - sprint 209 is in flight and will move them.
Stage uv.lock with the bump.
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
| | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?**

**Contradictions found between a law and this spec:**

**Laws found silent where a decision was needed:**

**Clauses that were ⬜ and are now proven:**

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
| A7 | | | | |
| A8 | | | | |
| A9 | | | | |

**Tests added beyond the plan:**

---

## Closeout — evidence

**Status:**

**Tree the proofs ran in (and `.env` present?):**

**Result:**

**Files changed:**

**Design decisions:** recorded as `DL-NNN`

**Proof — the red runs first:**

```text
```

**Proof — the green run:**

```text
```

**Guards planted:**

**Module line counts:**

**`make ci`:** redirected to `<path>`. Exit code `<n>`.

**`make gate-ran`:** run from `<worktree path>` at `<full 40-char SHA>`:

```text
```

**Not met / verified failing:**

---

## Return notes

-
