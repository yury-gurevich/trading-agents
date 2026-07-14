"""Dashboard Azure bundle and single-container log projection tests.

Agent: surfaces
Role: prove real-shaped images/logs, run windows, bounds, and degraded results.
External I/O: none; AzureReader is fake.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

from surfaces.dashboard.bundle_azure import bundle_artifacts, container_logs
from surfaces.tests.dashboard_fakes import FakeAzureReader
from surfaces.tests.test_dashboard_costs import _settings

NOW = datetime(2026, 7, 10, 12, tzinfo=UTC)


def test_bundle_has_per_container_logs_and_real_image_tags() -> None:
    azure = FakeAzureReader()
    logs, images = bundle_artifacts(azure, _settings(), "2026-07-09")
    log_rows = cast("dict[str, list[object]]", logs["containers"])
    image_rows = cast("dict[str, dict[str, str]]", images["containers"])
    assert logs["available"] is True
    assert set(log_rows) == {"master", "execution", "sleeping", "dispatcher-cron"}
    assert image_rows["execution"]["tag"] == "s123"
    assert len(azure.log_calls) == 4
    assert all(call[3] == 40 for call in azure.log_calls)
    assert cast("dict[str, str]", logs["window"])["end"].startswith("2026-07-10")


def test_bundle_partial_log_failure_and_unavailable_mode() -> None:
    logs, images = bundle_artifacts(
        FakeAzureReader(fail_logs_for="execution"), _settings(), "2026-07-09"
    )
    assert logs["available"] is False
    assert cast("dict[str, str]", logs["errors"])["execution"]
    assert images["available"] is True
    missing_logs, missing_images = bundle_artifacts(None, _settings(), "2026-07-09")
    assert missing_logs["available"] is False
    assert missing_images["available"] is False
    no_day, _ = bundle_artifacts(FakeAzureReader(), _settings(), "")
    assert no_day["available"] is False
    failed_apps, failed_images = bundle_artifacts(
        FakeAzureReader(fail_apps=True), _settings(), "2026-07-09"
    )
    assert failed_apps["available"] is False
    assert failed_images["available"] is False


class NoJobsReader(FakeAzureReader):
    def list_job_executions(self, job: str) -> list[dict[str, object]]:
        return []


def test_bundle_without_job_still_contains_app_evidence() -> None:
    logs, images = bundle_artifacts(NoJobsReader(), _settings(), "2026-07-09")
    assert logs["available"] is True
    assert "dispatcher-cron" not in cast("dict[str, object]", images["containers"])


def test_container_logs_run_day_scopes_window_and_bad_day_falls_back() -> None:
    scoped = container_logs(
        FakeAzureReader(), _settings(), "execution", 200, now=NOW, run_day="2026-07-08"
    )
    assert scoped["scope"] == "run"
    window = cast("dict[str, str]", scoped["window"])
    assert window["start"].startswith("2026-07-08T22:25")
    assert window["end"].startswith("2026-07-09T00:30")
    fallback = container_logs(
        FakeAzureReader(), _settings(), "execution", 200, now=NOW, run_day="not-a-day"
    )
    assert fallback["scope"] == "latest"


def test_single_container_logs_good_and_degraded() -> None:
    good = container_logs(FakeAzureReader(), _settings(), "execution", 200, now=NOW)
    assert good["available"] is True
    assert good["scope"] == "latest"
    assert len(cast("list[object]", good["rows"])) == 3
    failed = container_logs(
        FakeAzureReader(fail_logs_for="execution"),
        _settings(),
        "execution",
        200,
        now=NOW,
    )
    assert failed["available"] is False
    assert failed["rows"] == []
    absent = container_logs(None, _settings(), "execution", 200, now=NOW)
    assert absent["message"] == "Azure data unavailable"
