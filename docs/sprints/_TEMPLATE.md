<!-- Agent: planning | Role: sprint handover template -->
# Sprint NN — <one falsifiable sentence in the present tense>

<!--
HOW TO USE THIS FILE
  Copy to `docs/sprints/sprint-NN-<slug>.md`, add the INDEX.md row, then fill top-down.
  The title is a CLAIM the sprint makes true ("a gate that did not run says so"), never a task
  name ("add attestation"). If you cannot write the claim, the sprint is not yet understood.

  Base lineage: S164 (law rigour, handback contract, law reading record) merged with S177–S184
  (measured evidence, design decisions, blast radius, traps, Codex handover block). Two sections
  exist because a real sprint was damaged by their absence — they are marked 🩹.

  DELETE every HTML comment before handing over. Leave no placeholder unfilled: a handback with a
  placeholder intact is returned, not repaired (DL-48).
-->

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-NN-<slug>` <!-- created BEFORE any code, never main -->
**Status:** SPEC
<!-- 🩹 Machine-checkable, exactly one of: SPEC | BUILT | MERGED. Work-queue item 22 exists because
     closeouts used three different wordings and nothing could answer "is this spec built?".
     One line, one vocabulary. Update it at handback and again at merge. -->
**Version:** *next available <PATCH|MINOR> at merge*
<!-- 🩹 DO NOT PIN A NUMBER. Three specs were renumbered in one day, and S183 shipped a bump that
     would have LOWERED main's version. State the KIND and let the merge pick the digits.
     feat (new capability/agent/endpoint) → MINOR, the two middle digits. fix (bug, CVE, refactor)
     → PATCH, the last two. Docs-only or read-only tooling → NO BUMP AT ALL. -->
**Effort:** <S | M | L>
**Decisions:** <ADR-00NN what it settles> · <DL-NNN the open thread> · <DRIFT-0NN the row this closes>

> **Why this bump kind.** <One sentence. "No new capability — the clause already promises X and the
> code cannot deliver it" is a PATCH. "The agent gains a dimension it did not have" is a MINOR.>

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`<IDN>`**, **`<IDM>`**, **`<OBS>`**, **`<NEV>`**. <!-- name the real ones -->

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec —
   S183's spec told Codex to register a `tunable()` the locked analyst law forbids on purpose.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

- **No** → say so in the Law reading record and continue.
- **Yes** → this sprint owes a **law cycle in the same unit of work**: a new clause in the agent's
  `laws.md` (bump its version, add a Changelog line), a `test-plan.md` row per clause, the clause ID
  cited in the test docstring, the rollup updated in **both** `docs/laws/ledger.md` **and**
  `docs/laws/INDEX.md`, and a `drift-register.md` row for anything the change slipped under.

🪤 **This section exists because S183 skipped it and nobody noticed until merge.** S183 added
`skipped_filters` to two contract types and shipped a guarantee the scanner law did not make — under
a LOCKED law book — while S184, one day earlier, did the full cycle for the identical shape. **The
omission was the spec's, not the builder's.** A spec that does not ask for the law cycle will not
get one.
🪤 **The rollup is derived, not declared.** `make ci` recomputes it: two new clauses proven by three
test rows is **+2**, not +3. Let the gate tell you the number.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `<path/to/file.py>` | `agents/<name>/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `<CLAUSE-ID>` <what it requires> |
| `<contracts/x.py>` | same, plus the ADR that settles it | `<CLAUSE-ID>`; ADR-00NN §N |

⚠️ **<The one invariant this sprint must not break.>** <If your change would do X, stop and report.>

---

## Goal

<One paragraph. The claim in the title, restated as the postcondition that will be true at merge.>

## Why (context)

<Why now, and what it costs to keep not doing it. Cite the run, the flag, the veto, the incident.>

### Measured, <YYYY-MM-DD> — read these before designing

<!-- 🩹 Mark every number MEASURED or ASSUMED. Sprint residue has been traced to unmeasured claims
     written in a confident voice. A named assumption is a decision; a discovered one is a miss. -->

| Claim | Value | How it was measured |
| --- | --- | --- |
| <what> | <number> | *[measured <date>]* <the query, script, or run id> |
| <what> | <number> | *[ASSUMED — not measured]* <why it was not, and what would settle it> |

---

## Scope — and what is deliberately NOT here

1. **<Item 1 — the failing test first.>** <What must be true, asserted on the guarantee not a proxy.>
2. **<Item 2.>**
3. **<Item 3.>**

### Out of scope (do NOT build this sprint)

- **<Thing that looks adjacent and is not.>** <Why it is separate.>
- **No `laws.md` edit** *unless the law-cycle question answered Yes* — then the amendment is in scope
  and named above.
- **No ADR reversal.** An ADR is reversed by a new ADR, never by a sprint.

### The road not taken (LAW-06)

<!-- Capture the ruled-out options WITH the reason. A decision discussed but unrecorded is treated
     as not-yet-made, and gets re-litigated three sprints later. -->

- **<Rejected option>.** Rejected: <why — the constraint that kills it>.
- **<Rejected option>.** Rejected: <why>.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **<Decision 1>** — <the fork, and what hangs on it>.
2. **<Decision 2>** — <…>.

🪤 **Take the next free DL number, then re-check it at merge.** The log has historic duplicates (two
`DL-110`, two `DL-111`) and entries are prepended at the top *and* appended at the bottom. **A branch
cut before another DL lands will collide even when the number was free at branch time** — S183 chose
`DL-121` correctly and still collided, because `main` gained its own `DL-121` meanwhile. Check again
when you merge.

---

## Blast radius — measured <YYYY-MM-DD>

| What | Detail |
| --- | --- |
| Files changed | <list, with current line counts> |
| Agents affected | <names — and confirm none imports another> |
| Contract change? | <yes/no — if yes, the law cycle above is mandatory> |
| Graph vocabulary change? | <new label or property? → the deploy is a full `up`, not a retag> |
| New env keys / tunables | <names — these make the deploy a full `up` too> |
| Deploy implication | <image-only retag | full `up`> |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Plant the failing test first** and watch it fail. Paste the red output.
4. **Implement.**
5. **Law cycle** if owed — clause, test-plan row, docstring citation, rollups, drift row.
6. **Prove the guards can fail (DL-70)** — break the implementation, watch each guard go red, restore.
7. **`make ci` green** — all 12 steps, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 <the headline guarantee> | <the fixture state> | <the postcondition, in the artefact's own words> |
| A2 | <…> | <…> | <…> |
| A3 | 🪤 <the negative — the thing that must still be refused> | <…> | <…> |

---

## Success factors

<!-- Each one verifiable by someone who was not in the conversation. "Works correctly" is not one. -->

- [ ] <The postcondition from Goal, stated as an observable>.
- [ ] <No change to X, or the change is named and justified>.
- [ ] Design decisions recorded with rejected alternatives.
- [ ] Law cycle done, or the law-cycle question answered No with a reason.
- [ ] Every new guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **<Trap 1 — the thing that looks like success and is not.>**
🪤 **<Trap 2 — the measurement that correlates with the cause without being it.>** Read the reason
field before the metrics.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `<file>` **<n>**, `<file>` **<n>**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. 🪤 A **mode selector** (which formula
  runs) is *not* a tunable (a value within one) — check the agent's PARAM table before registering.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — `make ci | tail` reports *`tail`'s* exit code. Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**, so any proof needing live data
  is vacuous there. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** — it resolves the SHA
   from the working directory and ignores a `SHA=` argument. **Check the printed SHA against
   `git rev-parse HEAD`.**
2. Merge to `main` locally and push. 🪤 Check you are not on the branch already — a `git merge` from
   the branch's own worktree says *"Already up to date"* and merges nothing.
3. **Post-merge CodeQL.** `codeql.yml` runs **only on `main`**, so a green branch gate is not proof of
   a CodeQL-clean merge. Check after merging.
4. **Deploy** per the Blast radius row: image-only retag, or a full `up` if the sprint adds a graph
   label/property, an env key, or a tunable.

---

## Handover — paste this to Codex

```text
<!-- Self-contained. Assume the reader has none of this conversation. Repeat the MUST RULE, the
     branch name, the law-cycle answer, the failing-test-first order, and every DO NOT.
     Name the traps explicitly — a trap you know about and do not write down will be hit. -->
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
| <element> | <files> | <clause IDs> | <Yes/No + what changed> |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** <Yes/No + what it owed and what was done>

**Contradictions found between a law and this spec:** <none | what, and what you did>

**Laws found silent where a decision was needed:** <none | what, and the drift row filed>

**Clauses that were ⬜ and are now proven:** <IDs, and the rollup in ledger.md + INDEX.md>

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | <name> | <file> | PASS/FAIL | <clause IDs> |

**Tests added beyond the plan:** <none | what and why>

---

## Closeout — evidence

**Status:** <BUILT | MERGED>

**Tree the proofs ran in (and `.env` present?):** <path, branch, .env yes/no>

**Result:** <what is now true, in the artefact's own words — not the intent restated>

**Files changed:** <list>

**Design decisions:** recorded as [`DL-NNN`](../design-log.md) — <one line + where the rejected
alternatives are>

**Proof — the red run first:**

```text
<the failing test output, before the implementation>
```

**Proof — the green run:**

```text
<the passing output>
```

**Guards planted:** <per guard: what was planted, that it failed, that it was restored>

**Module line counts:** <file **n**, file **n**>

**`make ci`:** redirected to `<path>`. Exit code <n>. `<N passed, M skipped>`, coverage `<100.00 %>`.
pip-audit `<result>`. detect-secrets `<result>`.

**`make gate-ran`:** run from `<worktree path>` at `<full 40-char SHA>`:

```text
GATE PROVEN for <sha>:
  Security Findings: success
  CI: success
```

**Not met / verified failing:** <plainly, or "none">

---

## Return notes

- <Scope held / where it moved and why.>
- <What you disagreed with in the spec after reading the laws.>
- <What the next sprint should know that is not obvious from the diff.>
