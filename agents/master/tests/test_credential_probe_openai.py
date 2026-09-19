"""The OpenAI probe must spend, because a drained OpenAI key still lists models.

Agent: master
Role: pin the three deliberator OpenAI probes to an endpoint a key that cannot
      spend actually fails, and pin the model to the adapter default.
External I/O: none; the pack is read from disk, no request is made.

🚨 Item 53 is item 50's defect in a second place. `GET /v1/models` is free
metadata: it answers "is this key well-formed", never "may this key spend".
[DL-125] recorded the live proof on 2026-08-19 — a drained OpenAI key returns
`429 … no credits remaining` on a *billable* call while metadata still reads 200.

Measured against the live API on 2026-09-14, `POST /v1/chat/completions` with
`model: gpt-5.5`:

| Request | Status |
| --- | --- |
| valid key, `max_completion_tokens: 256` | **200** (7 input / 26-38 output tokens) |
| invalid key | **401** |
| valid key, **no body** | **400** (`you must provide a model parameter`) |
| valid key, `max_tokens` instead | **400** (`unsupported_parameter`) |
| valid key, retired model name | **404** (`model_not_found`) |
| valid key, `max_completion_tokens: 1` | **400** (`output limit was reached`) |

🪤 The last row is why the budget is 256 and not 1. `gpt-5.5` is a reasoning
model: it spends the whole budget on reasoning tokens before emitting any
content, so the Anthropic probe's `max_tokens: 1` shape returns **400 for a
perfectly valid key**. Five runs at 256 cost 26-38 completion tokens — the cap is
never reached, and an unreached cap is charged nothing, so the generous budget is
strictly safer *and* no more expensive than a tight one.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PACK = Path("orchestration/packs/trading_credential_tests.json")
OPENAI_PROBE_AGENTS = (
    "deliberator-manager",
    "deliberator-proponent",
    "deliberator-opponent",
)


def _probe(agent_type: str) -> dict[str, object]:
    entries = json.loads(PACK.read_text(encoding="utf-8"))[agent_type]
    (probe,) = [e for e in entries if e["name"] == "openai"]
    return dict(probe)


@pytest.mark.parametrize("agent_type", OPENAI_PROBE_AGENTS)
def test_the_openai_probe_spends_rather_than_reading_metadata(agent_type: str) -> None:
    """🎯 The pack asks the question a key that cannot spend is able to fail."""
    probe = _probe(agent_type)

    statuses = probe["credential_failure_statuses"]

    assert probe["method"] == "POST"
    assert probe["url"] == "https://api.openai.com/v1/chat/completions"
    assert isinstance(statuses, list)
    assert 429 in statuses


@pytest.mark.parametrize("agent_type", OPENAI_PROBE_AGENTS)
def test_the_openai_probe_model_tracks_the_adapter_default(agent_type: str) -> None:
    """🪤 A model name the adapter no longer uses returns 404 and blames the key."""
    from agents.deliberator.llm_factory import DEFAULT_MODEL

    body = _probe(agent_type)["json_body"]

    assert isinstance(body, dict)
    assert body["model"] == DEFAULT_MODEL["openai"]


@pytest.mark.parametrize("agent_type", OPENAI_PROBE_AGENTS)
def test_the_openai_probe_budget_survives_a_reasoning_model(agent_type: str) -> None:
    """🪤 Measured: `max_completion_tokens: 1` returns 400 for a *valid* key.

    A truncation 400 is indistinguishable from a dead key, so the budget must sit
    clear of the 38 completion tokens the worst of five live runs consumed. The
    parameter name is pinned too: `max_tokens` is rejected outright by this model.
    """
    body = _probe(agent_type)["json_body"]

    assert isinstance(body, dict)
    assert "max_tokens" not in body
    assert int(body["max_completion_tokens"]) >= 128


def test_the_openai_probe_is_required() -> None:
    """S217 / MST-NEV-06: every declared OpenAI probe is fleet-required."""
    assert [_probe(a)["required"] for a in OPENAI_PROBE_AGENTS] == [True] * 3


def test_an_unlisted_4xx_still_fails_the_probe() -> None:
    """🪤 `credential_failure_statuses` is a record, not a filter — measured here.

    Found while editing the pack for item 53: the runner's two 4xx branches were
    identical, so the field has never widened or narrowed anything. Any
    non-expected status below 500 fails closed whether it is listed or not. The
    behaviour is right; the field reading like a control was not. Pinned so a
    future reader trusts the code over the JSON.
    """
    from agents.master.credential_probes import parse_credential_tests

    declaration = json.dumps(
        {
            "provider": [
                {
                    "name": "narrow",
                    "kind": "http_status",
                    "method": "GET",
                    "url": "https://example.invalid/x",
                    "expected_statuses": [200],
                    "credential_failure_statuses": [401],
                    "required": True,
                    "cost": "cheap",
                }
            ]
        }
    )
    (test,) = parse_credential_tests(declaration, http_transport=lambda _r: 418)
    result = test.run({})

    assert not isinstance(result, bool)
    assert result.status == "credential_failure"
    assert result.reason == "unexpected:http_418"
