"""The recorded EXP-019 orders pin S255's frozen arithmetic text.

Agent: deliberator
Role: unit proof of the packet's recorded score arithmetic.
External I/O: local fixture reads only.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from contracts.analyst import Recommendation
from contracts.common import Provenance
from contracts.provider import RegimeContext

FIXTURE = Path(__file__).parent / "fixtures" / "score_arithmetic_nine_orders.json"


def test_nine_orders_render_the_measured_text() -> None:
    """DLIB-OUT-08: nine whole blocks equal the planner's corrected fixture."""
    from agents.deliberator.context_arithmetic import arithmetic_lines

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    equal = 0
    for order in fixture["orders"]:
        rec = Recommendation.model_validate(
            {**order["recommendation"], "score_arithmetic": order["score_arithmetic"]}
        )
        regime = RegimeContext(
            label="neutral",
            as_of=datetime(2026, 10, 5, tzinfo=UTC),
            base_min_confidence=order["base_min_confidence"],
            base_stop_loss_pct=0.05,
            base_take_profit_pct=0.10,
            base_max_holding_days=10,
            provenance=Provenance(run_id="s255", source_agent="provider"),
            vix_thresholds=fixture["vix_thresholds"],
        )
        actual = "\n".join(arithmetic_lines(rec, regime, order["ticker"]))
        assert actual == order["arithmetic_lines"], order["ticker"]
        equal += 1
    assert equal == 9
    print(f"{equal} of 9 orders equal")


def test_arithmetic_is_appended_without_changing_an_earlier_line() -> None:
    """DLIB-OUT-08 / DLIB-OUT-07: only the three final lines are added."""
    from tests.score_arithmetic_support import packet, recorded_order

    from agents.deliberator.context_arithmetic import arithmetic_lines

    rec, regime = recorded_order()
    old = packet(
        rec.model_copy(update={"score_arithmetic": None}),
        regime.model_copy(update={"vix_thresholds": None}),
    )
    new = packet(rec, regime)
    assert new == old + "\n" + "\n".join(arithmetic_lines(rec, regime, rec.ticker))


def test_old_and_missing_recommendations_keep_the_main_packet() -> None:
    """DLIB-OUT-08: both pre-field packets equal frozen main output bytewise."""
    from tests.score_arithmetic_support import MAIN_PACKETS, packet
    from tests.veto_context_fixtures import recs
    from tests.veto_context_provider_fixtures import regime

    main = json.loads(MAIN_PACKETS.read_text(encoding="utf-8"))
    old = Recommendation.model_validate(recs()["recommendations"][0])
    context = RegimeContext.model_validate(regime())
    assert old.score_arithmetic is None
    assert context.vix_thresholds is None
    assert packet(old, context) == main["recommendation"]
    assert packet(None, context) == main["no_recommendation"]
