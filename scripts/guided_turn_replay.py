"""The guided turn's live check: defender r1 and challenger r1 on recorded packets.

Agent: tooling
Role: rebuild recorded propositions through `orchestration/replay_corpus.py`, run
      the guided defender r1 and challenger r1 for each, and print per turn:
      parse ok or the error, readings, latency, output tokens and stop reason.
External I/O: graph reads and real LLM calls when run as a CLI (the planner's
      S246 live check, with `.env`); writes nothing to the graph.

Run it (≈ 2 calls per proposition; state the budget first):
  PYTHONPATH=. uv run python scripts/guided_turn_replay.py --limit 10
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from agents.deliberator.guided_turn import guided_turn
from contracts.deliberator import DebateProposition, DebateTurnRecord, DebateTurnRequest
from kernel.llm import llm_stop_reason
from kernel.llm_tokens import llm_usage
from orchestration.replay_corpus import build_corpus

if TYPE_CHECKING:
    from collections.abc import Mapping

    from contracts.deliberator import DebateRole
    from kernel import GraphStore
    from kernel.llm import LLMClient
    from orchestration.replay_types import ReplaySubject


@dataclass(frozen=True)
class TurnReport:
    """One guided turn as the live check reads it."""

    subject: str
    role: str
    parse: str
    readings: int
    latency_s: float
    tokens_out: int | None
    stop_reason: str

    def line(self) -> str:
        """Render one tab-separated line, the error last."""
        tokens = "?" if self.tokens_out is None else str(self.tokens_out)
        return (
            f"{self.subject}\t{self.role}\treadings={self.readings}\t"
            f"latency_s={self.latency_s:.1f}\ttokens_out={tokens}\t"
            f"stop={self.stop_reason}\tparse={self.parse}"
        )


def latest_subjects(graph: GraphStore, limit: int) -> tuple[ReplaySubject, ...]:
    """Return the `limit` most recent propositions (PMRun keys sort by date)."""
    subjects = sorted(
        build_corpus(graph).subjects, key=lambda item: (item.pm_run, item.ticker)
    )
    return tuple(subjects[-limit:]) if limit > 0 else ()


def replay(
    llms: Mapping[DebateRole, LLMClient], subjects: tuple[ReplaySubject, ...]
) -> list[TurnReport]:
    """Run defender r1, then challenger r1 on its transcript, for each subject.

    Each role asks through its own client, on that role's resolved model.
    """
    reports: list[TurnReport] = []
    for subject in subjects:
        proposition = DebateProposition(
            decision=subject.proposition.decision, context=subject.proposition.context
        )
        name = f"{subject.pm_run}:{subject.ticker}"
        transcript: tuple[DebateTurnRecord, ...] = ()
        roles: tuple[DebateRole, ...] = ("defender", "challenger")
        for role in roles:
            report, turn = _turn(llms[role], name, proposition, role, transcript)
            reports.append(report)
            if turn is None:
                break
            transcript = (turn,)
    return reports


def summary(reports: list[TurnReport]) -> str:
    """State the pass criteria's numbers, each with its denominator."""
    parsed = sum(report.parse == "ok" for report in reports)
    capped = sum(report.stop_reason == "max_tokens" for report in reports)
    challenger = [r.latency_s for r in reports if r.role == "challenger"]
    slowest = f"{max(challenger):.1f}" if challenger else "n/a"
    return (
        f"parsed {parsed} of {len(reports)}; max_tokens stops {capped}; "
        f"challenger max latency_s {slowest}"
    )


def _turn(
    llm: LLMClient,
    name: str,
    proposition: DebateProposition,
    role: DebateRole,
    transcript: tuple[DebateTurnRecord, ...],
) -> tuple[TurnReport, DebateTurnRecord | None]:
    request = DebateTurnRequest(
        request_id=f"{name}:{role}:r1",
        proposition=proposition,
        role=role,
        round_number=1,
        transcript=transcript,
    )
    started = time.monotonic()
    turn: DebateTurnRecord | None = None
    try:
        turn = guided_turn(llm, request)
    except Exception as exc:  # a failed call is a row of the report, not a crash
        parse = f"call failed: {type(exc).__name__}: {exc}"
    else:
        parse = "ok" if turn.reasoning is not None else str(turn.reasoning_error)
    usage = llm_usage(llm)
    report = TurnReport(
        subject=name,
        role=role,
        parse=parse,
        readings=len(turn.reasoning.readings) if turn and turn.reasoning else 0,
        latency_s=time.monotonic() - started,
        tokens_out=usage.tokens_out if usage is not None else None,
        stop_reason=llm_stop_reason(llm),
    )
    return report, turn


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI wiring
    """Run the live check against the configured graph and provider."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=".env", help="path to .env")
    parser.add_argument("--limit", type=int, default=10, help="propositions to run")
    args = parser.parse_args(argv)

    import os

    from dotenv import load_dotenv

    from agents.deliberator.settings import DeliberatorSettings
    from kernel.graph_env import build_graph_from_env
    from kernel.llm_factory import build_llm, key_env_var

    load_dotenv(Path(args.env_file), override=False)
    settings = DeliberatorSettings()
    roles: tuple[DebateRole, ...] = ("defender", "challenger")
    llms = {
        role: build_llm(
            settings.llm_provider,
            api_key=os.environ.get(key_env_var(settings.llm_provider)),
            model=settings.model_for_role(role),
            max_tokens=settings.max_tokens,
            effort=settings.effort,
        )
        for role in roles
    }
    reports = replay(llms, latest_subjects(build_graph_from_env(), args.limit))
    for report in reports:
        print(report.line())
    print(summary(reports))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
