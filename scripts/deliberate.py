"""Run an LLM deliberation — Defender vs Challenger, judged — over one decision.

Agent: tooling
Role: drive the kernel deliberation harness so a human can watch three LLM roles
      argue a decision and read the verdict. Default uses a deterministic fake
      (no credentials); --real calls Anthropic with the .env key.
External I/O: stdout; Anthropic API when --real.

Run it:
  PYTHONPATH=. python scripts/deliberate.py                      # fake, no creds
  uv pip install anthropic openai                                # for --real
  PYTHONPATH=. python scripts/deliberate.py --real \\
      --decision "Buy AAPL at market" --context "momentum 0.6; RSI 55; stop -3%"

--real follows LLM_PROVIDER in .env (openai | anthropic) and that provider's key.
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys

from kernel import Proposition, deliberate


class _AnthropicText:
    """Free-text Anthropic adapter (the operator's client is tool-use only)."""

    def __init__(self, api_key: str, model: str) -> None:
        anthropic = importlib.import_module("anthropic")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del tool_schema
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=2000,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(getattr(block, "text", "") for block in resp.content)


class _OpenAIText:
    """Free-text OpenAI adapter."""

    def __init__(self, api_key: str, model: str) -> None:
        openai = importlib.import_module("openai")
        self._client = openai.OpenAI(api_key=api_key)
        self._model = model

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del tool_schema
        resp = self._client.chat.completions.create(
            model=self._model,
            max_completion_tokens=2000,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""


class _DemoFake:
    """Deterministic stand-in so the demo runs with no credentials."""

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del user, tool_schema
        if "DEFENDER" in system:
            return "Momentum (0.6) and a tight stop bound the risk; entry is justified."
        if "CHALLENGER" in system:
            return "RSI 55 is neutral, not bullish — the edge is thin and may be noise."
        return '{"ruling": "revise", "rationale": "enter at half size; edge is thin"}'


def _build_llm(real: bool) -> _AnthropicText | _OpenAIText | _DemoFake:
    if not real:
        return _DemoFake()
    from dotenv import load_dotenv

    load_dotenv()
    provider = os.environ.get("LLM_PROVIDER", "anthropic").strip().lower()
    if provider == "openai":
        key = os.environ.get("OPENAI_API_KEY", "")
        if not key:
            raise SystemExit("OPENAI_API_KEY not set — cannot run --real")
        model = os.environ.get("OPENAI_MODEL", "gpt-4o")
        print(f"MODE: real  (OpenAI {model})")
        return _OpenAIText(key, model)
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY not set — cannot run --real")
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    print(f"MODE: real  (Anthropic {model})")
    return _AnthropicText(key, model)


def main() -> None:
    """Run one deliberation and print the debate + verdict."""
    # LLM output carries unicode (em-dashes, non-breaking hyphens); Windows stdout
    # defaults to cp1252 and would crash on it. Force UTF-8 for console and file.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description="defend/attack/judge a decision")
    parser.add_argument("--real", action="store_true", help="call Anthropic (.env key)")
    parser.add_argument("--decision", default="Buy AAPL at market")
    parser.add_argument("--context", default="momentum 0.6; RSI 55; stop -3%")
    parser.add_argument("--rounds", type=int, default=2)
    args = parser.parse_args()

    llm = _build_llm(args.real)
    proposition = Proposition(decision=args.decision, context=args.context)
    result = deliberate(llm, proposition, max_rounds=args.rounds)

    print(f"\nDELIBERATION — {proposition.decision}")
    print(f"context: {proposition.context}")
    print("-" * 60)
    for turn in result.transcript:
        print(f"[{turn.role:<10} r{turn.round}]  {turn.text}")
    print("-" * 60)
    print(f"VERDICT: {result.verdict.ruling.upper()} — {result.verdict.rationale}")


if __name__ == "__main__":
    main()
