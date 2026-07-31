"""Vocabulary property completeness — the dimension S144's suite did not prove.

Agent: kernel
Role: prove the declared vocabulary is a superset of the node properties
      reachable in shipped code, and that no enforced label hides a blind site.
External I/O: reads repo sources and the trading pack.

S149 taught `check_node` to reject undeclared node properties, but the S144
completeness suite proved supersets for labels, edge types and signatures only.
An under-declared property therefore reads green in `make ci` and raises
VocabularyError on the first real write — S143's trailing-indicator lesson one
level down, on a fail-closed path.

The blind-site test is the load-bearing one. Fill recovered 7 of its 45 declared
properties while reporting zero undeclared ones, because two writers pass props
through a frozen dataclass field: "didn't look" read exactly like "looked and
found nothing" (DL-57).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vocabulary_properties import properties  # noqa: E402

_PACK = ROOT / "orchestration" / "packs" / "trading_graph_vocabulary.json"

_PLANTED_PROP = '''"""Planted property writer.

Agent: tooling
Role: exercise the property scan against a name no pack declares.
External I/O: none.
"""


def write(graph: object) -> None:
    """Write one Fill carrying a property the vocabulary never declared."""
    graph.merge_node("Fill", "k", {"ticker": "AMD", "planted_undeclared_prop": 1})
'''

_PLANTED_OPAQUE = '''"""Planted opaque writer.

Agent: tooling
Role: exercise the blind-site report against props the scan cannot resolve.
External I/O: none.
"""


def write(graph: object, payload: object) -> None:
    """Write one Fill whose props arrive from an unresolvable expression."""
    graph.merge_node("Fill", "k", payload.unresolvable)
'''


def _properties_declaration() -> dict[str, list[str]]:
    data = json.loads(_PACK.read_text(encoding="utf-8"))
    declared = data["properties"]
    assert isinstance(declared, dict)
    return declared


def _enforced_labels() -> set[str]:
    """Labels the pack declares properties for — the only ones the guard checks."""
    return set(_properties_declaration())


def _declared_props(label: str) -> set[str]:
    return {str(name) for name in _properties_declaration()[label]}


def _plant(tmp_path: Path, source: str) -> Path:
    package = tmp_path / "planted"
    package.mkdir()
    (package / "writer.py").write_text(source, encoding="utf-8")
    return tmp_path


def test_every_property_the_code_can_write_is_declared() -> None:
    """The superset proof one dimension below labels and edge signatures."""
    written = properties(ROOT)
    for label in sorted(_enforced_labels()):
        undeclared = written.properties.get(label, frozenset()) - _declared_props(label)
        assert undeclared == set(), (
            f"undeclared properties on {label}: {sorted(undeclared)}"
        )


def test_property_enforced_labels_have_no_unresolved_write_sites() -> None:
    """DL-57: 'resolved nothing' must not read the same as 'found nothing'.

    The superset test above is vacuous for any label whose write sites the scan
    cannot read, so a blind site fails here rather than passing quietly.
    """
    written = properties(ROOT)
    blind = {
        label: sorted(written.unresolved[label])
        for label in _enforced_labels()
        if written.unresolved.get(label)
    }
    assert blind == {}, f"property-enforced labels with unresolved writers: {blind}"


def test_the_fill_attempt_passthrough_is_resolved() -> None:
    """Regression: the hop that made Fill look clean while proving nothing.

    write_fills hands _fill_props to select_fill_attempt, which stores it on a
    frozen FillAttempt and merges it back as attempt.props. Losing this hop
    drops Fill from 34 recovered properties to 9, with no test failing.
    """
    recovered = properties(ROOT).properties["Fill"]
    assert {"ticker", "side", "quantity", "broker_idempotency_key"} <= recovered
    assert {"drop_reason", "stop_pct_source"} <= recovered


def test_the_property_scan_detects_a_prop_no_pack_declares(tmp_path: Path) -> None:
    written = properties(_plant(tmp_path, _PLANTED_PROP), packages=("planted",))
    assert "planted_undeclared_prop" in written.properties["Fill"]
    assert written.properties["Fill"] - _declared_props("Fill") != set()


def test_the_property_scan_reports_an_unresolvable_props_argument(
    tmp_path: Path,
) -> None:
    """A props expression the scan cannot read is named, never silently dropped."""
    written = properties(_plant(tmp_path, _PLANTED_OPAQUE), packages=("planted",))
    assert written.unresolved["Fill"] == frozenset({"write"})
    assert written.properties["Fill"] == frozenset()
