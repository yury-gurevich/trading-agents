"""Scoreboard chat answer, MCP tool and route tests.

Agent: surfaces
Role: prove "vs the market" answers from the graph with no model call, wired end to end.
External I/O: none; graph is in-memory and the bus refuses every call.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from kernel import InMemoryGraphStore
from surfaces.context import SurfaceContext
from surfaces.dashboard.app import build_app
from surfaces.dashboard.chat import _QUICK_TOOLS, handle_chat
from surfaces.mcp_tools import dispatch_tool
from surfaces.tests.performance_fixtures import MEASURED, seed_run, with_excess
from surfaces.tests.test_dashboard_app import invoke

if TYPE_CHECKING:
    from kernel import MessageBus

_M = chr(0x2212)  # the typographic minus the operator reads
_SENTENCE = (
    f"Behind the market by 0.28 pts over 32 sessions: the book returned {_M}0.45 %, "
    f"SPY {_M}0.91 %, and SPY at the book's 21 % exposure {_M}0.17 %. "
    "Over the most recent sessions: behind by 0.59 pts."
)
_STATIC = Path(__file__).parents[1] / "dashboard" / "static"


class _RefusingBus:
    """A bus that fails the test if any agent (operator, LLM, reporter) is asked."""

    def __init__(self) -> None:
        self.calls = 0

    def request(self, message: object) -> object:
        self.calls += 1
        raise AssertionError(f"no agent may be called: {message!r}")


def _context(graph: InMemoryGraphStore) -> tuple[SurfaceContext, _RefusingBus]:
    bus = _RefusingBus()
    return SurfaceContext(graph, cast("MessageBus", bus)), bus


def test_a8_the_chat_answers_from_the_graph_with_no_model_call() -> None:
    """SRF-OUT-07 / RPT-SEC-02: numbers + one sentence; no agent or LLM called."""
    graph = InMemoryGraphStore()
    seed_run(graph, "sched-2026-09-24", performance=dict(MEASURED))
    ctx, bus = _context(graph)

    result = dispatch_tool(ctx, "performance", {})

    assert result["run_id"] == "sched-2026-09-24"
    assert result["status"] == "measured"
    assert result["metrics"] == MEASURED
    assert result["summary"] == _SENTENCE
    assert bus.calls == 0
    json.dumps(result)


def test_a8_ahead_and_level_read_in_plain_words() -> None:
    """SRF-OUT-07: ahead of / level with, on the rounded number the operator reads."""
    graph = InMemoryGraphStore()
    ahead = {**with_excess(0.5), "rolling_excess_return_pct": 0.004}
    seed_run(graph, "ahead", performance=ahead)
    ctx, _bus = _context(graph)

    summary = str(dispatch_tool(ctx, "performance", {"run_id": "ahead"})["summary"])

    assert summary.startswith("Ahead of the market by 0.50 pts over 32 sessions:")
    assert summary.endswith("Over the most recent sessions: level with it.")


def test_a9_the_quick_ask_is_wired_to_the_tool() -> None:
    """SRF-OUT-06 / SRF-OUT-07: the button exists and maps to the bounded tool."""
    page = (_STATIC / "index.html").read_text(encoding="utf-8")

    assert _QUICK_TOOLS["vs the market"] == "performance"
    assert 'data-ask="vs the market"' in page
    assert '<script src="/performance.js' in page
    assert 'id="vital-performance"' in page


def test_a9_the_chat_quick_ask_answers_for_the_selected_run() -> None:
    """SRF-OUT-01 / SRF-OUT-07: the quick ask reads the run the page has selected."""
    graph = InMemoryGraphStore()
    seed_run(graph, "sched-2026-09-24", performance=dict(MEASURED))
    seed_run(graph, "later", requested_at="2026-09-25T22:30:00+00:00")
    ctx, bus = _context(graph)
    body = json.dumps({"message": "vs the market", "run_id": "sched-2026-09-24"})
    environ: dict[str, Any] = {
        "REQUEST_METHOD": "POST",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body.encode()),
    }

    status, payload = handle_chat(environ, ctx)

    turn = cast("dict[str, object]", payload["turn"])
    assert (status, turn["outcome"], turn["message"]) == (200, "answer", _SENTENCE)
    assert bus.calls == 0


def test_a10_an_unknown_run_answers_unavailable_in_plain_words() -> None:
    """SRF-FAIL-02 / SRF-OUT-07: no chain is a plain answer, not an exception."""
    ctx, _bus = _context(InMemoryGraphStore())

    missing = dispatch_tool(ctx, "performance", {"run_id": "nope"})
    empty_graph = dispatch_tool(ctx, "performance", {})
    bad = dispatch_tool(ctx, "performance", {"run_id": 7})

    assert missing["status"] == "unavailable"
    assert "metrics" not in missing
    assert str(missing["summary"]).startswith("There is no scoreboard for run nope")
    assert str(empty_graph["summary"]).startswith("There is no scoreboard")
    assert bad["error"] == "run_id must be a string"


def test_the_vital_route_serves_the_selected_run_and_404s_unknown_runs() -> None:
    """SRF-IN-01 / SRF-TYP-02 / SRF-OUT-07: graph-only route for the vital."""
    graph = InMemoryGraphStore()
    seed_run(graph, "sched-2026-09-24", performance=dict(MEASURED))
    app = build_app(graph)

    status, _headers, body = invoke(app, "/api/runs/sched-2026-09-24/performance")
    missing = invoke(app, "/api/runs/nope/performance")
    script = invoke(app, "/performance.js")

    payload = json.loads(body)
    assert (status, payload["tone"], payload["run_id"]) == (
        "200 OK",
        "warn",
        "sched-2026-09-24",
    )
    assert missing[0] == "404 Not Found"
    assert script[0] == "200 OK"
    assert "/api/runs/" in script[2].decode("utf-8")
