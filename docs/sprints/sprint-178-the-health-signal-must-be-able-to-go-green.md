<!-- Agent: supervisor | Role: sprint spec — make the critical-flag health signal able to return to green, so it can carry news again -->
# S178 — the health signal must be able to go green

**Closes:** work-queue item 17 · **Opens from:** `/reconcile-broker`, 2026-08-15 ·
**Type:** fix ·
**Target version:** next available PATCH at merge — **do not pin it in this file** ·
**Branch:** `sprint-178-the-health-signal-must-be-able-to-go-green`

> Handover to a delegated coding agent. Everything under **Measured** was read off this repo or the
> live spine on **2026-08-15**. Everything marked **Assumed** has **not** been verified — check it
> before building on it. Do not treat an unmarked claim as measured.

## Why

**`healthy` has been `false` every single day since 2026-07-08, and nothing that happens can turn it
green.** A signal that cannot change carries no information: a genuinely new critical condition
arrives into a pile of 45 and moves nothing.

**Measured on the live spine, 2026-08-15:**

| Fact | Value |
| --- | --- |
| `Flag` nodes | **52** — 47 `critical`, 5 `warn` |
| `FlagResolution` nodes | **7** — 5 `warn`, 2 `critical` |
| **critical unresolved** → `pending_human_flags` | **45** |
| `healthy` | **`false`**, continuously since 2026-07-08 |
| Of the 47 criticals | **46** are `Broker position divergence at run start`; 1 is an older variant |

**The resolution machinery is not broken — two critical flags have been resolved.** The join in
[`health.py:33-39`](../../agents/supervisor/domain/health.py) is on the `(subject_ref, severity)`
**props**, not on node keys, and all 7 resolutions match a Flag correctly. Nothing is mis-keyed.

**The defect is that the backlog can only grow.** Two measured causes, and both must be fixed:

**1 · Every run mints a brand-new, unique flag.** In
[`reconciliation_store.py:122-140`](../../agents/execution/reconciliation_store.py):

```python
subject_ref = f"broker-position-divergence:{snapshot.key}"
key = f"flag:{subject_ref}:critical"
```

`snapshot.key` is `broker-position-snapshot:<run_id>:<ISO timestamp>` — unique per run. The
`if graph.get_node("Flag", key) is not None: return` guard therefore **never fires across runs**.
One new `critical` flag per trading day, forever, none of them ever the same flag twice.

**2 · Only a human can resolve one.** `resolve_flag` is reachable solely through the supervisor's
`approve` capability (`CAPABILITY_MATRIX["approve"] → supervisor.resolve_flag`,
[`matrix.py:33`](../../agents/supervisor/domain/matrix.py)). No automated path calls it. So the
system raises one unresolvable alarm per day and asks a human to clear each by hand.

**3 · The severity is decided before the outcome is known.** The flag is written at **run start**,
describing a divergence that reconciliation is *about to adopt*. Measured on `sched-2026-08-14`: the
flag was raised at `22:30:50` naming AMD/DOW/VZ as missing; by `22:54:06` all three had been adopted
from broker truth and given protective stops, and graph and broker agreed **19/19**. The flag was
**stale 3 minutes after it was written, by design**. It described normal, successful operation and
demanded human attention for it.

## The design decisions this sprint has to make

**1 · What severity does an *adopted* divergence deserve?** 🚨 **Recommended: severity follows the
outcome.** A divergence reconciliation successfully adopted is a **record** (DL-44 lineage —
valuable, keep it) and belongs at `info`/`warn`. A divergence it could **not** adopt is a genuine
`critical`. Today both get `critical` because severity is chosen before the outcome exists.

- *Rejected (state your own reasoning if you disagree):* **auto-resolve after adoption** — writes a
  `critical` then immediately clears it, so the signal flickers and depends on write ordering.
- *Rejected:* **stop raising the flag** — destroys the DL-44 lineage record, which is the point of
  having it.

**2 · Does the 45-flag backlog get swept, and how?** It must, or `healthy` stays `false` no matter
what the new code does. 🚨 **The sweep appends `FlagResolution` nodes; it must not edit, delete or
rewrite any `Flag`, `Position` or broker state.** DL-44's prohibition is on "fixing" divergence by
editing the graph — appending a resolution with a stated reason is not that, but say so explicitly
in the sweep's own record. **Decide:** one-off script under `scripts/`, or an operator command.

**3 · Should `healthy` distinguish "no alarms" from "alarms nobody can clear"?** Currently
`healthy = open_incidents == 0 and critical_flags == 0`. **Assumed, not measured:** that a single
boolean is still the right shape once severity means something. Consider whether the age of the
oldest unresolved critical belongs in `MasterReport`.

## Blast radius — measured

`healthy` and `pending_human_flags` flow: [`health.py`](../../agents/supervisor/domain/health.py) →
[`result.py:40-64`](../../agents/supervisor/result.py) → `MasterReport`
([`contracts/supervisor.py:50`](../../contracts/supervisor.py)) → the MCP tool surface
([`surfaces/mcp_tools.py:53`](../../surfaces/mcp_tools.py)).

🟢 **`orchestration/packs/trading_acceptance.py` does not read either field** — verified by grep.
**Changing this cannot fail a run or block a trade.** It is a reporting-surface fix.

## Steps, in order

1. **Reproduce the growth as a failing test:** two runs with the same underlying divergence must not
   produce two unresolvable `critical` flags.
2. **Record the severity convention** (decision 1) in `docs/design-log.md` with its rejected
   alternatives, **before** applying it. LAW-06.
3. **Make severity follow the adoption outcome** in `reconciliation_store.py`.
4. **Write the backlog sweep** (decision 2), append-only, with a stated reason on each resolution.
5. **Run the sweep against the live spine** and prove `pending_human_flags` falls from **45** toward
   0, and that `healthy` can be observed `true`. 🪤 This is the only success factor that cannot be
   proven by `make ci` — it needs the real graph.
6. `make ci` green, **plant each new guard and watch it fail**, restore.

## Success factors

- [ ] A repeated divergence does not mint a second unresolvable `critical` flag — asserted in a test.
- [ ] An **adopted** divergence no longer produces a `critical`; an **unadopted** one still does.
- [ ] The DL-44 lineage record still exists for every divergence — nothing stopped being recorded.
- [ ] Backlog swept: `pending_human_flags` measured **before and after** on the live spine, both
      numbers quoted; `healthy` observed `true` at least once.
- [ ] The sweep appended only `FlagResolution` nodes — no `Flag`, `Position` or broker mutation.
- [ ] Severity convention recorded in `docs/design-log.md` with rejected alternatives.
- [ ] Each new guard **planted, watched to fail, restored** — stated per guard.
- [ ] `make ci` exit 0, 100.00 % coverage.

## Traps

🪤 **Both files you will touch are already past the 150-line warn line.** Measured 2026-08-15:
`agents/execution/reconciliation_store.py` = **169**, `agents/supervisor/store.py` = **162**. The
hard block is **200** and `make ci` fails at it. Split before you add, do not `# noqa`.

🪤 **`Flag` is not in the enforced-property vocabulary, but `severity` is read by a join.** Changing
the severity *value* changes which flags `compute_health` counts. Check every reader before
widening the vocabulary of that field.

🪤 **Do not "fix" the historical flags by rewriting them.** They are an append-only record of what
was true at each run start. Resolve them; do not edit them, and do not delete them.

🪤 **A resolution that does not join is invisible, not an error.** The join is on
`(subject_ref, severity)` props. A resolution written with the wrong severity silently fails to
clear its flag and reports success. Assert the *count falls*, never that the write returned.

🪤 **S177 is in flight in this repo** on `sprint-177-every-number-names-its-unit`, touching
`agents/portfolio_manager/domain/concentration.py`, `agents/deliberator/context.py` and
`context_pm.py`. This sprint touches none of them. **Do not rebase onto or merge S177's branch.**

## Handover — paste this to Codex

```text
Work item: S178 — the health signal must be able to go green.
Repo: trading-agents. Read docs/sprints/sprint-178-the-health-signal-must-be-able-to-go-green.md in
full before writing anything. Read CLAUDE.md. Read docs/INDEX.md before opening any docs folder.

WHAT IS WRONG
healthy has been false every day since 2026-07-08 and nothing can turn it green. Measured on the
live spine 2026-08-15: 52 Flags (47 critical, 5 warn), 7 FlagResolutions, 45 critical unresolved.
The machinery is NOT broken - 2 critical flags have been resolved and all 7 resolutions join
correctly on the (subject_ref, severity) props. The backlog can only grow, for two reasons:

1. agents/execution/reconciliation_store.py builds subject_ref from snapshot.key, which embeds the
   run id AND an ISO timestamp. Every run mints a unique flag, so the existing dedupe guard
   ("if graph.get_node('Flag', key) is not None: return") never fires across runs. One new
   unresolvable critical per trading day, forever.
2. resolve_flag is reachable ONLY via the supervisor "approve" capability - a human command. No
   automated path calls it.
3. Severity is chosen at run START, before the outcome exists. On sched-2026-08-14 the flag was
   written 22:30:50 naming AMD/DOW/VZ missing; by 22:54:06 all three were adopted from broker truth
   and given stops, graph and broker agreeing 19/19. The flag described NORMAL SUCCESSFUL operation
   and demanded human attention for it.

WHAT TO DO
1. Failing test first: the same underlying divergence twice must not mint two unresolvable criticals.
2. Record the severity convention in docs/design-log.md WITH rejected alternatives, before applying.
3. Make severity follow the adoption outcome: adopted -> info/warn (keep the DL-44 lineage record),
   NOT adopted -> critical. Do not stop recording divergences.
4. Write an append-only backlog sweep. It may ONLY append FlagResolution nodes with a stated
   reason. It must NOT edit, delete or rewrite any Flag, Position, or broker state.
5. Run the sweep on the live spine. Quote pending_human_flags BEFORE and AFTER, and show healthy
   observed true at least once. make ci cannot prove this one - it needs the real graph.
6. make ci green. Plant EVERY new guard, watch it fail, restore. Report each plant in the closeout.

CONSTRAINTS
- reconciliation_store.py is 169 lines and supervisor/store.py is 162; the hard block is 200 and CI
  fails at it. Split before adding. No # noqa.
- This is a REPORTING fix: trading_acceptance.py reads neither healthy nor pending_human_flags, so
  it cannot fail a run. Verify that is still true before relying on it.
- A resolution written with the wrong severity silently fails to join and reports success. Assert
  the unresolved COUNT falls; never assert that the write returned.
- Do not rewrite or delete historical flags. They are an append-only record.
- S177 is in flight on sprint-177-every-number-names-its-unit touching concentration.py,
  context.py and context_pm.py. Touch none of them. Do not rebase onto or merge that branch.
- Branch sprint-178-the-health-signal-must-be-able-to-go-green. Version: next available PATCH at
  merge, do not pin it. Fill in the Closeout block at the bottom of the spec before handing back.
```

## Closeout — evidence

<!-- FILL THIS IN BEFORE HANDING BACK. A handback with this placeholder intact is not accepted. -->

**Result:** *not yet implemented.*

**Files changed:** *...*

**Design decisions:** *severity convention + rejected alternatives as a DL entry, linked.*

**Backlog sweep:** *`pending_human_flags` before and after, measured on the live spine; `healthy`
observed `true`; confirmation that only `FlagResolution` nodes were appended.*

**Guards planted:** *per guard: what was planted, that it failed, that it was restored.*

**`make ci`:** *exit code, passed/skipped counts, coverage %.*
