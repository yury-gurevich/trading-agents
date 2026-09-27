"""Graph fixtures for the S236 scorecard tests.

Agent: surfaces
Role: seed sessions and the records human actions leave, as their writers shape them.
External I/O: none; writes only to the supplied in-memory graph.

Every property here mirrors a production writer: `RunRequest` (orchestration/start.py,
a bare-date `requested_at`; orchestration/resume.py; orchestration/daily_brief.py),
`CommandAudit` and `Intent` (agents/operator/store.py), `RunHoldAnswer`
(orchestration/hold_answers.py), `Escalation` (agents/master/store.py) and
`DeployRecord` (orchestration/deploy_record.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, cast

from orchestration.packs.trading_acceptance import TradingAcceptanceResult
from surfaces.queries.scorecard import scorecard
from surfaces.queries.scorecard_verdicts import VerdictMemo
from surfaces.scorecard_settings import ScorecardSettings

if TYPE_CHECKING:
    from kernel import GraphStore
    from orchestration.packs.trading_acceptance import AcceptanceVerdict
    from surfaces.queries.scorecard_model import Scorecard

# The planner's measuring instant: Sunday 2026-09-27, after Friday's window closed.
NOW = datetime(2026, 9, 27, 3, 0, tzinfo=UTC)
# The five sessions an 8-day window holds from NOW (2026-09-19 through 2026-09-27).
WEEK = tuple(date(2026, 9, day) for day in range(21, 26))


def settings(window_days: int = 8) -> ScorecardSettings:
    """Scorecard settings; the default window holds exactly the sessions of WEEK."""
    return ScorecardSettings(scorecard_window_days=window_days)


def at(day: date, hour: int, minute: int = 0) -> datetime:
    """Return an aware UTC instant on ``day``."""
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=UTC)


@dataclass
class CountingJudge:
    """A stand-in for `accept_run` that records every run it is asked about."""

    words: dict[str, str]
    calls: list[str] = field(default_factory=list)

    def __call__(self, graph: GraphStore, run_id: str) -> TradingAcceptanceResult:
        """Return the planted word for ``run_id`` and count the call."""
        del graph
        self.calls.append(run_id)
        word = cast("AcceptanceVerdict", self.words[run_id])
        return TradingAcceptanceResult(verdict=word, breaches=())


def score(graph: GraphStore, window_days: int, now: datetime = NOW) -> Scorecard:
    """Score with a judge that must never be asked: every session is briefed."""
    return scorecard(
        graph,
        now=now,
        settings=settings(window_days=window_days),
        verdicts=VerdictMemo(CountingJudge({})),
    )


def session(
    graph: GraphStore,
    day: date,
    *,
    verdict: str | None = None,
    requested_at: str | None = None,
) -> str:
    """Place ``sched-<day>`` as the dispatcher does; brief it when given a verdict."""
    run_id = f"sched-{day.isoformat()}"
    props: dict[str, object] = {
        "run_id": run_id,
        "tickers": ["AAPL"],
        "requested_at": requested_at or day.isoformat(),
    }
    if verdict is not None:
        props |= {
            "brief_sent_at": at(day, 22, 50).isoformat(timespec="seconds"),
            "brief_message_id": 7,
            "brief_verdict": verdict,
        }
    graph.merge_node("RunRequest", f"run-request:{run_id}", props)
    return run_id


def command(
    graph: GraphStore,
    when: datetime,
    *,
    key: str,
    family: str | None = None,
    outcome: str = "intent",
) -> None:
    """Write one `CommandAudit`, and the `Intent` it produced when given a family."""
    audit = graph.merge_node(
        "CommandAudit",
        f"audit:{key}",
        {
            "correlation_id": key,
            "actor": "operator",
            "channel": "dashboard",
            "text": key,
            "outcome": outcome,
            "created_at": when.isoformat(),
        },
    )
    if family is None:
        return
    intent = graph.merge_node(
        "Intent",
        f"intent:{key}",
        {"family": family, "parameters": "{}", "requires_confirmation": False},
    )
    graph.add_edge(audit, intent, "RESULTED_IN")


def manual_run(graph: GraphStore, run_id: str, requested_at: str) -> None:
    """Place a run by hand (`place_run_request` under a non-scheduled id)."""
    graph.merge_node(
        "RunRequest",
        f"run-request:{run_id}",
        {"run_id": run_id, "tickers": ["AAPL"], "requested_at": requested_at},
    )


def resume(graph: GraphStore, source: str, stage: str, resumed_at: datetime) -> None:
    """Place a resume child as `orchestration.resume.resume_run` does.

    Like production, the child copies its source's `requested_at`.
    """
    child = f"{source}-resume-{stage}"
    parent = graph.get_node("RunRequest", f"run-request:{source}")
    assert parent is not None, f"place {source} before resuming it"
    graph.merge_node(
        "RunRequest",
        f"run-request:{child}",
        {
            "run_id": child,
            "tickers": ["AAPL"],
            "requested_at": parent.props["requested_at"],
            "resume_from": stage,
            "source_run_id": source,
            "resumed_at": resumed_at.isoformat(),
        },
    )


def hold_answer(graph: GraphStore, run_id: str, answered_at: datetime) -> None:
    """Record a human's answer to a held run, as the dashboard route does."""
    graph.merge_node(
        "RunHoldAnswer",
        f"answer:{run_id}:dashboard:1",
        {
            "run_id": run_id,
            "as_of": answered_at.date().isoformat(),
            "answer": "run_now",
            "source": "dashboard",
            "answered_at": answered_at.isoformat(timespec="seconds"),
            "update_id": 0,
        },
    )


def escalation(
    graph: GraphStore, created_at: datetime, *, agent: str = "operator"
) -> None:
    """Record a credential escalation as the master does (open, whatever follows)."""
    graph.merge_node(
        "Escalation",
        f"escalation:{agent}:{created_at:%Y%m%dT%H%M%S%f}",
        {
            "agent_type": agent,
            "failed_credentials": ["anthropic"],
            "mode": "manual",
            "auto_attempts": 0,
            "status": "open",
            "created_at": created_at.isoformat(),
        },
    )


def deploy(graph: GraphStore, deployed_at: datetime, tag: str = "s236") -> None:
    """Record a verified fleet deploy as `record_deploy` does."""
    stamp = deployed_at.astimezone(UTC).isoformat()
    graph.merge_node(
        "DeployRecord",
        f"deploy:{stamp}:{tag}:abc123",
        {"tag": tag, "git_sha": "abc123", "deployed_at": stamp, "actor": "planner"},
    )
