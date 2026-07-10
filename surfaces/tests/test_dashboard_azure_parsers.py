"""Azure dashboard fixture-parser tests.

Agent: surfaces
Role: prove pure parsing of committed app, job, log, and cost REST payloads.
External I/O: filesystem reads of committed JSON fixtures only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from surfaces.dashboard.azure_parsers import (
    parse_container_apps,
    parse_cost_rows,
    parse_job_executions,
    parse_log_rows,
    parse_replica_count,
)

_FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> dict[str, object]:
    return cast(
        "dict[str, object]",
        json.loads((_FIXTURES / name).read_text(encoding="utf-8")),
    )


def test_parse_container_apps_fixture() -> None:
    rows = parse_container_apps(_fixture("azure_container_apps.json"))
    assert [row["name"] for row in rows] == ["master", "execution", "sleeping"]
    assert rows[0]["image"] == "ghcr.io/yury-gurevich/trading-agents-master:s123"
    assert rows[0]["revision"] == "master--s123"
    assert rows[2]["image"] == ""
    assert rows[2]["replicas"] is None
    assert parse_replica_count({"value": [{"name": "one"}, {"name": "two"}]}) == 2


def test_parse_job_executions_fixture_newest_first() -> None:
    rows = parse_job_executions(_fixture("azure_job_executions.json"))
    assert [row["name"] for row in rows] == [
        "dispatcher-cron-new",
        "dispatcher-cron-old",
    ]
    assert str(rows[0]["image"]).endswith(":s123")
    assert rows[1]["image"] == ""


def test_parse_log_rows_fixture_and_empty_table() -> None:
    rows = parse_log_rows(_fixture("azure_log_rows.json"))
    assert [row["level"] for row in rows] == ["info", "warning", "error"]
    assert rows[0]["container"] == "execution"
    assert parse_log_rows({"tables": []}) == []


def test_parse_cost_rows_fixture_by_column_name() -> None:
    rows = parse_cost_rows(_fixture("azure_cost_rows.json"))
    assert rows == [
        {"service": "Service Bus", "cost": 5.83, "currency": "AUD"},
        {"service": "Container Apps", "cost": 1.1, "currency": "AUD"},
        {"service": "Log Analytics", "cost": 0.36, "currency": "AUD"},
    ]
