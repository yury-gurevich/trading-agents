"""Cross-stage boundary checks for the trading pack.

Agent: orchestration
Role: the invariants that hold *between* stages — no agent fabricates beyond its
      input (conservation), and a run the broker resolved without a single fill
      did not trade (DL-59). Split from the verdict logic to keep both readable.
External I/O: none.
"""

from __future__ import annotations

from orchestration.observatory import Breach, CrossCheck


def _conserves(child: str, child_key: str, parent: str, parent_key: str) -> CrossCheck:
    """No fabrication: a stage's output count cannot exceed its input count."""

    def check(observed: dict[str, dict[str, object]]) -> Breach | None:
        out = observed.get(child, {}).get(child_key)
        src = observed.get(parent, {}).get(parent_key)
        if not isinstance(out, int) or not isinstance(src, int):
            return None
        if out > src:
            return Breach(
                child, child_key, f"{out} > {parent}.{parent_key}={src} (fabricated)"
            )
        return None

    return check


def _orders_must_fill() -> CrossCheck:
    """Submitting is not trading: a run the broker resolved with no fill is a FAIL.

    Scored on the broker's own answer, so it stays silent while orders are still
    queued — an after-hours run is UNPROVEN, not failed (DL-59).
    """

    def check(observed: dict[str, dict[str, object]]) -> Breach | None:
        execution = observed.get("execution", {})
        # Counted from the Fill nodes, not ExecutionRun.submitted: a broker that
        # refuses an order at submit time leaves submitted=0, and scoring on intent
        # would let exactly that run pass.
        orders = execution.get("orders")
        filled = execution.get("filled")
        unfilled = execution.get("unfilled")
        if not all(isinstance(v, int) for v in (orders, filled, unfilled)):
            return None
        if orders and not filled and unfilled == orders:
            seen = execution.get("statuses") or "unknown"
            return Breach(
                "execution",
                "filled",
                f"0 of {orders} submitted orders filled; the broker resolved "
                f"every one unfilled ({seen}) - the run traded nothing",
            )
        return None

    return check


# Each agent's output is bounded by its input — the boundaries asserted (EXEC-NEV-01:
# "never decides what to trade"; the scanner/analyst/PM cannot invent names).
_CONSERVATION: tuple[CrossCheck, ...] = (
    _conserves("scanner", "survived", "provider", "returned"),
    _conserves("analyst", "scored", "scanner", "survived"),
    _conserves("pm", "approved", "analyst", "scored"),
    _conserves("execution", "submitted", "pm", "approved"),
    _orders_must_fill(),
)
