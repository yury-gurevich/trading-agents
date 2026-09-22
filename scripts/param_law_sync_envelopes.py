"""Warning-only evidence-envelope checks for PARAM/settings synchronization.

Agent: tooling
Role: report settings values that sit outside their declared evidence envelopes.
External I/O: none; operates on already-loaded Pydantic settings metadata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo


def envelope_warnings(
    agent: str,
    fields: dict[str, FieldInfo],
) -> list[str]:
    """Return warning lines for fields whose defaults sit outside an envelope."""
    warnings: list[str] = []
    for name, info in fields.items():
        extra = (
            info.json_schema_extra if isinstance(info.json_schema_extra, dict) else {}
        )
        envelope = extra.get("envelope")
        if envelope is None:
            continue
        minimum, maximum = (float(value) for value in envelope)
        declared_default: Any = info.get_default()
        if minimum <= float(declared_default) <= maximum:
            continue
        warnings.append(
            f"[WARN] {agent}.{name} declared_default={declared_default} "
            f"envelope=({minimum}, {maximum}) source={extra['source']}"
        )
    return warnings
