"""Run an LLM deliberation — Defender vs Challenger, judged — over one decision.

Agent: tooling
Role: drive the kernel deliberation harness so a human can watch three LLM roles
      argue a decision and read the verdict. Default uses a deterministic fake
      (no credentials); --real calls the .env-configured debate and judge models.
External I/O: stdout; OpenAI/Anthropic APIs when --real.

Run it:
  PYTHONPATH=. python scripts/deliberate.py                      # fake, no creds
  uv pip install anthropic openai                                # for --real
  PYTHONPATH=. python scripts/deliberate.py --real \\
      --decision "Buy AAPL at market" --context "momentum 0.6; RSI 55; stop -3%"

--real follows LLM_PROVIDER for Defender/Challenger and DELIBERATION_JUDGE_* for
the debate Judge. This is distinct from the EXP-004 LLMJudgeScorer.
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys

from kernel import (
    Proposition,
    deliberate,
    misread_parameters,
    score_understanding,
    understanding_rate,
)
from orchestration.packs.trading_parameter_truths import TRADING_PARAMETER_TRUTHS

_JUDGE_MAX_TOKENS = 512


class _AnthropicText:
    """Free-text Anthropic adapter (the operator's client is tool-use only)."""

    def __init__(self, api_key: str, model: str, *, max_tokens: int = 2000) -> None:
        anthropic = importlib.import_module("anthropic")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del tool_schema
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
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


def _provider_name(provider: str) -> str:
    return "OpenAI" if provider == "openai" else "Anthropic"


def _base_config() -> tuple[str, str]:
    provider = os.environ.get("LLM_PROVIDER", "anthropic").strip().lower()
    model = (
        os.environ.get("OPENAI_MODEL", "gpt-4o")
        if provider == "openai"
        else os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    )
    return provider, model


def _judge_config() -> tuple[str, str]:
    provider = (
        os.environ.get("DELIBERATION_JUDGE_PROVIDER", "anthropic").strip().lower()
    )
    model = os.environ.get("DELIBERATION_JUDGE_MODEL", "claude-opus-4-8")
    return provider, model


def _provider_llm(
    provider: str, model: str, *, max_tokens: int = 2000
) -> _AnthropicText | _OpenAIText:
    if provider == "openai":
        key = os.environ.get("OPENAI_API_KEY", "")
        if not key:
            raise SystemExit("OPENAI_API_KEY not set — cannot run --real")
        return _OpenAIText(key, model)
    if provider == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise SystemExit("ANTHROPIC_API_KEY not set — cannot run --real")
        return _AnthropicText(key, model, max_tokens=max_tokens)
    raise SystemExit(f"unsupported LLM provider {provider!r}")


def _build_llm(
    real: bool, *, announce: bool = True
) -> _AnthropicText | _OpenAIText | _DemoFake:
    if not real:
        return _DemoFake()
    from dotenv import load_dotenv

    load_dotenv()
    provider, model = _base_config()
    llm = _provider_llm(provider, model)
    if announce:
        print(f"MODE: real  ({_provider_name(provider)} {model})")
    return llm


def build_role_llms(
    real: bool,
) -> tuple[
    _AnthropicText | _OpenAIText | _DemoFake, _AnthropicText | _OpenAIText | _DemoFake
]:
    """Build the debate model and the separate debate Judge model."""
    if not real:
        return _DemoFake(), _DemoFake()
    from dotenv import load_dotenv

    load_dotenv()
    debate_provider, debate_model = _base_config()
    judge_provider, judge_model = _judge_config()
    debate_llm = _provider_llm(debate_provider, debate_model)
    judge_llm = _provider_llm(judge_provider, judge_model, max_tokens=_JUDGE_MAX_TOKENS)
    print(
        "MODE: real  "
        f"(debate {_provider_name(debate_provider)} {debate_model} · "
        f"judge {_provider_name(judge_provider)} {judge_model})"
    )
    return debate_llm, judge_llm


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
    parser.add_argument(
        "--score",
        action="store_true",
        help="grade the debate's parameter definitions vs the answer key (DL-31)",
    )
    args = parser.parse_args()

    debate_llm, judge_llm = build_role_llms(args.real)
    proposition = Proposition(decision=args.decision, context=args.context)
    result = deliberate(
        debate_llm, proposition, max_rounds=args.rounds, judge_llm=judge_llm
    )

    print(f"\nDELIBERATION — {proposition.decision}")
    print(f"context: {proposition.context}")
    print("-" * 60)
    for turn in result.transcript:
        print(f"[{turn.role:<10} r{turn.round}]  {turn.text}")
    print("-" * 60)
    print(f"VERDICT: {result.verdict.ruling.upper()} — {result.verdict.rationale}")

    if args.score:
        transcript_text = " ".join(t.text for t in result.transcript)
        scores = score_understanding(transcript_text, TRADING_PARAMETER_TRUTHS)
        print("\nUNDERSTANDING (define-then-justify, DL-31)")
        for s in scores:
            if not s.cited:
                continue
            mark = "MISREAD" if s.misread else ("ok" if s.understood else "vague")
            print(f"  [{mark:<7}] {s.name}")
        rate = understanding_rate(scores)
        misread = misread_parameters(scores)
        print(f"  understanding score (of cited): {rate:.0%}")
        if misread:
            print(f"  KNOWN MISREADS: {', '.join(misread)}")


if __name__ == "__main__":
    main()
