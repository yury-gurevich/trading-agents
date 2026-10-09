"""Fresh-process import proof with the optional Azure SDK refused.

Agent: tooling
Role: prove A10's lazy import even when the optional SDK cannot be imported.
External I/O: none.
"""

from __future__ import annotations

import builtins
import importlib
import sys

_ORIGINAL = builtins.__import__


def guarded_import(name, *args, **kwargs):
    if name == "azure.servicebus" or name.startswith("azure.servicebus."):
        raise ImportError("Azure Service Bus SDK is unavailable")
    return _ORIGINAL(name, *args, **kwargs)


def main():
    builtins.__import__ = guarded_import
    importlib.import_module("scripts.debate_lanes_live")
    assert not any(n.startswith("azure.servicebus") for n in sys.modules)
    print("live module imported; Azure Service Bus modules: 0")


if __name__ == "__main__":
    main()
