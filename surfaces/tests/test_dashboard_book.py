"""The selected session's book API and the served, wired trading panel.

Agent: surfaces
Role: prove A13-A15 with literal rows and in-memory WSGI requests.
External I/O: none.
"""

from __future__ import annotations

import json

from kernel import InMemoryGraphStore
from orchestration.start import place_run_request
from orchestration.tests.book_fixtures import DAY, lot, seed_book
from surfaces.dashboard import build_app
from surfaces.tests.test_dashboard_app import invoke

RUN = "sched-2026-10-20"


def test_the_book_view_says_what_the_brief_says_and_leads_with_the_stop() -> None:
    """SRF-OUT-09 / SRF-OUT-01: selected-session lines and exact ordered rows."""
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id=RUN, tickers=("COP",), as_of=DAY)
    seed_book(graph)
    lot(graph, "PM", 2, 18000)

    status, _, body = invoke(build_app(graph), f"/api/runs/{RUN}/book")

    assert status == "200 OK"
    from orchestration.book_brief import book_lines
    from orchestration.book_odds import book_odds

    data = json.loads(body)
    assert data["as_of"] == "2026-10-20"
    assert data["lines"] == list(book_lines(book_odds(graph, DAY)))
    rows = data["rows"]
    assert [row["ticker"] for row in rows] == ["GOOG", "COP", "MO", "KO", "PM"]
    assert rows[1] == {
        "ticker": "COP",
        "quantity": 8,
        "forecast": True,
        "close_cents": 14595,
        "stop_cents": 11708,
        "target_cents": 13058,
        "past_target": True,
        "p_target_first": 0.395,
        "p_stop_first": 0.002,
        "p_neither": 0.603,
        "gain_cents": 17232,
    }
    assert rows[4] == {"ticker": "PM", "quantity": 2, "forecast": False}


def test_a_run_with_no_request_or_no_book_shows_nothing() -> None:
    """SRF-OUT-09: unknown/invalid sessions have no date, and empty book no rows."""
    from surfaces.dashboard.projections_book import run_book

    graph = InMemoryGraphStore()
    assert run_book(graph, "unknown") == {"as_of": None, "lines": [], "rows": []}
    graph.merge_node(
        "RunRequest",
        "run-request:invalid",
        {"run_id": "invalid", "requested_at": "soon"},
    )
    assert run_book(graph, "invalid") == {"as_of": None, "lines": [], "rows": []}
    place_run_request(graph, run_id=RUN, tickers=("COP",), as_of=DAY)
    assert run_book(graph, RUN) == {"as_of": "2026-10-20", "lines": [], "rows": []}


def test_the_panel_is_served_and_wired() -> None:
    """SRF-OUT-09 / SRF-OUT-05: the served panel follows run selection, no IDs."""
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id=RUN, tickers=("COP",), as_of=DAY)
    app = build_app(graph)

    page_status, _, page = invoke(app, "/")
    script_status, headers, script = invoke(app, "/book.js")

    assert page_status == "200 OK"
    assert '<div id="bookbody">' in page.decode()
    assert '<script src="/book.js' in page.decode()
    assert script_status == "200 OK"
    assert "javascript" in headers["Content-Type"]
    assert "dashboard:run-selected" in script.decode()
    assert '"/book"' in script.decode()
    assert "S28" not in page.decode()
    assert "S28" not in script.decode()
