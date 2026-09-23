"""Deploy-currency tests for a main that was rebuilt after the deploy.

Agent: surfaces
Role: prove a newer build reads behind only when files the fleet runs moved.
External I/O: none; GitHub reads are injected fakes.
"""

from __future__ import annotations

from typing import cast

import pytest

from kernel import InMemoryGraphStore
from surfaces.dashboard.projections_currency import deploy_currency_projection
from surfaces.tests.test_dashboard_currency import _BuildReader, _containers, _record


@pytest.mark.parametrize(
    ("changes", "status", "count", "says"),
    [
        ((), "current", 0, "only documents, tests or the version number"),
        (("agents/scanner/filters.py", "uv.lock"), "behind", 2, "changed 2 file(s)"),
        (
            tuple(f"kernel/m{index:02}.py" for index in range(25)),
            "behind",
            25,
            "changed 25 file(s)",
        ),
    ],
)
def test_newer_main_build_is_behind_only_when_runtime_files_moved(
    changes: tuple[str, ...], status: str, count: int, says: str
) -> None:
    """A version bump or law edit rebuilds images without changing what runs."""
    graph = InMemoryGraphStore()
    _record(graph, sha="deployed-sha")
    reader = _BuildReader("new-main-sha", changes=changes)

    result = deploy_currency_projection(
        graph, _containers("s123"), reader, azure_verified=True
    )

    assert result["status"] == status
    assert reader.compared == [("deployed-sha", "new-main-sha")]
    evidence = cast("dict[str, object]", result["evidence"])
    assert evidence["main_matches_record"] is False
    assert evidence["runtime_change_count"] == count
    assert evidence["runtime_changes"] == list(changes[:20])
    assert says in str(result["message"])


def test_matching_builds_and_mixed_tags_never_compare_trees() -> None:
    graph = InMemoryGraphStore()
    _record(graph)
    reader = _BuildReader(changes=())

    deploy_currency_projection(graph, _containers("s123"), reader, azure_verified=True)
    mixed = deploy_currency_projection(
        graph, _containers("s123", "s121"), _BuildReader("x"), azure_verified=True
    )

    assert reader.compared == []
    assert mixed["status"] == "behind"
    evidence = cast("dict[str, object]", mixed["evidence"])
    assert evidence["runtime_changes"] is None


def test_unreadable_comparison_is_unverified_not_behind() -> None:
    graph = InMemoryGraphStore()
    _record(graph, sha="deployed-sha")
    reader = _BuildReader("new-main-sha", fail_diff=True)

    result = deploy_currency_projection(
        graph, _containers("s123"), reader, azure_verified=True
    )

    assert result["status"] == "unverified"
    assert "could not be read" in str(result["message"])
