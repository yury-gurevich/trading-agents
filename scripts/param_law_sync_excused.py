"""The eight deferred PARAM bounds reconciliations (DL-276 D4).

Agent: tooling
Role: record exact Type cells, allowing this list only to shrink.
External I/O: none.
"""

# These books are fidelity decision paths: editing any file restarts the count.
# Delete entries and reconcile their rows at the first deploy that restarts that
# count, or after DL-237's verdict. A changed or reconciled row fails this gate.
EXCUSED_BOUNDS = {
    "portfolio_manager.starting_cash": "`Decimal ≥ 0` (USD)",
    "portfolio_manager.max_position_pct": "`float ≥ 0.01, ≤ 1.0`",
    "portfolio_manager.max_positions": "`int ≥ 1, ≤ 50`",
    "portfolio_manager.cash_buffer_pct": "`float ≥ 0.0, ≤ 0.50`",
    "portfolio_manager.min_order_quantity": "`int ≥ 1` (shares)",
    "portfolio_manager.price_lookback_days": "`int ≥ 1, ≤ 30` (days)",
    "scanner.min_average_volume": "`float ≥ 0` (shares/day)",
    "analyst.scaled_stop_atr_multiplier": "`float` (ratio)",
}
