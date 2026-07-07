"""Remediation selector regression gate.

Agent: tooling
Role: freeze/check the bounded remediation selector against the trading golden set.
External I/O: stdout; optional LLM provider when --real is supplied.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.master.remediation_gate import RemediationSelectionScore
    from kernel import FakeLLMClient

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_PACK = _ROOT / "orchestration" / "packs"
_CASES = _PACK / "trading_remediation_selection_cases.json"
_CATALOGUE = _PACK / "trading_remediations.json"
_PROMPT = _PACK / "trading_remediation_prompt.json"
_GOLDEN = Path(__file__).with_name("remediation_selector_golden.json")


class _AnthropicStructured:
    """Structured-ish Anthropic adapter for live selector probes."""

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
            max_tokens=1000,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(getattr(block, "text", "") for block in resp.content)


class _OpenAIStructured:
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


def _fake() -> FakeLLMClient:
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


def _build_real_llm() -> _OpenAIStructured | _AnthropicStructured:
    from dotenv import load_dotenv

    load_dotenv()
    provider = os.environ.get("LLM_PROVIDER", "openai").strip().lower()
    if provider == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise SystemExit("ANTHROPIC_API_KEY not set - cannot run --real")
        model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        print(f"MODE: real (Anthropic {model})")
        return _AnthropicStructured(key, model)
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise SystemExit("OPENAI_API_KEY not set - cannot run --real")
    model = os.environ.get("OPENAI_MODEL", "gpt-5.5")
    print(f"MODE: real (OpenAI {model})")
    return _OpenAIStructured(key, model)


def _score(real: bool) -> tuple[RemediationSelectionScore, ...]:
    from agents.master.remediation import load_remediations
    from agents.master.remediation_gate import (
        load_prompt_artifact,
        load_selection_cases,
        run_selection_eval,
    )

    llm = _build_real_llm() if real else _fake()
    cases = load_selection_cases(str(_CASES))
    catalogue = load_remediations(str(_CATALOGUE))
    artifact = load_prompt_artifact(str(_PROMPT))
    return run_selection_eval(
        llm, cases, catalogue, system_prompt=artifact.system_prompt
    )


def _freeze(real: bool) -> None:
    from agents.master.remediation_gate import (
        passing_selection_names,
        selection_pass_rate,
    )

    scores = _score(real)
    model = os.environ.get("OPENAI_MODEL", "fake") if real else "fake"
    passing = sorted(passing_selection_names(scores))
    golden = {
        "model": model,
        "date": datetime.now(tz=UTC).date().isoformat(),
        "library": "trading-remediation-selection",
        "passing": passing,
        "pass_rate": selection_pass_rate(scores),
    }
    _GOLDEN.write_text(json.dumps(golden, indent=2) + "\n", encoding="utf-8")
    print(f"FROZEN remediation selector golden ({model})")
    print(f"  passing ({len(passing)}): {passing}")
    print(f"  pass_rate: {golden['pass_rate']:.2f}")
    print(f"  written: {_GOLDEN.name}")


def _check(real: bool) -> int:
    from agents.master.remediation_gate import (
        check_selection_baseline,
        selection_pass_rate,
    )

    golden = json.loads(_GOLDEN.read_text(encoding="utf-8"))
    scores = _score(real)
    result = check_selection_baseline(
        scores, frozenset(str(name) for name in golden["passing"])
    )
    print("REMEDIATION SELECTOR GATE")
    print(f"  pass_rate: {selection_pass_rate(scores):.2f}")
    print(f"  regressed: {list(result.regressed) or 'none'}")
    print(f"  gained:    {list(result.gained) or 'none'}")
    print(f"  VERDICT: {'PASS' if result.passed else 'FAIL'}")
    return 0 if result.passed else 1


def main() -> None:
    """Freeze or check the remediation selector golden."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="remediation selector gate")
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--real", action="store_true", help="call GPT-5.5 via .env")
    args = parser.parse_args()
    if args.freeze == args.check:
        raise SystemExit("pass exactly one of --freeze or --check")
    if args.freeze:
        _freeze(args.real)
        return
    raise SystemExit(_check(args.real))


if __name__ == "__main__":
    main()
