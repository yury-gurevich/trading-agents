"""Vocabulary completeness — the pack must cover everything the code can write.

Agent: kernel
Role: prove the declared vocabulary is a superset of the labels, edge types and
      edge signatures reachable in shipped code.
External I/O: reads repo sources and the trading pack.

S143 derived the vocabulary from the live graph, so it could only ever contain
what had already happened. Broker-native stops then shipped two edges no run had
produced, and enabling the guard would have raised VocabularyError on the first
real stop. These tests move that discovery into `make ci` (S144).

The negative tests are the load-bearing ones. A completeness check that has
never been observed failing is indistinguishable from one that examines nothing
(DL-52, DL-65).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vocabulary_coverage import scan  # noqa: E402
from vocabulary_signatures import signatures  # noqa: E402

_PACK = ROOT / "orchestration" / "packs" / "trading_graph_vocabulary.json"

_PLANTED = '''"""Planted writer.

Agent: tooling
Role: exercise the completeness scan against names no pack declares.
External I/O: none.
"""


def write(graph: object) -> None:
    """Write one undeclared node pair and one undeclared edge."""
    run = graph.merge_node("PlantedRun", "k", {})
    item = graph.merge_node("PlantedItem", "k", {})
    graph.add_edge(item, run, "PLANTED_EDGE")
'''


def _declaration() -> dict[str, object]:
    data = json.loads(_PACK.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _declared(field: str) -> set[str]:
    values = _declaration()[field]
    assert isinstance(values, list)
    return {str(value) for value in values}


def _declared_signatures() -> set[tuple[str, ...]]:
    rows = _declaration()["edge_signatures"]
    assert isinstance(rows, list)
    return {tuple(str(part) for part in row) for row in rows}


def _plant(tmp_path: Path) -> Path:
    package = tmp_path / "planted"
    package.mkdir()
    (package / "writer.py").write_text(_PLANTED, encoding="utf-8")
    return tmp_path


def test_every_node_label_the_code_can_write_is_declared() -> None:
    undeclared = scan(ROOT).labels - _declared("labels")
    assert undeclared == set(), f"undeclared node labels: {sorted(undeclared)}"


def test_every_edge_type_the_code_can_write_is_declared() -> None:
    undeclared = scan(ROOT).edge_types - _declared("edge_types")
    assert undeclared == set(), f"undeclared edge types: {sorted(undeclared)}"


def test_every_recoverable_edge_signature_is_declared() -> None:
    """The dimension that bit: both stop labels and edge types were declared."""
    undeclared = signatures(ROOT) - _declared_signatures()
    assert undeclared == set(), f"undeclared edge signatures: {sorted(undeclared)}"


def test_the_broker_stop_signature_is_recovered_from_code() -> None:
    """Regression: this exact triple was missing and had never run in production."""
    assert ("Fill", "STOPS_WITH", "BrokerStopOrder") in signatures(ROOT)


def test_the_label_scan_detects_names_no_pack_declares(tmp_path: Path) -> None:
    written = scan(_plant(tmp_path), packages=("planted",))
    assert {"PlantedRun", "PlantedItem"} <= written.labels
    assert written.labels - _declared("labels") != set()
    assert written.edge_types - _declared("edge_types") == {"PLANTED_EDGE"}


def test_the_signature_scan_detects_a_shape_no_pack_declares(tmp_path: Path) -> None:
    found = signatures(_plant(tmp_path), packages=("planted",))
    assert ("PlantedItem", "PLANTED_EDGE", "PlantedRun") in found
    assert found - _declared_signatures() != set()
