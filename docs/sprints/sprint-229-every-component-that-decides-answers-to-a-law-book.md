<!-- Agent: planning | Role: sprint handover -->
# Sprint 229 — every component that decides answers to a law book the gate reads

**Phase:** Law cycle (the S70/S71 backfill, for the two components they did not cover)
**Branch:** `sprint-229-every-component-that-decides-answers-to-a-law-book`
**Status:** BUILT
**Version:** *next available PATCH at merge*
**Effort:** M
**Decisions:** closes [DRIFT-068](../laws/drift-register.md) (the dispatcher has no law home) · work-queue item **86** · [DL-221](../design-log.md) (where non-agent law books live, and how the gate finds them) · ranked by the operator **ahead of** [S228](sprint-228-the-operator-sees-whether-the-book-beats-the-index.md) (*"a quick sprint to cover this gap before we go further"*, 2026-09-25)

> **Why this bump kind.** No behaviour changes. The gate learns to read two law books it cannot see
> today, and existing tests gain clause citations. That closes a coverage hole, which makes it a PATCH.

**Builder:** Codex. Every behaviour is pinned by a row in the test plan.
**If a number you measure differs from one written here, stop and report. Do not adjust and continue.**

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

**This sprint authors two new books**, so the usual "read-only" rule applies to every *existing* book
and to `docs/laws/_TEMPLATE.md`, which is **LOCKED v1 (S69)**: copy it, never edit it. Binding:
[`docs/laws/conventions.md`](../laws/conventions.md) (clause IDs append-only, §2; green means a test
cites the ID, §3; clause-summary fidelity, §7a), the master book's **`MST-OUT-04`** / **`MST-FAIL-05`**
(what a failing fleet check means, which the dispatcher consumes), the execution book's
**`EXEC-NEV-07`** (S227's degraded-run clause, the dispatcher's counterpart), and the reporter's
**`RPT-SEC-02`** (the surfaces display P&L).

### The rule

1. **Before writing anything**, read `docs/laws/_TEMPLATE.md`, `conventions.md`, `drift-register.md`,
   `ledger.md`, `INDEX.md`, and one finished book end to end — `agents/master/laws/laws.md` +
   `test-plan.md` — as the model.
2. Read the S70 precedent: [sprint-70](sprint-70-per-agent-law-backfill.md) (author → reconcile →
   citation → green → LOCK v1, four books in one sprint).
3. Read `docs/laws/flow.md`'s daily path: it records the dispatcher's place in the choreography, and
   the new book must not contradict it.
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** before the first file you create.
6. **If an existing law contradicts what you find in the code, STOP and report.**
7. **If the code does something no clause should promise** (or fails to do something a clause should),
   that is a **Divergence register** entry in the new book plus a `drift-register.md` row. **Never fix
   the code in this sprint.**
8. Every test you cite **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**No `contracts/` change, and no new behaviour.** It *does* declare guarantees the dispatcher and the
surfaces already keep but no book states. That is the law cycle itself, in full: new `laws.md`, a
`test-plan.md` row per clause, clause IDs in test docstrings, rollups in **both** `docs/laws/ledger.md`
and `docs/laws/INDEX.md`, and drift rows for every divergence. 🪤 **The rollup is derived, not
declared:** `make ci` recomputes it. Let the gate tell you the green count.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| new `orchestration/laws/dispatcher/laws.md` + `test-plan.md` | `_TEMPLATE.md`, `conventions.md`, master's book, `flow.md` | the dispatcher consumes `MST-OUT-04`/`MST-FAIL-05` and pairs with `EXEC-NEV-07` |
| new `surfaces/laws/laws.md` + `test-plan.md` | `_TEMPLATE.md`, `conventions.md`, reporter's `RPT-SEC-02`, DL-47 in `design-log.md` | the dashboard and chat are the operator's product surface (DL-47 reqs 5, 13, 14, 15) |
| `scripts/law_coverage_docs.py` (176) | `conventions.md` §3 | book discovery is `agents/*/laws/laws.md` only (line 26) |
| `scripts/param_law_sync_sources.py` (88) | `conventions.md`; S187's PARAM rule | settings and laws are both located under `agents/<name>/` (lines 34, 48, 52) |
| existing tests under `orchestration/tests/` and `surfaces/tests/` | conventions §3 | **docstring edits only** — a citation, never a behaviour change |

⚠️ **One invariant: no behaviour changes.** No `.py` file outside `scripts/law_coverage_docs.py`,
`scripts/param_law_sync_sources.py` and test docstrings may change. If a clause can only turn green by
changing product code, it stays ⬜ and gets a Divergence entry.

---

## Goal

The dispatcher and the operator surfaces each have a LOCKED v1 law book, built from the template and
reconciled against the code. Every clause has a test-plan row, every green row names a test whose
docstring cites the clause, and `make ci` reads both books. It fails on an orphan row, a missing row,
an uncited green, or a PARAM row that disagrees with the component's settings, exactly as it does for
the 14 agents. DRIFT-068 is closed by the dispatcher book.

## Why (context)

**Measured 2026-09-25:** all **14** agents have LOCKED law books, and **two components with decision
power have none.**

- **The dispatcher** decides whether a trading run happens at all: calendar, action window, the
  fleet-check gate, holds, human overrides and, since S227, whether a run places buys. DRIFT-068 has
  recorded the gap since S218, and explicitly deferred it to *"a later sprint"*. The DL-218 near-miss
  (an image that would have placed no run at all) happened in exactly this component.
- **The surfaces** (dashboard, chat, CLI) are read-mostly, but they carry operator **write paths**:
  hold answers, flag approve/dismiss, resume placement and the chat's command tool, some with broker
  consequences. E19.2 will open Telegram two-way commands onto the same intent layer. A law book
  should exist before that channel does, not after.

The etalon's claim is that every component answers to a law book the gate enforces (the
bundle-genesis method depends on it). Two exceptions make that claim false.

### Measured, 2026-09-25 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Agents with a LOCKED book | **14 of 14** (analyst, curator, deliberator, execution, forecaster, master, monitor, operator, portfolio_manager, provider, reporter, researcher, scanner, supervisor) | *[measured 2026-09-25]* `agents/*/laws/laws.md` headers |
| Law homes outside `agents/` | **none** — no `orchestration/laws`, `surfaces/laws`, `kernel/laws` (`ops/laws` holds the process laws LAW-01…06, not component books) | *[measured 2026-09-25]* `ls` |
| Coverage gate's book discovery | `sorted((root / "agents").glob("*/laws/laws.md"))`, `scripts/law_coverage_docs.py:26` | *[measured 2026-09-25]* read |
| PARAM sync's source lookup | `agents/<name>/settings*.py` and `agents/<name>/laws/laws.md`, `scripts/param_law_sync_sources.py:34,48,52` | *[measured 2026-09-25]* read |
| Clause-ID regex | `\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+-\d{2}\b`, `law_coverage_docs.py:19` | *[measured 2026-09-25]* read |
| Proposed prefixes are free | `DSP-` and `SRF-`: **0** occurrences in `agents/`, `docs/`, `orchestration/`, `surfaces/` | *[measured 2026-09-25]* `grep -rhoE` |
| Dispatcher modules | `scheduled_dispatch.py` **179**, `scheduled_dispatch_human.py` **164**, `scheduled_dispatch_actions.py` **100**, `scheduled_dispatch_polling.py` **97**, `scheduled_dispatch_gate.py` **77**, `dispatcher.py` **118** (the served-path `run.trigger` dispatcher) | *[measured 2026-09-25]* `wc -l` |
| Dispatcher tests | **9** files under `orchestration/tests/` with `dispatch` in the name | *[measured 2026-09-25]* `ls \| grep -c` |
| Settings classes | dispatcher: `OrchestratorSettings` (`orchestration/settings.py:17`); surfaces: `DashboardSettings` (`surfaces/dashboard/settings.py:16`) | *[measured 2026-09-25]* grep |
| Surfaces write paths | `hold_answer_route.py`, `hold_answer_panel.py`, `cli_commands_extra.py`, `operator_tools.py` (`command_tool`), `mcp_tools.py`, `queries/proposals.py` | *[measured 2026-09-25]* grep for approve/resume/dismiss/hold_answer/command_tool. **Your reconciliation must confirm the full list** |
| Size-gated files you may touch | `law_coverage_docs.py` **176**, `param_law_sync_sources.py` **88**; `check_law_coverage.py` **228** and `param_law_sync.py` **197** are in `scripts/module_size_baseline.py` and **may not grow** | *[measured 2026-09-25]* `wc -l`; baseline line 23 |
| How many clauses each book will have | roughly 25–40 each | *[ASSUMED — not measured]* by analogy with S70's 39–49 per agent. The number is whatever the code actually guarantees; do not pad it to match |

---

## Scope — and what is deliberately NOT here

1. **The gate first, with a failing test.** Replace the single `agents/*` glob with a declared tuple
   of law roots in `law_coverage_docs.py`: `agents/*/laws`, `orchestration/laws/*`, `surfaces/laws`.
   The book name is the directory that owns it (`dispatcher`, `surfaces`). Plant a fixture book under
   `orchestration/laws/<x>/` with an uncited green row and watch the gate **pass** it (red test), then
   make the gate fail it. Same for `param_law_sync_sources.py`: a book declares which settings module
   it is checked against. Do it by a small mapping, not by guessing paths; `dispatcher` →
   `orchestration/settings.py`, `surfaces` → `surfaces/dashboard/settings.py`. Neither baselined file
   may grow; put new code in the two unbaselined modules, or split.
2. **The dispatcher book**, `orchestration/laws/dispatcher/laws.md` + `test-plan.md`, prefix **`DSP`**,
   every template section present. Seed clauses to **verify against the code** (each one either becomes
   a clause with a test row, or a Divergence entry; none is taken on trust):
   - one `RunRequest` per NYSE session, day-keyed, merge-deduplicated (idempotent re-fires);
   - placement only inside the action window (`_ACTION_START` 22:30 UTC, `scheduled_dispatch_actions.py:29`,
     and its end) and only on a session day (the calendar skip);
   - no `RunRequest` unless the latest fleet check passed within `preflight_max_age_minutes`, with S227's
     single degraded exception (every failing check pack-declared degradable);
   - a failing gate writes a hold, sends **one** notice, and honours the **first** human answer; the
     override is bounded;
   - never writes master-owned `FleetPreflight` facts (`scheduled_dispatch_gate.py` docstring);
   - never talks to the broker and never decides what to trade.
3. **The surfaces book**, `surfaces/laws/laws.md` + `test-plan.md`, prefix **`SRF`**. Seeds to verify:
   - read-only over the graph **except** the named operator-intent write paths, each audited;
   - an action with broker consequences needs an explicit confirmation step (DL-207's pending-confirm
     flag is the live precedent);
   - the run selector scopes every contextual panel (DL-47 req 5; DRIFT-022 is an open divergence);
   - one definition per operator-facing fact, shared with the kernel query that owns it (DL-207/208:
     `open_faults` ≡ `live_fault_incidents`);
   - every displayed time is Melbourne, 24-hour;
   - no internal project vocabulary on the operator surface (DL-47 req 14);
   - never shows an unwired control (DL-47);
   - chat tools are a bounded list, and errors reach the operator in plain words.
4. **Test citations.** For each clause an existing test proves, add the clause ID to that test's
   docstring and mark the row 🟩. A clause no test proves stays ⬜ with the reason. **Do not write new
   behaviour tests to turn rows green** unless the test is under 30 lines and needs no product change.
   Anything larger is a follow-up row in *Return notes*.
5. **Rollups and drift.** Rows in `docs/laws/ledger.md` and `docs/laws/INDEX.md` for both books (the
   gate derives the counts). DRIFT-068 → **CLOSED**, citing the `DSP` clauses. DRIFT-022 stays open
   and is cited by the `SRF` run-selector clause. Every new divergence gets a row.
6. **LOCK v1** both books in their Changelog once reconciled, as S70 did.
7. **DL-221** in `docs/design-log.md`: the law-root layout and the discovery rule, with the rejected
   alternatives (below).

### Out of scope (do NOT build this sprint)

- **Any product-code change**, including fixing a divergence you find. Record it; the fix is a
  separate, ranked item.
- **A kernel law book.** The kernel is plumbing governed by `dependencies.md` / `stack.md`. If you
  believe it needs one, say so in *Return notes*.
- **Editing `docs/laws/_TEMPLATE.md`**, or any existing agent book.
- **`orchestration/` beyond the dispatcher** (bindings, packs, batch trace, shadow book). The book
  covers run placement and the human-hold loop, nothing else. Name what you left out in the book's
  Identity section.
- **No ADR reversal.**

### The road not taken (LAW-06)

- **Put the books under `agents/dispatcher/laws/` and `agents/surfaces/laws/`** so the gate needs no
  change. Rejected: it creates two fake agents, and `import-linter`'s *agents are islands* contract and
  every agent-shaped tool would start treating them as agents.
- **One `orchestration/laws/laws.md` for all of orchestration.** Rejected: orchestration is many
  components. A book scoped to "everything in the folder" cannot say what it owns (template `IDN`).
- **Write the books but leave the gate agents-only for now.** Rejected: an ungated book is item 33's
  failure mode. Nothing turns red, so nobody reads it.
- **Let the builder fix divergences as they are found.** Rejected: it turns a documentation sprint
  into an unbounded behaviour change on the component that decides whether trading happens.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` as DL-221, with their rejected alternatives, BEFORE authoring
(LAW-06).**

1. **The law-root rule** — a declared tuple of roots, not a recursive search for any `laws.md`
   (`ops/laws/` and `docs/laws/` must stay out of it).
2. **How a non-agent book fills agent-shaped sections** (`CAP` capability declaration, bus `DEP`s) —
   the planner's recommendation: every section stays, and one that does not apply says so in one line
   with the reason. Never delete a section; the template is the schema.
3. **The dispatcher's two faces** — `dispatcher.py` (the served-path `run.trigger` loop) and the
   `scheduled_dispatch*` graph-pull placer. Decide whether one book covers both or `dispatcher.py` is
   named out of scope, and say why.

🪤 **Take DL-221 and re-check at merge.** S228 already holds DL-220.

---

## Blast radius — measured 2026-09-25

| What | Detail |
| --- | --- |
| Files changed | new: 4 law files; edited: `scripts/law_coverage_docs.py` (176), `scripts/param_law_sync_sources.py` (88), docstrings in existing `orchestration/tests/*` and `surfaces/tests/*`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md`, `docs/design-log.md`; new tests for the gate change |
| Agents affected | **none** |
| Contract change? | **no** |
| Graph vocabulary change? | **no** |
| New env keys / tunables | **none** — PARAM tables *describe* existing settings |
| Deploy implication | **none** — `scripts/`, `docs/` and test files ship in no image |

---

## Steps, in order

1. **Read the laws** (MUST RULE) and write the Law reading record.
2. **Record DL-221.**
3. **Gate first:** plant the fixture book, watch the gate pass an uncited green (paste it), then
   extend discovery and watch it fail.
4. **Author the dispatcher book** in ideal-design mode, then **reconcile** clause by clause against the
   code and tests. Every seed ends as a clause or a Divergence entry.
5. **Author the surfaces book** the same way.
6. **Cite**: docstring edits, test-plan rows, rollups, drift rows. LOCK v1.
7. **Prove the guards can fail (DL-70)**: delete one clause citation from a test docstring and watch
   `make ci` fail on that `DSP` row; change one `SRF` PARAM default in the book and watch the PARAM
   sync fail. Restore both.
8. **`make ci` green** — every step, **redirected to a file, never piped**.
9. **Fill the handback sections.**

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 the coverage gate reads a book outside `agents/` | fixture `orchestration/laws/fixture/` with a 🟩 row whose test does not cite the clause | the gate **fails** naming that row; before the change it passed (paste both) |
| A2 | an orphan row in a non-agent book fails | fixture row with no clause in `laws.md` | gate error names the orphan |
| A3 | a clause with no row in a non-agent book warns or fails as it does for agents | fixture clause without a row | same behaviour as `agents/*` books (read `_add_missing_row_warnings`) |
| A4 | 🪤 `ops/laws/` and `docs/laws/` are not books | the real tree | discovery returns exactly 14 agents + `dispatcher` + `surfaces` |
| A5 | PARAM sync reads a non-agent book against its mapped settings | fixture book PARAM row vs a fixture settings class, one value different | the sync fails naming the parameter |
| A6 | 🎯 the real dispatcher book is green-consistent | the real tree | `make ci` passes; `ledger.md` / `INDEX.md` rows match the derived counts |
| A7 | 🎯 the real surfaces book is green-consistent | the real tree | same |
| A8 | DRIFT-068 is closed by clauses, not by prose | `drift-register.md` | the row reads CLOSED and names the `DSP` clause IDs that state the placement gate |

---

## Success factors

- [ ] `orchestration/laws/dispatcher/laws.md` and `surfaces/laws/laws.md` exist, LOCKED v1, every
      template section present.
- [ ] Every clause has a test-plan row; every 🟩 row's test docstring cites its clause.
- [ ] `make ci` fails on an uncited green, an orphan row, or a PARAM mismatch **in either new book**
      (A1, A2, A5, and the two DL-70 plants).
- [ ] No product-code change: the diff outside `docs/`, the two law folders, the two `scripts/` modules
      and test **docstrings** is empty. State it with the `git diff --stat` you ran.
- [ ] DRIFT-068 closed; every new divergence has a drift row.
- [ ] DL-221 recorded with rejected alternatives.
- [ ] Every touched Python module < 200 lines; the two baselined files not grown.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **A clause copied from a docstring is not a law.** Author the intent, then check the code. A book
that restates the code has nothing to diverge from, and it will turn green without proving anything
(item 30's *"matches the contract file exactly"* failure).
🪤 **A test that exercises a path is not a test that proves a clause.** Cite a test only if it would go
red when the clause is broken. If you are unsure, plant the break and see.
🪤 **The seed list is the planner's reading, not a fact.** If the code does not do a seed, that is the
most valuable output of this sprint: a Divergence entry, not a quietly dropped seed.
🪤 **`check_law_coverage.py` is 228 lines and baselined.** One added line fails the size gate. Put the
change in `law_coverage_docs.py`.
🪤 **The rollup counts the gate derives are the truth.** If your hand count differs, the gate is
right.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`. The baseline can only shrink.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers.
- `make ci` **every step** green, **100.00 % coverage floor**, **redirected to a file, never piped**.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0** from the worktree whose `HEAD`
   is the proven commit; check the printed SHA against `git rev-parse HEAD`.
2. Merge to `main` locally and push. Not from the branch's own worktree.
3. **Post-merge CodeQL** on `main`.
4. **No deploy.** The functionality check is the gate itself on `main`: a planner-side plant (remove one
   `DSP` citation on a scratch branch) must turn `make ci` red. Record it in
   `docs/laws/functionality-checks.md`.
5. Then S228 builds, and its MUST RULE gains `surfaces/laws/laws.md`.

---

## Handover — paste this to Codex

```text
Sprint 229 — every component that decides answers to a law book the gate reads.
Spec: docs/sprints/sprint-229-every-component-that-decides-answers-to-a-law-book.md (read all of it).

Branch: sprint-229-every-component-that-decides-answers-to-a-law-book, in its own worktree. Never main.

What: two new LOCKED v1 law books, built from docs/laws/_TEMPLATE.md (copy it, NEVER edit it):
  orchestration/laws/dispatcher/{laws.md,test-plan.md}  prefix DSP
  surfaces/laws/{laws.md,test-plan.md}                  prefix SRF
and teach the gate to read them: scripts/law_coverage_docs.py (discovery, line 26) and
scripts/param_law_sync_sources.py (settings mapping: dispatcher -> orchestration/settings.py,
surfaces -> surfaces/dashboard/settings.py).

MUST RULE before anything: read _TEMPLATE.md, conventions.md, drift-register.md, ledger.md, INDEX.md,
agents/master/laws/{laws.md,test-plan.md} as the model, docs/sprints/sprint-70-per-agent-law-backfill.md
as the precedent, and docs/laws/flow.md. Fill the Law reading record first.

Order: DL-221 in docs/design-log.md -> gate change test-first (fixture book with an uncited green row:
paste the gate PASSING it, then FAILING it) -> author dispatcher book in ideal-design mode ->
reconcile every clause against code + tests -> same for surfaces -> cite clause IDs in existing test
docstrings, test-plan rows, ledger.md + INDEX.md rows, DRIFT-068 CLOSED -> LOCK v1 -> DL-70 plants
(remove one DSP citation; change one SRF PARAM value; watch make ci fail; restore) -> make ci
redirected to a file, exit 0, 100.00 %.

DO NOT:
- change any product code. Not even to fix a divergence you find: record it in the book's Divergence
  register and add a drift-register.md row. Only law_coverage_docs.py, param_law_sync_sources.py,
  test DOCSTRINGS, new gate tests, docs and the two law folders may change.
- grow scripts/check_law_coverage.py (228) or scripts/param_law_sync.py (197): both are baselined.
- make discovery recursive: ops/laws and docs/laws are not component books (test A4).
- put the books under agents/: the dispatcher and surfaces are not agents.
- delete a template section that does not apply; say "not applicable" and why, in one line.
- cite a test that would stay green if the clause broke.
- pad the clause count. Whatever the code actually guarantees is the right number.
- pin a version: PATCH, next available at merge, uv.lock staged with it.

Handback: Law reading record, Test plan results, Closeout (red then green gate output, DL-70 plants,
git diff --stat proving no product code changed, line counts, make ci file + exit code, make gate-ran
from the worktree at the full SHA), Return notes including every divergence found. Status: BUILT, and
this sprint's README.md row leads with BUILT in the same commit. Anything not met: "not done".
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**, including **every divergence found**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| New dispatcher law book | `docs/laws/_TEMPLATE.md`; `docs/laws/conventions.md`; `docs/laws/INDEX.md`; `docs/laws/ledger.md`; `docs/laws/drift-register.md`; `docs/laws/flow.md`; `agents/master/laws/laws.md`; `agents/master/laws/test-plan.md`; `agents/execution/laws/laws.md`; `docs/sprints/sprint-70-per-agent-law-backfill.md` | Template sections stay present; conventions §2/§3/§7a/§9; `MST-OUT-04`; `MST-FAIL-05`; `EXEC-NEV-07`; DRIFT-068/069; flow says dispatcher is outside the trading-spine agents and does not replace `supervisor` | Yes: one dispatcher book should cover only run placement and the human-hold loop, naming other orchestration code out of scope rather than pretending all `orchestration/` is one component. |
| New surfaces law book | `docs/laws/_TEMPLATE.md`; `docs/laws/conventions.md`; `docs/laws/INDEX.md`; `docs/laws/ledger.md`; `docs/laws/drift-register.md`; `docs/laws/flow.md`; `agents/reporter/laws/laws.md`; `agents/reporter/laws/test-plan.md`; `docs/design-log.md` DL-47/DL-207/DL-208/DL-220 | Template sections stay present; conventions §2/§3/§7a/§9; `RPT-SEC-02`; DL-47 reqs 5, 13, 14, 15; DL-207 confirmation/control truth; DL-208 one definition of open incidents | Yes: surface laws must separate read-only display from the named audited operator-intent write paths, and must cite DRIFT-022 as already corrected rather than reopen it. |
| Law coverage gate | `docs/laws/conventions.md`; `docs/laws/_TEMPLATE.md`; `docs/laws/INDEX.md`; `docs/sprints/sprint-70-per-agent-law-backfill.md` | Green iff a passing functional test docstring cites the clause; every clause has a row; orphan rows are invalid; component books must be deliberate roots, not any `laws.md` recursively | Yes: discovery should be a declared root list that includes `agents/*/laws`, `orchestration/laws/*`, and `surfaces/laws` only. |
| PARAM/settings sync gate | `docs/laws/conventions.md`; `docs/laws/ledger.md`; S187 memory note on PARAM reconciliation; master PARAM table as model | PARAM rows document every setting with tunable/non-tunable status; mapping for non-agent books must be explicit: `dispatcher` -> `orchestration/settings.py`, `surfaces` -> `surfaces/dashboard/settings.py` | Yes: non-agent settings ownership should be a small map, not path guessing from the book name. |
| Existing dispatcher and surfaces tests | `docs/laws/conventions.md`; `agents/master/laws/test-plan.md`; `docs/sprints/sprint-70-per-agent-law-backfill.md` | A cited green row needs a test whose docstring names the clause and would fail if the clause broke | Yes: cite only existing tests that falsify the clause; anything merely adjacent stays gray or becomes a small targeted guard test if it fits the sprint cap. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No `contracts/`
change. It adds no product behaviour, but it declares existing dispatcher and surfaces guarantees in
new law books, so the full law cycle applies: books, test-plan rows, docstring citations, drift rows,
rollups, gate discovery, PARAM sync, LOCKED v1.

**Contradictions found between a law and this spec:** None found in the required reading before code
reconciliation. Existing books remain read-only.

**Laws found silent where a decision was needed:** Dispatcher placement and hold-answer behaviour had
no law home (DRIFT-068/069). Surfaces also had no component law home for read/write boundaries,
confirmation, run scoping, or operator-language rules; DL-47/DL-207/DL-208 carry those decisions but
the gate did not read them as law.

**Clauses that were ⬜ and are now proven:** The new dispatcher book is 25 / 30 green, and the new
surfaces book is 27 / 34 green. Remaining gray rows are unproven documentation-of-scope,
dependency/secret boundary, or output-contract claims that did not have a test that would fail if
the clause broke.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_component_law_book_uncited_green_is_checked` | `tests/test_law_coverage_component_books.py` | 🟩 old gate passed the planted non-agent book; new gate fails it | `DSP-FIX-01` fixture |
| A2 | `test_component_law_book_orphan_row_fails` | `tests/test_law_coverage_component_books.py` | 🟩 | fixture orphan row |
| A3 | `test_component_law_book_missing_row_is_reported` | `tests/test_law_coverage_component_books.py` | 🟩 | fixture missing row |
| A4 | `test_law_book_discovery_uses_declared_non_recursive_roots` | `tests/test_law_coverage_component_books.py` | 🟩 discovers agents + `dispatcher` + `surfaces`; ignores `ops/laws` and `docs/laws` | discovery guard |
| A5 | `test_surfaces_book_syncs_against_mapped_dashboard_settings` | `tests/test_param_law_sync_component_books.py` | 🟩 mapped `surfaces` book fails on a mismatched `Tunable` cell | PARAM sync |
| A6 | Real dispatcher book | `orchestration/laws/dispatcher/{laws.md,test-plan.md}` | 🟩 `check_law_coverage.py` exit 0; derived count 25 / 30 | `DSP-*` |
| A7 | Real surfaces book | `surfaces/laws/{laws.md,test-plan.md}` | 🟩 `check_law_coverage.py` exit 0; derived count 27 / 34 | `SRF-*` |
| A8 | DRIFT-068 closure row | `docs/laws/drift-register.md` | 🟩 row is CLOSED and cites `DSP-IN-03`, `DSP-OUT-03`, `DSP-OUT-04`, `DSP-ORD-01`, `DSP-IDM-02` | `DSP-*` |

**Tests added beyond the plan:** None beyond the two planned gate-test files. Existing
orchestration/surfaces tests received docstring citations only.

---

## Closeout — evidence

**Status:** BUILT.

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\trading-agents-sprint-229-every-component-that-decides-answers-to-a-law-book`; `.env` not read or printed.

**Result:** Dispatcher and surfaces law books authored from the template, reconciled against code and
tests, LOCKED v1, wired into law coverage and PARAM/settings gates.

**Files changed:** new law folders; docs/law rollups and drift rows; gate discovery/mapping scripts;
new gate tests; existing test docstrings; PATCH version bump. No product module changed. Gate-only
scope note: `scripts/param_law_sync.py` consumes the new explicit source mapping and did not grow
(197 lines).

**Design decisions:** recorded as [`DL-221`](../design-log.md) before authoring. Rejected fake
`agents/` homes, recursive discovery, one broad orchestration book, deleting template sections, and
fixing divergences inside this sprint.

**Proof — the red run first:**

```text
uv run pytest tests/test_law_coverage_component_books.py tests/test_param_law_sync_component_books.py --no-cov
collected 5 items
tests\test_law_coverage_component_books.py FFFF
tests\test_param_law_sync_component_books.py F

Old behavior: non-agent fixture books were outside discovery. A1/A2/A3 returned 0 for violations,
A4 discovered only ('probe',), and A5 returned 0 instead of failing the mapped component mismatch.
```

**Proof — the green run:**

```text
uv run pytest tests/test_law_coverage_component_books.py tests/test_param_law_sync_component_books.py --no-cov
5 passed in 2.40s

uv run python scripts\check_law_coverage.py
exit 0, no output

uv run python scripts\check_param_law_sync.py
exit 0, with only the two pre-existing portfolio-manager envelope warnings.
```

**Guards planted:** DL-70 plant 1 removed the only `DSP-IDM-01` test citation and full
`make ci > ci.txt` failed at law coverage:

```text
uv run python scripts/check_law_coverage.py
[FAIL] orchestration/laws/dispatcher/test-plan.md:25: DSP-IDM-01 no resolved test docstring names DSP-IDM-01: orchestration/tests/test_scheduled_dispatch.py::test_scheduled_run_id_is_stable
make: *** [Makefile:53: ci] Error 1
```

DL-70 plant 2 changed the `SRF` PARAM `log_tail_default` `Tunable` cell from `YES` to `NO`, and
full `make ci > ci.txt` failed at PARAM sync:

```text
uv run python scripts/check_param_law_sync.py
[FAIL] surfaces/laws/laws.md:168: surfaces.log_tail_default law declares NO; settings field is registered via tunable(), expected not registered via tunable()
make: *** [Makefile:54: ci] Error 1
```

Both plants were restored.

**Module line counts:** `scripts/check_law_coverage.py` 228 (unchanged legacy ceiling);
`scripts/param_law_sync.py` 197 (not grown); `scripts/law_coverage_docs.py` 185;
`scripts/param_law_sync_sources.py` 153; touched near-ceiling tests:
`orchestration/tests/test_scheduled_dispatch_polling.py` 199,
`orchestration/tests/test_scheduled_dispatch_readiness.py` 198,
`surfaces/tests/test_dashboard_chat.py` 198. All touched Python modules are below 200 lines.

**`make ci`:** `cmd /c "make ci > ci.txt 2>&1"` from the sprint worktree exited 0.

```text
================= 3159 passed, 6 skipped in 93.27s (0:01:33) ==================
Required test coverage of 100.0% reached. Total coverage: 100.00%
No unaccepted vulnerabilities; 1 accepted advisory re-checked
Detect secrets...........................................................Passed
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 6 new file(s)
```

**`make gate-ran`:** pending final SHA after commit/push.

**Not met / verified failing:** Remote gate and exact-SHA `make gate-ran` are pending until this
handback is committed and pushed.

---

## Return notes

- Dispatcher divergences found: none new. `DRIFT-068` and `DRIFT-069` are CLOSED by the new
  `DSP` book; `orchestration.dispatcher.Dispatcher` is explicitly out of scope by DL-221.
- Surfaces divergences found: none new. `DRIFT-022` was already corrected and is cited by `SRF-OUT-01`
  rather than reopened.
- Branch-built status only until merge: main is unchanged, no deployment is required, and no live
  proof is claimed for this docs/gate sprint.
