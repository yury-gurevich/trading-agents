"""A vault LLM probe must spend, or it proves only that the key is well-formed.

Agent: orchestration
Role: pin the two LLM vault probes to billable endpoints and to the adapter's
      own model names.
External I/O: none; no request is sent.

Item 53b. These two probes gate no scheduled run — only `seed_key_vault.py` and
`seed_key_vault_live_check.py` call them — which is why they were left behind
when S202 fixed the pack. A known-blind probe left undocumented is how item 50
survived nine nights, so they are corrected here rather than filed again.
"""

from __future__ import annotations

import json

import pytest

from kernel.llm_factory import DEFAULT_MODEL
from orchestration.packs import trading_vault_probes as probes
from orchestration.packs.trading_vault_llm_requests import (
    anthropic_spend_request,
    openai_spend_request,
)

ENV = {
    "OPENAI_API_KEY": "openai-key",  # pragma: allowlist secret
    "ANTHROPIC_API_KEY": "anthropic-key",  # pragma: allowlist secret
}


def test_the_openai_vault_probe_posts_a_billable_completion() -> None:
    """🎯 `GET /v1/models` answers 200 for a key that cannot spend a cent."""
    request = openai_spend_request(ENV)

    assert request.method == "POST"
    assert request.full_url == "https://api.openai.com/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer openai-key"


def test_the_anthropic_vault_probe_posts_a_billable_message() -> None:
    """🎯 The same correction S202 made to the pack, in the second place."""
    request = anthropic_spend_request(ENV)

    assert request.method == "POST"
    assert request.full_url == "https://api.anthropic.com/v1/messages"
    assert request.headers["X-api-key"] == "anthropic-key"
    assert request.headers["Anthropic-version"] == "2023-06-01"


@pytest.mark.parametrize(
    ("build", "provider"),
    [(openai_spend_request, "openai"), (anthropic_spend_request, "anthropic")],
)
def test_a_spend_probe_names_the_model_the_adapter_resolves(
    build: object, provider: str
) -> None:
    """🪤 A retired model name returns 404, and the runner blames the key for it."""
    body = json.loads(build(ENV).data)  # type: ignore[operator]

    assert body["model"] == DEFAULT_MODEL[provider]
    assert body["messages"] == [{"role": "user", "content": "."}]


def test_the_openai_budget_clears_a_reasoning_model_preamble() -> None:
    """🪤 Measured 2026-09-14: a budget of 1 returns 400 for a *valid* key."""
    body = json.loads(openai_spend_request(ENV).data)  # type: ignore[arg-type]

    assert "max_tokens" not in body
    assert body["max_completion_tokens"] >= 128


def test_a_spend_probe_declares_its_json_content_type() -> None:
    """A body the server cannot parse returns the same 4xx as a dead key."""
    assert openai_spend_request(ENV).headers["Content-type"] == "application/json"
    assert anthropic_spend_request(ENV).headers["Content-type"] == "application/json"


@pytest.mark.parametrize(
    ("build", "missing"),
    [
        (openai_spend_request, "OPENAI_API_KEY"),
        (anthropic_spend_request, "ANTHROPIC_API_KEY"),
    ],
)
def test_a_missing_key_is_a_failed_probe_not_an_anonymous_call(
    build: object, missing: str
) -> None:
    """Fail closed: an absent key never becomes an unauthenticated request."""
    env = {k: v for k, v in ENV.items() if k != missing}

    with pytest.raises(ValueError, match=missing):
        build(env)  # type: ignore[operator]


def test_the_registered_probes_use_the_billable_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The registry entries are the corrected probes, not their free ancestors."""
    seen: list[str] = []

    def fake_http_json(request: object) -> object:
        seen.append(str(getattr(request, "full_url", "")))
        return {"ok": True}

    monkeypatch.setattr(probes, "http_json", fake_http_json)

    assert probes.PROBES["openai"](ENV).ok is True
    assert probes.PROBES["anthropic"](ENV).ok is True
    assert seen == [
        "https://api.openai.com/v1/chat/completions",
        "https://api.anthropic.com/v1/messages",
    ]
