"""Read the text a vendor SDK gives an API status error.

Agent: kernel
Role: split an SDK status-error string into its HTTP status and the vendor's message.
External I/O: none.
"""

from __future__ import annotations

import re

# The Anthropic and OpenAI SDKs both render an API status error as
# "Error code: <status> - <python dict of the body>". A caller that relays or
# records str(exc) has only that text, so the text is what is read here.
_VENDOR_ERROR = re.compile(
    r"^Error code: (?P<status>\d{3}) - "
    r".*?['\"]message['\"]: (?P<quote>['\"])(?P<message>.*?)(?P=quote)",
    re.DOTALL,
)


def vendor_status_error(text: str) -> tuple[str, str] | None:
    """Return (HTTP status, the vendor's message) for a status error, else None."""
    match = _VENDOR_ERROR.match(text)
    if match is None:
        return None
    return match["status"], match["message"]
