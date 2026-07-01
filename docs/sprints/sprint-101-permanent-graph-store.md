# Sprint 101 — Permanent graph store + fleet store wiring

**Phase:** Fleet Activation (DL-30 / DL-35)
**Branch:** `sprint-101-permanent-graph-store`
**Status:** planned
**Effort:** M (ops-heavy; not CI-tested)

---

## Goal

Give the fleet a **durable** graph store to run against. Today Neo4j is local Docker (dev) + a lapsing
Aura trial (cloud) — neither is a permanent home for a hands-off fleet. This sprint provisions a
persistent Neo4j the master + 12 agents all connect to, and points the deploy at it. This is the first
sprint that touches **live infra and cost** — DL-35 accepted that in choosing full activation.

## Scope

**In:**

- Stand up a **permanent Neo4j** per [ADR-0008](../decisions/0008-neo4j-hosting-local-docker.md) /
  [DL-05](../design-log.md) / [DL-06](../design-log.md) — self-hosted on a small Azure VM (Enterprise if
  the dev licence lands, else Community), or a committed Aura tier if chosen. Record the choice + cost in
  an ADR amendment or a new decision.
- Wire the fleet at it: [`infra/deploy-agents.ps1`](../../infra/deploy-agents.ps1) and
  [`infra/container-apps.bicep`](../../infra/container-apps.bicep) inject `NEO4J_*` for every agent (the
  provider path already does — extend to all, since every agent builds its store via
  `build_graph_from_env`). Password stays a Container Apps `secretref` / Key Vault entry.
- Uniqueness constraints + schema bootstrap applied to the fresh DB (the constraints the in-memory store
  gets for free); a one-shot provisioning script or documented step.
- Backup/restore documented (DL-06 flagged backup as the real deferred cost; DL-11 for the API surface).

**Out:** no code logic changes; no fleet run-through (S102). Provisioning + wiring + a connectivity proof
only.

## Deliverables

- Provisioning script/steps (`infra/…`) + a short runbook in [`docs/deployment.md`](../deployment.md)
  (which is **stale** — update it in this sprint to the container-per-agent + permanent-store reality; it
  still describes the monolith).
- `deploy-agents.ps1` / bicep updated so every agent receives `NEO4J_*`.
- Decision record: store choice, edition, region (residency — DL-02), cost, backup plan.

## Decisions to confirm (before building)

- **Host: self-managed VM vs. managed Aura.** VM = cheaper/Enterprise-capable but you own patching +
  backup; Aura = managed but paid at a persistent tier. Recommend a VM with Community + a scripted backup
  unless the Enterprise dev licence lands. **This is an operator cost decision — confirm before spend.**
- **Region / residency** (DL-02) — pick a region defensible for the data; keep it consistent with the
  Container Apps environment (`australiaeast`).

## Acceptance / exit criteria

- [ ] The permanent Neo4j is reachable from the Container Apps environment; a probe does write→read→verify.
- [ ] Uniqueness constraints present on the fresh DB.
- [ ] Master + every agent get `NEO4J_*` from deploy; a manual master boot connects and writes a `Session`.
- [ ] `deployment.md` updated to current reality; backup/restore documented.

## Dependencies

- Decisions ADR-0008, DL-05, DL-06, DL-02 (residency). No code dependency on S97–S100, but sequenced after
  them so the thing we run on the store (S102) is ready.

## Version bump

Infra/provisioning — no application feature. **PATCH** only if a code/config file changes
(e.g. bicep/deploy script); otherwise no `pyproject` bump. Record the version decision in the sprint report.

## Notes

Not CI-testable by nature (live infra). Keep the *evidence* in the sprint report: the probe output and the
master boot log. Per LAW-02, "provisioned" is proven by a connectivity probe, not asserted.
