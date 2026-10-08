<!-- Agent: planning | Role: sprint handover -->
# Sprint 252 — every pending-work finder in the fleet fetches only its pending work

**Phase:** Etalon-first continuous improvement (DL-19) · work-queue 101 and 106 (DRIFT-097)
**Branch:** `sprint-252-every-finder-fetches-only-its-pending-work`
**Status:** MERGED 2026-10-02 — `0.121.03`, fast-forwarded to `dd22b348`, tag `v0.121.03`, GATE PROVEN `dd22b348` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (3,966 passed, 8 skipped, 100.00 %, dependency audit clean); built by Codex in `../ta-s252`, rebased over S253 and merged with the planner's mypy fix to the test clock; forecaster laws v1.10 (25 / 52), deliberator v1.12 (27 / 59), execution v1.12 (40 / 66), monitor v1.3 (21 / 46); DRIFT-097 and DRIFT-100 `CORRECTED`; **F1 PASS** (old and new finders on the live graph: 44 comparisons, every pending set equal and in the same order; one idle poll of the six reads 18.7 MB before and only a key query after); **deployed `s255` 2026-10-08**; owed: F2
**Version:** *next available PATCH at merge*
**Effort:** M
**Decisions:** [DL-246](../design-log.md) (the method, decided and built in S242) · the builder's decisions go to **DL-261**, reserved for this sprint · DRIFT-097 (closed here) · **DRIFT-100**, reserved for the execution book's silence on its graph-pull submit

> **Why this bump kind.** No new capability: each of the six finders already promises to find its
> pending work, and does it by downloading every node it might process. A fix, so PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED.** This sprint amends four named clauses and adds one (below). Any other clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the one law-adjacent file you may append to |

Binding sections here: each touched agent's **TRG** (what triggers it) and **IDM** (a re-poll does not
redo work).

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** The planner's answer is Yes, and names what is owed.
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**The planner's answer: Yes.** No `contracts/` file changes. But S251 wrote the payload bound into
six books (*"found by key and edge alone, props fetched only for those nodes"*), and this sprint makes
the same bound true for four more. That is a guarantee each book did not make, so the full cycle is
owed, in this sprint, for exactly these clauses:

| Book | Clause | Amendment |
| --- | --- | --- |
| monitor (v1.2 → **v1.3**) | `MON-TRG-02` | The last two sentences (the `ExecutionRun` bound, and *"The position-sync work is not bounded this way … (DRIFT-097)"*) become one statement covering **both** work kinds: sync work is found from the `RunRequest`s with no `POSITION_SYNCED_BY` edge, each read with its one linked snapshot; evaluation work as today. Also update the book's own Divergence register row for DRIFT-097 |
| forecaster (v1.9 → **v1.10**) | `FORE-TRG-01` | Add: both loop works are found by key and edge alone (`AnalystRun`s with no `FORECAST_BY` edge, and with no `BARRIER_SETTLEMENT_BY` edge), the deployed loop asks only for runs created within the 24 h, and props are fetched only for those |
| deliberator (v1.11 → **v1.12**) | `DLIB-TRG-01` | Add: the pending `PMRun`s are found by key and edge alone, and props are fetched only for those |
| execution (v1.11 → **v1.12**) | `EXEC-TRG-07` | Add: the unconsumed `RunRequest`s are found by key and edge alone (no `REFRESHES` edge), props fetched only for those |
| execution (same version) | **`EXEC-TRG-08`, new** | The book names RPC and pub/sub triggers for `submit` and is silent on the path the fleet runs. New clause: graph-pull submit, a `PMRun` with no `EXECUTED_BY` edge that is not waiting on its deliberation (`deliberation_grace_seconds`) is submitted from the graph, once; pending `PMRun`s are found by key and edge alone, props fetched only for those. **First check the whole book: if a clause already states this trigger, amend that clause instead and say so.** File the silence as **DRIFT-100**, CORRECTED by this sprint |

Each amended or new clause gets: a Changelog line in its book, a `test-plan.md` row naming the test
that proves the bound, the clause ID in that test's docstring, and the rollups in **both**
`docs/laws/ledger.md` and `docs/laws/INDEX.md` (let `make ci` tell you the numbers). DRIFT-097 becomes
`CORRECTED` in `docs/laws/drift-register.md`.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/forecaster/poll.py` (151), `agents/forecaster/settlement_pass.py` (139) | `agents/forecaster/laws/laws.md` + `test-plan.md` | `FORE-TRG-01`, `FORE-TRG-02`, `FORE-IDM-05`; DL-241 D10, D11 |
| `agents/deliberator/store.py` (88) | `agents/deliberator/laws/laws.md` + `test-plan.md` | `DLIB-TRG-01`, `DLIB-TRG-03` |
| `agents/execution/poll.py` (136) | `agents/execution/laws/laws.md` + `test-plan.md` | `EXEC-TRG-07`; the deliberation wait (`deliberation_grace_seconds`, DL-98) |
| `agents/monitor/position_sync.py` (101) | `agents/monitor/laws/laws.md` + `test-plan.md` | `MON-TRG-02`, DRIFT-097 |
| `tests/test_poll_payloads.py` (70), `tests/poll_payload_fixtures.py` (**166**) | `docs/laws/conventions.md` §3 | The guard S242 built; its docstring cites every clause it proves |
| `kernel/graph_pending.py` (34) — **read, do not change** | DL-246 | `pending_nodes(graph, label, edge_type, *, created_at_from=None)` |

⚠️ **The invariant: every finder returns exactly the work it returned before, in the same order.**
This sprint changes bytes moved, never decisions. Two differences are decided here and named in
decision 3 (the monitor's sync finder); any other change to a pending set on any fixture means stop
and report.

---

## Goal

At merge, all thirteen pending-work finders in the nine loop agents find their work by key and edge,
and fetch props only for the items that are pending. Seven have done so since S242. This sprint
converts the last six, and adds a guard that fails when a finder exists that the payload test does
not cover.

## Why (context)

S242 fixed the polls that were killing the reporter and scanner, and left four agents alone to keep
its diff reviewable. Those four now move the most data of any app in the fleet, on every idle poll,
and the amount grows with every run. It is a transfer cost, not a memory risk. The monitor's case is
also an open drift row (DRIFT-097), and the operator wants the register at zero.

### Measured, 2026-10-02 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Received bytes per app on one night | forecaster **2,324 MB**, deliberator-manager **1,094 MB**, execution **404 MB**, monitor **145 MB**; provider 68 MB and scanner 11 MB after S242 | *[measured 2026-10-01, carried from work-queue 101]* Azure Monitor `RxBytes`, 22:20–00:40 UTC, `sched-2026-09-30`. Re-measured by the planner at F2 |
| Received bytes, the night before this spec | forecaster **2,295 MB**, deliberator-manager **1,021 MB**, execution **403 MB**, monitor **143 MB**; analyst 49, provider 42, reporter 32, scanner 10, PM 8 | *[measured 2026-10-02]* Azure Monitor `RxBytes`, `Total`, 22:20–00:30 UTC, `sched-2026-10-01`: the baseline F2 compares against |
| Payload of each label, whole | `AnalystRun` 82 nodes **6.24 MB**; `DeliberationRun` 86 / **3.88 MB** (largest 0.38); `PMRun` 86 / 0.86 MB; `BrokerPositionSnapshot` 196 / 0.37 MB; `RunRequest` 82 / 0.07 MB; `MonitorRun` 168 / 0.05 MB; `ExecutionRun` 86 / 0.01 MB | *[measured 2026-10-02]* `len(json.dumps(props))` summed over `list_nodes(label)` on Neon |
| What one idle poll reads today | forecaster: lists `AnalystRun` **twice** (two finders), ≈ 12.5 MB. deliberator: lists `PMRun`, then walks `DELIBERATED_BY` from each, and the walk returns each `DeliberationRun`'s props, ≈ 4.7 MB. execution: lists `RunRequest` and `PMRun` and walks an edge from each, ≈ 1.1 MB. monitor sync: lists `BrokerPositionSnapshot`, gets a `RunRequest` per snapshot, walks `MONITORED_BY` per snapshot, ≈ 0.5 MB | *[read 2026-10-02]* the six functions, whole, with the label sizes above |
| Poll cadence | 60 s for all four (`kernel/work_loop_policy.py` default; `DeliberatorSettings.poll_interval_seconds` 60); no override in `infra/deploy-agents.ps1` | *[read 2026-10-02]* |
| Idle polls account for | ≈ 1.75 GB, 0.66 GB, 0.15 GB, 0.07 GB over a 140-minute window | *[derived, not measured]* per-poll bytes × 140. That is 50–75 % of the measured figures; the rest is not attributed (wire overhead, the run's own work) |
| Pending by key and edge, now | `AnalystRun` with no `FORECAST_BY` **77** (0 created within 24 h); with no `BARRIER_SETTLEMENT_BY` **77**; `PMRun` with no `DELIBERATED_BY` **0**, with no `EXECUTED_BY` **0**; `RunRequest` with no `REFRESHES` **0**, with no `POSITION_SYNCED_BY` **0**; `BrokerPositionSnapshot` with no `MONITORED_BY` **114** | *[measured 2026-10-02]* `graph.keys_without_edge(label, edge)` on Neon |
| Those 114 snapshots | 106 are keyed by a PM run (execution's pre-submit snapshot: no `RunRequest` has that run id, so the monitor skips them for ever), 8 are old test artifacts | *[measured 2026-10-02]* keys read |
| What the six finders return now | 0 pending each, in deployed mode | *[measured 2026-10-02]* the six functions run on Neon |
| Shapes the conversion relies on | 0 of 86 `PMRun`s lack `order_intent_set`; every `AnalystRun` carries `created_at` (82 of 82); no run id has more than one snapshot linked from its `RunRequest` | *[measured 2026-10-02]* |
| Transfer after the fix | megabytes a night for these four | *[ASSUMED — not measured]* settles at F2 |

---

## Scope — and what is deliberately NOT here

1. **The six finders use `kernel.graph_pending.pending_nodes`**, as the seven before them do:
   `forecaster.poll.find_pending`, `forecaster.settlement_pass.find_pending_settlement`,
   `deliberator.store.find_pending`, `execution.poll.find_pending`,
   `execution.poll.find_pending_position_sync`, `monitor.position_sync.find_pending_position_sync`.
   The decisions below say how, one by one. **The failing test first.**
2. **Six new cases in the payload guard** (`tests/test_poll_payloads.py`), each run on the
   `PayloadSpy`: the finder never lists its own label, never walks its processed edge per node, and
   fetches exactly the candidates the case names.
3. **A completeness guard.** A test that finds every finder function in `agents/` by reading the
   source (module-level functions named `find_pending` or `find_pending_<something>`, except the
   `find_pending_work` aggregators) and fails unless each one has a case. Thirteen today.
4. **The law cycle** named in the law-cycle section: four amended clauses, one new, DRIFT-097
   corrected, DRIFT-100 filed and corrected.

### Out of scope (do NOT build this sprint)

- **The work each finder triggers.** `forecast_analyst_node`, `settle_analyst_node` (it lists
  `BarrierForecast` and `BarrierSettlement` when a run is settled), `review_pm_node`,
  `execute_pm_node`, `sync_run_request`, `sync_positions_snapshot`: unchanged.
- **Other whole-label reads that run only when there is work**: `execution/filled_entry_stops.py`,
  `execution/fill_attempts.py`, `execution/reconciliation_store.py`, `monitor/reconcile.py`,
  `portfolio_manager/run_snapshot.py`, `reporter/performance_inputs.py`, `analyst/outcome_backfill.py`.
  Name any you think should follow in the Return notes; do not touch them.
- **`kernel/`.** `keys_without_edge` and `pending_nodes` exist and are enough. If you believe they
  are not, stop and report.
- **`agents/analyst/`, `agents/reporter/`, `agents/scanner/`, `agents/portfolio_manager/`,
  `agents/provider/`, `contracts/`.** A parallel sprint (S253, a cloud session) works in the analyst's
  and the reporter's books, and those paths also carry the fidelity check's clean-session rule
  (DL-237). Touch none of them.
- **No new label, edge, property, env key or tunable.**
- **No ADR reversal.**

### The road not taken (LAW-06)

- **Find the monitor's sync work from the snapshot side** (`BrokerPositionSnapshot` with no
  `MONITORED_BY`), as DRIFT-097's row suggested. Rejected: 114 snapshots lack that edge today and 106
  of them never will, so every poll would fetch all of them, one more with each run.
- **A 24-hour window on the snapshot label.** Rejected: it bounds the fetch but changes behaviour (a
  snapshot the monitor missed for a day would never be adopted), and decision 3 needs no window.
- **Strip props from `descendants()`.** Rejected in DL-246: dozens of callers read the props they walk to.
- **Lower the poll cadence.** Rejected: it trades a slower run for a smaller bill and fixes nothing.

---

## The design decisions this sprint has to make

The planner decided these from the measurements above. **Record them, with what you find while
building and the rejected alternatives, in `docs/design-log.md` as DL-261 BEFORE implementing.**

1. **Forecaster, both finders.** `pending_nodes(graph, "AnalystRun", <edge>, created_at_from=since)`,
   with `since = None if now is None else now - CLAIM_RUN_MAX_AGE` (`contracts/barrier_history.py`),
   exactly as `agents/provider/barrier_history.py::find_pending_barrier_history` does. `is_current_run`
   still decides, and `find_pending`'s `_history_ready` check runs on the fetched nodes only. Without
   `now` (the in-process pipeline) there is no window, as today.
2. **Deliberator and execution submit.** `pending_nodes(graph, "PMRun", <edge>)`, then the existing
   filter on the fetched nodes: `order_intent_set` present (deliberator), `is_waiting` false
   (execution). Two bounded costs are accepted and pinned by tests: a `PMRun` waiting out its
   deliberation grace is fetched on each poll until it is submitted (one run, minutes); a `PMRun`
   with no `order_intent_set` would be fetched on every poll for ever (0 of 86 exist).
3. **Monitor sync, found from the `RunRequest` side.**
   `pending_nodes(graph, "RunRequest", POSITION_SYNC_EDGE)`, then `linked_snapshot(graph, request)`
   (`contracts/position_sync.py`) for each; a request whose snapshot is not written yet yields
   nothing. The finder still returns **snapshot** nodes, in the requests' list order. Two differences
   from today, both decided:
   - A second snapshot for a run that is already synced is no longer picked up. None exists (measured).
   - A marker half-written (the snapshot has its `MONITORED_BY` edge, the request lacks
     `POSITION_SYNCED_BY`) is pending again, and `sync_positions_snapshot` completes it through its
     existing "marker already exists" branch. Today that run is stuck: the monitor sees it as synced,
     and the analyst, which waits on the request's edge, never starts.
4. **Execution sync.** `pending_nodes(graph, "RunRequest", SNAPSHOT_REFRESH_EDGE)`. Equivalent to
   today because the only `REFRESHES` edge written from a `RunRequest` points at its snapshot
   (`agents/execution/poll.py`; the other `REFRESHES` writer starts from a `BrokerOrderStatus`).
5. **Where the six cases live.** `tests/poll_payload_fixtures.py` is at 166 lines and cannot take six
   seeders. Split it; do not raise a number in `scripts/module_size_baseline.py`.
6. **How the completeness guard finds finders.** Reading source with `ast` is preferred over
   importing every module. State the rule it applies, and prove it with plant 4.

🪤 **DL-261 is reserved for you and DL-262 / DL-263 for the parallel sprint.** Re-check the top of
`docs/design-log.md` before writing; entries are prepended.

---

## Blast radius — measured 2026-10-02

| What | Detail |
| --- | --- |
| Files changed | `agents/forecaster/poll.py` 151, `agents/forecaster/settlement_pass.py` 139, `agents/deliberator/store.py` 88, `agents/execution/poll.py` 136, `agents/monitor/position_sync.py` 101; `tests/test_poll_payloads.py` 70, `tests/poll_payload_fixtures.py` **166** (split); four `laws.md`, four `test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md`, `docs/design-log.md`; the agents' own tests where a fixture must change |
| Agents affected | forecaster, deliberator, execution, monitor. None imports another; each imports the kernel helper and `contracts/` only |
| Contract change? | No. `contracts/` is not touched |
| Graph vocabulary change? | No: no label, property or edge |
| New env keys / tunables | None |
| Deploy implication | **Image-only retag**, the planner's, and **not before the fidelity verdict** (after `sched-2026-10-07`, [DL-237](../design-log.md) amendment of 2026-10-02): the fleet's decision code is held still until then. This sprint touches no decision path, but a build of `main` may carry merges that do |
| Rollback | Retag to the tag running before the deploy. **Not undone by a retag:** nothing. No graph write changes shape, nothing reaches the broker, no schema, pack or infra setting moves |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md` as DL-261.
3. **Plant the failing tests first** (A1, A4, A8) and watch them fail. Paste the red output.
4. **Implement** the six finders.
5. **Law cycle**: the five clauses, the test-plan rows, the docstring citations, both rollups,
   DRIFT-097 corrected, DRIFT-100 filed and corrected.
6. **Prove the guards can fail (DL-70)**: the four plants below, each red, pasted, restored.
7. **`make ci` green**, every step of the `ci:` target, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file, and set this spec and its README row to `BUILT`.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 The six finders under the payload spy | per finder: done, pending and not-yet-ready nodes of its label | no finder lists its own label or walks its processed edge per node; the fetched keys are exactly the case's candidates, the returned keys exactly its pending set, in list order. The old code fails each |
| A2 | Same pending set | each agent's existing finder tests | they pass with no expected value changed, except where decision 3 names a difference. List every existing test you had to edit, and why |
| A3 | 🪤 The forecaster's backlog | 71 stale `AnalystRun`s with no `FORECAST_BY` and no `BARRIER_SETTLEMENT_BY`, plus one current | with `now`, each finder fetches the current run only; without `now`, all 72 are candidates as today |
| A4 | 🎯 Monitor sync from the request side | (a) request + linked snapshot, no marker; (b) request with a marker; (c) request with no snapshot yet; (d) 106 snapshots keyed by a PM run with no `RunRequest`; (e) the half-written marker of decision 3 | (a) the snapshot is returned; (b) nothing; (c) nothing and no error; (d) none of the 106 is ever fetched; (e) pending again, and `sync_positions_snapshot` leaves one marker with both edges |
| A5 | 🪤 Deliberator, a run with no orders | a `PMRun` with no `order_intent_set` and no `DELIBERATED_BY` | it is fetched and not returned (the accepted cost of decision 2, pinned) |
| A6 | 🪤 Execution, the deliberation wait | a buy-carrying `PMRun` inside its grace window, the same one after it, and an executed one | inside: fetched, not returned; after: returned; executed: never fetched |
| A7 | Execution sync | a `RunRequest` with a `REFRESHES` snapshot, one without | only the one without is fetched and returned |
| A8 | 🪤 Completeness | the source tree as it is | the cases cover every finder function in `agents/`; thirteen today |

**DL-70 plants (each must go red, paste, restore):** (1) one finder back on `list_nodes`, A1 red;
(2) the forecaster's `created_at_from` dropped, A3 red; (3) the monitor's finder built from the
snapshot label instead, A4 (d) red; (4) one finder removed from the cases, A8 red.

---

## Success factors

- [x] All six finders pass the payload spy (A1) with the pending sets they had before (A2), bar the two named differences (A4 e, and the second-snapshot case).
- [x] The completeness guard counts thirteen finders and fails on a fourteenth with no case (A8, plant 4).
- [x] No file under `kernel/`, `contracts/`, or the analyst, reporter, scanner, PM or provider agents changed.
- [x] Law cycle done: `MON-TRG-02`, `FORE-TRG-01`, `DLIB-TRG-01`, `EXEC-TRG-07` amended, `EXEC-TRG-08` added (or the existing clause amended, stated), four Changelog lines, test-plan rows, both rollups, DRIFT-097 `CORRECTED`, DRIFT-100 filed `CORRECTED`.
- [x] DL-261 written with the decisions and their rejected alternatives.
- [x] Each of the four plants red, pasted, restored.
- [x] Every touched module < 200 lines; the fixtures file split.
- [ ] `make ci` exit 0, 100.00 % coverage; any step the sandbox could not run is named as not run.
- [ ] **Owed to the planner, not the builder:** the PATCH bump and `uv lock`, Windows `make ci`,
      `make gate-ran`, the CodeQL diff, **F1** (before merge, read-only on Neon: each of the six old
      and new finders returns the same pending set now and at five past instants, and the bytes one
      idle poll reads are measured before and after), the retag after the fidelity verdict, and
      **F2** (the first scheduled run after it reads 8 / 8 and `RxBytes` for forecaster,
      deliberator-manager, execution and monitor is down by at least a factor of ten).

---

## Traps

🪤 **The deliberator's bytes are not in the label it lists.** `PMRun` is 0.86 MB; the 3.88 MB comes
back through `descendants(node, {DELIBERATED_BY})`, which returns each `DeliberationRun` with its
transcript. A finder that stops listing `PMRun` and still walks that edge per node has fixed a fifth
of it. The spy refuses the walk; do not weaken the spy.
🪤 **The forecaster has two finders over one label.** Converting `poll.py` and leaving
`settlement_pass.py` halves the download and passes every test that names one finder. A8 is there
for this.
🪤 **Order is part of the invariant.** `pending_nodes` returns in the store's `list_nodes` order.
For the monitor the order is the requests', not the snapshots'.
🪤 **A green unit suite on the memory store proves the calls, not the bytes.** The bytes are proven
on Neon by the planner (F1, F2). Do not claim them.
🪤 **`is_current_run` reads `created_at` from props.** A node with no `created_at` is never current;
keep that, and say what `created_at_from` does with such a node (S242 pinned it: read its test).

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `tests/poll_payload_fixtures.py` **166**, `agents/forecaster/poll.py` **151**,
  `agents/forecaster/settlement_pass.py` **139**, `agents/execution/poll.py` **136**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: the 24 h window is `CLAIM_RUN_MAX_AGE`, reuse it.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- PATCH bump and `uv.lock` are the planner's: leave `pyproject.toml`'s version and `uv.lock` untouched.
- Secrets never through the worktree. A worktree has **no `.env`**: every proof here is a unit test.
  **State which tree you ran in.**

---

## Sequencing after merge

1. Planner: PATCH bump and `uv lock`, Windows `make ci`, push, **`make gate-ran` exits 0** from the
   worktree at the branch's `HEAD` (the printed SHA checked against `git rev-parse HEAD`), the
   branch's open CodeQL alerts diffed against `sprint-251-every-open-drift-row-is-decided` (131).
2. **F1** on Neon, read-only, before the merge.
3. Merge to `main`, tag, post-merge CodeQL.
4. **Deploy: image-only retag, after the fidelity verdict** (not before `sched-2026-10-07` has run).
   Rollback: the tag running before it.
5. **F2** on the first scheduled run after the retag.

---

## Handover — paste this to Codex

```text
Sprint 252 — every pending-work finder in the fleet fetches only its pending work. Spec:
docs/sprints/sprint-252-every-finder-fetches-only-its-pending-work.md on main (read ALL of it, then
CLAUDE.md). Repo: yury-gurevich/trading-agents, local checkout.

Work in your own worktree, never in the main checkout and never on main:
  git worktree add ../ta-s252 -b sprint-252-every-finder-fetches-only-its-pending-work main
Build its venv there (uv sync --locked; the main checkout's venv is not yours to change). You have no
.env and no network: every proof is a unit test. Leave pyproject.toml's version and uv.lock untouched
and say so; the planner bumps and re-locks. Do not push; commit on the branch and hand back.
If a make ci step cannot run in your sandbox (the dependency audit needs the network; a pre-commit
hook may fail to spawn sh), do not bypass it silently: name the step as NOT RUN in the handback.

This handover is complete: nobody will send you follow-up messages. If something in the spec is wrong
or blocked, record it in the handback (Return notes, "not done") and stop; do not improvise.

What and why: S242 made seven graph-pull finders find their work by key and edge
(kernel/graph_pending.py::pending_nodes over GraphStore.keys_without_edge) and left six alone. Those
six download their whole label on every idle poll, every 60 s: the forecaster lists AnalystRun twice
(6.24 MB each), the deliberator lists PMRun and walks DELIBERATED_BY per node, which returns every
DeliberationRun transcript (3.88 MB), execution lists RunRequest and PMRun, the monitor lists
BrokerPositionSnapshot. Measured on one night: forecaster 2,324 MB, deliberator-manager 1,094 MB,
execution 404 MB, monitor 145 MB received. The monitor's case is DRIFT-097.

MUST RULE before any code: read, whole, laws.md and test-plan.md of forecaster, deliberator,
execution and monitor; docs/laws/conventions.md; docs/laws/drift-register.md. Fill the Law reading
record first. Law-cycle answer: YES, and exactly this is owed: amend MON-TRG-02 (monitor v1.3),
FORE-TRG-01 (forecaster v1.10), DLIB-TRG-01 (deliberator v1.12), EXEC-TRG-07 and add EXEC-TRG-08 for
the graph-pull submit the execution book does not name (execution v1.12; if a clause already states
that trigger, amend it instead and say so); a Changelog line, a test-plan row and a docstring
citation per clause; both rollups (docs/laws/ledger.md and docs/laws/INDEX.md); DRIFT-097 CORRECTED;
DRIFT-100 filed for the execution silence and CORRECTED. Edit no other clause.

Build (the spec's decisions 1-6 give each one exactly):
1. forecaster/poll.py::find_pending and forecaster/settlement_pass.py::find_pending_settlement:
   pending_nodes(graph, "AnalystRun", <edge>, created_at_from=since), since = None when now is None
   else now - CLAIM_RUN_MAX_AGE, as agents/provider/barrier_history.py does. is_current_run and
   _history_ready run on the fetched nodes only.
2. deliberator/store.py::find_pending and execution/poll.py::find_pending:
   pending_nodes(graph, "PMRun", <edge>), then the existing filter on the fetched nodes.
3. execution/poll.py::find_pending_position_sync: pending_nodes(graph, "RunRequest", "REFRESHES").
4. monitor/position_sync.py::find_pending_position_sync: from the RunRequest side,
   pending_nodes(graph, "RunRequest", POSITION_SYNC_EDGE), then linked_snapshot() for each; still
   returns snapshot nodes. NOT from the snapshot label: 114 snapshots lack MONITORED_BY and 106 never
   will.
5. tests/test_poll_payloads.py: six new cases on the PayloadSpy, and a completeness test that reads
   the source and fails unless every finder function in agents/ has a case (thirteen today).
   tests/poll_payload_fixtures.py is at 166 lines: split it.

Order: DL-261 (the decisions, with rejected alternatives) -> red tests A1, A4, A8 (paste) ->
implement -> law cycle -> the four DL-70 plants (one finder back on list_nodes; the forecaster's
created_at_from dropped; the monitor's finder built from the snapshot label; one finder removed from
the cases: each must go red, paste, restore) -> make ci redirected to a file, exit 0, 100.00 %.

DO NOT:
- touch kernel/, contracts/, or agents/analyst, reporter, scanner, portfolio_manager, provider.
- change what a finder returns or its order, beyond the two differences decision 3 names.
- change the code a finder's work runs (forecast, settle, review, execute, sync).
- weaken PayloadSpy, or change descendants()/ancestors().
- add a label, edge, property, env key or tunable.
- grow any module past 200, raise a number in scripts/module_size_baseline.py, or use # noqa.
- edit any law clause the spec does not name.
- let any test reach the network.
- claim a live proof, a byte count or GATE PROVEN: F1, F2 and the gate are the planner's.
- touch pyproject.toml's version or uv.lock.

Handback — the planner returns it if ANY of these is missing:
[ ] Law reading record filled, with the law-cycle answer and any contradiction or silence found.
[ ] Test plan results: A1-A8, each with final test name, file, PASS, clause IDs cited.
[ ] Every existing test you edited, listed, with the reason (A2).
[ ] Closeout: the red run pasted before the change; the green run after.
[ ] Each of the four DL-70 plants: what was planted, its red output, restored.
[ ] Module line counts for every file touched (all < 200).
[ ] make ci: the file it was redirected to, exit code, passed/skipped, coverage 100.00 %, and every
    step that did not run in the sandbox named as NOT RUN.
[ ] The five clauses as amended, four Changelog lines, test-plan rows, both rollups, DRIFT-097
    CORRECTED, DRIFT-100 filed.
[ ] DL-261 written.
[ ] Statement that pyproject.toml's version and uv.lock are untouched.
[ ] Return notes: scope held or moved; what you disagreed with after reading the laws; which other
    whole-label reads should follow.
[ ] Status: BUILT on the spec, and this sprint's README.md row leads with BUILT, in the same commit.
[ ] The branch name and the commit SHA of the handback.
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
| Forecaster forecast + settlement finders | `agents/forecaster/laws/laws.md` v1.9 and whole `test-plan.md` | `FORE-TRG-01`, `FORE-TRG-02`, `FORE-IDM-05`, `FORE-IN-07` | Yes: retain the existing current-run and history-readiness predicates; pass the shared 24 h bound into the key query, with no bound without `now`. |
| Deliberator pending finder | `agents/deliberator/laws/laws.md` v1.11 and whole `test-plan.md` | `DLIB-TRG-01`, `DLIB-TRG-03`, `DLIB-IDM-01` | `TRG-01`, `TRG-03` and `IDM-01` are gray before this sprint. Prove and amend `TRG-01` only; keep the order-property filter and retry semantics. |
| Execution submit + position-sync finders | `agents/execution/laws/laws.md` v1.11 and whole `test-plan.md` | `EXEC-TRG-07`, `EXEC-IDM-01`, `EXEC-NEV-06`, `EXEC-NEV-07` | Whole-book check found no graph-pull submit trigger. Add `EXEC-TRG-08`, file DRIFT-100, and retain the existing grace/posture predicate. |
| Monitor position-sync finder | `agents/monitor/laws/laws.md` v1.2 and whole `test-plan.md` | `MON-TRG-02`, `MON-IDM-02`, `MON-STA-02` | Yes: find requests lacking `POSITION_SYNCED_BY`, read each linked snapshot, and preserve the existing marker-repair branch. Reject snapshot-side discovery as DRIFT-097's old suggestion is unbounded. |
| Payload cases and completeness guard | Whole `docs/laws/conventions.md` and `docs/laws/drift-register.md`; DL-246; read-only `kernel/graph_pending.py` and shared contracts | conventions sections 2, 3, 4, 7, 7a, 9; the five trigger clauses | Keep PayloadSpy's refusal checks unchanged; split fixtures and discover module-level finders by AST without importing the fleet. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** YES: no contract changes, but four books gain a payload bound. Amend only `FORE-TRG-01`, `DLIB-TRG-01`, `MON-TRG-02`, `EXEC-TRG-07`; add `EXEC-TRG-08`. Required versions, four Changelog entries, test-plan rows/citations, both rollups, DRIFT-097 and DRIFT-100 are owed in this branch.

**Contradictions found between a law and this spec:** No blocking behavioural contradiction. `EXEC-TRG-02` still calls pub/sub the primary production path; it does not forbid the additional graph-pull path, and this out-of-scope phrase is reported rather than edited. The named amendments are explicitly authorised despite the general locked-law rule. CLAUDE.md takes precedence over AGENTS.md's stale 14-step count and merge permission wording; the brief overrides push/merge and version closeout.

**Laws found silent where a decision was needed:** No existing execution clause states the graph-pull submit trigger; DRIFT-100 will record it and `EXEC-TRG-08` will declare it. The payload bounds absent from these four books are the guarantees authorised by this spec. No other silence requires a new decision to implement the six conversions.

**Clauses that were ⬜ and are now proven:** `DLIB-TRG-01` gray -> green; new `EXEC-TRG-08` declared and proven green. `FORE-TRG-01`, `MON-TRG-02` and `EXEC-TRG-07` are amended and re-proven green. `DLIB-TRG-03` and `DLIB-IDM-01` stay gray. Derived counters: forecaster 25 / 52, monitor 21 / 46, deliberator 27 / 59, execution 40 / 66; both rollups and law-coverage check agree.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_no_poll_downloads_a_payload_to_find_its_work` (six new parameters: forecaster, settlement, deliberator, execution, execution_sync, monitor_sync; thirteen total) | `tests/test_poll_payloads.py` | PASS | `FORE-TRG-01`, `DLIB-TRG-01`, `EXEC-TRG-07`, `EXEC-TRG-08`, `MON-TRG-02`; original six trigger IDs retained |
| A2 | Existing suites in all four affected agents: 609 passed, one optional SciPy oracle skipped; `test_the_memory_store_finds_the_old_pending_set_in_order` and `test_the_postgres_store_finds_the_old_pending_set_in_order` (seven each) also pass unchanged | `agents/{forecaster,deliberator,execution,monitor}/tests/`; `tests/test_poll_same_work.py` | PASS; one named optional skip | Existing citations retained; submit-anchor test also cites `EXEC-TRG-08` |
| A3 | `test_each_forecaster_finder_fetches_only_its_current_backlog` (forecast/settlement x deployed/local); `test_both_finders_keep_the_shared_current_run_predicate` | `agents/forecaster/tests/test_forecaster_pending_payloads.py` | PASS | `FORE-TRG-01`, `FORE-IDM-05` |
| A4 | `test_monitor_sync_fetches_only_linked_snapshots_in_request_order`; `test_a_half_written_sync_marker_is_reselected_and_completed_once`; `test_a_second_snapshot_of_an_already_synced_request_is_not_picked_up` | `agents/monitor/tests/test_monitor_pending_payloads.py` | PASS | `MON-TRG-02`, `MON-STA-02` |
| A5 | `test_an_orderless_pm_run_is_fetched_but_never_returned` | `agents/deliberator/tests/test_deliberator_pending_payloads.py` | PASS | `DLIB-TRG-01` |
| A6 | `test_a_waiting_pm_run_is_fetched_until_its_grace_expires` | `agents/execution/tests/test_execution_pending_payloads.py` | PASS | `EXEC-TRG-08`, `EXEC-NEV-06` |
| A7 | `test_position_sync_fetches_only_requests_without_a_snapshot_edge` | `agents/execution/tests/test_execution_pending_payloads.py` | PASS | `EXEC-TRG-07` |
| A8 | `test_the_payload_cases_cover_every_finder`; `test_an_uncovered_fourteenth_finder_is_rejected`; `test_discovery_excludes_methods_nested_functions_and_work_aggregators` | `tests/test_poll_payloads.py` | PASS | `FORE-TRG-01`, `DLIB-TRG-01`, `EXEC-TRG-07/08`, `MON-TRG-02` |

**Tests added beyond the plan:** The shared-boundary/missing/non-string/malformed/naive timestamp cases; the synthetic fourteenth-finder and discovery-rule tests; explicit second-snapshot exclusion. They pin the existing fail-closed recency predicate, non-vacuous completeness rule and the second difference decision 3 authorises.

**Existing tests edited, and why:**

- `tests/test_poll_payloads.py::test_no_poll_downloads_a_payload_to_find_its_work`: six parameters,
  five clause citations and a fixed execution clock added. The seven original cases' expected
  fetched/returned keys and all PayloadSpy refusal methods are unchanged.
- `agents/execution/tests/test_execution_poll.py::test_execute_pm_node_submits_and_anchors`:
  `EXEC-TRG-08` docstring only, proving graph submit writes the anchor and is no longer pending.
- Fixture-only edit: `agents/monitor/tests/position_sync_helpers.py::snapshot` now links the
  synthetic `RunRequest` to the synthetic snapshot with the existing `REFRESHES` edge, as
  production already does. The work-item ordering, position adoption, stale sync and repeat-sync
  tests keep every expected value unchanged. No other existing test function was edited.
- Fixture compatibility: keep the original seven-case `CASES` export stable for the S242
  same-work oracle; join the six new cases in `tests/test_poll_payloads.py` only. DL-261 records
  the full-CI finding and rejects changing the legacy oracle or its expected values.
- The barrier-history registry wrapper became `functools.partial` with the same `now=NOW`, so
  AST completeness can inspect its real function identity. This changes no test expectation.
- New local test files have unique agent-prefixed names: an initial shared basename caused pytest
  collection collisions; renaming fixed collection without changing behaviour or expected values.

---

## Closeout — evidence

**Status:** BUILT — branch-only, offline unit proof.

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s252`, branch `sprint-252-every-finder-fetches-only-its-pending-work`, clean start at `ae54cf3591bc3312d6f7056cfd79a4a888675613` (local main = origin/main). `.env` absent. Own venv created with `uv --offline sync --locked`; main's venv untouched. No external network proof.

**Result:** All six finders use `pending_nodes`; thirteen executable payload cases cover every discovered source finder. A1-A8 pass, both monitor differences are pinned, and all four guard plants fail and are restored. Five-clause law cycle complete; DRIFT-097/100 CORRECTED. Final pytest and fourteen available local checks pass; the offline dependency audit is NOT RUN to completion and `make ci` exits 2. Release/gate/F1/F2 are not done by this builder.

**Files changed:** The five finder modules; the split payload support/original/remaining fixture modules and payload test; four new agent-local test modules; the monitor snapshot fixture and one execution test docstring; four law books and test plans; both rollups, drift register, DL-261; this sprint handover, its README/INDEX rows and the single STATE tracker. Exact module paths and counts are below; the committed diff lists all 31 intended paths.

**Design decisions:** DL-261 D1-D6, recorded before implementation: recency in both forecaster key queries; PM filters retained; monitor from request side and its two decided differences; execution sync by REFRESHES; fixture split without weakening the spy; AST completeness by exact module/function identity. Rejected alternatives and accepted orderless/waiting-candidate costs are recorded there.

**Proof — the red run first:**

```text
A8, before the six new cases were added; product source unchanged.
uv run pytest tests/test_poll_payloads.py::test_the_payload_cases_cover_every_finder --no-cov -q
F                                                                        [100%]
================================== FAILURES ===================================
__________________ test_the_payload_cases_cover_every_finder __________________
tests\test_poll_payloads.py:106: in test_the_payload_cases_cover_every_finder
    _assert_finder_cases(_finder_functions(Path(__file__).resolve().parents[1] / "agents"))
tests\test_poll_payloads.py:99: in _assert_finder_cases
    assert discovered == covered, f"finders missing cases: {sorted(discovered - covered)}"
E   AssertionError: finders missing cases: [('agents.deliberator.store', 'find_pending'), ('agents.execution.poll', 'find_pending'), ('agents.execution.poll', 'find_pending_position_sync'), ('agents.forecaster.poll', 'find_pending'), ('agents.forecaster.settlement_pass', 'find_pending_settlement'), ('agents.monitor.position_sync', 'find_pending_position_sync')]
E   assert {('agents.ana...lement'), ...} == {('agents.ana...ending'), ...}
E
E     Extra items in the left set:
E     ('agents.forecaster.poll', 'find_pending')
E     ('agents.forecaster.settlement_pass', 'find_pending_settlement')
E     ('agents.monitor.position_sync', 'find_pending_position_sync')
E     ('agents.execution.poll', 'find_pending_position_sync')
E     ('agents.execution.poll', 'find_pending')
E     ('agents.deliberator.store', 'find_pending')
E     Use -v to get more diff
=========================== short test summary info ===========================
FAILED tests/test_poll_payloads.py::test_the_payload_cases_cover_every_finder
1 failed in 2.79s

EXIT_CODE=1

A1/A4, all six new cases added; product source still unchanged.
uv run pytest tests/test_poll_payloads.py agents/monitor/tests/test_pending_payloads.py --no-cov -q
.......FFFFFF....FFF                                                     [100%]
================================== FAILURES ===================================
________ test_no_poll_downloads_a_payload_to_find_its_work[forecaster] ________
tests\test_poll_payloads.py:72: in test_no_poll_downloads_a_payload_to_find_its_work
    found = FINDERS[case.name](graph)
            ^^^^^^^^^^^^^^^^^^^^^^^^^
agents\forecaster\poll.py:56: in find_pending
    for node in graph.list_nodes(ANALYST_RUN_LABEL):
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\poll_payload_support.py:41: in list_nodes
    assert label != self.label, f"poll listed every {label} with its props"
           ^^^^^^^^^^^^^^^^^^^
E   AssertionError: poll listed every AnalystRun with its props
________ test_no_poll_downloads_a_payload_to_find_its_work[settlement] ________
tests\test_poll_payloads.py:72: in test_no_poll_downloads_a_payload_to_find_its_work
    found = FINDERS[case.name](graph)
            ^^^^^^^^^^^^^^^^^^^^^^^^^
agents\forecaster\settlement_pass.py:49: in find_pending_settlement
    for node in graph.list_nodes(ANALYST_RUN_LABEL):
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\poll_payload_support.py:41: in list_nodes
    assert label != self.label, f"poll listed every {label} with its props"
           ^^^^^^^^^^^^^^^^^^^
E   AssertionError: poll listed every AnalystRun with its props
_______ test_no_poll_downloads_a_payload_to_find_its_work[deliberator] ________
tests\test_poll_payloads.py:72: in test_no_poll_downloads_a_payload_to_find_its_work
    found = FINDERS[case.name](graph)
            ^^^^^^^^^^^^^^^^^^^^^^^^^
agents\deliberator\store.py:27: in find_pending
    for node in graph.list_nodes(PM_RUN_LABEL):
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\poll_payload_support.py:41: in list_nodes
    assert label != self.label, f"poll listed every {label} with its props"
           ^^^^^^^^^^^^^^^^^^^
E   AssertionError: poll listed every PMRun with its props
________ test_no_poll_downloads_a_payload_to_find_its_work[execution] _________
tests\test_poll_payloads.py:72: in test_no_poll_downloads_a_payload_to_find_its_work
    found = FINDERS[case.name](graph)
            ^^^^^^^^^^^^^^^^^^^^^^^^^
agents\execution\poll.py:67: in find_pending
    for node in graph.list_nodes(PM_RUN_LABEL):
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\poll_payload_support.py:41: in list_nodes
    assert label != self.label, f"poll listed every {label} with its props"
           ^^^^^^^^^^^^^^^^^^^
E   AssertionError: poll listed every PMRun with its props
______ test_no_poll_downloads_a_payload_to_find_its_work[execution_sync] ______
tests\test_poll_payloads.py:72: in test_no_poll_downloads_a_payload_to_find_its_work
    found = FINDERS[case.name](graph)
            ^^^^^^^^^^^^^^^^^^^^^^^^^
agents\execution\poll.py:49: in find_pending_position_sync
    for node in graph.list_nodes(RUN_REQUEST_LABEL):
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\poll_payload_support.py:41: in list_nodes
    assert label != self.label, f"poll listed every {label} with its props"
           ^^^^^^^^^^^^^^^^^^^
E   AssertionError: poll listed every RunRequest with its props
_______ test_no_poll_downloads_a_payload_to_find_its_work[monitor_sync] _______
tests\test_poll_payloads.py:74: in test_no_poll_downloads_a_payload_to_find_its_work
    assert tuple(node.key for node in found) == case.pending
E   AssertionError: assert ('snapshot:a', 'snapshot:c') == ('snapshot:c'...napshot:half')
E
E     At index 0 diff: 'snapshot:a' != 'snapshot:c'
E     Right contains one more item: 'snapshot:half'
E     Use -v to get more diff
_ test_monitor_sync_reads_only_pending_requests_linked_snapshots_in_request_order _
agents\monitor\tests\test_pending_payloads.py:69: in test_monitor_sync_reads_only_pending_requests_linked_snapshots_in_request_order
    found = find_pending_position_sync(graph)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
agents\monitor\position_sync.py:33: in find_pending_position_sync
    for node in graph.list_nodes(SNAPSHOT_LABEL):
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
agents\monitor\tests\test_pending_payloads.py:42: in list_nodes
    assert label != SNAPSHOT_LABEL, "sync poll listed every snapshot with props"
E   AssertionError: sync poll listed every snapshot with props
E   assert 'BrokerPositionSnapshot' != 'BrokerPositionSnapshot'
______ test_a_half_written_sync_marker_is_reselected_and_completed_once _______
agents\monitor\tests\test_pending_payloads.py:99: in test_a_half_written_sync_marker_is_reselected_and_completed_once
    assert find_pending_position_sync(graph) == [snapshot]
E   AssertionError: assert [] == [Node(label='...ma_version=1)]
E
E     Right contains one more item: Node(label='BrokerPositionSnapshot', key='snapshot:half', props=mappingproxy({'run_id': 'half', 'status': 'stale'}), schema_version=1)
E     Use -v to get more diff
____ test_a_second_snapshot_of_an_already_synced_request_is_not_picked_up _____
agents\monitor\tests\test_pending_payloads.py:128: in test_a_second_snapshot_of_an_already_synced_request_is_not_picked_up
    assert find_pending_position_sync(graph) == []
E   AssertionError: assert [Node(label='...ma_version=1)] == []
E
E     Left contains one more item: Node(label='BrokerPositionSnapshot', key='snapshot:second', props=mappingproxy({'run_id': 'done', 'status': 'stale'}), schema_version=1)
E     Use -v to get more diff
=========================== short test summary info ===========================
FAILED tests/test_poll_payloads.py::test_no_poll_downloads_a_payload_to_find_its_work[forecaster]
FAILED tests/test_poll_payloads.py::test_no_poll_downloads_a_payload_to_find_its_work[settlement]
FAILED tests/test_poll_payloads.py::test_no_poll_downloads_a_payload_to_find_its_work[deliberator]
FAILED tests/test_poll_payloads.py::test_no_poll_downloads_a_payload_to_find_its_work[execution]
FAILED tests/test_poll_payloads.py::test_no_poll_downloads_a_payload_to_find_its_work[execution_sync]
FAILED tests/test_poll_payloads.py::test_no_poll_downloads_a_payload_to_find_its_work[monitor_sync]
FAILED agents/monitor/tests/test_pending_payloads.py::test_monitor_sync_reads_only_pending_requests_linked_snapshots_in_request_order
FAILED agents/monitor/tests/test_pending_payloads.py::test_a_half_written_sync_marker_is_reselected_and_completed_once
FAILED agents/monitor/tests/test_pending_payloads.py::test_a_second_snapshot_of_an_already_synced_request_is_not_picked_up
9 failed, 11 passed in 6.03s

EXIT_CODE=1
```

**Proof — the green run:**

```text
uv run pytest tests/test_poll_payloads.py agents/forecaster/tests/test_forecaster_pending_payloads.py agents/deliberator/tests/test_deliberator_pending_payloads.py agents/execution/tests/test_execution_pending_payloads.py agents/monitor/tests/test_monitor_pending_payloads.py --no-cov -q
.............................                                            [100%]
29 passed in 4.81s

EXIT_CODE=0

uv run pytest agents/forecaster/tests agents/deliberator/tests agents/execution/tests agents/monitor/tests --no-cov -q
..........................s............................................. [ 11%]
........................................................................ [ 23%]
........................................................................ [ 35%]
........................................................................ [ 47%]
........................................................................ [ 59%]
........................................................................ [ 70%]
........................................................................ [ 82%]
........................................................................ [ 94%]
..................................                                       [100%]
=========================== short test summary info ===========================
SKIPPED [1] agents\forecaster\tests\test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
609 passed, 1 skipped in 20.16s

EXIT_CODE=0
```

**Guards planted:** All four DL-70 regressions went red (exit 1) and were restored byte-for-byte.

1. Deliberator finder back on `list_nodes(PMRun)`; A1.

```text
F                                                                        [100%]
================================== FAILURES ===================================
_______ test_no_poll_downloads_a_payload_to_find_its_work[deliberator] ________
tests\test_poll_payloads.py:72: in test_no_poll_downloads_a_payload_to_find_its_work
    found = FINDERS[case.name](graph)
            ^^^^^^^^^^^^^^^^^^^^^^^^^
agents\deliberator\store.py:30: in find_pending
    for node in graph.list_nodes(PM_RUN_LABEL)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\poll_payload_support.py:41: in list_nodes
    assert label != self.label, f"poll listed every {label} with its props"
           ^^^^^^^^^^^^^^^^^^^
E   AssertionError: poll listed every PMRun with its props
=========================== short test summary info ===========================
FAILED tests/test_poll_payloads.py::test_no_poll_downloads_a_payload_to_find_its_work[deliberator]
1 failed in 1.94s
EXIT_CODE=1
RESTORED byte-for-byte
```

2. Forecast finder drops `created_at_from`; deployed A3 fetches 71 stale props.

```text
F.                                                                       [100%]
================================== FAILURES ===================================
_ test_each_forecaster_finder_fetches_only_its_current_backlog[deployed-find_pending-FORECAST_BY] _
agents\forecaster\tests\test_forecaster_pending_payloads.py:46: in test_each_forecaster_finder_fetches_only_its_current_backlog
    assert graph.fetched == expected
E   AssertionError: assert ['stale-00', ...tale-05', ...] == ['current']
E
E     At index 0 diff: 'stale-00' != 'current'
E     Left contains 71 more items, first extra item: 'stale-01'
E     Use -v to get more diff
=========================== short test summary info ===========================
FAILED agents/forecaster/tests/test_forecaster_pending_payloads.py::test_each_forecaster_finder_fetches_only_its_current_backlog[deployed-find_pending-FORECAST_BY]
1 failed, 1 passed, 2 deselected in 1.57s
EXIT_CODE=1
RESTORED byte-for-byte
```

3. Monitor finder starts from unmarked snapshots; A4(d) fetches orphan snapshots.

```text
F                                                                        [100%]
================================== FAILURES ===================================
______ test_monitor_sync_fetches_only_linked_snapshots_in_request_order _______
agents\monitor\tests\test_monitor_pending_payloads.py:72: in test_monitor_sync_fetches_only_linked_snapshots_in_request_order
    assert graph.snapshots == ["snapshot:c", "snapshot:a", "snapshot:half"]
E   AssertionError: assert ['snapshot:a'...:pm-003', ...] == ['snapshot:c'...napshot:half']
E
E     At index 0 diff: 'snapshot:a' != 'snapshot:c'
E     Left contains 105 more items, first extra item: 'snapshot:pm-001'
E     Use -v to get more diff
=========================== short test summary info ===========================
FAILED agents/monitor/tests/test_monitor_pending_payloads.py::test_monitor_sync_fetches_only_linked_snapshots_in_request_order
1 failed in 1.33s
EXIT_CODE=1
RESTORED byte-for-byte
```

4. Forecaster case and its matching callable entry removed; A8 finds the missing source finder (12 cases for 13 functions).

```text
F                                                                        [100%]
================================== FAILURES ===================================
__________________ test_the_payload_cases_cover_every_finder __________________
tests\test_poll_payloads.py:128: in test_the_payload_cases_cover_every_finder
    _assert_finder_cases(
tests\test_poll_payloads.py:119: in _assert_finder_cases
    assert discovered == covered, (
E   AssertionError: finders missing cases: [('agents.forecaster.poll', 'find_pending')]
E   assert {('agents.ana...lement'), ...} == {('agents.ana...ending'), ...}
E
E     Extra items in the left set:
E     ('agents.forecaster.poll', 'find_pending')
E     Use -v to get more diff
=========================== short test summary info ===========================
FAILED tests/test_poll_payloads.py::test_the_payload_cases_cover_every_finder
1 failed in 3.36s
EXIT_CODE=1
RESTORED byte-for-byte
```

**Module line counts:** All 15 touched Python modules are below 200 lines (largest: 196). Markdown handover/law documents follow their existing format.

| Module | Lines |
| --- | ---: |
| `agents/deliberator/store.py` | 87 |
| `agents/deliberator/tests/test_deliberator_pending_payloads.py` | 28 |
| `agents/execution/poll.py` | 126 |
| `agents/execution/tests/test_execution_pending_payloads.py` | 62 |
| `agents/execution/tests/test_execution_poll.py` | 196 |
| `agents/forecaster/poll.py` | 154 |
| `agents/forecaster/settlement_pass.py` | 138 |
| `agents/forecaster/tests/test_forecaster_pending_payloads.py` | 74 |
| `agents/monitor/position_sync.py` | 93 |
| `agents/monitor/tests/position_sync_helpers.py` | 105 |
| `agents/monitor/tests/test_monitor_pending_payloads.py` | 134 |
| `tests/poll_payload_fixtures.py` | 95 |
| `tests/poll_payload_remaining.py` | 157 |
| `tests/poll_payload_support.py` | 98 |
| `tests/test_poll_payloads.py` | 165 |

**`make ci`:** Run in `C:\Users\yury_\Downloads\project\ta-s252`, redirected to
`C:\Users\yury_\Downloads\project\s252-evidence\make-ci.txt`; **exit 2**, because the dependency
advisory lookup was refused before network I/O. The final source has **3,953 passed, 8 skipped,
100.00 % coverage**. **Full `make ci` exit 0: not done.** No remote gate is claimed.

`UV_OFFLINE=1` was set, dotenv loading disabled, external DNS/connect refused by a
`sitecustomize.py` outside the worktree, and optional network/database test variables removed.
The guard was probed and refused external DNS before I/O. Loopback-only unit servers were allowed.
No `.env` or product setting was added. Earlier gate attempts are retained as
`make-ci-attempt-1.txt` (new test annotation omitted the `now` keyword) and
`make-ci-attempt-2.txt` (shared fixture export accidentally fed six new cases to the legacy oracle).
Both were corrected within scope before this final run; no existing expected value changed.

| Step | Check | Result |
| --- | --- | --- |
| 1 | ruff | PASS in `make ci` |
| 2 | format | PASS in `make ci` |
| 3 | mypy | PASS in `make ci`, 1,147 files |
| 4 | import-linter | PASS in `make ci` |
| 5 | module size | PASS in `make ci` |
| 6 | module header | PASS in `make ci` |
| 7 | law coverage | PASS in `make ci` |
| 8 | PARAM/settings sync | PASS in `make ci` |
| 9 | sprint status | PASS in `make ci` |
| 10 | markdown links | PASS in `make ci` |
| 11 | version scheme | PASS in `make ci` |
| 12 | pytest / 100.00 % coverage | PASS in `make ci`, 3,953 passed, 8 skipped |
| 13 | dependency audit | **NOT RUN** to completion: invoked, external lookup blocked by the offline guard |
| 14 | detect-secrets | PASS, exact command run separately after `make ci` stopped |
| 15 | untracked secrets | PASS, exact command run separately; six new files scanned |

Pasted output excerpt (command lines, final coverage/skip/summary, and the complete audit refusal;
full output is in the named file):

```text
uv run ruff check . --output-format=github
uv run ruff format --check .
1552 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
Success: no issues found in 1147 source files
uv run lint-imports
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
uv run python scripts/check_sprint_status.py
uv run python scripts/check_markdown_links.py
uv run python scripts/check_version_scheme.py
uv run pytest
TOTAL                                                           19898      0   4216      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
SKIPPED [1] tests\test_bus_azure_config.py:21: Service Bus dotenv isolation proof requires local .env
SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
SKIPPED [1] tests\test_deliberator_servicebus_peer.py:36: A1 proof requires .env present; CI has no local secrets file
SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
SKIPPED [1] tests\test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
SKIPPED [1] agents\forecaster\tests\test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
SKIPPED [1] agents\provider\tests\test_sources.py:159: FINNHUB_TEST_NETWORK=1 is not set
SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
========= 3953 passed, 8 skipped, 2470 warnings in 351.41s (0:05:51) ==========
uv run python scripts/check_dependency_audit.py
dependency audit failed: WARNING:pip_audit._cli:--no-deps is supported, but users are encouraged to fully hash their pinned dependencies
WARNING:pip_audit._cli:Consider using a tool like `pip-compile`: https://pip-tools.readthedocs.io/en/latest/#using-hashes
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "C:\Users\yury_\Downloads\project\ta-s252\.venv\Scripts\pip-audit.exe\__main__.py", line 10, in <module>
    sys.exit(audit())
             ~~~~~^^
  File "C:\Users\yury_\Downloads\project\ta-s252\.venv\Lib\site-packages\pip_audit\_cli.py", line 554, in audit
    for spec, vulns in auditor.audit(source):
                       ~~~~~~~~~~~~~^^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s252\.venv\Lib\site-packages\pip_audit\_audit.py", line 68, in audit
    for dep, vulns in self._service.query_all(specs):
                      ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s252\.venv\Lib\site-packages\pip_audit\_service\interface.py", line 180, in query_all
    yield self.query(spec)
          ~~~~~~~~~~^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s252\.venv\Lib\site-packages\pip_audit\_service\pypi.py", line 64, in query
    response: requests.Response = self.session.get(url=url, timeout=self.timeout)
                                  ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s252\.venv\Lib\site-packages\requests\sessions.py", line 671, in get
    return self.request("GET", url, params=params, **kwargs)
           ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s252\.venv\Lib\site-packages\requests\sessions.py", line 651, in request
    resp = self.send(prep, **send_kwargs)
  File "C:\Users\yury_\Downloads\project\ta-s252\.venv\Lib\site-packages\requests\sessions.py", line 784, in send
    r = adapter.send(request, **kwargs)
  File "C:\Users\yury_\Downloads\project\ta-s252\.venv\Lib\site-packages\cachecontrol\adapter.py", line 76, in send
    resp = super().send(request, stream, timeout, verify, cert, proxies)
  File "C:\Users\yury_\Downloads\project\ta-s252\.venv\Lib\site-packages\requests\adapters.py", line 696, in send
    resp = conn.urlopen(
        method=request.method,
    ...<9 lines>...
        chunked=chunked,
    )
  File "C:\Users\yury_\Downloads\project\ta-s252\.venv\Lib\site-packages\urllib3\connectionpool.py", line 793, in urlopen
    response = self._make_request(
        conn,
    ...<10 lines>...
        **response_kw,
    )
  File "C:\Users\yury_\Downloads\project\ta-s252\.venv\Lib\site-packages\urllib3\connectionpool.py", line 470, in _make_request
    self._validate_conn(conn)
    ~~~~~~~~~~~~~~~~~~~^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s252\.venv\Lib\site-packages\urllib3\connectionpool.py", line 1125, in _validate_conn
    conn.connect()
    ~~~~~~~~~~~~^^
  File "C:\Users\yury_\Downloads\project\ta-s252\.venv\Lib\site-packages\urllib3\connection.py", line 827, in connect
    self.sock = sock = self._new_conn()
                       ~~~~~~~~~~~~~~^^
  File "C:\Users\yury_\Downloads\project\ta-s252\.venv\Lib\site-packages\urllib3\connection.py", line 239, in _new_conn
    sock = connection.create_connection(
        (self._dns_host, self.port),
    ...<2 lines>...
        socket_options=self.socket_options,
    )
  File "C:\Users\yury_\Downloads\project\ta-s252\.venv\Lib\site-packages\urllib3\util\connection.py", line 60, in create_connection
    for res in socket.getaddrinfo(host, port, family, socket.SOCK_STREAM):
               ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\yury_\Downloads\project\s252-evidence\offline\sitecustomize.py", line 32, in getaddrinfo
    require_local(host)
    ~~~~~~~~~~~~~^^^^^^
  File "C:\Users\yury_\Downloads\project\s252-evidence\offline\sitecustomize.py", line 22, in require_local
    raise ExternalNetworkBlocked("S252 offline proof: external network forbidden")
sitecustomize.ExternalNetworkBlocked: S252 offline proof: external network forbidden
make: *** [Makefile:59: ci] Error 1
```

**Step 14:** `uv run pre-commit run detect-secrets --all-files`, redirected to
`C:\Users\yury_\Downloads\project\s252-evidence\ci-step-14.txt`; exit **0**.

```text
Detect secrets...........................................................Passed
```

**Step 15:** `uv run python scripts/check_untracked_secrets.py`, redirected to
`C:\Users\yury_\Downloads\project\s252-evidence\ci-step-15.txt`; exit **0**.

```text
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 6 new file(s)
```

**Final fixture compatibility proof:** The original seven-case `CASES` export is unchanged;
only the payload suite joins the six S252 cases. No edit to `tests/test_poll_same_work.py`.
`uv run pytest --no-cov -q tests/test_poll_same_work.py tests/test_poll_payloads.py` plus the four
new agent-local test modules, redirected to `s252-evidence/green-a2-shared.txt`; exit **0**:

```text
...........................................                              [100%]
43 passed in 8.91s
```

**Commit hook isolation:** The shared hook points at main's venv. Its copy in
`s252-evidence/hooks/` changes only `INSTALL_PYTHON` to this worktree's interpreter.
The commit uses `git -c core.hooksPath=C:/Users/yury_/Downloads/project/s252-evidence/hooks commit`;
all configured hook checks stay enabled. The shared hook, Git configuration and main venv are untouched.

**`make gate-ran`:** owed to the planner.

**Not met / verified failing:** Not done: PATCH bump, `uv lock`, push, remote gate, CodeQL diff, merge, deployment, F1/F2 and any byte measurement. They are explicitly the planner's. `pyproject.toml`'s version and `uv.lock` are untouched. Dependency audit: NOT RUN to completion (offline lookup refused); full `make ci` exit 0 is not done. Steps 14/15 passed separately after the gate stopped.

---

## Return notes

- Scope held: only discovery changes in the five source modules; forecast, settle, review, execute,
  broker sync and snapshot adoption code unchanged. The unused snapshot-side marker predicate was
  removed with that discovery path. No forbidden path, graph vocabulary, env key or tunable moved.
- Reading changed the monitor plan's old drift suggestion: snapshot-side discovery still fetches
  permanently unconsumed snapshots. Use the RunRequest side; retry the existing half-marker branch.
  The request-order result is explicitly pinned even when snapshot insertion order differs.
- Whole execution book confirmed the submit-trigger silence; DRIFT-100 records it. The old
  `EXEC-TRG-02` primary-pub/sub qualifier is reported and left unamended, as required by scope.
- Follow-up whole-label reads: forecaster settlement's claim/settlement ledger per work item,
  execution's fill/stop reads in `filled_entry_stops.py`, `fill_attempts.py` and
  `reconciliation_store.py`, and the monitor's `reconcile.py` position-book reads. They run with
  work; measure their cadence and payload before scheduling another conversion. The other
  paths the spec names (analyst outcome backfill, PM snapshot, reporter performance inputs) are
  untouched and should be reviewed separately with their owning laws.
- Parallel-main movement: S253 advanced local main independently to
  `d8949a320751967f8f42b0b8dfc7219ad6cc809c` (`0.121.02`) during this build.
  This branch and its proof remain based on `ae54cf3591bc3312d6f7056cfd79a4a888675613`
  (`0.121.01`). The main checkout is clean; this builder made no main commit or merge.
  Planner integration must preserve S253 and reconcile shared documentation before release CI.
- No live proof or transfer saving is inferred from the memory-store spy. Planner owns PATCH,
  re-lock, full release CI, remote gate/CodeQL, F1 on Neon, merge, retag after the fidelity verdict,
  then F2. The final handback commit SHA is reported with the delivered branch handback; it is
  resolved by `git -C ../ta-s252 rev-parse HEAD` after this evidence is committed.

---

## Planner's closeout — 2026-10-02

**Result: MERGED.** `main` was fast-forwarded to `dd22b348`, so the merged SHA is the gated SHA; tag
`v0.121.03`. Not deployed: the retag waits for the fidelity verdict.

- **Handback:** complete against the thirteen-item checklist, with the one step the sandbox could
  not run named as not run. Scope held: the five finder modules change discovery only; nothing
  under `kernel/`, `contracts/`, or the analyst, reporter, scanner, PM and provider agents;
  `PayloadSpy` is byte-identical to S242's after the fixture split.
- **Rebase.** The branch was cut at `ae54cf35` and S253 merged while it was built. Rebased onto
  `d8949a32`: six shared docs conflicted (design log, both law rollups, both sprint tables,
  `STATE.md`). The tables were merged row by row, each row taken from the side that changed it;
  DL-261 sits between DL-262 and DL-260; `STATE.md` was taken from `main`. No code conflicted.
- **🔴 The handback's `mypy` PASS did not reproduce.** `uv run mypy` fails on the handback's own
  commit `f7ffb756`, in the same venv, with one error: `tests/poll_payload_support.py`,
  `FrozenDatetime.now` returned `datetime` where `datetime.now` returns `Self`. The builder's
  evidence file shows `Success: no issues found in 1147 source files`; why it passed there was not
  established. It would have failed the remote gate. Fixed at merge (the clock builds an instance of
  its own class from the pinned instant; the file is 100 lines), not returned: two lines in a test
  helper.
- **Rollup rows.** The four rows the sprint touched in `docs/laws/INDEX.md` named the previous
  sprint beside the new version, and in `ledger.md` put the sprint's sentence before the proven
  count; both now follow the other rows.
- **Bump and lock:** `0.121.02` → `0.121.03`; `uv lock` changed one line, the project's version.
- **Windows `make ci`:** redirected to a file, exit 0, all fifteen steps: 3,966 passed, 8 skipped,
  coverage 100.00 %, the dependency audit run with the network (clean, one accepted advisory),
  detect-secrets passed.
- **`make gate-ran`:** from the worktree at the branch's `HEAD`; `GATE PROVEN` for `dd22b348`
  (CI, CodeQL, Security Findings), the printed SHA equal to `git rev-parse HEAD`.
- **CodeQL:** the first push (`376ede39`, itself `GATE PROVEN`) showed 132 open alerts against 131
  on the last merged branch (`sprint-253-a-runs-snapshot-counts-what-the-broker-filled`): one new
  note, `py/unused-import`, a `PayloadSpy` re-export the fixture split left in
  `tests/poll_payload_fixtures.py` for a single importer. The gate cannot see it (it reads `main`'s
  alerts). Fixed, not dismissed: the test imports the spy from the module that defines it. The
  merged commit's alerts are the same 131, compared as sets.
- **F1 PASS**, before the merge ([functionality-checks](../laws/functionality-checks.md)). The six
  finders from `main` and from the branch, each run against the live graph through a store that
  counts every payload it returns and raises on a write:

  | Scenario | Comparisons | Pending sets | One idle poll reads, before → after |
  | --- | --- | --- | --- |
  | One idle poll now, six finders | 6 | 0 = 0, all six | forecaster 12.47 MB → 0; deliberator 4.72 MB → 0; execution 1.08 MB → 0; monitor 0.42 MB → 0 |
  | The forecaster's two finders at five real past instants, at one instant exactly 24 h after a run, and with no clock | 14 | equal, same order (up to 73 and 77 runs pending) | with a clock, only the runs inside the 24 h are fetched |
  | Deliberator and execution submit: each of the last five `PMRun`s made pending again, then all five | 12 | equal, same order | deliberator 4.5–4.7 MB → 4–41 KB a run |
  | Execution sync and monitor sync: five past `RunRequest`s made pending again, then all five | 12 | equal, same order | monitor 0.42 MB → 3–4 KB a run |

  "After" excludes the key query itself (a list of keys, empty when idle). The four finders that
  take no clock have no past instant to ask for, so a past state was made by hiding one run's
  processed edge from the store's answers. 0 live writes.
- **Where this spec was wrong.** (1) F1 asked for "five past instants" of all six finders; four take
  no clock, and the spec did not say how a past state would be produced. (2) The CodeQL baseline
  named `sprint-251-…`; the last merged branch at merge time was S253's.
- **Owed:** the image-only retag, not before `sched-2026-10-07` has run and the fidelity verdict is
  read; then **F2** on the first scheduled run after it (8 / 8, and `RxBytes` for forecaster,
  deliberator-manager, execution and monitor down by at least a factor of ten from 2,295, 1,021, 403
  and 143 MB).
