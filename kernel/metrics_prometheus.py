"""Prometheus metrics backend for the kernel observability adapter.

Agent: kernel
Role: adapt neutral metrics emissions to an in-memory Prometheus registry.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest
from pydantic_settings import SettingsConfigDict

from kernel.config import AgentSettings, tunable

if TYPE_CHECKING:
    from kernel.errors import AgentFault


class MetricsSettings(AgentSettings):
    """Prometheus naming settings for exported kernel metrics."""

    model_config = SettingsConfigDict(env_prefix="METRICS_", frozen=True)

    prometheus_namespace: str = tunable(
        "trading_agents",
        why="Keep this app's Prometheus series distinct from host/runtime metrics.",
    )
    prometheus_subsystem: str = tunable(
        "kernel",
        why="This sprint emits from kernel plumbing rather than agent domains.",
    )


class PrometheusMetrics:
    """Prometheus-backed Metrics implementation using a private registry."""

    def __init__(
        self,
        settings: MetricsSettings | None = None,
        registry: CollectorRegistry | None = None,
    ) -> None:
        """Create counters and histograms in an isolated CollectorRegistry."""
        self._settings = settings if settings is not None else MetricsSettings()
        self._registry = registry if registry is not None else CollectorRegistry()
        metric_options = {
            "namespace": self._settings.prometheus_namespace,
            "subsystem": self._settings.prometheus_subsystem,
            "registry": self._registry,
        }
        self._requests = Counter(
            "requests",
            "Bus requests handled by agent capability and outcome.",
            ("agent", "capability", "outcome"),
            **metric_options,
        )
        self._latency = Histogram(
            "request_latency_seconds",
            "Bus request latency by agent capability.",
            ("agent", "capability"),
            **metric_options,
        )
        self._faults = Counter(
            "faults",
            "Central fault-channel submissions by source and severity.",
            ("source_agent", "source_module", "severity"),
            **metric_options,
        )

    @property
    def registry(self) -> Any:  # noqa: ANN401 - prometheus registry is untyped.
        """Return the private registry for infra-free tests and exposition."""
        return self._registry

    def record_request(
        self, agent: str, capability: str, latency_s: float, *, ok: bool
    ) -> None:
        """Record one bus request outcome and observed latency."""
        outcome = "ok" if ok else "error"
        self._requests.labels(agent, capability, outcome).inc()
        self._latency.labels(agent, capability).observe(latency_s)

    def record_fault(self, fault: AgentFault) -> None:
        """Record one fault routed through the central fault channel."""
        self._faults.labels(
            fault.source_agent, fault.source_module, fault.severity
        ).inc()

    def exposition(self) -> bytes:
        """Render this registry in Prometheus text format."""
        return cast("bytes", generate_latest(self._registry))
