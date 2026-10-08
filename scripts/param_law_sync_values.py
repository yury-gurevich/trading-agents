"""Read PARAM Value cells using the default's type (DL-276 D1).

Agent: tooling
Role: compare law values as decimals, strings, booleans, dates or unset values.
External I/O: none; operates on cells and declared defaults only.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation


def decimal_number(text: str) -> Decimal:
    """Read grouped decimal numbers without binary float comparisons."""
    value = Decimal(text.replace(",", "").replace("_", ""))
    if not value.is_finite():
        raise ValueError("non-finite number")
    return value


def value_problem(cell: str, default: object) -> str | None:
    """Return one attributed comparison detail, never silently skip a value."""
    text = cell.strip().strip("`").strip()
    try:
        agrees = _agrees(text, default)
    except (InvalidOperation, ValueError) as exc:
        return (
            f"Value cell {cell!r} could not be compared with code default "
            f"{default!r}: {exc}"
        )
    if agrees:
        return None
    return f"law Value {cell!r} differs from code default {default!r}"


def _agrees(text: str, default: object) -> bool:
    if text in {"-", "—", "\N{EN DASH}"}:
        if default is None or default == "":
            return True
        raise ValueError("dash only represents None or an empty string")
    if default is None:
        if text.lower() in {"none", "null", "unset", "empty"}:
            return True
        raise ValueError("expected an unset value")
    if isinstance(default, bool):
        if text.lower() not in {"true", "false"}:
            raise ValueError("expected true or false")
        return (text.lower() == "true") == default
    if isinstance(default, (int, float, Decimal)):
        literal = re.fullmatch(r'Decimal\("([^"]+)"\)', text)
        return decimal_number(literal[1] if literal else text) == decimal_number(
            str(default)
        )
    if isinstance(default, date):
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) is None:
            raise ValueError("expected an ISO date in YYYY-MM-DD form")
        return date.fromisoformat(text) == default
    if isinstance(default, str):
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        elif text == "empty":
            text = ""
        return text == default
    raise ValueError(f"unsupported default type {type(default).__name__}")
