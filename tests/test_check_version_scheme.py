from __future__ import annotations

import tomllib
from pathlib import Path

import pytest


def _checker():
    try:
        from scripts.check_version_scheme import main
    except ModuleNotFoundError as exc:
        pytest.fail(f"version scheme checker is missing: {exc}")
    return main


def test_rejects_single_digit_patch_group(tmp_path, capsys):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nversion = "0.103.0"\n', encoding="utf-8")

    assert _checker()([str(pyproject)]) == 1
    output = capsys.readouterr().out
    assert "0.103.0" in output
    assert "MAJOR.MMM.PP" in output


@pytest.mark.parametrize(
    "version",
    ["0.90.16", "0.94.02", "0.98.11", "0.99.00", "0.100.00", "0.102.00", "0.103.00"],
)
def test_accepts_versions_from_real_tags(tmp_path, capsys, version):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(f'[project]\nversion = "{version}"\n', encoding="utf-8")

    assert _checker()([str(pyproject)]) == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("version", ["v0.103.00", "0.103.000", "0.103.00-dev", "0.103"])
def test_rejects_versions_outside_declared_shape(tmp_path, capsys, version):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(f'[project]\nversion = "{version}"\n', encoding="utf-8")

    assert _checker()([str(pyproject)]) == 1
    assert "MAJOR.MMM.PP" in capsys.readouterr().out


def test_real_pyproject_passes_despite_normalized_lockfile(capsys):
    root = Path(__file__).resolve().parents[1]
    project_version = tomllib.loads(
        (root / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["version"]
    lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    lock_version = next(
        package["version"]
        for package in lock["package"]
        if package["name"] == "trading-agents"
    )

    assert project_version != lock_version
    assert _checker()([str(root / "pyproject.toml")]) == 0
    assert capsys.readouterr().out == ""
