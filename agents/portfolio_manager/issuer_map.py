"""Issuer-map loader for Portfolio Manager pack data.

Agent: portfolio_manager
Role: parse and load the trading pack's ticker-to-issuer identity map.
External I/O: reads process environment and an optional local pack JSON file.
"""

from __future__ import annotations

import base64
import json
import os
from collections.abc import Mapping
from pathlib import Path

ISSUER_MAP_B64_ENV = "PORTFOLIO_MANAGER_ISSUER_MAP_B64"
ISSUER_MAP_PATH_ENV = "PORTFOLIO_MANAGER_ISSUER_MAP_PATH"
DEFAULT_ISSUER_MAP_PATH = "orchestration/packs/trading_issuer_map.json"

type IssuerMap = Mapping[str, str]


def parse_issuer_map(text: str) -> IssuerMap:
    """Parse ticker -> issuer-key pack data, normalizing ticker keys to uppercase."""
    raw: object = json.loads(text)
    if not isinstance(raw, dict):
        raise ValueError("issuer map must be a JSON object")
    parsed: dict[str, str] = {}
    for ticker, issuer in raw.items():
        if not isinstance(ticker, str) or not isinstance(issuer, str):
            raise ValueError("issuer map entries must be string -> string")
        parsed[ticker.upper()] = issuer
    return parsed


def load_issuer_map(path: str) -> IssuerMap:
    """Load issuer-map pack data from a JSON file path."""
    return parse_issuer_map(Path(path).read_text(encoding="utf-8"))


def load_issuer_map_from_env() -> IssuerMap:
    """Resolve pack data from base64 env content, then local path, then empty map."""
    b64 = os.environ.get(ISSUER_MAP_B64_ENV, "").strip()
    if b64:
        return parse_issuer_map(base64.b64decode(b64).decode("utf-8"))
    path = os.environ.get(ISSUER_MAP_PATH_ENV, DEFAULT_ISSUER_MAP_PATH).strip()
    if path and Path(path).exists():
        return load_issuer_map(path)
    return {}
