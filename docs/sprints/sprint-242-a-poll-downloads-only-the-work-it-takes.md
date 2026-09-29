<!-- Agent: planning | Role: sprint handover -->
# Sprint 242 — a graph-pull poll that finds no work downloads no payloads

**Phase:** Etalon-first continuous improvement (DL-19) · work-queue 93 (live defect: OOM + Neon transfer)
**Branch:** `sprint-242-a-poll-downloads-only-the-work-it-takes`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** M
**Decisions:** [DL-244](../design-log.md) (the defect, measured; the fix direction; the Azure-Postgres option kept) · the builder's design decisions go to the **next free DL** (`DL-246` at spec time: S241 holds DL-243, the planner DL-244/245)

> **Why this bump kind.** No new capability: every poll already promises to find its pending work;
> it does so by downloading every payload it might process. A fix, so PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: each touched agent's **TRG** (what triggers it) and **IDM** (a re-poll does not
redo work); the reporter's **`RPT-IDM-03`** and its benchmark paragraph (laws.md lines 52–55).

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row. (Expect this: the scanner's TRG clauses describe RPC and pub/sub, not the
   graph-pull poll it actually runs; DRIFT-082 already records the provider's case.)
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**The planner's answer: No, expected.** The kernel `GraphStore` port gains a method (the kernel has no
law book), and each poll's *what* is unchanged — only *how* it finds the work. No `contracts/` file
should change. If your design needs one, the answer becomes **Yes** and the full cycle is owed; say so.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `kernel/graph.py`, `graph_memory.py`, `graph_postgres.py` (**199**), `graph_postgres_queries.py` (150), `graph_guarded.py` | `docs/laws/conventions.md`; ADR-0014 (Postgres store); ADR-0012 (the substrate knows no pack label) | The port is substrate: the new method names no label, edge or pack concept |
| `agents/provider/poll.py` (148), `agents/provider/barrier_history.py` (186) | `agents/provider/laws/laws.md` + `test-plan.md` | `PROV-TRG-*`, DRIFT-082 |
| `agents/scanner/poll.py` (78) | `agents/scanner/laws/laws.md` + `test-plan.md` | `SCAN-TRG-*`, `SCAN-IDM-*` |
| `agents/analyst/poll.py` (158) | `agents/analyst/laws/laws.md` + `test-plan.md` | TRG / IDM |
| `agents/portfolio_manager/poll.py` (114) | `agents/portfolio_manager/laws/laws.md` + `test-plan.md` | TRG / IDM |
| `agents/monitor/poll.py` (130) | `agents/monitor/laws/laws.md` + `test-plan.md` | TRG / IDM |
| `agents/reporter/poll.py` (44), `agents/reporter/performance_inputs.py` (**190**) | `agents/reporter/laws/laws.md` + `test-plan.md` | `RPT-IDM-03`; benchmark bars come from `MarketData` |

⚠️ **The invariant: every poll finds exactly the work it found before.** Same pending set, same order,
same idempotency on a re-poll. This sprint changes bytes moved, never decisions. If a poll's pending set
would change on any fixture, stop and report.

---

## Goal

At merge, no graph-pull poll in the provider, scanner, analyst, PM, monitor or reporter downloads a
node's props to decide whether it is pending: the pending set is found by key and edge alone, and props
are fetched only for the items that are actually pending. The reporter's benchmark reads **one**
`MarketData` (its own run's, by lineage), not all of them. After deploy, the reporter and scanner go
back to 0.5 CPU / 1 GiB.

## Why (context)

`sched-2026-09-28` stopped at 7/8: the reporter was `OOMKilled` (exit 137, 8 restarts) and the scanner
after its stage (12 restarts). Mitigated by the planner with operator approval: both raised to 1 CPU /
2 GiB, and the run then read 8/8. The same defect is the Neon bill: **$33.74 of $35.68** for 09-01 →
09-21 is data transfer (837 GB). It grows with every run, because every run adds a `MarketData`.

### Measured, 2026-09-29 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Received bytes per app, 09-01 → 09-28 | **scanner 513 GB, provider 490 GB**, analyst 46, PM 30, deliberator-manager 26, execution 8, others < 4 | *[measured 2026-09-29]* Azure Monitor `RxBytes`, `Total`, daily, per Container App |
| One full list, bytes on the wire (uncompressed JSON) | `MarketData` **128.9 MB** (78 nodes), `AgentMessage` 13.4, `Fault` 9.6, `AnalystRun` 4.4, `ScanRun` 3.3 | *[measured]* `sum(octet_length(props::text)) group by label` on Neon |
| Loaded into Python | 78 `MarketData` → **785 MB** peak | *[measured]* `tracemalloc` around `list(graph.list_nodes("MarketData"))`, from the planner's machine |
| Growth | ~3 MB JSON / ~16 MB loaded per run | *[measured]* newest node 2,963 KB |
| The provider's hidden download | `find_pending` lists `RunRequest`s, then `descendants(..., {INGESTED_BY})` — and `TRAVERSE_DESCENDANTS_SQL` selects `n.props`, so the edge check downloads **every** `MarketData` | *[measured]* `kernel/graph_postgres_queries.py` lines 99–121 |
| Neon's own store | 98 MB database, 188 dead tuples of 40,471: not a storage problem | *[measured]* `pg_database_size`, `pg_stat_user_tables` |
| Transfer after the fix | megabytes a day | *[ASSUMED — not measured]* settles on the first runs after deploy (F2) |

---

## Scope — and what is deliberately NOT here

1. **A key-and-edge query on the kernel port.** One `GraphStore` method returning the **keys** of
   `label` nodes that have **no** edge of a given type in a given direction, with no props: in
   Postgres one anti-join (`NOT EXISTS` on `edges`), in memory the equivalent, delegated unchanged by
   the guarded store. Optional filter on a `created_at` prop at or after an instant, for the two
   polls that only take current runs (see decision 2). **The failing test first.**
2. **Every poll in scope uses it**: `find_pending` in provider (`RunRequest` / `INGESTED_BY`), scanner
   (`MarketData` / `SCANNED_BY`), analyst (`ScanRun` / `ANALYZED_BY`), PM (`AnalystRun` /
   `EVALUATED_BY`), monitor, reporter, and the provider's `find_pending_barrier_history`; then
   `get_node` for each pending key only. Same pending set, same order as today.
3. **The reporter's benchmark reads its own run's `MarketData`** by lineage (`PMRun` →
   `source_analyst_run_id` → `AnalystRun` ← `ANALYZED_BY` — `ScanRun` — `DERIVED_FROM` →
   `MarketData`, as `agents/portfolio_manager/poll.py` walks it), one node. No benchmark on that node →
   the same no-benchmark path as today.
4. **A guard that a poll cannot regress**: a test double that fails the test if a `find_pending` in
   scope calls `list_nodes` or a traversal on its own label.

### Out of scope (do NOT build this sprint)

- **The forecaster's poll** (`agents/forecaster/poll.py`, lists `AnalystRun`, ~4.4 MB a poll). S241 is
  building in that file right now; touching it here collides. Filed as a follow-up.
- **Execution and the deliberator** (`PMRun` lists, < 1 MB a poll). Worth doing with the same method,
  after this sprint proves it; not in scope, to keep the diff reviewable.
- **Storing bars once, retention, archiving, moving the database to Azure** — DL-244's options, not
  this fix.
- **Reverting the 2 GiB** — an infra change after deploy, the planner's.
- **No `laws.md` edit** unless the law-cycle answer turns Yes.

### The road not taken (LAW-06)

- **Raise memory permanently.** Rejected: moves the cliff, keeps the transfer bill, and grows with every run.
- **Strip props from `descendants` / `ancestors` globally.** Rejected: dozens of callers read the props
  they walk to (lineage walks in the reporter, PM, curator); a silent change of meaning.
- **List `RunRequest`s and `get_node` each `market-data:{run_id}`.** Rejected: still fetches every payload,
  one at a time, every poll.
- **Guess the reporter's `MarketData` key from the run id.** Rejected: a resumed run's id differs from
  its source's.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` (next free DL) with their rejected alternatives BEFORE implementing.**

1. **The method's name and signature** — e.g. `keys_without_edge(label, edge_type, *, downstream=True,
   created_at_from=None) -> tuple[str, ...]`. It must name no pack concept (ADR-0012).
2. **The recency filter.** The provider's barrier poll takes only runs created within 24 h
   (`CLAIM_RUN_MAX_AGE`, DL-241 D11); 71 old `AnalystRun`s are never forecast and would otherwise be
   pending forever. `created_at` lives in props (`props->>'created_at'`), not a column. Decide: a filter
   in the method, or a second key-only query; either way, the old backlog must not be fetched.
3. **Order.** Today's pending lists come back in `list_nodes` order. Keep it exactly (the invariant); name
   the SQL `ORDER BY` that does.
4. **The split** of `kernel/graph_postgres.py` (**199 lines**): the new method cannot be added without one.

🪤 **Take the next free DL number, then re-check it at merge.** S241 is building in parallel and takes
DL-243; a branch cut before another DL lands can still collide.

---

## Blast radius — measured 2026-09-29

| What | Detail |
| --- | --- |
| Files changed | `kernel/graph.py` 78, `graph_memory.py` 145, `graph_postgres.py` **199**, `graph_postgres_queries.py` 150, `graph_guarded.py` 67; `agents/{provider,scanner,analyst,portfolio_manager,monitor,reporter}/poll.py` (148 / 78 / 158 / 114 / 130 / 44); `agents/provider/barrier_history.py` 186; `agents/reporter/performance_inputs.py` **190**; tests |
| Agents affected | provider, scanner, analyst, PM, monitor, reporter — none imports another; each imports the kernel port only |
| Contract change? | No expected (`contracts/` untouched) |
| Graph vocabulary change? | No: no label, property or edge |
| New env keys / tunables | None |
| Deploy implication | **Image-only retag** of the six agents (the planner's), then revert reporter + scanner to 0.5 CPU / 1 GiB |
| Rollback | Retag the six agents back to the tag running before the deploy (`s239` at spec time). **Not undone by a retag:** nothing in the graph (no label, property or schema change) or at the broker; the one infra setting is the memory, so **revert to 1 GiB only after F2**, and on a rollback put reporter + scanner back to 1 CPU / 2 GiB first |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Plant the failing tests first** (A1, A4, A6) and watch them fail. Paste the red output.
4. **Implement**: the port method (three stores + guard), then each poll, then the reporter's benchmark.
5. **Law cycle** if the answer turned Yes; drift rows for silences.
6. **Prove the guards can fail (DL-70)** — plants below; each must go red, paste, restore.
7. **`make ci` green** — redirected to a file, never piped.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 The port method, memory store | nodes of one label, some with the edge (either direction), some without | returns exactly the keys without it, in list order, and no props |
| A2 | The port method, Postgres SQL | `tests/graph_postgres_fakes.py` / `tests/test_graph_postgres.py` patterns | the anti-join SQL selects no `props` column; parameters bound, never interpolated |
| A3 | Recency filter | runs with `created_at` inside and outside the window, and one with no `created_at` | only the current ones; state what a missing `created_at` does, and test it |
| A4 | 🎯 No poll downloads payloads | a spy store that fails on `list_nodes` / `descendants` / `ancestors` for the poll's own label | every `find_pending` in scope passes; the old code fails it |
| A5 | Same pending set | today's fixtures per poll | identical keys and order before and after |
| A6 | 🎯 Reporter benchmark by lineage | two runs' `MarketData` with different SPY series | a run's snapshot uses its own run's series; the other run's node is never read |
| A7 | 🪤 Reporter, no benchmark | the run's `MarketData` has no benchmark | the same no-benchmark outcome as today, never another run's series |
| A8 | 🪤 Barrier backlog | 71 stale `AnalystRun`s without `BarrierHistory` plus one current | only the current run is fetched |

**DL-70 plants (each must go red, paste, restore):** (1) the Postgres SQL selects `n.props` again; (2) one
poll goes back to `list_nodes`; (3) the reporter reads the latest `MarketData` by `window_end` instead of
lineage; (4) the recency filter dropped.

---

## Success factors

- [ ] Every `find_pending` in scope finds its work without downloading props (A4), with the same set and order (A5).
- [ ] The reporter's benchmark reads exactly one `MarketData`, its own run's (A6, A7).
- [ ] No `contracts/` change, or the law cycle done.
- [ ] Design decisions recorded with rejected alternatives.
- [ ] Every DL-70 plant red, pasted, restored.
- [ ] Every touched module < 200 lines; `kernel/graph_postgres.py` split.
- [ ] `make ci` exit 0, 100.00 % coverage.
- [ ] **Owed to the planner:** `uv lock` (version), `make gate-ran`, Windows `make ci`, **F1** (a live
      dry run of every poll against Neon: pending sets equal `main`'s, bytes per poll measured), the
      retag, **F2** (next run 8/8; `RxBytes` for scanner and provider down by orders of magnitude), and
      the revert to 0.5 CPU / 1 GiB with the run after it still 8/8.

---

## Traps

🪤 **A green unit suite on the memory store proves nothing about bytes.** The defect lives in the
Postgres SQL (`n.props` in the traversal). A2 and plant (1) are the only proof that reaches it.
🪤 **Order is part of the invariant.** `list_nodes` returns in a definite order today; a set-based SQL
without `ORDER BY` passes every membership test and reorders work.
🪤 **`RPT-IDM-03`: no fact dated after the run's as-of counts.** The run's own `MarketData` satisfies it;
"the latest `MarketData`" does not on a re-report of an old run.
🪤 **Do not touch `agents/forecaster/`.** S241 is building there; a shared edit is a merge conflict in a
file you do not own this sprint.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `kernel/graph_postgres.py` **199**, `agents/reporter/performance_inputs.py` **190**,
  `agents/provider/barrier_history.py` **186**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds; the 24 h window already exists
  (`CLAIM_RUN_MAX_AGE`), reuse it.
- Faults, not silent failure — `kernel.fault_boundary` wraps the new store method like its siblings.
- `make ci` **every step** green, **100.00 % coverage floor**, **redirected to a file, never piped**.
- PATCH bump; leave `uv.lock` to the planner (see handover).
- No `.env` in a cloud session: every proof here is a unit test. **State which tree you ran in.**

---

## Sequencing after merge

1. Planner: `uv lock`, Windows `make ci`, `make gate-ran` from the worktree at the branch's `HEAD`
   (check the printed SHA against `git rev-parse HEAD`), F1 against Neon, merge, post-merge CodeQL.
2. **Deploy: image-only retag** of the six agents (operator's call).
3. F2 on the next scheduled run; then revert reporter + scanner to 0.5 CPU / 1 GiB (operator's call)
   and prove the run after it 8/8.

---

## Handover — paste this to the Claude cloud session

```text
Sprint 242 — a graph-pull poll that finds no work downloads no payloads. Spec:
docs/sprints/sprint-242-a-poll-downloads-only-the-work-it-takes.md on main (read ALL of it, then
CLAUDE.md). Repo: yury-gurevich/trading-agents.

Branch: sprint-242-a-poll-downloads-only-the-work-it-takes, cut from main. Never main. If your
session forces another branch name, use it and name it in the handback.
You have NO .env, NO gh, NO Azure and no route to download.pytorch.org. Every proof is a unit test.
You cannot run `make gate-ran`: it is owed to the planner. Leave uv.lock untouched and say so; the
planner re-locks. Take the next free DL (DL-246 at spec time; re-check on main).

This handover is complete: nobody will send you follow-up messages. If something in the spec is
wrong or blocked, record it in the handback (Return notes, "not done") and stop; do not wait.

What and why: the reporter and scanner were OOM-killed on sched-2026-09-28 (1 GiB), and Neon billed
$33.74 of $35.68 as data transfer (837 GB). Measured per app: scanner 513 GB, provider 490 GB. Every
graph-pull find_pending lists its whole label with props, then walks an edge with descendants(),
whose SQL (kernel/graph_postgres_queries.py TRAVERSE_DESCENDANTS_SQL) also returns n.props. One full
MarketData list is 128.9 MB of JSON and 785 MB in Python, and grows ~3 MB per run.

MUST RULE before any code: read, whole, the laws.md and test-plan.md of provider, scanner, analyst,
portfolio_manager, monitor, reporter; docs/laws/conventions.md; docs/laws/drift-register.md; ADR-0012
and ADR-0014. Fill the Law reading record first. Law-cycle answer expected: NO (no contracts/ change,
no new agent guarantee); if your design needs a contracts/ change it becomes YES and the full cycle is
owed. Record silences as drift rows (the scanner's TRG clauses do not describe its graph-pull poll).

Build:
1. Kernel GraphStore port: one method returning the KEYS (no props) of `label` nodes with no edge of
   `edge_type` in a given direction, optionally only those whose props created_at is at or after an
   instant. Postgres: one anti-join (NOT EXISTS on edges), parameters bound, a definite ORDER BY that
   reproduces list_nodes order. Memory store: the same semantics. Guarded store: delegate.
   kernel/graph_postgres.py is at 199 lines: split it. The method names no pack label (ADR-0012).
2. Use it in find_pending of provider (RunRequest/INGESTED_BY), scanner (MarketData/SCANNED_BY),
   analyst, portfolio_manager, monitor, reporter, and provider/barrier_history.py's
   find_pending_barrier_history (current runs only: reuse CLAIM_RUN_MAX_AGE; the 71-run backlog must
   never be fetched). Then get_node only for the pending keys. Same pending set, same order.
3. Reporter: performance_inputs._benchmark reads ONE MarketData, the run's own, by lineage (PMRun ->
   source_analyst_run_id -> AnalystRun <-ANALYZED_BY- ScanRun -DERIVED_FROM-> MarketData, as
   agents/portfolio_manager/poll.py walks it). No benchmark there -> today's no-benchmark path.
   performance_inputs.py is at 190: split if needed. RPT-IDM-03 binds.

Order: next free DL (decisions 1-4 in the spec, with rejected alternatives) -> red tests A1, A4, A6
(paste) -> implement -> drift rows -> DL-70 plants (Postgres SQL selects n.props again; one poll back
on list_nodes; reporter picks the latest MarketData by window_end; recency filter dropped: each must go
red, paste, restore) -> make ci redirected to a file, exit 0, 100.00 %.

DO NOT:
- touch agents/forecaster/ (S241 is building there), agents/execution/ or agents/deliberator/.
- change descendants()/ancestors() semantics for existing callers.
- change which work a poll finds, or its order.
- add a label, property, edge, env key or tunable.
- grow any module past 200; # noqa to bypass a rule.
- let any test reach the network.
- claim a live proof or GATE PROVEN: F1, F2 and the gate are the planner's.
- pin a version: PATCH, next available at merge.

Handback — the planner returns it if ANY of these is missing:
[ ] Law reading record filled, including the law-cycle answer and contradictions/silences found.
[ ] Test plan results: A1-A8, each with final test name, file, PASS, clause IDs cited.
[ ] Closeout: the red run pasted before the fix; the green run after.
[ ] Each of the four DL-70 plants: what was planted, its red output, restored.
[ ] Module line counts for every file touched (all < 200).
[ ] make ci: the file, exit code, passed/skipped, coverage 100.00 %, dependency audit, detect-secrets.
[ ] Exactly how uv.lock was touched (untouched and owed, or re-resolved).
[ ] The design decisions under the DL you took, with rejected alternatives.
[ ] Return notes: scope held or moved; what you disagreed with after reading the laws; which other
    callers still list a heavy label (forecaster, execution, deliberator, tooling) for the follow-up.
[ ] Status: BUILT on the spec, and this sprint's README.md row leads with BUILT, in the same commit.
[ ] Owed items named: uv lock, make gate-ran, Windows make ci, F1, retag, F2, the memory revert.
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
| *to fill* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *to fill*

**Contradictions found between a law and this spec:** *to fill*

**Laws found silent where a decision was needed:** *to fill*

**Clauses that were ⬜ and are now proven:** *to fill*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1–A8 | *to fill* | | | |

**Tests added beyond the plan:** *to fill*

---

## Closeout — evidence

**Status:** *to fill (BUILT)*

**Tree the proofs ran in (and `.env` present?):** *to fill*

**Result:** *to fill — what is now true, in the artefact's own words*

**Files changed:** *to fill*

**Design decisions:** *to fill — the DL taken and where the rejected alternatives are*

**Proof — the red run first:**

```text
to fill
```

**Proof — the green run:**

```text
to fill
```

**Guards planted:** *to fill — per plant: what, red, restored*

**Module line counts:** *to fill*

**`make ci`:** *to fill — file, exit code, passed/skipped, coverage, audit, detect-secrets*

**`make gate-ran`:** owed to the planner.

**Not met / verified failing:** *to fill*

---

## Return notes

- *to fill*
