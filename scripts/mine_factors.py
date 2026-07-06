"""Mine one governed factor proposal from a bounded researcher catalogue.

Agent: tooling
Role: compose Tiingo CSV bars, an LLM/manual selector, and researcher evidence.
External I/O: filesystem (reads CSV, writes JSON); LLM provider API with --real.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Protocol
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.deliberate import _provider_llm
from scripts.mine_factors_prompt import (
    params_object,
    selection_from_text,
    selection_prompt,
    tool_schema,
)
from scripts.price_csv import load_price_csv

from agents.researcher.domain.backtest import run_walkforward, to_evidence
from agents.researcher.domain.factor_proposal import build_factor_proposal
from agents.researcher.domain.factors import (
    Bars,
    FactorSelection,
    score,
    validate_selection,
)
from agents.researcher.settings import ResearcherSettings
from contracts.common import Provenance
from contracts.researcher import FactorProposal

_SELECTOR_MAX_TOKENS = 2000
_SYSTEM_PROMPT = (
    "You are a governed factor selector. Choose exactly one factor from the "
    "catalogue. Do not invent factors or parameters. Return JSON only."
)


class _SelectorClient(Protocol):
    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str: ...


class _DemoSelector:
    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, user, tool_schema
        return json.dumps(
            {
                "name": "momentum",
                "params": {"lookback": 20},
                "rationale": "Momentum is the default offline catalogue smoke test.",
            }
        )


def close_series(bars: Bars) -> dict[str, list[tuple[str, float]]]:
    """Drop volume for the pure S112 walk-forward harness."""
    return {
        ticker: [(bar_date, close) for bar_date, close, _ in rows]
        for ticker, rows in bars.items()
    }


def run(args: argparse.Namespace) -> int:
    """Build one factor proposal, or fail open with no output."""
    bars = load_price_csv(args.input)
    selection = (
        _manual_selection(args)
        if _has_manual_selection(args)
        else _llm_selection(_selector_client(args.real), bars)
    )
    if selection is None:
        print("off-catalogue selection - no proposal generated")
        return 0
    result = run_walkforward(
        score(selection, bars),
        close_series(bars),
        top_k=args.top_k,
        slippage_bps=args.slippage_bps,
        holdout_fraction=args.holdout_fraction,
    )
    try:
        evidence = to_evidence(result, slippage_bps=args.slippage_bps)
    except ValueError:
        print("backtest evidence unavailable - no proposal generated")
        return 0
    proposal_id = args.proposal_id or f"factor-{selection.name}-{uuid4().hex[:12]}"
    proposal = build_factor_proposal(
        selection,
        evidence,
        Provenance(run_id=proposal_id, source_agent="researcher"),
        proposal_id,
    )
    out = Path(args.out)
    out.write_text(
        json.dumps(proposal.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    round_trip = FactorProposal.model_validate(
        json.loads(out.read_text(encoding="utf-8"))
    )
    print(
        f"proposal_id={round_trip.proposal_id} "
        f"factor={round_trip.factor.name} n_days={round_trip.backtest.n_days}"
    )
    return 0


def build_parser(settings: ResearcherSettings | None = None) -> argparse.ArgumentParser:
    """Build the CLI parser."""
    defaults = settings or ResearcherSettings()
    parser = argparse.ArgumentParser(description="Mine one governed factor proposal.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--real", action="store_true", help="call the .env LLM")
    parser.add_argument("--factor", default="")
    parser.add_argument("--params", default="{}")
    parser.add_argument("--rationale", default="Manual bounded catalogue selection.")
    parser.add_argument("--selection-json", default="")
    parser.add_argument("--proposal-id", default="")
    parser.add_argument("--top-k", type=int, default=defaults.backtest_top_k)
    parser.add_argument(
        "--slippage-bps", type=float, default=defaults.backtest_slippage_bps
    )
    parser.add_argument(
        "--holdout-fraction",
        type=float,
        default=defaults.backtest_holdout_fraction,
    )
    return parser


def _llm_selection(llm: _SelectorClient, bars: Bars) -> FactorSelection | None:
    del bars
    return selection_from_text(
        llm.complete(
            system=_SYSTEM_PROMPT,
            user=selection_prompt(),
            tool_schema=tool_schema(),
        )
    )


def _selector_client(real: bool) -> _SelectorClient:
    if not real:
        return _DemoSelector()
    from dotenv import load_dotenv

    load_dotenv()
    provider = os.environ.get("LLM_PROVIDER", "openai").strip().lower()
    model = (
        os.environ.get("OPENAI_MODEL", "gpt-5.5")
        if provider == "openai"
        else os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    )
    print(f"MODE: real factor selector ({provider} {model})")
    return _provider_llm(provider, model, max_tokens=_SELECTOR_MAX_TOKENS)


def _manual_selection(args: argparse.Namespace) -> FactorSelection | None:
    if args.selection_json:
        return selection_from_text(args.selection_json)
    params = params_object(args.params)
    return (
        validate_selection(args.factor, params, rationale=args.rationale)
        if params
        else None
    )


def _has_manual_selection(args: argparse.Namespace) -> bool:
    return bool(args.factor or args.selection_json)


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    """CLI entry point."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    parser = build_parser()
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
