"""A credential probe may spend, so it can prove the key is allowed to spend.

Agent: master
Role: pin probe request bodies, and pin the deliberator Anthropic probe to an
      endpoint a drained key actually fails.
External I/O: none; the transport is an injected fake.

🚨 Measured over four nights to 2026-09-13. Every deliberator activated cleanly
and every debate then failed with `400 … credit balance is too low`. The DL-36
entry condition existed and already listed **400** in
`credential_failure_statuses` — it simply asked the wrong question:
`GET /v1/models` is free metadata, so a zero-credit key is still a *valid* key
and returns 200. Key validity and spend capability are different facts.

Measured against the live API the same day, `POST /v1/messages` with
`max_tokens: 1`:

| Request | Status |
| --- | --- |
| valid key, body present | **200** (7 input / 1 output tokens) |
| invalid key | **401** |
| valid key, **no body** | **400** |
| valid key, retired model name | **404** |

🪤 Row three is why this file exists rather than a one-line pack edit. A bodyless
POST fails for a *valid* key, so pointing the pack at `/v1/messages` without
teaching the runner to send a body would have failed all four required Anthropic
probes at once — turning a credit outage into a total activation outage.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.master.credential_probes import HttpProbeRequest, parse_credential_tests
from agents.master.credential_test import ActivationRefused
from agents.master.tests.credential_probe_testkit import ehlo, master

PACK = Path("orchestration/packs/trading_credential_tests.json")
SPEND_PROBE_AGENTS = (
    "operator",
    "deliberator-manager",
    "deliberator-proponent",
    "deliberator-opponent",
)


def _declaration(**overrides: object) -> str:
    entry: dict[str, object] = {
        "name": "provider-llm",
        "kind": "http_status",
        "method": "POST",
        "url": "https://example.invalid/messages",
        "headers": {"Authorization": "Bearer {PROVIDER_LLM_KEY}"},
        "json_body": {"max_tokens": 1, "model": "m"},
        "expected_statuses": [200],
        "required": True,
        "cost": "cheap",
    }
    entry.update(overrides)
    return json.dumps({"provider": [entry]})


def _seen(declaration: str, status: int = 200) -> HttpProbeRequest:
    seen: list[HttpProbeRequest] = []

    def transport(request: HttpProbeRequest) -> int:
        seen.append(request)
        return status

    tests = parse_credential_tests(declaration, http_transport=transport)
    _, agent = master(tests, {"llm-key": "sentinel"})
    agent.activate(ehlo())
    return seen[0]


def test_declared_json_body_reaches_the_transport_as_sorted_bytes() -> None:
    """🎯 A probe body is serialised deterministically, keys sorted."""
    request = _seen(_declaration())

    assert request.body == b'{"max_tokens":1,"model":"m"}'


def test_a_body_probe_gets_a_json_content_type() -> None:
    """🪤 The measured 400: a body the server cannot parse reads as a bad key."""
    request = _seen(_declaration())

    assert request.headers["content-type"] == "application/json"


def test_a_pack_declared_content_type_is_not_duplicated() -> None:
    """A pack may name its own content type without the runner adding a second."""
    request = _seen(
        _declaration(
            headers={
                "Authorization": "Bearer {PROVIDER_LLM_KEY}",
                "Content-Type": "application/json; charset=utf-8",
            }
        )
    )
    content_types = [k for k in request.headers if k.lower() == "content-type"]

    assert content_types == ["Content-Type"]
    assert request.headers["Content-Type"] == "application/json; charset=utf-8"


def test_a_probe_declaring_no_body_sends_none() -> None:
    """Every pre-existing GET probe stays byte-identical to what it was."""
    declaration = json.loads(_declaration())
    del declaration["provider"][0]["json_body"]
    declaration["provider"][0]["method"] = "GET"

    request = _seen(json.dumps(declaration))

    assert request.body is None
    assert all(key.lower() != "content-type" for key in request.headers)


def test_a_non_object_json_body_is_rejected_at_load() -> None:
    """A malformed body is a pack defect, caught before any key is tested."""
    with pytest.raises(ValueError, match="json_body"):
        parse_credential_tests(_declaration(json_body=["not", "an", "object"]))


def test_a_drained_key_refuses_activation() -> None:
    """MST-NEV-06 / MST-FAIL-04: the 400 a credit-exhausted key returns halts handover.

    This is the four-night incident, end to end: the status the live API actually
    returns for an exhausted balance now reaches `ActivationRefused` instead of
    being masked by a free metadata endpoint.
    """
    tests = parse_credential_tests(_declaration(), http_transport=lambda _r: 400)
    graph, agent = master(tests, {"llm-key": "sentinel"})

    with pytest.raises(ActivationRefused, match="provider-llm"):
        agent.activate(ehlo())

    (escalation,) = graph.list_nodes("Escalation")
    assert list(escalation.props["failed_credentials"]) == ["provider-llm"]


@pytest.mark.parametrize("agent_type", SPEND_PROBE_AGENTS)
def test_the_anthropic_probe_spends_rather_than_reading_metadata(
    agent_type: str,
) -> None:
    """🎯 The pack asks the question a drained key can fail."""
    entries = json.loads(PACK.read_text(encoding="utf-8"))[agent_type]
    (probe,) = [e for e in entries if e["name"] == "anthropic"]

    assert probe["method"] == "POST"
    assert probe["url"] == "https://api.anthropic.com/v1/messages"
    assert probe["json_body"]["max_tokens"] == 1
    assert 400 in probe["credential_failure_statuses"]
    assert probe["required"] is True


@pytest.mark.parametrize("agent_type", SPEND_PROBE_AGENTS)
def test_the_probe_model_tracks_the_adapter_default(agent_type: str) -> None:
    """🪤 A retired model name returns 404, which reads as a credential failure.

    Measured 2026-09-13: `claude-does-not-exist` → **404**, and the runner maps
    every 4xx to a credential failure. So a probe naming a model the deliberator
    no longer uses would halt activation and blame the key. The pack's model must
    therefore be the model the adapter actually resolves — asserted here so the
    two cannot drift apart silently.
    """
    from agents.deliberator.llm_factory import DEFAULT_MODEL

    entries = json.loads(PACK.read_text(encoding="utf-8"))[agent_type]
    (probe,) = [e for e in entries if e["name"] == "anthropic"]

    assert probe["json_body"]["model"] == DEFAULT_MODEL["anthropic"]
