# Error Handling — the central fault channel

**Principle:** an error is never just logged where it happens. Every failure is
captured with provenance, redirected to one central channel, and acted upon by the
supervisor — the system's central agent for faults.

## What a fault carries

Every exception becomes an `AgentFault` (`kernel.errors`) that records **where it
came from** and what happened:

- `source_agent` and `source_module` — which agent and which module produced it,
  so the origin is known without grepping logs;
- `capability` — the capability being served, if any;
- `severity` — `info` / `warning` / `error` / `critical`;
- `error_type`, `message`, `traceback` — the failure itself;
- `correlation_id` — the message thread it belongs to;
- `context` — any structured extras the call site attaches.

## How errors are redirected

Agent code wraps fallible work in a fault boundary. The boundary captures any
exception, stamps it with provenance, submits it to the central sink, and (by
default) re-raises so the failure is still surfaced — recorded centrally **and**
not silently swallowed:

```python
from kernel import fault_boundary

with fault_boundary(sink, agent="analyst", module="analyst.scoring"):
    score = compute_blended_score(candidate)
```

`reraise=False` is allowed only on an explicit, documented degraded-but-continue
path (e.g. one provider failing while others succeed).

## Who acts on faults — the central agent

The `FaultSink` is wired, at runtime, to publish each fault as an `error` message
to the **supervisor**, whose `report_fault(AgentFault) -> DispatchResult` capability
is the single place faults are acted upon. The supervisor decides — per severity
and policy — whether to:

- open an incident (durable, operator-visible),
- flag for human review,
- dead-letter and retry the originating message,
- or escalate via the notification budget.

Every fault is also written to the provenance graph as a `Fault` node (owned by the
supervisor), so the failure history is queryable and exportable alongside every
decision (ADR-0001 — Neo4j is the single store; there is no relational `faults` table).

## Why this shape

- **Single place to watch.** One channel, one acting agent — not error handling
  scattered across twelve agents.
- **Always attributable.** Provenance travels with the fault, satisfying the
  acquisition-grade audit requirement.
- **Never silent.** Redirect-and-reraise is the default; swallowing is the
  deliberate, documented exception.
