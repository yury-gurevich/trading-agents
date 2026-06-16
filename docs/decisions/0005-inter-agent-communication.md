# ADR 0005 — Inter-agent communication: event-driven pub/sub over Azure Service Bus (claim-check)

**Status:** Accepted · **Date:** 2026-06-16 · **Decider:** Yury Gurevich (product owner)

> **History.** This ADR was first accepted (same day) as *synchronous RPC*. On review the owner
> reversed it: RPC makes a producer name its consumer, and the goal is fuller decoupling for the
> coming parallel multi-agent operation. It was then aligned with the Azure commitment (ADR-0003).
> This is the final decision; it **supersedes ADR-0004** (RabbitMQ command broker).

## Context

How do agents hand off work? Today the runtime is **synchronous request→response RPC** sequenced by a
dispatcher (agents name a logical recipient; the bus routes; no credentials/addresses are exchanged).
The owner wants agents **fully decoupled** — a producer should not name its consumer at all — to
support **parallel multi-agent** operation and first-class **communication logging**. The system was
designed toward this (the contracts already declare `consumes`/`emits`; "idle until messaged").

The owner has also accepted **Azure lock-in** (ADR-0003) and prefers **Azure-native** infrastructure
where it simplifies. Azure's native broker, **Azure Service Bus**, provides exactly pub/sub
(topics/subscriptions), FIFO sessions, dead-letter, and at-least-once delivery — the managed
RabbitMQ-equivalent. Azure **Event Hubs** (the Kafka-equivalent) is already the logs/telemetry plane
(ADR-0003).

## Decision

**Inter-agent communication is event-driven publish/subscribe over Azure Service Bus, using the
claim-check pattern.**

- **Topics, not recipients.** Each agent **publishes** its outputs to a Service Bus **topic** and
  **subscribes** to the topics it consumes (from its contract's `emits`/`consumes`). **No agent names
  another** — the broker routes by topic. The dispatcher thins from a sequencer to a **trigger-emitter
  + watchdog**.
- **Claim-check for data.** The **data + audit live in Neo4j** (ADR-0001, the source of truth); the
  Service Bus message carries only a small **`ready: <graph-ref>`** event; the consumer **reads the
  artifact from Neo4j** by reference. *Required*, not merely preferred: Service Bus caps a message at
  **256 KB** (Standard), and a market-data payload is far larger.
- **Logs** remain on **Azure Event Hubs** (ADR-0003). Operator/human request→response may remain RPC
  (a sync answer is the point there).

## Rationale

- **Full decoupling** — agents know topics, never each other; matches the parallel-agent future and
  makes "log every communication" first-class (every event is observable on the bus).
- **Azure-native simplicity** — a managed broker; no self-hosted RabbitMQ/Kafka to run, secure, and
  upgrade. Consistent with the Azure commitment and Event Hubs already in place.
- **Bounded lock-in** — the broker is Azure, but **the data stays in Neo4j (portable).** Service Bus
  carries only tiny reference-events; leaving Azure swaps the broker, not the data or the logic. This
  keeps the lock-in on *transport*, not on the money-path *data* — the spirit of ADR-0003.

## Consequences

- **Kernel** — the `MessageBus` protocol grows from request→response to **publish/subscribe**
  (`publish(topic, event)` / `subscribe(topic, handler)`); an in-process backend keeps the unit gate
  infra-free, an Azure Service Bus backend runs in deployment (the two-backend discipline of ADR-0001's
  store and the existing bus).
- **Every agent** wires its `emits`/`consumes` to topics; outputs are written to Neo4j then announced
  as `ready: <ref>` events.
- **Provider law** — `PROV-TRG-01` / `PROV-OUT-01` change from "reactive request→response" to
  "consume a data-request event → fetch → write to the store → publish `ready: <ref>`"
  (reconciled when the provider cycle resumes; changelog v0.3).
- **`flow.md`** edges become **topic events** (a pass pending).
- **Supersedes ADR-0004** (RabbitMQ): the broker is **Azure Service Bus**. Magnitude: a real,
  system-wide phase — but designed-for (the `emits`/`consumes` declarations).

## Alternatives considered

- **Synchronous RPC (the prior decision).** Simple for a sequential batch, but couples a producer to
  its consumer's identity and doesn't fit parallel agents. Reversed.
- **Self-hosted RabbitMQ + Kafka.** Vendor-neutral, but more always-running machinery to operate —
  against the Azure-native simplification the owner chose.
- **Data in the message (not claim-check).** Blocked by the 256 KB Service Bus cap and duplicates the
  data (bus + Neo4j). Rejected.

## Revisit triggers

If the Azure commitment is ever reversed, the broker swaps to RabbitMQ/AMQP with **no change to the
data model** (claim-check keeps data in Neo4j) — the bus backend is the only Azure-specific piece.
