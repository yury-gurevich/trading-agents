"""Stable Position reference helpers.

Agent: contracts
Role: share deterministic Position identity across graph readers.
External I/O: none.
"""

from __future__ import annotations

import hashlib


def position_ref_for_keys(keys: tuple[str, ...]) -> str:
    """Return the stable aggregate position_ref for one or more Position keys."""
    joined = "\n".join(sorted(keys)).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()[:16]
