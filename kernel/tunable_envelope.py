"""Evidence-envelope validation for justified tunables.

Agent: kernel
Role: reject evidence bands that exceed their fields' declared safety rails.
External I/O: none.
"""

from __future__ import annotations


def validate_envelope(
    envelope: tuple[float, float] | None,
    source: str | None,
    *,
    ge: float | None,
    gt: float | None,
    le: float | None,
) -> None:
    """Reject an evidence envelope that includes a value a field would reject."""
    if envelope is not None and source is None:
        raise ValueError("An evidence envelope requires a source.")
    if envelope is None:
        return

    minimum, maximum = envelope
    if ge is not None and minimum < ge:
        raise ValueError(f"Evidence envelope {envelope} extends below ge={ge}.")
    if gt is not None and minimum <= gt:
        raise ValueError(
            f"Evidence envelope {envelope} extends below or equals gt={gt}."
        )
    if le is not None and maximum > le:
        raise ValueError(f"Evidence envelope {envelope} extends above le={le}.")
