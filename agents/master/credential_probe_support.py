"""Pure helpers for master credential-probe declarations.

Agent: master
Role: validate and render pack-declared credential probe fields.
External I/O: none.
"""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True)
class HttpProbeRequest:
    """Sanitized HTTP probe request passed to injected test transports."""

    method: str
    url: str
    headers: dict[str, str]
    timeout_seconds: int


def render_url(
    url_template: str, query: dict[str, str], config: Mapping[str, str]
) -> str:
    """Render a URL and query templates against resolved activation config."""
    url = render(url_template, config)
    if not query:
        return url
    rendered = {key: render(value, config) for key, value in query.items()}
    separator = "&" if urllib.parse.urlparse(url).query else "?"
    return f"{url}{separator}{urllib.parse.urlencode(rendered)}"


def render(template: str, config: Mapping[str, str]) -> str:
    """Render one format template, raising KeyError for missing config names."""
    return template.format_map(_RequiredConfig(config))


class _RequiredConfig(dict[str, str]):
    def __missing__(self, key: str) -> str:
        raise KeyError(key)


def required_str(entry: dict[str, object], key: str) -> str:
    """Return a required non-empty string field from a probe declaration."""
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"credential probe field {key!r} must be a non-empty string")
    return value


def str_dict(value: object, field: str) -> dict[str, str]:
    """Return a string-to-string mapping from a probe declaration field."""
    if not isinstance(value, dict):
        raise ValueError(f"credential probe field {field!r} must be an object")
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
        raise ValueError(
            f"credential probe field {field!r} must map strings to strings"
        )
    return dict(value)


def status_set(value: object) -> set[int]:
    """Return a validated set of HTTP status codes."""
    if not isinstance(value, list) or not value:
        raise ValueError("credential probe statuses must be a non-empty list")
    if not all(isinstance(item, int) and not isinstance(item, bool) for item in value):
        raise ValueError("credential probe statuses must be integers")
    statuses = set(value)
    if not all(100 <= status <= 599 for status in statuses):
        raise ValueError("credential probe statuses must be HTTP status codes")
    return statuses


def int_field(value: object, field: str) -> int:
    """Return a required integer field from a probe declaration."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise ValueError(f"credential probe field {field!r} must be an integer")


def bool_field(value: object, field: str) -> bool:
    """Return a required boolean field from a probe declaration."""
    if isinstance(value, bool):
        return value
    raise ValueError(f"credential probe field {field!r} must be a boolean")


def cost(value: object) -> Literal["cheap", "costly"]:
    """Return a validated credential-test cost class."""
    if value in ("cheap", "costly"):
        return value
    raise ValueError("credential probe cost must be 'cheap' or 'costly'")
