---
department: <kebab-name>
tier: <0 foundation | 1 supply | 2 state | 3 compute | 4 signal | x cross-cutting>
owner: <the maintaining loop, e.g. "operator + AI ops loop">
status: draft | active | locked
version: 0.1
implements_with: [infra/<script>.ps1, …]   # the mechanism this policy drives
---

# Charter — <Subsystem Name>

> The operational "law" for this subsystem. Mirrors the agent `laws.md` schema, adapted
> for infrastructure. Copy this file to `ops/subsystems/<name>/charter.md` and fill it in.
> Every section is mandatory; write "none" rather than deleting a section.

## OPS-IDN · Identity

One paragraph: what this subsystem *is*, its tier, and its single reason to exist.

## OPS-OWN · Owns (single-writer)

The resources/artifacts this subsystem is the **sole** owner of. Nothing else may create,
mutate, or delete these. (Mirrors `owns_graph` in agent contracts.)

## OPS-UP · Upstream (needs)

What must exist/be-true before this subsystem can function. List each dependency and which
subsystem (or human/external) provides it. This is the **up-flow**.

## OPS-DOWN · Downstream (blast radius)

What depends on this subsystem — i.e. what breaks if it breaks. This is the **down-flow**
and the blast radius. Be specific; this is what you check before changing anything here.

## OPS-GATE · Preflight gates (GO / NO-GO)

The checks that MUST pass before any action runs. No gate green → no action.

| Gate ID | Check | Pass criteria | On fail |
| --- | --- | --- | --- |
| G-… | <what is verified> | <green condition> | block / warn / prompt |

## OPS-ACT · Actions / Runbooks

Each operation this subsystem supports. One row per action; link a runbook for the steps.

| Action | Gates required | Idempotent | Dry-run | Postcondition (proof it worked) | Rollback | Blast radius |
| --- | --- | --- | --- | --- | --- | --- |
| <verb> | G-… | yes/no | yes/no | <verifiable check> | <how to undo, or PNR-id> | <scope> |

## OPS-PNR · Points of no return

Every **irreversible** step, explicitly. Each must be guarded by an interactive
confirmation and a pre-action state snapshot. If a step can be undone, it does NOT belong
here — it belongs in a Rollback instead.

| PNR ID | Irreversible step | Why it can't be undone | Guard (confirmation + snapshot) |
| --- | --- | --- | --- |

## OPS-REC · Recovery

- **Backup:** what is backed up, where, how often.
- **Restore:** the exact steps to rebuild this subsystem from backup.
- **RPO / RTO:** how much data loss / downtime is acceptable.

## OPS-NEV · Never

Operational must-nevers (the hard boundaries). e.g. "never delete X without a backup",
"never proceed if the residency gate is RED".

## OPS-OBS · Observability

How to know it's healthy: the status command, the signals, where the logs go.

## OPS-TUNE · Tuning (assessment + improvement)

- **Assess:** the metrics that say whether this subsystem's ops are good (duration, failure
  rate, cost, manual-touch count).
- **Improve:** what the LLM-review loop should look for here, and who approves a change.

## OPS-PARAM · Parameters (the tunable knobs)

| Param | Default | Range / options | Effect |
| --- | --- | --- | --- |

## OPS-MNT · Maintenance trigger

**When you touch `<paths / resources>` → do `<these checks/updates>`** and re-verify the
named downstream neighbors. This is what fires the maintenance loop for this subsystem.

## Changelog

| Version | Date | Change |
| --- | --- | --- |
| 0.1 | <date> | initial draft |
