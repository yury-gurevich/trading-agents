"""The scorecard tile's reason is a fixed sentence, never an exception's text.

Agent: surfaces
Role: prove no exception text reaches the dashboard through the unattended tile.
External I/O: none; in-memory graph only.

CodeQL flagged `py/stack-trace-exposure` (alerts 256 and 257) on the route S236 added:
the tile put `str(exc)` in its payload. The sentence the operator reads is unchanged;
it is now chosen from a fixed table by the record's kind.
"""

from __future__ import annotations

import json

import pytest

from kernel.graph_memory import InMemoryGraphStore
from surfaces.dashboard import projections_scorecard
from surfaces.dashboard.projections_scorecard import scorecard_vital
from surfaces.queries.scorecard_actions import PLACED_LABELS, ScorecardDataError
from surfaces.tests.scorecard_fixtures import NOW, settings


def _failing_with(label: str, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    def unplaceable(*_args: object, **_kwargs: object) -> object:
        raise ScorecardDataError(label)

    monkeypatch.setattr(projections_scorecard, "scorecard", unplaceable)
    return scorecard_vital(InMemoryGraphStore(), settings(), now=NOW)


def test_an_unknown_kind_never_reaches_the_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SRF-SEC-02 / SRF-FAIL-02: exception text never reaches the dashboard."""
    tile = _failing_with("Mystery <b>", monkeypatch)

    assert tile["reason"] == "a stored record carries no readable time"
    assert "Mystery" not in json.dumps(tile)


@pytest.mark.parametrize("label", PLACED_LABELS)
def test_every_placed_kind_keeps_its_own_sentence(
    label: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SRF-SEC-02 / SRF-OUT-08: the operator still hears which kind of record."""
    tile = _failing_with(label, monkeypatch)

    assert (tile["status"], tile["reason"]) == (
        "unavailable",
        f"one {label} carries no readable time",
    )
