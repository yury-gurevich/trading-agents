"""Generic graph-poll work loop for agent entrypoints.

Agent: kernel
Role: shared "find pending → process each → sleep" loop so every graph-pull agent
      entrypoint stays thin (DL-08 graph-as-queue). The single-pass `run_once` is
      independently testable; `work_loop` is the infinite wrapper.
External I/O: none.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

_DEFAULT_POLL_INTERVAL = 60


def run_once[T](
    find_pending: Callable[[], list[T]],
    process_one: Callable[[T], None],
) -> int:
    """Process every currently-pending item once; return how many were processed."""
    items = find_pending()
    for item in items:
        process_one(item)
    return len(items)


def work_loop[T](  # pragma: no cover - blocks forever; run_once carries the coverage
    find_pending: Callable[[], list[T]],
    process_one: Callable[[T], None],
    *,
    poll_interval: int = _DEFAULT_POLL_INTERVAL,
) -> None:
    """Poll the graph forever: process all pending work, then sleep when idle."""
    while True:
        if run_once(find_pending, process_one) == 0:
            time.sleep(poll_interval)
