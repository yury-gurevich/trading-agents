"""Model-swap regression gate — freeze a golden baseline, then check a candidate.

Agent: tooling
Role: operationalise the DL-24 drift firewall (EXP-005). `--freeze` runs the champion
      (OPENAI_MODEL) on the grounded Class-1 library and writes the golden passing set.
      `--check MODEL` runs MODEL as the *debater* while the champion stays the *judge*
      (the fixed measuring instrument), then trips if the candidate regressed on any
      case the golden passed. The trading cases live in deliberation_eval (pack).
External I/O: stdout; the golden JSON file; the LLM via the adapters when --real.

Run it:
  PYTHONPATH=. python scripts/deliberation_gate.py --freeze --real
  PYTHONPATH=. python scripts/deliberation_gate.py --check gpt-5.4 --real
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from scripts.deliberate import _AnthropicText, _build_llm, _OpenAIText
from scripts.deliberation_eval import _CLASS1, _build

from kernel import (
    EvalScore,
    LLMJudgeScorer,
    check_baseline,
    pass_rate,
    passing_names,
    run_debates,
)

_GOLDEN = Path(__file__).with_name("deliberation_golden.json")


def _named_llm(model: str) -> _OpenAIText | _AnthropicText:
    """Build an LLM for a specific model id, on the .env provider."""
    from dotenv import load_dotenv

    load_dotenv()
    provider = os.environ.get("LLM_PROVIDER", "openai").strip().lower()
    if provider == "openai":
        return _OpenAIText(os.environ["OPENAI_API_KEY"], model)
    return _AnthropicText(os.environ["ANTHROPIC_API_KEY"], model)


def _score(debate_llm: object, judge_llm: object, rounds: int) -> tuple[EvalScore, ...]:
    """Debate each grounded Class-1 case with debate_llm; score with the judge_llm."""
    cases = _build(_CLASS1, grounded=True)
    debates = run_debates(debate_llm, cases, max_rounds=rounds)  # type: ignore[arg-type]
    judge = LLMJudgeScorer(judge_llm)  # type: ignore[arg-type]
    return tuple(judge(d, c) for d, c in zip(debates, cases, strict=True))


def _freeze(rounds: int) -> None:
    champ = _build_llm(True)
    scores = _score(champ, champ, rounds)
    model = os.environ.get("OPENAI_MODEL", "unknown")
    golden = {
        "model": model,
        "judge": model,
        "date": datetime.now(tz=UTC).date().isoformat(),
        "library": "class1-grounded",
        "passing": sorted(passing_names(scores)),
        "scores": {
            s.name: {"flaw_caught": s.flaw_caught, "passed": s.passed} for s in scores
        },
    }
    _GOLDEN.write_text(json.dumps(golden, indent=2) + "\n", encoding="utf-8")
    print(f"\nFROZEN golden ({model}) — pass-rate {pass_rate(scores):.0%}")
    print(f"  passing: {golden['passing']}")
    print(f"  written: {_GOLDEN.name}")


def _check(model: str, rounds: int) -> int:
    golden = json.loads(_GOLDEN.read_text(encoding="utf-8"))
    judge = _build_llm(True)  # champion judge — the fixed measuring instrument
    candidate = _named_llm(model)
    scores = _score(candidate, judge, rounds)
    result = check_baseline(scores, frozenset(golden["passing"]))
    print(f"\nGATE — debater {model} vs golden {golden['model']} ({golden['date']})")
    print(
        f"  golden pass-rate {len(golden['passing'])}/{len(golden['scores'])}"
        f"   candidate pass-rate {pass_rate(scores):.0%}"
    )
    print(f"  regressed: {list(result.regressed) or 'none'}")
    print(f"  gained:    {list(result.gained) or 'none'}")
    print(f"  VERDICT: {'PASS' if result.passed else 'FAIL — firewall tripped'}")
    return 0 if result.passed else 1


def main() -> None:
    """Freeze the golden baseline, or check a candidate model against it."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description="deliberation model-swap gate")
    parser.add_argument("--freeze", action="store_true", help="write the golden")
    parser.add_argument("--check", metavar="MODEL", help="check MODEL vs the golden")
    parser.add_argument("--real", action="store_true", help="call the model (.env)")
    parser.add_argument("--rounds", type=int, default=1)
    args = parser.parse_args()

    if not args.real:
        raise SystemExit("the gate needs --real (a live model); there is no fake gate")
    if args.freeze:
        _freeze(args.rounds)
    elif args.check:
        raise SystemExit(_check(args.check, args.rounds))
    else:
        raise SystemExit("pass --freeze or --check MODEL")


if __name__ == "__main__":
    main()
