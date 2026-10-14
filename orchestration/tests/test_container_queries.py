"""A13: malformed tables and hostile replica names are refused.

Agent: orchestration
Role: prove safe parsing and query interpolation at the reader boundary.
External I/O: none; all HTTP responses are stand-ins.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from orchestration.container_queries import (
    ContainerLogReadError,
    lines_query,
    table_rows,
)
from orchestration.tests.container_reader_helpers import Opener, reader
from orchestration.tests.container_sensor_helpers import NOW


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"tables": []},
        {"tables": [7]},
        {"tables": [{"columns": None, "rows": []}]},
        {"tables": [{"columns": [], "rows": None}]},
        {"tables": [{"columns": [{}], "rows": [[7]]}]},
        {"tables": [{"columns": [None], "rows": [[7]]}]},
        {"tables": [{"columns": [{"name": "x"}], "rows": [[]]}]},
        {"tables": [{"columns": [], "rows": [7]}]},
    ],
)
def test_a13_bad_table_is_a_shape_failure(payload: dict[str, object]) -> None:
    """DSP-SEC-03: malformed tables yield the shape word, never any table contents."""
    with pytest.raises(ContainerLogReadError) as failed:
        table_rows(payload)
    assert (str(failed.value), failed.value.status) == ("read failed (shape)", "shape")


@pytest.mark.parametrize(
    "name", ["replica' | take 1", "Provider-abc", "", "-leading", "a" * 101]
)
def test_a13_hostile_replica_is_never_sent(name: str) -> None:
    """DSP-SEC-03: an invalid platform name cannot reach a query or trigger HTTP."""
    opener = Opener([])
    assert reader(opener).error_lines([name], NOW, NOW) == []
    assert opener.calls == []
    query = lines_query([name, "provider-abc"], NOW - timedelta(minutes=15), NOW)
    assert "in ('provider-abc') and Stream_s == 'stderr'" in query
    assert "| take 500" in query
    if name:
        assert name not in query


def test_a13_first_table_is_read_by_column_name() -> None:
    """DSP-SEC-03: the first table's row cells match its named columns exactly."""
    assert table_rows(
        {
            "tables": [
                {
                    "columns": [{"name": "app"}, {"name": "count"}],
                    "rows": [["provider", 2]],
                },
                {"malformed": True},
            ]
        }
    ) == [{"app": "provider", "count": 2}]
