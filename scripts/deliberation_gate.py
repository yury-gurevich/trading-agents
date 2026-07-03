"""Model-swap regression gate — freeze a golden baseline, then check a candidate.

Agent: tooling
Role: operationalise the DL-24 drift firewall (EXP-005). `--freeze` runs the champion
      debate config on the grounded Class-1 library and writes the golden passing set.
      `--check MODEL` varies MODEL as the *debater* only. There are two judges here:
      the debate Judge inside deliberate() (S109, Opus by default) and the EXP-004
      LLMJudgeScorer, which stays the fixed champion measuring instrument.
      The trading cases live in deliberation_eval (pack).
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

from scripts.deliberate import (
    _AnthropicText,
    _base_config,
    _judge_config,
    _OpenAIText,
    build_role_llms,
)
from scripts.deliberation_eval import _CLASS1, _build

from kernel import (
    EvalScore,
    LLMJudgeScorer,
    check_robust,
    pass_fractions,
    robust_passing,
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


def _score(
    debate_llm: object,
    debate_judge_llm: object,
    scorer_judge_llm: object,
    rounds: int,
) -> tuple[EvalScore, ...]:
    """Debate with a role Judge; score with the separate EXP-004 scorer Judge."""
    cases = _build(_CLASS1, grounded=True)
    debates = run_debates(  # type: ignore[arg-type]
        debate_llm, cases, max_rounds=rounds, judge_llm=debate_judge_llm
    )
    judge = LLMJudgeScorer(scorer_judge_llm)  # type: ignore[arg-type]
    return tuple(judge(d, c) for d, c in zip(debates, cases, strict=True))


def _runs(
    debate_llm: object,
    debate_judge_llm: object,
    scorer_judge_llm: object,
    rounds: int,
    n: int,
) -> tuple[tuple[EvalScore, ...], ...]:
    """Score the library ``n`` times — the noise-averaging pass (EXP-006)."""
    return tuple(
        _score(debate_llm, debate_judge_llm, scorer_judge_llm, rounds) for _ in range(n)
    )


def _fractions(runs: tuple[tuple[EvalScore, ...], ...]) -> dict[str, float]:
    return {name: round(frac, 3) for name, frac in pass_fractions(runs).items()}


def _freeze(rounds: int, n: int, threshold: float) -> None:
    champ, debate_judge = build_role_llms(True)
    runs = _runs(champ, debate_judge, champ, rounds, n)
    debate_provider, model = _base_config()
    judge_provider, judge_model = _judge_config()
    passing = sorted(robust_passing(runs, threshold=threshold))
    golden = {
        "model": model,
        "model_provider": debate_provider,
        "judge": judge_model,
        "judge_provider": judge_provider,
        "scorer_judge": model,
        "date": datetime.now(tz=UTC).date().isoformat(),
        "library": "class1-grounded",
        "n_runs": n,
        "threshold": threshold,
        "passing": passing,
        "fractions": _fractions(runs),
    }
    _GOLDEN.write_text(json.dumps(golden, indent=2) + "\n", encoding="utf-8")
    print(
        f"\nFROZEN golden (debate {model}; judge {judge_model}) — "
        f"n={n} threshold={threshold}"
    )
    print(f"  robust passing ({len(passing)}): {passing}")
    print(f"  fractions: {golden['fractions']}")
    print(f"  written: {_GOLDEN.name}")


def _check(model: str, rounds: int, n: int, threshold: float) -> int:
    golden = json.loads(_GOLDEN.read_text(encoding="utf-8"))
    scorer_judge, debate_judge = build_role_llms(True)
    candidate = _named_llm(model)
    runs = _runs(candidate, debate_judge, scorer_judge, rounds, n)
    result = check_robust(runs, frozenset(golden["passing"]), threshold=threshold)
    print(
        f"\nGATE — {model} (n={n}) vs golden {golden['model']} "
        f"+ judge {golden.get('judge', golden['model'])} ({golden['date']})"
    )
    print(f"  golden robust passing ({len(golden['passing'])}): {golden['passing']}")
    print(f"  candidate fractions: {_fractions(runs)}")
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
    parser.add_argument("--runs", type=int, default=1, help="N runs to average (noise)")
    parser.add_argument(
        "--threshold", type=float, default=0.5, help="robust-pass fraction of N"
    )
    args = parser.parse_args()

    if not args.real:
        raise SystemExit("the gate needs --real (a live model); there is no fake gate")
    if args.freeze:
        _freeze(args.rounds, args.runs, args.threshold)
    elif args.check:
        raise SystemExit(_check(args.check, args.rounds, args.runs, args.threshold))
    else:
        raise SystemExit("pass --freeze or --check MODEL")


if __name__ == "__main__":
    main()
