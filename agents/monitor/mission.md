# Monitor Agent

**Mission.** Watch open positions and decide when to exit under policy (stops,
targets, time, regime), hand exits to execution, and explain every close and hold.

## Owns
- Exit-signal logic.
- The position aggregate and its lifecycle (opens on a fill event, closes on exit).
- Hold/exit rationale.

## Boundary — contract: `contracts/monitor.py`
- **Consumes:** `check_positions(MonitorRequest) -> CloseDecisionSet`,
  `explain_hold(MonitorRequest) -> Explanation`.
- **Emits:** `exits_decided`.
- **Depends on (messages only):** `forecaster` (advisory exit timing),
  `execution` (consumes its `fill_recorded` notifications to open positions).

## Data ownership
- **Graph:** `MonitorRun`, `Position`, `PositionCheck`, `CloseDecision`;
  `Fill -[:OPENS]-> Position`, `PositionCheck -[:CHECKS]-> Position`, and
  `CloseDecision -[:CLOSES]-> Position`.
- **Position lifecycle:** open positions are reconstructed from execution fills in
  the graph; broker submission remains execution's boundary.

## External I/O
- None.

## MCP surface
- `check_positions`, `explain_hold`.

## Never
- Submit to the broker directly — hand close decisions to `execution`.
- Open new positions — it manages and exits existing ones.
- Call a market-data API directly.
