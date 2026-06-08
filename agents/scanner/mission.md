# Scanner Agent

**Mission.** Reduce the full tradable universe to a small, ranked set of
candidates worth deeper analysis, and explain why each survived or was filtered.

## Owns

- Universe selection for the active market pack.
- Scanner filters (beta, relative strength, returns, earnings proximity).
- Scanner diagnostics and the per-filter drop trace.

## Boundary — contract: `contracts/scanner.py`

- **Consumes:** `run_scan(ScanRequest) -> CandidateSet`,
  `explain_filter(ScanRequest) -> Explanation`.
- **Emits:** `scan_completed`.
- **Depends on (messages only):** `provider` (for market data).

## Data ownership

- **Graph:** `ScanRun`, `Candidate` nodes; `Candidate -[:SURVIVED]-> ScanRun`
  and `ScanRun -[:DERIVED_FROM]-> MarketSnapshot` lineage edges.

## External I/O

- None. All market data is requested from `provider`.

## MCP surface

- `run_scan`, `explain_filter`.

## Never

- Score or recommend — that is the analyst's job.
- Call a market-data API directly.
- Size or approve trades.
