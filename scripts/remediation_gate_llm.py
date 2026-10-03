"""LLM clients for the remediation selector regression gate.

Agent: tooling
Role: build the selector's LLM for `remediation_gate.py` - the deterministic fake
      that answers every golden case, or a live Anthropic/OpenAI adapter for --real.
External I/O: reads .env and calls an LLM provider, only via build_real_llm.
"""

from __future__ import annotations

import importlib
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import FakeLLMClient


class AnthropicStructured:
    """Structured-ish Anthropic adapter for live selector probes."""

    def __init__(self, api_key: str, model: str) -> None:
        # Local import, kept from before the split: only a live --real run needs
        # `scripts.deliberate`, so --check never imports it.
        from scripts.deliberate import anthropic_effort

        anthropic = importlib.import_module("anthropic")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._effort = anthropic_effort()

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del tool_schema
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=1000,
            output_config={"effort": self._effort},
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(getattr(block, "text", "") for block in resp.content)


class OpenAIStructured:
    """OpenAI adapter that asks the model for JSON matching the tool schema."""

    def __init__(self, api_key: str, model: str) -> None:
        openai = importlib.import_module("openai")
        self._client = openai.OpenAI(api_key=api_key)
        self._model = model

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            max_completion_tokens=1000,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "remediation_selection",
                    "schema": tool_schema,
                    "strict": True,
                },
            },
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""


def fake() -> FakeLLMClient:
    from kernel import FakeLLMClient

    return FakeLLMClient(
        {
            "blank-key-vault-secret": _response("refetch-from-key-vault"),
            "postgres-unreachable": _response("resume-instance"),
            "credential-compromised": _response("rotate-credential"),
            "service-destroyed": _response("recreate-instance"),
            "unknown": _response("pause-and-escalate"),
        }
    )


def _response(remediation: str) -> str:
    return f'{{"remediation": "{remediation}", "rationale": "matched golden"}}'


def build_real_llm() -> OpenAIStructured | AnthropicStructured:
    from dotenv import load_dotenv

    load_dotenv()
    provider = os.environ.get("LLM_PROVIDER", "openai").strip().lower()
    if provider == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise SystemExit("ANTHROPIC_API_KEY not set - cannot run --real")
        model = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5")
        print(f"MODE: real (Anthropic {model})")
        return AnthropicStructured(key, model)
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise SystemExit("OPENAI_API_KEY not set - cannot run --real")
    model = os.environ.get("OPENAI_MODEL", "gpt-5.5")
    print(f"MODE: real (OpenAI {model})")
    return OpenAIStructured(key, model)
