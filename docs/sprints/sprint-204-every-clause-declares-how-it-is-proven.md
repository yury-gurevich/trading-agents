<!-- Agent: planning | Role: sprint handover — every law clause has a row, and the row says how it is proven -->
# Sprint 204 — every law clause declares how it is proven, or that it cannot be

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-204-every-clause-declares-how-it-is-proven` *(create before any code)*
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** L
**Decisions:** work-queue **items 10 and 30** (both) · hardening row **O** · [DRIFT-058](../laws/drift-register.md) (the lesson this applies) · [DL-121](../design-log.md) (item 30's measurement) · conventions **§7a** trade, knowingly re-taken

> **Why this bump kind.** PATCH. No new capability and no agent behaviour changes. The deliverable is
> that a **warn-only gate becomes enforcing** and the law book stops having silent holes. Tooling and
> documentation of what is already true.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/*/laws/laws.md` (all 15) | **LOCKED** constitutions | **Read-only.** This sprint edits **test-plans**, not laws — with the one exception in Scope 4, which is a *clause rewrite* and needs the full cycle |
| `agents/*/laws/test-plan.md` | proven 🟩 / unproven ⬜ per clause | **This is what the sprint writes** |
| `docs/laws/conventions.md` | §7a (rewrite trade), §9 (drift) | Read both — §7a is the accepted cost of Scope 4 |
| `docs/laws/ledger.md` + `docs/laws/INDEX.md` | the two rollups | **Both** must be reconciled; they drift apart otherwise |
| `docs/laws/drift-register.md` | the appendable file | Rows owed where a clause turns out to be unprovable *and* wrong |

**Law-cycle question — does this sprint change `contracts/`, or add a guarantee an agent did not
previously make?** **No for Scopes 1–3** — writing a test-plan row records how an *existing* clause is
proven; it adds no guarantee. **Yes for Scope 4**, which rewrites unfalsifiable clauses and therefore
owes the full cycle for each: clause text, test-plan row, clause ID in the test docstring, rollups in
**both** `ledger.md` and `INDEX.md`, and a drift row. Do Scopes 1–3 first and land Scope 4 separately
if the sprint gets long — **say so rather than rushing the law cycle**.

⚠️ **The invariant this must not break: no clause may become 🟩 in this sprint.** This sprint's job is
to make the book *honest*, not to make it *greener*. A row that says ⬜ is a success here. If you find
yourself writing a test to turn something green, you have left the scope.

---

## Goal

Every law clause in every agent has a test-plan row; each row declares **how** the clause is proven —
by a test, by a CI gate, or not at all — and `check_law_coverage.py` assertion E is promoted from
warn-only to enforcing.

## Why (context)

Work-queue **item 10** (hardening row O) and **item 30**, which are the same defect at two depths.

🚨 **Item 10 is about rows, not tests, and that is what makes it tractable.** Its own text: *"101 law
clauses with no test-plan row; assertion E in `check_law_coverage.py` is warn-only and **cannot be
promoted until the rows exist**."* Writing 101 honest rows — most of them ⬜ — is mechanical. Writing
101 tests is not, and is not asked for.

### Measured, 2026-09-14 (re-measured; both rows were `[carried]`)

`PYTHONPATH=. uv run python scripts/check_law_coverage.py` → **101** clauses with no row, confirming
the carried number, spread over **8** agents:

| Agent | Missing rows |
| --- | --- |
| provider | 22 |
| master | 21 |
| execution | 13 |
| scanner | 13 |
| analyst | 12 |
| portfolio_manager | 12 |
| monitor | 7 |
| reporter | 1 |

🎯 **They are not 101 distinct problems — they cluster into a few families**, each missing across most
agents:

| Family | Missing | Missing in N agents | Cumulative |
| --- | --- | --- | --- |
| DEP | 18 | 6 | 17.8 % |
| SEC | 15 | 7 | 32.7 % |
| ORD | 12 | 7 | 44.6 % |
| IDN | 11 | 5 | 55.4 % |
| PERF | 7 | 7 | **62.4 %** |
| FAIL / NEV / IN / STA / OBS | 28 | 3–5 each | 90.1 % |
| TRG / TYP / OUT / IDM | 10 | 1–3 each | 100 % |

**Five families are 62 % of the backlog.** So the work is *decide once per family what proving it
means*, then apply — not 101 independent judgements.

### What the families turn out to be — sampled, and it changes the answer

| Clause | Text (abridged) | What proves it |
| --- | --- | --- |
| `MST-DEP-03` | *"No dependency on any trading agent's code"* | 🧱 **import-linter already enforces this** — contract *"Agents may not import one another"* |
| `MST-ORD-01` | *"`start()` must be called before `activate()`"* | ✅ an ordinary test; nobody wrote one |
| `MST-PERF-01` | *"`activate()` writes 1 `AgentInstance` + N `CapabilityGrant`"* | ✅ a counting assertion — **not a performance claim despite the family name** |
| `MST-SEC-02` | *"Each agent receives only the config for its declared grants"* | ✅ testable; likely already covered by an uncited test |
| `SCAN-IDN-01` | *"The scanner's sole job is universe → ranked candidates"* | 📜 **a charter statement — not falsifiable** |
| `PM-IDN-01` | *"The portfolio manager's sole job is recommendation → sized order intent"* | 📜 same |

🪤 **Do not turn the family into the rule.** `MST-IDN-01` *does* have a row and *is* testable
(*"`start()` writes Session node"*). Families **cluster**; classification is **per clause**. I made
exactly this overgeneralisation while scoping and it was wrong within one sample.

🚨 **And the deepest case is item 30:** 15 clauses assert *"X matches `contracts/<agent>.py` exactly"*,
so the file is **both the claim and the oracle** — a contract can change with every test still green.
[DL-121](../design-log.md) measured this and it is **not theoretical**: the scanner's `FilterVerdict`
collapsed *"did not run"* and *"passed"* into the same bytes, which **is the S183 bug**, and no law
book prevented it.

**This is [DRIFT-058](../laws/drift-register.md) again** — *a green row whose oracle cannot fail
proves only that the oracle ran* — in the law book itself rather than in a credential probe.

---

## Scope

### 1. A proof-kind vocabulary for test-plan rows

Extend the Status column beyond 🟩/⬜ with two kinds that are **honest answers, not excuses**:

| Mark | Meaning | Test column must contain |
| --- | --- | --- |
| 🟩 | proven by a functional test | the test name; the test docstring cites the clause ID |
| ⬜ | owed a test | what is missing, if known |
| 🧱 | **structural** — proven by a named CI gate, not a unit test | the gate + the contract/rule name, e.g. `import-linter: "Agents may not import one another"` |
| 📜 | **charter** — a purpose/identity statement, not falsifiable by design | *why* it is not falsifiable |

Document it in `docs/laws/conventions.md` as the authority; the per-agent test-plans follow.

🪤 **📜 is the dangerous one.** It must never become a dumping ground for "hard to test". The test is:
*could any observation contradict this clause?* If yes, it is ⬜, not 📜. Expect to justify every 📜 in
the closeout, and expect me to push back on them individually.

### 2. Write the 101 missing rows

One row per clause, with the honest kind. Most will be ⬜ and that is the correct outcome. Work by
**family across agents**, not agent by agent — the decision is per family and the application is
mechanical, and doing it agent-first re-litigates the same question eight times.

### 3. Promote assertion E to enforcing

Once every clause has a row, flip assertion E in `scripts/check_law_coverage.py` (**225** lines) from
`[WARN]` to a gate failure, so a new clause without a row **fails CI**. This is the whole point of the
sprint — the ratchet that stops the backlog regrowing.

🪤 **Watch it fail first** (DL-70): add a clause with no row, see CI go red, remove it.

### 4. Item 30's 15 unfalsifiable clauses *(land separately if the sprint gets long)*

Rewrite each *"matches `contracts/<agent>.py` exactly"* clause to **enumerate the required fields**,
so the clause stops being its own oracle. `PM-TYP-03` is already rewritten (PM laws v1.3) — **follow
that precedent exactly** rather than inventing a second shape.

⚠️ **This demotes greens, knowingly** — conventions §7a, the trade already accepted. Each rewrite is a
full law cycle per the law-cycle answer above.

### Out of scope

- **Writing tests to turn ⬜ into 🟩.** Explicitly not this sprint. The backlog of *tests* is what the
  honest rows will finally make visible and rankable.
- **Editing any `laws.md` outside Scope 4.**
- **Item 33** (57 PARAM/settings divergences). Same *shape* — a claim whose check is warn-only — but a
  different surface (laws↔settings) and a different decision (putting secret names into PARAM tables
  as `NO (secret)`). Ranked separately on purpose.

### The road not taken

- **One sprint for items 10, 30 and 33.** I measured the hypothesis that they are one problem: they are
  the same *shape* but three different *couplings* — laws↔test-plan, laws↔contracts, laws↔settings —
  with three different decisions. Rejected; 33 stays its own row.
- **Writing the 101 tests.** Rejected: that is a multi-sprint programme, and item 10 does not ask for
  it. Rows first makes the test backlog legible and rankable for the first time.
- **Leaving assertion E warn-only and just adding rows.** Rejected — without the promotion the backlog
  regrows silently, which is the ratchet failure item 33 already demonstrates with its 57 `[WARN]`s.

---

## Blast radius

| What | Detail |
| --- | --- |
| Files changed | 8 × `agents/*/laws/test-plan.md`, `docs/laws/conventions.md`, `scripts/check_law_coverage.py` **225**, `docs/laws/ledger.md`, `docs/laws/INDEX.md`; Scope 4 also touches ≤15 `laws.md` |
| Contract change? | No |
| Graph vocabulary change? | No |
| Deploy implication | **None.** Nothing ships in an agent image |
| Agent behaviour change | **None** — this is the point; if behaviour changes, scope has leaked |

🚨 **The rollups will get *worse*, and that is the correct result.** Adding ⬜ rows for
previously-rowless clauses changes the proven/total ratios in `ledger.md` and `INDEX.md`. **Measure
the before and after and state both** — a ratio that drops because the denominator became honest is a
success, and must not be presented as a regression or quietly smoothed. 🪤 **Derive the new numbers
with the coverage checker, never by arithmetic** — it has rejected my hand-counted rollups twice
(S199 17/54, S172 15/52).

---

## Success factors

- [ ] `check_law_coverage.py` reports **0** clauses without a test-plan row.
- [ ] Assertion E is **enforcing**, and was watched failing on a planted rowless clause.
- [ ] The 🧱/📜 vocabulary is documented in `conventions.md` and used consistently.
- [ ] Every 🧱 row names the gate **and** the specific contract/rule that proves it.
- [ ] Every 📜 row states why no observation could contradict the clause.
- [ ] **No clause became 🟩** in Scopes 1–3.
- [ ] `ledger.md` and `INDEX.md` rollups reconciled, both, with before/after numbers stated.
- [ ] `make ci` exit 0, 100.00 % coverage, redirected to a **file** and read from the file.
- [ ] `make gate-ran` exit 0 from **this** worktree, printed SHA checked against `git rev-parse HEAD`.

---

## Traps

🪤 **📜 will be abused under time pressure.** Every charter mark is a clause nobody will ever test
again. If in doubt, ⬜.

🪤 **Families cluster; clauses classify.** `MST-IDN-01` is testable while `SCAN-IDN-01` is a charter
statement, and both are IDN. Read each clause.

🪤 **`PERF` mostly is not about performance.** `MST-PERF-01` is a node-count assertion. Do not mark a
family ⬜-by-default on the strength of its name.

🪤 **Both rollups, or they drift.** `ledger.md` and `INDEX.md` each carry per-agent counts; updating
one is how they diverged before.

🪤 **Never measure the gate through a pipe.** `make ci | tail` reports `tail`'s exit code.

🪤 **Run `make gate-ran` from the worktree whose `HEAD` is the commit being proven** — a `SHA=`
argument is ignored, and it will happily print `GATE PROVEN` for a different commit.

---

## Test plan

| # | Test | Watched red first? | Status |
| --- | --- | --- | --- |
| A1 | `check_law_coverage.py` reports 0 rowless clauses | | |
| A2 | a planted rowless clause **fails** the gate (assertion E enforcing) | **required** | |
| A3 | a 🧱 row without a named gate is rejected | | |
| A4 | a 📜 row without a stated reason is rejected | | |
| A5 | rollup numbers are derived by the checker, and match `ledger.md` and `INDEX.md` | | |
| B1 *(Scope 4)* | a rewritten contract clause enumerates fields and its test cites the clause ID | | |

---

## Closeout — evidence

**Status:** *(SPEC → BUILT at handback)*

**Tree the proofs ran in:** *(path; `.env` present or not)*

**Result:** *(what is now true that was not)*

**Rows written:** *(count by kind — 🟩 / ⬜ / 🧱 / 📜 — and the per-agent breakdown)*

**Every 📜 justified:** *(list them with the reason; this is the part most likely to be challenged)*

**Rollups before → after:** *(both files, numbers from the checker not by hand)*

**Proof — assertion E watched failing:** *(paste)*

**Proof — the green run:** *(`make ci` exit code, counts, coverage)*

**`make gate-ran`:** *(printed SHA and the `git rev-parse HEAD` it was checked against)*

**Scope 4 landed or deferred:** *(say which, and why)*

**Not met / verified failing:** *(plainly)*

---

## Return notes

*(What the next sprint should know — especially which ⬜ rows look most worth turning green first,
since this sprint makes that backlog rankable for the first time.)*
