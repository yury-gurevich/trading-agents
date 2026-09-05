"""Fixtures for the debate replay harness tests.

Agent: tooling
Role: build arms, subjects and canned batch answers without touching a provider.
External I/O: none.
"""

from __future__ import annotations

import json

from kernel.deliberation import CHALLENGER_SYSTEM, DEFENDER_SYSTEM, Proposition
from orchestration.replay_types import Arm, BatchResult, ReplaySubject

CONTROL = Arm(name="control", model="claude-opus-5", effort="high", max_rounds=2)
ONE_ROUND = Arm(name="rounds1", model="claude-opus-5", effort="high", max_rounds=1)


def subject(ticker: str = "USB", pm_run: str = "pm-run-1") -> ReplaySubject:
    """One replayable decision with a fixed proposition."""
    return ReplaySubject(
        pm_run=pm_run,
        ticker=ticker,
        proposition=Proposition(f"buy {ticker} (qty 7)", f"evidence for {ticker}"),
    )


def verdict_json(ruling: str = "uphold", rationale: str = "held") -> str:
    """The judge's answer in the shape the live parser expects."""
    return json.dumps({"ruling": ruling, "rationale": rationale})


def answers(requests: object, text: str) -> tuple[BatchResult, ...]:
    """Answer every request in a round with the same text."""
    return tuple(
        BatchResult(custom_id=request.custom_id, status="succeeded", text=text)
        for request in requests  # type: ignore[attr-defined]
    )


class ScriptedGateway:
    """A gateway that answers each round from a script and records what it saw."""

    def __init__(self, texts: dict[str, str], *, judge: str | None = None) -> None:
        """Answer arguing turns by role name, and the judge with its own text."""
        self._texts = texts
        self._judge = judge if judge is not None else verdict_json()
        self.rounds: list[tuple[str, ...]] = []
        self.prompts: list[str] = []

    def run(self, requests: object) -> tuple[BatchResult, ...]:
        """Return one canned answer per request, in reverse order."""
        items = list(requests)  # type: ignore[call-overload]
        self.rounds.append(tuple(item.custom_id for item in items))
        self.prompts.extend(item.user for item in items)
        results = [
            BatchResult(
                custom_id=item.custom_id,
                status="succeeded",
                text=self._answer(item),
            )
            for item in items
        ]
        return tuple(reversed(results))

    def _answer(self, item: object) -> str:
        role = _role(str(getattr(item, "system", "")))
        return self._judge if role == "judge" else self._texts.get(role, role)


def _role(system: str) -> str:
    """Identify the speaking role by the exact system prompt it was sent."""
    if system == DEFENDER_SYSTEM:
        return "defender"
    if system == CHALLENGER_SYSTEM:
        return "challenger"
    return "judge"
