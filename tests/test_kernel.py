"""Kernel plumbing tests — the message envelope and contract descriptors."""

from __future__ import annotations

import uuid

import pytest
from pydantic import BaseModel, ValidationError

from kernel import AgentContract, AgentMessage, Capability


class _Req(BaseModel):
    pass


class _Resp(BaseModel):
    pass


def test_request_envelope_is_valid():
    msg = AgentMessage(
        sender="scanner",
        recipient="analyst",
        message_type="request",
        capability="analyze",
    )
    assert msg.correlation_id is None
    assert isinstance(msg.id, uuid.UUID)


def test_sender_and_recipient_must_differ():
    with pytest.raises(ValidationError):
        AgentMessage(
            sender="scanner",
            recipient="scanner",
            message_type="request",
            capability="analyze",
        )


def test_request_must_not_carry_correlation_id():
    with pytest.raises(ValidationError):
        AgentMessage(
            sender="scanner",
            recipient="analyst",
            message_type="request",
            capability="analyze",
            correlation_id=uuid.uuid4(),
        )


def test_response_must_carry_correlation_id():
    with pytest.raises(ValidationError):
        AgentMessage(
            sender="analyst",
            recipient="scanner",
            message_type="response",
            capability="analyze",
        )


def test_capability_must_be_non_empty():
    with pytest.raises(ValidationError):
        AgentMessage(
            sender="scanner",
            recipient="analyst",
            message_type="request",
            capability="   ",
        )


def test_contract_capability_lookup():
    contract = AgentContract(
        name="x",
        version="0.1.0",
        mission="m",
        consumes=(Capability("do", "does", request=_Req, response=_Resp),),
        never=("nothing",),
        owns_graph=("XNode",),
    )
    assert contract.capability("do").response is _Resp
    with pytest.raises(KeyError):
        contract.capability("missing")
