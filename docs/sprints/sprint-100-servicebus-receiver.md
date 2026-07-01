# Sprint 100 — Azure Service Bus receiver: the distributed backend

**Phase:** Fleet Activation (DL-30 / DL-35)
**Branch:** `sprint-100-servicebus-receiver`
**Status:** planned
**Effort:** M–L

---

## Goal

Give the S97 serve transport its **real distributed backend**. Today
[`AzureServiceBusBus`](../../kernel/bus_azure.py) is **send-only**: `publish` can push to a topic
(`_azure_send`) but there is **no receiver** — nothing consumes a subscription and dispatches to a
handler, and `request` routes through an in-process shim. This sprint implements the **consume/receive
half** so an agent's `serve_loop` can pull work off Service Bus and the claim-check `ready:<ref>` events
actually flow between containers. Mirrors S67 (which added the Azure *send* backend behind the pub/sub
protocol): same pattern, receive side.

## Scope

**In:**

- `AzureServiceBusBus` gains a `RequestConsumer`/receiver implementation (per the S97 Protocol): a
  Service Bus subscription receiver that pulls messages, decodes the envelope, resolves the claim-check
  ref via [`kernel/claim_check.py`](../../kernel/claim_check.py), and hands the request to `serve_loop`'s
  dispatch. `complete`/`abandon` (ack) semantics on success/fault.
- Consumer-side claim-check **read** (the producer-side write already exists) so a `ready:<ref>` event
  resolves to the graph artifact on the receiving container.
- A **both-backends parity test**: the same served round-trip over the in-process consumer and (skipped
  without creds) over Service Bus — proving in-process == Service Bus, exactly as S67 did for publish.
- All Azure I/O paths carry `# pragma: no cover` and the SDK stays an **optional** dependency group
  (the unit gate stays infra-free); a live smoke is run via a probe, not in CI.

**Out:** no new agent logic; no fleet deploy (S101–S102). This sprint makes the *wire* real and proven at
parity; running 13 containers on it is S102.

## Deliverables

- Receiver added to `kernel/bus_azure.py` (or a small `kernel/bus_azure_receiver.py` if the 200-line
  guard bites — split rather than grow).
- `AzureServiceBusSettings` extended if a subscription name / receive timeout is needed
  ([`kernel/bus_azure_config.py`](../../kernel/bus_azure_config.py)).
- Parity test (`tests/integration/…`) skipping cleanly without creds (pattern from S67).
- A `probes/` entry (or extension) that does one live send→receive round-trip against a real namespace.

## Decisions to confirm (before building)

- **Topics/subscriptions vs. queues.** Pub/sub (topic per capability, subscription per agent) matches
  ADR-0005; point-to-point queues are simpler for RPC. Recommend topics for the event/`ready` path,
  and confirm whether the operator sync-RPC path needs a request/reply queue or stays HTTP (as the master
  already is). **Capture in `design-log.md`.**
- **Ack on fault.** Recommend `abandon` (redeliver) on a transient fault, `dead-letter` after N — confirm
  the retry policy and where the supervisor sees dead-letters.

## Acceptance / exit criteria

- [ ] A served round-trip works over the in-process consumer **and** the Service Bus consumer (parity
      test); the SB half skips without creds.
- [ ] A `ready:<ref>` event published on one side resolves to the graph artifact on the consuming side.
- [ ] Live smoke (probe): one real send→receive against a Service Bus namespace succeeds.
- [ ] `make ci` green; 100% coverage on non-`# pragma` lines; SDK stays optional.

## Dependencies

- **S97** (serve Protocol), **S99** (agents serve over it in-process).
- ADR-0005 (Azure Service Bus is the deployment bus); reuses the S67 send backend + claim-check.

## Version bump

New capability (distributed serve backend). **0.45.00 → 0.46.00** (feat → MINOR, HARD RULE).

## Notes

**This is the etalon-first cut line.** S97–S100 are CI/parity-provable with no live spend. S101–S103 below
commit to running the fleet on live Azure infra (DL-35 accepted that trade). Ship S100 and the fleet's
*communication* is complete and proven at parity; only provisioning + a live run remain.
