"""Plain operator wording for vendor API errors relayed as text.

Agent: surfaces
Role: turn an SDK status-error string into one sentence an operator can read.
External I/O: none.
"""

from __future__ import annotations

from kernel.llm_error_text import vendor_status_error


def plain_error(text: str) -> str:
    """Return a vendor status error as one sentence; any other text unchanged."""
    parsed = vendor_status_error(text)
    if parsed is None:
        return text
    status, message = parsed
    return f"The language model refused the request (HTTP {status}): {message}"
