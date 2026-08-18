<!-- Agent: supervisor | Role: sprint spec — give faults a retirement path so `healthy` can return to true -->
# S179 — a fault must be able to stop being an incident

**Closes:** work-queue item 19 · **Opens from:** `/diagnose-run` + the `probe-s178-flaglifecycle`
run, 2026-08-18 · **Type:** fix ·
**Target version:** next available PATCH at merge — **do not pin it in this file** ·
**Branch:** `sprint-179-a-fault-must-be-able-to-stop-being-an-incident`

> Handover to a delegated coding agent. Everything under **Measured** was read off this repo or the
> live spine on **2026-08-18**. Everything marked **Assumed** has **not** been verified — check it
> before building on it. Do not treat an unmarked claim as measured.

## Why

S178 made `pending_human_flags` able to fall, and it did: **46 → 0**. `healthy` **still** did not go
green, because it has two locks and S178 only opened one.

```python
# agents/supervisor/domain/health.py:32,42
open_incidents = sum(1 for node in faults if node.props.get("status") != "resolved")
"healthy": open_incidents == 0 and critical_flags == 0,
```

**Measured on the live spine, 2026-08-18:**

| Fact | Value |
| --- | --- |
| `Fault` nodes | **6119** |
| Their `status` values | `pending` × **6119** — every single one |
| `FaultResolution` nodes | **0** — the label does not exist |
| `FaultSuppression` nodes | **0** — the collapse machinery has never produced one |
| `open_incidents` | **6119** |
| `healthy` | **`false`** |

**The defect in one line: nothing in the codebase ever writes `status="resolved"` on a `Fault`.**
There are exactly two writers, and neither can produce that value:

- `kernel/fault_graph.py:75` → `_fault_props` hardcodes `"status": "pending"` (line 118).
- `agents/supervisor/store.py:54` → `write_fault` writes **no `status` prop at all**, so those
  faults read `None`, which is also `!= "resolved"`.

So `open_incidents` is **monotonically non-decreasing by construction**. Once the system has
recorded its first fault, `healthy` can never be `true` again for the lifetime of the graph. It is
not reporting a system in trouble; it is reporting that a system once had trouble.

### 🪤 Correction — the recurrence is *not* the bug. Do not "fix" it.

An earlier reading of this called the per-run repetition a dedupe failure, by analogy with the S178
flag bug. **That was wrong, and building on it would break a deliberate design.** `fault_node_key`
is keyed by `occurred_at` on purpose — its own docstring says so:

> *"Keyed by origin plus timestamp so a repeated failure appends rather than overwriting the earlier
> occurrence — a fault that recurs every run is itself the signal."*

`FaultCollapsePolicy.collapse_window_seconds`'s `why` says the same: it bounds *one storm* while
"preserving recurrence across separate fleet runs as distinct `Fault` nodes". **Recurrence is the
signal. Leave the keying alone.** The problem is only that an all-time counter drives a live boolean.

### The backlog is not what the number suggests

**5762 of 6119 (94 %) are a single closed incident.** One message — `property 'broker_status' cannot
be overwritten` (`ValueError`, `agents.execution.poll`, capability `position_sync`) — confined to
**2026-07-30 (4125)** and **2026-07-31 (1637)**, and **never seen since**. Whatever caused it stopped
two and a half weeks ago.

**The live rate is ~12–14 per run**, measured on `probe-s178-flaglifecycle`: 12 × `stop identity
mismatch` (`agents/execution/drop_sweep_records.py:76`) on stale stop `Fill` nodes, plus one
untracked `probe-s164` order (`drop_sweep_records.py:131`), plus incidental run-specific ones.

### 🪤 The collapse machinery has never fired in production

`FaultSuppression` = **0** on the spine, despite a 3600 s collapse policy existing and being
tunable. **Measured cause:** `GraphFaultSink._windows` is an **in-process dict**, and the fleet
scales to zero between runs, so a window never survives long enough to flush. **Assumed, not
verified:** that this is unintended. Decide explicitly — it may be exactly right, since the policy's
stated purpose is bounding a storm *within* a run.

## The design decisions this sprint has to make

**1 · What retires a fault?** 🚨 **Recommended: mirror S178/DL-111 exactly** — an append-only
`FaultResolution` node joined to the `Fault`, never mutating the `Fault` itself. That pattern is
already proven here, and it keeps the record intact.

- *Rejected:* **set `status="resolved"` on the `Fault`.** It mutates an append-only record, and the
  graph store's `_append_props` **will raise** `ValueError: property 'status' cannot be overwritten`
  — which is, with some irony, the exact error that produced 94 % of this backlog.
- *Rejected:* deleting old faults. Destroys the evidence the sink exists to preserve.

**2 · What is allowed to retire one, and on whose authority?** This is the hard half. A `Flag` names
a condition you can re-observe ("is the book still divergent?"); most faults name an *event* that
already happened, with nothing to re-check. Options, pick and justify:

- **Age/rotation** — a fault older than N runs stops counting as a live *incident* while remaining
  in the graph. Simple, needs no per-fault semantics.
- **Run-scoping** — `open_incidents` counts only faults from the latest run (or last N).
- **Explicit operator retirement** — an `acknowledge` capability. Honest, but 6119 of them.

🚨 **Recommended: run-scope or window the count, and there is precedent in-repo** —
`surfaces/dashboard/projections_state.py:_in_scope` already does this for the dashboard:
*"run-scoped = created on the run's day; anything still pending/open rides too."* Reuse the idea
rather than inventing a second convention.

**3 · Should `healthy` stay a single all-time boolean?** **Assumed, not measured:** that it should.
A boolean that has been `false` for six weeks carries no information. Consider whether
`MasterReport` should carry the count *and* its scope, so "3 faults in the last run" is
distinguishable from "6119 since July".

**4 · The ~12/run stop-identity leak — defect or correct reporting?** Measured: `broker_stop=True
graph_stop=False` on ~12 stale stop `Fill` nodes (BMY, MDT, ABT, USB, WFC, PYPL, HPE, SCHW, BAC,
CSCO, AVGO, AMZN). 🚨 **Determine this on its own evidence and do not silence it as a side effect of
the health fix.** If the condition is real, the fault is correct and the *health model* is what
needs to change. If the stop nodes are stale, they need cleaning and that is a separate change.

## Blast radius — measured

🚨 **There are TWO independent copies of the same predicate, and they must move together:**

- `agents/supervisor/domain/health.py:32` → `MasterReport` → `surfaces/mcp_tools.py`
- `surfaces/queries/health.py:31-34` → `system_health()` → the dashboard

Both compute `!= "resolved"` and both derive `healthy = <faults> == 0 and critical_flags == 0`.
Change one only, and the MCP surface and the dashboard will disagree about whether the system is
healthy — with no test failing.

🟢 **`orchestration/packs/trading_acceptance.py` reads neither field** — verified by grep, 0 hits for
`healthy` and `open_incidents`. **Changing this cannot fail a run or block a trade.** It is a
reporting-surface fix, exactly as S178 was.

## Steps, in order

1. **Reproduce as a failing test:** a graph with one old fault and one from the current run must not
   report the same `open_incidents` as a graph with two current faults.
2. **Record the decision** (decisions 1–3) in `docs/design-log.md` with rejected alternatives,
   **before** applying it. LAW-06.
3. **Implement retirement/scoping**, changing **both** copies of the predicate.
4. **Handle the 5762-fault closed incident** — under whatever model you chose, prove it stops
   counting as a live incident without being deleted.
5. **Prove on the live spine:** `open_incidents` and `healthy` quoted **before and after**, and
   `healthy` observed **`true`** at least once. 🪤 `make ci` cannot prove this one.
6. `make ci` green, **plant each new guard and watch it fail**, restore.

## Success factors

- [ ] `healthy` observed **`true`** on the live spine at least once — the whole point.
- [ ] `open_incidents` before and after, both quoted, measured on the spine.
- [ ] No `Fault` node deleted, and none mutated — the 6119 records still readable afterwards.
- [ ] **Both** predicate copies changed; a test asserts `health.py` and `surfaces/queries/health.py`
      agree on the same graph.
- [ ] The per-occurrence `fault_node_key` keying is **unchanged** — recurrence still appends.
- [ ] The stop-identity question answered on evidence, either fixed or explicitly deferred with a
      reason. Not silenced.
- [ ] Decision recorded in `docs/design-log.md` with rejected alternatives.
- [ ] Each new guard **planted, watched to fail, restored** — stated per guard.
- [ ] `make ci` exit 0, 100.00 % coverage.

## Traps

🪤 **Two copies of the predicate.** Listed above. This is the one that will silently half-ship.

🪤 **Do not touch `fault_node_key`.** Per-occurrence append is deliberate and documented. See the
correction above.

🪤 **`write_fault` in `agents/supervisor/store.py:41-50` writes no `status` prop at all.** Any
status-based scheme must treat `None` and `"pending"` identically, or supervisor-path faults will
behave differently from kernel-path ones.

🪤 **Mutating a `Fault` will raise.** `kernel/graph_support.py:86` `_append_props` refuses to
overwrite a property with a different value. Resolution must be a *new node*, not an edit.

🪤 **Module sizes** (hard block 200, warn 150): `agents/execution/drop_sweep_records.py` = **178**,
`agents/supervisor/store.py` = **162**, `surfaces/queries/health.py` = **72**,
`agents/supervisor/domain/health.py` = **59**. Split before adding to the first two. No `# noqa`.

🪤 **A script run from a git worktree silently gets the in-memory store and reports `0`.** A
worktree has no `.env` (gitignored). S178 hit this exactly — its sweep dry-run reported
`healthy=True, pending_human_flags=0`, which was a lie. Run spine checks from the **main worktree**,
and copy the guard from `scripts/sweep_divergence_flags.py`, which refuses rather than reporting a
zero it cannot stand behind. **Never copy `.env` into a worktree** — CLAUDE.md forbids credentials
as files in the repo tree.

🪤 **`healthy` needs *both* locks open.** If any `critical` Flag is unresolved when you measure,
`healthy` stays `false` no matter how perfect the fault half is. Check `pending_human_flags` is
still 0 before concluding your change failed.

## Handover — paste this to Codex

```text
Work item: S179 - a fault must be able to stop being an incident.
Repo: trading-agents. Read docs/sprints/sprint-179-a-fault-must-be-able-to-stop-being-an-incident.md
in full before writing anything. Read CLAUDE.md. Read docs/INDEX.md before opening any docs folder.

WHAT IS WRONG
healthy has been false since 2026-07-08. S178 fixed one of its two locks (pending_human_flags is now
0). The other lock cannot open at all. Measured on the live spine 2026-08-18: 6119 Fault nodes, ALL
with status="pending", 0 FaultResolution nodes, 0 FaultSuppression nodes, open_incidents=6119.

agents/supervisor/domain/health.py:32 counts faults whose status != "resolved", and NOTHING in the
codebase ever writes "resolved". Two writers only: kernel/fault_graph.py:75 hardcodes
status="pending" (line 118), and agents/supervisor/store.py:54 writes no status prop at all. So
open_incidents only ever grows and healthy can never return to true.

DO NOT "FIX" THE RECURRENCE. fault_node_key is keyed by occurred_at deliberately - its docstring
says "a repeated failure appends rather than overwriting the earlier occurrence - a fault that
recurs every run is itself the signal." An earlier analysis wrongly called this a dedupe bug.
Leave the keying alone. The problem is that an ALL-TIME counter drives a LIVE boolean.

CONTEXT ON THE BACKLOG
5762 of 6119 (94%) are ONE closed incident: ValueError "property 'broker_status' cannot be
overwritten", agents.execution.poll, capability position_sync, confined to 2026-07-30 (4125) and
2026-07-31 (1637), never seen since. The live rate is ~12-14 per run, mostly "stop identity
mismatch" from agents/execution/drop_sweep_records.py:76.

WHAT TO DO
1. Failing test first: an old fault and a current fault must not count the same as two current ones.
2. Record the design decision in docs/design-log.md WITH rejected alternatives, before applying.
3. Retirement must APPEND a FaultResolution node (mirror S178/DL-111). Do NOT set status on the
   Fault - kernel/graph_support.py:86 will raise "property 'status' cannot be overwritten", which is
   the very error that generated 94% of this backlog. Do not delete faults.
4. Recommended model: run-scope or window open_incidents. Precedent already in-repo at
   surfaces/dashboard/projections_state.py:_in_scope ("run-scoped = created on the run's day;
   anything still pending/open rides too"). Reuse it rather than inventing a second convention.
5. Prove on the live spine: quote open_incidents and healthy BEFORE and AFTER, and show healthy
   observed true at least once. make ci cannot prove this - it needs the real graph.
6. make ci green. Plant EVERY new guard, watch it fail, restore. Report each plant in the closeout.

CRITICAL CONSTRAINTS
- THERE ARE TWO COPIES OF THE PREDICATE. agents/supervisor/domain/health.py:32 (-> MasterReport ->
  surfaces/mcp_tools.py) and surfaces/queries/health.py:31-34 (-> dashboard). Both must change
  together or the MCP surface and the dashboard will disagree with no test failing.
- agents/supervisor/store.py write_fault writes NO status prop, so those faults read None. Treat
  None and "pending" identically.
- Module sizes: drop_sweep_records.py=178, supervisor/store.py=162. Hard block 200, CI fails at it.
  Split before adding. No # noqa.
- A script run from a git worktree gets the in-memory store and reports 0 - a worktree has no .env.
  S178's sweep dry-run reported "healthy=True, pending_human_flags=0" and it was a lie. Run spine
  checks from the MAIN worktree and copy the refuse-on-in-memory guard from
  scripts/sweep_divergence_flags.py. NEVER copy .env into a worktree.
- healthy needs BOTH locks open. Confirm pending_human_flags is still 0 before concluding failure.
- The ~12/run stop-identity mismatch: decide on its own evidence whether it is a real defect. Do NOT
  silence it as a side effect of the health fix.
- trading_acceptance.py reads neither healthy nor open_incidents (grep: 0 hits), so this cannot fail
  a run. Verify that is still true before relying on it.
- Branch sprint-179-a-fault-must-be-able-to-stop-being-an-incident. Version: next available PATCH at
  merge, do not pin it. Fill in the Closeout block at the bottom of the spec before handing back.
```

## Closeout — evidence

<!-- FILL THIS IN BEFORE HANDING BACK. A handback with this placeholder intact is not accepted. -->

**Result:** *not yet implemented.*

**Files changed:** *...*

**Design decisions:** *retirement/scoping model + rejected alternatives as a DL entry, linked.*

**Live-spine proof:** *`open_incidents` and `healthy` before and after; `healthy` observed `true`;
confirmation that no `Fault` was deleted or mutated.*

**Both predicates:** *evidence that `health.py` and `surfaces/queries/health.py` agree.*

**Stop-identity question:** *answered or explicitly deferred, with the reason.*

**Guards planted:** *per guard: what was planted, that it failed, that it was restored.*

**`make ci`:** *exit code, passed/skipped counts, coverage %.*
