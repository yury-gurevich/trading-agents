"""Broker selection from execution settings.

Agent: execution
Role: pick the live Alpaca paper broker when keyed, else the in-process PaperBroker.
External I/O: none (delegates to the chosen broker).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.broker import PaperBroker

if TYPE_CHECKING:
    from agents.execution.broker import Broker
    from agents.execution.settings import ExecutionSettings


def broker_from_settings(settings: ExecutionSettings) -> Broker:
    """Return the Alpaca paper broker when both keys are set, else PaperBroker."""
    if settings.alpaca_api_key and settings.alpaca_secret_key:
        from agents.execution.alpaca import AlpacaBroker

        return AlpacaBroker(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            base_url=settings.alpaca_base_url,
            timeout=settings.alpaca_timeout,
        )
    return PaperBroker(slippage_bps=settings.slippage_bps)
