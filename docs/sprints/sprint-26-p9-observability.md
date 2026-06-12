# Sprint 26 — P9: Observability stack

**Phase:** P9 — Observability stack (closes P9)
**Branch:** `sprint-26-p9-observability`
**Depends on:** Sprint 25 shipped (main, `3d3d9b1`)

---

## Context

The infrastructure is already deployed and wired. What this sprint closes:

**Already done (do not rebuild):**
- `PrometheusMetrics` kernel adapter — `kernel/metrics_prometheus.py`
- `surfaces/entrypoint.py` + `surfaces/metrics_server.py` — /metrics HTTP server
- `surfaces/context.py` — `paper_context(metrics=)` passes `Metrics` to `InProcessBus`
- Azure Monitor Workspace + Azure Managed Grafana live in `trading-agents-prod`
- `infra/prometheus/prometheus.local.yml` — generated, gitignored; remote_write to Azure
- `infra/grafana/dashboards/trading-agents.json` — 10-panel dashboard imported
- `docker-compose.yml` — app + prometheus sidecar

**Gap:** `MeteredFaultSink` is not yet wired into `paper_context`. The `InProcessBus`
records request metrics but the fault channel is bare — fault-rate panels in Grafana
have no data. This sprint closes that gap and proves it with a test.

---

## Tasks

### 1. Wire MeteredFaultSink in `surfaces/context.py`

In `_context()`, when a real `Metrics` object is provided, wrap the `CollectingFaultSink`
with `MeteredFaultSink` before passing to `InProcessBus`. Faults then flow through metrics
emission before being forwarded to the collecting sink.

Current code (line ~99):
```python
sink = CollectingFaultSink()
bus = InProcessBus(sink=sink, metrics=metrics or NullMetrics())
```

Replace with:
```python
sink = CollectingFaultSink()
active_sink = MeteredFaultSink(metrics, sink) if metrics else sink
bus = InProcessBus(sink=active_sink, metrics=metrics or NullMetrics())
```

Add `MeteredFaultSink` to the kernel import on line 17.

File: `surfaces/context.py` (currently 133L — stays well within 150L limit)

### 2. Write `surfaces/tests/test_p9_exit.py` — P9 exit proof

Create `surfaces/tests/test_p9_exit.py`. One test drives the full metered pipeline:
paper_context with PrometheusMetrics, one successful bus request, one injected fault.
Assert all three metric families are present in the exposition output with correct labels.

```python
def test_p9_exit_metrics_cover_request_and_fault() -> None:
    """P9 exit: request metrics AND fault metrics flow to Prometheus registry."""
    from kernel import AgentFault, PrometheusMetrics, fault_from_exception
    from agents.execution.broker import PaperBroker
    from agents.provider.sources import FakeDataSource
    from kernel import AgentMessage, FakeLLMClient, InMemoryGraphStore
    from surfaces.context import paper_context

    metrics = PrometheusMetrics()
    ctx = paper_context(
        source=FakeDataSource(),
        broker=PaperBroker(),
        graph=InMemoryGraphStore(),
        llm=FakeLLMClient({}),
        metrics=metrics,
    )

    # Drive a successful request — covers request throughput + latency metrics
    ctx.bus.request(
        AgentMessage(
            sender="test",
            recipient="supervisor",
            message_type="request",
            capability="system_status",
            payload={},
        )
    )

    # Inject a fault — covers fault-rate metrics via MeteredFaultSink
    fault = fault_from_exception(
        ValueError("probe"), source="test", severity="warning"
    )
    ctx.bus._sink.submit(fault)  # type: ignore[attr-defined]

    text = metrics.exposition().decode("utf-8")
    assert "trading_agents_kernel_requests_total" in text
    assert "trading_agents_kernel_request_latency_seconds" in text
    assert "trading_agents_kernel_faults_total" in text
```

The fault injection uses `ctx.bus._sink` which is the `MeteredFaultSink` wrapping the
`CollectingFaultSink`. If task 1 is correct, submitting to `_sink` flows through
`MeteredFaultSink.submit` → `metrics.record_fault` → `faults_total` counter.

Note on `fault_from_exception`: check the actual kernel export name — it may be
`fault_from_exception` or `AgentFault(source=..., severity=..., ...)` directly.
Adjust to match what `kernel/__init__.py` actually exports.

File: `surfaces/tests/test_p9_exit.py` — target ≤ 80L

### 3. Update `docs/observability.md`

Replace the entire "Build phase" section at the bottom with a "Deployed stack" section
that documents the live setup:

```markdown
## Deployed stack

| Component | Where |
| --- | --- |
| Prometheus metrics adapter | `kernel/metrics_prometheus.py` |
| /metrics HTTP server | `surfaces/metrics_server.py` (WSGI, port 8000) |
| Container entrypoint | `surfaces/entrypoint.py` |
| Azure Monitor Workspace | `trading-agents-monitor`, Australia East |
| Azure Managed Grafana | `https://trading-agents-grafana-hecpbea2b9cqckf2.eau.grafana.azure.com` |
| Dashboard | "Trading Agents — System Health" (uid: `trading-agents-main`) |
| Prometheus config template | `infra/prometheus/prometheus.yml` |
| Auth setup script | `infra/setup-prometheus-auth.ps1` |

### Running locally

```bash
docker compose up
```

Requires:
- `.env` file with `NEO4J_*` vars (copy from `.env.example`)
- `infra/prometheus/prometheus.local.yml` — generate with `.\infra\setup-prometheus-auth.ps1`

Access:
- `/metrics` endpoint: `http://localhost:8000/metrics`
- Prometheus UI: `http://localhost:9090`
- Grafana: see URL in table above

### Dashboard panels

1. Request rate (req/s) — `trading_agents_kernel_requests_total`
2. Error rate (%) — ratio of failed to total requests
3. P99 latency (s) — `trading_agents_kernel_request_latency_seconds`
4. P50 latency (s)
5. Faults by severity — `trading_agents_kernel_faults_total{severity="..."}`
6. Faults by agent — same metric broken out by `agent` label
7–10. (additional panels for throughput and agent breakdown)
```

Do not change any section above "Build phase" — the principles and layer descriptions are
authoritative design documentation.

---

## Exit criterion

**P9 exit (from `docs/build-plan.md`):** an operator can watch system health and fault
trends in Grafana, beside the product dashboard.

**Proof:** `surfaces/tests/test_p9_exit.py::test_p9_exit_metrics_cover_request_and_fault`
green — request metrics and fault metrics both flow through the metered pipeline to the
Prometheus registry.

The Grafana side is live (infrastructure deployed in Sprint 25 session work); the test
proves the code path is correctly wired.

---

## Handback checklist

- [ ] `make ci` green
- [ ] Coverage floor raised to new measured value (never lowered)
- [ ] `test_p9_exit.py` green
- [ ] `surfaces/context.py` imports and wires `MeteredFaultSink`
- [ ] `docs/observability.md` "Deployed stack" section added
- [ ] Short report: files changed, new test count, coverage %

**Do not** update `docs/STATE.md` or `docs/build-plan.md` — the planning agent does
that on review.

---

## Files touched

| File | Change |
| --- | --- |
| `surfaces/context.py` | Add `MeteredFaultSink` import + conditional wrap in `_context()` |
| `surfaces/tests/test_p9_exit.py` | New — P9 exit proof test |
| `docs/observability.md` | Replace "Build phase" footer with "Deployed stack" section |
