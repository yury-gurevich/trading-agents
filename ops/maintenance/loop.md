# The maintenance & tuning loop

Two loops keep `ops/` honest: a **change-triggered** loop (fires when you touch a
subsystem) and a **periodic tuning** loop (assesses whether the process itself can be
better). Both write to `ledger.md` so everything is traceable.

---

## Loop 1 — change-triggered (the "don't let it drift" loop)

**Trigger:** any change to files/resources in a subsystem's realm (its `OPS-MNT` section
lists the paths). When that happens, in the *same* change:

1. **Re-run the subsystem's gates** (`ta <subsystem> preflight`). Red → stop.
2. **Update its charter** — owned-list, params, points-of-no-return, changelog.
3. **Check declared downstream neighbors** (the `OPS-DOWN` list) still hold.
4. **Append to `ledger.md`** — what changed, gate result, who/what.

This is the operational equivalent of "every law clause cites a test." A charter that
drifts from reality is a bug. Enforced lightly now (checklist + a CLAUDE.md rule + memory
seed so the AI honors it); later a git-hook maps changed paths → required charter touch.

## Loop 2 — periodic tuning (the "is there room to improve" loop)

The process is **assessable**, not auto-trained. On demand (or scheduled):

1. **Collect** the `ledger.md` rows + the `ta` run logs for a window.
2. **An LLM reviews** them against each charter and proposes improvements:
   - reorder or parallelize steps that always run in sequence,
   - add a gate that would have caught a recurring failure,
   - retire a step that never changes anything,
   - flag a credential/resource used more widely than its charter declares,
   - surface a cost spike or a slow step.
3. **The operator is the gate** — proposals are suggestions, never auto-applied. Approved
   ones become a charter/script change (which itself fires Loop 1).

This is the same shape as ADR-0010's prompt quality gate: the ops process is a **predictor**
we measure; the LLM is the **challenger** proposing a better version; the **eval is the
ledger** (did runs get faster / cheaper / less manual / less failure-prone); the **operator
is the promotion gate**. Nothing is "tuned" blindly — every change is justified by the log.

> **Two subjects, one loop.** Loop 2 here tunes the **infrastructure/ops process** (charters,
> runbooks; eval = this ledger). The **trading pipeline** is tuned by the same loop on a different
> subject and store — see the [Experimentation & Tuning charter](../departments/experimentation/charter.md)
> (ADR-0013): predictor = a pipeline `tunable`, challenger = a `ParameterSet`, eval = `RunMetrics`
> on the graph, gate = the operator. Both inherit LAW-01; neither auto-promotes.

### What "better" is measured on
| Signal | Source | Better = |
| --- | --- | --- |
| failure rate | ledger outcomes | ↓ |
| duration | ta run logs | ↓ (where safe) |
| cost per run | ledger cost field | ↓ |
| manual touches | ledger operator field | ↓ |
| gate coverage | charters vs incidents | ↑ |

---

## The ledger (traceability)

`ledger.md` is append-only. Every `ta` action and every charter change writes one row:

```
| ts (AEST) | subsystem | action | outcome | duration | cost | operator | note |
```

The ledger is the audit trail *and* the training set for Loop 2. Never edit past rows.

## Points of no return

`points-of-no-return.md` is the consolidated, system-wide registry of every irreversible
step (each charter's `OPS-PNR` rolls up here). Before any such step, `ta` must:
1. show the blast radius, 2. snapshot current state, 3. require an interactive confirm.
This is the "I do not want to go blind into a costly, unrecoverable move" guarantee.

## Ownership

Solo operator + the AI ops loop. "Owner" in a charter = the loop responsible for keeping it
true, not a person. As the system grows, an owner can become a specific agent (e.g. a
`supervisor`/`curator` could run Loop 2 against the ledger automatically).
