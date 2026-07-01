# Sprint 97 — Kernel serve transport: the `serve_loop` consume primitive

**Phase:** Fleet Activation (DL-30 / DL-35)
**Branch:** `sprint-97-serve-loop-primitive`
**Status:** planned
**Effort:** M

---

## Goal

Build the one missing primitive DL-30 named: a transport-neutral **serve/consume loop** so an
RPC-triggered agent can run as its own container — "consume a request off my inbox → dispatch to the
bound handler → reply". Today the kernel has only [`work_loop`](../../kernel/work_loop.py) (graph-pull,
self-triggering) and [`idle_loop`](../../kernel/bootstrap.py#L115) (sleep forever). The 5 control-plane
agents (operator/supervisor/curator/researcher/forecaster) `idle_loop()` because there is no way to
*serve* a capability off the bus in a standalone process. This sprint adds the abstraction; S98–S99 wire
the agents to it; S100 gives it a real Service Bus backend.

**In-process before distributed** (build-plan principle): prove the loop over an in-process inbox with
the unit gate; the Service Bus receiver is S100 behind the identical protocol.

## Scope

**In:**

- A `RequestConsumer` (or `Inbox`) **Protocol** in the kernel: `poll() -> list[AgentMessage]` (or a
  blocking `receive`), plus `reply(response)` for the RPC path. Transport-neutral — the in-process bus
  and the Service Bus backend both implement it.
- `serve_loop(consumer, dispatch, *, poll_interval)` — the infinite wrapper — and an independently
  testable `serve_once(consumer, dispatch) -> int` (mirrors `run_once`/`work_loop`'s split so coverage
  lands on the single-pass function, `# pragma: no cover` on the infinite wrapper).
- `dispatch` reuses the existing capability lookup + `caller_authorized` gate + `fault_boundary` from
  [`kernel/bus.py`](../../kernel/bus.py) so an unauthorized or faulting request returns an error message,
  never raises. **No new authorization logic** — the capability matrix is already enforced there.
- A thin in-process `RequestConsumer` implementation backed by a list/queue, for tests and the local
  demonstrator.

**Out:** no Azure I/O (that is S100); no agent entrypoint changes (that is S98–S99); no change to the
graph-pull `work_loop` or the trade-spine agents.

## Deliverables

- `kernel/serve_loop.py` — `RequestConsumer` Protocol, `serve_once`, `serve_loop`, in-process consumer.
- Unit tests: a registered capability served via `serve_once` round-trips; an unauthorized caller is
  rejected (`Unauthorized`); a faulting handler returns an error message (loop does not die); an empty
  inbox is a no-op.
- Header + size guards green; 100% coverage on `serve_once`.

## Decisions to confirm (before building)

- **Poll vs. blocking receive.** In-process is naturally poll; Service Bus supports a blocking receiver.
  Recommend the Protocol expose `poll()` (non-blocking, returns 0..N) so `serve_once` stays testable and
  both backends fit; the SB backend's blocking receive wraps into `poll()` with a timeout. *Confirm.*
- **RPC reply path.** The operator/human sync path needs a response returned to the caller; graph-pull
  agents don't. Recommend `RequestConsumer.reply(msg)` optional — pub/sub-triggered handlers ignore it,
  RPC handlers use it. *Confirm the shape.*

## Acceptance / exit criteria

- [ ] `serve_once` dispatches a request to the bound handler and returns a reply; caller-authz enforced.
- [ ] A faulting handler yields an error message and the loop continues (never raises).
- [ ] `make ci` green; 100% coverage; every new module ≤ 200 lines with the coding-agent header.

## Dependencies

- Reuses [`kernel/bus.py`](../../kernel/bus.py) (`caller_authorized`, error-message shape) and
  [`kernel/errors.py`](../../kernel/errors.py) (`fault_boundary`). No new external dependency.
- Unblocks S98–S99 (control-plane agents served) and S100 (Service Bus receiver).

## Version bump

New kernel capability (serve transport primitive). **0.42.00 → 0.43.00** (feat → MINOR, HARD RULE).

## Notes

This is the linchpin of the arc: every later sprint sits behind this Protocol. Keep it minimal and
transport-neutral — resist adding Azure specifics here; those live in S100's backend.
