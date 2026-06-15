# ADR 0003 — Telemetry/log plane on Azure; separate from the command bus

**Status:** Accepted · **Date:** 2026-06-15 · **Decider:** Yury Gurevich (product owner)

## Context

Agents need an operational **log/telemetry plane** that is **separate from the inter-agent command
bus** (different volume profile, reliability needs, and consumers — log traffic must never compete with
trade messages). Requirements:

- All agents emit operational logs to a dedicated plane.
- A **settable retention window** (~10 days), then the data is freed.
- The stream **populates a Redis cache** that the dashboard reads for **debugging/tuning**.
- **Future-proof for parallel agents:** several agents may emit *separate log streams describing one
  logical step*, so **correlation/stitching is first-class** (single-operator is a temporary condition).

The system already runs on Azure (Azure Monitor Workspace + Azure Managed Grafana, P9) and already
isolates infrastructure behind kernel protocols (`MessageBus`, `GraphStore`, `Metrics`, `FaultSink`).
The open question was whether to self-host Kafka or use Azure-native services.

## Decision

Build the log plane **Azure-native**, behind a new kernel **`LogSink`** protocol (stdout backend for
tests, Azure backend for prod — the same two-backend discipline as the bus and graph):

```
agents → LogSink → Azure Event Hubs (Kafka endpoint) → Event Hubs-triggered Azure Function
       → Azure Cache for Redis (10-day key TTL) → dashboard (debug/tuning)
```

- **Transport: Azure Event Hubs via its Kafka 1.0+ wire-protocol endpoint** — the managed
  Kafka-as-a-service. Agents use a **Kafka client** (not the proprietary Azure SDK) so the transport
  stays Kafka-portable. Partitions + consumer groups give parallel producers and multiple readers.
- **The 10-day window lives as a Redis TTL** on the dashboard cache — *not* in Event Hubs (Standard
  caps retention at 7 days; this keeps us off Premium and puts the settable window where the dashboard
  reads it).
- **Correlation: emit W3C Trace Context ids** (an open standard) on every log event, seeded from the
  existing provenance `run_id` + a per-step span — so parallel producers' streams stitch into one
  logical step. Application Insights is the *viewer*; the correlation *data* stays portable.
- **Neo4j remains the system of record** (ADR-0001). Only **ephemeral operational logs** flow through
  the Event Hubs → Redis → expire path. **Audit/provenance/business events are never deleted** and stay
  in Neo4j. Keep that boundary explicit.

### The four planes

| Plane | Job | Backend | Lifetime |
| --- | --- | --- | --- |
| **Command** | agent-to-agent request/response (IPC) | `MessageBus` → Celery on RabbitMQ | transient, ack-and-delete |
| **Log/telemetry** | operational logs for debug/tuning | `LogSink` → Event Hubs → Redis | retention window (~10 d) |
| **System of record** | audit, provenance, business events | Neo4j (ADR-0001) | durable, never deleted |
| **Metrics** | throughput, latency, fault-rate | Prometheus / Grafana (P9) | aggregated/rolled up |

## Rationale

- **Meets every requirement** with the **least new ops** — all managed services, no Kafka/Zookeeper/ELK
  to run while also building a trading system.
- **Already on Azure** — reuses the provisioned Monitor + Grafana footprint.
- **Kafka-protocol keeps the door open** — Event Hubs speaks Kafka, so a later move to self-hosted/
  Confluent Kafka is a connection-string change, not a rewrite.
- **Correlation-aware from day one** — the parallel-agent future is designed in, not retrofitted.

## Lock-in and exit cost (the accepted trade-off)

The product owner explicitly accepts **Azure lock-in** as the price. The honest scope of that lock-in,
because it is **uneven** and deliberately bounded:

| Piece | Lock-in | Why |
| --- | --- | --- |
| **Neo4j (system of record)** | **None** | Not Azure; runs on Aura (any cloud) or self-hosted. The money-critical data is free. |
| **Command plane (contracts + bus + RabbitMQ/Celery)** | **None** | RabbitMQ/Celery are portable; the bus is a protocol. |
| **Event Hubs (log transport)** | **Low** | Used via the **Kafka protocol** → re-point a Kafka client to swap. |
| **Azure Cache for Redis** | **None** | Standard Redis (RESP) → any Redis substitutes. |
| **Event Hubs-triggered Function (glue)** | **Low** | Small consumer loop behind `LogSink`/consumer protocol; replaceable with a plain worker. |
| **Application Insights (tracing viewer)** | **Medium** | Azure-shaped, but the trace *data* is W3C-standard → portable; only the viewer is Azure. |
| **Log Analytics + KQL (if adopted)** | **High** | KQL + LAW are genuinely Azure-proprietary. **Therefore deferred** (see Consequences). |
| **Azure Managed Grafana** | **Low–Medium** | Grafana is open; dashboards port with effort. |

**Net:** the lock-in concentrates in the **ephemeral telemetry plane**, never in the durable data or the
inter-agent logic. "Head over heels" is really *head-and-shoulders* — the legs (data, brain) stay free.
Realistic exit cost later: re-point Kafka clients, redeploy a consumer worker, rebuild some dashboards,
replace any KQL. Bounded, because the authoritative store was never on Azure-proprietary storage.

**Three discipline rules that keep it bounded (binding on the implementing sprint):**

1. Talk to Event Hubs through a **Kafka client**, never the proprietary Event Hubs SDK.
2. Everything sits behind the **`LogSink`** (producer) and a consumer protocol — no agent imports an
   Azure client; the unit gate stays infra-free.
3. Emit **W3C Trace Context** correlation ids (open standard), not Azure-proprietary ids.

## Consequences

- New kernel **`LogSink`** protocol + stdout backend (tests) and an Event Hubs/Kafka backend (prod);
  agents log through it, never a cloud client directly.
- **Correlation-id schema is a now-decision** (cheap now, expensive to retrofit): `run_id` + per-step
  span on every log event. Settle it before the plane lands.
- **Defer the Log Analytics + KQL forensic tier** — it is the **deepest** lock-in and Neo4j already
  holds durable audit. Start with Event Hubs (Kafka-portable) + Redis (standard) + thin Function only.
  Add a LAW searchable tier later *only if* a forensic need beyond the 10-day Redis cache appears.
- **Provision when parallelism lands**, not before — build behind `LogSink` now; stand up Event Hubs +
  Redis + the Function when the parallel agents actually arrive ("in-process before distributed").
- Tracked as a **cross-cutting workstream** in `docs/build-plan.md`; a propagation pass updates
  `docs/observability.md`, `docs/architecture.md`, and `docs/deployment.md` when the workstream is built.

## Alternatives considered

- **Self-hosted Kafka + ELK/Loki.** Maximum portability and the full Kafka ecosystem (Streams/ksqlDB),
  but a stack of stateful services to run, secure, and upgrade — against the "minimal operator friction"
  ethos. Only wins if an Azure exit or heavy in-stream log processing is a real plan; the use case here
  (collect → cache in Redis) needs neither.
- **Azure Service Bus instead of Event Hubs.** Service Bus is a queue (command semantics), not a
  replayable log; wrong tool for multi-consumer, replayable telemetry.
- **Log Analytics only (no Redis cache).** Simpler, but LAW's ~31-day included-retention cost floor and
  query latency fit a forensic tier, not a fast debug/tuning cache; and it is the stickiest lock-in.
- **Do nothing (stdout → Azure Monitor agent).** Lowest effort, but no replayable stream and no
  correlation backbone for the parallel-agent future.

## Open items (do not block the decision)

- **Forensic tier:** is a 30–90-day searchable Log Analytics + KQL tier wanted *in addition to* the
  10-day Redis cache, or is the 10-day window the whole story? Default per this ADR: **no** (minimise
  lock-in; Neo4j covers durable audit).
- **Command-plane broker:** confirm RabbitMQ (the natural Celery pairing; reliability + dead-letter)
  replaces the current Redis-broker assumption in `.env.example` — related, but separable from this
  ADR's telemetry decision.
