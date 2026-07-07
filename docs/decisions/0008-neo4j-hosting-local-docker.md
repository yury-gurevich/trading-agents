---
type: Architecture Decision
status: amended
closes: "Where does Neo4j run in dev/staging? Aura cloud vs Desktop vs Docker? Single instance or cluster?"
tags: [neo4j, docker, hosting, aura, analysis]
---

# ADR 0008 — Neo4j hosting: local, in Docker, single instance

**Status:** Amended · **Date:** 2026-06-18 · **Decider:** Yury Gurevich (product owner)

> **Amendment (2026-07-07) — scope narrowed to analysis only.** ADR-0014 supersedes
> ADR-0001 and makes PostgreSQL the system of record. This ADR now records how to run Neo4j only when
> it is intentionally used as an ad-hoc analysis workbench; it no longer describes production
> primary-store hosting or rollback.

> This ADR decides **where the Neo4j server runs and how when Neo4j is deliberately enabled**. It
> records the move off **Neo4j Aura (cloud)** to a **local** instance, why we run it as a **Docker
> container** rather than Neo4j Desktop, and why a **single instance** (not a cluster) is correct.
> It also analyses the "can several Neo4j instances share one graph for parallel processing?"
> question so the answer is on record.

## Context

- **Cost.** Aura's minimum *paid* graph tier is ~**$260/month**. For a single-operator system that
  has not yet accrued data, that is not justified. "Local for now, managed cloud when the product
  earns it."
- **Clean moment.** The live Aura instance was verified **empty** (0 nodes) on 2026-06-18, so the
  cutover is a config swap with nothing to export. We cut over early (2026-06-18) rather than wait for
  the 2026-06-28 Aura expiry — see memory `neo4j-aura-to-local-migration`.
- **A real friction surfaced.** The local instance was first stood up via **Neo4j Desktop 2**. Desktop
  is excellent for interactive browsing, but its lifecycle is **GUI-tied**: it could not be started/
  managed headlessly, the `neo4j` password was Desktop-encrypted and unrecoverable (had to be reset),
  and to bring it up out-of-band the server had to be launched *outside* Desktop. That is the opposite
  of the reproducible, code-managed substrate the rest of the system targets.
- **We are already settled on containers.** [ADR-0007](0007-container-per-agent-master-bootstrap.md)
  commits the fleet to one Docker image per agent on Azure Container Apps. A local **Docker engine on
  WSL2, managed by Portainer**, is already the owner's day-to-day environment.

## Decision

1. **Run Neo4j locally as a dedicated Docker container** (`infra/neo4j/docker-compose.yml`), on the
   WSL2 Docker engine, Portainer-managed — **not** as a Neo4j Desktop instance. Desktop is retained
   only as an optional ad-hoc GUI/browser that can point at the container's Bolt endpoint.
2. **One instance, not a cluster.** A single Neo4j DBMS process serves all agents. See the analysis
   below for why this is sufficient (and why clustering is premature).
3. **Enterprise edition during development** (free dev/eval license,
   `NEO4J_ACCEPT_LICENSE_AGREEMENT=eval`), **with the application kept Community-portable on purpose.**
   *Revised 2026-06-18* from an initial Community lean, after weighting the goal of **automated backup +
   point-in-time restore + hands-free recovery** — which only Enterprise provides (online/differential
   backup + restore-to-time; Community has offline dumps only). Production Enterprise is unaffordable
   (~$250K/yr), so the permanent edition is **deliberately deferred**: Enterprise-in-dev buys the
   features *and the information* to decide later, while a **Community-portability discipline** keeps the
   cheap exit open:
   - **App logic must not depend on an Enterprise-only feature** (no RBAC-as-auth, no CDC-driven logic,
     no Fabric/cross-db queries in agent code).
   - **Enterprise *ops* features (online backup, PITR) are allowed** — ops layer only, each with a
     documented Community fallback (offline dump).
   - The named **`trading-agent`** db is a *soft* dependency (Enterprise→Community = a 2-command
     `dump`/`load`-rename).
   - **Enforcement:** the integration suite must stay runnable against a throwaway Community container —
     the checkable invariant, not a hope.
   - `// TODO` **permanent edition + hosting placement** (which box, RAM/cores; prod = pay vs managed
     Aura vs Community+gap-code) — decided *after* we know which features we use.
   Image size is a non-issue: Enterprise `2025.08` = **778 MB** vs Community **634 MB**; the real lever
   is runtime heap/page-cache (tunable, edition-agnostic).
4. **Persistence + lifecycle:** the graph store lives on a **named Docker volume** (survives container
   recreation), `restart: unless-stopped`, a healthcheck on Bolt, published ports `7474` (HTTP/Browser)
   and `7687` (Bolt). Credentials come from a **gitignored** `infra/neo4j/.env` (never committed).
5. **App ↔ Neo4j networking:** the app on the host (via `uv`) reaches the container at
   `neo4j://127.0.0.1:7687`. A **containerised** app reaches it via a shared Docker network (by service
   name) or `neo4j://host.docker.internal:7687` — a container's own `127.0.0.1` is itself.

## Why local in *this* configuration (the reasons, on record)

| Choice | Why this and not the alternative |
| --- | --- |
| **Local, not Aura/cloud** | ~$260/mo for the min paid tier; no data yet to justify it. Cloud is deferred until the product earns it (consistent with ADR-0001's "no premature infrastructure"). |
| **Docker, not Neo4j Desktop** | Reproducible-as-code (committed compose), headless + restart-policied lifecycle, Portainer-managed, isolated, and **the same shape it will run in production** (a container) per ADR-0007. Desktop's GUI-tied lifecycle was the concrete friction we hit. |
| **Single instance, not a cluster** | One node already serves all 12 agents concurrently (see below). Clustering buys read-scale/HA we do not need yet and (Enterprise) adds licensing + ops weight. |
| **Community, not Enterprise** | ADR-0001 designed the invariants around Community. The `trading-agent` *named* db was a Desktop happenstance (Desktop bundles Enterprise), never a design requirement — the code default is `neo4j`. Enterprise stays a documented upgrade, not a dependency. |

## Parallelism & shared data — the analysis (answering "can instances share one graph?")

**Short answer: no, you cannot point several Neo4j instances at the same physical store — and you do
not need to.**

- **One store, one process.** A Neo4j database directory is opened with an **exclusive lock**
  (`store_lock`). A second DBMS pointed at the same files (or the same Docker volume) **fails to
  start** — and forcing it would corrupt the store. There is no "shared-disk, multiple-writers" mode.
  *Do not mount one data volume into two Neo4j containers.*
- **The supported multi-instance model is replication, not sharing.** Neo4j **clustering** (Enterprise)
  gives each instance its **own copy** of the store, kept consistent by **Raft** (primary members) and
  async replication (secondary / **read replicas**). So "several instances over the same logical graph"
  = several *replicated copies*, not one shared store.
- **Reads scale; writes do not.** Across a cluster, **reads** fan out to any member → genuine read
  parallelism + HA. **Writes** still funnel through a **single leader per database** — graph writes do
  **not** scale horizontally. (Sharding via **Fabric** can partition data, but graphs shard poorly
  because relationships cross shards.) Treat the single write-leader as a fundamental property, not a
  bug to engineer around.
- **You already have intra-instance concurrency.** *One* Neo4j instance is fully concurrent: many
  simultaneous transactions and queries run in parallel (entity-level write locks; reads don't block).
  The 12 agents hitting one instance at once is exactly what it is built for. **Parallelism-for-
  correctness is satisfied by a single node.**

**Conclusion.** A single local container is the right answer now. The "parallel processing" idea is
real only for **reads at scale we don't have**, and is available later via **Enterprise read replicas**
(or Fabric) — a pleasant future option, not a goal. If we ever pursue it: each replica gets its own
volume; never a shared one. Nothing about the single-instance choice forecloses it.

## Consequences

- **`infra/neo4j/local/docker-compose.yml`** and the root `docker-compose.yml` `workbench` profile are
  reproducible analysis-workbench installs. Runtime `.env` does not select Neo4j.
- **No primary-store duty remains.** Provenance/state accrues in PostgreSQL (ADR-0014). Neo4j can be
  populated from exports or pointed at rollback data for ad-hoc graph exploration, not trusted as the
  normal runtime source of truth.
- **Neo4j Browser is still available** — the container serves it on `http://localhost:7474`; Desktop or
  any Bolt client can connect for ad-hoc exploration.
- **`trading-agent` named db is dropped** under Community (default `neo4j` db). Docs/memory that named
  it are updated. (Re-obtainable under Enterprise if ever wanted.)
- **Migration is complete:** runtime provenance/state accrues in PostgreSQL. Neo4j workbench data is
  loaded only for ad-hoc analysis when an investigation needs it.

## Alternatives considered

- **Neo4j Desktop (keep).** Best-in-class GUI, bundles Enterprise — but GUI-tied lifecycle, opaque
  credential storage, not reproducible-as-code, not how production runs. Rejected as the *primary*
  host; kept as an optional browser.
- **Aura / managed cloud.** Zero-ops, clustering/backups included — but ~$260/mo and premature.
  Deferred; revisit when the product earns it.
- **Enterprise cluster locally (now).** Read-scale + HA — but no current need, licensing + ops weight.
  Deferred; documented as the upgrade path.
- **Two instances sharing one data volume.** *Impossible* (exclusive store lock) and corrupting.
  Rejected on the facts.

## Links (how this fits the larger picture)

- [ADR-0014 — PostgreSQL is the system of record](0014-postgresql-system-of-record.md) — supersedes
  ADR-0001 and narrows Neo4j to workbench-only use.
- [ADR-0007 — container-per-agent + master bootstrap](0007-container-per-agent-master-bootstrap.md) —
  the container philosophy this aligns with.
- `docs/deployment.md` — deployment surfaces.
- `docs/architecture.md` §"Data: one store, three jobs" — the store's role.
- Memory `neo4j-aura-to-local-migration` — the cutover record + password-reset recovery steps.
