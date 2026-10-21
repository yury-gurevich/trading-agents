"""Dashboard book projection: the held names and their odds on the run's session.

Agent: surfaces
Role: project `orchestration.book_odds` for the selected run as one row per held
      name and the brief's own book lines (DL-311, `SRF-OUT-09`), so the panel and
      the brief say the same thing; the likeliest to reach its stop first leads.
External I/O: reads the injected GraphStore; never writes.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from orchestration.book_brief import book_lines
from orchestration.book_odds import book_odds
from surfaces.dashboard.projections import run_request_node

if TYPE_CHECKING:
    from kernel import GraphStore
    from orchestration.book_odds import HeldName


def run_book(graph: GraphStore, run_id: str) -> dict[str, object]:
    """The book on the run's session: the brief's lines and a row per held name."""
    session = _session(graph, run_id)
    odds = None if session is None else book_odds(graph, session)
    return {
        "as_of": None if session is None else session.isoformat(),
        "lines": list(book_lines(odds)),
        "rows": [] if odds is None else [_row(name) for name in _ordered(odds.names)],
    }


def _session(graph: GraphStore, run_id: str) -> date | None:
    node = run_request_node(graph, run_id)
    if node is None:
        return None
    try:
        return date.fromisoformat(str(node.props.get("requested_at", ""))[:10])
    except ValueError:
        return None


def _ordered(names: tuple[HeldName, ...]) -> list[HeldName]:
    """Forecast names, likeliest to reach the stop first on top; then the rest."""
    return sorted(
        names,
        key=lambda n: (n.claim is None, -(n.claim.p_stop if n.claim else 0), n.ticker),
    )


def _row(name: HeldName) -> dict[str, object]:
    claim = name.claim
    row: dict[str, object] = {
        "ticker": name.ticker,
        "quantity": name.quantity,
        "forecast": claim is not None,
    }
    if claim is not None:
        row.update(
            {
                "close_cents": claim.close_cents,
                "stop_cents": claim.stop_cents,
                "target_cents": claim.target_cents,
                "past_target": claim.passed,
                "p_target_first": claim.p_target,
                "p_stop_first": claim.p_stop,
                "p_neither": claim.p_neither,
                "gain_cents": name.gain_cents(claim),
            }
        )
    return row
