"""Shadow-book hit-direction tests.

Agent: orchestration
Role: prove a sell is scored a hit when the price falls, and a hold has no hit rate.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

import pytest

from kernel import InMemoryGraphStore
from orchestration.shadow_book import derive_shadow_book
from orchestration.shadow_book_scorecard import score_rows
from orchestration.tests.shadow_book_helpers import (
    add_market,
    bar,
    recommendation,
    seed_run,
)

AS_OF = date(2026, 8, 3)
NEXT_DAY = date(2026, 8, 4)


def test_hit_rate_is_direction_aware_for_sells() -> None:
    """A sell is a hit when the price FALLS, and a hold cannot be hit at all.

    Planted violation: the first shipped scorecard scored every row as
    ``forward_return > 0``, which inverted every sell. Against the live graph it
    reported 1-day sells at a 16.67% hit rate on a -6.75% mean return (those
    sells were right) and 5-day sells at 80% on +6.17% (those were wrong).
    Both sells here FALL, so the correct rule scores 100% and the old rule scores
    0%. An earlier version of this fixture used one falling and one rising sell
    and read 50% under BOTH rules - it passed the planted violation and was
    therefore proving nothing.
    """
    graph = InMemoryGraphStore()
    seed_run(
        graph,
        "analyst-directional",
        AS_OF,
        (
            recommendation("FALL", action="sell", confidence=0.62),
            recommendation("FALL2", action="sell", confidence=0.62),
            recommendation("FLAT", action="hold", confidence=0.62),
        ),
        (
            bar("FALL", AS_OF, 100.0),
            bar("FALL2", AS_OF, 100.0),
            bar("FLAT", AS_OF, 100.0),
        ),
    )
    add_market(
        graph,
        "forward-directional",
        NEXT_DAY,
        (
            bar("FALL", NEXT_DAY, 90.0),
            bar("FALL2", NEXT_DAY, 95.0),
            bar("FLAT", NEXT_DAY, 101.0),
        ),
    )

    rows = {
        row.bucket: row
        for row in score_rows(
            derive_shadow_book(graph, (1,)), confidence_bucket_width=0.05
        )
        if row.cut == "action"
    }

    assert rows["sell"].directional_n == 2
    assert rows["sell"].hit_rate == pytest.approx(1.0)
    assert rows["hold"].directional_n == 0
    assert rows["hold"].hit_rate is None
