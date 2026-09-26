"""Build and read the survivorship-free S&P 500 replay universe cache.

Agent: tooling
Role: combine Wikipedia membership, symbol-map windows, Alpaca bars, and coverage.
External I/O: Wikipedia, Alpaca market data, and an out-of-worktree local cache.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts import replay_dataset  # noqa: E402
from scripts.replay_dataset_sources import daily_bars  # noqa: E402
from scripts.replay_universe_cache import (  # noqa: E402
    Universe,
    coverage_payload,
    load_pages,
    load_universe_cache,
    write_pages,
    write_universe_cache,
)
from scripts.sp500_bars import (  # noqa: E402
    fetch_bars_for_windows,
    windows_from_episodes,
)
from scripts.sp500_chain import chain_source_switches  # noqa: E402
from scripts.sp500_coverage import coverage_report, require_floor  # noqa: E402
from scripts.sp500_guards import (  # noqa: E402
    known_move_counts,
    load_known_moves,
    require_switch_actions,
    review_same_source_moves,
)
from scripts.sp500_membership import (  # noqa: E402
    load_symbol_map,
    reconstruct_membership,
)
from scripts.sp500_replay_build import action_lookup, raw_close_fetcher  # noqa: E402
from scripts.sp500_wiki import (  # noqa: E402
    CHANGES_URL,
    CONSTITUENTS_URL,
    fetch_source_pages,
    parse_changes_page,
    parse_constituents_page,
)

UNIVERSE_START = "2016-01-04"  # First replay session measured for P17 E17.1.
SESSION_SYMBOL = "SPY"  # SPY sessions define market days; weekdays do not.
PageFetcher = Callable[[], dict[str, str]]
BarFetcher = Callable[..., dict[str, list[Any]]]


def build_universe(
    end: str | None = None,
    from_snapshot: bool = False,
    cache: Path | None = None,
    page_fetcher: PageFetcher = fetch_source_pages,
    bar_fetcher: BarFetcher = daily_bars,
) -> Universe:
    cache_dir = cache or replay_dataset.CACHE
    _refuse_repo_cache(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    end_day = end or _default_end()
    pages = load_pages(cache_dir) if from_snapshot else _fetch_pages(page_fetcher)
    write_pages(cache_dir, pages)
    constituents_page = parse_constituents_page(pages["constituents"]["html"])
    changes_page = parse_changes_page(pages["changes"]["html"])
    sessions, spy_closes = _sessions(end_day, bar_fetcher)
    map_rows = load_symbol_map()
    membership = reconstruct_membership(
        constituents_page.rows, changes_page.rows, sessions, map_rows
    )
    windows = windows_from_episodes(membership.episodes, map_rows)
    fetched = fetch_bars_for_windows(windows, sessions, bar_fetcher)
    chained = chain_source_switches(
        fetched.rows,
        raw_close_fetcher(bar_fetcher),
        spy_closes,
        action_lookup(map_rows),
    )
    require_switch_actions(chained.switches)
    known_moves = load_known_moves()
    reviewed_moves = review_same_source_moves(
        chained.rows, spy_closes, known_moves, membership.episodes
    )
    report = coverage_report(membership.episodes, chained.rows, sessions)
    require_floor(report)
    coverage = coverage_payload(
        report, membership, fetched.refetched, chained.switches, reviewed_moves
    )
    write_universe_cache(cache_dir, sessions, membership, chained.rows, coverage)
    return Universe(sessions, membership.episodes, chained.rows, coverage)


def load_universe(cache: Path | None = None) -> Universe:
    return load_universe_cache(cache or replay_dataset.CACHE)


def describe(cache: Path | None = None) -> str:
    universe = load_universe(cache)
    reconciliation = universe.coverage["reconciliation"]
    coverage = universe.coverage["coverage"]
    switches = universe.coverage.get("switches", [])
    reviewed_moves = universe.coverage.get("reviewed_moves", [])
    known_counts = known_move_counts(load_known_moves())
    lines = [
        f"cache: {cache or replay_dataset.CACHE}",
        (
            "membership: "
            f"{len(universe.episodes)} episodes, count "
            f"{reconciliation['count_min']}..{reconciliation['count_max']}, "
            f"unreconciled {len(reconciliation['unreconciled'])}"
        ),
        (
            "coverage: "
            f"{coverage['covered_sessions']}/{coverage['member_sessions']} "
            f"({coverage['ratio']:.2%}), shortfalls {len(coverage['shortfalls'])}"
        ),
        (
            "switches: "
            f"{len(switches)} recorded, "
            f"{sum(1 for row in switches if row.get('action'))} with action"
        ),
        f"known moves: {len(reviewed_moves)} reviewed, file {known_counts}",
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Build or describe S&P 500 replay universe."
    )
    parser.add_argument(
        "command", nargs="?", choices=("build",), help="build the universe cache"
    )
    parser.add_argument("--end", help="inclusive YYYY-MM-DD end date for bars")
    parser.add_argument(
        "--from-snapshot", action="store_true", help="reuse saved Wikipedia pages"
    )
    parser.add_argument(
        "--describe", action="store_true", help="print the cached report"
    )
    arguments = parser.parse_args(argv)
    if arguments.describe:
        print(describe())
        return 0
    if arguments.command != "build":
        parser.error("expected 'build' or --describe")
    build_universe(end=arguments.end, from_snapshot=arguments.from_snapshot)
    print(describe())
    return 0


def _fetch_pages(page_fetcher: PageFetcher) -> dict[str, dict[str, str]]:
    fetched = page_fetcher()
    return {
        "constituents": {"url": CONSTITUENTS_URL, "html": fetched["constituents"]},
        "changes": {"url": CHANGES_URL, "html": fetched["changes"]},
    }


def _sessions(
    end: str, bar_fetcher: BarFetcher
) -> tuple[tuple[date, ...], dict[date, float]]:
    rows = bar_fetcher([SESSION_SYMBOL], end=end, start=UNIVERSE_START, asof=end).get(
        SESSION_SYMBOL, ()
    )
    spy_closes = {date.fromisoformat(str(row[0])[:10]): float(row[4]) for row in rows}
    return tuple(sorted(spy_closes)), spy_closes


def _refuse_repo_cache(cache_dir: Path) -> None:
    try:
        cache_dir.resolve().relative_to(_ROOT.resolve())
    except ValueError:
        return
    raise RuntimeError(f"replay universe cache must be outside the repo: {cache_dir}")


def _default_end() -> str:
    return (datetime.now(UTC).date() - timedelta(days=1)).isoformat()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
