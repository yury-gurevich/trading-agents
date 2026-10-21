"""The finished fire's book placement and the RED and malformed-session bounds.

Agent: orchestration
Role: prove A10-A12 through existing real brief fixtures and the composer.
External I/O: none; the Telegram port is a recording fake.
"""

from __future__ import annotations

import pytest

from kernel import InMemoryGraphStore, Node
from orchestration.batch_chain import walk_chain
from orchestration.daily_brief_facts import brief_facts
from orchestration.daily_brief_text import BriefDataError, BriefFacts, compose_brief
from orchestration.tests.book_fixtures import BOOK_LINES, seed_book
from orchestration.tests.daily_brief_fixtures import DAY, at, fire, seed_run
from orchestration.tests.daily_brief_scenarios import A1_TEXT, seed_pair
from orchestration.tests.scheduled_dispatch_human_helpers import FakeTelegram

RUN = "sched-2026-09-25"


def test_a_finished_brief_carries_the_book_after_its_fills() -> None:
    """DSP-OUT-10 / DSP-OUT-06: exact fire text, then book/container/LLM order."""
    graph = InMemoryGraphStore()
    seed_pair(graph)
    seed_book(graph, DAY)
    telegram = FakeTelegram()

    fire(graph, telegram, at(22, 50))

    expected = A1_TEXT.replace("Filled: none", "\n".join(("Filled: none", *BOOK_LINES)))
    assert telegram.briefs == [expected]
    facts = BriefFacts(
        verdict="PASS",
        run_id=RUN,
        stamp="Sat 26 Sep 08:50",
        containers="Containers: no alarms in 24 hours",
        llm="LLM: analyst on vendor/model/effort",
        book=BOOK_LINES,
    )
    assert compose_brief(facts).splitlines()[-5:] == [
        *BOOK_LINES,
        "Containers: no alarms in 24 hours",
        "LLM: analyst on vendor/model/effort",
        "Needs you: nothing",
    ]


def test_a_red_brief_carries_no_book() -> None:
    """DSP-OUT-10: a real unfinished run with a held book has no book lines."""
    graph = InMemoryGraphStore()
    seed_run(graph, pm_created="2026-09-25T22:41:00+00:00", through="ExecutionRun")
    seed_book(graph, DAY)
    telegram = FakeTelegram()

    fire(graph, telegram, at(23, 50))

    assert len(telegram.briefs) == 1
    lines = telegram.briefs[0].splitlines()
    assert "NOT FINISHED" in lines[0]
    assert not any(line.startswith(("Book:", "Odds,")) for line in lines)


def test_a_malformed_session_names_its_field() -> None:
    """DSP-OUT-10: an unreadable requested_at fails with the exact field name."""
    graph = InMemoryGraphStore()
    seed_pair(graph)
    seed_book(graph, DAY)
    nodes = walk_chain(graph, RUN)
    request = nodes["RunRequest"]
    nodes["RunRequest"] = Node(
        request.label, request.key, dict(request.props) | {"requested_at": "x"}
    )

    with pytest.raises(BriefDataError) as raised:
        brief_facts(graph, RUN, nodes, now=at(22, 50), timezone="Australia/Melbourne")

    assert str(raised.value) == "RunRequest.requested_at"
