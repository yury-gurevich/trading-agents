# Supervisor Agent

**Mission.** Route messages between agents, enforce the capability matrix and
hard-NO safety surface, flag anomalies for human review, and produce the master
health/decision report.

## Owns

- The A2A router and the message store (append-only message lineage).
- The capability matrix and the hard-NO safety surface.
- Human-review flagging and dead-letter handling.
- **The central fault channel** — every agent's errors are redirected here with
  provenance (which module produced them) and acted upon (flag, incident, retry).
- The master agent report.

## Boundary — contract: `contracts/supervisor.py`

- **Consumes:** `dispatch_intent(TypedIntent) -> DispatchResult`,
  `system_status(StatusRequest) -> MasterReport`,
  `flag_for_human(FlagRequest) -> DispatchResult`,
  `report_fault(AgentFault) -> DispatchResult`.
- **Emits:** `human_flag_raised`, `message_dead_lettered`.
- **Depends on:** every agent (it routes to and reports across all of them).

## Data ownership

- **Postgres:** `a2a_messages`, `capability_matrix`, `human_review_flags`,
  `master_agent_reports`, `agent_faults`.
- **Graph:** `Message`, `Agent`, `Flag`, `Fault` (`Message -[:SENT_TO]-> Agent`).

## External I/O

- None.

## MCP surface

- `system_status`, `flag_for_human`.

## Never

- Make a domain trading decision — it governs flow and safety, not strategy.
- Enable a hard-NO capability, even if asked.
- Route a capability to a caller the matrix forbids.
