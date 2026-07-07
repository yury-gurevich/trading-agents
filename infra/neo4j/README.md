# Local Neo4j (Docker)

Neo4j is no longer the primary store after [ADR-0014](../../docs/decisions/0014-postgresql-system-of-record.md).
This local Docker instance is retained only as an ad-hoc analysis workbench and pre-S118 rollback backend,
per amended [ADR-0008](../../docs/decisions/0008-neo4j-hosting-local-docker.md).

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

## Point the app at it for rollback

PostgreSQL is the default. To use Neo4j before S118, unset `POSTGRES_DSN` and set the rollback env:

```env
POSTGRES_DSN=
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<see project-root .env — gitignored>
NEO4J_DATABASE=traiding-agents
```

Verify: `uv run --extra runtime python -c "from probes.creds import load_creds; from probes.checks import probe_neo4j; [print(r.status, r.dep, r.detail) for r in probe_neo4j(load_creds())]"`

## Edition

**Enterprise** (dev/eval) is required here for the **named default database** (`traiding-agents`)
and the **GDS** plugin. The eval license is free for development/testing, **not production**.
To drop to Community later: image `neo4j:<ver>-community`, remove the license env, and use
`NEO4J_DATABASE=neo4j` (Community exposes only the default db) — at the cost of the named db and
Enterprise GDS. Rationale + parallelism analysis: ADR-0008.
