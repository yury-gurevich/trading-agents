<!-- Agent: planning | Role: sprint handover -->
# Sprint 242 — a graph-pull poll that finds no work downloads no payloads

**Phase:** Etalon-first continuous improvement (DL-19) · work-queue 93 (live defect: OOM + Neon transfer)
**Branch:** `sprint-242-a-poll-downloads-only-the-work-it-takes`
**Status:** MERGED 2026-09-29 — `f704907c`, tag `v0.119.01`, GATE PROVEN `f704907c`, F1 passed on Neon; **deployed `s242`** (full `up`, 2026-09-29 11:21–11:49 AEST, with S241). Owed: F2 on `sched-2026-09-29`, then the reporter and scanner memory revert (operator) and one more 8/8 run
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

All read whole, first time, 2026-09-29, before the first code change: the six agents' `laws.md` and
`test-plan.md` below, `docs/laws/conventions.md`, `docs/laws/drift-register.md` (189 lines),
ADR-0012 (with its S232 correction) and ADR-0014.

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `kernel/graph*.py` (port, memory, Postgres, guarded) | conventions; ADR-0012; ADR-0014 | ADR-0012 Decision 2 (no pack concept in the substrate); ADR-0014 (the `GraphStore` port over the `nodes`/`edges` spine, no schema change outside Alembic) | Yes: the method takes the label and edge as arguments and names none; the recency filter reads a generic `created_at` prop by text so no timestamp cast can fault a poll; no migration (the anti-join uses the existing edge primary key and `edges_child` index). ADR-0014's "six-method graph port" becomes seven: a count in an ADR's context, not a decision, so no ADR edit |
| `agents/provider/poll.py`, `barrier_history.py` | provider `laws.md` v1.5 + `test-plan.md` | `PROV-TRG-02` (a recorded need found unconsumed is a trigger; a poll that finds none fetches nothing) ⬜; `PROV-TRG-04` 🟩 (only a **current** run, `is_current_run`, DL-241 D11); `PROV-IDM-02`; DRIFT-082 | Yes: `TRG-04`'s "an older run is never fetched" is kept literally: the SQL bound only narrows, and `is_current_run` still decides on what is fetched |
| `agents/scanner/poll.py` | scanner `laws.md` v1.3 + `test-plan.md` | `SCAN-TRG-01..03` (RPC and pub/sub only; `TRG-03` ⬜), `SCAN-IDM-02` 🟩, `SCAN-STA-01` ⬜ | No; the TRG silence is recorded (DRIFT-085) |
| `agents/analyst/poll.py` | analyst `laws.md` v1.6 + `test-plan.md` | `ANLZ-TRG-02`/`-03` (pub/sub; `TRG-03` ⬜), `ANLZ-IN-02`, `ANLZ-IDM-02` 🟩 | Yes: the sync-attempt condition stays part of "pending", so it is applied after the key query, on pending keys only |
| `agents/portfolio_manager/poll.py` | PM `laws.md` v1.10 + `test-plan.md` | `PM-TRG-02`/`-03` (`TRG-03` ⬜), `PM-IDM-02` 🟩, `PM-IN-05` (the lineage walk this sprint copies) | No |
| `agents/monitor/poll.py` | monitor `laws.md` v1.1 + `test-plan.md` | `MON-TRG-02`, `MON-TRG-04` ⬜, `MON-IDM-02` 🟩 (not idempotent per invocation: the poll is what keeps a run from being re-monitored), `MON-ORD-01` ⬜ (iteration order) | Yes: `MON-ORD-01` makes order explicit, so the keys come back in `list_nodes` order |
| `agents/reporter/poll.py`, `performance_inputs.py` | reporter `laws.md` v1.3 + `test-plan.md` | `RPT-TRG-02`/`-04` (`TRG-04` ⬜), `RPT-OUT-07` 🟩 (benchmark bars on `MarketData`), `RPT-IDM-03` 🟩 (nothing after the PM run's as-of), `RPT-FAIL-04` 🟩 | Yes: the run's own `MarketData` keeps the `window_end ≤ as-of` and bar-date guards, so `RPT-IDM-03` holds on a re-report |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **No.** No
`contracts/` file changes and no agent promises anything new: every poll finds the same work in the same
order, and the reporter's benchmark is still bars on a `MarketData` bounded by the as-of. The one new
surface is the kernel port method, and the kernel has no law book. No `laws.md` is edited.

**Contradictions found between a law and this spec:** none. One tension recorded, not a contradiction:
ADR-0014's context says "the same six-method graph port"; the port now has seven methods.

**Laws found silent where a decision was needed:** (1) the scanner's `TRG` clauses describe RPC and
pub/sub, not the graph-pull poll the fleet runs (DRIFT-085); (2) the same silence in the analyst, PM,
monitor and reporter `TRG` clauses, and no clause anywhere bounds what a poll may download to decide
it has no work (DRIFT-086); (3) `RPT-OUT-07` says the benchmark is "bars on `MarketData`" but not
**which** `MarketData`: the code read the latest by `window_end`, now the run's own (DRIFT-087).

**Clauses that were ⬜ and are now proven:** none. The new tests cite `SCAN-TRG-03`, `ANLZ-TRG-03`,
`PM-TRG-03`, `MON-TRG-04`, `RPT-TRG-04` and `PROV-TRG-02`, but each proves only the poll's half of its
clause (no download to decide there is no work), not "idle ⇒ zero provider calls and zero writes"; the
test plans are read-only here and the rows stay ⬜ (conventions §7a).

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_keys_without_an_outgoing_edge_come_back_in_list_order`; `test_the_guarded_store_reads_through` | `tests/test_graph_keys_without_edge.py` | PASS | DL-246 D1/D3 (kernel: no law book) |
| A2 | `test_the_anti_join_selects_the_key_and_nothing_else[outgoing/incoming]`; `test_the_store_sends_values_as_parameters_and_reads_keys_only`; `test_a_naive_bound_is_refused_and_faulted`; `test_the_anti_join_on_a_real_postgres_when_configured` (opt-in, `POSTGRES_TEST_DSN`; skipped in the gate, **run by hand against a local PostgreSQL 16.13: PASS**) | `tests/test_graph_postgres_keys.py` (fake: `tests/graph_postgres_keys_fake.py`) | PASS | DL-246 D1–D3 |
| A3 | `test_the_created_at_bound_keeps_only_current_nodes` (at/after in, 1 s before out, +1 µs in; **a missing or non-string `created_at` is excluded**); `test_the_bound_compares_in_utc_and_refuses_a_naive_instant` | `tests/test_graph_keys_without_edge.py` | PASS | DL-246 D2 |
| A4 | `test_no_poll_downloads_a_payload_to_find_its_work[provider, scanner, analyst, portfolio_manager, monitor, reporter, barrier_history]` | `tests/test_poll_payloads.py` (spy + fixtures: `tests/poll_payload_fixtures.py`) | PASS (all 7 red before the fix) | `PROV-TRG-02`, `PROV-TRG-04`, `SCAN-TRG-03`, `ANLZ-TRG-03`, `PM-TRG-03`, `MON-TRG-04`, `RPT-TRG-04` |
| A5 | `test_the_memory_store_finds_the_old_pending_set_in_order[×7]`; `test_the_postgres_store_finds_the_old_pending_set_in_order[×7]` — each finder against the pre-fix list-then-walk code kept verbatim as an oracle (`tests/poll_reference.py`): equal node lists, same order | `tests/test_poll_same_work.py` | PASS | `PROV-TRG-02`, `PROV-TRG-04`, `SCAN-IDM-02`, `ANLZ-IDM-02`, `PM-IDM-02`, `MON-ORD-01`, `RPT-TRG-04` |
| A6 | `test_a_run_benchmarks_on_its_own_market_data_by_lineage` (the other run's later `MarketData` is never read; no `MarketData` listing) | `agents/reporter/tests/test_benchmark_lineage.py` | PASS | `RPT-OUT-07`, `RPT-IDM-03` |
| A7 | `test_no_benchmark_on_the_runs_own_node_is_the_no_benchmark_path` ("missing benchmark", another run's series never used); `test_the_runs_own_node_without_a_usable_benchmark_gives_none[×6]`; `test_a_broken_lineage_gives_no_benchmark_and_never_another_runs` | `agents/reporter/tests/test_benchmark_lineage.py`, `test_benchmark_lineage_edges.py` | PASS | `RPT-OUT-07`, `RPT-NEV-03`, `RPT-IDM-03` |
| A8 | `test_the_barrier_backlog_is_never_fetched` (71 stale runs without `BarrierHistory` + 1 current: `fetched == ["current"]`) | `tests/test_poll_payloads.py` | PASS | `PROV-TRG-04` |

**Tests added beyond the plan:** `surfaces/tests/test_dashboard_read_cache.py::test_caching_graph_store_caches_key_and_edge_lookups` (the dashboard's `CachingGraphStore` implements the port, so it gained the method). Existing tests adjusted, behaviour unchanged: four reporter fixtures now link their `MarketData` into the PM run's lineage (`test_performance.py`, `test_performance_inputs_edges.py`, `test_performance_snapshot.py` ×2; the `RPT-FAIL-04` double now fails the `DERIVED_FROM` hop instead of a `MarketData` listing); `tests/test_replay_fidelity_facts.py` expects the seventh port method on the read-only export view (which refuses it, like its walks); the supervisor's `_BrokenGraph` double now subclasses the in-memory store so it keeps the whole port.

---

## Closeout — evidence

**Status:** BUILT 2026-09-29 — not merged. Branch `sprint-242-a-poll-downloads-only-the-work-it-takes`; the cloud session's own branch `claude/confident-archimedes-sz4so4` carries the same commit.

**Tree the proofs ran in (and `.env` present?):** the claude.ai cloud container's clone of `yury-gurevich/trading-agents`, branch cut from `main` at `6851752`; **no `.env`**, no `gh`, no Azure. Python deps from the untouched `uv.lock` (`uv run --frozen`). One extra local observation: a throwaway PostgreSQL 16.13 cluster in the container, migrated with the repo's Alembic `0001_spine`, for the opt-in live SQL test; it is not the fleet's Neon and proves the SQL parses and answers, nothing about bytes on the fleet.

**Result:** `GraphStore.keys_without_edge(label, edge_type, *, downstream=True, created_at_from=None)` returns keys only — in Postgres from one `NOT EXISTS` anti-join whose `SELECT` list is `n.key`, ordered `ORDER BY n.key` as `list_nodes` is. The provider, scanner, analyst, PM, monitor and reporter `find_pending` and the provider's `find_pending_barrier_history` find their work through it (`kernel.graph_pending.pending_nodes`) and `get_node` only the keys that lack their processed edge; none lists its label or walks its processed edge (A4), each finds the pre-fix set in the pre-fix order on both stores (A5), and the barrier poll never reads a run older than `CLAIM_RUN_MAX_AGE` (A8). The reporter's benchmark reads one `MarketData`, its run's own, by `PMRun.source_analyst_run_id` → `AnalystRun` ← `ScanRun` → `MarketData` (A6/A7).

**Files changed:** kernel `graph.py`, `graph_memory.py`, `graph_guarded.py`, `graph_postgres.py` (split), `graph_support.py`; new `kernel/graph_postgres_reads.py`, `graph_postgres_keys.py`, `graph_pending.py`. Agents: `provider/poll.py`, `provider/barrier_history.py`, `scanner/poll.py`, `analyst/poll.py`, `portfolio_manager/poll.py`, `monitor/poll.py`, `reporter/poll.py`, `reporter/performance_inputs.py`; new `reporter/benchmark_input.py`. Port implementers outside the scope list, changed only to keep the port whole: `surfaces/dashboard/read_cache.py`, `scripts/replay_fidelity_facts.py`. Tests as listed above. Docs: `docs/design-log.md` (DL-246), `docs/laws/drift-register.md` (DRIFT-085/086/087), this spec, `docs/sprints/README.md`, `docs/sprints/INDEX.md`. **No `contracts/`, no `laws.md`, no `test-plan.md`, no `pyproject.toml`, no `uv.lock`.**

**Design decisions:** [DL-246](../design-log.md) — D1 the method and `pending_nodes`, D2 the recency filter in the method (text order, `COLLATE "C"`, `is_current_run` still decides), D3 order = each store's own `list_nodes` order, D4 the read-side mixin split; each with its rejected alternatives, plus the residue named for the follow-up.

**Proof — the red run first:** (A1/A3/A4/A8 and A6/A7, on `6851752` + the new tests only, before any implementation)

```text
$ uv run pytest --no-cov tests/test_graph_keys_without_edge.py tests/test_poll_payloads.py
E   AttributeError: 'InMemoryGraphStore' object has no attribute 'keys_without_edge'   (×3)
E   AttributeError: 'GuardedGraphStore' object has no attribute 'keys_without_edge'
E   AssertionError: poll listed every RunRequest with its props
E   AssertionError: poll listed every MarketData with its props
E   AssertionError: poll listed every ScanRun with its props
E   AssertionError: poll listed every AnalystRun with its props
E   AssertionError: poll listed every ExecutionRun with its props
E   AssertionError: poll listed every MonitorRun with its props
E   AssertionError: poll listed every AnalystRun with its props                       (×2, barrier)
12 failed in 0.58s

$ uv run pytest --no-cov agents/reporter/tests/test_benchmark_lineage.py
E   AssertionError: the reporter listed every MarketData
E   AssertionError: assert 'missing benchmark' in '… Performance: no usable sessions since 2026-08-10 (performance inputs unavailable)'
FAILED agents/reporter/tests/test_benchmark_lineage.py::test_a_run_benchmarks_on_its_own_market_data_by_lineage
FAILED agents/reporter/tests/test_benchmark_lineage.py::test_no_benchmark_on_the_runs_own_node_is_the_no_benchmark_path
2 failed in 0.33s
```

**Proof — the green run:**

```text
$ uv run pytest --no-cov tests/test_graph_keys_without_edge.py tests/test_graph_postgres_keys.py \
    tests/test_poll_payloads.py tests/test_poll_same_work.py \
    agents/reporter/tests/test_benchmark_lineage.py agents/reporter/tests/test_benchmark_lineage_edges.py
SKIPPED [1] tests/test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
39 passed, 1 skipped in 0.56s

$ POSTGRES_TEST_DSN=<local PostgreSQL 16.13, migrated 0001_spine> uv run pytest --no-cov \
    tests/test_graph_postgres_keys.py tests/test_graph_postgres.py -k "real_postgres or round_trip"
2 passed, 10 deselected in 0.52s
```

**Guards planted:** each on the finished tree, run, then restored from a copy (the restored tree is the one `make ci` passed):

1. **The Postgres SQL selects `n.props` again** (`SELECT n.key, n.props` in `KEYS_WITHOUT_OUTGOING_SQL`) → `E AssertionError: assert 'n.key, n.props' == 'n.key'` · `FAILED …test_the_anti_join_selects_the_key_and_nothing_else[outgoing]` · 1 failed, 3 passed, 1 skipped. Restored.
2. **The scanner's poll back on `list_nodes`** (list `MarketData`, walk `SCANNED_BY` per node) → `E AssertionError: poll listed every MarketData with its props` · `FAILED …[scanner]` · 1 failed, 7 passed. Restored.
3. **The reporter picks the latest `MarketData` by `window_end`** (list all, keep the max at or before the as-of) → `E AssertionError: the reporter listed every MarketData` and `E AssertionError: assert 'missing benchmark' in '…'` · 2 failed. Also run without the spy, on a plain store over the same fixture: planted `closes read: {08-10: 200.0, 08-11: 202.0, 08-12: 204.0}` (the other run's series), restored `{08-10: 100.0, 08-11: 101.0}`. Restored.
4. **The recency filter dropped** (no `created_at_from` in `find_pending_barrier_history`) → `E AssertionError: assert ('stale-00', …) == ('current',)` … `Left contains 71 more items` and `E AssertionError: assert ['stale-00', …] == ['current']` · the barrier A4 case and A8 red. Restored.

**Module line counts:** all < 200. Kernel: `graph.py` 98, `graph_memory.py` 176, `graph_guarded.py` 81, `graph_postgres.py` 147 (was **199**), `graph_postgres_reads.py` 113, `graph_postgres_keys.py` 58, `graph_pending.py` 34, `graph_support.py` 121, `graph_postgres_queries.py` 150 (untouched). Agents: `provider/poll.py` 145, `provider/barrier_history.py` 191, `scanner/poll.py` 78, `analyst/poll.py` 160, `portfolio_manager/poll.py` 111, `monitor/poll.py` 127, `reporter/poll.py` 44, `reporter/performance_inputs.py` 146 (was **190**), `reporter/benchmark_input.py` 87. Others: `surfaces/dashboard/read_cache.py` 174, `scripts/replay_fidelity_facts.py` 99. Tests: `tests/poll_payload_fixtures.py` 166, `tests/test_graph_postgres_keys.py` 117, `tests/test_graph_keys_without_edge.py` 102, `tests/graph_postgres_keys_fake.py` 85, `tests/test_poll_payloads.py` 69, `tests/test_poll_same_work.py` 68, `tests/poll_reference.py` 63, `tests/test_replay_fidelity_facts.py` 71, `agents/reporter/tests/test_benchmark_lineage.py` 93, `test_benchmark_lineage_edges.py` 76, `benchmark_lineage.py` 66, `test_performance.py` 160, `test_performance_inputs_edges.py` 98, `test_performance_snapshot.py` 162, `agents/supervisor/tests/test_supervisor_agent.py` 181 (was 197), `surfaces/tests/test_dashboard_read_cache.py` 115.

**`make ci`:** `make ci > ci.txt 2>&1; echo $?` in the cloud tree (no `.env`) → **exit 0**. ruff clean, format clean, mypy `Success: no issues found in 1105 source files`, import-linter 5 kept / 0 broken, module size / header / law coverage / PARAM sync / sprint status / markdown links / version scheme passed, pytest **3632 passed, 8 skipped**, coverage **100.00 %** (19,536 statements, 0 missed), dependency audit `No unaccepted vulnerabilities; 1 accepted advisory re-checked`, detect-secrets **Passed** (tracked and 14 untracked new files). Re-run on the final tree with this handback written (`ci3.txt`): **exit 0**, the same 3632 passed / 8 skipped, 100.00 %, audit and detect-secrets clean.

**`make gate-ran`:** owed to the planner.

**Not met / verified failing:** nothing in the build list is unmet. **Not done here, by design:** any live proof (F1, F2), `uv lock`, `make gate-ran`, Windows `make ci`, the retag, the memory revert — see Return notes.

---

## Return notes

- **Scope held**, with two out-of-list files touched only because they implement the port (`surfaces/dashboard/read_cache.py`, `scripts/replay_fidelity_facts.py`) and one supervisor test double; no `agents/forecaster/`, `agents/execution/` or `agents/deliberator/` file changed; no label, property, edge, env key or tunable added; `descendants()`/`ancestors()` untouched for every caller; no `# noqa` added.
- **Law-cycle answer: No.** No `contracts/` change, no new agent guarantee, no `laws.md` or `test-plan.md` edit. Three silences filed as DRIFT-085 (scanner TRG), DRIFT-086 (the graph-pull polls of analyst/PM/monitor/reporter, and no clause bounding what a poll downloads), DRIFT-087 (`RPT-OUT-07` does not say which `MarketData`).
- **What I disagreed with after reading the laws:** nothing that blocked the spec. Two notes: ADR-0014's context says "six-method graph port" (now seven; a count, not a decision); and the spec's A4 wording ("fails on a traversal on its own label") would forbid the analyst's `DERIVED_FROM` walk, which is part of *its* pending rule (the sync check), so the spy refuses the **processed-edge** walk and the listing, and pins which nodes are fetched instead.
- **Residue (not built, for the follow-up):** the analyst still reads one `MarketData` (with props, via `DERIVED_FROM`) per **un-analysed** `ScanRun` per poll to learn its `run_id` for the sync check — unchanged from before for those, but a `ScanRun` that never syncs costs ~3 MB a poll forever; the reporter `get_node`s every never-reported sync `MonitorRun` (small props, one per run, grows by one a run); the monitor's `find_pending_position_sync` still lists `BrokerPositionSnapshot`s.
- **Other callers that still list a heavy label:** `agents/forecaster/poll.py` and `agents/forecaster/settlement_pass.py` (`AnalystRun`, ~4.4 MB a poll); execution and the deliberator (`PMRun`); resume (`orchestration/resume.py` clones a `MarketData` by copying its props — a write, but ~3 MB per resume); tooling that lists `MarketData`/`AnalystRun` for reports. `grep -rn 'list_nodes("MarketData")\|list_nodes(MARKET_DATA_LABEL)'` is the starting list.
- **`uv.lock`: untouched.** No `pyproject.toml` change and no version bump (PATCH at merge, the planner's); every command ran `uv run --frozen` or plain `uv run` against the unchanged lock.
- **Owed to the planner:** `uv lock` with the PATCH bump; Windows `make ci`; `make gate-ran` from the worktree at this branch's `HEAD` (check the printed SHA); **F1** — a live dry run of every poll against Neon (pending sets equal `main`'s, bytes per poll measured; the text-order recency filter and the anti-join have never met Neon's data or collation); merge; the image-only **retag** of the six agents; **F2** on the next run (8/8, `RxBytes` for scanner and provider down by orders of magnitude); then the **memory revert** of reporter + scanner to 0.5 CPU / 1 GiB and the run after it 8/8. No `GATE PROVEN` and no live result is claimed here.
