"""Disposable topic names, lazy SDK import and isolated memory settings.

Agent: tooling
Role: prove DL-279 A9/A10 without constructing any live transport.
External I/O: none; only a child Python process for the fresh import proof.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest
from scripts.debate_lanes import main
from scripts.debate_lanes_live import PRODUCTION_TOPICS, guard_topic_names, topic_names
from scripts.debate_lanes_memory import MemoryTransport


def test_disposable_names_hold_the_run_id():
    """DL-279 A9: the suffix isolates the manager while retaining its identity."""
    assert topic_names("lanes-example") == (
        "lanes-example-proponent.requests",
        "lanes-example-opponent.requests",
        "deliberator-manager.lanes-example.reply",
    )


@pytest.mark.parametrize(
    ("run_id", "topic"),
    [
        ("deliberator-manager", "deliberator-manager.reply"),
        ("deliberator-proponent", "deliberator-proponent.requests"),
        ("deliberator-opponent", "deliberator-opponent.requests"),
        ("lanes-example", "some-other.requests"),
        ("", "any.requests"),
    ],
)
def test_fleet_or_unrelated_topic_is_refused(run_id, topic):
    """DL-279 A9: a run id substring cannot excuse any fleet topic."""
    with pytest.raises(ValueError, match="refused non-disposable"):
        guard_topic_names(run_id, (topic,))
    assert len(PRODUCTION_TOPICS) == 3


def test_live_without_connection_string_returns_two_and_creates_nothing(
    monkeypatch, capsys
):
    """DL-279 A9: absent credentials are refused before any SDK call."""
    monkeypatch.delenv("SERVICEBUS_CONNECTION_STRING", raising=False)
    monkeypatch.delenv("AZURE_SERVICEBUS_CONNECTION_STRING", raising=False)
    loaded = set(sys.modules)
    assert main(["--transport", "live", "--concurrency", "1"]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "SERVICEBUS_CONNECTION_STRING is required" in output.err
    assert not any(
        name.startswith("azure.servicebus") for name in set(sys.modules) - loaded
    )


def test_live_module_imports_with_the_azure_sdk_refused():
    """DL-279 A10: even an unavailable SDK permits importing the live module."""
    result = subprocess.run(
        [sys.executable, "-m", "tests.debate_lanes_import_probe"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "live module imported; Azure Service Bus modules: 0"


def test_memory_settings_ignore_connections_in_the_environment(monkeypatch):
    """DL-279 D5 / DLIB-DEP-02: the memory ports cannot reach live credentials."""
    for name in ("SERVICEBUS_CONNECTION_STRING", "AZURE_SERVICEBUS_CONNECTION_STRING"):
        monkeypatch.setenv(name, "must-never-be-used")
    monkeypatch.setenv("AZURE_SERVICEBUS_CONNECTION_STRINGS_JSON", "not JSON")
    transport = MemoryTransport()
    assert transport.sb.connection_string is None
    assert transport.sb.connection_strings_json is None
    assert transport.sb.connection_string_for_topic(transport.reply_topic) is None
    assert transport.sb.receive_max_messages == 1
    assert os.getenv("AZURE_SERVICEBUS_CONNECTION_STRINGS_JSON") == "not JSON"
