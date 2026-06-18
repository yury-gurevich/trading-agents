# ADR 0008 — Neo4j hosting: local, in Docker, single instance

**Status:** Accepted · **Date:** 2026-06-18 · **Decider:** Yury Gurevich (product owner)

> This ADR decides **where the Neo4j server runs and how**. It does **not** revisit
> [ADR-0001](0001-neo4j-primary-store.md) (Neo4j is the single primary store) — that stands. It
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
3. **Community edition** is the default — it satisfies every guarantee the system relies on (ADR-0001
   was written *for* Community: ACID, unique-property constraints, vector index). It exposes only the
   default **`neo4j`** database, so `NEO4J_DATABASE=neo4j`. **Enterprise (free dev/eval license)** is a
   documented one-flag upgrade (`NEO4J_ACCEPT_LICENSE_AGREEMENT=yes`) *iff* we later want named
   databases, hot backup, or clustering/Fabric for read-scale experiments — see "Parallelism" below.
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

- **`infra/neo4j/docker-compose.yml`** (+ `infra/neo4j/.env.example`, README) is the reproducible
  install; `.env` (root) points at the container; `NEO4J_DATABASE=neo4j` under Community.
- **Always-on store** (`restart: unless-stopped`) means provenance/state can accrue continuously —
  this is what unblocks the **live news-accrual runway** the P12 scorecard harness needs (see memory
  `sentiment-champion-challenger`), and lets us "start using it as state records" in earnest.
- **Neo4j Browser is not lost** — the container serves it on `http://localhost:7474`; Desktop or any
  Bolt client can still connect for ad-hoc exploration.
- **`trading-agent` named db is dropped** under Community (default `neo4j` db). Docs/memory that named
  it are updated. (Re-obtainable under Enterprise if ever wanted.)
- **Migration is clean** (empty graph): stop the Desktop instance, `docker compose up -d`, repoint
  `.env`, verify `DEP-NEO4J` green. Desktop + `.env.bak` remain as rollback.

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

- [ADR-0001 — Neo4j as the single primary store](0001-neo4j-primary-store.md) — *what* Neo4j is for
  (provenance graph + transactional truth + RAG); this ADR decides *where it runs*.
- [ADR-0007 — container-per-agent + master bootstrap](0007-container-per-agent-master-bootstrap.md) —
  the container philosophy this aligns with; Neo4j is the operational registry there.
- `docs/deployment.md` — deployment surfaces (interim monolith; Neo4j hosting note).
- `docs/architecture.md` §"Data: one store, three jobs" — the store's role.
- Memory `neo4j-aura-to-local-migration` — the cutover record + password-reset recovery steps.
