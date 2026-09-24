"""Plain operator wording for vendor API errors relayed as text.

Agent: surfaces
Role: turn an SDK status-error string into one sentence an operator can read.
External I/O: none.
"""

from __future__ import annotations

import re

# The Anthropic and OpenAI SDKs both render an API status error as
# "Error code: <status> - <python dict of the body>". It reaches the surface as
# text (the operator relays str(exc) over the bus), so the text is all there is.
_VENDOR_ERROR = re.compile(
    r"^Error code: (?P<status>\d{3}) - "
    r".*?['\"]message['\"]: (?P<quote>['\"])(?P<message>.*?)(?P=quote)",
    re.DOTALL,
)


def plain_error(text: str) -> str:
    """Return a vendor status error as one sentence; any other text unchanged."""
    match = _VENDOR_ERROR.match(text)
    if match is None:
        return text
    return (
        f"The language model refused the request (HTTP {match['status']}): "
        f"{match['message']}"
    )
