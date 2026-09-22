from __future__ import annotations

import pytest


def _checker():
    try:
        from scripts import check_module_size
    except ModuleNotFoundError as exc:
        pytest.fail(f"module size checker is missing: {exc}")
    return check_module_size


def _write(tmp_path, name, lines):
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"x = {n}" for n in range(lines))
    path.write_text(body + "\n", encoding="utf-8")
    return path


def test_a_new_script_over_the_block_fails(tmp_path, capsys, monkeypatch):
    module = _checker()
    monkeypatch.setattr(module, "LEGACY_MAX_LINES", {})
    path = _write(tmp_path, "scripts/probe.py", 240)

    assert module.main([str(path)]) == 1
    output = capsys.readouterr().out
    assert "hard block" in output
    assert "240 lines" in output


def test_a_legacy_script_at_its_ceiling_passes(tmp_path, capsys, monkeypatch):
    module = _checker()
    path = _write(tmp_path, "scripts/legacy.py", 240)
    monkeypatch.setattr(module, "LEGACY_MAX_LINES", {module._relative(path): 240})

    assert module.main([str(path)]) == 0
    assert "[LEGACY]" in capsys.readouterr().out


def test_a_legacy_script_that_grows_by_one_line_fails(tmp_path, capsys, monkeypatch):
    module = _checker()
    path = _write(tmp_path, "scripts/legacy.py", 241)
    monkeypatch.setattr(module, "LEGACY_MAX_LINES", {module._relative(path): 240})

    assert module.main([str(path)]) == 1
    output = capsys.readouterr().out
    assert "only shrinks" in output
    assert "241" in output


def test_a_legacy_script_split_below_the_block_must_leave_the_baseline(
    tmp_path, capsys, monkeypatch
):
    """The ratchet converges: shrinking below 200 requires deleting the entry."""
    module = _checker()
    path = _write(tmp_path, "scripts/legacy.py", 120)
    monkeypatch.setattr(module, "LEGACY_MAX_LINES", {module._relative(path): 240})

    assert module.main([str(path)]) == 1
    output = capsys.readouterr().out
    assert "under the block" in output
    assert "module_size_baseline.py" in output


def test_a_baselined_file_that_no_longer_exists_fails(tmp_path, capsys, monkeypatch):
    module = _checker()
    monkeypatch.setattr(module, "LEGACY_MAX_LINES", {"scripts/deleted.py": 240})
    path = _write(tmp_path, "scripts/other.py", 10)

    assert module.main([str(path)]) == 1
    assert "no longer present" in capsys.readouterr().out


def test_the_warn_band_does_not_fail(tmp_path, capsys, monkeypatch):
    module = _checker()
    monkeypatch.setattr(module, "LEGACY_MAX_LINES", {})
    path = _write(tmp_path, "scripts/warn.py", 170)

    assert module.main([str(path)]) == 0
    assert "[WARN]" in capsys.readouterr().out


def test_every_baselined_path_is_over_the_block_today():
    """A shipped baseline entry must name a real file that still needs it."""
    module = _checker()
    for name, ceiling in module.LEGACY_MAX_LINES.items():
        path = module._ROOT / name
        assert path.exists(), name
        count = len(path.read_text(encoding="utf-8").splitlines())
        assert count >= module.FAIL_LIMIT, f"{name} is {count}; delete its entry"
        assert count <= ceiling, f"{name} grew to {count} over ceiling {ceiling}"


def test_scripts_are_inside_the_enforcement_scope():
    """Work-queue item 78: the block must read scripts/, not only the packages."""
    from pathlib import Path

    module = _checker()
    assert module._is_checked_path(Path("scripts/anything.py"))
