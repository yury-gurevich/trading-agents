"""Deterministic dataset splitting.

Agent: curator
Role: partition ordered example records into train/validation/test by ratio.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.curator.domain.assembly import ExampleRecord

_RATIO_TOLERANCE = 1e-9


@dataclass(frozen=True)
class SplitAssignment:
    """Records partitioned into the three named splits over a stable order."""

    train: tuple[ExampleRecord, ...]
    validation: tuple[ExampleRecord, ...]
    test: tuple[ExampleRecord, ...]


def split_examples(
    records: tuple[ExampleRecord, ...], ratios: tuple[float, float, float]
) -> SplitAssignment:
    """Partition records by cumulative ratio over their stable order."""
    if any(ratio < 0 for ratio in ratios) or abs(sum(ratios) - 1.0) >= _RATIO_TOLERANCE:
        raise ValueError("train_val_test ratios must be non-negative and sum to 1.0")
    total = len(records)
    n_train = int(total * ratios[0])
    n_val = int(total * ratios[1])
    return SplitAssignment(
        train=records[:n_train],
        validation=records[n_train : n_train + n_val],
        test=records[n_train + n_val :],
    )
