# Reporter Agent

**Mission.** Stitch each run and each trade into durable, human-readable narrative
and metrics — the truth surface the dashboard and operator read.

## Owns
- Portfolio, signal, and regime-attribution metrics.
- Per-trade narratives (why selected, sized, exited, what was learned).
- Run snapshots.

## Boundary — contract: `contracts/reporter.py`
- **Consumes:** `report(ReportRequest) -> RunSnapshot`,
  `narrative(NarrativeRequest) -> TradeNarrative`.
- **Emits:** `report_ready`.
- **Depends on (read-only):** the whole provenance graph — scanner, analyst,
  portfolio_manager, execution, monitor, provider.

## Data ownership
- **Postgres:** `performance_snapshots`, `trade_narratives`.
- **Graph:** `Snapshot`, `TradeNarrative` (reads all; writes only these).

## External I/O
- None.

## MCP surface
- `report`, `narrative`.

## Never
- Make or alter a trading decision.
- Mutate another agent's data — it only reads the provenance graph.
