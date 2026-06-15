# ADR 0004 — RabbitMQ as the Celery command-bus broker

**Status:** Accepted · **Date:** 2026-06-15 · **Decider:** Yury Gurevich (product owner)

## Context

The distributed `MessageBus` backend is `CeleryBus` (Sprint 07). Celery needs a broker; the default in
`kernel/bus_celery_config.py` is `memory://` (eager tests) and `.env.example` suggested `redis://` for
production. The command plane carries agent-to-agent request/response — **including trade-bearing
messages** — and the build plan (P4) calls for **dead-letter and retry handling** in the supervisor.
The production broker needs picking. (This is the command-plane counterpart to the telemetry-plane
decision in `docs/decisions/0003-telemetry-log-plane-azure.md`.)

## Decision

**RabbitMQ (AMQP) is the production Celery broker.** `celery_broker_url` stays `memory://` for eager
unit tests; production overrides to `amqp://`. Redis is **not** the broker — it keeps its proper roles
(the ADR-0003 dashboard cache; optionally the Celery result backend).

## Rationale

- **Acknowledged delivery** — AMQP gives reliable, acked delivery; a trade-intent message must not be
  silently dropped. Redis-as-broker has weaker, visibility-timeout redelivery semantics.
- **Native dead-letter exchanges** — P4 wants dead-letter + retry in the supervisor; RabbitMQ provides
  DLX out of the box rather than emulated.
- **Canonical Celery pairing** — RabbitMQ is Celery's reference broker and best-supported for the
  request/response RPC the bus uses (the `CeleryBus` already handles nested request/response via the
  eager `disable_sync_subtasks` fix from Sprint 14).
- **Vendor-neutral — deliberately.** Unlike the telemetry plane (ADR-0003, Azure), the command plane
  stays portable: RabbitMQ runs anywhere, with managed options on every cloud. The money path is kept
  off cloud lock-in.

## Consequences

- **No code-logic change.** `CeleryBus` is broker-agnostic; this is a connection-string + deployment
  choice behind the `MessageBus` protocol ("the distributed backend changes deployment, not logic").
- **Result backend** pairs cleanly as **Redis** (a common split: RabbitMQ broker + Redis result
  backend) or RabbitMQ's RPC backend; `celery_result_backend` is chosen at deploy.
- **Propagation checklist (code, an implementing sprint — per the ADR-0001 pattern):** update
  `.env.example` (`CELERY_BROKER_URL` example redis→amqp) and the `celery_broker_url`/
  `celery_result_backend` `why=` notes in `kernel/bus_celery_config.py`; document the RabbitMQ service
  in `docs/deployment.md`; add a RabbitMQ service to the distributed-bus integration lane when the
  real-broker round-trip test is un-skipped.

## Alternatives considered

- **Redis as broker.** Simplest (one service for broker + result + cache), but weaker delivery
  guarantees and no true dead-letter — wrong for trade-bearing messages.
- **Azure Service Bus.** Managed AMQP with dead-letter queues, but re-introduces cloud lock-in on the
  command plane — rejected to keep the money path vendor-neutral (deliberate contrast with ADR-0003,
  where the *ephemeral* telemetry plane accepts Azure lock-in but the command plane does not).
