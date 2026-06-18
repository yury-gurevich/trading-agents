# Local Neo4j (Docker)

The system's primary store (graph + provenance + RAG, [ADR-0001](../../docs/decisions/0001-neo4j-primary-store.md))
runs as a single local Docker container per
[ADR-0008](../../docs/decisions/0008-neo4j-hosting-local-docker.md).

## Start

```bash
cp infra/neo4j/.env.example infra/neo4j/.env   # set NEO4J_LOCAL_PASSWORD (match root .env)
cd infra/neo4j && docker compose up -d          # or deploy as a Portainer stack
```

- Browser: <http://localhost:7474>  ·  Bolt: `neo4j://127.0.0.1:7687`  ·  user `neo4j`
- The graph persists on the `neo4j-data` named volume across container recreation.

## Point the app at it

In the **project-root** `.env`:

```
NEO4J_URI=neo4j://127.0.0.1:7687       # neo4j://host.docker.internal:7687 if the app is itself in a container
NEO4J_USER=neo4j
NEO4J_PASSWORD=<same as NEO4J_LOCAL_PASSWORD>
NEO4J_DATABASE=neo4j                    # Community exposes only the default db
```

Verify: `uv run --extra runtime --extra probes python -c "from probes.creds import load_creds; from probes.checks import probe_neo4j; [print(r.status, r.dep, r.detail) for r in probe_neo4j(load_creds())]"`

## Edition

Community (default) covers everything the system needs. For **named databases / clustering /
Fabric / hot-backup**, switch the image to `neo4j:<ver>-enterprise` and add
`NEO4J_ACCEPT_LICENSE_AGREEMENT: "yes"` (free dev/eval license). Rationale + the parallelism
analysis: ADR-0008.
