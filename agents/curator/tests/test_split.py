"""Curator split tests.

Agent: curator
Role: verify deterministic, contiguous train/validation/test partitioning.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.curator.domain.assembly import ExampleRecord
from agents.curator.domain.split import split_examples


def _records(count: int) -> tuple[ExampleRecord, ...]:
    return tuple(
        ExampleRecord(
            example_id=f"x:{index}",
            content=f"c{index}",
            label="target",
            source_ref=f"TradeNarrative:narrative:{index}",
            metadata={},
        )
        for index in range(count)
    )


def test_eighty_ten_ten_split_is_contiguous_and_deterministic() -> None:
    records = _records(10)

    first = split_examples(records, (0.8, 0.1, 0.1))
    second = split_examples(records, (0.8, 0.1, 0.1))

    assert (len(first.train), len(first.validation), len(first.test)) == (8, 1, 1)
    assert first.train == records[:8]
    assert first.validation == records[8:9]
    assert first.test == records[9:]
    assert first == second


def test_ratios_not_summing_to_one_raise() -> None:
    with pytest.raises(ValueError, match=r"sum to 1\.0"):
        split_examples(_records(3), (0.5, 0.1, 0.1))


def test_int_floor_behaviour_for_small_corpus() -> None:
    split = split_examples(_records(3), (0.8, 0.1, 0.1))

    assert (len(split.train), len(split.validation), len(split.test)) == (2, 0, 1)
