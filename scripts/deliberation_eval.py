"""Manufactured-eval runner for the deliberation — grounded vs blind on known flaws.

Agent: tooling
Role: run the deliberation eval (DL-23 Path B) over adversarial trading decisions
      whose right answer we know, and report the pass-rate. Two libraries: CLASS-2
      (textbook flaws a capable model knows blind — EXP-003) and CLASS-1 (flaws only
      OUR implementation reveals — EXP-004). Two scorers per run: keyword + LLM-judge.
      The 2x2 (blind|grounded x keyword|judge) shows whether grounding pays off where
      it should — on Class-1. The trading cases live here (pack), not in the kernel.
External I/O: stdout; the LLM via deliberate (--real); a deterministic fake otherwise.

Run it:
  PYTHONPATH=. python scripts/deliberation_eval.py            # Class-2, fake
  PYTHONPATH=. python scripts/deliberation_eval.py --class1 --real
"""

from __future__ import annotations

import argparse
import sys

from scripts.deliberate import build_role_llms

from kernel import (
    EvalCase,
    EvalScore,
    LLMJudgeScorer,
    Proposition,
    pass_rate,
    run_debates,
    score_debate,
)

# Each case: (name, decision, BLIND context, GROUNDING facts, flaw statement, keywords).
# GROUNDING reveals the flaw; BLIND is the bare decision + its raw signal.

# CLASS-2 — textbook flaws a finance-literate model catches without our facts (EXP-003).
_CLASS2 = (
    (
        "concentration",
        "Buy NVDA at market",
        "12-month momentum +0.7; RSI 60.",
        "Portfolio already holds INTC, AMD, CSCO, QCOM (all semis).",
        "adding another semiconductor concentrates the book in one correlated sector",
        ("correlation", "concentration", "crowded", "sector", "semis", "semiconductor"),
    ),
    (
        "event-risk",
        "Buy AAPL at market",
        "momentum +0.5; RSI 58; stop -3%.",
        "Earnings are in 2 days and the -3% stop is not earnings-gap-aware.",
        "an earnings gap can blow through the -3% stop overnight",
        ("earnings", "gap", "event"),
    ),
)

# CLASS-1 — flaws that need OUR implementation; a world-knowledge-only model cannot
# derive them. Each grounding fact cites where it lives (EXP-004).
_CLASS1 = (
    (
        "pooled-sigma",
        "ABC spiked +9% but the data-quality gate passed it — trade the print.",
        "ABC printed a +9% day; the batch validated clean.",
        "The gate's max_daily_move_sigma is POOLED cross-sectional over the whole "
        "batch, not per name (validate-once, 0.28.01); one 9% name does not trip it.",
        "the single-name 9% move cannot trip the data gate because the sigma is "
        "pooled cross-sectional, not per-name — the outlier passes unflagged",
        ("pooled", "cross-sectional", "per-name", "per name", "sigma"),
    ),
    (
        "calendar-staleness",
        "Friday's signal is still fresh on Tuesday after the long weekend — trade it.",
        "the signal is 2 calendar days old.",
        "Our staleness gate counts CALENDAR days, not trading sessions (DL-10); over "
        "a long weekend a 'fresh' signal can be several sessions stale.",
        "the staleness gate counts calendar days not trading sessions, so the "
        "long-weekend gap leaves it stale in session terms while it reads fresh",
        ("calendar", "session", "trading day", "trading-day", "stale"),
    ),
    (
        "name-correlation",
        "Four semis each pass the sector cap individually, so add a fifth.",
        "each position sits within the per-sector limit.",
        "The portfolio cap is a GICS-SECTOR cap with NO name-correlation / "
        "sub-industry penalty (quant-methods Part 2/3); correlated semis satisfy it.",
        "the sector cap has no name-correlation penalty, so a basket of correlated "
        "semiconductors passes while carrying concentrated single-factor risk",
        ("name-correlation", "name correlation", "sub-industry", "single-factor"),
    ),
    (
        "fixed-fraction-size",
        "Size this 2.5-beta name the same as a utility — the rule is uniform.",
        "position size = a fixed fraction of equity.",
        "Sizing is FIXED-FRACTION, not vol-adjusted or Kelly (quant-methods); a "
        "2.5-beta name gets the same dollar size as a 0.5-beta name.",
        "fixed-fraction sizing is not vol-adjusted, so a high-beta name carries far "
        "more risk per position than a low-beta one at the same dollar size",
        ("fixed-fraction", "vol-adjust", "volatility-adjust", "kelly", "beta"),
    ),
    (
        "alpha158-weight-zero",
        "Alpha158 is enabled, so trust its contribution to the score.",
        "Alpha158 is part of the scoring stack.",
        "The Alpha158 pillar ships with WEIGHT = 0.00 (off by default, S68/Q2); it "
        "contributes nothing to the composite despite being 'enabled'.",
        "the Alpha158 weight is 0.00, so although enabled it contributes nothing to "
        "the score — relying on it is relying on a disabled signal",
        ("weight", "0.00", "zero", "disabled", "off"),
    ),
    (
        "lightgbm-shadow",
        "The LightGBM model agrees, so let it confirm the trade.",
        "the ML model's prediction aligns with the signal.",
        "The LightGBM price/return model runs in SHADOW mode (Q1) — logged for IC "
        "only; it does NOT feed the live decision.",
        "the LightGBM model is a shadow signal logged for IC only and does not feed "
        "the live decision, so 'it agrees' adds no real confirmation",
        ("shadow", "does not feed", "ic ", "advisory", "logged"),
    ),
)


def _build(
    cases: tuple[tuple[object, ...], ...], *, grounded: bool
) -> tuple[EvalCase, ...]:
    out = []
    for name, decision, blind, ground, flaw, keywords in cases:
        context = str(blind) + (" " + str(ground) if grounded else "")
        out.append(
            EvalCase(
                str(name),
                Proposition(str(decision), context),
                flaw_keywords=tuple(keywords),  # type: ignore[arg-type]
                flaw=str(flaw),
            )
        )
    return tuple(out)


def _row(label: str, kw: tuple[EvalScore, ...], lj: tuple[EvalScore, ...]) -> None:
    print(f"  {label:<10} keyword {pass_rate(kw):>4.0%}   judge {pass_rate(lj):>4.0%}")


def _disagreements(kw: tuple[EvalScore, ...], lj: tuple[EvalScore, ...]) -> None:
    print("\n  per-case flaw_caught (grounded) — keyword vs judge:")
    for k, j in zip(kw, lj, strict=True):
        differ = "  <-- differ" if k.flaw_caught != j.flaw_caught else ""
        print(
            f"    {k.name:<22} keyword={k.flaw_caught!s:<5} "
            f"judge={j.flaw_caught!s:<5}{differ}"
        )


def main() -> None:
    """Run blind vs grounded under both scorers and print the 2x2 + the deltas."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description="deliberation manufactured-eval")
    parser.add_argument("--real", action="store_true", help="call the model (.env)")
    parser.add_argument("--class1", action="store_true", help="use the Class-1 set")
    parser.add_argument("--rounds", type=int, default=1)
    args = parser.parse_args()

    library = _CLASS1 if args.class1 else _CLASS2
    label = "CLASS-1" if args.class1 else "CLASS-2"
    debate_llm, debate_judge_llm = build_role_llms(args.real)
    scorer = LLMJudgeScorer(debate_llm)

    def score(grounded: bool) -> tuple[tuple[EvalScore, ...], tuple[EvalScore, ...]]:
        cases = _build(library, grounded=grounded)
        debates = run_debates(
            debate_llm,
            cases,
            max_rounds=args.rounds,
            judge_llm=debate_judge_llm,
        )
        kw = tuple(score_debate(d, c) for d, c in zip(debates, cases, strict=True))
        lj = tuple(scorer(d, c) for d, c in zip(debates, cases, strict=True))
        return kw, lj

    bk, bj = score(grounded=False)
    gk, gj = score(grounded=True)

    print(f"\n{label} — pass-rate (blind|grounded x keyword|judge):")
    _row("BLIND", bk, bj)
    _row("GROUNDED", gk, gj)
    print(
        f"\n  DELTA grounded-blind:  keyword {pass_rate(gk) - pass_rate(bk):+.0%}"
        f"   judge {pass_rate(gj) - pass_rate(bj):+.0%}"
    )
    _disagreements(gk, gj)


if __name__ == "__main__":
    main()
