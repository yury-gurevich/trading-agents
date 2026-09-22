"""The one map from a PM rejection reason to the gate that produced it.

Agent: portfolio_manager
Role: hold the single reason/gate vocabulary that the PM rejects with and every
      read-only renderer displays, so the two cannot disagree.
External I/O: none.

This exists because they *did* disagree. On `sched-2026-09-21` the operator trace
rendered `GOOGL  SKIP  sizing (also failed: sizing)`: `orchestration` kept its own
inverted copy of this mapping and that copy omitted `sizing`, so the gate that
produced the rejection was not recognised as its own primary and was echoed back
as a secondary failure.

The fix is not the missing key. `REASON_TO_GATE` is *derived* from
`POSITION_GATE_REASONS` rather than retyped beside it, so a gate added on one side
cannot go missing on the other — the failure mode is removed, not this instance
of it.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Mapping

# Gate name -> the rejection reason it produces, in the PM's established
# precedence order. `position_rejection` walks this to pick the first failure,
# so the ORDER is behaviour, not presentation.
POSITION_GATE_REASONS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "sizing": "sizing",
        "min_order_quantity": "below_min_quantity",
        "max_positions": "max_positions",
        "cash_available": "insufficient_cash",
    }
)

# Reasons raised outside the position gates. Several legitimately share a gate —
# `invalid_stop_loss` and `reward_risk_below_min` are both the `reward_risk` gate —
# which is why this direction is stored and the inverse is not.
_NON_POSITION_REASON_GATES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "invalid_stop_loss": "reward_risk",
        "reward_risk_below_min": "reward_risk",
        "sector_name_count": "max_names_per_sector",
        "sector_concentration": "max_sector_pct",
        "sector_not_evaluated": "max_sector_pct",
        "correlated_cluster_concentration": "correlated_cluster_pct",
        "correlation_not_evaluated": "correlated_cluster_pct",
    }
)

# Rejection reason -> the gate that produced it, for renderers that must not
# repeat a rejection's own gate back to the reader. Derived, never retyped.
REASON_TO_GATE: Final[Mapping[str, str]] = MappingProxyType(
    {reason: gate for gate, reason in POSITION_GATE_REASONS.items()}
    | dict(_NON_POSITION_REASON_GATES)
)

# Reasons the PM raises before any gate runs. They carry no gate report, so a
# renderer has nothing to filter and correctly shows no secondary failures.
UNGATED_REASONS: Final[frozenset[str]] = frozenset(
    {
        "hold_recommendation",
        "unsupported_action",
        "position_unavailable",
        "account_unavailable",
        "price_unavailable",
    }
)
