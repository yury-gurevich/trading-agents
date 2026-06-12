"""Built-in market-pack declarations.

Agent: orchestration
Role: expose default pack definitions for surface wiring.
External I/O: none.
"""

from orchestration.packs.us_equities_sp500 import USEquitiesSP500Pack

__all__ = ["USEquitiesSP500Pack"]
