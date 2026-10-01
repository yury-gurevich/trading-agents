<!-- Agent: planning | Role: sprint handover -->
# Sprint 252 — every pending-work finder in the fleet fetches only its pending work

**Phase:** Etalon-first continuous improvement (DL-19) · work-queue 101 and 106 (DRIFT-097)
**Branch:** `sprint-252-every-finder-fetches-only-its-pending-work`
**Status:** SPEC
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

- [ ] All six finders pass the payload spy (A1) with the pending sets they had before (A2), bar the two named differences (A4 e, and the second-snapshot case).
- [ ] The completeness guard counts thirteen finders and fails on a fourteenth with no case (A8, plant 4).
- [ ] No file under `kernel/`, `contracts/`, or the analyst, reporter, scanner, PM or provider agents changed.
- [ ] Law cycle done: `MON-TRG-02`, `FORE-TRG-01`, `DLIB-TRG-01`, `EXEC-TRG-07` amended, `EXEC-TRG-08` added (or the existing clause amended, stated), four Changelog lines, test-plan rows, both rollups, DRIFT-097 `CORRECTED`, DRIFT-100 filed `CORRECTED`.
- [ ] DL-261 written with the decisions and their rejected alternatives.
- [ ] Each of the four plants red, pasted, restored.
- [ ] Every touched module < 200 lines; the fixtures file split.
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
| *builder fills* | *builder fills* | *builder fills* | *builder fills* |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *builder fills*

**Contradictions found between a law and this spec:** *builder fills*

**Laws found silent where a decision was needed:** *builder fills*

**Clauses that were ⬜ and are now proven:** *builder fills*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | *builder fills* | *builder fills* | *builder fills* | *builder fills* |

**Tests added beyond the plan:** *builder fills*

**Existing tests edited, and why:** *builder fills*

---

## Closeout — evidence

**Status:** *builder fills*

**Tree the proofs ran in (and `.env` present?):** *builder fills*

**Result:** *builder fills*

**Files changed:** *builder fills*

**Design decisions:** *builder fills*

**Proof — the red run first:**

```text
builder fills
```

**Proof — the green run:**

```text
builder fills
```

**Guards planted:** *builder fills*

**Module line counts:** *builder fills*

**`make ci`:** *builder fills*

**`make gate-ran`:** owed to the planner.

**Not met / verified failing:** *builder fills*

---

## Return notes

- *builder fills*
