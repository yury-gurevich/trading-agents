<!-- Agent: planning | Role: sprint handover — every law clause has a row, and the row says how it is proven -->
# Sprint 204 — every law clause declares how it is proven, or that it cannot be

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-204-every-clause-declares-how-it-is-proven` <!-- create BEFORE any code -->
**Status:** BUILT
**Version:** 0.98.01
**Effort:** L
**Decisions:** work-queue **item 10** (hardening row **O**) · [DRIFT-058](../laws/drift-register.md) applied to the law book itself · conventions **§3** (Layer-0 green bill) · work-queue **item 30** deliberately **not** here — see Out of scope

> **Why this bump kind.** PATCH. No new capability, no agent behaviour change, nothing ships in an
> image. The deliverable is that a **warn-only gate becomes enforcing** and the law book stops having
> 101 silent holes. That is a fix to tooling and to documentation of what is already true.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until the Law reading record is written.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/*/laws/laws.md` (8 agents) | **LOCKED** constitutions | **Read-only. This sprint does not edit a single one.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/*/laws/test-plan.md` (8 agents) | proven 🟩 / unproven ⬜ per clause | **This is the only law-adjacent thing the sprint writes** |
| `docs/laws/conventions.md` | the status vocabulary and §3 (Layer-0 green bill) | Read; **this sprint extends the vocabulary here** |
| `docs/laws/dependencies.md` | the **Layer-0 dependency charter** — 32 `DEP-*` clauses | Read before classifying any agent `*-DEP-*` clause. It is their oracle |
| `docs/laws/ledger.md` + `docs/laws/INDEX.md` | the two rollups | **Both** must be reconciled — they drift when only one is updated |
| `docs/laws/drift-register.md` | the one law-adjacent file you may append to | A row is owed for any clause that turns out to be **wrong**, not merely unproven |

### The rule

1. Read every law file in the map below — whole file, first time.
2. Read each agent's `test-plan.md` alongside its `laws.md`.
3. Read [`conventions.md`](../laws/conventions.md) and [`drift-register.md`](../laws/drift-register.md).
4. Answer the law-cycle question below.
5. Write the **Law reading record** before your first change.
6. If a law contradicts this spec, **stop and report**. The law is more likely right than the spec.
7. If a law is **silent** where you needed a decision, that silence is a finding: record it.

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**No.** Writing a test-plan row **records how an existing clause is proven**; it creates no guarantee
that did not already exist. No `contracts/` file is touched, no `laws.md` is edited, no clause text
changes, no agent behaviour changes.

🪤 **The trap in this answer is the opposite of the usual one.** The usual failure is a sprint that
owes a law cycle and skips it. Here the temptation is to *invent* one — to rewrite a clause because
writing its row exposed that it is badly worded. **Do not.** A clause you believe is wrong is a
`drift-register.md` row and a report. Rewriting clauses is work-queue item 30 and is explicitly out
of scope; mixing it in turns an L sprint into an XL one and produces a rushed law cycle, which is the
failure mode the template's own warning describes.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/*/laws/test-plan.md` × 8 | that agent's `laws.md`; `conventions.md` | Every row must name a clause that exists and describe it truthfully |
| any `*-DEP-*` row | `docs/laws/dependencies.md`; `probes/checks.py` | conventions §3 — an agent DEP clause **declares which Layer-0 component it stands on**; the charter plus its probe is the oracle |
| `docs/laws/conventions.md` | itself | It is the authority for the status vocabulary this sprint extends |
| `scripts/check_law_coverage.py` **225** | `conventions.md` | It is the gate that enforces the convention |
| `docs/laws/ledger.md`, `docs/laws/INDEX.md` | both | Rollups are **derived by the gate**, never hand-counted |

⚠️ **The one invariant this sprint must not break: no clause may become 🟩.** This sprint makes the
book *honest*, not *greener*. A row that says ⬜ is a success. If you are writing a test to turn
something green, you have left the scope — stop and report.

---

## Goal

Every law clause in every agent has a test-plan row; each row declares **how** the clause is
proven — by a test, by a named CI gate, or not at all — and assertion E in
`scripts/check_law_coverage.py` is promoted from warn-only to enforcing.

## Why (context)

Work-queue **item 10** / hardening row **O**, carried since S157 and never picked up because it reads
as a 101-item slog.

🎯 **It is not. It is about rows, not tests** — which is the re-scope that makes it tractable. Item
10's own text: *"101 law clauses with no test-plan row; assertion E in `check_law_coverage.py` is
warn-only and **cannot be promoted until the rows exist**."* Writing 101 honest rows — most of them
⬜ — is mechanical. Writing 101 tests is a multi-sprint programme and is **not what this asks for**.

🚨 **This is [DRIFT-058](../laws/drift-register.md) applied to the law book itself.** That row, written
2026-09-13 out of S202, says: *a green row whose oracle cannot fail proves only that the oracle ran.*
A clause with **no row at all** is the same defect one level worse — there is not even an oracle to
interrogate, and the gate that should have said so has been warn-only.

### Measured, 2026-09-14 — read these before designing

`PYTHONPATH=. uv run python scripts/check_law_coverage.py` → **101** clauses with no test-plan row
(the `[carried]` number re-measured and **confirmed**), across **8** agents:

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

🎯 **They cluster into families, so the decision is per family and the application is mechanical:**

| Family | Missing | Missing in N agents | Cumulative |
| --- | --- | --- | --- |
| DEP | 18 | 6 | 17.8 % |
| SEC | 15 | 7 | 32.7 % |
| ORD | 12 | 7 | 44.6 % |
| IDN | 11 | 5 | 55.4 % |
| PERF | 7 | 7 | **62.4 %** |
| FAIL / NEV / IN / STA / OBS | 28 | 3–5 each | 90.1 % |
| TRG / TYP / OUT / IDM | 10 | 1–3 each | 100 % |

### What sampling the clauses actually showed — and it contradicted this spec twice

| Clause | Text (abridged) | What proves it |
| --- | --- | --- |
| `ANLZ-DEP-01` | *"`DEP-BUS`: requires request/reply and subscribe/publish"* | 🧱 the **Layer-0 charter** + its probe |
| `MST-DEP-03` | *"No dependency on any trading agent's code"* | 🧱 **import-linter**, contract *"Agents may not import one another"* |
| `MST-ORD-01` | *"`start()` must be called before `activate()`"* | ✅ an ordinary test; nobody wrote one |
| `MST-PERF-01` | *"`activate()` writes 1 `AgentInstance` + N `CapabilityGrant`"* | ✅ a **counting** assertion — not a performance claim |
| `MST-IDN-01` | *"`start()` writes Session node"* | ✅ testable — **and it already has a row** |
| `SCAN-IDN-01` | *"The scanner's sole job is universe → ranked candidates"* | 📜 a **charter statement**; no observation contradicts it |

🪤 **First contradiction: I generalised DEP to import-linter from a single sample, and it is wrong for
17 of 18.** Most agent DEP clauses name `DEP-BUS` / `DEP-POSTGRES` / `DEP-BROKER` / `DEP-FEED` — they
declare which **Layer-0 infrastructure** the agent stands on, and `docs/laws/dependencies.md` is that
charter (32 clauses), with `probes/checks.py` (**367** lines of `DEP-*`-tagged probes) as its oracle.
`MST-DEP-03` is the *exception*. Classify agent DEP rows against the charter, not the linter.

🪤 **Second contradiction: families cluster, clauses classify.** `MST-IDN-01` is testable and already
rowed while `SCAN-IDN-01` is a charter statement — same family. **Read every clause.** Marking a
family by its name is the exact error this spec made and had corrected by one sample.

---

## Scope — and what is deliberately NOT here

### 1. Extend the status vocabulary in `conventions.md`

Two additional kinds, each an **honest answer** rather than an excuse:

| Mark | Meaning | The Test column must contain |
| --- | --- | --- |
| 🟩 | proven by a functional test | the test name; its docstring cites the clause ID |
| ⬜ | owed a test | what is missing, where known |
| 🧱 | **structural** — proven by a named gate or charter, not a unit test | the gate **and** the specific rule, e.g. `import-linter: "Agents may not import one another"`, or `dependencies.md DEP-BUS-01 + probes/checks.py` |
| 📜 | **charter** — a purpose statement no observation could contradict | **why** it is unfalsifiable |

### 2. Write the 101 missing rows

Work **by family across agents**, not agent by agent — the judgement is per family and doing it
agent-first re-litigates the same question eight times. Most rows will be ⬜; that is correct.

### 3. Promote assertion E to enforcing

Flip it in `scripts/check_law_coverage.py` from `[WARN]` to a gate failure, so a new clause without a
row fails CI. **This is the point of the sprint** — the ratchet that stops the backlog regrowing.

### Out of scope (do NOT build this sprint)

- **Writing tests to turn ⬜ into 🟩.** Explicitly not this sprint.
- **Editing any `laws.md`.** Not one, not even to fix wording.
- **Work-queue item 30** (15 clauses asserting *"matches `contracts/<agent>.py` exactly"*). Same family
  of defect — a clause that is its own oracle — but each rewrite is a **full law cycle** and demotes
  greens under conventions §7a. 101 rows plus 15 law cycles is an XL sprint that would produce a
  rushed law cycle. It gets its own sprint.
- **Work-queue item 33** (57 PARAM/settings divergences). Same *shape*, different coupling
  (laws↔settings) and a different decision (putting secret names into PARAM tables as `NO (secret)`).

### The road not taken (LAW-06)

- **One sprint for items 10, 30 and 33.** I measured the hypothesis that they are one problem: same
  shape, but three couplings — laws↔test-plan, laws↔contracts, laws↔settings — with three different
  decisions. Rejected; only item 10 is here.
- **Writing the 101 tests.** Rejected: a multi-sprint programme, and not what item 10 asks for. Rows
  first is what makes the test backlog legible and rankable for the first time.
- **Adding rows but leaving assertion E warn-only.** Rejected — without the promotion the backlog
  regrows silently, which is precisely what item 33's 57 standing `[WARN]`s demonstrate.
- **Auto-generating rows from clause text.** Rejected: it would encode the family-name error above at
  scale. A generator may *list* the clauses; a human classifies them.

---

## The design decisions this sprint has to make

1. **Is 🧱 allowed to cite a charter, or only an executable gate?** Agent DEP clauses point at
   `dependencies.md`, whose own clauses are proven by `probes/checks.py` — that is a two-hop
   citation. Decide whether a 🧱 row must name the probe, or may name the charter clause. **Record the
   choice and why.**
2. **What happens to a 📜 clause's agent when rolling up?** Does a charter clause count in the
   denominator of "19 of 55 proven"? Either answer is defensible; an unrecorded answer is not.
3. **Does assertion E enforce only row *existence*, or also row *well-formedness*** (a 🧱 naming its
   gate, a 📜 stating its reason)? Existence is the minimum item 10 asks for; well-formedness is what
   stops 📜 becoming a dumping ground.
4. **Is a clause that is wrong, not merely unproven, in scope to flag?** Yes — as a
   `drift-register.md` row, never as an edit.

---

## Blast radius — measured 2026-09-14

| What | Detail |
| --- | --- |
| Files changed | 8 × `agents/*/laws/test-plan.md`; `docs/laws/conventions.md`; `scripts/check_law_coverage.py` **225**; `docs/laws/ledger.md`; `docs/laws/INDEX.md` |
| Contract change? | **No** |
| Graph vocabulary change? | **No** |
| Agent behaviour change? | **None.** If behaviour changes, scope has leaked |
| Deploy implication | **None** — nothing ships in an agent image. No retag, no `up` |
| Live data touched | None |

🚨 **The rollups will get *worse*, and that is the correct result.** Adding ⬜ rows for
previously-rowless clauses changes the proven/total ratios in `ledger.md` and `INDEX.md`. **State
before and after.** A ratio that falls because the denominator became honest is a success and must not
be presented as a regression or quietly smoothed.

🪤 **Derive the rollups with the gate, never by arithmetic** — it has rejected hand-counted rollups
twice (S199's claimed 17/54, S172's claimed 15/52).

---

## Steps, in order

1. **Read the laws** (MUST RULE) and write the **Law reading record** below.
2. **Record the design decisions** (the four above) in `docs/design-log.md`.
3. **Plant the failing test first**: add a clause with no test-plan row, run `make ci`, watch
   assertion E **pass** (it is warn-only today). That red-first is inverted — capture the *current*
   behaviour, then after step 5 the same plant must **fail**. Paste both.
4. **Extend `conventions.md`** with 🧱 and 📜 and their evidence requirements.
5. **Write the 101 rows**, family by family across agents.
6. **Promote assertion E**, then re-run the step-3 plant and watch it go red. Restore.
7. **Reconcile both rollups** from the gate's own numbers.
8. **`make ci` green** — all 12 steps, **redirected to a file, never piped**.
9. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 assertion E fails a rowless clause | a clause added to any `laws.md` with no test-plan row | `make ci` exits non-zero naming the clause |
| A2 | assertion E passes when every clause has a row | the tree as delivered | `check_law_coverage.py` reports **0** rowless clauses |
| A3 | 🪤 a 🧱 row with no named gate is rejected | a 🧱 row whose Test column names no gate | the gate refuses it *(only if decision 3 says well-formedness is enforced)* |
| A4 | 🪤 a 📜 row with no stated reason is rejected | a 📜 row with an empty justification | as A3 |
| A5 | rollups match the gate | the delivered tree | `ledger.md` and `INDEX.md` numbers equal the checker's |

---

## Success factors

- [ ] `check_law_coverage.py` reports **0** clauses without a test-plan row.
- [ ] Assertion E is **enforcing**, watched failing on a planted rowless clause, then restored.
- [ ] 🧱 and 📜 are documented in `conventions.md` with their evidence requirements.
- [ ] Every 🧱 row names the gate **and** the specific rule or charter clause.
- [ ] Every 📜 row states why no observation could contradict the clause.
- [ ] **No clause became 🟩.**
- [ ] **No `laws.md` was edited.**
- [ ] `ledger.md` and `INDEX.md` reconciled, both, with before/after numbers from the gate.
- [ ] The four design decisions recorded in `docs/design-log.md` with rejected alternatives.
- [ ] Law-cycle question answered **No** with its reason, in the Law reading record.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **📜 will be abused under time pressure.** Every charter mark is a clause nobody tests again. The
test is: *could any observation contradict this clause?* If yes, it is ⬜. Expect every 📜 to be
challenged individually at handback.

🪤 **Families cluster; clauses classify.** This spec asserted "DEP = import-linter" and was wrong for
17 of 18, and asserted IDN was charter when `MST-IDN-01` is testable and already rowed. **Read every
clause.** If you find more spec errors of this kind, say so in Return notes — specs here are corrected
by the build, not defended.

🪤 **`PERF` mostly is not about performance.** `MST-PERF-01` is a node-count assertion.

🪤 **Both rollups, or they drift.** Updating one is how they diverged before.

🪤 **A clause that is wrong is not a clause you may fix.** Drift row and report.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `scripts/check_law_coverage.py` **225** *(already over — it is a `scripts/` file and
  `scripts/` is **exempt** from the module-size gate; do not "fix" it)*, `probes/checks.py` **367**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — `make ci | tail` reports *`tail`'s* exit code. Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**. This sprint needs none; **say so**.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** — it resolves the SHA from
   the working directory and ignores a `SHA=` argument. **Check the printed SHA against
   `git rev-parse HEAD`.**
2. Merge to `main` locally and push. 🪤 Check you are not on the branch already.
3. **Post-merge CodeQL** — `codeql.yml` runs only on `main`.
4. **Deploy: none.** Nothing in this sprint reaches an agent image.

---

## Handover — paste this to Codex

```text
Sprint 204 — every law clause declares how it is proven, or that it cannot be.
Branch: sprint-204-every-clause-declares-how-it-is-proven (create it before any code; never main).
Full spec: docs/sprints/sprint-204-every-clause-declares-how-it-is-proven.md — read it all first.

WHAT: 101 law clauses across 8 agents have no test-plan row, so assertion E in
scripts/check_law_coverage.py has been warn-only. Give every clause a row that declares HOW it is
proven, then promote assertion E to enforcing.

THIS IS ABOUT ROWS, NOT TESTS. Do not write tests to turn anything green. A row that says
"unproven" is a success. If you are writing a test, you have left the scope — stop and report.

MUST RULE — before any code: read every agents/*/laws/laws.md and test-plan.md you touch, plus
docs/laws/conventions.md, docs/laws/dependencies.md and docs/laws/drift-register.md. Then write the
"Law reading record" section at the bottom of the spec. It is a gate, not advice.

LAW-CYCLE ANSWER: No. Writing a row records how an existing clause is proven; it adds no guarantee.
DO NOT EDIT ANY laws.md — not one, not even wording. A clause you believe is wrong is a
drift-register.md row plus a report. Rewriting clauses is work-queue item 30 and is out of scope.

THE WORK:
1. Extend docs/laws/conventions.md with two row kinds beyond the existing proven/unproven:
     structural — proven by a named gate or charter, not a unit test. The Test column must name the
                  gate AND the specific rule (e.g. import-linter "Agents may not import one another",
                  or dependencies.md DEP-BUS-01 + probes/checks.py).
     charter    — a purpose statement no observation could contradict. Must state WHY.
2. Write the 101 rows. Work family-by-family ACROSS agents, not agent by agent.
3. Promote assertion E from [WARN] to a gate failure.
4. Reconcile the rollups in BOTH docs/laws/ledger.md AND docs/laws/INDEX.md, using numbers the gate
   derives — never hand-counted. It has rejected hand-counted rollups twice before.

GET THE CURRENT LIST WITH:
  PYTHONPATH=. uv run python scripts/check_law_coverage.py

TRAPS, named because a trap not written down gets hit:
- Families cluster, clauses classify. This spec itself asserted "DEP is import-linter" and was WRONG
  for 17 of 18 — most agent DEP clauses name DEP-BUS/DEP-POSTGRES/DEP-BROKER/DEP-FEED and point at
  the Layer-0 charter in docs/laws/dependencies.md, whose oracle is probes/checks.py. MST-DEP-03 is
  the exception. It also asserted IDN was charter, but MST-IDN-01 is testable and already has a row.
  READ EVERY CLAUSE. If you find more spec errors, say so in Return notes.
- PERF is mostly not about performance. MST-PERF-01 is a node-count assertion.
- "charter" will be abused under time pressure. The test is: could any observation contradict this
  clause? If yes it is unproven, not charter. Every charter mark will be challenged at handback.
- The rollups will get WORSE as denominators become honest. That is the correct result. State before
  and after; do not smooth it.
- scripts/ is EXEMPT from the 200-line module-size gate. check_law_coverage.py is 225 lines; do not
  "fix" that.
- Never measure the gate through a pipe: `make ci | tail` reports tail's exit code. Redirect to a
  file and read the file.
- Run `make gate-ran` from the worktree whose HEAD is the commit being proven; a SHA= argument is
  ignored. Check the printed SHA against `git rev-parse HEAD`.

ORDER: laws → law reading record → design decisions to docs/design-log.md → plant a rowless clause
and confirm it currently PASSES (warn-only) → extend conventions → write rows → promote assertion E
→ re-plant and watch it FAIL → restore → reconcile both rollups → make ci to a file → fill handback.

FOUR DESIGN DECISIONS the spec asks you to make and record: (1) may a structural row cite a charter,
or must it name an executable probe; (2) do charter clauses count in rollup denominators; (3) does
assertion E enforce row existence only, or well-formedness too; (4) confirm that a wrong clause is
flagged as drift, never edited.

HANDBACK IS MANDATORY: fill the Law reading record BEFORE coding, then Test plan results, Closeout
evidence with real pasted output, and Return notes; set Status: BUILT. Anything not met is stated
plainly as "verified failing" or "not done". An incomplete handback is returned, not repaired.

Deploy: none. Nothing here reaches an agent image. No .env needed — say which tree you ran in.
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

| Law file | Read in full? | Clauses that bind this work | Anything ⬜ you relied on |
| --- | --- | --- | --- |
| `docs/laws/conventions.md` | Yes | §2 append-only IDs; §3 green definition; §7/§7a test-plan citation and summary fidelity; §9 drift-register rule | No unproved row used as authority; current §3 lacks 🧱/📜, which this sprint extends |
| `docs/laws/dependencies.md` | Yes | Layer-0 `DEP-*` charter, probe sequencing, and `probes/` as the dependency oracle | Live dependency greens are not re-proven here; dependency rows cite the charter/probe surface, not a fresh probe run |
| `agents/analyst/laws/*` | Yes | Existing `ANLZ-*` clauses and current analyst test-plan rows; missing rows from the checker only | Existing ⬜ rows identify backlog only; no analyst clause is promoted |
| `agents/execution/laws/*` | Yes | Existing `EXEC-*` clauses and current execution test-plan rows; broker-boundary and dependency rows classify from clause text | Existing ⬜ rows identify backlog only; no execution clause is promoted |
| `agents/master/laws/*` | Yes | Existing `MST-*` clauses and current master test-plan rows; `MST-DEP-03` is the import-linter exception among DEP rows | Existing ⬜ rows identify backlog only; no master clause is promoted |
| `agents/monitor/laws/*` | Yes | Existing `MON-*` clauses and current monitor test-plan rows | Existing ⬜ rows identify backlog only; no monitor clause is promoted |
| `agents/portfolio_manager/laws/*` | Yes | Existing `PM-*` clauses and current PM test-plan rows; DRIFT-039 remains a false/unbuilt clause finding, not a row-edit fix | Existing ⬜ rows identify backlog only; no PM clause is promoted |
| `agents/provider/laws/*` | Yes | Existing `PROV-*` clauses and current provider test-plan rows; DRIFT-040 remains an open provenance gap | Existing ⬜ rows identify backlog only; no provider clause is promoted |
| `agents/reporter/laws/*` | Yes | Existing `RPT-*` clauses and current reporter test-plan rows | Existing ⬜ rows identify backlog only; no reporter clause is promoted |
| `agents/scanner/laws/*` | Yes | Existing `SCAN-*` clauses and current scanner test-plan rows; DRIFT-047 stays out of scope | Existing ⬜ rows identify backlog only; no scanner clause is promoted |

**Law-cycle question answered:** No. This sprint writes test-plan rows that describe how existing
clauses are proven, structurally covered, charter-only, or still unproven. It touches no
`contracts/` file, edits no `laws.md`, and adds no new agent guarantee.

**Laws that contradicted the spec, if any:** None found. The spec's known traps were confirmed:
most agent `DEP` clauses point at the Layer-0 dependency charter rather than import-linter, while
`MST-DEP-03` is the import-boundary exception; family names clustered the work, but each clause still
had to be classified individually.

---

## Test plan results — fill at handback

| # | Test | Status |
| --- | --- | --- |
| A1 | assertion E fails a rowless clause | Passed. Pre-change planted `RPT-PERF-99` was warn-only and `make ci` exited 0; post-change the same plant made `make ci` exit non-zero naming `RPT-PERF-99`. |
| A2 | 0 rowless clauses reported | Passed. `PYTHONPATH=. uv run python scripts\check_law_coverage.py` exited 0 with no output after restore. |
| A3 | malformed 🧱 row rejected | Passed. Temporary `SCAN-DEP-01` structural row with `_tbd_` test failed: `structural row names no gate, probe, or charter`, `exit=1`. |
| A4 | malformed 📜 row rejected | Passed. Temporary `SCAN-IDN-01` charter row with `_tbd_` test failed: `charter row states no unfalsifiable reason`, `exit=1`. |
| A5 | rollups match the gate | Passed. Delivered checker run exited 0; no ledger/index rollup drift reported. |

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in:** `C:\Users\yury_\Downloads\project\trading-agents`; `.env` present in the worktree but this sprint did not read or require secrets.

**Result:** All target law clauses now have test-plan rows, assertion E is an enforcing failure instead of a warn-only advisory, and 🧱/📜 rows have documented well-formedness rules checked by the law-coverage gate. No delivered `laws.md` edit remains.

**Rows written, by kind:** 🟩 0 / ⬜ 80 / 🧱 19 / 📜 2. Per agent: analyst ⬜9 🧱3; execution ⬜10 🧱3; master ⬜18 🧱2 📜1; monitor ⬜7; portfolio_manager ⬜9 🧱3; provider ⬜17 🧱5; reporter ⬜1; scanner ⬜9 🧱3 📜1.

**Every 📜 justified:** `MST-FAIL-03` is the architectural RISK-1 mitigation charter; no single functional observation can prove the envelope, and narrower FAIL rows cover mechanics. `SCAN-IDN-01` is the scanner mission statement; filter/rank/drop obligations are falsified by narrower IN/OUT/NEV rows, not by one mission observation.

**Rollups before → after:** Green/total counters stayed unchanged because the checker already counted law IDs in denominators: provider 16/62 → 16/62; analyst 25/48 → 25/48; scanner 18/41 → 18/41; portfolio_manager 29/48 → 29/48; execution 35/61 → 35/61; monitor 20/46 → 20/46; reporter 20/39 → 20/39; master 15/44 → 15/44. The changed number is rowless clauses: 101 → 0. Both `docs/laws/ledger.md` and `docs/laws/INDEX.md` were reconciled to that gate behavior.

**Proof — assertion E watched passing, then failing:** Pre-change plant (`RPT-PERF-99`) with temporary reporter rollup adjustment, `make ci > $env:TEMP\s204-assertion-e-warn-only-ci.txt 2>&1`, shell observed `exit=0`:
```text
[WARN] law coverage: 102 clause(s) have no test-plan row (assertion E warn-only)
[WARN] agents/reporter/laws/test-plan.md: 2 missing row(s): RPT-PERF-99, RPT-TYP-03
Required test coverage of 100.0% reached. Total coverage: 100.00%
================= 2706 passed, 4 skipped in 208.24s (0:03:28) =================
No known vulnerabilities found
Detect secrets...........................................................Passed
```
Post-change re-plant after assertion E promotion, `make ci > $env:TEMP\s204-assertion-e-fails-ci.txt 2>&1`, shell observed non-zero:
```text
[FAIL] law coverage: 1 clause(s) have no test-plan row (assertion E)
[FAIL] agents/reporter/laws/test-plan.md: 1 missing row(s): RPT-PERF-99
make: *** [Makefile:53: ci] Error 1
```

**Proof — the green run:** `make ci > C:\Users\yury_\AppData\Local\Temp\s204-clean-ci-final.txt 2>&1`, shell observed `exit=0`:
```text
uv run ruff check . --output-format=github
uv run ruff format --check .
uv run mypy kernel contracts agents orchestration surfaces
uv run lint-imports
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
Required test coverage of 100.0% reached. Total coverage: 100.00%
================= 2710 passed, 4 skipped in 207.55s (0:03:27) =================
No known vulnerabilities found
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
```

**`make gate-ran`:** `make gate-ran` from `C:\Users\yury_\Downloads\project\trading-agents` printed:
```text
GATE PROVEN for 4a5184fbf4edabce8148b04e5f9d44080d309019:
  CI: success (attempt 1)
  Security Findings: success (attempt 1)
```
`git rev-parse HEAD` matched `4a5184fbf4edabce8148b04e5f9d44080d309019`.

**Design decisions recorded:** `DL-112`.

**Not met / verified failing:** Deploy is not applicable; nothing here reaches an agent image.

---

## Return notes

The highest-value ⬜ rows to turn green first are the PM snapshot cluster (`PM-STA-04` / `PM-OUT-06` / `PM-OBS-01`, tracked by DRIFT-039), provider total-space completeness (`PROV-OUT-03`), and master RSA/Key Vault credential rows if the next sprint is platform-hardening. Structural rows are not green proof and do not improve the numerator; they only make the dependency contract explicit.

Spec correction found during build: the rollup green/total counters did not get worse, because the checker already counted law IDs in denominators before rows existed. The honest change was rowless clauses going from 101 to 0, while green/total stayed the same.
