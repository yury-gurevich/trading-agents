"""Read the complete PARAM Type bounds set (DL-276 D2).

Agent: tooling
Role: compare inclusive and exclusive rails using exact decimal numbers.
External I/O: none; reads Type cells and Pydantic metadata already in memory.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from scripts.param_law_sync_values import decimal_number

if TYPE_CHECKING:
    from decimal import Decimal

    from pydantic.fields import FieldInfo

_NUMBER = r"[+-]?(?:\d[\d_]*(?:,\d{3})*(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_COMPARISON = re.compile(rf"(>=|≥|>|<=|≤|<)\s*({_NUMBER})")
_INTERVAL = re.compile(rf"(?<![\w])([\[(])\s*({_NUMBER})\s*,\s*({_NUMBER})\s*([\])])")
_OPERATORS = {">=": "ge", "≥": "ge", ">": "gt", "<=": "le", "≤": "le", "<": "lt"}
_BOUND_KEYS = ("ge", "gt", "le", "lt")


def law_bounds(cell: str) -> dict[str, Decimal]:
    """Read only numeric rails; generic type brackets and units are not rails."""
    bounds = {
        _OPERATORS[match[1]]: decimal_number(match[2])
        for match in _COMPARISON.finditer(cell)
    }
    for match in _INTERVAL.finditer(cell):
        bounds["ge" if match[1] == "[" else "gt"] = decimal_number(match[2])
        bounds["le" if match[4] == "]" else "lt"] = decimal_number(match[3])
    return bounds


def code_bounds(info: FieldInfo) -> dict[str, Decimal]:
    """Read the field's rails without constructing settings or consulting .env."""
    bounds = {}
    for metadata in info.metadata:
        for key in _BOUND_KEYS:
            value = getattr(metadata, key, None)
            if value is not None:
                bounds[key] = decimal_number(str(value))
    return bounds


def bounds_text(bounds: dict[str, Decimal]) -> str:
    return (
        ", ".join(f"{key}={value}" for key, value in sorted(bounds.items())) or "none"
    )
