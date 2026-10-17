"""USB stop-pass fixtures accepting any broker port.

Agent: execution
Role: rest a fallback stop and run the normal decided-stop placement pass.
External I/O: none; injected broker doubles only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.broker_stop_actions import place_stop
from agents.execution.broker_stop_types import StopProvenance
from agents.execution.broker_stops import place_broker_stops
from agents.execution.tests.broker_stop_helpers import order_set
from agents.execution.tests.stop_realign_helpers import (
    FALLBACK_STOP_PCT,
    OPENED_CENTS,
    QUANTITY,
    usb_snapshot,
)
from contracts.positions import PositionStopThreshold, open_positions
from kernel import CollectingFaultSink

if TYPE_CHECKING:
    from agents.execution.broker import Broker
    from kernel import GraphStore


def rest_fallback_stop(graph: GraphStore, broker: Broker) -> str:
    """Place the historical 5 percent stop for the adopted USB position."""
    ref = open_positions(graph)[0].position_ref
    threshold = PositionStopThreshold(
        "USB", QUANTITY, ref, OPENED_CENTS, FALLBACK_STOP_PCT
    )
    key = f"stop:{ref}:USB"
    place_stop(
        graph,
        broker,
        CollectingFaultSink(),
        threshold,
        key,
        provenance=StopProvenance("position", "active_position"),
    )
    return key


def run_stop_pass(graph: GraphStore, broker: Broker) -> CollectingFaultSink:
    """Run the normal stop pass with USB's fresh market snapshot."""
    sink = CollectingFaultSink()
    place_broker_stops(
        graph,
        broker,
        sink,
        order_set("pm-run-today"),
        usb_snapshot(graph),
        fallback_stop_pct=FALLBACK_STOP_PCT,
    )
    return sink
