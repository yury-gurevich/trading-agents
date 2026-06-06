"""Operator LLM agent contract — human language into typed, policy-bound intents.

Agent: operator
Role: contract — typed boundary (capabilities, owned data, never-do).
External I/O: LLM provider.
"""

from __future__ import annotations

from typing import Literal

from contracts.common import Explanation, Provenance, _Frozen
from kernel.contract import AgentContract, Capability

IntentFamily = Literal[
    "status",
    "explain",
    "approve",
    "reject",
    "modify",
    "run",
    "mode",
    "stage",
    "pause",
    "resume",
]


# ── Inbound payloads ────────────────────────────────────────────────────────
class HumanCommand(_Frozen):
    text: str
    actor: str
    channel: Literal["dashboard", "phone", "mcp"]


class ExplainRequest(_Frozen):
    subject: str
    """e.g. 'why was AAPL rejected', 'why is the system in manual'."""


# ── Outbound payloads ───────────────────────────────────────────────────────
class TypedIntent(_Frozen):
    family: IntentFamily
    parameters: dict[str, str]
    requires_confirmation: bool
    provenance: Provenance


class CommandResult(_Frozen):
    outcome: Literal["intent", "refused", "needs_clarification"]
    intent: TypedIntent | None = None
    message: Explanation
    """Refusals and clarification requests are explained, never silent."""


CONTRACT = AgentContract(
    name="operator",
    version="0.1.0",
    mission=(
        "Translate the operator's human-language commands into typed, policy-bound "
        "intents; explain system state from stored evidence; refuse or escalate "
        "anything ambiguous or unsafe."
    ),
    consumes=(
        Capability(
            "interpret",
            "Map a human command to one typed intent, a refusal, or a clarification.",
            request=HumanCommand,
            response=CommandResult,
            mcp=True,
        ),
        Capability(
            "explain",
            "Produce an evidence-grounded plain-language explanation on demand.",
            request=ExplainRequest,
            response=Explanation,
            mcp=True,
        ),
    ),
    emits=("intent_parsed", "command_refused"),
    owns_graph=("CommandAudit", "Intent"),
    external_io=("llm_provider",),
    depends_on=("supervisor",),
    mcp_tools=("interpret", "explain"),
    never=(
        "invent trades outside the policy and data path",
        "bypass approval, stage, or capability gates",
        "submit broker actions directly",
        "mutate strategy parameters outside the approval and audit flow",
        "become a free-form open-ended trading advisor",
    ),
)
