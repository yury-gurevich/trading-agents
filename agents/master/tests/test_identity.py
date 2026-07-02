"""Master instance identity tests.

Agent: master
Role: prove instance-id allocation is protected by a lock under concurrent callers.
External I/O: none.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from agents.master.identity import next_instance_id


def test_next_instance_id_is_unique_under_threads() -> None:
    counters: dict[str, int] = {}
    lock = Lock()
    with ThreadPoolExecutor(max_workers=8) as pool:
        ids = tuple(
            pool.map(lambda _: next_instance_id("scanner", counters, lock), range(50))
        )
    assert len(set(ids)) == 50
    assert counters == {"scanner": 50}
