"""Before any paid call: prove the provider accepts us and serves the model, however the key arrives.

The key can reach a request two ways: as a variable in this process (`ANTHROPIC_API_KEY`), or added by the
environment (claude.ai "API credentials", which a session never sees). A check for the variable alone
would refuse the second, so the proof is one free call that lists the provider's models. It is made with
the variable when it is set, else with a placeholder the environment may replace. The run is refused,
before any paid call, unless that call returns 200 AND the model is listed.

`ProviderAbort` is how a provider failure leaves a compile. It is a BaseException, so GEPA, which scores
any Exception as a failed answer, cannot learn from an outage.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

PLACEHOLDER = "provided-by-environment"
_PROVIDERS = {
    # provider -> (key variable, models endpoint, auth header builder)
    "anthropic": (
        "ANTHROPIC_API_KEY",
        "https://api.anthropic.com/v1/models?limit=1000",
        lambda k: {"x-api-key": k, "anthropic-version": "2023-06-01"},
    ),
    "openai": (
        "OPENAI_API_KEY",
        "https://api.openai.com/v1/models",
        lambda k: {"Authorization": f"Bearer {k}"},
    ),
}
_PROVEN: dict[str, str] = {}  # model -> the api_key value to pass (the variable's, or the placeholder)


class ProviderAbort(BaseException):
    """A provider call failed during a compile: stop, never score it."""


def prove(model: str) -> str | None:
    """Return the api_key value dspy.LM must carry for `model`; raise SystemExit (no paid call made) if refused."""
    provider, _, name = model.partition("/")
    if provider not in _PROVIDERS:
        return None
    if model in _PROVEN:
        return _PROVEN[model]
    var, url, headers = _PROVIDERS[provider]
    key = os.environ.get(var) or PLACEHOLDER
    how = (
        f"the {var} variable" if key != PLACEHOLDER else "the environment's API credentials (no variable set)"
    )
    req = urllib.request.Request(url, headers=headers(key))
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            listed = {m.get("id") for m in json.load(r).get("data", [])}
    except urllib.error.HTTPError as e:
        raise SystemExit(
            f"REFUSED: {provider} answered {e.code} to a free models call using {how}; no paid call was made. "
            f"Add the key as {var} under the environment's Environment variables, or check the API credential."
        ) from None
    except OSError as e:
        raise SystemExit(f"REFUSED: could not reach {url} ({e}); no paid call was made.") from None
    if name not in listed:
        near = sorted(i for i in listed if i and i.split("-")[0] == name.split("-")[0])[:12]
        raise SystemExit(f"REFUSED: {provider} accepted the key but does not list `{name}`. Listed: {near}")
    _PROVEN[model] = key
    return key
