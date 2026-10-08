"""The output ceiling and manager wait follow the measured envelope (S257).

Agent: deliberator
Role: refuse caps beyond the non-streaming client limit and wire bounded waits.
External I/O: reads the deliberator law book; all transports are synthetic.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

import kernel.llm_anthropic as anthropic_adapter
from agents.deliberator import entrypoint
from agents.deliberator.settings import DeliberatorSettings
from kernel import AzureServiceBusSettings, FakeLLMClient, InMemoryGraphStore, describe


def test_the_cap_cannot_exceed_anthropics_nonstreaming_limit() -> None:
    """DLIB-DEP-04 / DLIB-NEV-06: no legal cap exceeds the measured client limit."""
    ceiling = getattr(anthropic_adapter, "NONSTREAMING_MAX_TOKENS", None)
    assert ceiling == 600 * 128_000 // 3_600
    row = {item.name: item for item in describe(DeliberatorSettings)}["max_tokens"]
    assert row.maximum is not None
    assert row.maximum <= ceiling


def test_the_manager_may_wait_up_to_300_seconds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DLIB-PERF-02 / DLIB-DEP-04: the bounded setting reaches the peer client."""
    settings = DeliberatorSettings(request_timeout_seconds=300.0)
    assert settings.request_timeout_seconds == 300.0
    assert DeliberatorSettings().request_timeout_seconds == 30.0
    with pytest.raises(ValidationError, match="request_timeout_seconds"):
        DeliberatorSettings(request_timeout_seconds=300.1)

    law = (Path(__file__).parents[1] / "laws" / "laws.md").read_text(encoding="utf-8")
    assert "| `request_timeout_seconds` | `30.0` | float >= 1 <= 300 | YES |" in law
    why = str(DeliberatorSettings.model_fields["request_timeout_seconds"].description)
    assert "Bounds manager wait time for served proponent/opponent replies." in why
    for reason in ("190", "slowest", "cap"):
        assert reason in why

    sent: dict[str, object] = {}

    def peer_client(graph: object, **kwargs: object) -> object:
        sent.update(kwargs)
        return object()

    monkeypatch.setattr(
        entrypoint,
        "AzureServiceBusSettings",
        lambda: AzureServiceBusSettings(
            connection_string="synthetic", connection_strings_json=None
        ),
    )
    monkeypatch.setattr(entrypoint, "ServiceBusPeerClient", peer_client)
    entrypoint.build_manager(InMemoryGraphStore(), settings, llm=FakeLLMClient({}))
    assert sent["timeout_seconds"] == 300.0
