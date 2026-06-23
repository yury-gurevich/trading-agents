# Org map — the system as an IT department

Modelled the way a real IT shop is siloed, so it maps to how you already think. Each
**department** owns a slice of operations, has a charter (its "law"), and declares its
dependencies. Boundaries are governed by need and are revisable under **LAW-01** — this
table is a *proposal*, not a fixture. Adjust the silos freely.

## Departments

| Dept | Owns (its remit) | Maps to (technical) | Needs (up) | Serves (down) |
| --- | --- | --- | --- | --- |
| **Security & IAM** | identities, keys, secrets, grants | identity-secrets | human mint, Azure AD, GitHub | every dept |
| **Release Engineering** (DevOps/CI-CD) | build → image → deploy pipeline | GHCR build, deploy-agents | Security, source | Platform |
| **Platform / Infrastructure** | compute hosting, the running fleet | Container Apps, future VMs | Security, Release, Data, Network | the product, SRE |
| **Data & Storage** (DBA) | the graph store, backups, restores | Neo4j (Aura→VM) | Security, Network, GRC | Platform (master needs it) |
| **Networking** | DNS, custom domains, ingress, region routing | CA ingress, FQDNs | Platform | Platform, Service Desk |
| **SRE / Observability** | health, logs, metrics, incidents | Log Analytics, Monitor, `ta status` | Platform | the operator |
| **GRC** (Governance/Risk/Compliance) | residency, audit, retention, the ledger | region-residency, `maintenance/ledger.md` | law/jurisdiction | every dept (constraint) |
| **Service Desk** | operator-facing requests + comms | `ta` CLI UX, custom-domain requests | all depts | the operator |
| **Experimentation & Tuning** (cross-cutting) | how a pipeline parameter is changed by evidence — register/run/measure/compare/gate/promote | ADR-0013 ParameterSet/RunMetrics/Experiment nodes, `run_local` | Data (graph), the owning agent's metric | every pipeline process (its dials) |

## Dependency direction (who waits on whom)

```text
Security & IAM ─┬─▶ Release Eng ─▶ Platform ◀─ Data & Storage ◀─┐
                ├──────────────────▶ Platform                    │
                └──▶ Data & Storage ◀── Networking ──▶ Platform  │
GRC ── constrains ▶ Data, Platform, Networking, Release ─────────┘
SRE ◀── observes ── Platform        Service Desk ── fronts ── all
```

Rule of thumb: you may depend **up** the Security→Release→Platform spine; GRC constrains
everyone sideways (compliance is not optional); SRE and Service Desk are read/serve layers.

## Where the old "subsystems" went

The earlier 7-subsystem cut folded into departments: *identity-secrets → Security & IAM;
registry+deploy → Release Engineering; fleet-compute → Platform; graph-store → Data &
Storage; region-residency → GRC (+ Networking for routing); observability → SRE;
operator-cli → Service Desk.* Same matter, org-shaped.
