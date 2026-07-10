"""Azure REST reader tests — injection, caching, URLs, and sanitized failures.

Agent: surfaces
Role: verify the live read adapter without making network or credential calls.
External I/O: none; senders, credentials, clocks, and openers are fakes.
"""

from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, cast
from urllib.error import HTTPError, URLError

import pytest

import surfaces.dashboard.azure_http as azure_http
import surfaces.dashboard.azure_rest as azure_rest
from surfaces.dashboard.azure_http import AzureIdentitySend
from surfaces.dashboard.azure_port import AzureReadError
from surfaces.dashboard.settings import DashboardSettings

_FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> dict[str, object]:
    return cast(
        "dict[str, object]",
        json.loads((_FIXTURES / name).read_text(encoding="utf-8")),
    )


def _settings(**updates: object) -> DashboardSettings:
    base = DashboardSettings.model_construct(
        azure_subscription_id="sub id",
        azure_resource_group="trading agents",
        azure_workspace_id="workspace id",
        azure_environment_name="trading-agents-env",
        azure_job_name="dispatcher-cron",
        azure_timeout_seconds=5.0,
        azure_credential_mode="auto",
        fleet_cache_ttl_seconds=30.0,
        cost_cache_ttl_seconds=300.0,
        log_tail_default=200,
        log_tail_max=500,
        bundle_log_tail=40,
        master_window_start_utc="22:25",
        agent_window_start_utc="22:30",
        window_end_utc="00:30",
        dispatcher_fire_utc="22:30",
    )
    return base.model_copy(update=updates)


class FakeSend:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, object]] = []

    def __call__(
        self, method: str, url: str, scope: str, body: object
    ) -> dict[str, object]:
        self.calls.append((method, url, scope, body))
        if "/replicas" in url:
            if "execution--" in url:
                raise AzureReadError("replica read unavailable")
            return {"value": [{"name": "replica"}]}
        if "/containerApps?" in url:
            return _fixture("azure_container_apps.json")
        if "/executions?" in url:
            return _fixture("azure_job_executions.json")
        if "loganalytics" in url:
            return _fixture("azure_log_rows.json")
        return _fixture("azure_cost_rows.json")


def test_reader_lists_apps_and_caches_replica_reads() -> None:
    now = [10.0]
    sender = FakeSend()
    reader = azure_rest.AzureRestReader(_settings(), send=sender, clock=lambda: now[0])
    rows = reader.list_container_apps()
    assert [row["replicas"] for row in rows] == [1, None, None]
    assert "sub%20id" in sender.calls[0][1]
    assert "trading%20agents" in sender.calls[0][1]
    assert len(sender.calls) == 3
    rows[0]["replicas"] = 99
    assert reader.list_container_apps()[0]["replicas"] == 1
    assert len(sender.calls) == 3
    now[0] = 40.0
    reader.list_container_apps()
    assert len(sender.calls) == 6


def test_reader_jobs_logs_and_cost_cache() -> None:
    now = [1.0]
    sender = FakeSend()
    reader = azure_rest.AzureRestReader(_settings(), send=sender, clock=lambda: now[0])
    jobs = reader.list_job_executions("dispatcher cron")
    assert jobs[0]["status"] == "Succeeded"
    assert "dispatcher%20cron" in sender.calls[-1][1]
    assert reader.list_job_executions("dispatcher cron") == jobs
    start = __import__("datetime").datetime.fromisoformat("2026-07-09T22:25:00+00:00")
    end = __import__("datetime").datetime.fromisoformat("2026-07-10T00:30:00+00:00")
    logs = reader.query_logs("execu'tion", start, end, 17)
    assert len(logs) == 3
    log_body = cast("dict[str, str]", sender.calls[-1][3])
    assert "execu''tion" in log_body["query"]
    assert "take 17" in log_body["query"]
    scope = "/subscriptions/sub/resourceGroups/rg"
    costs = reader.query_costs(scope, True)
    assert costs[0]["service"] == "Service Bus"
    costs[0]["cost"] = 999
    assert reader.query_costs(scope, True)[0]["cost"] == 5.83
    with pytest.raises(ValueError, match="month-to-date"):
        reader.query_costs(scope, False)


class _Credential:
    def get_token(self, scope: str) -> Any:
        return SimpleNamespace(token=f"token-for-{scope}")


class _Response(BytesIO):
    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def test_identity_sender_get_post_and_sanitized_errors() -> None:
    requests: list[Any] = []

    def opener(request: Any, *, timeout: float) -> _Response:
        requests.append((request, timeout))
        return _Response(b'{"ok": true}')

    sender = AzureIdentitySend(timeout=7.0, credential=_Credential(), opener=opener)
    assert sender("GET", "https://example.test/read", "scope", None) == {"ok": True}
    assert sender("POST", "https://example.test/read", "scope", {"x": 1}) == {
        "ok": True
    }
    assert requests[0][0].headers["Authorization"] == "Bearer token-for-scope"
    assert requests[1][0].headers["Content-type"] == "application/json"
    assert requests[1][1] == 7.0
    failures = [
        HTTPError("https://example.test", 403, "denied", cast("Any", {}), None),
        URLError("offline"),
        TimeoutError(),
    ]
    for failure in failures:
        bad = AzureIdentitySend(
            timeout=1.0,
            credential=_Credential(),
            opener=lambda *args, _failure=failure, **kwargs: (_ for _ in ()).throw(
                _failure
            ),
        )
        with pytest.raises(AzureReadError, match="Azure read failed"):
            bad("GET", "https://example.test/read", "scope", None)


def test_credential_selection_and_reader_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    identity = ModuleType("azure.identity")
    identity.ClientSecretCredential = lambda *args: ("sp", args)  # type: ignore[attr-defined]
    identity.DefaultAzureCredential = lambda: "default"  # type: ignore[attr-defined]
    identity.AzureCliCredential = lambda: "cli"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "azure", ModuleType("azure"))
    monkeypatch.setitem(sys.modules, "azure.identity", identity)
    monkeypatch.setenv("AZURE_SP_TENANT_ID", "tenant")
    monkeypatch.setenv("AZURE_SP_CLIENT_ID", "client")
    monkeypatch.setenv("AZURE_SP_CLIENT_SECRET", "secret")
    assert cast("Any", azure_http._credential_from_env()) == (
        "sp",
        ("tenant", "client", "secret"),
    )
    assert cast("Any", azure_http._credential_from_env("cli")) == "cli"
    assert cast("Any", azure_http._credential_from_env("default")) == "default"
    monkeypatch.delenv("AZURE_SP_CLIENT_SECRET")
    assert cast("Any", azure_http._credential_from_env()) == "default"
    with pytest.raises(AzureReadError, match="credential unavailable"):
        azure_http._credential_from_env("service_principal")
    assert azure_rest.build_azure_reader(_settings(azure_subscription_id="")) is None
    monkeypatch.setattr(
        azure_rest,
        "AzureIdentitySend",
        lambda **kwargs: (_ for _ in ()).throw(ImportError("azure missing")),
    )
    assert azure_rest.build_azure_reader(_settings()) is None
    monkeypatch.setattr(azure_rest, "AzureIdentitySend", lambda **kwargs: FakeSend())
    assert isinstance(
        azure_rest.build_azure_reader(_settings()), azure_rest.AzureRestReader
    )
