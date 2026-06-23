# Research: DB placement — substrate registry vs trading-pack provenance graph

**Status:** Research complete · **Date:** 2026-06-23 · **Author:** planning session
**Audience:** Product owner, planning agents, coding agents
**Source:** Neo4j docs, Azure docs, vendor comparison pages (see links at foot)

---

## Why this question now

ADR-0012 (platform/pack wall) and DL-12 (S84–S86) separated the master's grant/secret policy from
the trading pack. The next natural step: the substrate should not be tied to a trading-pack DB choice.
Neo4j was adopted because the trading provenance graph needed it; the substrate registry piggy-backs
on the same store by accident, not design. Now that the wall exists, each layer can choose the right
store for its actual needs.

---

## What each layer actually stores

### Layer A — substrate registry (master agent)

Bounded, flat, operational.

| Node type | Max rows (12-agent fleet) | Query pattern |
| --- | --- | --- |
| AgentInstance | ~12 | "is agent X registered?" |
| Session | ~12 active + history | "active sessions" |
| CapabilityGrant | ~60 (5 avg/agent) | "what capabilities does agent X have?" |
| CapabilityRoute | ~60 | "who handles capability Y?" |

Total: a few hundred nodes at most, never growing unbounded. **No graph traversal required** —
all lookups are keyed by agent-type or capability name. A document or key-value store is sufficient;
a graph engine is overkill.

### Layer B — trading-pack provenance graph

Unbounded, append-only, graph-traversal-heavy.

| Node type | Per run (12 tickers) | Notes |
| --- | --- | --- |
| RunRequest | 1 | root |
| MarketData | ~12 | ~24 KB each (dominates) |
| ScanRun + CandidateSet | 1+1 | carries FilterTrace.verdicts |
| AnalystRun + scored tickers | 1+~8 | per-ticker scored nodes |
| PMRun + decisions | 1+~6 | per-ticker PMDecision |
| ExecutionRun + orders | 1+~6 | TradeOrder per ticker |
| MonitorRun + closes | 1+~6 | CloseDecision per ticker |
| ReporterRun | 1 | summary |

**Estimate: ~55 nodes + ~60 relationships per daily run.** 1,000 runs → ~55K nodes / ~60K rels;
3,600 runs → 200K nodes (AuraDB Free ceiling). At one run per trading day, that is ~14 years before
the Free ceiling. At 10 runs/day (backtest-style), ~1.4 years. Graph traversal is essential:
`run_request → provider → scanner → analyst → PM → execution → monitor → reporter` lineage walk.

---

## AuraDB Free — capability map

**Tier:** AuraDB Free (cloud-managed, no credit card required)

| Capability | Limit | Fits substrate? | Fits trading pack? |
| --- | --- | --- | --- |
| Node limit | 200K (FAQ) / 50K (product page) — **inconsistent; verify in console** | ✅ comfortably | ✅ years at 1 run/day; ⚠️ months at 10 runs/day |
| Relationship limit | 400K (FAQ) / 175K (product page) — same inconsistency | ✅ | same caveat |
| Storage GB | Not published for Free tier | — | — |
| Instances | 1 per account | — | 1 is enough |
| Snapshots / backups | **Not available on Free tier** | — | ❌ no automated backup |
| Restore via API | **Forbidden (403) even on Professional** — console-only (DL-11) | — | manual only |
| Auto-pause | Yes — pauses on inactivity | ⚠️ adds latency on first request | ⚠️ same |
| Regions | Limited (no australiaeast) | ❌ latency to Azure australiaeast fleet | same |
| Cypher | Full | ✅ | ✅ |
| APOC | Not available on Free | ❌ if APOC queries needed | same |
| Price after Free limits hit | Must upgrade (Professional ~$65–260/mo) or self-host | — | — |

**Key verdict for trading pack:** AuraDB Free works for low-frequency runs (≤ 5/day). No automated
backups is the operational risk. Region mismatch to Azure australiaeast adds latency. **If the trial
ends and no paid plan is chosen, self-hosting Neo4j Community Edition in the existing Azure Container
Apps environment is the zero-cost path that removes all these constraints.**

**Key verdict for substrate:** overkill — the registry doesn't need graph queries, Cypher, or the
200K-node headroom. A simpler free-tier Azure store fits better and keeps the substrate independent.

---

## Azure free database offerings (always-free unless noted)

All of these live within the existing Azure subscription (australiaeast RG `trading-agents`).

| Service | What's free | API / query language | Good for |
| --- | --- | --- | --- |
| **Azure Cosmos DB — NoSQL API** | 1,000 RU/s + **25 GB** storage, lifetime, 1 account/subscription | JSON documents, SQL-like | substrate registry, small doc store |
| **Azure Cosmos DB — Gremlin API** | Same allowance (shared with NoSQL) | Gremlin graph traversal | trading provenance graph (but Gremlin ≠ Cypher) |
| **Azure Cosmos DB — MongoDB API** | Same allowance | BSON + Mongo wire | general document |
| **Azure Cosmos DB — Table API** | Same allowance | Key-value, OData | simple KV registry |
| **Azure Cosmos DB — vector search** | Built into NoSQL API, no extra cost | DiskANN / quantized flat | embeddings (forecaster, curator) |
| **Azure SQL Database** | 100K vCore-sec/month + 32 GB data + 32 GB backup, per-DB, up to 10 DBs, lifetime | T-SQL | relational data, audit logs |
| **Azure Table Storage** | Part of any storage account; pay-as-you-go (≈$0.045/GB/month) — not strictly free, but near-zero | REST, OData key-value | simplest KV; config, feature flags |
| **Azure Queue Storage** | Included in storage account; first 2M operations free/month | REST | job queues, orchestration triggers |
| **Azure Service Bus — Basic** | 10M operations free/month | AMQP | already used for agent bus in P14 |
| **Azure Cache for Redis — C0** | **12-month trial only**, then ~$16/mo | Redis commands | session cache, pub/sub |
| **Azure Blob Storage** | First 5 GB/month free (12 months then pay-as-you-go) | REST | model artefacts, dataset exports |

**Cosmos DB constraint:** one free-tier account per subscription. If Cosmos DB is chosen for *both*
the substrate registry and the trading pack provenance graph, they must share the same account and
the 1,000 RU/s / 25 GB allowance across containers. At the registry's traffic levels this is fine.

---

## Other graph/vector DB options

### Considered: cloud-hosted free tiers

| Product | Free limit | License | Cypher? | Vector? | Auto-delete? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| **Neo4j AuraDB Free** | 200K nodes / 400K rels (unverified) | Proprietary | ✅ | ✅ (vector index) | pauses on inactivity | see table above |
| **FalkorDB Cloud Free** | **100 MB RAM** | Source-available | ✅ (Cypher-like) | ✅ HNSW | stopped after 1 day idle; **deleted after 7 days** | Too small; no TLS; AWS/GCP only |
| **Memgraph Community** | Unlimited storage (self-hosted) | BSL 1.1 | ✅ 95% Cypher | ❌ | N/A (self-host) | Data must fit in RAM; no managed cloud free tier |
| **ArcadeDB** | Unlimited (self-hosted) | Apache 2.0 | ✅ 97.8% | ✅ built-in | N/A (self-host) | Best open-source option; 6 data models; MCP server; no managed cloud |
| **ArangoDB Community** | 100 GB cap (BSL 1.1) | BSL 1.1 (was Apache) | ❌ (AQL/Gremlin) | Enterprise only | N/A (self-host) | Licence changed 2024; not recommended |

### Considered: self-host in existing Azure Container Apps

The existing `trading-agents-env` Container Apps environment can run an additional container at
near-zero cost (scale-to-zero). This makes **Neo4j Community Edition** or **ArcadeDB** viable as
zero-licence-cost options inside the Azure estate.

| Option | Container image | Storage | Notes |
| --- | --- | --- | --- |
| **Neo4j Community** | `neo4j:5-community` | Azure File Share (pay-as-you-go) | Zero licence cost; full Cypher; all existing code works unchanged; no clustering; manual backup via `neo4j-admin dump` |
| **ArcadeDB** | `arcadedata/arcadedb` | Azure File Share | Apache 2.0; Cypher-compatible; vector search; multi-model; would require migration from Neo4j property graph schema |

**Self-host verdict:** neo4j Community in Container Apps is the lowest-friction fallback — existing
Cypher queries and graph schema work unchanged, and the Azure infra is already in place.

---

## Recommended placement

| Layer | Recommended store | Why |
| --- | --- | --- |
| **Substrate registry** (AgentInstance, Session, CapabilityGrant, CapabilityRoute) | **Azure Cosmos DB — NoSQL API** (free tier) | Already in Azure estate; 25 GB free (far more than needed); document API is sufficient (no graph traversal); vector search available for future use; keeps substrate independent of any graph engine |
| **Trading-pack provenance graph** (RunRequest → reporter lineage) | **Neo4j** — Aura Free while it serves; self-host Community Edition in Container Apps when limits bind | All existing Cypher queries and `kernel/graph_cypher.py` work unchanged; Aura Free covers years of daily single-batch runs; Container Apps self-host is the zero-cost escape hatch |
| **Future vector store** (forecaster embeddings, curator examples) | **Azure Cosmos DB vector search** (same account as registry) | Free, Azure-native, no extra service |

---

## What this implies for the codebase

1. **Substrate registry → replace `GraphStore` with a Cosmos DB client in the master.** The master
   currently registers agents and queries capabilities through the same `GraphStore` protocol used by
   the provenance graph. Implementing a `CosmosRegistryStore` (or adapting the existing `GraphStore`
   protocol to a document backend) decouples the substrate from Neo4j entirely.
2. **Trading pack keeps `Neo4jGraphStore`.** No change to the 7-agent spine, graph schema, or Cypher
   queries. The `kernel/graph_neo4j.py` + `kernel/graph_cypher.py` + `kernel/graph_support.py`
   investment is preserved exactly where it's needed.
3. **`GraphStore` protocol stays in `kernel/`.** It is already abstract; the substrate just gets a
   new backend. This is the clean extension ADR-0012 anticipated.

---

## Open questions before acting

1. **Verify AuraDB Free actual node/rel limits** — discrepancy between 200K and 50K. Log in to
   `console.neo4j.io` and check the instance limits panel for the free instance once created.
2. ~~Does the substrate actually need a persistent store?~~ **ANSWERED (2026-06-23): No.**
   Code inspection of `agents/master/agent.py` + `agents/master/store.py` confirms the registry
   writes (Session, AgentInstance, CapabilityGrant) are audit-only — nothing reads them back.
   Grants are computed from the in-memory `_grant_policy` dict. The master already works identically
   with `InMemoryGraphStore`. Recommended sprint: remove the `graph` parameter from `MasterAgent`
   and delete `agents/master/store.py` entirely — substrate becomes Neo4j-free.
3. **Cosmos DB Gremlin for the trading pack?** Possible (free, Azure-native, avoids Aura dependency)
   but requires rewriting every Cypher query as Gremlin — high migration cost for a working system.
   Not recommended unless Aura becomes genuinely untenable.

---

## Sources

- [Neo4j AuraDB FAQ](https://neo4j.com/cloud/platform/aura-graph-database/faq/)
- [Aura Free Tier Support Article](https://support.neo4j.com/s/article/16094506528787-Support-resources-and-FAQ-for-Aura-Free-Tier)
- [Azure Cosmos DB Lifetime Free Tier](https://learn.microsoft.com/en-us/azure/cosmos-db/free-tier)
- [Azure SQL Database Free Offer](https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer)
- [Azure Free Services](https://azure.microsoft.com/en-us/pricing/free-services)
- [Neo4j Alternatives 2026 — ArcadeDB comparison](https://arcadedb.com/blog/neo4j-alternatives-in-2026-a-fair-look-at-the-open-source-options/)
- [FalkorDB Cloud Free Tier](https://docs.falkordb.com/cloud/free-tier.html)
