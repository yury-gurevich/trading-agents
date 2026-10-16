"""Synthetic four-session cache and buy-once runner for S281.

Agent: tooling
Role: share deterministic bars, intents and a day runner for replay exit proofs.
External I/O: synthetic cache files under pytest's external tmp_path only.
"""

from __future__ import annotations

import csv
import gzip
import io
from datetime import date
from decimal import Decimal

from scripts.replay_broker import ReplayPosition
from scripts.replay_day import ReplayDayResult
from scripts.replay_universe_cache import write_universe_cache
from scripts.sp500_bars import BarRow
from scripts.sp500_membership import Episode, MembershipResult

from agents.execution.order_tolerance import OrderToleranceConfig
from contracts.analyst import RecommendationSet
from contracts.common import Explanation, Money, Provenance
from contracts.portfolio_manager import OrderIntent
from contracts.scanner import CandidateSet, FilterTrace

SESSIONS = tuple(date(2024, 1, day) for day in (2, 3, 4, 5))
CONFIG = OrderToleranceConfig("flat", 50, 0.5, 25, 250)


def bar(index=2, *, line="AAA", prices=(104, 111, 100, 108)):
    return BarRow(line, line, SESSIONS[index], *prices, 1_000_000)


def position(line="AAA", **changes):
    values = {
        "line": line,
        "quantity": 2,
        "entry_price_cents": 10_000,
        "stop_price_cents": 9_500,
        "opened": SESSIONS[0],
        "stop_active_from": SESSIONS[1],
        "position_ref": f"position-{line}",
        "stop_pct": 0.05,
    }
    return ReplayPosition(**(values | changes))


def intent(action="buy", *, line="AAA", **changes):
    values = {
        "ticker": line,
        "action": action,
        "quantity": 2,
        "est_price": Money(amount=Decimal("100")),
        "stop_pct": 0.05,
        "target_pct": 0.10,
        "rationale": Explanation(summary="synthetic exit fixture"),
    }
    return OrderIntent(**(values | changes))


def write_cache(path, *, stopped=False):
    path.mkdir()
    rows = (
        bar(0, prices=(100, 101, 99, 100)),
        bar(1, prices=(100, 102, 99, 102)),
        bar(2, prices=(100, 101, 94, 96)) if stopped else bar(),
        bar(3, prices=(106, 109, 105, 107)),
    )
    membership = MembershipResult(
        (Episode("AAA", "AAA", SESSIONS[0], SESSIONS[-1]),),
        dict.fromkeys(SESSIONS, ("AAA",)),
        1,
        1,
        (),
    )
    write_universe_cache(path, SESSIONS, membership, rows, {})
    _csv(
        path / "sp500_benchmark.csv.gz",
        ["symbol", "date", "open", "high", "low", "close", "volume"],
        [["SPY", day, 300, 302, 299, 300 + i, 100] for i, day in enumerate(SESSIONS)],
    )
    _csv(path / "sp500_vix.csv.gz", ["date", "vix_close"], [[s, 20] for s in SESSIONS])
    _csv(path / "sp500_sectors.csv.gz", ["line", "sector"], [["AAA", "fixture"]])
    return path


def _csv(path, header, rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    path.write_bytes(gzip.compress(buffer.getvalue().encode("utf-8"), mtime=0))


class BuyOnce:
    def __init__(self):
        self.offered = []

    def __call__(self, inputs, settings):
        self.offered.append(inputs.tickers)
        common = {
            "run_id": inputs.run_id,
            "explanation": Explanation(summary="fixture day"),
            "provenance": Provenance(run_id=inputs.run_id, source_agent="scanner"),
        }
        candidates = CandidateSet(
            **common,
            candidates=(),
            filter_trace=FilterTrace(universe_size=len(inputs.tickers), evaluated=0),
        )
        recommendations = RecommendationSet(**common, recommendations=(), rejections=())
        approved = (intent(),) if inputs.session == SESSIONS[0] else ()
        return ReplayDayResult(candidates, recommendations, approved, (), {})


def run_fixture(monkeypatch, path, **options):
    from scripts.replay_runner import run

    day = BuyOnce()
    monkeypatch.setattr("scripts.replay_runner.run_replay_day", day)
    summary = run(
        cache_dir=write_cache(path / "cache", stopped=options.pop("stopped", False)),
        out=path / "out",
        start=None,
        end=None,
        overrides=(),
        slippage_bps=0,
        progress_every=0,
        **options,
    )
    with (path / "out" / "fills.csv").open(encoding="utf-8", newline="") as handle:
        fills = list(csv.DictReader(handle))
    return summary, fills, day.offered
