"""Celery-backed message bus for distributed agent requests.

Agent: kernel
Role: adapt the MessageBus protocol to a Celery task backend.
External I/O: optional Celery broker/result backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict, cast

from celery import Celery

from kernel.config import AgentSettings, tunable
from kernel.envelope import AgentMessage
from kernel.errors import CollectingFaultSink, FaultSink, fault_boundary
from kernel.metrics import Metrics, NullMetrics, request_metric

if TYPE_CHECKING:
    from kernel.bus import MessageHandler


class CeleryBusSettings(AgentSettings):
    """Infrastructure settings for the Celery message bus."""

    celery_broker_url: str = tunable(
        "memory://", why="Default broker keeps local tests infra-free in eager mode."
    )
    celery_result_backend: str = tunable(
        "cache+memory://",
        why="In-memory result backend is enough for eager tests; override for Redis.",
    )
    celery_task_always_eager: bool = tunable(
        True,
        why="Default to synchronous local dispatch so the unit gate needs no broker.",
    )
    celery_task_eager_propagates: bool = tunable(
        False,
        why="Let the bus convert task faults into error envelopes like InProcessBus.",
    )
    celery_request_timeout_seconds: float = tunable(
        30.0,
        why="Bound distributed waits while leaving room for local worker startup lag.",
        ge=1.0,
        le=300.0,
        unit="seconds",
    )


class TaskError(TypedDict):
    """Serialized task error payload."""

    error_type: str
    message: str


class TaskResult(TypedDict, total=False):
    """Serialized task result payload."""

    ok: dict[str, Any]
    error: TaskError


class CeleryBus:
    """Celery-backed bus with InProcessBus-compatible response semantics."""

    def __init__(
        self,
        sink: FaultSink | None = None,
        *,
        settings: CeleryBusSettings | None = None,
        app: Celery | None = None,
        metrics: Metrics | None = None,
    ) -> None:
        """Create a Celery bus with optional settings, sink, app, and metrics."""
        self._settings = settings if settings is not None else CeleryBusSettings()
        self.sink = sink if sink is not None else CollectingFaultSink()
        self.metrics = metrics if metrics is not None else NullMetrics()
        self._handlers: dict[tuple[str, str], MessageHandler] = {}
        self._app = app if app is not None else self._build_app()
        self._dispatch_task = self._register_dispatch_task()

    def register(
        self, recipient: str, capability: str, handler: MessageHandler
    ) -> None:
        """Register a handler for one recipient capability."""
        self._handlers[(recipient, capability)] = handler

    def request(self, message: AgentMessage) -> AgentMessage:
        """Dispatch a request through Celery and return a response or error."""
        with request_metric(
            self.metrics, message.recipient, message.capability
        ) as metric:
            if (message.recipient, message.capability) not in self._handlers:
                return self._error_message(
                    message,
                    error_type="UnknownCapability",
                    text=(
                        "No handler registered for "
                        f"{message.recipient}.{message.capability}"
                    ),
                )
            result = self._dispatch(message)
            if error := result.get("error"):
                return self._error_message(
                    message, error_type=error["error_type"], text=error["message"]
                )
            metric.ok = True
            return AgentMessage(
                sender=message.recipient,
                recipient=message.sender,
                message_type="response",
                capability=message.capability,
                payload=result.get("ok", {}),
                correlation_id=message.id,
            )

    def _build_app(self) -> Celery:
        app = Celery(
            "trading_agents_bus",
            broker=self._settings.celery_broker_url,
            backend=self._settings.celery_result_backend,
        )
        app.conf.update(
            task_always_eager=self._settings.celery_task_always_eager,
            task_eager_propagates=self._settings.celery_task_eager_propagates,
            task_store_eager_result=True,
            task_serializer="json",
            result_serializer="json",
            accept_content=("json",),
        )
        return app

    def _register_dispatch_task(self) -> Any:  # noqa: ANN401 - Celery Task is dynamic.
        @self._app.task(name="kernel.bus_celery.dispatch")  # type: ignore[untyped-decorator]
        def dispatch(
            recipient: str, capability: str, payload: dict[str, Any]
        ) -> TaskResult:
            handler = self._handlers.get((recipient, capability))
            if handler is None:
                return {
                    "error": {
                        "error_type": "UnknownCapability",
                        "message": (
                            f"No handler registered for {recipient}.{capability}"
                        ),
                    }
                }
            out: dict[str, Any] = {}
            with fault_boundary(
                self.sink,
                agent=recipient,
                module="kernel.bus_celery",
                capability=capability,
                reraise=False,
            ) as capture:
                out = handler(payload)
            if capture.fault is not None:
                return {
                    "error": {
                        "error_type": capture.fault.error_type,
                        "message": capture.fault.message,
                    }
                }
            return {"ok": out}

        return cast("Any", dispatch)

    def _dispatch(self, message: AgentMessage) -> TaskResult:
        async_result = self._dispatch_task.apply_async(
            args=[message.recipient, message.capability, message.payload]
        )
        return cast(
            "TaskResult",
            async_result.get(timeout=self._settings.celery_request_timeout_seconds),
        )

    @staticmethod
    def _error_message(
        message: AgentMessage, *, error_type: str, text: str
    ) -> AgentMessage:
        return AgentMessage(
            sender=message.recipient,
            recipient=message.sender,
            message_type="error",
            capability=message.capability,
            payload={"error_type": error_type, "message": text},
            correlation_id=message.id,
        )
