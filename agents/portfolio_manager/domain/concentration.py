"""Compatibility import for the split Portfolio Manager concentration book.

Agent: portfolio_manager
Role: keep older imports stable after S184 split sector/correlation logic.
External I/O: none.
"""

from __future__ import annotations

from agents.portfolio_manager.domain.sector_book import SectorBook

__all__ = ["SectorBook"]
