# Sprint 98 — Control-plane served in-process (1/2): supervisor + operator

**Phase:** Fleet Activation (DL-30 / DL-35)
**Branch:** `sprint-98-control-plane-serve-supervisor-operator`
**Status:** in progress (0.43.00 → 0.44.00)
**Effort:** M

---

## Goal

Retire `idle_loop()` for the two always-on control-plane services — **supervisor** (router / capability
gate / fault sink / master report) and **operator** (operator-language → typed intent bridge). Their
[entrypoints](../../agents/supervisor/entrypoint.py) currently EHLO → ACTIVATE → `idle_loop()`; wire
them to the S97 `serve_loop` so each runs as a live container that consumes its capability inbox and
dispatches to its existing handlers. These two come first because they are the fleet's control spine:
nothing else can be *governed* until the gate and the command bridge actually serve.

## Scope

**In:**

- Replace `idle_loop()` in `agents/supervisor/entrypoint.py` and `agents/operator/entrypoint.py` with a
  `serve_loop` bound to that agent's registered capabilities (from its existing `agent.py` handlers).
- Honour each agent's **TRG / NEVER law clauses** — these agents are *request-triggered*, never
  self-triggering. Reconcile the touched laws' `TRG` rows and cite the new serving tests by clause ID
  (project law convention).
- Operator keeps its existing tool/MCP surface ([`surfaces/mcp_tools.py`](../../surfaces/mcp_tools.py))
  — serving over the bus is *additional*, not a replacement for the human/tool path.

**Out:** forecaster/curator/researcher (S99); the Service Bus backend (S100) — this sprint proves serving
over the **in-process** consumer; no live infra.

## Deliverables

- Updated supervisor + operator entrypoints (serve, not idle) built on `serve_loop`.
- In-process integration tests: a request placed on the supervisor inbox is routed/gated and answered; an
  operator command is parsed to a typed intent and answered — each asserting the relevant `TRG` clause.
- Law reconciliation: supervisor + operator `laws.md` `TRG` rows updated if serving changes the trigger
  contract; `test-plan.md` cites the serving tests; ledger green-count deltas recorded.

## Decisions to confirm (before building)

- **Supervisor's role in a graph-pull fleet.** In the container fleet the trade spine talks via the graph,
  not through a central router — so what does the supervisor *serve*? Options: (a) a capability endpoint for
  faults + capability-gate checks + master-report queries; (b) also a message-lineage recorder. Recommend
  (a) for this sprint (gate + fault sink + report), lineage deferred. **Capture the choice in `design-log.md`.**
- **Operator sync reply.** Confirm the operator uses the S97 `reply` path (human expects a synchronous
  answer), while graph-triggered agents (S99) do not.

## Acceptance / exit criteria

- [ ] Neither `agents/supervisor/entrypoint.py` nor `agents/operator/entrypoint.py` calls `idle_loop()`.
- [ ] Integration test: supervisor serves a gate/fault request; operator serves a command → typed intent.
- [ ] Touched `TRG` law clauses reconciled and cited; ledger updated.
- [ ] `make ci` green; 100% coverage; modules ≤ 200 lines.

## Dependencies

- **S97** (`serve_loop` primitive) — hard prerequisite.
- Respects the operator/supervisor LOCKED v1 laws (S71); any `TRG` change is a law reconciliation, not a
  rewrite.

## Version bump

New capability (two control-plane agents now serve). **0.43.00 → 0.44.00** (feat → MINOR, HARD RULE).

## Notes

Do supervisor + operator together because they are the smallest coherent "the fleet can now be commanded
and governed" increment. Keep each agent's handler logic untouched — this sprint changes *how they are
triggered*, not *what they do*.
