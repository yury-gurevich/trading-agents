# Sprint 08 — Observability: the kernel metrics adapter

**Status:** shipped (merged to `main` @ `515a713`) · **Branch:** `sprint-08-observability-adapter` · **Build phase:** P1 (kernel runtime — observability emission)

## Goal

Add the kernel **metrics adapter** — the plumbing every agent emits *through* (no agent
touches a metrics backend directly). It captures, per agent and per capability,
**throughput + latency + request outcome** (from the bus) and **fault-rate by source** (from
the central fault channel), behind a vendor-neutral `Metrics` protocol with a **no-op default**
(so the gate stays infra-free) and a **Prometheus backend** (unit-tested via an in-memory
registry — no server). The Prometheus *server* + Grafana dashboards are **P9**, not this sprint.

## Why (context)

- `docs/observability.md` §1: "the kernel exposes an observability adapter that every agent
  emits through … per agent and per capability: throughput, latency …; fault rate by
  `source_agent`/`severity` (fed from the central fault channel)." Its Build-phase note: "the
  metrics adapter ships with the kernel runtime; Prometheus + Grafana provisioning … land in
  the observability phase." So this sprint is the **emission adapter**, not the stack.
- It now has real consumers: three agents (`provider`/`scanner`/`analyst`) produce throughput
  and faults over the bus.
- Mirrors the established pattern — a `Protocol` with swappable backends and a null/in-memory
  default (`MessageBus`: in-process/Celery; `GraphStore`: in-memory/Neo4j). Keep it
  vendor-neutral so an OpenTelemetry backend could be added later without touching agents.
- Read first: `docs/sprints/README.md` (guardrails + gate); `docs/observability.md` §1 + Build
  phase; `kernel/bus.py` (`InProcessBus.request` — the request choke point to instrument) and
  `kernel/bus_celery.py` (`CeleryBus` — instrument identically; **note it is already 182 lines,
  so keep the metrics wiring there minimal or extract**); `kernel/errors.py` (`AgentFault`,
  `FaultSink`, `CollectingFaultSink`); `kernel/config.py` (`AgentSettings`/`tunable`);
  `kernel/graph_neo4j.py` (a kernel backend that reads infra settings + is unit-tested without
  the real service — the shape to copy).

## Key design constraints (do not break)

- **Vendor-neutral protocol, null default.** A `Metrics` Protocol; agents and the buses depend
  on the protocol, never on `prometheus_client`. `NullMetrics` (no-op) is the **default**, so
  existing behaviour and the gate are unchanged unless a real backend is injected.
- **Kernel stays pure.** The adapter modules import `prometheus_client` (external infra; add it
  to the mypy overrides) but **nothing from `contracts`/`agents`**. `import-linter` "Kernel is
  pure plumbing" KEPT.
- **Instrument at the choke points, not in agents.** The **bus** records per-request throughput
  + latency + outcome (`ok` vs `error`); the **fault channel** records fault-rate by source via
  a metered `FaultSink`. Agents are not modified.
- **Infra-free gate.** `PrometheusMetrics` uses its **own `CollectorRegistry`** (not the global
  default — avoids cross-test collisions) so tests assert counter/histogram sample values
  in-memory; **no HTTP server, no Prometheus process**. Exposition text (`generate_latest`) is
  exposed for a later P9 surface to serve, but this sprint serves nothing.
- **No magic numbers / headers / < 200 lines** each (watch `bus_celery.py`’s headroom).

## Suggested shape (latitude on internals)

```python
class Metrics(Protocol):
    def record_request(self, agent: str, capability: str, latency_s: float,
                       *, ok: bool) -> None: ...
    def record_fault(self, fault: AgentFault) -> None: ...

class NullMetrics:        # default everywhere; no-op
    ...
class PrometheusMetrics:  # own CollectorRegistry; Counter(requests_total) by
    ...                   # (agent, capability, outcome); Histogram(request_latency_seconds)
                          # by (agent, capability); Counter(faults_total) by
                          # (source_agent, source_module, severity). exposition() -> bytes.
```

A `MeteredFaultSink(metrics, inner)` decorates any `FaultSink`: it calls
`metrics.record_fault(fault)` and forwards to `inner` — this is how "fault rate fed from the
central fault channel" is wired (compose it with `CollectingFaultSink`).

## Deliverables

1. **`kernel/metrics.py`** — the `Metrics` Protocol, `NullMetrics`, and `MeteredFaultSink`.
   Headered, < 200 lines.
2. **`kernel/metrics_prometheus.py`** — `PrometheusMetrics(Metrics)` (its own
   `CollectorRegistry`, the counters + latency histogram above, an `exposition() -> bytes`
   using `generate_latest`) + `MetricsSettings(AgentSettings)` if any knob is needed (e.g. a
   metric `namespace`/`subsystem`, via `tunable`). Headered, < 200 lines.
3. **Bus instrumentation** — `InProcessBus` and `CeleryBus` each take an optional
   `metrics: Metrics = NullMetrics()`; in `request`, time the dispatch and call
   `record_request(recipient, capability, latency_s, ok=<response, not error>)`. Keep both
   modules < 200 lines (extract a tiny helper if `bus_celery.py` needs it).
4. **`kernel/__init__.py`** — export `Metrics`, `NullMetrics`, `PrometheusMetrics`,
   `MeteredFaultSink` (+ `MetricsSettings` if added).
5. **Dependencies** — add `prometheus-client>=0.20` to the `runtime` extra **and** the `dev`
   group (so `uv sync` installs it for the gate); add `prometheus_client` /
   `prometheus_client.*` to `[[tool.mypy.overrides]]` if mypy needs it.
6. **`tests/test_metrics.py`** — infra-free:
   - `NullMetrics` is a safe no-op; a bus with the default metrics behaves exactly as before.
   - `PrometheusMetrics` + a bus: drive several requests (success + handler-raise) through a
     real `EchoAgent`; assert `requests_total{outcome="ok"|"error"}` counts and that the
     latency histogram observed the requests (sample count > 0), read from the registry.
   - `MeteredFaultSink`: feeding faults records `faults_total` by `source_agent`/`source_module`/
     `severity` **and** forwards to the inner sink.
   - `exposition()` returns parseable Prometheus text containing the metric names.

## Steps

1. Branch `sprint-08-observability-adapter` off `main`.
2. `kernel/metrics.py` + `kernel/metrics_prometheus.py`; export from `__init__`.
3. Instrument `InProcessBus` + `CeleryBus` (optional `metrics`, default `NullMetrics`).
4. Add `prometheus-client` to deps + mypy overrides; `uv sync`.
5. Write `tests/test_metrics.py`.
6. Run the gate; re-tune the coverage floor. Push; hand back. Do not merge to `main`.

## Acceptance criteria

- `Metrics` protocol + `NullMetrics` (default) + `PrometheusMetrics` + `MeteredFaultSink`;
  both buses instrumented with the null default (existing tests + behaviour unchanged).
- `PrometheusMetrics` records request throughput/latency/outcome and fault-rate by source,
  asserted in-memory (no server); `exposition()` renders Prometheus text.
- `import-linter` "Kernel is pure plumbing" KEPT; boundary meta-test green; all modules
  headered and < 200 lines.
- `make ci` green at/above the re-tuned floor; **gate needs no external infra**.

## Out of scope (do NOT build this sprint)

The Prometheus **server**/scrape endpoint + Grafana dashboards (P9); OpenTelemetry traces;
queue-depth (needs the real broker/workers — P4); domain **outcome counters**
(recommendations/approvals/fills/exits — agent-emitted, a later opt-in increment); the
**trust indicators** (silent-failure rate, explainability coverage, … — computed later atop
these primitives). Flag anything you think is needed earlier.

## Handback report (paste into the PR / reply)

- Files added/changed and final line counts; the `Metrics` protocol shape, the metric names/
  labels chosen, and how the buses + fault channel are instrumented; the `prometheus-client`
  dep decision.
- New coverage % and the re-tuned floor; confirmation the gate needs no external infra.
- Any design decision worth recording or anything that felt out of scope.

The planning agent will review, merge to `main`, and update `docs/STATE.md` +
`docs/build-plan.md`.
