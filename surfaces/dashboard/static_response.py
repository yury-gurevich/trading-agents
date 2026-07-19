"""Dashboard static-file responses.

Agent: surfaces
Role: serve the allowlisted frontend assets and inject dynamic dashboard config.
External I/O: reads committed static files.
"""

from __future__ import annotations

import json
import mimetypes
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from surfaces.dashboard.settings import DashboardSettings

StartResponse = Callable[..., Any]

_STATIC = Path(__file__).parent / "static"
# Allowlist computed at import: request paths are only ever dict keys, so no
# user input can reach a filesystem path or a response header.
_STATIC_FILES: dict[str, tuple[Path, str]] = {
    entry.name: (
        entry,
        mimetypes.guess_type(entry.name)[0] or "application/octet-stream",
    )
    for entry in _STATIC.iterdir()
    if entry.is_file()
}


def static_response(
    path: str, settings: DashboardSettings, start_response: StartResponse
) -> list[bytes]:
    """Serve one static asset, with settings injected into ``index.html``."""
    name = "index.html" if path == "/" else path.lstrip("/")
    entry = _STATIC_FILES.get(name)
    if entry is None:
        return _json(start_response, 404, {"error": f"not found {path}"})
    target, content_type = entry
    if name == "index.html":
        return _index(target, settings, start_response)
    start_response("200 OK", [("Content-Type", content_type)])
    return [target.read_bytes()]


def _index(
    target: Path, settings: DashboardSettings, start_response: StartResponse
) -> list[bytes]:
    ms = int(settings.self_heal_refetch_seconds * 1000)
    marker = "</head>"
    config = (
        "<script>window.dashboardConfig = "
        f"{json.dumps({'selfHealRefetchMs': ms})};</script>"
    )
    body = target.read_text(encoding="utf-8").replace(marker, f"  {config}\n{marker}")
    start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
    return [body.encode("utf-8")]


def _json(start_response: StartResponse, status: int, payload: object) -> list[bytes]:
    reason = {404: "Not Found"}[status]
    body = json.dumps(payload).encode("utf-8")
    start_response(
        f"{status} {reason}",
        [("Content-Type", "application/json; charset=utf-8")],
    )
    return [body]
