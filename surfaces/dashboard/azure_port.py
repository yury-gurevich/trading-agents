"""Azure dashboard read port — one narrow boundary for fleet infrastructure.

Agent: surfaces
Role: describe Azure reads without coupling projections to REST or Azure SDKs.
External I/O: none; live implementations are injected by the composition root.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime

AzureRow = dict[str, object]


class AzureReadError(RuntimeError):
    """A sanitized Azure read failure safe to expose as degraded status."""

    def __init__(self, public_message: str) -> None:
        """Carry the display-safe message as a structured attribute.

        Projections must render ``public_message`` (never ``str(exc)``) so no
        exception-text flow ever reaches an HTTP response.
        """
        super().__init__(public_message)
        self.public_message = public_message


class AzureReader(Protocol):
    """Read-only Azure facts used by the dashboard projections."""

    def list_container_apps(self) -> list[AzureRow]:
        """Return app names, images, current replicas, and provisioning state."""
        ...  # pragma: no cover - protocol declaration only.

    def list_job_executions(self, job: str) -> list[AzureRow]:
        """Return recent executions for one Container Apps job."""
        ...  # pragma: no cover - protocol declaration only.

    def job_template_image(self, job: str) -> str:
        """Return the configured image for the next job execution."""
        ...  # pragma: no cover - protocol declaration only.

    def query_logs(
        self, container: str, start: datetime, end: datetime, tail: int
    ) -> list[AzureRow]:
        """Return a bounded chronological Log Analytics excerpt."""
        ...  # pragma: no cover - protocol declaration only.

    def query_costs(self, scope: str, month_to_date: bool) -> list[AzureRow]:
        """Return Cost Management totals grouped by Azure service."""
        ...  # pragma: no cover - protocol declaration only.
