"""The unattended scorecard over MCP, the chat's quick ask and the dashboard route.

Agent: surfaces
Role: prove one answer from the graph everywhere, whatever run is selected, no model.
External I/O: none; the graph is in-memory and the bus refuses every call.
"""

from __future__ import annotations

import io
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from kernel import InMemoryGraphStore
from surfaces import scorecard_tool as tool_module
from surfaces.context import SurfaceContext
from surfaces.dashboard.app import build_app
from surfaces.dashboard.chat import _QUICK_TOOLS, handle_chat
from surfaces.dashboard.projections_scorecard import scorecard_vital
from surfaces.mcp_tools import dispatch_tool
from surfaces.scorecard_settings import ScorecardSettings
from surfaces.tests.scorecard_fixtures import NOW, WEEK, at, command, deploy, session
from surfaces.tests.test_dashboard_app import invoke

if TYPE_CHECKING:
    import pytest

    from kernel import MessageBus

_STATIC = Path(__file__).parents[1] / "dashboard" / "static"
_ANSWER = (
    "Unattended for the last 4 sessions and untouched for 2, of the 20 in a row the "
    "goal needs; 5 of 20 scheduled sessions completed (25 %, goal at least 95 %), "
    "and a human acted on 1 of 5 healthy ones (20 %, goal under 20 %; 2 counting "
    "deploys). Not counted, because the graph does not record them: broker orders "
    "placed or cancelled by hand, Azure changes other than a recorded deploy, and "
    "graph repairs made by scripts."
)


class _RefusingBus:
    """A bus that fails the test if any agent (operator, model, supervisor) is asked."""

    def __init__(self) -> None:
        self.calls = 0

    def request(self, message: object) -> object:
        self.calls += 1
        raise AssertionError(f"no agent may be called: {message!r}")


def _graph() -> InMemoryGraphStore:
    """WEEK briefed and complete; an approve on Monday; a deploy on Wednesday."""
    graph = InMemoryGraphStore()
    for day, word in zip(
        WEEK, ("PASS", "PASS", "PASS", "PASS", "NO_TRADE"), strict=True
    ):
        session(graph, day, verdict=word)
    command(graph, at(WEEK[0], 5), key="approve", family="approve")
    deploy(graph, at(WEEK[2], 4))
    return graph


def _ask(ctx: SurfaceContext, message: str, run_id: str) -> dict[str, object]:
    body = json.dumps({"message": message, "run_id": run_id})
    environ: dict[str, Any] = {
        "REQUEST_METHOD": "POST",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body.encode()),
    }
    status, payload = handle_chat(environ, ctx)
    assert status == 200
    return cast("dict[str, object]", payload["turn"])


def test_a11_mcp_chat_and_tile_give_one_answer_with_no_model_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SRF-OUT-08 / SRF-TRG-02: the same numbers from all three; no agent, no model.

    Asked with two different runs selected, the chat's answer does not change:
    the scorecard is a window of sessions, never the selected run.
    """
    graph = _graph()
    monkeypatch.setattr(tool_module, "utc_now", lambda: NOW)
    bus = _RefusingBus()
    ctx = SurfaceContext(graph, cast("MessageBus", bus))

    result = dispatch_tool(ctx, "scorecard", {})
    turns = [_ask(ctx, "Running unattended", run) for run in ("sched-2026-09-21", "x")]
    tile = scorecard_vital(graph, ScorecardSettings(), now=NOW)

    numbers = ("sessions", "complete", "healthy", "hands_on", "hands_on_with_deploys")
    assert [result[name] for name in numbers] == [20, 5, 5, 1, 2]
    assert (result["unattended"], result["untouched"], result["g3"]) == (4, 2, 0.2)
    assert result["summary"] == _ANSWER == tile["summary"]
    assert [(turn["outcome"], turn["message"]) for turn in turns] == [
        ("answer", _ANSWER),
        ("answer", _ANSWER),
    ]
    assert bus.calls == 0
    json.dumps(result)


def test_the_tool_says_plainly_when_there_is_nothing_to_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SRF-OUT-08 / SRF-FAIL-02: an empty window is a plain answer with no numbers."""
    monkeypatch.setattr(tool_module, "utc_now", lambda: NOW)
    monkeypatch.setenv("DASHBOARD_SCORECARD_WINDOW_DAYS", "1")
    ctx = SurfaceContext(InMemoryGraphStore(), cast("MessageBus", _RefusingBus()))

    result = dispatch_tool(ctx, "scorecard", {})

    assert result == {
        "status": "unavailable",
        "reason": "no scheduled session in the window has closed yet",
        "summary": "There is nothing to score yet: no scheduled session in the "
        "window has closed yet.",
    }


def test_the_tool_reports_an_unplaceable_record_in_plain_words(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SRF-OUT-08 / SRF-FAIL-02: the chat hears which record, not a traceback."""
    graph = _graph()
    graph.merge_node("RunHoldAnswer", "answer:x", {"answered_at": "soon"})
    monkeypatch.setattr(tool_module, "utc_now", lambda: NOW)
    ctx = SurfaceContext(graph, cast("MessageBus", _RefusingBus()))

    turn = _ask(ctx, "running unattended", "sched-2026-09-25")

    assert (turn["outcome"], turn["message"]) == (
        "refused",
        "one RunHoldAnswer carries no readable time",
    )


def test_the_quick_ask_the_tile_and_its_script_are_wired() -> None:
    """SRF-OUT-06 / SRF-OUT-08: the button, the slot, and a script blind to the run.

    The script fetches its own route and does not listen for a run selection.
    """
    page = (_STATIC / "index.html").read_text(encoding="utf-8")
    script = (_STATIC / "scorecard.js").read_text(encoding="utf-8")

    assert _QUICK_TOOLS["running unattended"] == "scorecard"
    assert 'data-ask="Running unattended"' in page
    assert 'id="vital-scorecard"' in page
    assert '<script src="/scorecard.js' in page
    assert 'fetch("/api/scorecard")' in script
    assert "run-selected" not in script


def test_the_route_serves_the_window_and_ignores_any_run() -> None:
    """SRF-TYP-02 / SRF-OUT-08: GET answers JSON whatever run is named; POST is 405."""
    app = build_app(_graph(), now=NOW)

    status, _headers, body = invoke(app, "/api/scorecard")
    named = invoke(app, "/api/scorecard?run_id=sched-2026-09-21")
    posted = invoke(app, "/api/scorecard", method="POST")
    script = invoke(app, "/scorecard.js")

    payload = json.loads(body)
    assert (status, payload["tone"], payload["status"]) == (
        "200 OK",
        "crit",
        "measured",
    )
    assert json.loads(named[2]) == payload
    assert (posted[0], script[0]) == ("405 Method Not Allowed", "200 OK")


def test_the_tool_ends_its_window_now_in_utc() -> None:
    """SRF-OUT-08: the tool's window ends at an aware UTC instant: now."""
    before = datetime.now(tz=UTC)

    now = tool_module.utc_now()

    assert now.tzinfo is UTC
    assert before <= now <= datetime.now(tz=UTC)
