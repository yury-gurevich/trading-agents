# Sprint 78 — Provider as standalone graph-ingestor

**Phase:** P15 (multi-agent container split)
**Branch:** `sprint-78-provider-ingestor`
**Status:** shipped (0.17.00)

---

## Goal

Make the provider the **first "one container at a time" proof**: start one container,
watch data appear in the graph, stop it. All downstream agents can work off the DB
without provider being alive.

This implements the "graph as queue" pattern decided in DL-08: provider is the sole
data-write boundary; other agents pull from the graph at their own pace.

---

## Prerequisites

- S77 merged (canonical credential names — provider reads `PROVIDER_TIINGO_API_KEY`)
- DL-08a resolved: Neo4j credentials reach the provider container (recommend: plain
  Container App env vars for `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD`)

---

## Design: provider work loop

After `activate_agent()` and `_apply_config()` inject credentials, the provider
entrypoint runs an ingest loop:

```python
def main() -> None:
    payload = activate_agent(master_url, "provider", public_key_pem=pubkey)
    # _apply_config already wrote PROVIDER_TIINGO_API_KEY etc to os.environ
    settings = ProviderSettings()
    graph    = build_graph_from_env()   # reads NEO4J_URI from env
    agent    = ProviderAgent(settings, graph=graph)
    _ingest_loop(agent, settings)

def _ingest_loop(agent: ProviderAgent, settings: ProviderSettings) -> None:
    interval = int(os.environ.get("PROVIDER_POLL_INTERVAL", "3600"))  # 1h default
    universe = _load_universe()   # from env or a graph query
    while True:
        agent.run(universe, window=_today_window())
        time.sleep(interval)
```

The provider's `run()` already writes to the graph (`DataNode`, `NewsItem`,
`RegimeReading`, etc.) — no new graph writes needed. We're only replacing
`idle_loop()` with a real loop that calls `run()`.

---

## Scope

### 1 — `build_graph_from_env()` helper in `kernel/`

A small shared helper that reads `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` from
`os.environ` and returns the right `GraphStore`:

```python
def build_graph_from_env() -> GraphStore:
    uri = os.environ.get("NEO4J_URI", "")
    if not uri:
        from kernel import InMemoryGraphStore
        return InMemoryGraphStore()
    from kernel.graph_neo4j import Neo4jGraphStore  # pragma: no cover
    return Neo4jGraphStore()                         # pragma: no cover
```

Falls back to in-memory if `NEO4J_URI` is absent (local dev / CI without Neo4j).

### 2 — Provider entrypoint: replace `idle_loop()` with `_ingest_loop()`

Wire:

- `ProviderSettings()` (reads injected creds from env)
- `build_graph_from_env()`
- `ProviderAgent(settings, graph=graph)`
- Poll loop at configurable interval (`PROVIDER_POLL_INTERVAL` env var, default 3600s)

Universe source: `PROVIDER_UNIVERSE` env var (comma-separated tickers, e.g.
`"AAPL,MSFT,GOOGL"`) for now; later replaced by a graph query that reads the
`Universe` node written by the scanner.

### 3 — `deploy-agents.ps1`: pass Neo4j env vars to all agents

Add `NEO4J_URI`, `NEO4J_USER` as plain env vars; `NEO4J_PASSWORD` as a Container
App secret (stored in the app definition, not in Key Vault — same as the GHCR pull
secret). All agents get these; they only matter once an agent's entrypoint actually
uses the graph.

### 4 — Local smoke test

```powershell
# One container, watch DB fill up:
$env:PROVIDER_TIINGO_API_KEY = "..."
$env:NEO4J_URI = "neo4j+s://8cf6d231.databases.neo4j.io"
$env:PROVIDER_UNIVERSE = "AAPL,MSFT,TSLA"
python -m agents.provider.entrypoint
# then: ta graph  →  should show DataNode + NewsItem nodes for those tickers
```

### 5 — `make ci` green

`_ingest_loop` and `build_graph_from_env` must be fully unit-tested (inject fake graph,
fake agent, verify loop calls `run()` once per tick). Neo4j path stays `# pragma: no cover`.

---

## Files to modify

| File | Change |
| --- | --- |
| `kernel/__init__.py` or `kernel/graph_env.py` | New `build_graph_from_env()` helper |
| `agents/provider/entrypoint.py` | Replace `idle_loop()` with `_ingest_loop()` |
| `infra/deploy-agents.ps1` | Add `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` as env/secret |
| `docs/design-log.md` | Mark DL-08a CLOSED with chosen option |
| `docs/STATE.md` | Update at closeout |

---

## Exit criteria

- [ ] `python -m agents.provider.entrypoint` (with fake master that returns ACTIVATE)
  calls `ProviderAgent.run()` at least once and exits cleanly
- [ ] After a real run against Aura, `ta graph` shows `DataNode` / `NewsItem` nodes
  for the configured universe tickers
- [ ] CI green; provider entrypoint test covers the loop (fake clock or `maxiter=1`)
- [ ] No other agent entrypoints changed (they still `idle_loop()` — S79 handles them)

---

## Version bump

New capability (provider does real work). **0.17.0** (feat → MINOR, HARD RULE).

---

## Deferred (S79)

- Scanner, analyst, PM, execution, monitor, reporter work loops ("check graph → do work")
- The "is there unprocessed data for me?" graph-query function per agent
- Dispatcher trigger (optional, once manual testing validates the loop works)
