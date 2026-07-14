"""Operator-language guard for dashboard assets and API display strings.

Agent: surfaces
Role: prevent sprint and design-log identifiers from leaking into the dashboard.
External I/O: reads committed static assets; API dependencies are in-memory fakes.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path

from surfaces.dashboard import build_app
from surfaces.tests.dashboard_fakes import FakeAzureReader
from surfaces.tests.test_dashboard_app import invoke
from surfaces.tests.test_dashboard_costs import _settings
from surfaces.tests.test_dashboard_projections import cascade_graph

_JARGON = re.compile(r"\b(?:S\d{2,3}|DL-\d+)\b")
_STATIC = Path(__file__).parents[1] / "dashboard" / "static"


def _strings(value: object) -> list[str]:
    """Flatten every API string; raw data stays eligible except lowercase image tags."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [text for item in value.values() for text in _strings(item)]
    if isinstance(value, (list, tuple)):
        return [text for item in value for text in _strings(item)]
    return []


def test_static_assets_contain_no_internal_identifiers() -> None:
    offenders = {
        path.name: match.group()
        for path in _STATIC.iterdir()
        if path.is_file()
        for match in [_JARGON.search(path.read_text(encoding="utf-8"))]
        if match is not None
    }
    assert offenders == {}


def test_api_display_strings_contain_no_internal_identifiers() -> None:
    app = build_app(cascade_graph("guard"), FakeAzureReader(), _settings())
    paths = [
        "/api/runs",
        "/api/infra",
        "/api/fleet?run_id=guard",
        "/api/vitals?run_id=guard",
        "/api/verdict?run=guard",
        "/api/chat",
        "/api/containers/execution/logs",
        *(
            f"/api/runs/guard/{view}"
            for view in (
                "verdict",
                "stages",
                "flags",
                "positions",
                "recovery",
                "bundle",
            )
        ),
    ]
    offenders: list[tuple[str, str]] = []
    for path in paths:
        status, _, body = invoke(app, path)
        assert status == "200 OK", path
        offenders.extend(
            (path, match.group())
            for text in _strings(json.loads(body))
            if (match := _JARGON.search(text)) is not None
        )
    assert offenders == []
