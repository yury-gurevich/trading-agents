"""Config-pack file integrity tests.

Agent: tooling
Role: refuse a pack whose JSON hides a key behind a later duplicate.
External I/O: reads every orchestration/packs/*.json.

A duplicate key is the failure mode that looks like success: `json.load` keeps the
**last** occurrence and discards the earlier one silently, so the row an operator
reads in the file is not the row the fleet gets. Measured 2026-09-04 while merging
S172 — two `DELIBERATOR_DEBATE_CONCURRENCY` keys in one object, the visible first
entry inert, and the pack's own 61-test suite green throughout, because every one
of those tests iterates the *parsed* dict where the loser no longer exists.

The guard is at file level rather than in a loader on purpose: the pack is checked
into the repo and read by both `entrypoint.py` (Python) and `deploy-agents.ps1`
(PowerShell, whose `ConvertFrom-Json` discards the same way). Catching it in the
file catches it for every reader, including ones not written yet.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterable

PACK_DIR = Path(__file__).resolve().parents[1] / "orchestration" / "packs"


class DuplicatePackKeyError(ValueError):
    """Raised when one JSON object declares the same key twice."""


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a dict, refusing any object that names a key more than once."""
    seen: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise DuplicatePackKeyError(key)
        seen[key] = value
    return seen


def strict_loads(text: str) -> Any:
    """Parse JSON, raising on a duplicate key at any nesting depth."""
    return json.loads(text, object_pairs_hook=_no_duplicates)


def pack_files() -> Iterable[Path]:
    """Every JSON pack a deploy or an agent reads."""
    return sorted(PACK_DIR.glob("*.json"))


def test_the_pack_directory_is_not_silently_empty() -> None:
    """A glob that matches nothing would make every check below vacuous."""
    assert len(list(pack_files())) >= 8


@pytest.mark.parametrize("path", pack_files(), ids=lambda path: path.name)
def test_no_pack_hides_a_key_behind_a_duplicate(path: Path) -> None:
    """The row an operator reads must be the row the fleet gets."""
    try:
        strict_loads(path.read_text(encoding="utf-8"))
    except DuplicatePackKeyError as exc:
        pytest.fail(f"{path.name} declares {exc.args[0]!r} twice in one object")


def test_the_guard_catches_a_duplicate_at_the_top_level() -> None:
    """S172's actual shape: two settings keys in one app object."""
    with pytest.raises(DuplicatePackKeyError):
        strict_loads(
            '{"DELIBERATOR_DEBATE_CONCURRENCY": "1", '
            '"DELIBERATOR_DEBATE_CONCURRENCY": "4"}'
        )


def test_the_guard_catches_a_duplicate_nested_inside_an_app() -> None:
    """Tunables are nested one level down, which is where it happened."""
    with pytest.raises(DuplicatePackKeyError):
        strict_loads('{"apps": {"deliberator-manager": {"A": "1", "A": "2"}}}')


def test_a_repeated_key_in_two_different_objects_is_not_a_duplicate() -> None:
    """Every app declares the same setting names; only one object binds a key."""
    parsed = strict_loads('{"a": {"MAX": "1"}, "b": {"MAX": "2"}}')

    assert parsed == {"a": {"MAX": "1"}, "b": {"MAX": "2"}}


def test_the_strict_parser_agrees_with_json_load_on_a_clean_file() -> None:
    """The guard must reject duplicates and change nothing else."""
    for path in pack_files():
        text = path.read_text(encoding="utf-8")

        assert strict_loads(text) == json.loads(text)
