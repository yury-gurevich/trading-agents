# Sprint 83 — Graph-pull orchestration trigger + end-to-end demonstrator

**Phase:** P15 (multi-agent container split)
**Branch:** `sprint-83-graph-pull-orchestration`
**Status:** shipped (0.22.00)

---

## Goal

Give the graph-pull fleet an explicit **start**: one dispatcher-placed trigger that kicks
off a run, after which every downstream agent wakes itself off its prerequisite gate. Before
this sprint the provider self-triggered on a timer and nothing "started a run"; the only
dispatcher ([orchestration/dispatcher.py](../../orchestration/dispatcher.py)) is the P14
**pub/sub** one, which can't drive containers (no shared in-process bus). This sprint unifies
the model: **the provider becomes graph-pull too**, so the dispatcher's RunRequest is the
single trigger source for the whole pipeline.

Also lands the first **end-to-end graph-pull test** and a runnable local demonstrator — the
pipeline was proven agent-by-agent (S79–S82) but never as one cascade.

---

## The model (operator's, 2026-06-22)

```text
dispatcher places ONE RunRequest node   ← the only explicit trigger ("message on the queue")
        │
        ▼
provider (graph-pull: polls RunRequest) → ingests MarketData + RegimeContext
        │  every downstream agent wakes itself: find_pending sees the upstream
        ▼  processed-edge appear (the "prerequisite gate") — no agent-to-agent calls
   scanner → analyst → PM → execution → monitor → reporter
```

"Place a message on the queue" is, in DL-08's own framing, **write a node to the graph**
(graph-as-queue). So the provider polls `RunRequest` exactly as the scanner polls `MarketData`.

---

## What shipped

- **`RUN_REQUEST_LABEL`** in [contracts/provider.py](../../contracts/provider.py) — the shared
  graph vocabulary so the dispatcher (orchestration) and the provider (agent) need not import
  each other.
- **Provider is now graph-pull** ([agents/provider/poll.py](../../agents/provider/poll.py)):
  - `find_pending` — `RunRequest` nodes with no `INGESTED_BY` descendant.
  - `ingest_run_node` — ingests the request's universe via the existing `ingest_once`, then
    links `RunRequest ─[INGESTED_BY]→ MarketData`. `ingest_once` now returns the MarketData
    node key it wrote (was `None`).
  - Entrypoint drops the timer `ingest_loop` for the standard `work_loop()` over the poll.
- **System start** ([orchestration/start.py](../../orchestration/start.py)):
  - `preflight(graph, source, tickers)` → a `PreflightCheck` checklist (graph reachable via a
    live read probe, data source configured, universe non-empty) + `all_passed`.
  - `place_run_request(graph, run_id, tickers)` → writes the single trigger node.
- **One-pass cascade** ([orchestration/local_pipeline.py](../../orchestration/local_pipeline.py)):
  `cascade_once` runs each agent's `find_pending → process` once in dependency order and
  returns per-stage processed counts. Same logic the container fleet runs continuously, one
  agent per process, collapsed into one process for tests and the demonstrator.
- **Runnable demonstrator** ([scripts/run_local.py](../../scripts/run_local.py)) —
  `PYTHONPATH=. python scripts/run_local.py` prints pre-flight, the dispatcher trigger, the
  per-agent cascade ("woke: processed 1"), and the final provenance-chain tally. No store, no
  Docker.

---

## Proof

`test_graph_pull_e2e.py`: one `place_run_request` → `cascade_once` builds the full chain
(`MarketData → ScanRun → AnalystRun → PMRun → ExecutionRun → MonitorRun → Snapshot`, each
count 1); a second pass processes nothing (gates satisfied); and the scanner gate is empty
until the provider ingests — i.e. work flows only when the prerequisite node appears.

---

## Known limitations / not in scope

- **Single-process cascade is the test/demonstrator path.** The real fleet runs each agent's
  `work_loop()` in its own container, polling concurrently; `cascade_once` is the same poll
  functions run once in order. It is not a scheduler.
- **Dispatcher cron** (who places the daily RunRequest on a schedule) is deferred — the
  operator deferred it. Today the RunRequest is placed by hand / by the demonstrator.
- The P14 pub/sub `Dispatcher` is left intact (its tests still pass); it is the in-process
  dev path, now superseded by the graph-pull trigger for the fleet.
- Still needs the **permanent graph store** to run as real containers (Aura lapses ~2026-06-29).

---

## Exit criteria

- [x] One dispatcher RunRequest drives provider→reporter by graph-pull; full chain asserted.
- [x] Scanner gate is empty until the provider ingests (prerequisite-gate proof).
- [x] Runnable demonstrator prints the cascade end-to-end.
- [x] `make ci` green; 100 % coverage; every new module ≤ 200 lines.

---

## Version bump

New capability (graph-pull orchestration trigger + provider graph-pull). **0.22.00**
(feat → MINOR, HARD RULE).

---

## Deferred (next)

- **Dispatcher cron** — schedule the daily RunRequest (operator deferred).
- **Permanent graph store** — the fleet blocker before Aura lapses ~2026-06-29.
- Forecaster + control-plane agents (operator/supervisor/curator/researcher) work loops.
