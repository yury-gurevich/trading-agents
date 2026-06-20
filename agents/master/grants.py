"""Default capability grants issued by master per agent type.

Agent: master
Role: declare the minimum-privilege capability grants for each known agent type.
External I/O: none.
"""

from __future__ import annotations

# Grants describe the functional interface, never a product name.
# Key Vault secrets are resolved at runtime and injected separately in S74.
DEFAULT_GRANTS: dict[str, dict[str, object]] = {
    "scanner": {
        "messaging": {"operations": ["subscribe", "publish"]},
        "graph": {"operations": ["append_write"], "access": "own_labels_only"},
    },
    "analyst": {
        "messaging": {"operations": ["subscribe", "publish"]},
        "graph": {"operations": ["append_write"], "access": "own_labels_only"},
    },
    "portfolio_manager": {
        "messaging": {"operations": ["subscribe", "publish"]},
        "graph": {"operations": ["append_write"], "access": "own_labels_only"},
    },
    "execution": {
        "messaging": {"operations": ["subscribe", "publish"]},
        "graph": {"operations": ["append_write"], "access": "own_labels_only"},
        "broker": {"operations": ["submit", "cancel", "status"]},
    },
    "monitor": {
        "messaging": {"operations": ["subscribe", "publish"]},
        "graph": {"operations": ["append_write", "read"], "access": "own_and_read"},
    },
    "reporter": {
        "messaging": {"operations": ["subscribe", "publish"]},
        "graph": {"operations": ["read", "append_write"], "access": "read_heavy"},
    },
    "forecaster": {
        "messaging": {"operations": ["subscribe", "publish"]},
        "graph": {"operations": ["append_write"], "access": "own_labels_only"},
    },
    "operator": {
        "messaging": {"operations": ["request"]},
        "graph": {"operations": ["append_write", "read"]},
        "llm": {"operations": ["complete"]},
    },
    "supervisor": {
        "messaging": {"operations": ["subscribe", "publish", "request"]},
        "graph": {"operations": ["append_write", "read"]},
    },
    "curator": {
        "messaging": {"operations": ["subscribe", "publish"]},
        "graph": {"operations": ["append_write", "read"]},
    },
    "researcher": {
        "messaging": {"operations": ["subscribe", "publish"]},
        "graph": {"operations": ["append_write", "read"]},
    },
    "provider": {
        "messaging": {"operations": ["subscribe", "publish"]},
        "graph": {"operations": ["append_write"], "access": "own_labels_only"},
        "data_feeds": {"operations": ["ohlcv", "fundamentals", "news", "sentiment"]},
    },
}
