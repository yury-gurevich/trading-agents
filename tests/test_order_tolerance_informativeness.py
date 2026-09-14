"""A comparison that could not have discriminated must say so.

Agent: tooling
Role: pin the label that distinguishes a measured 0.00 from a forced one.
External I/O: none.

Item 56. On 2026-09-13 the report printed `flat 0.00` / `scaled 0.00` over 170
orders and read as "the two modes are equivalent". They are not: the applied band
was flat's fixed 50 bps and scaled was wider on **170 of 170** rows, so every
order flat accepted scaled also accepts, and the orders flat *refused* never
became a `Fill` to be counted. Both zeros were structurally determined.

🪤 The arithmetic was never wrong, and this sprint does not touch it — `_would_fill`
is pinned below precisely so the fix stays a statement and not a change of answer.
"""

from __future__ import annotations

import pytest
from scripts.compare_order_tolerances import (
    _would_fill,
    compare_order_tolerances,
    render_report,
)
from scripts.order_tolerance_informativeness import (
    ToleranceRow,
    assess,
    render_comparison_line,
)

from kernel import InMemoryGraphStore, Node


def _row(applied: str | None, side: str, flat: int, scaled: int) -> ToleranceRow:
    return ToleranceRow(
        applied_mode=applied,
        side=side,
        flat_limit_cents=flat,
        scaled_limit_cents=scaled,
    )


def test_a_narrower_applied_band_forces_both_columns_to_zero() -> None:
    """🎯 The measured case: flat applied, scaled wider on every row."""
    info = assess((_row("flat", "buy", 10050, 10150), _row("flat", "buy", 9900, 9950)))

    assert info.forced is True
    assert info.discriminating == 0
    assert "FORCED" in render_comparison_line(info)


def test_a_wider_applied_band_makes_the_comparison_informative() -> None:
    """🎯 DL-165 flipped the applied band to scaled, which is the wider one."""
    info = assess((_row("scaled", "buy", 10050, 10150), _row("flat", "buy", 100, 200)))

    assert info.forced is False
    assert info.discriminating == 1
    assert "INFORMATIVE - the applied band was the wider one on 1 of 2" in (
        render_comparison_line(info)
    )


def test_a_sell_band_is_wider_downwards() -> None:
    """A sell limit is a floor, so the wider band is the *lower* one."""
    assert assess((_row("scaled", "sell", 10050, 9950),)).discriminating == 1
    assert assess((_row("scaled", "sell", 9950, 10050),)).discriminating == 0


def test_a_row_with_no_recorded_applied_mode_is_not_guessed() -> None:
    """Rows written before S149's mode stamp cannot be classified either way."""
    info = assess((_row(None, "buy", 10050, 10150),))

    assert info.unclassified == 1
    assert "record no applied mode and were skipped" in render_comparison_line(info)


def test_an_empty_comparison_says_it_has_no_data() -> None:
    """Zero rows is not a forced answer; it is the absence of one."""
    info = assess(())

    assert info.forced is False
    assert render_comparison_line(info) == (
        "comparison: NO DATA - no eligible orders carry tolerance evidence"
    )


def test_the_rendered_report_carries_the_label() -> None:
    """The statement is a line of the report, not a footnote a reader may skip."""
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Fill",
        "pm-run:AMD:buy",
        {
            "source_run_id": "pm-run",
            "side": "buy",
            "price_cents": 10040,
            "order_decided_price_cents": 10000,
            "order_flat_limit_price_cents": 10050,
            "order_scaled_limit_price_cents": 10150,
            "order_tolerance_mode": "flat",
        },
    )

    report = render_report(compare_order_tolerances(graph))

    assert report.splitlines()[-1].startswith("comparison: FORCED")


@pytest.mark.parametrize(
    ("side", "actual", "expected"),
    [
        ("buy", 10040, True),
        ("buy", 10060, False),
        ("sell", 9960, True),
        ("sell", 9940, False),
    ],
)
def test_would_fill_is_unchanged_by_this_sprint(
    side: str, actual: int, expected: bool
) -> None:
    """C3: the arithmetic S203 was forbidden to touch, pinned against drift."""
    node = Node(
        label="Fill",
        key="k",
        props={
            "side": side,
            "price_cents": actual,
            "order_flat_limit_price_cents": 10050 if side == "buy" else 9950,
            "order_scaled_limit_price_cents": 10150,
        },
    )

    assert _would_fill(node, "flat") is expected
