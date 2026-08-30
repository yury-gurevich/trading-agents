"""Load pack-declared credential probes for master activation.

Agent: master
Role: turn credential-test JSON into injected CredentialTest callables without
      importing trading-pack code into the master image.
External I/O: optional HTTPS requests; optional PostgreSQL SELECT 1 for DSN probes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from agents.master.credential_probe_support import (
    bool_field,
    cost,
    int_field,
    render,
    render_url,
    required_str,
    status_set,
    str_dict,
)
from agents.master.credential_probe_transports import (
    default_dsn_select_1 as _default_dsn_select_1,
)
from agents.master.credential_probe_transports import (
    default_http_transport as _default_http_transport,
)
from agents.master.credential_result import (
    CheckResult,
    credential_failed,
    credential_passed,
    credential_transport_failed,
)
from agents.master.credential_test import CredentialTest

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

ProbeKind = Literal["http_status", "dsn_select_1"]


@dataclass(frozen=True)
class HttpProbeRequest:
    """Sanitized HTTP probe request passed to injected test transports."""

    method: str
    url: str
    headers: dict[str, str]
    timeout_seconds: int


def parse_credential_tests(
    text: str,
    *,
    http_transport: Callable[[HttpProbeRequest], int] | None = None,
    dsn_select_1: Callable[[str, int], CheckResult] | None = None,
) -> tuple[CredentialTest, ...]:
    """Parse pack JSON into credential tests, rejecting empty declarations."""
    raw = json.loads(text)
    if not isinstance(raw, dict):
        raise ValueError("credential test declaration must be an object")
    transport = http_transport or _default_http_transport
    dsn_probe = dsn_select_1 or _default_dsn_select_1
    tests: list[CredentialTest] = []
    for agent_type, entries in raw.items():
        if not isinstance(agent_type, str) or not isinstance(entries, list):
            raise ValueError("credential test declaration maps agent types to lists")
        for entry in entries:
            tests.append(_test_from_entry(agent_type, entry, transport, dsn_probe))
    if not tests:
        raise ValueError("credential test declaration is empty")
    return tuple(tests)


def load_credential_tests(
    path: str,
    *,
    http_transport: Callable[[HttpProbeRequest], int] | None = None,
    dsn_select_1: Callable[[str, int], CheckResult] | None = None,
) -> tuple[CredentialTest, ...]:
    """Load credential tests from a JSON file."""
    return parse_credential_tests(
        Path(path).read_text(encoding="utf-8"),
        http_transport=http_transport,
        dsn_select_1=dsn_select_1,
    )


def _test_from_entry(
    agent_type: str,
    entry: object,
    http_transport: Callable[[HttpProbeRequest], int],
    dsn_select_1: Callable[[str, int], CheckResult],
) -> CredentialTest:
    if not isinstance(entry, dict):
        raise ValueError(f"credential test for {agent_type} must be an object")
    name = required_str(entry, "name")
    kind = required_str(entry, "kind")
    required = bool_field(entry.get("required", True), "required")
    test_cost = cost(entry.get("cost", "cheap"))
    if kind == "http_status":
        run = _http_runner(entry, http_transport)
    elif kind == "dsn_select_1":
        run = _dsn_runner(entry, dsn_select_1)
    else:
        raise ValueError(f"unknown credential probe kind {kind!r} for {name!r}")
    return CredentialTest(
        name, run, required=required, cost=test_cost, agent_types=(agent_type,)
    )


def _http_runner(
    entry: dict[str, object], transport: Callable[[HttpProbeRequest], int]
) -> Callable[[Mapping[str, str]], CheckResult]:
    method = str(entry.get("method", "GET")).upper()
    url_template = required_str(entry, "url")
    headers = str_dict(entry.get("headers", {}), "headers")
    query = str_dict(entry.get("query", {}), "query")
    expected = status_set(entry.get("expected_statuses", [200]))
    failure_statuses = status_set(entry.get("credential_failure_statuses", [401, 403]))
    timeout_seconds = int_field(entry.get("timeout_seconds", 15), "timeout_seconds")

    def run(config: Mapping[str, str]) -> CheckResult:
        try:
            url = render_url(url_template, query, config)
            rendered_headers = {
                key: render(value, config) for key, value in headers.items()
            }
        except KeyError as exc:
            return credential_failed(f"missing_config:{exc.args[0]}")
        try:
            status = transport(
                HttpProbeRequest(method, url, rendered_headers, timeout_seconds)
            )
        except (TimeoutError, OSError) as exc:
            return credential_transport_failed(type(exc).__name__)
        if status in expected:
            return credential_passed()
        if status >= 500:
            return credential_transport_failed(f"http_{status}")
        if status in failure_statuses or 400 <= status < 500:
            return credential_failed(f"http_{status}")
        return credential_failed(f"http_{status}")

    return run


def _dsn_runner(
    entry: dict[str, object],
    dsn_select_1: Callable[[str, int], CheckResult],
) -> Callable[[Mapping[str, str]], CheckResult]:
    dsn_key = required_str(entry, "dsn")
    timeout_seconds = int_field(entry.get("timeout_seconds", 10), "timeout_seconds")

    def run(config: Mapping[str, str]) -> CheckResult:
        dsn = config.get(dsn_key, "")
        if not dsn:
            return credential_failed(f"missing_config:{dsn_key}")
        try:
            return dsn_select_1(dsn, timeout_seconds)
        except (TimeoutError, OSError) as exc:
            return credential_transport_failed(type(exc).__name__)

    return run
