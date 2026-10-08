"""DL-276 D3 pins the four authorized execution PARAM amendments.

Agent: tooling
Role: pin exact Type cells, next book version and the one S258 Changelog line.
External I/O: read the execution law book only.
"""

from pathlib import Path

from scripts.param_law_sync_sources import param_rows

_ROOT = Path(__file__).resolve().parents[1]
_BOOK = "agents/execution/laws/laws.md"
_CELLS = {
    "slippage_bps": "`int ≥ 0, ≤ 1000` (basis points)",
    "min_promotion_runs": "`int ≥ 3, ≤ 200`",
    "min_approval_rate": "`float ≥ 0.0, ≤ 1.0`",
    "alpaca_timeout": "`int ≥ 1, ≤ 60` (seconds)",
}
_CHANGELOG = (
    "- **v1.13 — S258 / DL-276 (2026-10-08).** PARAM only: reconciles the bounds of "
    "`slippage_bps`, `min_promotion_runs`, `min_approval_rate` and `alpaca_timeout` "
    "with settings; no clause, default or code bound changes."
)


def test_the_four_execution_rows_state_the_decided_bounds():
    """DL-276 B1: the four literal Type cells and amendment record follow D3."""
    rows = param_rows(_ROOT, "execution")
    assert {name: rows[name].type_cell for name in _CELLS} == _CELLS
    book = (_ROOT / _BOOK).read_text(encoding="utf-8")
    assert "**status:** LOCKED v1.13" in book
    assert book.splitlines().count(_CHANGELOG) == 1
