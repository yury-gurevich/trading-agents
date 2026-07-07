"""Regression tests for the Service Bus request proof helper.

Agent: tooling
Role: keep live proof output JSON-serializable after reading frozen graph payloads.
External I/O: none.
"""

from __future__ import annotations

import json
from types import MappingProxyType

from scripts.servicebus_request import _jsonable


def test_jsonable_thaws_frozen_graph_payloads() -> None:
    payload = MappingProxyType(
        {
            "outer": MappingProxyType({"value": 1}),
            "items": (MappingProxyType({"name": "alpha"}),),
        }
    )

    normalized = _jsonable(payload)

    assert normalized == {"outer": {"value": 1}, "items": [{"name": "alpha"}]}
    json.dumps(normalized, sort_keys=True)
