"""The why of a container alarm: one line of the replica's own console, made safe.

Agent: orchestration
Role: choose the console line that explains an alarm, and strip what must not leave.
External I/O: none.

Lines of one traceback share a timestamp, so "the last line" is not the error: the
line is chosen by its shape. A container's closing line naming a failed close comes
first, then an exception line, then the line saying it was told to stop (DL-297).
A failure of the platform itself has no replica and so no console: its why is the
platform's own reason and message (DL-301 amendment 7).
"""

from __future__ import annotations

import re
from datetime import timedelta
from typing import TYPE_CHECKING

from orchestration.container_events import PLATFORM_KINDS

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from orchestration.container_events import ContainerEvent

LINE_WINDOW = timedelta(minutes=15)  # how far before an alarm its line may be
_LINE_AFTER = timedelta(minutes=1)  # the platform stamps an exit after its last line
LINE_LIMIT = 160
_CLOSING = re.compile(r"\] stopped on \S+ after .*; exit [1-9]")
_EXCEPTION = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)\b")
_SIGNAL = re.compile(r"\] stop signal \S+:")
_SHAPES = (_CLOSING, _EXCEPTION, _SIGNAL)
_URL_CREDENTIAL = re.compile(r"(\w+://)[^/\s:@]+:[^@\s]+@")
_BEARER = re.compile(r"(?i)\bbearer\s+\S+")
_NAMED_SECRET = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|token|apikey|api_key|key|sig|signature"
    r"|sharedaccesskey|accountkey|access_token|client_secret)(\s*[=:]\s*)"
    r"[^\s;&'\",]+"
)
_LONG_RUN = re.compile(r"[A-Za-z0-9+/=_\-]{32,}")
_AMOUNT = re.compile(
    r"\$\s?\d[\d,]*(?:\.\d+)?|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|\b\d+\.\d{2}\b"
)


def choose_line(lines: Sequence[tuple[datetime, str]], occurred: datetime) -> str:
    """Return the safe line that explains an alarm at ``occurred``, or ``""``."""
    inside = [
        (at, text)
        for at, text in lines
        if occurred - LINE_WINDOW <= at <= occurred + _LINE_AFTER
    ]
    for shape in _SHAPES:
        matching = [(at, text) for at, text in inside if shape.search(text)]
        if matching:
            return safe_line(max(matching, key=lambda item: item[0])[1])
    return ""


def platform_why(event: ContainerEvent) -> str:
    """Return the platform's own words for a platform failure, made safe; else ''."""
    if event.kind not in PLATFORM_KINDS:
        return ""
    return safe_line(f"{event.reason}: {event.message}")


def safe_line(text: str) -> str:
    """Return one line with credentials, long tokens and amounts masked, and cut."""
    line = " ".join(text.split())
    line = _URL_CREDENTIAL.sub(r"\1***@", line)
    line = _BEARER.sub("Bearer ***", line)
    line = _NAMED_SECRET.sub(r"\1\2***", line)
    line = _LONG_RUN.sub("***", line)
    line = _AMOUNT.sub("#", line)
    return line if len(line) <= LINE_LIMIT else line[: LINE_LIMIT - 1] + "…"
