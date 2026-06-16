# ADR 0005 — Inter-agent communication: synchronous RPC + Neo4j durable store

**Status:** Accepted · **Date:** 2026-06-16 · **Decider:** Yury Gurevich (product owner)

## Context

Authoring the provider's laws reframed it as an "autonomous agent that fetches from outside and
**stores for later pickup**," which forced the foundational question: **how do agents hand off data?**
Three models were on the table — (A) DB-mediated blackboard, (B) RabbitMQ message *payloads*, (C)
claim-check (data in Neo4j, a lightweight "ready: ref" event on the bus, consumer reads the store). The
current code is **(option 3) synchronous request→response RPC** over the `MessageBus`, with every
artifact also written to Neo4j as provenance.

The owner was given the explicit trade-off (including that RPC "does not match store-for-pickup for the
*next pipeline step*") and chose **to keep synchronous RPC.**

## Decision

**Inter-agent pipeline hand-offs are synchronous request→response RPC over the `MessageBus`.** The
consumer receives the producer's output **in the reply**. **Neo4j (ADR-0001) is the durable record and
audit** of every artifact, read *later and independently* by surfaces, the reporter, re-runs, and
backtests — it is **not** the medium by which the next pipeline step receives its input. Operator /
human-facing capabilities are RPC too.

## Rationale

- The daily loop is a **sequential batch**; RPC is the simplest correct model for it.
- **Persistency and audit are already satisfied** without a new mechanism: each agent persists its own
  output artifact to Neo4j as it produces it; the supervisor records a `Message` node per dispatch step
  (control-flow lineage). "Store for later pickup" is the provenance graph, available to non-pipeline
  readers.
- The `MessageBus` abstraction already runs RPC both **in-process** and **distributed** (Celery /
  RabbitMQ, ADR-0004) — deployment can scale without changing this logic.
- Avoids a large re-architecture for decoupling/resume benefits **not yet needed** at single-operator
  batch scale.

## Consequences

- The provider's `PROV-TRG-01` / `PROV-OUT-01` (reactive request→response) are **confirmed correct**;
  the comms question is resolved — **not a drift**.
- **Persistency:** durable per-artifact, in Neo4j (not in the transient reply or a queue).
- **Communication audit:** message-lineage (`Message` nodes) for control flow + provenance nodes for
  data. No separate payload logging required.
- **Accepted trade-offs:** a mid-run crash loses only the in-flight reply (completed steps are durable;
  recover by re-running the day); producer↔consumer are time-coupled (acceptable for sequential batch).

## Alternatives considered

- **(C) Claim-check (store + "ready" event).** Better decoupling, crash-resume, and scaling; the
  natural fit for parallel multi-agent operation. **Deferred, not rejected** — revisit when parallel
  agents / long-running async steps arrive; RabbitMQ (ADR-0004) already enables it then. The switch
  would amend `PROV-TRG-01`/`PROV-OUT-01`.
- **(B) RabbitMQ payloads.** Data would live in the queue *and* Neo4j (duplication), with large
  messages on the bus. Rejected.

## Revisit triggers

Adopt the claim-check model (C) if any of: parallel multi-agent operation lands; a hand-off becomes
long-running/async; crash-resume of an in-flight run becomes a requirement.
