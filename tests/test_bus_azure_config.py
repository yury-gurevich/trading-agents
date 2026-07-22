"""Azure Service Bus settings tests.

Agent: kernel
Role: pin environment parsing and entity-level SAS bundle fallback behavior.
External I/O: none.
"""

from __future__ import annotations

import json

from kernel import AzureServiceBusSettings


def test_settings_connection_string_read_from_env(monkeypatch) -> None:
    monkeypatch.setenv("AZURE_SERVICEBUS_CONNECTION_STRING", "Endpoint=sb://example/")

    settings = AzureServiceBusSettings()

    assert settings.connection_string == "Endpoint=sb://example/"


def test_settings_accepts_servicebus_connection_string_alias(monkeypatch) -> None:
    monkeypatch.delenv("AZURE_SERVICEBUS_CONNECTION_STRING", raising=False)
    monkeypatch.setenv("SERVICEBUS_CONNECTION_STRING", "Endpoint=sb://alias/")

    settings = AzureServiceBusSettings()

    assert settings.connection_string == "Endpoint=sb://alias/"


def test_settings_resolves_topic_scoped_connection_string() -> None:
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
    assert settings.connection_string_for_topic("researcher.reply") == "shared"


def test_settings_topic_bundle_falls_back_on_unusable_values() -> None:
    malformed = AzureServiceBusSettings(
        _env_file=None,
        connection_string="shared",
        connection_strings_json="{",
    )
    missing_value = AzureServiceBusSettings(
        _env_file=None,
        connection_string="shared",
        connection_strings_json=json.dumps({"topic": {"rights": ["Send"]}}),
    )
    empty_value = AzureServiceBusSettings(
        _env_file=None,
        connection_string="shared",
        connection_strings_json=json.dumps({"topic": {"connection_string": ""}}),
    )

    assert malformed.connection_string_for_topic("topic") == "shared"
    assert missing_value.connection_string_for_topic("topic") == "shared"
    assert empty_value.connection_string_for_topic("topic") == "shared"


def test_settings_defaults_to_none_without_env(monkeypatch) -> None:
    monkeypatch.delenv("AZURE_SERVICEBUS_CONNECTION_STRING", raising=False)
    monkeypatch.delenv("SERVICEBUS_CONNECTION_STRING", raising=False)
    monkeypatch.delenv("AZURE_SERVICEBUS_CONNECTION_STRINGS_JSON", raising=False)

    settings = AzureServiceBusSettings(_env_file=None)

    assert settings.connection_string is None
    assert settings.connection_string_for_topic("topic") is None
