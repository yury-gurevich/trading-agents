"""A run's as-of decides the coverage check, and an unusable one is refused (S249).

Agent: provider
Role: prove PROV-TRG-05's limits: the declared lookback is checked against the
      sessions up to the as-of, and a RunRequest whose as-of is absent, not an
      exact ISO date, or later than today is refused before any fetch (DL-256).
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.provider.poll import ingest_run_node
from agents.provider.tests.as_of_helpers import (
    RecordingSource,
    agent_over,
    run_request,
    window_ends,
)
from contracts.provider import MARKET_DATA_LABEL
from kernel import InMemoryGraphStore

# 2025-12-24 → 2025-12-31 holds five NYSE sessions (Christmas Day is closed).
_HOLIDAY_AS_OF = "2025-12-31"
_HOLIDAY_LOOKBACK = 7


def test_the_coverage_check_counts_sessions_up_to_the_as_of() -> None:
    """PROV-TRG-05: five sessions to the as-of cover five bars, and are ingested."""
    graph = InMemoryGraphStore()
    source = RecordingSource()
    node = run_request(
        graph, _HOLIDAY_AS_OF, lookback_days=_HOLIDAY_LOOKBACK, required_bars=5
    )
    ingest_run_node(node, agent=agent_over(graph, source))

    assert window_ends(graph) == ("2025-12-31", "2025-12-31")


def test_a_lookback_short_of_the_as_ofs_sessions_is_refused() -> None:
    """PROV-TRG-05: five sessions to the as-of miss six bars: refused, no fetch."""
    graph = InMemoryGraphStore()
    source = RecordingSource()
    node = run_request(
        graph, _HOLIDAY_AS_OF, lookback_days=_HOLIDAY_LOOKBACK, required_bars=6
    )

    with pytest.raises(ValueError, match="required history"):
        ingest_run_node(node, agent=agent_over(graph, source))
    assert source.calls == 0


@pytest.mark.parametrize(
    "as_of",
    [
        pytest.param(None, id="absent"),
        pytest.param("", id="empty"),
        pytest.param("not-a-date", id="not-a-date"),
        pytest.param("2026-09-30T22:30:00+00:00", id="a-full-datetime"),
        pytest.param("20260930", id="compact-iso"),
        pytest.param("2026-W40-3", id="iso-week"),
        pytest.param("2026-9-30", id="unpadded"),
        pytest.param(20260930, id="not-a-string"),
        pytest.param("9999-12-31", id="after-today"),
    ],
)
def test_a_request_with_no_usable_as_of_is_refused_before_any_fetch(
    as_of: object,
) -> None:
    """PROV-TRG-05: absent, not an exact ISO date, or after today: refused, no fetch."""
    graph = InMemoryGraphStore()
    source = RecordingSource()

    with pytest.raises(ValueError, match="requested_at"):
        ingest_run_node(run_request(graph, as_of), agent=agent_over(graph, source))
    assert source.calls == 0
    assert graph.list_nodes(MARKET_DATA_LABEL) == ()
