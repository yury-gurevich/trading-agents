"""Vault seed mechanism tests.

Agent: master
Role: prove seeding writes only after live probe success and fails closed.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from agents.master.vault_seed import (
    Probe,
    ProbeResult,
    SeedEntry,
    SeedOutcome,
    load_seed_manifest,
    parse_seed_manifest,
    seed_vault,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

_ENTRY = SeedEntry("vendor-token", "VENDOR_TOKEN", "vendor")


class _Writer:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.writes: list[tuple[str, str]] = []

    def set_secret(self, name: str, value: str) -> None:
        if self.fail:
            raise RuntimeError("write refused")
        self.writes.append((name, value))


def _ok(_env: Mapping[str, str]) -> ProbeResult:
    return ProbeResult(True, "live check passed")


def _bad(_env: Mapping[str, str]) -> ProbeResult:
    return ProbeResult(False, "auth rejected")


def _raise(_env: Mapping[str, str]) -> ProbeResult:
    raise RuntimeError("probe exploded")


def test_seed_vault_writes_only_after_probe_passes_with_apply() -> None:
    writer = _Writer()
    out = seed_vault(
        (_ENTRY,), {"VENDOR_TOKEN": "works"}, {"vendor": _ok}, writer, apply=True
    )
    assert out == (SeedOutcome("vendor-token", "seeded", "live check passed"),)
    assert writer.writes == [("vendor-token", "works")]


def test_seed_vault_dry_run_never_writes_verified_value() -> None:
    writer = _Writer()
    out = seed_vault(
        (_ENTRY,), {"VENDOR_TOKEN": "works"}, {"vendor": _ok}, writer, apply=False
    )
    assert out[0].status == "seeded"
    assert out[0].message == "would seed: live check passed"
    assert writer.writes == []


def test_seed_vault_skips_empty_env_value() -> None:
    writer = _Writer()
    out = seed_vault((_ENTRY,), {}, {"vendor": _ok}, writer, apply=True)
    assert out == (
        SeedOutcome("vendor-token", "skipped", "env var is empty or missing"),
    )
    assert writer.writes == []


@pytest.mark.parametrize(
    ("probes", "message"),
    [
        ({}, "unknown probe"),
        ({"vendor": _bad}, "auth rejected"),
        ({"vendor": _raise}, "probe raised RuntimeError"),
    ],
)
def test_seed_vault_rejects_unverified_candidates(
    probes: Mapping[str, Probe], message: str
) -> None:
    writer = _Writer()
    out = seed_vault(
        (_ENTRY,), {"VENDOR_TOKEN": "candidate"}, probes, writer, apply=True
    )
    assert out == (SeedOutcome("vendor-token", "rejected", message),)
    assert writer.writes == []


def test_seed_vault_rejects_when_writer_fails() -> None:
    writer = _Writer(fail=True)
    out = seed_vault(
        (_ENTRY,), {"VENDOR_TOKEN": "works"}, {"vendor": _ok}, writer, apply=True
    )
    assert out == (
        SeedOutcome("vendor-token", "rejected", "write failed: RuntimeError"),
    )
    assert writer.writes == []


def test_parse_seed_manifest_loads_entries_and_rejects_duplicates(
    tmp_path: Path,
) -> None:
    text = """[
      {"kv_name": "one", "env_var": "ONE", "probe": "p1"},
      {"kv_name": "two", "env_var": "TWO", "probe": "p2"}
    ]"""
    path = tmp_path / "seed.json"
    path.write_text(text, encoding="utf-8")
    assert load_seed_manifest(str(path)) == (
        SeedEntry("one", "ONE", "p1"),
        SeedEntry("two", "TWO", "p2"),
    )
    with pytest.raises(ValueError, match="duplicate"):
        parse_seed_manifest(
            """[
              {"kv_name": "one", "env_var": "ONE", "probe": "p1"},
              {"kv_name": "one", "env_var": "TWO", "probe": "p2"}
            ]"""
        )


@pytest.mark.parametrize(
    "text",
    [
        "{}",
        "[42]",
        """[{"kv_name": "", "env_var": "ONE", "probe": "p"}]""",
    ],
)
def test_parse_seed_manifest_rejects_invalid_shape(text: str) -> None:
    with pytest.raises(ValueError, match=r"seed manifest|seed entries"):
        parse_seed_manifest(text)
