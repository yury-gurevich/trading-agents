"""Azure job-template image read tests.

Agent: surfaces
Role: cover dispatcher job template reads and degraded projection errors.
External I/O: none; Azure senders and readers are fakes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, cast

from surfaces.dashboard import azure_rest
from surfaces.dashboard.projections_azure import job_template_image
from surfaces.tests.test_dashboard_azure_rest import _settings

if TYPE_CHECKING:
    from surfaces.dashboard.azure_port import AzureReader

_FIXTURES = Path(__file__).parent / "fixtures"


def test_rest_reader_reads_job_template_image() -> None:
    calls: list[tuple[str, str, str, object]] = []

    def send(method: str, url: str, scope: str, body: object) -> dict[str, object]:
        calls.append((method, url, scope, body))
        return cast(
            "dict[str, object]",
            json.loads(
                (_FIXTURES / "azure_job_template.json").read_text(encoding="utf-8")
            ),
        )

    reader = azure_rest.AzureRestReader(_settings(), send=send)

    assert reader.job_template_image("dispatcher cron").endswith(":s123")
    assert "/jobs/dispatcher%20cron?api-version=" in calls[0][1]


def test_job_template_projection_generic_failure_is_unverified() -> None:
    class BrokenReader:
        def job_template_image(self, job: str) -> str:
            del job
            raise ValueError("unparseable")

    image, message = job_template_image(
        cast("AzureReader", BrokenReader()), "dispatcher"
    )

    assert image is None
    assert message == "Azure job template unavailable"
