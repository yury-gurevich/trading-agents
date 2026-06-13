"""Curator agent module-level helpers.

Agent: curator
Role: degraded-manifest and dataset-payload helpers, kept out of the thin agent.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.curator.domain.manifest import build_manifest
from agents.curator.domain.split import SplitAssignment
from agents.curator.settings import CuratorSettings

if TYPE_CHECKING:
    from contracts.curator import DatasetManifest


def degraded_manifest(purpose: str, dataset_id: str, version: int) -> DatasetManifest:
    """Build an empty-split manifest for a degraded dataset build."""
    return build_manifest(
        purpose=purpose,
        schema_ref=CuratorSettings().schema_ref,
        split=SplitAssignment((), (), ()),
        dataset_id=dataset_id,
        version=version,
    )


def dataset_payload(split: SplitAssignment) -> dict[str, dict[str, str]]:
    """Project a split into the dataset_store payload shape."""
    return {
        record.example_id: {
            "content": record.content,
            "label": record.label,
            "split": name,
            "source_ref": record.source_ref,
        }
        for name, records in (
            ("train", split.train),
            ("validation", split.validation),
            ("test", split.test),
        )
        for record in records
    }
