# Sprint 62 — P14.3: Provider pub/sub dual-mode

**Phase:** P14 — Inter-agent comms re-architecture (ADR-0005)
**Status:** planned
**Branch:** `sprint-62-p14-provider-pubsub`
**Effort:** M
**Prerequisite:** S61 shipped (claim-check helpers available).

---

## Goal

Establish the agent event-binding pattern and apply it to the provider: the provider
subscribes to `data.request.*` topics (OHLCV, news, fundamentals, sectors, sentiment,
earnings) and answers each by fetching data, writing a `MarketData` claim-check node to the
graph, and publishing a `data.ready.*` event.

**Dual-mode:** the provider ALSO retains its existing RPC `bind()` handlers so that the
orchestration step functions (`orchestration/steps.py`) keep working without change.
The full RPC-to-pub/sub cut-over happens in S66 (dispatcher).

**Exit criterion:** provider answers a `data.request.ohlcv` pub/sub event via claim-check
(no RPC); the existing RPC tests remain green; CI 100%.

---

## Context

The provider is the data boundary — the highest-traffic source of claim-check events.  It is
the "pattern stress-test" called out in the build plan.  Migrating it first validates the
`claim_check_write` helper under real data shapes before any consumer is changed.

The provider law (`agents/provider/laws/laws.md`) already declares `PROV-TRG-01` and
`PROV-OUT-01` in v0.3 pub/sub terms.  This sprint reconciles the implementation to match.

---

## What to build

### Topic map

| Data field | Subscribe (request) | Publish (ready) | Node label |
| --- | --- | --- | --- |
| ohlcv | `data.request.ohlcv` | `data.ready.ohlcv` | `MarketData` |
| news | `data.request.news` | `data.ready.news` | `MarketData` |
| fundamentals | `data.request.fundamentals` | `data.ready.fundamentals` | `MarketData` |
| sectors | `data.request.sectors` | `data.ready.sectors` | `MarketData` |
| sentiment | `data.request.sentiment` | `data.ready.sentiment` | `MarketData` |
| earnings | `data.request.earnings` | `data.ready.earnings` | `MarketData` |

### Request event schema

All `data.request.*` events carry:
```python
{"ticker": str, "run_id": str | None, "fields": list[str]}
```

The `ref` for the claim-check node is `f"MarketData:{ticker}:{run_id}"` (matches the existing
RPC write pattern so the graph node is idempotent between both paths).

### `agents/provider/agent.py` changes

In `bind()`, call `super().bind()` first (keeps RPC), then subscribe to each
`data.request.*` topic:

```python
def bind(self) -> None:
    super().bind()
    for field in ("ohlcv", "news", "fundamentals", "sectors", "sentiment", "earnings"):
        self.bus.subscribe(
            f"data.request.{field}",
            self._make_field_handler(field),
        )
```

Each handler: validates event, calls the existing `_fetch_field` logic, writes via
`claim_check_write`, publishes ready.

### `agents/provider/laws/laws.md` update

Reconcile `PROV-TRG-01` and `PROV-OUT-01` to match the new implementation.

### Tests (`agents/provider/tests/test_provider_pubsub.py`) — new file

| Test name | Verifies |
| --- | --- |
| `test_ohlcv_request_event_triggers_ready_event` | subscribe `data.ready.ohlcv`, publish request, verify ready received |
| `test_ohlcv_claim_check_node_is_in_graph` | after request, graph has `MarketData` node with `ref` |
| `test_ohlcv_bus_event_has_only_ref_not_bars` | ready event dict has `ref`, not raw OHLCV payload |
| `test_news_request_event_triggers_ready_event` | same pattern for news |
| `test_existing_rpc_still_works_after_dual_mode_bind` | `bus.request(provider, "fetch_data")` still returns data |

---

## Non-negotiable guardrails

- `super().bind()` called first — existing RPC handlers remain registered.
- `claim_check_write` used for every pub/sub fetch (never `bus.publish` with raw props).
- All new subscriber paths covered by the new test file.
- 100% coverage floor maintained.

---

## Out of scope

- Removing RPC handlers — that is S66.
- Consumer-side changes (scanner, analyst) — S63.
