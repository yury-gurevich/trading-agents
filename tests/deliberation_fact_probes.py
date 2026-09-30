"""Probes the S245 fact pins read our code with (DLIB-NEV-09).

Agent: tooling
Role: build the one-session batch the pooled-sigma pin validates and the buys
      the sizing pin weighs, scan sources for the pack and forecaster pins, and
      read the distinctions a champion prompt states.
External I/O: none (callers pass the text they read).
"""

from __future__ import annotations

import ast
import re
from datetime import date

from agents.portfolio_manager.tests.helpers import recommendation
from agents.provider.domain.integrity import validate_bars
from agents.provider.settings import ProviderSettings
from contracts.analyst import QuantMetric, Recommendation
from contracts.common import Window
from contracts.provider import OHLCVBar

_SESSION = date(2026, 9, 28)
# From the lead-in to the first sentence-ending period: "0.00" is not one.
_DISTINCTIONS = re.compile(r"Preserve these distinctions: (.*?)\.(?=\s)")


def anomalous(mover_close: float, spread: float = 1.5) -> tuple[str, ...]:
    """Validate one session: 98 names at +/-spread % open-to-close, then X.

    Every bar opens at 100 on the same date, so the guard sees exactly the pool
    `PROV-OUT-09` names: each ticker's newest open-to-close move on that session.
    """
    closes = [100 + (spread if i % 2 else -spread) for i in range(98)]
    names = (*(f"N{i:03d}" for i in range(98)), "X")
    bars = tuple(
        OHLCVBar(
            ticker=name,
            bar_date=_SESSION,
            open=100.0,
            high=max(100.0, close),
            low=min(100.0, close),
            close=close,
            volume=1_000,
        )
        for name, close in zip(names, (*closes, mover_close), strict=True)
    )
    window = Window(start=_SESSION, end=_SESSION)
    _, quality = validate_bars(names, bars, window, ProviderSettings())
    return quality.anomalous_tickers


def buy(ticker: str, beta: float, atr_pct: float) -> Recommendation:
    """A fixture buy carrying the risk metrics a volatility-aware sizer would read."""
    metrics = (
        QuantMetric(name="beta", value=beta),
        QuantMetric(name="atr_pct", value=atr_pct),
    )
    return recommendation(ticker).model_copy(update={"quant_metrics": metrics})


def keys(node: object) -> list[str]:
    """Every mapping key anywhere in a parsed JSON document."""
    if isinstance(node, dict):
        return [*node, *(key for value in node.values() for key in keys(value))]
    if isinstance(node, list):
        return [key for item in node for key in keys(item)]
    return []


def reads_forecaster(source: str) -> bool:
    """Whether a module imports the forecaster contract or names ShadowPrediction."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            modules = [base, *(f"{base}.{alias.name}" for alias in node.names)]
        else:
            continue
        if any(name.startswith("contracts.forecaster") for name in modules):
            return True
    return "ShadowPrediction" in source


def distinctions(prompt: str) -> set[str]:
    """The distinctions a champion prompt tells a role to preserve, one per `;`."""
    match = _DISTINCTIONS.search(prompt)
    assert match is not None
    return {part.strip() for part in match.group(1).split(";")}
