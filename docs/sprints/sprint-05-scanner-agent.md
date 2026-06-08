# Sprint 05 — Scanner agent (first agent-to-agent call, P2)

**Status:** active · **Branch:** `sprint-05-scanner-agent` · **Build phase:** P2 (first vertical slice)

## Goal

Implement the **`scanner`** agent end-to-end over the in-process bus: reduce a named
universe to a small, ranked, fully-explained candidate set by **requesting market data
from `provider` over the bus** (never fetching it itself), and write the provenance
(`ScanRun`, `Candidate`) with a **cross-agent lineage edge** back to the provider's
`MarketSnapshot`. This is the **first agent-to-agent call** in the system, so it also
establishes the inter-agent request pattern every later agent copies. Gate stays infra-free.

## Why (context)

- `scanner` is the second step of the P2 slice (`provider → scanner → analyst`) and the
  first agent that *depends on another* (`depends_on=("provider",)`). It must reach provider
  **only via a typed message**, never an import (the one rule; `import-linter` enforces).
- Establishes two firsts: an agent calling another over the bus, and provenance lineage that
  spans agents (`Candidate → ScanRun → MarketSnapshot`) — the substrate for the P2 exit
  ("a request produces explained recommendations with full provenance").
- Read first: `docs/sprints/README.md` (guardrails + gate); **`contracts/scanner.py`** (THE
  contract — implement exactly) and `contracts/provider.py` (`DataRequest`/`MarketData` you
  will call); `contracts/common.py` (`ScanRequest`, `Explanation`, `Provenance`);
  `agents/provider/agent.py` + `agents/provider/sources.py` (the agent pattern + how to wire
  a provider in tests); `kernel/agent.py`, `kernel/bus.py`, `kernel/envelope.py` (the
  `AgentMessage` you build), `kernel/graph.py`, `kernel/config.py`; `tests/test_bus.py` (how
  a request flows over `InProcessBus`); `agents/scanner/mission.md`; ADR-0001.
- Porting source: v1 `src/trading_v2/` scanner filters (relative strength, returns, beta,
  earnings proximity). Port the *logic* into <200-line modules; do not copy structure.

## Pinned: how an agent calls another agent (the inter-agent pattern)

The scanner's handler sends a typed request through `self.bus` and consumes the response —
never importing provider. Build the envelope exactly as `tests/test_bus.py` does:

```python
from kernel import AgentMessage
from contracts.provider import DataRequest, MarketData

req = AgentMessage(
    sender="scanner", recipient="provider", message_type="request",
    capability="get_market_data",
    payload=DataRequest(tickers=tickers, window=window).model_dump(mode="json"),
)
resp = self.bus.request(req)                    # synchronous over InProcessBus
if resp.message_type == "error":
    ...                                         # degrade honestly (FilterTrace/Explanation)
else:
    market = MarketData.model_validate(resp.payload)
```

This is the template for every downstream agent (analyst→scanner/provider, pm→analyst, …).

## Key design constraints (do not break)

- **Implement `contracts/scanner.py` exactly** — `run_scan(ScanRequest) -> CandidateSet`
  and `explain_filter(ScanRequest) -> Explanation`. Don't change the contract or the
  boundary map (meta-test stays green).
- **The one rule.** `agents/scanner/` imports `kernel` + `contracts` only — **never
  `agents.provider`**. Reach provider through `self.bus.request(...)`. `import-linter`
  enforces ("agents may not import one another KEPT").
- **No external I/O.** `external_io=()`. The scanner never calls a data API; all market data
  comes from provider. The universe is resolved via an injected `UniverseSource` (a
  *configured* list, not an external fetch — see deliverable 2 and the scope note).
- **Explain every drop.** `FilterTrace` accounts for the universe shrinking
  (universe_size/evaluated/dropped_by_filter); `Candidate.survived_filters` lists what each
  passed; `CandidateSet.explanation` summarizes. Explainable-silence is a contract
  obligation, not optional.
- **Cross-agent provenance.** Write `ScanRun` + `Candidate` nodes, the
  `Candidate -[:SURVIVED]-> ScanRun` edges (per mission), and a
  `ScanRun -[:DERIVED_FROM]-> MarketSnapshot` edge using the provider response's
  `provenance.graph_node_id` (parse `"MarketSnapshot:<key>"` → `get_node` → `add_edge`).
  If the snapshot node isn't found, skip that edge gracefully.
- **Deterministic + faults.** Filters/ranking are deterministic with **justified tunables**
  (no magic numbers). Wrap the provider call + parsing in `fault_boundary`; a provider error
  or degraded data yields an honest empty/explained `CandidateSet`, never a crash.
- **Small files, headers, < 200 lines**; secrets n/a here.

## Deliverables

1. **`agents/scanner/agent.py`** — `ScannerAgent(AgentBase)` per the provider pattern
   (inject `graph`, `universe`, `settings`, `sink`; `super().__init__(CONTRACT, bus)`;
   `handlers` for `run_scan` + `explain_filter`). `run_scan`: resolve universe → derive the
   lookback `Window` (tunable) → request `get_market_data` from provider over the bus → run
   filters + ranking → write provenance → return `CandidateSet`. `explain_filter`: return an
   `Explanation` for the named ticker's pass/fail.

2. **`agents/scanner/universe.py`** — a `UniverseSource` Protocol (`members(universe: str) ->
   tuple[Ticker, ...]`) + a `StaticUniverse` (configured tuple; default a small built-in set)
   and a `FakeUniverse` for tests. (Not an external fetch — boundary-clean. The real S&P-500
   listing is provider-owned; feeding it from provider is a flagged follow-up.)

3. **`agents/scanner/settings.py`** — `ScannerSettings(AgentSettings)`, `env_prefix=
   "SCANNER_"`. Justified tunables: the lookback window (days), filter thresholds (e.g.
   `min_relative_strength`, min price/volume), and the candidate cap (top-N). All via
   `kernel.tunable(why=..., bounds)`.

4. **`agents/scanner/domain/`** — deterministic logic:
   - `filters.py`: apply the filter chain to the per-ticker market data, recording each drop
     into a `FilterTrace` and the `survived_filters` per surviving ticker.
   - `ranking.py`: score + rank survivors into `Candidate`s (rank, score, metrics).

5. **`agents/scanner/store.py`** — graph writes: `ScanRun` + `Candidate` nodes, the
   `SURVIVED` edges, and the cross-agent `DERIVED_FROM` edge to the provider `MarketSnapshot`;
   return `Provenance` with `graph_node_id`.

6. **`agents/scanner/__init__.py`** — export `ScannerAgent`. Update
   `agents/scanner/mission.md`: replace the stale **Postgres** ownership line with the graph
   model (ADR-0001).

7. **`agents/scanner/tests/`** — infra-free (`InProcessBus` + `InMemoryGraphStore` +
   a real `ProviderAgent` wired with a `FakeDataSource`, both `.bind()`-ed; `FakeUniverse`):
   - `run_scan` over the bus returns a ranked `CandidateSet` with a populated `FilterTrace`,
     `survived_filters`, an `explanation`, and `provenance.graph_node_id`; the right tickers
     survive given fixture bars + thresholds.
   - **Provenance lineage:** `ScanRun` + `Candidate` nodes exist, `SURVIVED` edges present,
     and the `ScanRun -[:DERIVED_FROM]-> MarketSnapshot` edge links to the provider's node
     (assert via `descendants`/`ancestors`).
   - **Degraded path:** when the provider returns an error/degraded data, `run_scan` returns
     an empty, explained `CandidateSet` (no crash) and records a fault.
   - `explain_filter` returns a grounded `Explanation`.
   - Confirm the scanner does **not** import `agents.provider` (the bus call is the only link).

## Steps

1. Branch `sprint-05-scanner-agent` off `main`.
2. `universe.py`, `settings.py`; `domain/filters.py` + `domain/ranking.py`.
3. `store.py` (graph + cross-agent edge); `agent.py` (the two handlers + the bus call);
   `__init__.py`; refresh `mission.md`.
4. Write `agents/scanner/tests/` (wire a real provider on the bus).
5. Run the gate; re-tune the coverage floor to the new measured value. Push; hand back. Do
   not merge to `main`.

## Acceptance criteria

- Both capabilities answer over the in-process bus; the scanner obtains market data **only**
  via `self.bus.request` to provider; `import-linter` "agents may not import one another"
  KEPT; boundary meta-test green.
- `CandidateSet` is ranked and fully explained (`FilterTrace` + `survived_filters` +
  `explanation`); degraded provider data yields an honest empty result, not a crash.
- Provenance nodes/edges written, including the cross-agent `DERIVED_FROM → MarketSnapshot`
  lineage; a test asserts the chain.
- All modules headered, < 200 lines; tunables justified; no magic numbers.
- `make ci` green at/above the re-tuned coverage floor; gate needs no external infra.

## Out of scope (do NOT build this sprint)

A provider-fed real S&P-500 universe (needs a new provider capability — flag it; this slice
uses a configured `UniverseSource`); the analyst agent; the full v1 filter suite beyond a
sensible core (earnings proximity, sector caps, etc. are later); `scan_completed` emission as
a real pub/sub message (no pub/sub until P4 — record it in provenance for now); MCP
(`mcp.py`). Flag anything you think is needed earlier.

## Handback report (paste into the PR / reply)

- Files added/changed and final line counts; the inter-agent call + cross-agent provenance
  approach; the filter/ranking subset implemented; how the universe is resolved.
- New coverage % and the re-tuned floor.
- Any design decision worth recording or anything that felt out of scope.

The planning agent will review, merge to `main`, and update `docs/STATE.md` +
`docs/build-plan.md`.
