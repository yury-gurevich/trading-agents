# Subsystem map — the helicopter view

The BIG parts, their tier, and how data/authority flows between them. Tiers run
foundation → signal; a subsystem may only depend **upward** (lower tier numbers). This is
the dependency DAG; it's what you consult before changing anything.

## Tiers & boundaries

| Tier | Subsystem | Owns | Needs (up) | Affects (down) |
| --- | --- | --- | --- | --- |
| 0 | **identity-secrets** | all credentials + grants | human mint, Azure AD, GitHub | everything |
| 1 | **registry** | container images (GHCR) | identity, source code | fleet |
| 1 | **region-residency** | *where data may legally live* | jurisdiction/law (ADR) | graph, fleet, registry, observability |
| 2 | **graph-store** | Neo4j registry/provenance | identity, region | fleet (master can't boot without it) |
| 3 | **fleet-compute** | running agents (Container Apps) | registry, graph, identity, region | observability, the product |
| 4 | **observability** | logs + metrics | fleet | alerting, the operator |
| x | **operator-cli** (`ta`) | orchestration + gates | identity (reads all creds) | how every part is driven |

## Data-flow (one line)

```
source ──build──▶ registry ──pull──▶ fleet ◀──auth── identity
                                       │  ▲
                              writes   │  │ reads creds
                                       ▼  │
                                   graph-store ◀── region (legal constraint on location)
                                       │
                                  logs ▼
                                 observability
```

## Cross-cutting: region / residency

`region-residency` is tier-1 but **constrains** graph, fleet, registry, and observability —
because financial data may be legally required to stay in a jurisdiction (data
residency / data sovereignty). Any region move is a coordinated, gated migration across all
four, not a single action. This deserves its own ADR. **Hard rule:** no data movement
proceeds until the residency gate is GREEN for the *target* region.

## Consolidated risk view

- **Highest blast radius:** identity-secrets (tier 0) — one bad rotation downs the fleet.
- **Hardest to reverse:** graph-store region migration, Key Vault purge, RG deletion.
- **Most coupled:** fleet-compute — sits downstream of four subsystems.
- See `maintenance/points-of-no-return.md` for the full irreversible-step registry.

## Scenarios this map must support (runbooks, per subsystem)

| Scenario | Primary subsystem | Coordinates with |
| --- | --- | --- |
| Tear down + move region (residency law) | region-residency | graph, fleet, registry, observability |
| Custom domain instead of generic | fleet-compute | identity (cert), observability |
| Retire / decommission | (each) | identity (revoke), graph (backup) |
| Scheduled config backup | (each) | graph-store, identity |
| Credential rotation | identity-secrets | registry, fleet |
| Permanent graph store (Aura → VM) | graph-store | identity, region, fleet |
