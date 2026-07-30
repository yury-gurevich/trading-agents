"""Declared graph vocabulary — a closed set of labels, edges, and who writes them.

Agent: kernel
Role: turn a declared vocabulary into a write-time check, so a mistyped label
      fails loudly instead of returning an empty result later (R007).
External I/O: none — callers supply the already-parsed mapping.

Deliberately domain-free (ADR-0012): the *mechanism* is substrate, the actual
labels are pack data. This module never names a trading concept.

Only constraints live here. There is no inference: nothing in this module ever
derives or writes a fact. An append-only store is evidence, and a derived row is
indistinguishable from an observed one at read time (R007 §5).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

EdgeSignature = tuple[str, str, str]
"""``(parent_label, edge_type, child_label)`` — one permitted edge shape."""


class VocabularyError(RuntimeError):
    """Raised when a write does not conform to the declared vocabulary."""


def _iterable(value: object) -> tuple[object, ...]:
    """Return *value* as a tuple, or empty when it is not a usable sequence."""
    if isinstance(value, str | bytes) or not isinstance(value, Iterable):
        return ()
    return tuple(value)


def _names(value: object) -> frozenset[str]:
    """Coerce a declared list of names into a frozen set of strings."""
    return frozenset(str(item) for item in _iterable(value))


def _pairs(value: object) -> tuple[tuple[str, object], ...]:
    """Return the items of a declared mapping, or empty when it is not one."""
    if not isinstance(value, Mapping):
        return ()
    return tuple((str(key), inner) for key, inner in value.items())


def _signatures(value: object) -> frozenset[EdgeSignature]:
    """Coerce declared ``[parent, edge, child]`` rows into edge signatures."""
    found: set[EdgeSignature] = set()
    for row in _iterable(value):
        parts = [str(part) for part in _iterable(row)]
        if len(parts) == 3:  # an edge signature is a triple
            found.add((parts[0], parts[1], parts[2]))
    return frozenset(found)


@dataclass(frozen=True)
class Vocabulary:
    """A closed graph vocabulary: what may be written, and by whom."""

    labels: frozenset[str]
    edge_types: frozenset[str]
    edge_signatures: frozenset[EdgeSignature]
    owners: Mapping[str, frozenset[str]]
    properties: Mapping[str, frozenset[str]]

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> Vocabulary:
        """Build a vocabulary from a parsed declaration (e.g. pack JSON)."""
        return cls(
            labels=_names(data.get("labels")),
            edge_types=_names(data.get("edge_types")),
            edge_signatures=_signatures(data.get("edge_signatures")),
            owners={
                str(writer): _names(labels)
                for writer, labels in _pairs(data.get("owners"))
            },
            properties={
                str(label): _names(names)
                for label, names in _pairs(data.get("properties"))
            },
        )

    def check_node(
        self, label: str, *, writer: str = "", props: Mapping[str, object] | None = None
    ) -> None:
        """Raise unless *label* is declared, and *writer* may create it.

        An unknown label is the typo case: without this it merges happily and the
        matching ``list_nodes`` returns an empty tuple forever.
        """
        if label not in self.labels:
            raise VocabularyError(
                f"undeclared node label {label!r} — "
                f"add it to the vocabulary or fix the spelling"
            )
        owned = self.owners.get(writer)
        if writer and owned is not None and label not in owned:
            raise VocabularyError(
                f"{writer!r} may not write label {label!r}; it declared {sorted(owned)}"
            )
        declared = self.properties.get(label)
        if declared is not None and props is not None:
            unknown = set(props) - set(declared)
            if unknown:
                raise VocabularyError(
                    f"undeclared properties for label {label!r}: {sorted(unknown)}"
                )

    def check_edge(self, parent_label: str, edge_type: str, child_label: str) -> None:
        """Raise unless the edge type is declared and this shape is permitted."""
        if edge_type not in self.edge_types:
            raise VocabularyError(
                f"undeclared edge type {edge_type!r} — "
                f"add it to the vocabulary or fix the spelling"
            )
        if not self.edge_signatures:
            return
        signature = (parent_label, edge_type, child_label)
        if signature not in self.edge_signatures:
            raise VocabularyError(
                f"edge {edge_type!r} is not declared to run "
                f"{parent_label} -> {child_label}"
            )
