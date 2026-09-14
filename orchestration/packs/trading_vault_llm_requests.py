"""Billable LLM probe requests for vault seeding.

Agent: orchestration
Role: build the smallest request that proves an LLM key may *spend*, not merely
      that it exists.
External I/O: none here; the caller performs the HTTPS request.

🚨 Both vendors answer free metadata endpoints for a key that can no longer
spend. Measured: Anthropic returns 200 on `GET /v1/models` while every message
fails `400 … credit balance is too low` (S202, four nights to 2026-09-13);
OpenAI returns 200 on `GET /v1/models` while billable calls fail
`429 … no credits remaining` ([DL-125], 2026-08-19). A probe against metadata
cannot fail for the reason it exists to catch.
"""

from __future__ import annotations

import json
import urllib.request
from typing import TYPE_CHECKING

from agents.deliberator.llm_factory import DEFAULT_MODEL
from orchestration.packs.trading_vault_probe_support import required

if TYPE_CHECKING:
    from collections.abc import Mapping

_ONE_TOKEN_PROMPT = [{"role": "user", "content": "."}]
_JSON = "application/json"

# 🪤 `gpt-5.5` is a reasoning model: measured 2026-09-14, a budget of 1 returns
# **400 for a valid key** because reasoning consumes it before any content is
# emitted. Five runs at 256 used 26-38 completion tokens, and an unreached cap is
# charged nothing — so a generous budget is safer at identical cost.
_OPENAI_MAX_COMPLETION_TOKENS = 256


def openai_spend_request(env: Mapping[str, str]) -> urllib.request.Request:
    """Return a minimal billable OpenAI chat completion request."""
    return _post(
        "https://api.openai.com/v1/chat/completions",
        {
            "model": DEFAULT_MODEL["openai"],
            "max_completion_tokens": _OPENAI_MAX_COMPLETION_TOKENS,
            "messages": _ONE_TOKEN_PROMPT,
        },
        {"Authorization": f"Bearer {required(env, 'OPENAI_API_KEY')}"},
    )


def anthropic_spend_request(env: Mapping[str, str]) -> urllib.request.Request:
    """Return a minimal billable Anthropic message request."""
    return _post(
        "https://api.anthropic.com/v1/messages",
        {
            "model": DEFAULT_MODEL["anthropic"],
            "max_tokens": 1,
            "messages": _ONE_TOKEN_PROMPT,
        },
        {
            "anthropic-version": "2023-06-01",
            "x-api-key": required(env, "ANTHROPIC_API_KEY"),
        },
    )


def _post(
    url: str, body: dict[str, object], headers: Mapping[str, str]
) -> urllib.request.Request:
    return urllib.request.Request(  # noqa: S310
        url,
        data=json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8"),
        headers={**headers, "content-type": _JSON},
        method="POST",
    )
