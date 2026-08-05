"""Azure Service Bus settings tests.

Agent: kernel
Role: pin environment parsing and entity-level SAS bundle routing behavior.
External I/O: none.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kernel import AzureServiceBusSettings
from kernel.bus_azure_config import BusConfigError


def _require_dotenv_file() -> None:
    if not Path(".env").is_file():
        pytest.skip("Service Bus dotenv isolation proof requires local .env")
    assert Path(".env").is_file()


def test_settings_connection_string_read_from_env(monkeypatch) -> None:
    monkeypatch.setenv("AZURE_SERVICEBUS_CONNECTION_STRING", "Endpoint=sb://example/")

    settings = AzureServiceBusSettings()

    assert settings.connection_string == "Endpoint=sb://example/"


def test_settings_accepts_servicebus_connection_string_alias(monkeypatch) -> None:
    """A5 / DEP-CONFIG-01: os.environ-only Service Bus config still resolves."""
    monkeypatch.delenv("AZURE_SERVICEBUS_CONNECTION_STRING", raising=False)
    monkeypatch.setenv("SERVICEBUS_CONNECTION_STRING", "Endpoint=sb://alias/")

    settings = AzureServiceBusSettings()

    assert settings.connection_string == "Endpoint=sb://alias/"


def test_settings_do_not_read_dotenv_after_process_env_is_cleared(
    monkeypatch,
) -> None:
    """DEP-CONFIG-02: AzureServiceBusSettings does not read .env directly."""
    _require_dotenv_file()
    monkeypatch.delenv("AZURE_SERVICEBUS_CONNECTION_STRING", raising=False)
    monkeypatch.delenv("SERVICEBUS_CONNECTION_STRING", raising=False)
    monkeypatch.delenv("AZURE_SERVICEBUS_CONNECTION_STRINGS_JSON", raising=False)

    settings = AzureServiceBusSettings()

    assert settings.connection_string is None
    assert (
        settings.connection_string_for_topic("deliberator-proponent.requests") is None
    )


def test_settings_no_bundle_uses_primary_connection_string() -> None:
    """A1: local dev and single-entity deploys keep the primary fallback."""
    settings = AzureServiceBusSettings(
        _env_file=None,
        connection_string="shared",
        connection_strings_json=None,
    )

    assert settings.connection_string_for_topic("supervisor.requests") == "shared"


def test_settings_resolves_topic_scoped_connection_string() -> None:
    """A3: a configured bundle returns the named topic entry, not the primary."""
    settings = AzureServiceBusSettings(
        _env_file=None,
        connection_string="shared",
        connection_strings_json=json.dumps(
            {
                "supervisor.requests": {
                    "connection_string": "scoped",
                    "rights": ["Send"],
                },
            }
        ),
    )

    assert settings.connection_string_for_topic("supervisor.requests") == "scoped"


def test_settings_bundle_topic_absent_raises_with_configured_keys() -> None:
    """A2: a configured bundle missing the requested topic fails loud."""
    settings = AzureServiceBusSettings(
        _env_file=None,
        connection_string="shared",
        connection_strings_json=json.dumps(
            {"supervisor.requests": {"connection_string": "scoped"}}
        ),
    )

    with pytest.raises(BusConfigError) as excinfo:
        settings.connection_string_for_topic("researcher.reply")

    message = str(excinfo.value)
    assert "researcher.reply" in message
    assert "supervisor.requests" in message


def test_settings_malformed_topic_bundle_raises_parse_error() -> None:
    """A4: malformed configured JSON is a config error, not a fallback."""
    settings = AzureServiceBusSettings(
        _env_file=None,
        connection_string="shared",
        connection_strings_json="{oops",
    )

    with pytest.raises(BusConfigError, match="malformed JSON"):
        settings.connection_string_for_topic("topic")


def test_settings_topic_bundle_must_be_json_object() -> None:
    """A4: configured bundle JSON must still have the expected object shape."""
    settings = AzureServiceBusSettings(
        _env_file=None,
        connection_string="shared",
        connection_strings_json="[]",
    )

    with pytest.raises(BusConfigError, match="JSON object"):
        settings.connection_string_for_topic("topic")


def test_settings_topic_entry_without_string_raises() -> None:
    settings = AzureServiceBusSettings(
        _env_file=None,
        connection_string="shared",
        connection_strings_json=json.dumps({"topic": {"rights": ["Send"]}}),
    )

    with pytest.raises(BusConfigError, match="non-empty connection_string"):
        settings.connection_string_for_topic("topic")


def test_2026_08_02_manager_bundle_missing_peer_topic_fails_config() -> None:
    """A5 2026-08-02: missing peer topic fails before Azure get_topic_sender."""
    settings = AzureServiceBusSettings(
        _env_file=None,
        connection_string="manager-primary",
        connection_strings_json=json.dumps(
            {
                "deliberator-manager.requests": {"connection_string": "manager-scoped"},
                "deliberator-manager.reply": {"connection_string": "manager-reply"},
            }
        ),
    )

    with pytest.raises(BusConfigError) as excinfo:
        settings.connection_string_for_topic("deliberator-proponent.requests")

    message = str(excinfo.value)
    assert "deliberator-proponent.requests" in message
    assert "deliberator-manager.requests" in message


def test_settings_defaults_to_none_without_env(monkeypatch) -> None:
    monkeypatch.delenv("AZURE_SERVICEBUS_CONNECTION_STRING", raising=False)
    monkeypatch.delenv("SERVICEBUS_CONNECTION_STRING", raising=False)
    monkeypatch.delenv("AZURE_SERVICEBUS_CONNECTION_STRINGS_JSON", raising=False)

    settings = AzureServiceBusSettings(_env_file=None)

    assert settings.connection_string is None
    assert settings.connection_string_for_topic("topic") is None
