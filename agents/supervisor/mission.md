# Supervisor Agent

**Mission.** Record message lineage and central faults for dispatcher runs now;
grow into routing, capability gating, human review, and the master health report
in P5.

## Owns

- P4: dispatcher message lineage.
- P4: central fault records.
- P5: the A2A router and the message store (append-only message lineage).
- P5: the capability matrix and the hard-NO safety surface.
- P5: human-review flagging and dead-letter handling.
- **The central fault channel** — every agent's errors are redirected here with
  provenance (which module produced them) and acted upon (flag, incident, retry).
- The master agent report.

## Boundary — contract: `contracts/supervisor.py`

- **Consumes:** `dispatch_intent(TypedIntent) -> DispatchResult`,
  `system_status(StatusRequest) -> MasterReport`,
  `flag_for_human(FlagRequest) -> DispatchResult`,
  `record_dispatch_run(DispatchRunRecord) -> DispatchResult`,
  `report_fault(AgentFault) -> DispatchResult`.
- **Emits:** `human_flag_raised`, `message_dead_lettered`.
- **Depends on:** every agent (it routes to and reports across all of them).

## Data ownership

- **Postgres:** `a2a_messages`, `capability_matrix`, `human_review_flags`,
  `master_agent_reports`, `agent_faults`.
- **Graph:** `Message`, `Fault` in P4; `Agent`, `Flag` in P5.

## External I/O

- None.

## MCP surface

- `system_status`, `flag_for_human`.

## Never

- Make a domain trading decision — it governs flow and safety, not strategy.
- Enable a hard-NO capability, even if asked.
- Route a capability to a caller the matrix forbids.
