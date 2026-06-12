"""Curator dataset-store ports and a deterministic in-memory store.

Agent: curator
Role: isolate curated-dataset writes behind a DatasetStore boundary.
External I/O: writes curated dataset payloads to the configured store.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Mapping


class DatasetStore(Protocol):
    """Boundary for all curator-owned curated-dataset writes."""

    def write(self, dataset_id: str, payload: Mapping[str, Any]) -> None:
        """Persist one curated dataset payload, keyed by dataset_id."""
        ...  # pragma: no cover - protocol declaration only.


class FakeDatasetStore:
    """In-memory store used by the unit gate; payloads inspectable via .written."""

    def __init__(self) -> None:
        """Create an empty in-memory dataset store."""
        self.written: dict[str, Mapping[str, Any]] = {}

    def write(self, dataset_id: str, payload: Mapping[str, Any]) -> None:
        """Record one curated dataset payload under its dataset_id."""
        self.written[dataset_id] = payload
