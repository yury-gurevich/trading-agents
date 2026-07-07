"""Scanner universe source tests.

Agent: scanner
Role: verify configured static and file-backed universe membership sources.
External I/O: filesystem via pytest tmp_path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.scanner.universe import FileUniverse, StaticUniverse, load_universe_file

if TYPE_CHECKING:
    from pathlib import Path


def test_static_universe_keeps_small_fixture_default() -> None:
    assert StaticUniverse().members("sp500") == ("AAPL", "MSFT", "NVDA", "SPY")


def test_load_universe_file_skips_comments_and_blanks(tmp_path: Path) -> None:
    path = tmp_path / "tickers.txt"
    path.write_text("\n# comment\n aapl \nMSFT\n", encoding="utf-8")

    assert load_universe_file(path) == ("AAPL", "MSFT")


def test_file_universe_reads_named_file(tmp_path: Path) -> None:
    path = tmp_path / "tickers.txt"
    path.write_text("NVDA\nSPY\n", encoding="utf-8")

    source = FileUniverse({"fixture": path})

    assert source.members("fixture") == ("NVDA", "SPY")
    assert source.members("missing") == ()
