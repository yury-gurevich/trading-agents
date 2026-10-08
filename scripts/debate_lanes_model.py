"""Canned completions and a fresh PM scene for the debate lanes command.

Agent: tooling
Role: supply D4's model and warm its guided turn before measuring D5's scene.
External I/O: none.
"""

from __future__ import annotations

import time
from decimal import Decimal

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.settings import DeliberatorSettings
from contracts.common import Explanation, Money, Provenance
from contracts.deliberator import DebateProposition, DebateTurnRequest
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import InMemoryGraphStore, InProcessBus, Node

MANAGER = "deliberator-manager"
SUBSCRIPTION = "agent"
GUIDED = (
    "[[ ## reasoning ## ]]\n"
    '{"readings": [], "gaps": []}\n\n'
    "[[ ## argument ## ]]\nA.\n\n"
    "[[ ## completed ## ]]"
)
UPHOLD = '{"ruling": "uphold", "rationale": "clears review"}'
_WARM = False


class SleepingLLM:
    """Wait for a guided turn; give the manager its verdict immediately."""

    def __init__(self, seconds: float) -> None:
        self._seconds = seconds

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, tool_schema
        if user.startswith("DECISION UNDER TEST"):
            return UPHOLD
        time.sleep(self._seconds)
        return GUIDED


def warm_up() -> None:
    """Run one guided turn so DSPy's initial import is outside every span."""
    global _WARM
    if _WARM:
        return
    agent = DeliberatorAgent(
        InProcessBus(),
        graph=InMemoryGraphStore(),
        llm=SleepingLLM(0.0),
        settings=DeliberatorSettings(_env_file=None, role="proponent"),
    )
    agent.debate_turn(
        DebateTurnRequest(
            request_id="warm-up",
            role="defender",
            round_number=1,
            proposition=DebateProposition(decision="buy WARM", context="ctx"),
        )
    )
    _WARM = True


def pm_node(graph: InMemoryGraphStore, orders: int) -> Node:
    """Record a fresh set of approved buys, exactly as in the Appendix."""
    order_set = OrderIntentSet(
        run_id="pm-lanes",
        approved=tuple(
            OrderIntent(
                ticker=f"T{n:02d}",
                action="buy",
                quantity=1,
                est_price=Money(amount=Decimal("100.00")),
                rationale=Explanation(summary=f"T{n:02d} approved"),
            )
            for n in range(orders)
        ),
        rejected=(),
        explanation=Explanation(summary="sized"),
        provenance=Provenance(run_id="pm-lanes", source_agent="portfolio_manager"),
    )
    return graph.merge_node(
        "PMRun",
        order_set.run_id,
        {"order_intent_set": order_set.model_dump(mode="json")},
    )
