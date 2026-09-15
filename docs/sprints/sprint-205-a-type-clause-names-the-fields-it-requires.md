<!-- Agent: planning | Role: sprint handover — a type clause names the fields it requires -->
# Sprint 205 — a type clause names the fields it requires, so the contract file stops being its own oracle

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-205-a-type-clause-names-the-fields-it-requires` *(created from `21a746e`, before any code)*
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** L
**Decisions:** work-queue **item 30** · [DRIFT-047](../laws/drift-register.md) (the scanner instance this closes) · [DL-121](../design-log.md) (where the item was first measured) · `conventions.md` §3 (gray → green, and the 🧱/📜 row kinds S204 made checkable) · **the precedent is already in the law book: `PM-TYP-03`, rewritten by S184**

> **Why this bump kind.** PATCH. No agent gains a capability and no contract changes shape. Twelve
> clauses currently assert something no observation can contradict; they are narrowed to something
> that can go red. That is a defect fix in the evidence system, not a new guarantee.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

This sprint *is* a law cycle — twelve of them. The MUST RULE is not a formality here; it is the work.

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **Amended in this sprint, under the law cycle below** — version bump + Changelog line per agent. Never a quiet edit, never a clause deleted |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | **Rows move here.** A green whose test no longer proves the rewritten clause is **demoted**, explicitly |
| `agents/portfolio_manager/laws/laws.md` | `PM-TYP-03` + the v1.3 Changelog entry | **Read first — this is the worked example.** Do not re-do PM |
| `docs/laws/conventions.md` §3 | gray → green, 🧱 structural, 📜 charter | Read — it decides which rows may exist at all |
| `docs/laws/drift-register.md` | the correction worklist | **`DRIFT-047` is closed by this sprint.** The one law-adjacent file you may append to |
| `agents/provider/laws/laws.md` | **LOCKED v1 (S69)** | **Do not touch.** Measured: provider has no clause naming a `contracts/` file. It is not in scope |
| `docs/laws/_TEMPLATE.md` | the law template | **Do not edit** (CLAUDE.md hard rule) |

Binding sections here: **`TYP`** in twelve agent law books, plus **`OUT`** wherever a `TYP` clause
you rewrite cites an `OUT` clause as the reason a field must exist.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Answer: NO to both — and the second half is the whole point.**

- **No `contracts/` file changes.** Not one. If you find yourself editing a contract to make a clause
  true, **stop and report**: that is a different sprint, and the finding is more valuable than the fix.
- **No new guarantee.** Each rewritten clause promises *less* than the old text appeared to, and
  promises it *checkably*. The old text implied the payload matched the file in every respect; the new
  text names the fields the agent's own clauses depend on.

🚨 **It is still a full law cycle, twelve times over**, because the clause text changes: per agent,
a `laws.md` version bump, a Changelog line, the `test-plan.md` row updated (including **demotions**),
and the rollup recomputed in **both** `docs/laws/ledger.md` **and** `docs/laws/INDEX.md`.

🪤 **The rollup is derived, not declared.** `make ci` recomputes it — let the gate tell you the
number, and if your arithmetic disagrees with the gate, the gate is right.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/analyst/laws/laws.md:154-156` | analyst `laws.md` + `test-plan.md` | `ANLZ-TYP-01` — the "match exactly" tail sits on a clause whose *first* sentence is falsifiable |
| `agents/curator/laws/laws.md:112` | curator `laws.md` + `test-plan.md` | `CUR-TYP-01` |
| `agents/deliberator/laws/laws.md:102` | deliberator `laws.md` + `test-plan.md` | `DLIB-TYP-01` |
| `agents/execution/laws/laws.md:200` | execution `laws.md` + `test-plan.md` | `EXEC-TYP-03`, and `CONTRACT.version` is named in it |
| `agents/forecaster/laws/laws.md:103` | forecaster `laws.md` + `test-plan.md` | `FORE-TYP-01` (and `FORE-TYP-03`, second shape) |
| `agents/monitor/laws/laws.md:110` | monitor `laws.md` + `test-plan.md` | `MON-TYP-01` (and `MON-TYP-02`, second shape) |
| `agents/master/laws/laws.md:105` | master `laws.md` + `test-plan.md` | `MST-TYP-01` — **LOCKED v1.2**, and its phrasing differs; see the per-clause decision |
| `agents/operator/laws/laws.md:110` | operator `laws.md` + `test-plan.md` | `OPR-TYP-01` |
| `agents/reporter/laws/laws.md:92` | reporter `laws.md` + `test-plan.md` | `RPT-TYP-01` (and `RPT-TYP-03`, second shape) |
| `agents/researcher/laws/laws.md:95` | researcher `laws.md` + `test-plan.md` | `RES-TYP-01` |
| `agents/scanner/laws/laws.md:140` | scanner `laws.md` + `test-plan.md` | `SCAN-TYP-01` — **this is `DRIFT-047`** |
| `agents/supervisor/laws/laws.md:99` | supervisor `laws.md` + `test-plan.md` | `SUP-TYP-01` |
| `tests/test_contract_values.py` **173** | `agents/portfolio_manager/laws/laws.md` | the PM precedent test lives here; follow its shape |

⚠️ **The one invariant this sprint must not break: a clause may be narrowed, never weakened into
silence.** S184's rule, stated in the PM v1.3 Changelog: *"nothing the old clause asserted may
disappear — it moves to new clauses that start ⬜ unproven, so the amendment adds asserted truth
rather than removing it."* If the old wording implied a guarantee your enumeration does not carry,
that guarantee goes somewhere — a named field, a new clause, or a `drift-register.md` row. **It may
not simply stop being asserted.** If you cannot find where it goes, stop and report.

---

## Goal

Twelve law clauses that name a `contracts/` file as the authority on their own payloads are rewritten
to **enumerate the fields those payloads must carry**, each field traceable to the clause that needs
it — so deleting a required field from a contract turns a test **red** instead of leaving every test
green. The law book's `TYP` rollup then reports coverage it actually has.

## Why (context)

The `laws → test-plan → tests` loop is CI-enforced, and since [S204](sprint-204-every-clause-declares-how-it-is-proven.md)
a clause with no proof row **fails the gate**. Contracts sit outside that loop. The only link between
them is a family of clauses asserting *"X matches `contracts/<agent>.py` exactly"* — which makes the
file both the claim and the oracle, so the claim cannot fail.

🚨 **Not theoretical, and measured twice:**

- **S183** added `skipped_filters` to `Candidate` **and** `FilterVerdict` and moved
  `contracts.scanner.CONTRACT.version` 0.2.0 → 0.2.1 **with every test green**, because `SCAN-TYP-01`
  names the file as its own oracle — and does not name `FilterVerdict` at all, the type S183 changed
  most ([DRIFT-047](../laws/drift-register.md)).
- **`PM-NEV-09`** turned out to be *unexpressible* in the contract that carried its evidence:
  `GateOutcome.passed: bool` has two states where the clause requires three
  ([DRIFT-046](../laws/drift-register.md)). A clause can be false in the type system and green in CI
  at the same time.

🎯 **The pattern is already in the law book and does not need inventing.** S184 rewrote `PM-TYP-03`
from *"matches `contracts/portfolio_manager.py` exactly"* to an enumeration — read it first
(`agents/portfolio_manager/laws/laws.md:172-180`). It even states the reason in the clause text:
*"the clause, not the file, is the authority on what must be present."* This sprint applies that
decision to the other twelve. **PM is done; do not re-do it.**

### Measured, 2026-09-14 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Clauses naming a `contracts/` file as their authority | **12** | *[measured]* `grep -n "contracts/" agents/*/laws/laws.md`, then read each hit — 11 say "match … exactly", `MST-TYP-01` says "are declared in" |
| Second, related shape: "graph node payload matches the contract/schema" | **3** — `FORE-TYP-03`, `MON-TYP-02`, `RPT-TYP-03` | *[measured]* same sweep. **Partly falsifiable** (a round-trip test can check serialisation), so a different family — classify, do not assume |
| The carried figure in work-queue item 30 | **"15"**, measured 2026-08-20 | *[re-measured]* 12 + 3 = 15 reconciles it, **and `PM-TYP-03` was a 16th, already rewritten by S184.** The number was right; its composition was not known |
| Of the 12, how many are 🟩 today | **4** — `ANLZ-TYP-01`, `EXEC-TYP-03`, `RPT-TYP-01`, `SCAN-TYP-01` | *[measured]* each agent's `test-plan.md` |
| What those 4 greens actually cite | a `*_is_deserializable` round-trip test, in all four cases | *[measured]* e.g. `test_scanner_pubsub.py::test_scan_result_node_candidates_are_deserializable` |
| Of the 12, how many are ⬜ today | **8** | *[measured]* `CUR/DLIB/FORE/MON/MST/OPR/RES/SUP-TYP-01`; several cite `_tbd_` |
| Files in `contracts/` | **25** (incl. `__init__.py`) | *[measured]* `ls contracts/*.py \| wc -l` |
| Contract files citing a clause ID | **0** | *[measured]* item 30's original sweep, unchanged |
| The precedent test | `tests/test_contract_values.py::test_gate_outcome_has_three_wire_states_and_legacy_passed_view` (file is **173** lines) | *[measured]* read it before writing yours |

🪤 **Read the four greens before you touch them.** A round-trip test proves *"what we wrote, we can
read back"*. It does **not** prove a field exists, and it stays green when a field is deleted from
both sides. Those four are the rows most likely to need **demotion**, and a demotion here is a
correct result, not a regression.

---

## Scope — and what is deliberately NOT here

1. **Classify all 15 clauses first, in the sprint doc, before editing any law.** For each: is it
   (a) file-as-oracle → rewrite, (b) serialisation-shape → keep, and say why it is falsifiable, or
   (c) already fine? **The classification is a deliverable**, not scratch work — it is what makes the
   rewrite reviewable.
2. **Rewrite each (a) clause to enumerate its required fields**, following `PM-TYP-03`. Each field
   names the clause that requires it (`PM-TYP-03` cites `PM-OUT-01`/`PM-OUT-02`). A field no clause
   requires is a finding — either the clause is missing or the field is not load-bearing; **say
   which**, do not silently include or exclude it.
3. **Write one falsifiable test per rewritten clause**, citing the clause ID in its docstring, that
   fails if a required field is removed from the contract type.
4. **Update every `test-plan.md` row**, including demotions with a stated reason.
5. **Per-agent law cycle:** version bump, Changelog line, rollups recomputed by the gate in both
   `ledger.md` and `INDEX.md`.
6. **Close `DRIFT-047`** with the clause text that closes it, and make sure `SCAN-TYP-01` now names
   **`FilterVerdict`** — the type S183 changed and the clause never mentioned.

### Out of scope (do NOT build this sprint)

- **Any edit to `contracts/`.** If a clause cannot be satisfied by the current contract, that is
  `DRIFT-046`'s shape: file a drift row and report. Do not fix the type.
- **Provider laws.** LOCKED v1, and measured to have no clause in this family.
- **PM.** Already done by S184. Read it, cite it, leave it.
- **Making `CONTRACT.version` mean something.** `EXEC-TYP-03` and `SCAN-TYP-01` both name it, and
  nothing enforces that it moves when the shape moves. Real, and a separate decision — file it.
- **Promoting any clause that is gray for an unrelated reason.** This sprint touches `TYP` rows only.
- **No ADR reversal.** An ADR is reversed by a new ADR, never by a sprint.

### The road not taken (LAW-06)

- **One clause, one sprint (twelve sprints).** Rejected: the decision is made once — S184 made it —
  and repeating the ceremony twelve times buys nothing but twelve merges. The per-agent work here is
  mechanical *after* the classification.
- **A generic test that walks every contract and asserts "no field was removed since the last run"**
  (a snapshot/golden file). Rejected: it makes the *previous run* the oracle instead of the file —
  the same defect wearing a third hat. It would also go green on a field nobody ever required.
- **Deleting the "match exactly" sentence and asserting nothing in its place.** Rejected: that
  weakens the constitution into silence, which the invariant above forbids. The clause must say less
  *and check more*, not simply say less.
- **Rewriting the three serialisation clauses too, in the same pass.** Rejected as a default: they
  may already be falsifiable by a round-trip test. Classify them; rewrite only what item 1's
  classification says is file-as-oracle, and record the call.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Where the enumeration tests live.** One parameterised module (following
   `tests/test_contract_values.py`) versus a test per agent in `agents/<name>/tests/`. The 200-line
   hard block bites a single module at twelve agents; agents-are-islands does **not** forbid a shared
   test, but a shared test must still cite each clause ID in a docstring the coverage checker can see.
   **Decide, and state how clause citation survives parameterisation** — a `pytest.mark.parametrize`
   whose docstring names no clause is how a whole family goes uncited at once.
2. **What "required field" means for a payload with optional fields.** `PM-TYP-03` says *"carry, at
   minimum, the fields its own clauses require"*. Decide whether optionality is part of the clause
   (must the field be present-and-non-None, or merely declared?) and apply one rule everywhere.
3. **`MST-TYP-01`.** Its phrasing differs — *"are declared in `contracts/master.py`. All are Pydantic
   `_Frozen` models. `AgentState` is a `StrEnum`."* The second and third sentences **are** falsifiable.
   Decide: rewrite the first sentence only, or leave the clause alone and record why. Master laws are
   **LOCKED v1.2** and S203 just declined to touch them for a different reason ([DRIFT-059](../laws/drift-register.md)) —
   either answer is defensible; an unstated one is not.
4. **The four greens.** Per clause: write a real field test (preferred) or demote to ⬜. Demotion is
   an acceptable outcome and must be stated as one. **Do not keep a green by arguing the round-trip
   test covers the new wording** unless you can say which assertion in it fails when a field is
   deleted.

🪤 **Take the next free DL number, then re-check it at merge.** `DL-166` is taken (S203, 2026-09-14).
The log has historic duplicates and entries are prepended at the top *and* appended at the bottom.

---

## Blast radius — measured 2026-09-14

| What | Detail |
| --- | --- |
| Files changed | 12 × `agents/<name>/laws/laws.md`, 12 × `agents/<name>/laws/test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md`, and the new/changed test modules (`tests/test_contract_values.py` **173**, or new per-agent files) |
| Agents affected | analyst, curator, deliberator, execution, forecaster, master, monitor, operator, reporter, researcher, scanner, supervisor — **law text and tests only.** No agent module changes; none imports another |
| Contract change? | **No.** Zero files in `contracts/` may change. This is a hard boundary of the sprint |
| Graph vocabulary change? | **No** |
| New env keys / tunables | **None** |
| Deploy implication | **None — no deploy.** No agent behaviour changes. Do not build images, do not retag |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record. Read `PM-TYP-03` first.
2. **Publish the classification table** (scope item 1) in this doc before any edit.
3. **Record the design decisions** in `docs/design-log.md`.
4. **Plant the failing test first** for one agent — delete a required field from a *local copy* of
   the thinking, not the file: the test must fail because the assertion names a field, so write the
   test against the clause and watch it fail before the clause exists. Paste the red output.
5. **Implement**, agent by agent: clause → test → test-plan row → version bump → Changelog line.
6. **Law cycle** per agent; let the gate recompute both rollups.
7. **Prove the guards can fail (DL-70)** — for at least **three** agents spanning different payload
   shapes, temporarily remove a required field from the contract type, watch the new test go red,
   **restore it**, and paste each. 🚨 This is the only proof that the rewrite achieved anything: the
   old clauses were green *because* nothing could make them red.
8. **Close `DRIFT-047`** and re-read `DRIFT-046` — say whether it is affected.
9. **`make ci` green** — all 12 steps, **redirected to a file, never piped**.
10. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 each rewritten clause has a test that names its required fields | the contract type as shipped | every field the clause enumerates is present on the type |
| A2 | 🪤 removing a required field turns that test **red** | field deleted from the contract type, then restored | the clause can now fail — done for ≥ 3 agents, output pasted |
| A3 | `SCAN-TYP-01` names and checks `FilterVerdict` | the S183 shape | the type S183 changed is inside the clause's reach (`DRIFT-047`) |
| A4 | `EXEC-TYP-03`'s `CONTRACT.version` sentence | current `contracts.execution.CONTRACT` | either it is checked, or the gap is filed — **not left implied** |
| A5 | every demoted row states its reason | the 4 current greens | a demotion reads as a decision, not an omission |
| A6 | the rollup the gate computes matches the test-plan rows | `make ci` | no hand-counted number appears anywhere |

---

## Success factors

- [ ] All 15 clauses classified in this doc, with the (a)/(b)/(c) call and its reason.
- [ ] Every (a) clause enumerates its required fields, each traceable to a clause that needs it.
- [ ] Every rewritten clause has a passing test citing its ID in the docstring.
- [ ] **≥ 3 agents:** a required field removed, the test watched **red**, the field restored — pasted.
- [ ] Every green that no longer holds is **demoted with a stated reason**, not quietly kept.
- [ ] `DRIFT-047` closed; `SCAN-TYP-01` names `FilterVerdict`.
- [ ] Per-agent `laws.md` version bumped with a Changelog line; **nothing the old clause asserted
      has stopped being asserted somewhere**.
- [ ] Rollups in `ledger.md` **and** `docs/laws/INDEX.md` recomputed **by the gate**.
- [ ] **Zero changes under `contracts/`** (`git diff --stat contracts/` is empty).
- [ ] Design decisions recorded with rejected alternatives.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage, redirected to a file and read from the file.
- [ ] `make gate-ran` exit 0 from **this** worktree, printed SHA checked against `git rev-parse HEAD`.

---

## Traps

🪤 **A test that reads the contract and asserts "these fields exist" is only falsifiable if the field
list lives in the *test*, not derived from the type.** `assert set(Model.model_fields) == set(Model.model_fields)`
is the same tautology one layer down. Write the names out. Yes, literally.

🪤 **The four greens are the trap, not the eight grays.** A gray row costs nothing but honesty; a
green row that cannot fail is coverage the ledger reports and does not have. Expect demotions and
report them as results.

🪤 **"Matches exactly" may be hiding a real guarantee.** Before deleting the phrase, ask what a reader
relied on it for. If the answer is "that no field is ever removed", that duty must land somewhere —
a clause, or a drift row saying nobody owns it.

🪤 **A parameterised test can decouple the docstring from the clause.** The coverage checker reads
docstrings; twelve clauses covered by one docstring naming one ID leaves eleven uncited and the gate
(since S204) will tell you — read what it says rather than adding IDs until it goes quiet.

🪤 **Never measure the gate through a pipe.** `make ci | tail` reports *`tail`'s* exit code. Redirect
to a file and read the file.

🪤 **Run `make gate-ran` from the worktree whose `HEAD` is the commit you are proving** — it resolves
the SHA from the working directory and ignores a `SHA=` argument. Check the printed SHA.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `tests/test_contract_values.py` **173**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**. Nothing in this sprint needs
  live data; if you think it does, you have left the scope.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
2. Merge to `main` locally and push. 🪤 Check you are not on the branch already — a `git merge` from
   the branch's own worktree says *"Already up to date"* and merges nothing.
3. **Post-merge CodeQL.** `codeql.yml` runs **only on `main`**, so a green branch gate is not proof of
   a CodeQL-clean merge. Check after merging.
4. **No deploy.** Law text and tests only — no agent behaviour changes. Do not retag the fleet.

---

## Handover — paste this to Codex

```text
Sprint 205 — a type clause names the fields it requires.
Branch: sprint-205-a-type-clause-names-the-fields-it-requires (already created; never work on main).
Spec: docs/sprints/sprint-205-a-type-clause-names-the-fields-it-requires.md — read it whole first.

THE PROBLEM, in one sentence: twelve law clauses say a payload "matches contracts/<agent>.py
exactly", which makes the file both the claim and the oracle, so the clause cannot fail — measured:
S183 added fields to two scanner contract types and moved CONTRACT.version with every test green.

THE PATTERN ALREADY EXISTS. Read agents/portfolio_manager/laws/laws.md:172-180 (PM-TYP-03) and
tests/test_contract_values.py before designing anything. S184 made this decision; you are applying
it to the other twelve. DO NOT re-do PM.

MUST RULE — before you open an editor:
  1. Read every agent laws.md + test-plan.md in the spec's element->law map, whole file.
  2. Read docs/laws/conventions.md (section 3: gray/green, structural, charter rows) and
     docs/laws/drift-register.md (DRIFT-046, DRIFT-047).
  3. Fill the Law reading record at the bottom of the spec BEFORE your first code change.
  4. If a law contradicts the spec, STOP and report. The law is more likely right.

LAW-CYCLE ANSWER (already decided, do not re-derive): NO contracts/ change, NO new guarantee — but
YES it is a full law cycle per agent: clause rewrite, laws.md version bump + Changelog line,
test-plan row updated, rollups recomputed BY THE GATE in docs/laws/ledger.md AND docs/laws/INDEX.md.

ORDER OF WORK:
  1. Classify all 15 clauses (12 file-as-oracle + 3 "serialisation matches the contract") in the
     spec's own table: rewrite / keep / already fine, with the reason. This is a deliverable.
  2. Record the design decisions in docs/design-log.md (next free DL number; DL-166 is taken).
  3. Failing test first, watched red, output pasted.
  4. Then implement, agent by agent.

DO NOT:
  - DO NOT change ANY file under contracts/. Zero. If a clause cannot be satisfied by the current
    type, that is a drift-register row plus a report — DRIFT-046 is exactly that shape.
  - DO NOT touch agents/provider/laws/laws.md (LOCKED v1, and it has no clause in this family).
  - DO NOT edit docs/laws/_TEMPLATE.md.
  - DO NOT delete a guarantee. Nothing the old clause asserted may stop being asserted: it moves to
    a named field, a new clause, or a drift row. Narrowing is the goal; silence is not.
  - DO NOT keep a green by arguing the existing round-trip test covers the new wording, unless you
    can name the assertion in it that fails when a required field is deleted. Four clauses are green
    today on *_is_deserializable tests; expect demotions and report them as results.
  - DO NOT build images or deploy. No agent behaviour changes.

THE PROOF THAT MATTERS (success factor, not optional): for at least THREE agents spanning different
payload shapes, delete a required field from the contract type, watch the new test go RED, restore
the field, and paste each red output. The old clauses were green precisely because nothing could
make them red; if you cannot make the new ones red, the sprint achieved nothing.

TRAPS:
  - A test that derives its field list from the type is the same tautology one layer down. Write the
    field names out literally in the test.
  - A parameterised test can leave eleven clauses uncited under one docstring. The S204 gate checks
    clause citation — read what it tells you rather than adding IDs until it goes quiet.
  - make ci | tail reports tail's exit code. Redirect to a FILE and read the file.
  - make gate-ran resolves the SHA from the working directory and ignores SHA=. Run it from THIS
    worktree and check the printed SHA against git rev-parse HEAD.

HANDBACK: fill Law reading record, Test plan results, Closeout — evidence (real pasted output),
Return notes, and set Status: BUILT. A placeholder left intact means the handback is returned, not
repaired. State anything unmet plainly as "verified failing" or "not done" — never write a Result
for work you have not done.
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

## Clause classification — fill BEFORE editing any law

| Clause | File:line | Shape (a) file-as-oracle / (b) serialisation / (c) already fine | Current row | Call + reason |
| --- | --- | --- | --- | --- |
| `ANLZ-TYP-01` | `agents/analyst/laws/laws.md:154` | (a) file-as-oracle | 🟩 round-trip | Rewrite to name `RecommendationSet`, `Recommendation`, `StopTargetEvidence`, and `Rejection` fields; replace round-trip row with literal field guard. |
| `CUR-TYP-01` | `agents/curator/laws/laws.md:112` | (a) file-as-oracle | ⬜ | Rewrite to name dataset, split, predictor, and promotion-result fields; add literal field guard. |
| `DLIB-TYP-01` | `agents/deliberator/laws/laws.md:102` | (a) file-as-oracle | ⬜ `_tbd_` | Rewrite to name proposition, turn, turn request/reply, and verdict request/reply fields; add literal field guard. |
| `EXEC-TYP-03` | `agents/execution/laws/laws.md:200` | (a) file-as-oracle | 🟩 round-trip | Rewrite to name current execution result, fill, reconcile, stage-status, promotion-result, and version fields; file drift for unenforced version-move semantics and output-law mismatches. |
| `FORE-TYP-01` | `agents/forecaster/laws/laws.md:103` | (a) file-as-oracle | ⬜ | Rewrite to name `ShadowPrediction` and `Scorecard` fields; add literal field guard. |
| `FORE-TYP-03` | `agents/forecaster/laws/laws.md:106` | (b) serialisation shape | | Keep: it names a concrete `graph_store.forecasts` JSON shape that can be falsified by graph/serialization round-trip tests. |
| `MON-TYP-01` | `agents/monitor/laws/laws.md:110` | (a) file-as-oracle | ⬜ | Rewrite to name `CloseDecisionSet` and `CloseDecision` fields; align the cited output clause to the same concrete payload. |
| `MON-TYP-02` | `agents/monitor/laws/laws.md:112` | (b) serialisation shape | | Keep: it names a concrete graph `positions` node shape that can be falsified by graph/serialization tests. |
| `MST-TYP-01` | `agents/master/laws/laws.md:105` | (a) file-as-oracle | ⬜ `_tbd_` | Rewrite the contract-file sentence to name `EHLOMessage`, `ACTIVATEMessage`, and `DRAINMessage` fields; preserve `_Frozen` and `AgentState`/`StrEnum` checks. |
| `OPR-TYP-01` | `agents/operator/laws/laws.md:110` | (a) file-as-oracle | ⬜ | Rewrite to name `CommandResult`, `TypedIntent`, and `HumanCommand` fields; add literal field guard. |
| `RPT-TYP-01` | `agents/reporter/laws/laws.md:92` | (a) file-as-oracle | 🟩 round-trip | Rewrite to name `RunSnapshot` and `TradeNarrative` fields; replace round-trip row with literal field guard. |
| `RPT-TYP-03` | `agents/reporter/laws/laws.md:95` | (b) serialisation shape | | Keep: it names the claim-check JSON shape rather than a contract file as its own oracle. |
| `RES-TYP-01` | `agents/researcher/laws/laws.md:95` | (a) file-as-oracle | ⬜ | Rewrite to name proposal, proposed-change, and backtest-evidence fields; add literal field guard. |
| `SCAN-TYP-01` | `agents/scanner/laws/laws.md:140` | (a) file-as-oracle | 🟩 round-trip | `DRIFT-047`: rewrite to name `CandidateSet`, `Candidate`, `FilterTrace`, `FilterVerdict`, and version fields; replace round-trip row with literal field guard. |
| `SUP-TYP-01` | `agents/supervisor/laws/laws.md:99` | (a) file-as-oracle | ⬜ | Rewrite to name dispatch, report, accepted `contracts.operator.TypedIntent`, and flag-request fields; add literal field guard. |

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| PM precedent | `agents/portfolio_manager/laws/laws.md`, `agents/portfolio_manager/laws/test-plan.md` | `PM-TYP-03` | Yes: use PM's direct field-list pattern and do not touch PM. |
| Analyst | `agents/analyst/laws/laws.md`, `agents/analyst/laws/test-plan.md` | `ANLZ-TYP-01`, cited output clauses | Yes: its green row must move from generic round-trip proof to a required-field proof. |
| Curator | `agents/curator/laws/laws.md`, `agents/curator/laws/test-plan.md` | `CUR-TYP-01`, cited archive/promotion clauses | Yes: the row can become green if the clause names current manifest fields directly. |
| Deliberator | `agents/deliberator/laws/laws.md`, `agents/deliberator/laws/test-plan.md` | `DLIB-TYP-01`, cited debate/verdict clauses | Yes: the `_tbd_` row needs a shared required-field test with its own docstring citation. |
| Execution | `agents/execution/laws/laws.md`, `agents/execution/laws/test-plan.md` | `EXEC-TYP-03`, cited output/stage clauses | Yes: current contract-visible fields can be named, but output-law mismatches and version-move enforcement require drift rows. |
| Forecaster | `agents/forecaster/laws/laws.md`, `agents/forecaster/laws/test-plan.md` | `FORE-TYP-01`, `FORE-TYP-03` | Yes: rewrite only `FORE-TYP-01`; keep `FORE-TYP-03` as a falsifiable serialized graph shape. |
| Monitor | `agents/monitor/laws/laws.md`, `agents/monitor/laws/test-plan.md` | `MON-TYP-01`, `MON-TYP-02`, `MON-OUT-02` | Yes: rewrite `MON-TYP-01`; keep `MON-TYP-02`; align `MON-OUT-02` with the contract-visible close-decision fields it requires. |
| Master | `agents/master/laws/laws.md`, `agents/master/laws/test-plan.md` | `MST-TYP-01` | Yes: only the contract-file sentence changes; `_Frozen` and `AgentState` as `StrEnum` remain asserted and tested. |
| Operator | `agents/operator/laws/laws.md`, `agents/operator/laws/test-plan.md` | `OPR-TYP-01`, cited command clauses | Yes: the row can become green through a literal field test rather than a placeholder. |
| Reporter | `agents/reporter/laws/laws.md`, `agents/reporter/laws/test-plan.md` | `RPT-TYP-01`, `RPT-TYP-03`, cited output clauses | Yes: rewrite `RPT-TYP-01`; keep `RPT-TYP-03` as a claim-check JSON shape. |
| Researcher | `agents/researcher/laws/laws.md`, `agents/researcher/laws/test-plan.md` | `RES-TYP-01`, cited output clauses | Yes: the row can become green through proposal/change/backtest field assertions. |
| Scanner | `agents/scanner/laws/laws.md`, `agents/scanner/laws/test-plan.md` | `SCAN-TYP-01`, `DRIFT-047` | Yes: the rewritten clause must name `FilterVerdict` and prove `skipped_filters`, closing the measured drift. |
| Supervisor | `agents/supervisor/laws/laws.md`, `agents/supervisor/laws/test-plan.md` | `SUP-TYP-01`, cited dispatch/report/flag clauses | Yes: accepted typed intents come from `contracts.operator.TypedIntent`, so the clause must name that source explicitly. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(the spec says
No/No but Yes to twelve per-agent cycles — confirm after reading, and say if you disagree)*

Confirmed: no final `contracts/` changes and no new agent guarantee. This sprint narrows existing
file-as-oracle wording into falsifiable field-name wording while preserving guarantees through named
fields or drift rows.

**Contradictions found between a law and this spec:**

No direct contradiction. Execution law reading plus contract inspection exposed stale output field
names in `EXEC-OUT-01`, `EXEC-OUT-02`, `EXEC-OUT-04`, and `EXEC-OUT-05`; S205 recorded that as
DRIFT-061 instead of editing contracts.

**Laws found silent where a decision was needed:**

Execution and Scanner mention `CONTRACT.version`, but the law/gate set does not require a version
bump when contract shape changes. S205 recorded the missing version-move enforcement as DRIFT-060
and only proves the current version identity and required fields.

**Clauses that were ⬜ and are now proven:** *(IDs, and the rollup the gate computed)*

`CUR-TYP-01` (22/47 → 23/47), `DLIB-TYP-01` (19/55 → 20/55), `FORE-TYP-01`
(16/45 → 17/45), `MON-TYP-01` (20/46 → 21/46), `MST-TYP-01` (15/44 → 16/44),
`OPR-TYP-01` (15/50 → 16/50), `RES-TYP-01` (19/43 → 20/43), and `SUP-TYP-01`
(21/48 → 22/48). Computed by `uv run python scripts\check_law_coverage.py` after the row updates.

**Clauses that were 🟩 and are now ⬜:** *(IDs, and why the old test does not prove the new clause)*

None. `ANLZ-TYP-01`, `EXEC-TYP-03`, `RPT-TYP-01`, and `SCAN-TYP-01` stayed green because their rows
now cite literal required-field tests; the older round-trip tests remain supplemental rather than
being the only proof.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_analyst_payload_fields_required_by_law` | `tests/test_contract_required_payload_fields.py` | PASS | `ANLZ-TYP-01` |
| A2 | `test_curator_payload_fields_required_by_law` | `tests/test_contract_required_payload_fields.py` | PASS | `CUR-TYP-01` |
| A3 | `test_deliberator_bus_payload_fields_required_by_law` | `tests/test_contract_required_payload_fields.py` | PASS | `DLIB-TYP-01` |
| A4 | `test_execution_payload_fields_required_by_law` | `tests/test_contract_required_payload_fields.py` | PASS | `EXEC-TYP-03` |
| A5 | `test_forecaster_payload_fields_required_by_law` | `tests/test_contract_required_payload_fields.py` | PASS | `FORE-TYP-01` |
| A6 | `test_monitor_payload_fields_required_by_law` | `tests/test_contract_required_payload_fields.py` | PASS | `MON-TYP-01` |
| A7 | `test_master_payload_fields_required_by_law` | `tests/test_contract_required_fields.py` | PASS | `MST-TYP-01` |
| A8 | `test_operator_payload_fields_required_by_law` | `tests/test_contract_required_fields.py` | PASS | `OPR-TYP-01` |
| A9 | `test_reporter_payload_fields_required_by_law` | `tests/test_contract_required_fields.py` | PASS | `RPT-TYP-01` |
| A10 | `test_researcher_payload_fields_required_by_law` | `tests/test_contract_required_fields.py` | PASS | `RES-TYP-01` |
| A11 | `test_scanner_payload_fields_required_by_law` | `tests/test_contract_required_fields.py` | PASS | `SCAN-TYP-01` |
| A12 | `test_supervisor_payload_fields_required_by_law` | `tests/test_contract_required_fields.py` | PASS | `SUP-TYP-01` |

**Tests added beyond the plan:**

None.

---

## Closeout — evidence

**Status:** BUILDING — remote gate and merge still pending.

**Tree the proofs ran in (and `.env` present?):**

`C:/Users/yury_/Downloads/project/trading-agents`, branch
`sprint-205-a-type-clause-names-the-fields-it-requires`; pre-commit HEAD
`6e046e1123842b6ab678937308a0e309e8c1f2c6`; `.env` present: `True`. No live data or secrets were
needed or read for S205.

**Result:** *(what is now true, in the artefact's own words — not the intent restated)*

The twelve file-as-oracle `TYP` clauses now name the payload fields they require. The three
serialization-shape clauses (`FORE-TYP-03`, `MON-TYP-02`, `RPT-TYP-03`) stayed in their existing
family. `DRIFT-047` is corrected; DRIFT-060 and DRIFT-061 record the two scoped findings S205 did
not build.

**Files changed:**

Agent law books and test plans for Analyst, Curator, Deliberator, Execution, Forecaster, Master,
Monitor, Operator, Reporter, Researcher, Scanner, and Supervisor; `docs/design-log.md`;
`docs/laws/drift-register.md`; `docs/laws/ledger.md`; `docs/laws/INDEX.md`;
`docs/sprints/sprint-205-a-type-clause-names-the-fields-it-requires.md`;
`tests/test_contract_required_fields.py`; `tests/test_contract_required_payload_fields.py`;
`pyproject.toml`; `uv.lock`.

**Design decisions:** recorded as `DL-168`

**Proof — the red run first:**

```text
Command:
uv run pytest tests\test_contract_required_fields.py::test_scanner_payload_fields_required_by_law --no-cov

Result:
collected 1 item

tests\test_contract_required_fields.py F                                 [100%]

FAILED tests/test_contract_required_fields.py::test_scanner_payload_fields_required_by_law
E   AssertionError: assert ['skipped_filters'] == []
1 failed in 1.29s
```

**Proof — the field-deletion guards (≥ 3 agents):**

```text
Guard 1 — Scanner / FilterVerdict.skipped_filters:
Output pasted in "Proof — the red run first" above.

Guard 2 — Master / EHLOMessage.capability_declaration:
Command:
uv run pytest tests\test_contract_required_fields.py::test_master_payload_fields_required_by_law --no-cov

Result:
collected 1 item

tests\test_contract_required_fields.py F                                 [100%]

FAILED tests/test_contract_required_fields.py::test_master_payload_fields_required_by_law
E   AssertionError: assert ['capability_declaration'] == []
1 failed in 1.23s

Guard 3 — Researcher / ParameterChangeProposal.backtest:
Command:
uv run pytest tests\test_contract_required_fields.py::test_researcher_payload_fields_required_by_law --no-cov

Result:
collected 1 item

tests\test_contract_required_fields.py F                                 [100%]

FAILED tests/test_contract_required_fields.py::test_researcher_payload_fields_required_by_law
E   AssertionError: assert ['backtest'] == []
1 failed in 1.22s
```

**Proof — the green run:**

```text
uv run pytest tests\test_contract_required_fields.py tests\test_contract_required_payload_fields.py --no-cov
collected 12 items
tests\test_contract_required_fields.py ......                            [ 50%]
tests\test_contract_required_payload_fields.py ......                    [100%]
12 passed in 1.34s

uv run python scripts\check_law_coverage.py
exit code 0, no output
```

**`git diff --stat contracts/`:** *(must be empty)*

`git diff --stat -- contracts` exited 0 with no output.

**Rollups, as computed by the gate:** *(before → after, in `ledger.md` and `docs/laws/INDEX.md`)*

Analyst 25/48 → 25/48; Curator 22/47 → 23/47; Deliberator 19/55 → 20/55; Execution 35/61 → 35/61;
Forecaster 16/45 → 17/45; Master 15/44 → 16/44; Monitor 20/46 → 21/46; Operator 15/50 → 16/50;
Reporter 20/39 → 20/39; Researcher 19/43 → 20/43; Scanner 18/41 → 18/41; Supervisor 21/48 → 22/48.

**Module line counts:**

`tests/test_contract_required_fields.py`: 114 lines.
`tests/test_contract_required_payload_fields.py`: 116 lines.

**`make ci`:** redirected to `%TEMP%\s205-make-ci.txt`. Exit code 0. 2756 passed, 4 skipped,
coverage 100.00%.

```text
TOTAL                                                     16467      0   3500      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
================= 2756 passed, 4 skipped in 267.92s (0:04:27) =================
uv run pip-audit
No known vulnerabilities found
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 2 new file(s)
```

**`make gate-ran`:** run from *(worktree path)* at *(full 40-char SHA)*:

```text
Pending branch push and remote checks.
```

**Not met / verified failing:**

Pending remote branch gate, merge, and post-merge CodeQL.

---

## Return notes

- Scope held: no final `contracts/` edits; temporary contract edits were used only for the required
  red guards and were restored before green proof.
- I did not disagree with the spec after reading the laws. I did separate the three serialization
  clauses from the twelve file-as-oracle clauses, as the spec asked.
- The first full `make ci` attempt failed on module size after the single guard file counted as 215
  lines; the guard family was split into two files and rechecked with `scripts/check_module_size.py`.
- Next sprint should know that `CONTRACT.version` movement is not enforced (DRIFT-060), and execution
  output clauses name several fields the current execution contract does not carry (DRIFT-061).
