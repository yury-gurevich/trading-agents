"""Manufactured-eval runner for the deliberation — grounded vs blind on known flaws.

Agent: tooling
Role: run the deliberation eval (DL-23 Path B) over a library of adversarial trading
      decisions whose right answer we know, and report the pass-rate — comparing
      BLIND vs GROUNDED context to show grounding raises debate quality (EXP-002) as a
      repeatable number. The trading cases live here (pack), not in the kernel harness.
External I/O: stdout; the LLM via deliberate (--real); a deterministic fake otherwise.

Run it:
  PYTHONPATH=. python scripts/deliberation_eval.py            # fake, no creds
  PYTHONPATH=. python scripts/deliberation_eval.py --real     # live model (.env)
"""

from __future__ import annotations

import argparse
import sys

from scripts.deliberate import _build_llm

from kernel import EvalCase, EvalScore, Proposition, pass_rate, run_eval

# Each case: (name, decision, BLIND context, GROUNDING facts, flaw keywords). The
# grounding holds the system-/portfolio-supplied facts that *reveal* the flaw — blind
# is the bare decision + its own raw signal, so a flaw needing those facts can only be
# caught when grounded (the EXP-002 setup, generalised).
_CASES = (
    (
        "concentration",
        "Buy NVDA at market",
        "12-month momentum +0.7; RSI 60.",
        "Portfolio already holds INTC, AMD, CSCO, QCOM (all semis); the system has a "
        "sector cap but NO name-correlation penalty.",
        ("correlation", "concentration", "crowded", "sector", "semis", "semiconductor"),
    ),
    (
        "event-risk",
        "Buy AAPL at market",
        "momentum +0.5; RSI 58; stop -3%.",
        "Earnings are in 2 days and the -3% stop is not earnings-gap-aware.",
        ("earnings", "gap", "event"),
    ),
    (
        "tight-stop",
        "Buy TSLA at market",
        "momentum +0.4; a fixed -3% stop.",
        "TSLA is high-volatility; sizing is fixed-fraction, not vol-adjusted.",
        ("volatil", "whipsaw", "gap", "high-beta"),
    ),
    (
        "thin-signal",
        "Buy MSFT at market",
        "the only signal is RSI 52.",
        "There is no other edge and the system has no multi-factor confirmation.",
        ("thin", "noise", "no edge", "weak", "insufficient"),
    ),
)


def _cases(*, grounded: bool) -> tuple[EvalCase, ...]:
    return tuple(
        EvalCase(
            name,
            Proposition(decision, blind + (" " + grounding if grounded else "")),
            flaw_keywords=keywords,
        )
        for name, decision, blind, grounding, keywords in _CASES
    )


def _report(label: str, scores: tuple[EvalScore, ...]) -> None:
    print(f"\n{label}  pass-rate = {pass_rate(scores):.0%}")
    for score in scores:
        flag = "PASS" if score.passed else "fail"
        print(
            f"  [{flag}] {score.name:<14} "
            f"flaw_caught={score.flaw_caught}  verdict_aligned={score.verdict_aligned}"
        )


def main() -> None:
    """Run the eval blind and grounded, and print the delta."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description="deliberation manufactured-eval")
    parser.add_argument(
        "--real", action="store_true", help="call the live model (.env)"
    )
    parser.add_argument("--rounds", type=int, default=1)
    args = parser.parse_args()

    llm = _build_llm(args.real)
    blind = run_eval(llm, _cases(grounded=False), max_rounds=args.rounds)
    grounded = run_eval(llm, _cases(grounded=True), max_rounds=args.rounds)
    _report("BLIND   ", blind)
    _report("GROUNDED", grounded)
    print(
        f"\nDELTA: grounded {pass_rate(grounded):.0%} vs blind {pass_rate(blind):.0%}"
        "  — the training signal DSPy optimises, manufactured today (DL-23)."
    )


if __name__ == "__main__":
    main()
