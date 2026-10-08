"""PARAM rows excused from the bounds comparison (DL-276 D4): none.

Agent: tooling
Role: record exact Type cells, allowing this list only to shrink.
External I/O: none.
"""

# Empty since S259 (2026-10-08): the eight rows S258 recorded here were rewritten to the
# code's bounds. An entry excuses a bounds disagreement only while the row's Type cell
# equals the recorded text; a changed or reconciled row fails the gate. A test holds the
# list empty, so adding an entry is a recorded decision, never a quiet edit.
EXCUSED_BOUNDS: dict[str, str] = {}
