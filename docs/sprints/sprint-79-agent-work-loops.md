# Sprint 79 — Agent work loops: "check graph → do work"

**Phase:** P15 (multi-agent container split)
**Branch:** `sprint-79-agent-work-loops`
**Status:** planned

---

## Goal

Replace `idle_loop()` in all 12 non-provider trading agent entrypoints with the
"graph-as-queue" pull loop: each agent wakes up, asks the graph for unprocessed work,
processes it, writes results, and sleeps. After this sprint every agent can be started
independently and will pick up from wherever the upstream agent left off in the DB.

This is the "one container at a time" proof for the full trading pipeline:

```
provider → writes DataNode/NewsItem
scanner  → reads DataNode, writes ScanResult
analyst  → reads ScanResult, writes AnalystRun
pm       → reads AnalystRun, writes PMRun/Position
execution → reads PMRun, writes OrderIntent/Fill
monitor  → reads Fill, writes CloseDecision
reporter → reads CloseDecision, writes RunSnapshot
```

---

## Prerequisites

- S77 merged (credential naming correct)
- S78 merged (`build_graph_from_env()` in kernel, provider ingest loop working)
- At least one day of provider data in Aura so downstream agents have something to process

---

## Design: the "is there work?" query per agent

Each agent needs one graph query that returns "pending" work items:

| Agent | Pending query (Cypher sketch) |
| --- | --- |
| scanner | `MATCH (w:ScanWindow) WHERE NOT (w)-[:HAS_RESULT]->(:ScanResult) RETURN w` |
| analyst | `MATCH (r:ScanResult) WHERE NOT (r)-[:ANALYZED_BY]->(:AnalystRun) RETURN r` |
| pm | `MATCH (r:AnalystRun) WHERE NOT (r)-[:PM_RUN]->(:PMRun) RETURN r` |
| execution | `MATCH (r:PMRun) WHERE NOT (r)-[:EXECUTED_BY]->(:Fill) AND r.approved=true RETURN r` |
| monitor | `MATCH (p:Position) WHERE NOT (p)-[:CLOSED_BY]->(:CloseDecision) RETURN p` |
| reporter | `MATCH (p:PMRun) WHERE NOT (p)-[:REPORTED_IN]->(:RunSnapshot) RETURN p` |

These are the *starting point* queries — they will be refined as we learn what's
actually in the graph schema. The exact Cypher depends on the node/rel names the
current agents write; check `contracts/*.py` and `agents/*/graph_*.py` files.

Control-plane agents (supervisor, curator, researcher, operator) get minimal stubs
for now — their "work" is less well-defined at this stage.

---

## Scope

### 1 — Per-agent `_find_pending(graph)` function

One module per agent: `agents/<name>/poll.py`. Each exports:

```python
def find_pending(graph: GraphStore) -> list[<InputType>]:
    """Return items in the graph that this agent hasn't processed yet."""
    ...
```

Keeps the entrypoint thin; the query is independently testable with `InMemoryGraphStore`.

### 2 — Generic `work_loop()` in `kernel/`

A shared helper to avoid repeating the loop in each entrypoint:

```python
def work_loop(
    find_pending: Callable[[], list[T]],
    process_one:  Callable[[T], None],
    poll_interval: int = 60,
) -> None:  # pragma: no cover  (blocks forever; tested via the individual pieces)
    while True:
        items = find_pending()
        for item in items:
            process_one(item)
        if not items:
            time.sleep(poll_interval)
```

Each agent entrypoint calls `work_loop(find_pending=..., process_one=agent.run)`.

### 3 — Replace `idle_loop()` in 11 entrypoints

Replace for: scanner, analyst, portfolio_manager, execution, monitor, reporter.
Stub loop (no-op pending work) for: operator, supervisor, curator, researcher,
forecaster (its work is triggered by explicit `sentiment_scorecard` requests — later).

### 4 — `make ci` green

- `find_pending()` functions must have unit tests with `InMemoryGraphStore` (seed
  some nodes with/without downstream results; assert correct items returned).
- `work_loop` is `# pragma: no cover` (infinite loop); test the pieces.

---

## "One container at a time" manual test sequence

```powershell
# Step 1: start provider (S78), let it ingest one day
ta deploy provider
# verify: ta graph  →  DataNode nodes appear

# Step 2: start scanner
ta deploy scanner
# verify: ta graph  →  ScanResult nodes appear

# Step 3: start analyst
ta deploy analyst
# verify: ta graph  →  AnalystRun nodes appear

# ... and so on
# Step N: start reporter → RunSnapshot in graph → ta graph shows full pipeline
```

Each step is independently verifiable. No agent needs to be alive for the next one
to start — it just needs DB rows to be present.

---

## Files to create / modify

| File | Change |
| --- | --- |
| `kernel/work_loop.py` | New — `work_loop()` generic helper |
| `agents/scanner/poll.py` | New — `find_pending()` for scanner |
| `agents/analyst/poll.py` | New — `find_pending()` for analyst |
| `agents/portfolio_manager/poll.py` | New |
| `agents/execution/poll.py` | New |
| `agents/monitor/poll.py` | New |
| `agents/reporter/poll.py` | New |
| `agents/{name}/entrypoint.py` (×11) | Replace `idle_loop()` with `work_loop()` call |
| `tests/test_work_loop.py` | Unit tests for the kernel helper |
| `tests/agents/{name}/test_poll.py` (×6) | Unit tests per agent poll function |
| `docs/design-log.md` | Mark DL-07c + DL-08 CLOSED |
| `docs/STATE.md` | Update at closeout |

---

## Exit criteria

- [ ] Starting only the scanner container (with provider data in the graph) produces
  `ScanResult` nodes in Aura within one poll interval
- [ ] Starting analyst after scanner produces `AnalystRun` nodes (without provider or
  scanner containers being alive)
- [ ] `make ci` green; coverage floor maintained; every `poll.py` module ≤ 200 lines
- [ ] `idle_loop()` is only called by entrypoints that have no work loop yet
  (forecaster / supervisor / curator / researcher stubs)

---

## Version bump

New capability (agents do real work). **0.18.0** (feat → MINOR, HARD RULE).

---

## Deferred (S80+)

- Forecaster work loop (triggered by curator promoting a model, not a DB poll)
- Supervisor / curator / researcher real work definitions
- P14 pub/sub as fast-path notification overlay (bus publishes "data ready" →
  agent wakes immediately instead of waiting for poll interval)
- Dispatcher container (triggers provider ingest on market-open/close schedule)
- Alpaca live keys in KV (after execution work loop is proven on paper)
