"""Forecaster return-model test message builders.

Agent: forecaster
Role: provide deterministic message builders for return_scorecard and forecast_return.
External I/O: none.
"""

from __future__ import annotations

from typing import Literal

from contracts.forecaster import ForecastRequest, ReturnScorecardRequest
from kernel import AgentMessage


def return_scorecard_message(
    model_id: str, forward_returns: dict[str, float]
) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="forecaster",
        message_type="request",
        capability="return_scorecard",
        payload=ReturnScorecardRequest(
            model_id=model_id, forward_returns=forward_returns
        ).model_dump(mode="json"),
    )


def forecast_return_message(
    subject_ref: str,
    *,
    subject_kind: Literal["recommendation", "position"] = "recommendation",
) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="forecaster",
        message_type="request",
        capability="forecast_return",
        payload=ForecastRequest(
            subject_kind=subject_kind,
            subject_ref=subject_ref,
            features={},
        ).model_dump(mode="json"),
    )
