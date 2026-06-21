# `ops/` — the Operations sub-project

**What this is:** the governance layer for everything operational — deployment, the
graph store, secrets, region/residency, the CLI, observability. It is to *operations*
what `agents/<name>/laws/` is to *agents*: it defines boundaries, sets expectations,
and is the single source of truth for "how do I safely run, change, recover, or move
this part of the system."

**What this is NOT:** the implementation. The executable scripts live in `infra/`
(`deploy-agents.ps1`, `aura.ps1`, `status.ps1`, …) and are driven by the `ta` CLI.
`ops/` is **policy**; `infra/` is **mechanism**. A charter names the `infra/` tool that
implements each action — the two stay uncoupled, like the agents and their laws.

---

## Why this exists

The project is too big to hold in one head. The code realm already has discipline
(`INDEX.md`, `laws/`, ADRs, import-linter boundaries). The operational realm had none —
just scripts in a folder. Undocumented side-effects, missing gate-checks, and
"we can't remember if this step is reversible" are exactly what bite a one-person
product later. `ops/` closes that gap **before** the script count explodes.

## Reading the folder path tells you where you are

```
ops/
  README.md                 ← you are here: what the realm is
  INDEX.md                  ← the map: every subsystem, its tier, its status
  subsystem-map.md          ← helicopter view: boundaries, data-flow, the dependency DAG
  _template/charter.md      ← the "law" schema every subsystem charter follows
  subsystems/
    identity-secrets/       ← tier-0 foundation (everything depends on it)
      charter.md            ← the law: owns / gates / points-of-no-return / recovery / tuning
      runbooks/             ← step-by-step procedures (deploy, rotate, migrate, restore)
    registry/               ← GHCR build+push
    graph-store/            ← Neo4j (Aura now → VM later)
    fleet-compute/          ← Azure Container Apps
    region-residency/       ← cross-cutting: where data is legally allowed to live
    observability/          ← logs + metrics
    operator-cli/           ← the `ta` CLI itself
  maintenance/
    loop.md                 ← the maintenance + tuning loop (incl. the LLM-review process)
    ledger.md               ← append-only trace of every operational action
    points-of-no-return.md  ← consolidated registry of every irreversible step
```

A path like `ops/subsystems/graph-store/runbooks/migrate-region.md` reads top-to-bottom
as *operations → a subsystem → the graph store → a procedure → migrate it to a new region.*

---

## The seven principles every charter must honour

1. **Gated** — no action runs before its preflight gates pass GO. *Never go blind into a
   costly move to discover we lack the rights to save the result.* (Your founding rule.)
2. **Interactive** — destructive or irreversible steps stop and ask, showing blast radius.
3. **Idempotent** — every action is safe to re-run; re-running converges, never corrupts.
4. **Dry-runnable** — `--dry-run` shows exactly what *would* happen, changing nothing.
5. **Traceable** — every run appends to `maintenance/ledger.md`: when, what, outcome,
   duration, cost, and the postcondition check that proves it worked.
6. **Recoverable** — every subsystem declares its backup + restore path and RPO/RTO;
   destructive actions snapshot state first.
7. **Reversible-or-flagged** — every action is either rollback-able **or** explicitly
   listed as a **Point of No Return** with a guarding confirmation.

## Tunable (not in the PyTorch sense)

The process is **assessable**: every run is logged with its outcome, timing, and cost, so
we can ask "is there room for improvement?" A periodic **LLM-review loop** reads the ledger
+ script logs and proposes changes — reorder steps, add a missing gate, parallelize, retire
a flaky step. The operator approves; the charter/script is updated. This mirrors the
champion–challenger / eval-gate philosophy already adopted for prompts (ADR-0010): the ops
process is a predictor we measure and improve, the LLM is the challenger, the operator is
the gate. See `maintenance/loop.md`.

---

## How it connects

| Layer | Lives in | Role |
| --- | --- | --- |
| Policy (the law) | `ops/subsystems/*/charter.md` | boundaries, gates, recovery, tuning |
| Procedure | `ops/subsystems/*/runbooks/*.md` | the steps, with rollback |
| Mechanism | `infra/*.ps1` | the executable implementation |
| Driver | `ta` CLI (`infra/`) | runs a charter's gates then its action |
| Trace | `ops/maintenance/ledger.md` | append-only record of every run |

Status of this draft: **skeleton for discussion.** The `identity-secrets` charter is the
worked example; other subsystems are stubs in `INDEX.md` awaiting their charters.
