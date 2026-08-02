"""Tunable policy for graph-pull retry containment.

Agent: kernel
Role: declare the bounded retry/backoff envelope shared by graph-pull agents.
External I/O: none.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict, model_validator

from kernel.config import tunable

if TYPE_CHECKING:
    from collections.abc import Mapping


class WorkLoopPolicy(BaseModel):
    """Operator-visible retry policy for one graph-pull work loop."""

    model_config = ConfigDict(frozen=True)

    poll_interval_seconds: float = tunable(
        60.0,
        why=(
            "Default graph-pull idle cadence from DL-08; long enough to avoid busy "
            "polling while still fitting the nightly fleet window."
        ),
        gt=0.0,
        unit="seconds",
    )
    backoff_base_seconds: float = tunable(
        60.0,
        why=(
            "First retry delay for a still-pending item; matches the idle poll "
            "cadence so a poison item cannot spin faster than normal graph polling."
        ),
        gt=0.0,
        unit="seconds",
    )
    backoff_multiplier: float = tunable(
        2.0,
        why=(
            "Exponential per-item growth separates an ongoing defect from a "
            "transient miss without starving healthy siblings."
        ),
        gt=1.0,
    )
    backoff_ceiling_seconds: float = tunable(
        900.0,
        why=(
            "Ceiling keeps retries bounded while still giving a poisoned item "
            "several attempts inside the roughly two-hour fleet window."
        ),
        gt=0.0,
        unit="seconds",
    )
    max_attempts_before_quarantine: int = tunable(
        5,
        why=(
            "Attempt cap turns an ongoing poison item into a visible quarantine "
            "instead of retrying indefinitely."
        ),
        ge=1,
    )

    @model_validator(mode="after")
    def _ceiling_must_cover_base(self) -> Self:
        if self.backoff_ceiling_seconds < self.backoff_base_seconds:
            raise ValueError("backoff ceiling must be at least the base delay")
        return self


DEFAULT_WORK_LOOP_POLICY = WorkLoopPolicy()


def poll_interval_from_env(
    name: str,
    *,
    policy: WorkLoopPolicy = DEFAULT_WORK_LOOP_POLICY,
    environ: Mapping[str, str] | None = None,
) -> float:
    """Resolve an entrypoint poll interval using the tunable default."""
    source = os.environ if environ is None else environ
    raw = source.get(name)
    return policy.poll_interval_seconds if raw is None else float(raw)
