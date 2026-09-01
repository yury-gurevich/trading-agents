"""Apply the declared execution deliberation posture to order intents.

Agent: execution
Role: keep advisory/binding policy separate from deliberation status detection.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.execution.deliberation_gate import DeliberationStatus
    from contracts.execution import DeliberationPosture
    from contracts.portfolio_manager import OrderIntentSet


@dataclass(frozen=True)
class PostureFilteredOrderSet:
    """Order set after posture policy, plus buy intents blocked by that policy."""

    order_set: OrderIntentSet
    blocked_count: int


def apply_deliberation_posture(
    order_set: OrderIntentSet,
    *,
    status: DeliberationStatus,
    posture: DeliberationPosture,
) -> PostureFilteredOrderSet:
    """Drop buy exposure when binding posture has no deliberation artifact.

    Arrived veto evidence is handled by ``drop_vetoed`` before this function.
    Fail-open deliberation remains a loud ``applied_failed_open`` fact; S185 only
    changes the no-DeliberationRun branch for explicit binding posture.
    """
    if posture != "binding" or status != "proceeded_unvetoed":
        return PostureFilteredOrderSet(order_set=order_set, blocked_count=0)
    survivors = tuple(intent for intent in order_set.approved if intent.action != "buy")
    blocked = len(order_set.approved) - len(survivors)
    if blocked == 0:
        return PostureFilteredOrderSet(order_set=order_set, blocked_count=0)
    filtered = order_set.model_copy(update={"approved": survivors})
    return PostureFilteredOrderSet(order_set=filtered, blocked_count=blocked)
