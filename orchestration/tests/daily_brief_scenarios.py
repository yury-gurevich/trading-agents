"""Shared S234 scenarios: the measured run pair, its expected brief, amount checks.

Agent: orchestration
Role: give every daily-brief test one A1 scenario and one definition of "an amount".
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from orchestration.batch_chain import walk_chain
from orchestration.daily_brief_facts import brief_facts
from orchestration.daily_brief_text import compose_brief
from orchestration.tests.daily_brief_fixtures import (
    PREVIOUS_DAY,
    at,
    metrics_with,
    performance,
    seed_run,
)
from orchestration.tests.scheduled_dispatch_human_helpers import preflight

if TYPE_CHECKING:
    from kernel import InMemoryGraphStore, Node

RUN_KEY = "run-request:sched-2026-09-25"
MINUS = chr(0x2212)  # the typographic minus the brief prints
A1_TEXT = "\n".join(
    (
        "\U0001f7e2 PASS · sched-2026-09-25 · Sat 26 Sep 08:50",
        f"Equity $101,976.32 ({MINUS}$24.40 since sched-2026-09-24)",
        "vs SPY: -0.43 pts over 33 sessions at 21% invested",
        "Orders: none",
        "Filled: none",
        "Needs you: nothing",
    )
)
# Every textual form the two stored figures could take outside the message.
AMOUNTS = ("$", "101,976", "101976", "10197632", "24.40", "10200072", "102,000")


def seed_pair(graph: InMemoryGraphStore, *, briefed: bool = False) -> None:
    """sched-2026-09-24 (briefed, 10,200,072) then sched-2026-09-25 (10,197,632)."""
    seed_run(
        graph,
        PREVIOUS_DAY,
        pm_created="2026-09-24T22:40:00+00:00",
        metrics=metrics_with(performance(10_200_072.0)),
        briefed=True,
    )
    seed_run(graph, pm_created="2026-09-25T22:41:00+00:00", briefed=briefed)
    preflight(graph, passed=True, checked_at=at(22, 45))


def run_request(graph: InMemoryGraphStore) -> Node:
    """Return the fixture day's RunRequest."""
    node = graph.get_node("RunRequest", RUN_KEY)
    assert node is not None
    return node


def amount_free(text: str) -> bool:
    """Whether a piece of text carries none of the brief's amounts."""
    return not any(amount in text for amount in AMOUNTS)


def fault_text(fault: Node) -> str:
    """Every field of a Fault a reader could see, except its clock."""
    names = ("error_type", "message", "traceback", "context", "source_module")
    return " ".join(str(fault.props.get(name)) for name in names)


def add_fill(graph: InMemoryGraphStore, key: str, **props: object) -> Node:
    """Append one execution-shaped Fill fact."""
    base: dict[str, object] = {"side": "buy", "quantity": 10, "ticker": key.upper()}
    return graph.merge_node("Fill", key, base | props)


def brief_lines(
    graph: InMemoryGraphStore, run_id: str = "sched-2026-09-25"
) -> list[str]:
    """Compose the brief a fire at 22:50 would send, one line per item."""
    nodes = walk_chain(graph, run_id)
    facts = brief_facts(
        graph, run_id, nodes, now=at(22, 50), timezone="Australia/Melbourne"
    )
    return compose_brief(facts).splitlines()
