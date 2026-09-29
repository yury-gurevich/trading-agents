"""S241 C7: barrier_scorecard scores the ledger exactly as EXP-018 scored its cases.

Agent: forecaster
Role: prove the scorecard's shares, Brier, skill over EXP-018's fixed climatology
      and date-bootstrap interval against the experiment's own `run()`, read at test
      time from the frozen record (Appendix S, `exp018_score.py`) and run on the same
      cases in the same order with the same seed, outcome for outcome.
External I/O: reads docs/research/experiments/EXP-018-garch-history-depth.md.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from agents.forecaster.domain.barrier_settlement import OUTCOMES, VOID, Settlement
from agents.forecaster.settlement_store import write_settlement
from agents.forecaster.tests.ledger_fixture import (
    CLIMATOLOGY,
    DATES,
    LEDGER,
    MODEL,
    card,
    settle_row,
    write_ledger,
)
from agents.forecaster.tests.settlement_helpers import seed_claim
from kernel import InMemoryGraphStore

_ROOT = Path(__file__).resolve().parents[3]
_RECORD = _ROOT / "docs/research/experiments/EXP-018-garch-history-depth.md"


def _experiment(tmp_path: Path) -> Any:
    """EXP-018's `run()` from `exp018_score.py`, verbatim, as an importable module."""
    text = _RECORD.read_text(encoding="utf-8")
    block = text.split("### `exp018_score.py`", 1)[1].split("```python", 1)[1]
    lines = block.split("```", 1)[0].splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("def run("))
    end = next(
        i
        for i in range(start + 1, len(lines))
        if lines[i] and not lines[i][0].isspace()
    )
    source = "import numpy as np\n" + "\n".join(lines[start:end]) + "\n"
    target = tmp_path / "exp018_run.py"
    target.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("exp018_run", target)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_oracle_is_the_records_run(tmp_path: Path) -> None:
    """FORE-OUT-08: the oracle is the record's scorer: 1,000 draws, seed 20260929."""
    source = Path(_experiment(tmp_path).__file__).read_text(encoding="utf-8")
    assert "np.random.default_rng(20260929)" in source
    assert "for _ in range(1000)" in source
    assert "np.percentile(sk, 2.5), np.percentile(sk, 97.5)" in source


def test_the_scorecard_reports_the_ledger_as_exp018_scores_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """FORE-OUT-08 / FORE-OUT-03 / FORE-OUT-04 / FORE-NEV-03: ten settled claims on
    four dates, one void, one open and another model's settled claim. Counts and
    shares by hand; Brier, the fixed-climatology Brier, skill and the date-bootstrap
    interval equal EXP-018's `run()` on the same cases, order and seed; never
    promotion-eligible."""
    graph = InMemoryGraphStore()
    write_ledger(graph)
    settle_row(graph, ("MSFT", 3, (0.3, 0.4, 0.3), VOID))
    seed_claim(graph, ticker="NVDA", as_of=DATES[3])  # open
    template = seed_claim(InMemoryGraphStore(), ticker="AMZN", as_of=DATES[0])
    other = graph.merge_node(
        "BarrierForecast",
        "other-model:AMZN:2026-09-28",
        {**template.props, "model_id": "other-model"},
    )
    write_settlement(
        graph,
        other,
        Settlement("stop", None, DATES[2], 100.0, 1.0),
        settling_ref="market-data:other",
    )

    scorecard = card(graph)

    run = _experiment(tmp_path)
    run.cases = [
        {"outcome": OUTCOMES.index(o), "day": DATES[i].isoformat(), "G_ledger": p}
        for _t, i, p, o in LEDGER
    ]
    run.Y_all = np.eye(3)[[case["outcome"] for case in run.cases]]
    run.clim_all = np.tile(CLIMATOLOGY, (len(LEDGER), 1))
    forecast, realised, loss, draws, res, _d, _i = run.run(
        "ledger", list(range(len(LEDGER))), ("ledger",)
    )
    capsys.readouterr()
    skills = [
        1 - loss["G_ledger"][s].mean() / loss["climatology"][s].mean() for s in draws
    ]
    metrics = scorecard.metrics
    assert (metrics["settled"], metrics["void"], metrics["open"]) == (10.0, 1.0, 1.0)
    assert scorecard.sample_size == 10
    assert scorecard.promotion_eligible is False
    assert scorecard.model_id == MODEL
    shares = tuple(metrics[f"realised_{name}"] for name in OUTCOMES)
    assert shares == pytest.approx((0.3, 0.5, 0.2))
    assert shares == tuple(realised.mean(0))
    declared = tuple(metrics[f"declared_{name}"] for name in OUTCOMES)
    assert declared == tuple(forecast["G_ledger"].mean(0))
    assert metrics["brier_model"] == loss["G_ledger"].mean()
    assert metrics["brier_climatology"] == loss["climatology"].mean()
    assert (metrics["skill"], metrics["skill_lo"]) == res["G_ledger"]
    assert metrics["skill_hi"] == np.percentile(skills, 97.5)
