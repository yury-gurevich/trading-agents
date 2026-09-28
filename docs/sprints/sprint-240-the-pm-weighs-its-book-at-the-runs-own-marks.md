<!-- Agent: planning | Role: sprint handover -->
# Sprint 240 — the PM weighs its held book at the run's own marks, and a resumed PM at the run it resumes

**Phase:** Etalon-first continuous improvement (DL-19) · work-queue 91 ([DRIFT-079](../laws/drift-register.md)), the step before item 92's exits
**Branch:** `sprint-240-the-pm-weighs-its-book-at-the-runs-own-marks`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** [DL-240](../design-log.md) (item 91 comes before trims, adds and take-profit, which need current marks) · [DL-238](../design-log.md) D3 (the fidelity replay reproduces what the live PM read) · [DL-237](../design-log.md) (the clean-session check) · the builder's design decisions go to the **next free DL** (`DL-242` at spec time: `DL-241` is reserved by [S239](sprint-239-the-forecaster-states-how-likely-a-buy-reaches-its-target.md), which may merge first)

> **Why this bump kind.** Nothing new is built. The PM already means to weigh the current book
> (`PM-IDN-01`) and reads the wrong number. That is a bug, so PATCH, even though a clause is written to
> pin the corrected reading.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build**, except the PM amendment this spec names (law-cycle answer: Yes) |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to**, and DRIFT-079's row is yours to close |

Binding sections: **`PM-IDN-01`**, **`PM-IN`**, **`PM-OUT-06`**, **`PM-NEV-06`**, **`PM-NEV-08`**, **`PM-NEV-09`**,
**`PM-STA-01/03`**, **`PM-IDM-01`**, **`PM-FAIL`**, and the v1.6 changelog entry (the deployed-capital
denominator, which is built from these same held values).

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so
   (`PM-IDN-01` and `PM-STA-01` are ⬜ at spec time).
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md) (DRIFT-079 is this sprint).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**No `contracts/` change. Yes, a guarantee.** The PM has never stated where a held name's value comes
from, or what a resumed run reads; DRIFT-079 was found precisely because the law was silent. Owed in the
same unit of work:

- **A new `IN` clause** (next free ID; `PM-IN-05` at spec time, check it): the held book is weighed at the
  marks of the run's own `BrokerPositionSnapshot`, one value per ticker; a ticker the snapshot does not list
  falls back to the node's adoption mark, then to its cost basis; a resumed run reads the snapshot of the run
  it resumes; with no snapshot anywhere in the run's lineage, `starting_cash`. You own the final wording.
- PM book **v1.9 → v1.10** with a Changelog line; a `test-plan.md` row for the new clause, and `PM-IDN-01`
  moved ⬜ → 🟩 if your tests prove it (say so either way); clause IDs in test docstrings; the rollup in
  **both** `docs/laws/ledger.md` **and** `docs/laws/INDEX.md` (let `make ci` tell you the number).
- **DRIFT-079 closed** in `drift-register.md`, naming the fix and the DL.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/portfolio_manager/graph_portfolio.py` (and any module you split out of it) | `agents/portfolio_manager/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `PM-IDN-01`, `PM-IN`, `PM-NEV-06/08/09`, `PM-STA-01`, `PM-IDM-01` |
| `tests/test_replay_fidelity_book.py` (DRIFT-079's witness) | DL-238 D3; DRIFT-079 | the replay calls the live `portfolio_from_graph`, so this test must now prove the fix, not the defect |

⚠️ **The monitor does not change.** `Position.broker_market_value_cents` stays exactly as the monitor writes
it. If your design needs the monitor to refresh it, stop and report: that is a monitor law cycle and a
different sprint.

---

## Goal

At merge, on every run the PM values each held name at that run's broker snapshot mark, so buy headroom,
the sector-dollar cap (`PM-NEV-06`) and the correlated-cluster cap (`PM-NEV-08`) weigh today's book, not the
book on the day each holding was adopted. A run placed by `resume_run` values its book from the snapshot of
the run it resumes, instead of sizing on `starting_cash` ($100,000).

## Why (context)

DL-240 (operator, 2026-09-28) points the pack at managing the book as a distribution: take profit, trim and
add by evidence. Every one of those decisions reads a held name's current value. Today the PM reads a number
fixed on the day the holding was adopted. The error is small while the book is ~24 % invested and grows with
exposure, which S238 (deployed 2026-09-28) raises: more names now pass the volume floor.

### Measured — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| The PM's held value on `sched-2026-09-25` (the latest scheduled run at spec time) | **$23,680** for 25 names, against the run's own snapshot **$24,333**: **2.76 % low**; INTC 40 % low, AAPL 12 % | *[measured 2026-09-27 on the live spine, through `portfolio_from_graph`]* work-queue 91 |
| Why | `_node_market_value_cents` (`agents/portfolio_manager/graph_portfolio.py:121`) returns `Position.broker_market_value_cents` whenever the prop exists, **before** the snapshot's mark; the monitor writes that prop once, at adoption (`agents/monitor/reconcile.py:111`, `_create_broker_position`), and reuses the node while quantity and average entry are unchanged | *[read from the code, 2026-09-28]* |
| Who else reads `broker_market_value_cents` at runtime | **nobody**; only `scripts/fidelity_export_book.py` exports it | *[measured]* `grep -rn broker_market_value_cents agents contracts orchestration scripts` |
| The value loop | sums **per Position node** into a per-ticker total (`graph_portfolio.py:98-104`); `open_positions` can hold several active nodes for one ticker | *[read from the code]* |
| Why a resumed PM sizes on $100,000 | `resume_run` clones the source's `MarketData` with `run_id` set to the **child** id (`orchestration/resume.py:131`); the PM poll takes that id (`agents/portfolio_manager/poll.py:105`) and `_latest_snapshot` filters `BrokerPositionSnapshot` by it; no snapshot is cloned (`orchestration/resume_plan.py` `ARTIFACTS`), so none matches and the PM takes the `starting_cash` branch | *[read from the code, 2026-09-28; measured on the fleet's own code with S237 fixtures, 2026-09-27]* |
| How a child finds its source | the child `RunRequest` (`run-request:{child}`) carries `source_run_id` and a `RESUMES` edge to the source's `RunRequest`; a child's id is `{source}-resume-{stage}`, and a resume of a resume chains | *[read from the code]* `orchestration/resume.py:43-67` |
| The fidelity replay calls the live function | `scripts/replay_fidelity_inputs.py:115` calls `portfolio_from_graph`; `tests/test_replay_fidelity_book.py::test_drift_079_the_pm_weighs_a_held_name_at_its_adoption_mark` asserts the **defect** | *[measured]* grep |
| Module sizes | `graph_portfolio.py` **132**, `poll.py` 114, `agent.py` 132 | *[measured]* `wc -l` at spec time |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first** (B1–B7 below).
2. **Held value at the run's marks.** For each held ticker: the run's snapshot mark when the snapshot lists
   that ticker, counted **once per ticker** (not once per Position node); else the sum of the nodes'
   `broker_market_value_cents`; else quantity × `opened_price_cents`. Today's order of preference is inverted.
3. **A resumed run reads its source's snapshot.** When no snapshot carries the run's id, follow the run's
   `RunRequest.source_run_id` (bounded; a resume of a resume chains) and use the first ancestor's snapshot.
   Only with none in the whole lineage does the PM take `starting_cash`, exactly as today.
4. **DRIFT-079's witness test** now proves the fix: live and replay both read the snapshot marks.
5. **The law cycle** above, and the builder's decisions in `docs/design-log.md` under the next free DL.

### Out of scope (do NOT build this sprint)

- **The monitor, and `Position.broker_market_value_cents`.** Unchanged; it is the fallback when a snapshot
  does not list a ticker.
- **`orchestration/resume.py` / `resume_plan.py`.** The PM follows the lineage the resume already writes; it
  does not add a cloned snapshot.
- **The RPC path's snapshot choice** (`agent.py::_current_portfolio`, no `run_id`, so the latest snapshot of
  all). It gets the value fix for free through the shared helper; its selection is not this sprint.
- **Any change to the gates, their denominators or their tunables.** Only the held values fed into them move.
- **Fidelity tooling** (`scripts/replay_fidelity*`, `scripts/fidelity_export*`). They call the live function
  and follow it; the only test edit is DRIFT-079's witness.

### The road not taken (LAW-06)

- **Have the monitor refresh `broker_market_value_cents` every run.** Rejected: it turns an adoption record
  into a daily price ticker, costs a monitor law cycle, and the per-run mark already exists in the snapshot.
- **Clone the snapshot in `resume_run`.** Rejected: it widens the fix into orchestration and the vocabulary's
  resume edge signatures (`resume_edge_signatures`) for a lookup the PM can make from lineage already in the
  graph.
- **A resumed PM reads the latest snapshot of all** (as the RPC path does). Rejected: a resume placed days
  later would weigh the book of a different day, and the replay could not reproduce which one it read.
- **Declare the adoption mark and keep it** (DRIFT-079's other option). Rejected: nothing argues for it, and
  every exit in item 92 needs today's value.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Which snapshot's marks count.** A `stale` snapshot (broker fetch failed) may list no holdings or old
   ones. Say whether a stale snapshot's holdings are used or skipped to the fallback, and why.
2. **How the resume lineage is walked**: by `source_run_id` props or the `RESUMES` edge, and the bound on hops.
3. **Where the code lives** if `graph_portfolio.py` passes 150 lines.
4. **The final wording of the new `IN` clause.**

🪤 **Take the next free DL number, then re-check it at merge.** `DL-242` is free at spec time and `DL-241`
is S239's.

---

## Blast radius — measured 2026-09-28

| What | Detail |
| --- | --- |
| Files changed | `agents/portfolio_manager/graph_portfolio.py` (**132**), perhaps one new module beside it; PM tests; `tests/test_replay_fidelity_book.py`; `agents/portfolio_manager/laws/{laws,test-plan}.md`, `docs/laws/{ledger,INDEX,drift-register}.md`, `docs/design-log.md` |
| Agents affected | portfolio manager only. No agent imports another. |
| Contract change? | **No.** A PM law amendment (above). |
| Graph vocabulary change? | **No.** It reads labels and props that exist. |
| New env keys / tunables | **None.** The hop bound is a named constant. |
| Decision path | **Yes**: `agents/portfolio_manager/` is on the fidelity check's list (`scripts/replay_fidelity_git.py`). See Sequencing. |
| Deploy implication | **PM image retag**, the operator's call. It changes what the PM approves: held winners weigh more in both caps and in headroom. |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Plant the failing tests first** (B1–B7) and watch them fail. Paste the red output.
4. **Implement.**
5. **Law cycle**: the new `IN` clause, v1.10 + Changelog, test-plan rows, docstring citations, both rollups,
   DRIFT-079 closed.
6. **Prove the guards can fail (DL-70)**: plant each, watch it go red, restore: the node's prop preferred over
   the snapshot again (B1 red); the snapshot mark added once per node (B2 red); the lineage walk removed (B4
   red); the hop bound removed on a cyclic lineage (B5 red, or say why it cannot be caught).
7. **`make ci` green**: every step of the `ci:` target, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| B1 | 🎯 A held name is weighed at the run's snapshot mark (new `IN` clause, `PM-IDN-01`) | one adopted Position with `broker_market_value_cents` 100,000; the run's snapshot lists it at 150,000 | `position_values[ticker]` = $1,500 |
| B2 | One value per ticker (new clause) | two active Position nodes for one ticker; the snapshot lists the ticker once | the ticker's value equals the snapshot mark, not twice it |
| B3 | The fallbacks, in order (new clause) | a ticker the snapshot omits, with the prop; one without the prop; a run with no snapshot | the adoption mark; then quantity × `opened_price_cents`; then today's `starting_cash` branch, unchanged |
| B4 | 🎯 A resumed PM reads the snapshot of the run it resumes (new clause) | a source run with a fresh snapshot (equity, cash, holdings); a child `RunRequest` shaped exactly as `resume_run` writes it; `run_id` = the child's | cash and held values equal the source snapshot's; **not** `starting_cash` |
| B5 | A resume of a resume, and a broken lineage | child of child; a `source_run_id` naming a missing run; a lineage that loops | the first ancestor's snapshot; `starting_cash`; the walk stops at the bound without raising |
| B6 | 🎯 The gates see the fix (`PM-NEV-06` / `PM-NEV-08`) | a held winner whose adoption mark leaves sector headroom that its snapshot mark fills | before the fix the buy is approved; after it, rejected with the sector reason |
| B7 | DRIFT-079's witness now proves the fix, end to end (`PM-IDN-01`) | `tests/test_replay_fidelity_book.py`, the S237 fleet fixtures | live `portfolio_from_graph` equals the snapshot marks, and the replay equals live |

Put at least one resume test (B4) in the top-level `tests/` so it can place the child with the real
`orchestration.resume.resume_run`, not a hand-built node; PM-local tests may hand-build it.

---

## Success factors

- [ ] Every held ticker is valued at its run's snapshot mark, once per ticker, with the stated fallbacks (B1–B3).
- [ ] A resumed PM reads its lineage's snapshot, and only a lineage with none uses `starting_cash` (B4, B5).
- [ ] The caps decide on the corrected values (B6); the replay and live agree on them (B7).
- [ ] Law cycle done; DRIFT-079 closed; design decisions recorded under a free DL.
- [ ] Every DL-70 plant in step 6 planted, watched to fail, restored — stated per plant.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.
- [ ] **Planner, before merge (live data):**
  - **F1, the live book**: on the latest scheduled run, `portfolio_from_graph` from the branch's worktree with
    `main`'s `.env` equals that run's snapshot marks name for name (the $653 gap on `sched-2026-09-25` closes).
  - **F2, the decisions it moves**: re-run the PM's gates for that run with the branch's code and name every
    approval or rejection that changes, and why.
- [ ] **Owed after the operator's retag (F3)**: the first scheduled run's `PMRun` reads held values equal to its
      snapshot, and the fidelity check's next verdict counts sessions from this deploy.

---

## Traps

🪤 **The snapshot is per ticker; Position nodes are not.** Add the snapshot mark inside the per-node loop and a
ticker with two active nodes is counted twice. B2 exists for this.
🪤 **The PM poll's `run_id` is the `MarketData`'s**, which on a resume is the child's id, not the source's.
Read it from `poll.py:105`, not from the `RecommendationSet`.
🪤 **Do not touch `orchestration/`.** Its import contract forbids nothing here, but it is out of scope and its
resume edges are declared to the vocabulary guard.
🪤 **The witness test asserts the defect today.** It goes red on your fix by design: rewrite it to assert the
fix. Do not delete it.
🪤 **Money is `Decimal` from integer cents.** No floats anywhere in the book.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass a rule.
  📌 Current sizes: `graph_portfolio.py` **132**, `poll.py` **114**, `agent.py` **132**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: the hop bound is a named constant with a comment saying why it is enough.
- Faults, not silent failure: `kernel.fault_boundary` where the code can fail.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a pipe.**
- Version bump: PATCH in `pyproject.toml`. 🪤 A cloud session cannot re-resolve `uv lock`
  (`download.pytorch.org` is blocked, DL-228): leave `uv.lock` untouched and say so; the planner re-locks.
- Secrets never through the tree. The cloud session has **no `.env`, no `gh` and no Azure**: state which
  environment you ran in, and leave F1–F2 to the planner.

---

## Sequencing after merge

1. The cloud session: `make ci` green in its environment, the branch pushed, then it stops.
2. The planner, locally: re-lock, `make ci` on Windows, **`make gate-ran`** from a worktree whose `HEAD` is the
   pushed commit (check the printed SHA), F1–F2, and the branch ref's open CodeQL alerts.
3. 🪤 **DL-237's first fidelity verdict (due after `sched-2026-10-01`) must be run from a worktree at the last
   `main` commit before this sprint merges** (or before S239 merges, whichever is first), or run before it
   merges: `agents/portfolio_manager/` is a decision path, so after this merge every earlier session reads
   non-clean against `main`.
4. Merge to `main` locally and push; post-merge CodeQL on `main`.
5. **Deploy: PM image retag**, the operator's call. Then F3 on the next scheduled run. The fidelity clean-session
   count restarts from this deploy.

---

## Handover — paste this to the Claude cloud session

```text
Sprint 240 — the PM weighs its held book at the run's own marks, and a resumed PM at the run it
resumes. Spec: docs/sprints/sprint-240-the-pm-weighs-its-book-at-the-runs-own-marks.md on main
(read ALL of it, then CLAUDE.md). Repo: yury-gurevich/trading-agents.

Branch: sprint-240-the-pm-weighs-its-book-at-the-runs-own-marks, cut from main. Never main. If
your session forces another branch name, use it and name it in the handback.
You have NO .env, NO gh, NO Azure and no route to download.pytorch.org. Every proof is a unit test.
You cannot run `make gate-ran`: it is owed to the planner. Leave uv.lock untouched and say so; the
planner re-locks. A run result read through the GitHub connector is an observation, never GATE
PROVEN. Take DL-242 (DL-241 is S239's; re-check both on main).

What and why (DRIFT-079, work-queue 91): the PM values held names from
Position.broker_market_value_cents, written once at adoption, before the run's own
BrokerPositionSnapshot mark (agents/portfolio_manager/graph_portfolio.py:121). On sched-2026-09-25
it weighed 25 names at $23,680 against the snapshot's $24,333 (INTC 40 % low). Buy headroom, the
sector-dollar cap and the correlated-cluster cap all read these values. Separately, a run placed by
resume_run finds no snapshot (the MarketData clone carries the child's run_id; no snapshot is
cloned), so a resumed PM sizes on starting_cash ($100,000).

MUST RULE before any code: read agents/portfolio_manager/laws/laws.md and test-plan.md whole,
docs/laws/conventions.md, docs/laws/drift-register.md. Fill the Law reading record first.

Law-cycle answer: no contracts/ change, but YES a guarantee. New PM IN clause (PM-IN-05 if free):
held book at the run's snapshot marks, once per ticker; fallback adoption mark, then cost basis; a
resumed run reads the snapshot of the run it resumes; none in the lineage -> starting_cash. PM v1.9
-> v1.10 + Changelog; test-plan rows (say whether PM-IDN-01 moves to green); clause IDs in
docstrings; rollups in docs/laws/ledger.md AND docs/laws/INDEX.md; close DRIFT-079.

Build (PM only):
1. Held value: per ticker, the run's snapshot mark if the snapshot lists the ticker, counted ONCE
   per ticker (the current loop is per Position node); else the nodes' broker_market_value_cents;
   else quantity x opened_price_cents.
2. Resume: when no snapshot carries the run's id, follow RunRequest(run-request:{id}).source_run_id
   (bounded hops; a resume of a resume chains) to the first ancestor with a snapshot; none -> the
   existing starting_cash branch, unchanged.
3. tests/test_replay_fidelity_book.py::test_drift_079_... asserts the DEFECT today. Rewrite it to
   assert the fix (live == snapshot marks, replay == live). Do not delete it.

Order: DL-242 -> red tests B1-B7 (paste) -> implement -> law cycle -> DL-70 plants (prop preferred
over snapshot again; snapshot mark added per node; lineage walk removed; hop bound removed on a
looping lineage: each must go red, paste, restore) -> make ci redirected to a file, exit 0, 100.00 %.

DO NOT:
- touch the monitor or Position.broker_market_value_cents (agents/monitor/*).
- touch orchestration/resume.py, resume_plan.py, or the vocabulary pack.
- change any gate, denominator or tunable; only the held values fed into them move.
- change scripts/replay_fidelity* or scripts/fidelity_export*; they call the live function.
- make the resumed PM read the latest snapshot of all runs.
- let any test reach the network. Use Decimal from integer cents, never floats.
- claim a live proof or GATE PROVEN: F1-F2 and the gate are the planner's.
- pin a version: PATCH, next available at merge.

Handback — the planner returns it if ANY of these is missing:
[ ] Law reading record filled, including the law-cycle answer and contradictions/silences found.
[ ] Test plan results: B1-B7, each with final test name, file, PASS, clause IDs cited.
[ ] Closeout: the red run pasted before the fix; the green run after.
[ ] Each of the four DL-70 plants: what was planted, its red output, restored.
[ ] Module line counts for every file touched (all < 200).
[ ] make ci: the file, exit code, passed/skipped, coverage 100.00 %, dependency audit, detect-secrets.
[ ] Exactly how uv.lock was touched (untouched and owed, or re-resolved).
[ ] The design decisions under DL-242 with rejected alternatives (stale snapshots; lineage walk).
[ ] DRIFT-079 closed; PM laws v1.10; both rollups updated.
[ ] Return notes: scope held or moved; what you disagreed with after reading the laws; what item
    92's exits should know about held values.
[ ] Status: BUILT on the spec, and this sprint's README.md row leads with BUILT, in the same commit.
[ ] Owed items named: uv lock, make gate-ran, Windows make ci, F1-F2.
Commit on the branch and PUSH it, then stop: no merge. Anything not met: "not done", never a
Result: for work not done.
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
| *(builder)* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(builder)*

**Contradictions found between a law and this spec:** *(builder)*

**Laws found silent where a decision was needed:** *(builder)*

**Clauses that were ⬜ and are now proven:** *(builder)*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| B1 | *(builder)* | | | |

**Tests added beyond the plan:** *(builder)*

---

## Closeout — evidence

**Status:** *(builder: BUILT)*

**Tree the proofs ran in (and `.env` present?):** *(builder)*

**Result:** *(builder)*

**Files changed:** *(builder)*

**Design decisions:** *(builder: DL number, one line, where the rejected alternatives are)*

**Proof — the red run first:**

```text
(builder)
```

**Proof — the green run:**

```text
(builder)
```

**Guards planted:** *(builder, per plant)*

**Module line counts:** *(builder)*

**`make ci`:** *(builder: file, exit code, passed/skipped, coverage, dependency audit, detect-secrets)*

**`uv.lock`:** *(builder: untouched and owed, or re-resolved)*

**`make gate-ran`:** *(planner: local worktree, full SHA, output)*

**Planner live checks (F1–F2):** *(planner, before merge)*

**Not met / verified failing:** *(builder)*

---

## Return notes

- *(builder: scope held, or where it moved and why)*
- *(builder: what you disagreed with in the spec after reading the laws)*
- *(builder: what item 92's exits should know about held values)*
