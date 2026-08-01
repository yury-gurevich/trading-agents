"""Deliberator contract value validation tests.

Agent: contracts (shared)
Role: verify deliberator payload values fail at typed message boundaries.
External I/O: none.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from contracts.deliberator import CONTRACT as DELIBERATOR_CONTRACT
from contracts.deliberator import DebateProposition, DebateTurnRequest


def test_deliberator_contract_boundary_and_round_validation() -> None:
    assert DELIBERATOR_CONTRACT.name == "deliberator"
    assert DELIBERATOR_CONTRACT.owns_graph == ("DeliberationRun",)
    turn = DELIBERATOR_CONTRACT.capability("debate_turn")
    assert turn.allowed_callers == ("deliberator-manager",)
    with pytest.raises(ValidationError):
        DebateTurnRequest(
            request_id="bad",
            proposition=DebateProposition(decision="buy AAPL", context="ctx"),
            role="defender",
            round_number=0,
        )
