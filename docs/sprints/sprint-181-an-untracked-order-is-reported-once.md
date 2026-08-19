<!-- Agent: execution | Role: sprint spec — an untracked terminal broker order must report once, not every run -->
# S181 — an untracked broker order is reported once, not every night

**Closes:** work-queue item 23 · **Opens from:** the `sched-2026-08-18` run diagnosis, 2026-08-19 ·
**Type:** fix ·
**Target version:** next available **PATCH** at merge — **do not pin it in this file** ·
**Branch:** `sprint-181-an-untracked-order-is-reported-once`

> Handover to a delegated coding agent. Everything under **Measured** was read off this repo, the
> live spine or the Alpaca paper account on **2026-08-19**. Everything marked **Assumed** has **not**
> been verified — check it before building on it. Do not treat an unmarked claim as measured.

## Why

**S179 turned `healthy` green on 2026-08-18. The very next run turned it red again, over one
canceled test order from 2026-08-07.**

**Measured — the single live incident on the spine, 2026-08-19.** `live_fault_incidents(graph)`
returns exactly **one** node:

```text
error · execution · agents.execution.drop_sweep · UntrackedOpenOrder
open order stop:probe-s164:T#1 for T has no Fill chain; durable drop lineage was not recorded
occurred_at 2026-08-18T22:30:33.158857+00:00
```

**Measured — what that order actually is.** An Alpaca paper order left behind by S164:

```json
{"id": "e5e6edcc-1853-49cf-8086-e9fed687ad24", "client_order_id": "stop:probe-s164:T#1",
 "symbol": "T", "side": "buy", "type": "limit", "qty": "1", "status": "canceled",
 "submitted_at": "2026-08-07T08:50:21.582865Z", "canceled_at": "2026-08-07T08:50:22.271403Z",
 "filled_qty": "0"}
```

A one-share probe, canceled 0.7 s after it was submitted, with **no `Fill` node in the graph**.

**Measured — it has fired on every run since.** **12** identical `Fault` nodes, first
`2026-08-08T05:27`, latest `2026-08-18T22:30`, one per run:
`08-08 ×4 · 08-10 · 08-11 · 08-12 · 08-13 · 08-14 · 08-17 · 08-18 ×2`.

**Measured — it is the only one.** The production query returns **197** orders. **192** are
"pipeline-owned" by the current predicate; **103** of those are terminal (`canceled`/`expired`);
of those 103, exactly **1** has no `Fill` chain — this order.

### The mechanism, measured in code

1. [`alpaca.py:154-157`](../../agents/execution/alpaca.py#L154-L157) — `_list_orders()` queries
   `status=all&limit=500`. Only 197 orders exist, so a 2026-08-07 order is **well inside** the
   window and stays there.
2. [`alpaca_orders.py:104-110`](../../agents/execution/alpaca_orders.py#L104-L110) — Alpaca
   `canceled` is not `filled`/`partially_filled`/pending, so it maps to
   `BrokerFill(status="rejected", reason="canceled")`.
3. [`drop_sweep.py:111-113`](../../agents/execution/drop_sweep.py#L111-L113) — `_pipeline_owned` is
   `key.startswith("exit:") or key.count(":") >= 2`. `stop:probe-s164:T#1` has two colons, so the
   sweep **claims it**.
4. [`drop_sweep.py:116-118`](../../agents/execution/drop_sweep.py#L116-L118) — `_already_dropped`
   reads `fill.props["drop_reason"]`. There is no `Fill` node, so this is `False`. **This is the
   hinge: the only memory the sweep has lives on a node that does not exist.**
5. [`drop_sweep.py:127-135`](../../agents/execution/drop_sweep.py#L127-L135) — `_is_stop_order`:
   the broker type is `limit`, and no `BrokerStopOrder` matches, so `broker_stop == graph_stop ==
   False`. Not exempt, and no mismatch fault. (The `stop:` prefix in the key is a red herring.)
6. [`drop_sweep.py:145-149`](../../agents/execution/drop_sweep.py#L145-L149) — `_is_resolved_drop`
   is `True` (`rejected` + reason `canceled`), so `record_drop(..., fill=None, "canceled")`.
7. [`drop_sweep_records.py:34-36`](../../agents/execution/drop_sweep_records.py#L34-L36) —
   `fill is None` → `_record_untracked_drop` → **`severity="error"`** → `return False`.

**Nothing on that path writes anything.** State is unchanged, so the next run walks the identical
path and reaches the identical conclusion. The fault is not an event; it is **a permanent property
of the broker's order history**, re-announced nightly.

### Why it matters now and not before

[`kernel/fault_incidents.py:30-34`](../../kernel/fault_incidents.py#L30-L34) — since S179, an
unresolved `error` Fault in the latest graph-run day sets `healthy=false`. Before S179 this was one
line in an all-time tally of 6,119; after S179 it is **the single thing keeping the fleet red**.
`healthy` was true for roughly fifteen hours.

🟢 **Reporting-only.** Acceptance reads neither `healthy` nor `open_incidents`, and the sweep
already exempts and continues. No trade is affected either way.

## Four exits that do not work — do not spend time on them

🪤 **You cannot tear down the artifact.** The probe is already `canceled` — terminal and immutable
at Alpaca. There is no broker-side delete. The standing "tear down test artifacts at sprint close"
rule has **no move available** here, which is exactly why this needs a code fix.

🪤 **S179's `FaultResolution` sweep does not fix it.** That retires the fault already written; the
next run writes a new one under a new `occurred_at` key. Retirement is downstream of an emission
that has not stopped. (You will still want one such resolution — see step 5 — but as cleanup, not
as the fix.)

🪤 **It "fixes itself" eventually, and that is worse.** Once 500 newer orders push the probe out of
the `limit=500` window the error vanishes. Health would then flip green on **order volume**, not on
anything becoming true.

🪤 **Tightening `_pipeline_owned` by string shape cannot work.** `stop:probe-s164:T#1` is shaped
exactly like the live `stop:41995c05a31800d7:BMY`. Nothing but a human distinguishes a hash from
the word `probe`.

## The design decisions this sprint has to make

**1 · What makes the report stop?** 🚨 **Recommended: remember the acknowledgement durably**, so
the error fires on **first sight of a given broker order** and never again. This keeps the signal —
a genuinely new lineage hole is real and still deserves an error, once — while removing its
permanence.

- *Rejected:* **demote `UntrackedOpenOrder` to `warning`.** Cheapest, and S179 already made warnings
  non-blocking, so it would go green tonight. But a `Fill` missing for an order the pipeline really
  did place is a real defect, and this silences that class permanently. It treats the symptom
  (health is red) rather than the defect (the check has no memory).
- *Rejected:* **skip terminal orders older than N days.** A time cutoff hides holes that arrive
  late, and adds a second unrelated policy knob to tune.
- *Rejected:* **exclude no-Fill orders from `_pipeline_owned`.** That is identical to never
  reporting them — it deletes the check rather than fixing it.

**2 · Where does the memory live — and does it move the vocabulary pack?** Two shapes, and this is
the decision with real consequences:

- **(a) A new label** (e.g. `UntrackedOrderAck`, keyed by the broker idempotency key). Clean and
  self-describing, but it adds to `orchestration/packs/trading_graph_vocabulary.json` `labels`,
  which means **code and pack must deploy together** — the exact constraint that held S179 back
  ("S179 changes the graph vocabulary pack by adding `FaultResolution`, so a deploy must carry code
  and pack together").
- **(b) Reuse `BrokerOrderStatus`** — already in the pack (`trading_graph_vocabulary.json:12`),
  already the drop-evidence node. No pack move. 🪤 But it is keyed today as
  `broker-order-status:{fill.key}:drop:{ts}` and written with a `REFRESHES` edge **to the Fill**
  ([`drop_sweep_records.py:46-59`](../../agents/execution/drop_sweep_records.py#L46-L59)) — neither
  the key nor the edge exists in this case, so you would be writing an orphan node under a
  non-uniform key. Check the vocabulary **edge** constraints and the S144 write guard before
  choosing.

🚨 **Decide this on what a reader of the graph a year from now can interpret, not on which is less
typing.** Record the choice and the rejected one.

**3 · Is `error` still right for first sight?** Once the sweep can tell "never seen before" from
"seen every night", first sight is genuinely new information and `error` is defensible. Say so
explicitly, or demote it with a reason. Either is acceptable; leaving it undecided is not.

**4 · Is the ack revocable?** If a `Fill` later appears for that key (a repair via
`scripts/repair_orphan_fills.py`), the ack must step aside. 🚨 **Recommended: by construction** —
look for the `Fill` first and consult the ack only when there is still none. **Do not add a delete
path** (DL-94 / append-only spine).

## Blast radius — measured 2026-08-19

| File | Lines | Note |
| --- | --- | --- |
| `agents/execution/drop_sweep.py` | **164** | 🚨 **14 over the 150 warn line already**, 36 from the hard block |
| `agents/execution/drop_sweep_records.py` | **178** | 🚨 **28 over the warn line**, **22 from the hard block** |
| `agents/execution/fill_attempts.py` | 127 | `latest_fill_attempt` reused unchanged |
| `kernel/fault_incidents.py` | 63 | **Unchanged.** Do not touch the S179 predicate |
| `orchestration/packs/trading_graph_vocabulary.json` | — | only if decision 2 picks (a) |

🚨 **Both files you must edit are already past the 150-line warning.** Plan the split **before**
writing, not after `make ci` blocks you. A new `drop_sweep_ack.py` is the obvious home.

**Measured — `broker.fills()` has four other callers.** `agent.py:118`, `reconciliation.py:80`,
`scripts/audit_broker_graph.py:51`, `scripts/repair_orphan_fills.py:67`. 🪤 **The fix belongs in the
sweep, not in the broker client** — narrowing what `fills()` returns would silently change
reconciliation and both repair scripts.

## Steps, in order

1. **Reproduce as a failing test first:** a terminal broker order with no `Fill` chain, swept
   **twice**, must produce **one** `UntrackedOpenOrder` fault, not two. Assert on the fault count
   from the sink across two sweeps — not on a log line, and not on a single sweep.
2. **Record decisions 1–4** in `docs/design-log.md` with rejected alternatives, **before** applying.
   LAW-06. Use **DL-115** — 🪤 the log has duplicate numbers already (two `DL-110`, two `DL-111`,
   entries prepended at the top *and* appended at the bottom); confirm DL-115 is free before
   claiming it, and put it where the recent ones are.
3. **Implement**, respecting the module-size ceilings above.
4. **Prove it read-only against the real spine before and after.** `live_fault_incidents(graph)`
   returns **1** today, this order. Quote the before count, the after count, and the `Fault` total
   (**6132** on 2026-08-19) to show nothing was mutated or deleted.
5. **Then retire the fault already written** with one `FaultResolution` via S179's append-only path
   (`resolved_by=s181-untracked-order-ack` or similar). The code fix stops the *next* one; it
   cannot unwrite this one. 🪤 Do this **after** the fix is deployed, or the next run re-raises it
   and the cleanup reads as ineffective.
6. `make ci` green, **plant each new guard and watch it fail**, restore.
7. **If decision 2 added a label, code and pack must ship in the same deploy.** Say so in the
   closeout so the deploy is not split.

## Success factors

- [ ] The same untracked terminal order swept twice yields **one** fault, proven by a test.
- [ ] A **new** untracked order still produces an error on first sight — the check is not deleted.
- [ ] If a `Fill` later exists for that key, normal drop evidence is recorded and the ack does not
      suppress it. Test both orders of arrival.
- [ ] An acked order is still **not** counted as dropped — `record_drop` returns `False` today and
      `remember_execution_run` is skipped; `ExecutionRun.dropped` must not change.
- [ ] Decisions 1–4 recorded in `docs/design-log.md` with rejected alternatives.
- [ ] Both edited modules land **under 150 lines**, or the split that keeps them there is in the diff.
- [ ] `live_fault_incidents` on the spine: before/after quoted, `Fault` total unchanged.
- [ ] One `FaultResolution` appended for the existing fault; no Fault mutated, none deleted.
- [ ] Each new guard **planted, watched to fail, restored** — stated per guard.
- [ ] `make ci` exit 0 (**redirected to a file, never piped**), 100.00 % coverage.
- [ ] `make gate-ran` **GATE PROVEN**, run from the worktree whose `HEAD` is the commit being proven,
      with the printed SHA checked against `git rev-parse HEAD`.

## Traps

🪤 **Do not touch the `occurred_at` fault keying.** S179 established that recurrence is deliberate —
`fault_node_key` is keyed by `occurred_at` on purpose. The fix is to stop *deciding* to emit, not to
make the emission collide.

🪤 **Do not touch `kernel/fault_incidents.py`.** S179 shipped it eighteen hours ago and there are
**two copies of the health predicate** (`agents/supervisor/domain/health.py:33` and
`surfaces/queries/health.py:32`) that must always agree. This sprint has no business in either.

🪤 **A script run from a git worktree silently gets the in-memory store** — a worktree has no `.env`
(gitignored), and every count then reads 0. Copy the refuse-on-in-memory guard from
`scripts/sweep_divergence_flags.py`. **Never copy `.env` into a worktree** — CLAUDE.md forbids
credentials as files in the repo tree.

🪤 **`scripts/` appears to be outside the coverage floor** (S178 added a script and CI still read
100.00 %). **Assumed, not verified.** Keep the testable logic in a module with `scripts/` a thin
entry point.

🪤 **The 26 `BrokerStopIdentityMismatch` warnings in the same sweep are work-queue item 20, not this
sprint.** They come from the adjacent branch at `drop_sweep.py:127-135` and are warning-level, so
S179 already stopped them pinning health. Resist bundling: this sprint's before/after is a fault
count, and mixing in a second fault class ruins it.

## Handover — paste this to Codex

```text
Work item: S181 - an untracked broker order is reported once, not every night.
Repo: trading-agents. Read docs/sprints/sprint-181-an-untracked-order-is-reported-once.md in full
before writing anything. Read CLAUDE.md. Read docs/INDEX.md before opening any docs folder.

WHAT IS WRONG
The head-of-run drop sweep re-raises an identical error-severity Fault every single run for one
broker order it can never resolve, and since S179 that one fault pins healthy=false for the whole
fleet. healthy went true on 2026-08-18 and was false again at the next run.

The order is a leftover S164 test probe at Alpaca: client_order_id stop:probe-s164:T#1, symbol T,
buy, LIMIT (despite the "stop:" prefix), qty 1, submitted 2026-08-07T08:50:21Z, canceled 0.7s
later, filled_qty 0, broker id e5e6edcc-1853-49cf-8086-e9fed687ad24. It has NO Fill node.

The loop, measured in code:
- alpaca.py:154-157 lists status=all&limit=500. Only 197 orders exist, so a 2026-08-07 order stays
  in the window indefinitely.
- alpaca_orders.py:104-110 maps Alpaca "canceled" to BrokerFill(status="rejected",
  reason="canceled").
- drop_sweep.py:111-113 _pipeline_owned is key.count(":") >= 2, so the sweep claims it.
- drop_sweep.py:116-118 _already_dropped reads fill.props["drop_reason"] - there IS no Fill node,
  so it is always False. THIS IS THE HINGE: the only memory the sweep has lives on a node that
  does not exist.
- drop_sweep.py:145-149 _is_resolved_drop is True, so record_drop(..., fill=None, "canceled").
- drop_sweep_records.py:34-36 -> _record_untracked_drop -> severity="error" -> return False.
Nothing on that path writes anything, so the next run repeats it exactly. 12 identical Faults
since 2026-08-08, one per run.

Measured: of 197 broker orders, 192 are pipeline-owned, 103 of those are terminal, and exactly 1
has no Fill chain - this one.

FOUR EXITS THAT DO NOT WORK - do not spend time on them
- You CANNOT tear down the artifact. The order is already canceled: terminal and immutable at
  Alpaca. There is no broker-side delete.
- A FaultResolution sweep does not fix it. That retires the fault already written; the next run
  writes a new one under a new occurred_at key.
- It self-heals once 500 newer orders push it out of the window. That is worse, not better -
  health would flip green on order volume.
- Tightening _pipeline_owned by string shape cannot work: stop:probe-s164:T#1 is shaped exactly
  like the live stop:41995c05a31800d7:BMY.

WHAT TO DO
1. Failing test FIRST: the same untracked terminal order swept TWICE must produce ONE fault, not
   two. Assert on the sink's fault count across two sweeps.
2. Record the design decisions in docs/design-log.md WITH rejected alternatives, before applying.
   Use DL-115, but the log has duplicate numbers already (two DL-110, two DL-111) - confirm it is
   free first.
3. Give the check a durable memory so the error fires on FIRST SIGHT of a broker order and never
   again. Do NOT just demote it to warning - that silences every future lineage hole, and a
   missing Fill for an order the pipeline really placed is a real defect.
4. DECIDE and record: new label (e.g. UntrackedOrderAck) vs reusing BrokerOrderStatus. A new label
   moves orchestration/packs/trading_graph_vocabulary.json, which means code and pack must deploy
   TOGETHER (the constraint that held S179 back). Reusing BrokerOrderStatus avoids the pack move
   but writes an orphan node under a non-uniform key, because its REFRESHES edge points at a Fill
   that does not exist. Decide on what a reader of the graph a year from now can interpret.
5. The ack must step aside if a Fill later appears for that key - check the Fill first, consult
   the ack only when there is still none. Do NOT add a delete path.
6. Prove read-only on the spine before and after: live_fault_incidents(graph) returns 1 today;
   quote before, after, and the Fault total (6132 on 2026-08-19) to show nothing was mutated.
7. AFTER the fix is deployed, append ONE FaultResolution via S179's path for the fault already
   written. The code fix stops the next one; it cannot unwrite this one.
8. make ci green, REDIRECTED TO A FILE not piped. Plant EVERY new guard, watch it fail, restore.
   Report each plant in the closeout.

CONSTRAINTS
- Both files you must edit are ALREADY over the 150-line warning: drop_sweep.py is 164,
  drop_sweep_records.py is 178 (hard block is 200). Plan the split before writing. A new
  drop_sweep_ack.py is the obvious home.
- Do NOT change broker.fills(). It has four other callers - agent.py:118, reconciliation.py:80,
  scripts/audit_broker_graph.py:51, scripts/repair_orphan_fills.py:67. The fix belongs in the sweep.
- Do NOT touch kernel/fault_incidents.py or either copy of the health predicate
  (agents/supervisor/domain/health.py:33, surfaces/queries/health.py:32). S179 shipped that
  eighteen hours ago and the two copies must always agree.
- Do NOT touch the occurred_at fault keying. S179 established that recurrence is deliberate.
- An acked order must still NOT count as dropped: record_drop returns False today and
  remember_execution_run is skipped. ExecutionRun.dropped must not change.
- The 26 BrokerStopIdentityMismatch warnings in the same sweep are work-queue item 20, NOT this
  sprint. Do not bundle them - this sprint's before/after is a fault count.
- A script run from a git worktree silently gets the in-memory store (a worktree has no .env) and
  every count reads 0. Copy the refuse-on-in-memory guard from scripts/sweep_divergence_flags.py.
  NEVER copy .env into a worktree.
- scripts/ appears to be excluded from the 100% coverage floor - VERIFY, and keep testable logic
  in a module with scripts/ a thin entry point.
- This is reporting-only: acceptance reads neither healthy nor open_incidents, and the sweep
  already exempts and continues. No trade is affected. Verify that is still true.
- Branch sprint-181-an-untracked-order-is-reported-once. Version: next available PATCH at merge,
  do not pin it. Push the branch and get `make gate-ran` GATE PROVEN before merging - run it from
  the worktree whose HEAD is the commit, and check the printed SHA. Fill in the Closeout block
  before handing back.
```

## Closeout — evidence

**Status:** implemented on branch `sprint-181-an-untracked-order-is-reported-once` as `0.90.15`.
Branch push / remote gate proof happens after this closeout commit; merge, deploy, and the
post-deploy `FaultResolution` are not claimed here.

**Result:** the drop sweep now writes a durable first-sight acknowledgement for a pipeline-owned
broker order whose `Fill` is missing. The ack is consulted only when no `Fill` exists, so the same
broker order swept twice yields one `UntrackedOpenOrder` error, a different untracked order still
errors on first sight, and a later repaired `Fill` records normal drop evidence. Ack-only orders
still return `False`, so `ExecutionRun.dropped` does not change.

**Files changed:** `agents/execution/drop_sweep.py`; new
`agents/execution/drop_sweep_ack.py`; `agents/execution/drop_sweep_records.py`; new
`agents/execution/tests/test_drop_sweep_ack.py`; `agents/execution/tests/test_drop_sweep_edges.py`;
`docs/design-log.md`; `docs/STATE.md`; `pyproject.toml`; `uv.lock`.

**Design decisions:** recorded as [DL-115](../design-log.md). The sprint keeps first-sight severity
as `error`, uses an edge-less `BrokerOrderStatus` ack with
`lineage_status="missing_fill_ack"` instead of a new vocabulary label, and makes revocation
structural: `Fill` lookup wins before ack lookup. Rejected: warning demotion, age cutoffs, excluding
no-Fill orders from `_pipeline_owned`, a new `UntrackedOrderAck` label for this sprint, and a fake
`REFRESHES` edge to a nonexistent `Fill`.

**Proof:** initial failing test before implementation:
`test_untracked_terminal_order_faults_once_across_sweeps` failed with `2 == 1` Fault nodes. Restored
focused proof: `uv run pytest agents/execution/tests/test_drop_sweep.py
agents/execution/tests/test_drop_sweep_append_safe.py agents/execution/tests/test_drop_sweep_edges.py
agents/execution/tests/test_drop_sweep_ack.py orchestration/tests/test_drop_sweep_cascade.py --no-cov
-q` passed `25 passed`. Edited module sizes: `drop_sweep.py` 137 lines,
`drop_sweep_records.py` 139, `drop_sweep_ack.py` 60, `test_drop_sweep_edges.py` 127,
`test_drop_sweep_ack.py` 120.

**Live-spine read-only proof:** run from the main worktree with `.env` in the gitignored main
checkout and the S181 worktree on `PYTHONPATH`; the guarded script refused in-memory fallback if
`POSTGRES_DSN` was absent. Before dry-run:
`healthy=False`, `open_incidents=1`, `pending_human_flags=0`, `fault_count=6132`,
`fault_resolution_count=2`, one incident: `open order stop:probe-s164:T#1 for T has no Fill chain;
durable drop lineage was not recorded`. After independent read-back:
`healthy=False`, `open_incidents=1`, `pending_human_flags=0`, `fault_count=6132`,
`fault_resolution_count=2`, `live_incident_count=1`, same incident. Nothing was mutated or deleted.

**Post-deploy cleanup:** not done in this branch. The existing live Fault still needs one
append-only `FaultResolution` with `resolved_by=s181-untracked-order-ack` after the fixed code is
deployed; doing it before deploy would let the next run re-emit the incident.

**Reporting-only check:** `rg -n "healthy|open_incidents|live_fault_incidents|compute_health"
scripts/accept.py orchestration agents/execution agents/supervisor/domain/health.py
surfaces/queries/health.py` showed health reads only in supervisor/dashboard health paths, not in
acceptance or execution acceptance flow. `pyproject.toml` coverage source is
`["kernel", "contracts", "agents", "orchestration", "surfaces"]`, so `scripts/` is excluded; no
new script logic was added.

**Guards planted:** repeat-suppression disabled in `_skip_order` -> two-sweep test failed `2 == 1`;
ack key collapsed to a constant -> new-order test failed `1 == 2`; first-sight severity demoted to
warning -> severity test failed `warning == error`; ack allowed to suppress a later `Fill` -> repair
test failed `(0, 0) == (0, 1)`; no-Fill `record_drop` returned `True` -> ack-only dropped assertion
failed `(1, 0) == (0, 0)`; ordinary Fill path forced to write an ack -> Fill-first test failed
`2 == 1`; helper replay forced to rewrite the ack -> append-only guard raised
`ValueError: property 'created_at' cannot be overwritten`. Each plant was restored.

**`make ci`:** final-tree redirected gate
`C:\Users\yury_\AppData\Local\Temp\s181-make-ci-final-tree.txt` exited `0`: `2322 passed, 6
skipped`, `100.00%` coverage, `pip-audit` no known vulnerabilities, detect-secrets tracked and
untracked checks passed.
