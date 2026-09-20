"""Default HTTPS sender for the dispatcher Telegram port.

Agent: orchestration
Role: issue one bounded Telegram JSON request.
External I/O: Telegram HTTPS.
"""

from __future__ import annotations

import json
from urllib.request import Request, urlopen


def send_request(
    api_token: str, method: str, payload: dict[str, object], timeout: float
) -> object:
    """Post one JSON payload to the selected Telegram bot method."""
    request = Request(
        f"https://api.telegram.org/bot{api_token}/{method}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))
