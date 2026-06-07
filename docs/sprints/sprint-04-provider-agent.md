# Sprint 04 — Provider agent (first vertical-slice agent, P2 start)

**Status:** shipped (merged to `main` @ `fd1df0c`) · **Branch:** `sprint-04-provider-agent` · **Build phase:** P2 (first vertical slice)

## Goal

Implement the **`provider`** agent end-to-end over the in-process bus — the sole holder
of market-data credentials — answering its two typed capabilities (`get_market_data`,
`get_regime`) with validated data, honest quality accounting, and provenance written to
the Neo4j `GraphStore`. This is the **first real agent**, so it also establishes the
reusable patterns every later agent copies: how an agent injects the graph + external
sources + settings, lays out `domain/`, applies data-integrity gates, and writes
provenance. Gate stays infra-free (a fake data source + the in-memory graph).

## Why (context)

- `provider` is the root of the data graph (`depends_on=()`); scanner and analyst can't be
  built until it exists. It is the **only** agent allowed to hold data-API credentials.
- The kernel runtime is ready: in-process bus, `AgentBase`, and the Neo4j `GraphStore`
  (Sprint 03) are in place. Per the build-plan's *in-process-before-distributed* principle,
  this slice runs on `InProcessBus`; the distributed bus is not needed here.
- Read first: `docs/sprints/README.md` (guardrails + exact gate commands);
  **`contracts/provider.py`** (THE contract — implement it exactly, do not change it);
  `contracts/common.py` (`Provenance`, `Window`, `Ticker`, `RegimeLabel`, `_Frozen`);
  `kernel/agent.py` (`AgentBase` + `handlers`/`bind`), `kernel/bus.py`, `kernel/graph.py`
  (`GraphStore`, `Node`, `InMemoryGraphStore`), `kernel/config.py` (`AgentSettings`,
  `tunable`); `agents/provider/mission.md`; `docs/decisions/0001-neo4j-primary-store.md`
  (graph store, money as integer minor units, append-only); `docs/configuration.md`
  (tunables vs secrets).
- **Porting source (settled domain logic):** v1 at
  `C:\Users\yury_\Downloads\project\traiding-system\src\trading_v2\` — its provider/data
  clients (stooq, finnhub, fred) and regime classifier. Port the *logic*, refactored into
  <200-line modules; do not copy structure.

## Agent composition pattern (pinned — this is the template for all agents)

`AgentBase(contract, bus)` is unchanged. An agent injects its dependencies in its own
`__init__`, then registers handlers and binds:

```python
class ProviderAgent(AgentBase):
    def __init__(self, bus: MessageBus, *, graph: GraphStore,
                 source: DataSource, settings: ProviderSettings | None = None) -> None:
        super().__init__(CONTRACT, bus)         # CONTRACT from contracts/provider.py
        self._graph = graph
        self._source = source
        self._settings = settings or ProviderSettings()
        self.handlers = {
            "get_market_data": self._get_market_data,   # (DataRequest) -> MarketData
            "get_regime": self._get_regime,             # (RegimeRequest) -> RegimeContext
        }
    # AgentBase.bind() validates inbound/outbound against the contract automatically.
```

Tests build `ProviderAgent(bus, graph=InMemoryGraphStore(), source=FakeDataSource(...),
settings=ProviderSettings(...))` then `.bind()` — exactly how `EchoAgent` used the bus in
`tests/test_bus.py`, now with real dependencies.

## Key design constraints (do not break)

- **Implement `contracts/provider.py` exactly.** Both capabilities, the typed payloads as
  written. Don't modify the contract or the boundary map (the meta-test must stay green).
- **The one rule.** `agents/provider/` imports `kernel` + `contracts` only — never another
  agent. `import-linter` enforces.
- **Sole credential holder.** All external calls go through a `DataSource` port; only the
  real client reads creds (from settings/env). Credentials must **never** appear in any
  output payload (`never: expose raw provider credentials downstream`).
- **Deterministic by default.** Integrity gates and regime classification are deterministic
  code with **justified tunables** (`kernel.tunable(why=..., ge/le)`) — no magic numbers, no
  LLM.
- **Provenance + append-only.** Write `MarketSnapshot` / `Regime` / `Ticker` nodes via the
  injected `GraphStore` (`merge_node`, append-only) and set `Provenance.graph_node_id` on
  outputs. Any money value stored as integer minor units (ADR-0001).
- **Faults, not silent failure.** Wrap fallible fetch/parse work in `fault_boundary`; a
  degraded/missing source yields an honest `DataQualityTrace` (and the `market_data_degraded`
  signal), never a crash.
- **Infra-free gate.** A `FakeDataSource` + `InMemoryGraphStore` cover the unit gate (no
  network, no Neo4j). Real clients are `@pytest.mark.integration` and skip without
  network/keys.
- **Small files, headers, < 200 lines** each; split `domain/` as needed.

## Deliverables

1. **`agents/provider/sources.py`** — a `DataSource` Protocol (e.g. `fetch_ohlcv(tickers,
   window) -> tuple[OHLCVBar, ...]`, `fetch_regime_inputs(as_of) -> RegimeInputs` with at
   least `vix`; fundamentals/news may return empty for now), plus a deterministic
   `FakeDataSource` for tests. One **real** keyless client `StooqDataSource` (OHLCV) behind
   the port, exercised only by an integration test. Keyed sources (finnhub/fred/edgar/
   finbert) are deferred (out of scope) — they slot behind this same port later.

2. **`agents/provider/settings.py`** — `ProviderSettings(AgentSettings)` with
   `env_prefix="PROVIDER_"`. Tunables (`kernel.tunable(why=..., bounds)`): the regime policy
   inputs (`base_min_confidence`, `base_stop_loss_pct`, `base_take_profit_pct`,
   `base_max_holding_days`), the integrity thresholds (e.g. `max_daily_move_sigma`), and the
   regime VIX thresholds. **Credentials** (`finnhub_api_key`, `fred_api_key`) are secrets,
   not tunables — plain env-read fields, never logged or returned. (v1's global `.env` values
   like `STOP_LOSS_PCT` are the porting reference for defaults.)

3. **`agents/provider/domain/`** — deterministic logic:
   - `integrity.py`: ingest gates (N-sigma daily-move check, missing-field / NaN-Inf reject,
     staleness) producing a `DataQualityTrace` (requested/returned/used_fallback/
     stale_tickers/notes).
   - `regime.py`: classify VIX (+ optional breadth) into a `RegimeLabel` via tunable
     thresholds and assemble the `base_*` policy inputs from settings.

4. **`agents/provider/store.py`** — the agent↔graph write path: given validated data, mint a
   `run_id`, `merge_node` the `MarketSnapshot` / `Ticker` / `Regime` nodes and their edges,
   and return the `graph_node_id` for `Provenance`. (This is the template for every agent's
   `store.py`.)

5. **`agents/provider/agent.py`** — `ProviderAgent(AgentBase)` per the pinned pattern:
   `_get_market_data` (fetch via source → integrity gate → write provenance → return
   `MarketData` with `quality` + `provenance`) and `_get_regime` (fetch inputs → classify →
   write `Regime` node → return `RegimeContext`). Degraded data sets `quality`/`incident_refs`
   and the `market_data_degraded` path; nothing crashes.

6. **`agents/provider/__init__.py`** — export `ProviderAgent`. Update
   `agents/provider/mission.md`: replace the stale **Postgres** data-ownership line with the
   graph model (nodes, not tables) per ADR-0001.

7. **Coverage source** — add `"agents"` to `[tool.coverage.run] source` in `pyproject.toml`
   so the ratchet now measures agent code, then re-tune the floor to the new measured value
   (never below the meaningful floor). Add any client dep (e.g. `httpx`) to `dev` + the
   `runtime` extra; flag the choice.

8. **`agents/provider/tests/`** (pytest already includes `agents/` in `testpaths`):
   - **Unit (gate; `FakeDataSource` + `InMemoryGraphStore`):** `get_market_data` round-trips
     over the bus → validated `MarketData` with `provenance.graph_node_id` set and a
     `MarketSnapshot` node present in the graph; an injected anomaly (>Nσ move / NaN) is
     caught → `DataQualityTrace` flags it (stale/notes/used_fallback), no crash; a source
     failure records exactly one fault and returns degraded data; `get_regime` maps VIX →
     the right `RegimeLabel` + `base_*` policy; **no credential string appears in any output**.
   - **Integration (`@pytest.mark.integration`, skips without network):** `StooqDataSource`
     fetches real OHLCV for one ticker.

## Steps

1. Branch `sprint-04-provider-agent` off `main`.
2. `sources.py` (port + `FakeDataSource` + `StooqDataSource`); `settings.py`.
3. `domain/integrity.py` + `domain/regime.py`.
4. `store.py` (graph provenance writes); `agent.py` (the two handlers); `__init__.py`;
   refresh `mission.md`.
5. Add `agents` to coverage source + the client dep; `uv sync`.
6. Write `agents/provider/tests/`.
7. Run the gate; re-tune the coverage floor to the new measured value. Push; hand back.
   Do not merge to `main`.

## Acceptance criteria

- Both capabilities answer over the in-process bus with validated payloads; `import-linter`
  KEPT (provider imports only kernel + contracts); boundary meta-test still green.
- The `DataSource` port + `FakeDataSource` keep the unit gate **infra-free**; the Stooq
  integration test passes with network and skips cleanly without it.
- Provenance nodes are written and `Provenance.graph_node_id` is set; `DataQualityTrace` is
  honest on degraded inputs; no credential leaks (a test proves it).
- All modules headered, < 200 lines; tunables justified; no magic numbers.
- `agents` is in the coverage source; `make ci` green at/above the re-tuned floor.

## Out of scope (do NOT build this sprint)

Keyed/extra sources (finnhub, fred, edgar, finbert, S&P-500 listing) — each is a later
client behind the same port; the full v1 data-integrity suite (cross-provider canary,
survivorship-aware universe); fundamentals/news beyond empty stubs; the scanner/analyst
agents; the distributed bus; MCP (`mcp.py`). Flag anything you think is needed earlier.

## Handback report (paste into the PR / reply)

- Files added/changed and final line counts; the `DataSource` port shape and which real
  client landed; the client dep chosen.
- New coverage % and the re-tuned floor (and that `agents` is now measured).
- How provenance + degraded-data + credential-safety are handled; any design decision worth
  recording; anything out of scope.

The planning agent will review, merge to `main`, and update `docs/STATE.md` +
`docs/build-plan.md`.
