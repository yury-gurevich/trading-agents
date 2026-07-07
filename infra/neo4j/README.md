# Local Neo4j (Docker)

Neo4j is no longer the primary store after [ADR-0014](../../docs/decisions/0014-postgresql-system-of-record.md).
This local Docker instance is retained only as an ad-hoc analysis workbench, per amended
[ADR-0008](../../docs/decisions/0008-neo4j-hosting-local-docker.md). It is never a runtime
rollback backend after S118.

**Single source of truth for the workbench:** [`local/docker-compose.yml`](local/docker-compose.yml) —
Neo4j **Enterprise** (dev/eval) with the **APOC** + **Graph Data Science** plugins, all state
bind-mounted under `local/` so you can browse/edit it straight from the filesystem.

> The earlier named-volume compose (`infra/neo4j/docker-compose.yml`) plus its `.env` /
> `.env.example` were **retired 2026-06-18** and moved to the sibling `trading-agent-del/`
> staging folder. Rationale + restore steps: [`docs/repo-hygiene.md`](../../docs/repo-hygiene.md).

## Start

```bash
cd infra/neo4j/local && docker compose up -d
```

- Browser: <http://localhost:7474>  ·  Bolt: `bolt://localhost:7687`  ·  user `neo4j`
- Default database: **`traiding-agents`** (Enterprise named db; the `neo4j` db is never created).
- State persists as bind mounts under `local/`: `data/ conf/ logs/ plugins/ import/ backups/`.

## Runtime boundary

PostgreSQL is the runtime system of record. Do not point application env at this workbench.
Use it only for manual investigation or future one-off snapshot analysis.

## Edition

**Enterprise** (dev/eval) is required here for the **named default database** (`traiding-agents`)
and the **GDS** plugin. The eval license is free for development/testing, **not production**.
To drop to Community later: image `neo4j:<ver>-community`, remove the license env, and use the
default `neo4j` database (Community exposes only the default db) — at the cost of the named db and
Enterprise GDS. Rationale + parallelism analysis: ADR-0008.
