<!-- Agent: execution | Role: sprint spec — protect a newly filled position on the run that opens it, not the next one -->
# S182 — a new position is protected on the run that opens it

**Closes:** work-queue item 27 · **Opens from:** the 2026-08-19 22:30 unprotected-position faults ·
**Type:** fix ·
**Target version:** next available **PATCH** at merge — **do not pin it in this file** ·
**Branch:** `sprint-182-a-new-position-is-protected-on-the-run-that-opens-it`

> Handover to a delegated coding agent. Everything under **Measured** was read off this repo, the
> live spine or the Alpaca paper account on **2026-08-20**. Everything marked **Assumed** has **not**
> been verified — check it before building on it. Do not treat an unmarked claim as measured.

## Why

**A position that fills between two runs is unprotected until the run *after* the one that notices
it. Measured: 15½ hours and $2,147.76 of live exposure on 2026-08-19.**

**Measured — what happened.** MO, CSCO and NFLX filled at the 13:30 UTC open on 2026-08-19. At the
22:30 UTC run the fleet raised three `error` faults from `place_broker_stops`:

```text
error  execution  place_broker_stops  unprotected held position CSCO qty=9:  no active graph position
error  execution  place_broker_stops  unprotected held position MO   qty=15: no active graph position
error  execution  place_broker_stops  unprotected held position NFLX qty=2:  no active graph position
```

The stops were finally placed by the **next** run, at 05:09 UTC on 2026-08-20. Between the fill and
that moment the book carried **22 positions against 19 stops**.

**Measured — the mechanism, and it is structural.** `Position` nodes are created by the **monitor**
([`agents/monitor/store.py:41-61`](../../agents/monitor/store.py#L41-L61), and
[`reconcile.py:118-160`](../../agents/monitor/reconcile.py#L118)), which is **stage 7** of the
cascade. Stops are placed by **execution**, **stage 6**:

| Stage | 6 · execution | 7 · monitor |
| --- | --- | --- |
| does | `settle_stops` → `place_broker_stops` | creates `Position` from the `Fill` (`OPENS` edge) |
| needs | an active graph `Position` | — |

[`broker_stops.py:72-82`](../../agents/execution/broker_stops.py#L72-L82) walks the broker's holdings
from the snapshot and, for any ticker with no matching plan, records
`_record_unprotected_fault(..., "no active graph position")`. For a position filled since the last
run there **cannot** be one: the producer runs a stage later than the consumer. **Protection always
lags by a full run, by construction.**

🪤 **`reconcile_run_start` does not close this gap, and I initially assumed it did.**
[`reconciliation.py:38-75`](../../agents/execution/reconciliation.py#L38-L75) refreshes pending
fills, writes the snapshot and records divergences — it **never creates a `Position`**. Do not build
on the idea that reconciliation adopts holdings into positions; it does not.

**Measured — a second, independent blocker stacked on it.** Two stop submissions were rejected
outright:

```text
error  execution  submit  HTTP 403 {"code":40310000,"message":"potential wash trade detected.
use complex orders","reject_reason":"opposite side market/limit order exists"}
```

Alpaca refuses a sell-stop while an opposing **buy** order rests on the same symbol. Open buy limits
from a test run were sitting on those tickers. **A pending buy anywhere in the book can block a
protective stop** — that is a real production hazard, not a test artifact, because a partially
filled or still-open entry order on a held name reproduces it exactly.

🚨 **Same class as S146**, the unprotected ABT position. That one was a single incident; this is the
standing behaviour underneath it.

🟢 **Not a divergence.** Graph and broker agreed throughout — 22 active `Position` nodes against 22
broker holdings once the monitor had run. Do not go looking for a reconciliation defect.

## The design decisions this sprint has to make

**1 · Who may create the `Position`?** 🚨 **This is the crux, and it is a law question before it is
a code question.** `agents/monitor/laws/laws.md` declares `labels_owned` including **`Position`**, so
execution creating one to protect it would break the ownership declaration the vocabulary guard and
the law book both rest on. Options, none free:

- **(a) Move stop placement after the monitor.** Honest — the consumer runs after the producer. But
  stop placement is an execution capability and the monitor does not submit to the broker, so this
  means either a second execution pass or a new orchestration edge.
- **(b) Let the monitor request the stop**, execution still submits it. Keeps ownership intact, adds
  a message hop and a new contract.
- **(c) Place the stop from the `Fill` instead of the `Position`.** Execution **owns** `Fill`, so no
  ownership breach. 🪤 But `broker_stop_thresholds` is keyed on `position_ref` — check what actually
  needs the `Position` versus what merely reads it through one.
- **(d) Amend the law so execution may create `Position`.** Cheapest code, largest blast radius; it
  weakens a boundary deliberately drawn. **Requires a law cycle, not a code edit.**

🚨 **Do not pick by which is least typing.** Record the choice and the rejected ones in the design
log **before** implementing. **Assumed, not verified:** that execution's own `laws.md` has a
comparable `labels_owned` block — I could not find one; confirm before relying on either side.

**2 · What about the wash-trade rejection?** Decide explicitly, because it is independent of
decision 1 and will still bite after it is fixed. Cancel the conflicting buy first and re-place the
stop? Leave it and fault? 🚨 A silent `403` that leaves a position naked is the worst of the three,
and it is what happens today.

**3 · Is `error` the right severity, and should it repeat?** It fires every run until protection
lands. 🪤 **Look at S181 first** (`drop_sweep_ack`) — the same "fires every run, nothing changes"
shape was just solved there with a durable first-sight acknowledgement. Consider whether the same
pattern applies, or whether this one *should* keep shouting because unlike an untracked test order
it represents live unprotected money.

## Blast radius — measured 2026-08-20

| File | Lines | Note |
| --- | --- | --- |
| `agents/execution/poll.py` | **197** | 🚨 **Three lines from the 200 hard block. Nothing can be added here without a split.** |
| `agents/execution/broker_stops.py` | **179** | over the 150 warn line already |
| `agents/monitor/store.py` | **165** | over the warn line; owns `Position` creation |
| `agents/execution/exit_stops.py` | 108 | `settle_stops` lives here — the ordering seam |

🚨 **Plan the split before writing a line.** `poll.py` cannot absorb even a small addition.

## Steps, in order

1. **Reproduce as a failing test:** a broker holding with a `Fill` but no `Position` yet must end the
   run **protected**, not faulted. Assert on the placed stop, not on the absence of a fault.
2. **Decide 1–3 and record them** in `docs/design-log.md` with rejected alternatives, **before**
   implementing. LAW-06. Take the next free DL number — 🪤 the log has duplicates (two `DL-110`, two
   `DL-111`) and entries are prepended at the top *and* appended at the bottom; check before claiming.
3. **If the choice touches label ownership, do the law cycle** — amending `laws.md` is not a code
   edit, and the vocabulary/ownership guard is fail-closed.
4. **Implement**, respecting the module ceilings above.
5. **Cover the wash-trade path** with a test that a `403 opposite side` on a stop does not leave the
   position silently naked.
6. `make ci` green (**redirected to a file, never piped**), each new guard planted, watched to fail,
   restored.
7. **Live proof needs a fill.** 🪤 The bug only appears for a position filled *between* runs, so a
   synthetic graph fixture will not show it. Either wait for a real fill or construct one
   deliberately — and if you construct one, **tear it down** (`docs/laws/functionality-checks.md`).

## Success factors

- [ ] A position filled between runs is protected **on the next run**, not the one after.
- [ ] No `no active graph position` fault for a holding that has a `Fill` in the graph.
- [ ] A stop rejected `403 potential wash trade` is handled per decision 2 and proven by a test.
- [ ] Ownership: either `Position` is still created only by its declared owner, **or** the law was
      amended through a law cycle and the diff says so.
- [ ] `poll.py` ends **under 200**, and ideally under 150; the split is in the diff.
- [ ] Decisions 1–3 recorded with rejected alternatives.
- [ ] Each new guard planted, watched to fail, restored — stated per guard.
- [ ] `make ci` exit 0, 100.00 % coverage.
- [ ] `make gate-ran` **GATE PROVEN**, run from the worktree whose `HEAD` is the commit, SHA checked.

## Traps

🪤 **`reconcile_run_start` does not create positions.** Stated twice on purpose — it is the natural
wrong assumption and I made it before checking.

🪤 **A pending buy blocks a sell-stop at Alpaca.** Any fix that places stops while entry orders rest
on the same symbol will hit `403` in production even when the graph is perfect.

🪤 **`poll.py` is at 197 of 200.** The hard block will stop the build, not warn it.

🪤 **Do not "fix" this by widening `fallback_stop_pct`.** The fallback covers a position with no
*threshold*; here there is no *`Position`*, so the fallback is never reached.

🪤 **A script run from a git worktree silently gets the in-memory store** — a worktree has no `.env`.
Copy the refuse-on-in-memory guard from `scripts/sweep_divergence_flags.py`. **Never copy `.env` into
a worktree.**

🪤 **This is live money exposure, not reporting.** Unlike most recent sprints, being wrong here
leaves real positions unstopped. Prefer the conservative option at every fork.

## Handover — paste this to Codex

```text
Work item: S182 - a new position is protected on the run that opens it.
Repo: trading-agents. Read
docs/sprints/sprint-182-a-new-position-is-protected-on-the-run-that-opens-it.md in full before
writing anything. Read CLAUDE.md. Read docs/INDEX.md before opening any docs folder.

WHAT IS WRONG
A position that fills between two runs stays unprotected until the run AFTER the one that notices
it. Measured 2026-08-19: MO, CSCO and NFLX filled at the 13:30 UTC open; the 22:30 run raised three
errors from place_broker_stops -

  unprotected held position CSCO qty=9:  no active graph position
  unprotected held position MO   qty=15: no active graph position
  unprotected held position NFLX qty=2:  no active graph position

and the stops were only placed by the NEXT run at 05:09 UTC on 2026-08-20. That is 15.5 hours and
$2,147.76 of live exposure, with the book at 22 positions against 19 stops.

THE MECHANISM IS STRUCTURAL
Position nodes are created by the MONITOR (agents/monitor/store.py:41-61, monitor/reconcile.py:118),
which is stage 7. Stops are placed by EXECUTION at stage 6. broker_stops.py:72-82 walks broker
holdings and faults with "no active graph position" for any ticker with no plan. For a position
filled since the last run there CANNOT be one - the producer runs a stage after the consumer.
Protection lags by a full run by construction.

TRAP: reconcile_run_start does NOT close this gap. reconciliation.py:38-75 refreshes pending fills,
writes the snapshot and records divergences - it never creates a Position. I assumed it adopted
holdings and I was wrong; do not build on that idea.

SECOND, INDEPENDENT BLOCKER
Two stop submissions were rejected: HTTP 403 {"code":40310000,"message":"potential wash trade
detected. use complex orders","reject_reason":"opposite side market/limit order exists"}. Alpaca
refuses a sell-stop while an opposing BUY rests on the same symbol. A partially filled or still-open
entry order on a held name reproduces this in production - it is not a test-only artifact.

NOT a divergence: graph and broker agreed at 22 active positions each once the monitor had run.

WHAT TO DO
1. Failing test FIRST: a broker holding with a Fill but no Position yet must end the run PROTECTED.
   Assert on the placed stop, not on the absence of a fault.
2. DECIDE and record in docs/design-log.md WITH rejected alternatives, before implementing, who may
   create the Position. This is a LAW question first: agents/monitor/laws/laws.md declares
   labels_owned including "Position", so execution creating one breaks an ownership declaration the
   vocabulary guard rests on. Options: (a) move stop placement after the monitor; (b) monitor
   requests, execution submits; (c) place the stop from the Fill, which execution owns - but check
   what actually needs the Position versus merely reads through one, since broker_stop_thresholds is
   keyed on position_ref; (d) amend the law, which needs a full law cycle, not a code edit.
3. Decide explicitly what happens on a 403 wash-trade rejection. A silent 403 leaving a position
   naked is what happens today and is the worst option.
4. Decide whether the fault should keep repeating. Look at S181's drop_sweep_ack first - the same
   "fires every run, nothing changes" shape was just solved there - but consider that unlike an
   untracked test order this one represents live unprotected money and maybe SHOULD keep shouting.
5. make ci green, REDIRECTED TO A FILE not piped. Plant every guard, watch it fail, restore.

CONSTRAINTS
- agents/execution/poll.py is 197 lines. The hard block is 200. NOTHING can be added there without a
  split - plan it before writing. broker_stops.py is 179 and monitor/store.py is 165, both already
  over the 150 warn line.
- Do NOT widen fallback_stop_pct to paper over this. The fallback covers a position with no
  THRESHOLD; here there is no POSITION, so it is never reached.
- Live proof needs a real fill between two runs - a synthetic graph fixture will not exhibit the
  bug. If you construct one, tear it down and record it in docs/laws/functionality-checks.md.
- A script run from a git worktree silently gets the in-memory store (no .env) and every count reads
  0. Copy the refuse-on-in-memory guard from scripts/sweep_divergence_flags.py. NEVER copy .env into
  a worktree.
- Assumed, not verified: that execution's own laws.md has a comparable labels_owned block. I could
  not find one. Confirm before relying on either side of the ownership argument.
- This is LIVE MONEY EXPOSURE, not reporting. Being wrong leaves real positions unstopped. Take the
  conservative option at every fork.
- Branch sprint-182-a-new-position-is-protected-on-the-run-that-opens-it. Version: next available
  PATCH at merge, do not pin it. Push the branch and get `make gate-ran` GATE PROVEN before merging -
  run it from the worktree whose HEAD is the commit, and check the printed SHA. Fill in the Closeout
  block before handing back.
```

## Closeout — evidence

**Status:** implemented on branch
`sprint-182-a-new-position-is-protected-on-the-run-that-opens-it` as `0.90.16`.
Branch push / remote gate proof happens after this closeout commit; merge, deploy, and live-fill
proof are not claimed here.

**Result:** a broker holding whose buy `Fill` is already filled but whose monitor-owned `Position`
does not exist yet now gets a broker stop from Fill + OrderIntent lineage. Execution still writes
only execution-owned facts (`Fill`, `BrokerStopOrder`) and predicts the same `position_ref` the
monitor will later derive for `Position`, so monitor adoption does not cause a duplicate stop.
Rejected stop submissions, including Alpaca-style `403 potential wash trade`, remain rejected stop
Fills plus `UnprotectedPosition` faults and repeat until a live stop exists.

**Files changed:** `agents/execution/broker_stops.py`;
`agents/execution/filled_entry_stops.py`; `agents/execution/pm_execution.py`;
`agents/execution/poll.py`; `agents/execution/tests/test_broker_stop_pending_position.py`;
`agents/execution/tests/test_filled_entry_stops.py`; `contracts/position_refs.py`;
`contracts/positions.py`; `docs/design-log.md`; `docs/STATE.md`; `pyproject.toml`; `uv.lock`;
this sprint handoff.

**Design decisions:** recorded as [DL-118](../design-log.md). Chosen: place stops from filled-entry
lineage without execution writing `Position`; keep wash-trade stop rejections loud/repeated instead
of auto-cancelling unknown buys; keep repeated unprotected faults because this is live risk, not
immutable residue. Rejected: moving stop placement after monitor for S182, monitor-to-execution stop
requests, execution-created `Position`, Fill-key-derived `position_ref`, and blind buy cancellation.

**Proof:** first failing test before implementation:
`uv run pytest agents/execution/tests/test_broker_stop_pending_position.py::test_filled_entry_without_position_is_protected_from_fill_lineage --no-cov`
failed with `ValueError: not enough values to unpack (expected 1, got 0)` because no
`BrokerStopOrder` was written. Restored focused proof:
`uv run pytest agents/execution/tests/test_broker_stop_pending_position.py
agents/execution/tests/test_filled_entry_stops.py --no-cov` passed `7 passed`; the broader
broker-stop/poll regression set passed `43 passed`.

**Module sizes:** `poll.py` is split and now **135** lines, under both the 150 warning and 200 hard
cap. Other touched modules are under the hard cap: `pm_execution.py` **84**,
`broker_stops.py` **187**, `filled_entry_stops.py` **176**, `contracts/positions.py` **187**,
`contracts/position_refs.py` **16**, `test_broker_stop_pending_position.py` **156**,
`test_filled_entry_stops.py` **167**.

**Live proof:** not done. The sprint's live proof requires a real or deliberately constructed fill
between runs; this branch proves the behavior with graph/broker fixtures only. No production graph
state was mutated, no broker order was created, and no teardown was required.

**Guards planted:** Fill-derived planning disabled by blocking every broker holding -> S182 test
failed with zero `BrokerStopOrder` nodes; restored. Rejected-stop fault branch suppressed -> wash
trade test failed with `len(unprotected) == 0`; restored. Fill-derived `position_ref` changed to a
Fill-key-shaped hash -> S182 test failed on the expected monitor-compatible `position_ref`;
restored.

**`make ci`:** final redirected local gate
`C:\Users\yury_\AppData\Local\Temp\trading-agents-s182-make-ci-final.log` exited `0`:
`2331 passed, 4 skipped`, `100.00%` coverage, `pip-audit` no known vulnerabilities, tracked and
untracked detect-secrets checks passed.
