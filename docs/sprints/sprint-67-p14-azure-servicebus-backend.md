# Sprint 67 — P14.8: Azure Service Bus backend

**Phase:** P14 — Inter-agent comms re-architecture (ADR-0005)
**Status:** planned
**Branch:** `sprint-67-p14-azure-servicebus-backend`
**Effort:** M–L
**Prerequisite:** S66 shipped (full event-driven pipeline on in-process bus).

---

## Goal

Implement `AzureServiceBusBackend` — a `MessageBus`-compatible backend where `publish` sends
to an Azure Service Bus **topic** and `subscribe` attaches a **subscription** handler.
The claim-check pattern (data in Neo4j, tiny ref-event on the bus) guarantees every message
< 256 KB.  Integration-marked tests skip without Azure creds.

**Celery is retired** as the distributed bus backend after this sprint (ADR-0005 supersedes
ADR-0004).

**Exit criterion:** a both-backends parity test (in-process == Azure Service Bus) passes with
Azure creds; without creds the test is skipped; CI 100% on coverage source.

---

## What to build

### `kernel/bus_azure.py` (new)

```python
class AzureServiceBusBus:
    """Azure Service Bus pub/sub backend; claim-check keeps messages < 256 KB."""

    def subscribe(self, topic: str, handler: EventHandler) -> None: ...
    def publish(self, topic: str, event: dict[str, Any]) -> None: ...
    # request/register retained for operator sync path (via in-process shim)
    def register(self, recipient: str, capability: str, handler: MessageHandler) -> None: ...
    def request(self, message: AgentMessage) -> AgentMessage: ...
```

Lazy import `azure.servicebus` (integration optional-dep group).

### `pyproject.toml`

Add optional group:

```toml
[project.optional-dependencies]
azure = ["azure-servicebus>=7.12"]
```

### `kernel/bus_azure_config.py` (new)

`AzureServiceBusSettings(AgentSettings)` — connection string or managed-identity endpoint.

### `kernel/__init__.py`

Export `AzureServiceBusBus`, `AzureServiceBusSettings` (behind `TYPE_CHECKING` guard for
non-Azure envs).

### Tests

`tests/test_bus_azure.py` — integration-marked (`@pytest.mark.integration`), skipped
without `AZURE_SERVICEBUS_CONNECTION_STRING` env var.

Parity test: `test_azure_and_in_process_produce_same_outcome` — same pub/sub chain on both
backends, same graph output.

### Retire `CeleryBus` from the distributed path

`CeleryBus` is NOT removed (it is still used in tests that need a second backend for
comparison), but `orchestration/bindings.py` default switches from `CeleryBus` to
`AzureServiceBusBus` when `AZURE_SERVICEBUS_CONNECTION_STRING` is set.

---

## Non-negotiable guardrails

- Every pub/sub message ≤ 256 KB (enforced by claim-check; no raw payloads on the bus).
- Lazy `azure.servicebus` import so the unit gate never loads the SDK.
- Integration tests marked `@pytest.mark.integration`; skipped without Azure creds.
- 100% coverage on `kernel/bus_azure.py` production code (non-I/O path); I/O paths `# pragma: no cover`.
- ADR-0005 closes with a status update in `docs/decisions/INDEX.md`.

---

## Post-P14 state

After S67 ships:

- Agents communicate exclusively via pub/sub + claim-check (graph-ref events on the bus).
- Operator/human sync path remains `bus.request()` (in-process shim inside `AzureServiceBusBus`).
- Celery/RabbitMQ no longer used for inter-agent messaging (ADR-0004 superseded).
- Every agent boundary is observable: every event is a bus message; provenance is in Neo4j.
- P14 **complete** — update `docs/build-plan.md` status.
