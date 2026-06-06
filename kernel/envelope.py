"""The transport-agnostic A2A message envelope.

Agent: kernel
Role: the typed envelope wrapping every inter-agent message (the audit unit).
External I/O: none.

Every inter-agent message is wrapped in an ``AgentMessage`` regardless of whether
it travels over the in-process bus (tests) or the Celery/Redis bus (runtime). The
envelope is the audit unit: persisting it gives append-only message lineage for
the provenance graph for free.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MessageType = Literal["request", "response", "notification", "error"]


class AgentMessage(BaseModel):
    """Typed envelope for one A2A communication."""

    model_config = ConfigDict(frozen=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    sent_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    sender: str
    """Agent name or 'operator' / 'scheduler'. Must match a registered actor."""

    recipient: str
    """Agent name."""

    message_type: MessageType
    capability: str
    """Capability this message exercises (must exist on the recipient's contract)."""

    payload: dict[str, Any] = Field(default_factory=dict)
    """The typed payload, serialized. Validated against the capability's model."""

    correlation_id: uuid.UUID | None = None
    """Thread id linking a response/error back to its originating request."""

    @model_validator(mode="after")
    def _validate(self) -> AgentMessage:
        if self.sender == self.recipient:
            raise ValueError("sender and recipient must differ")
        if self.message_type == "request" and self.correlation_id is not None:
            raise ValueError("request messages must not carry a correlation_id")
        if self.message_type in ("response", "error") and self.correlation_id is None:
            raise ValueError("response/error messages must carry a correlation_id")
        if not self.capability.strip():
            raise ValueError("capability must be non-empty")
        return self
