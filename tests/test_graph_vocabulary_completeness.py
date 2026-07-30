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

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vocabulary_coverage import scan  # noqa: E402
from vocabulary_signatures import signatures  # noqa: E402

from kernel.graph_vocabulary import Vocabulary, VocabularyError  # noqa: E402

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


def test_fill_tolerance_props_are_declared_and_unknown_prop_fails() -> None:
    """EXEC-OBS-01 / DL-70: S149 Fill props are vocabulary-declared."""
    vocabulary = Vocabulary.from_mapping(_declaration())
    props = {
        "order_tolerance_mode": "flat",
        "order_applied_tolerance_bps": 50,
        "order_counterfactual_limit_price_cents": 10150,
        "position_ref": "position:AMD",
        "stop_order_key": "stop:AMD",
        "stop_pct": 0.05,
        "stop_pct_source": "position",
    }

    vocabulary.check_node("Fill", props=props)
    with pytest.raises(VocabularyError, match="undeclared properties"):
        vocabulary.check_node("Fill", props={**props, "order_tolerence_mode": "flat"})


def test_recommendation_stop_target_props_are_declared_and_unknown_prop_fails() -> None:
    """ANLZ-OBS-01 / DL-70: S150 Recommendation props are vocabulary-declared."""
    vocabulary = Vocabulary.from_mapping(_declaration())
    props = {
        "ticker": "MRVL",
        "action": "buy",
        "confidence": 0.8,
        "technical_score": 0.7,
        "stop_target_mode": "scaled",
        "stop_target_applied_stop_pct": 0.08,
        "stop_target_counterfactual_stop_pct": 0.05,
        "stop_target_observed_drawdown_pct": 0.06,
    }

    vocabulary.check_node("Recommendation", props=props)
    with pytest.raises(VocabularyError, match="undeclared properties"):
        vocabulary.check_node(
            "Recommendation", props={**props, "stop_targt_mode": "flat"}
        )
