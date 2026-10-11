"""Planted violations for the gates that read the repo's documents.

Agent: tooling
Role: hold the can-fail cases that do not fit the frozen first case table.
External I/O: none; exports an immutable case table.

`gate_selftest_cases.py` is frozen at its measured size (`module_size_baseline.py`)
and may only shrink, so a new case lives here and the runner reads both tables.
"""

from __future__ import annotations

from scripts.gate_selftest_types import PROBE_PREFIX, FailureCase

_TRACKER_ROOT = f"scripts/{PROBE_PREFIX}_tracker_size"
_TRACKER_CHARTER = """## OPS-TRIM

| Tracker | Limit |
| --- | --- |
| `docs/STATE.md` | 1 KB |
"""

DOCS_FAILURE_CASES: tuple[FailureCase, ...] = (
    FailureCase(
        name="tracker-size",
        why=(
            "S261: a tracker over the byte limit its charter declares must fail "
            "the gate; by hand, two of seven sat over their limit for weeks"
        ),
        files={
            f"{_TRACKER_ROOT}/ops/departments/housekeeping/charter.md": (
                _TRACKER_CHARTER
            ),
            f"{_TRACKER_ROOT}/docs/STATE.md": "x" * 1001,
        },
        command=[
            "uv",
            "run",
            "python",
            "scripts/check_tracker_size.py",
            _TRACKER_ROOT,
        ],
        must_output=("[FAIL] docs/STATE.md: 1,001 of 1,000 bytes", "over by 1"),
    ),
)
