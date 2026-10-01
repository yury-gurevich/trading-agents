"""S250: arms that do not belong together give no verdict; outputs stay out of the repo.

Agent: tooling
Role: prove the scorer's refusals on synthetic arm folders, and byte-stable output.
External I/O: local tmp files only.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from scripts.replay_verdict import main, score_out_root
from tests.replay_arm_folders import edit_record, read_record, write_arms

if TYPE_CHECKING:
    from collections.abc import Callable

RESAMPLES = 50
_ROOT = Path(__file__).resolve().parents[1]


def _drop_last_session(root: Path, arm: str) -> None:
    folder = root / arm
    lines = (folder / "equity.csv").read_text(encoding="utf-8").splitlines()
    (folder / "equity.csv").write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    record = read_record(folder)
    record["sessions"] -= 1
    record["last_session"] = lines[-2].split(",")[0]
    edit_record(folder, record)


def _edit(arm: str, key: str, value: object) -> Callable[[Path], None]:
    def apply(root: Path) -> None:
        record = read_record(root / arm)
        record[key] = value
        edit_record(root / arm, record)

    return apply


CASES: dict[str, tuple[Callable[[Path], None], str, str]] = {
    "missing arm": (
        lambda root: shutil.rmtree(root / "technical-only-25"),
        "technical-only-25",
        "missing arm.json, equity.csv, benchmark.csv, summary.json",
    ),
    "different commit": (
        _edit("base-10", "commit", "f" * 40),
        "base-10",
        "its commit differs from base-25's",
    ),
    "different cache": (
        _edit("base-05", "cache", {"sp500_bars.csv.gz": "000000000000"}),
        "base-05",
        "its cache checksums differ from base-25's",
    ),
    "different sessions": (
        lambda root: _drop_last_session(root, "relative-strength-only-25"),
        "relative-strength-only-25",
        "its sessions differ from base-25's",
    ),
    "rule off": (
        _edit("base-10", "require_history", False),
        "base-10",
        "require_history is False; the manifest says True",
    ),
    "dirty worktree": (
        _edit("base-05", "dirty", True),
        "base-05",
        "it ran from a worktree with uncommitted changes",
    ),
}


@pytest.mark.parametrize("case", sorted(CASES))
def test_c12_arms_that_do_not_belong_together_give_no_verdict(
    tmp_path: Path, case: str
) -> None:
    """S250-C12: a refusal names the arm and the reason, and there is no verdict."""
    plant, arm, reason = CASES[case]
    root = write_arms(tmp_path / "arms")
    plant(root)

    document = score_out_root(root, resamples=RESAMPLES)

    assert document["verdict"] is None
    assert {"arm": arm, "reason": reason} in document["refusals"]
    assert document["arms"] == {}
    page = (root / "verdict.md").read_text(encoding="utf-8")
    assert page.startswith("# EXP-014 verdict: NO VERDICT")
    assert f"- **{arm}**: {reason}" in page


def test_c12_a_gap_session_gives_no_verdict(tmp_path: Path) -> None:
    """S250-C12 / RPT-OUT-07: a session with no SPY close is a gap; all arms refuse."""
    root = write_arms(tmp_path / "arms")
    for folder in root.iterdir():
        lines = (folder / "benchmark.csv").read_text(encoding="utf-8").splitlines()
        del lines[40]
        (folder / "benchmark.csv").write_text("\n".join(lines) + "\n", "utf-8")

    document = score_out_root(root, resamples=RESAMPLES)

    assert document["verdict"] is None
    assert len(document["refusals"]) == 5
    reasons = {item["reason"] for item in document["refusals"]}
    assert reasons == {"2 gap session(s) in the scored window"}


def test_c15_outputs_stay_out_of_the_repo_and_are_byte_stable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """S250-C15: an out-root in the worktree is refused; scoring twice, same bytes."""
    with pytest.raises(ValueError, match="inside the worktree"):
        score_out_root(_ROOT / "tests" / "no-such-out-root", resamples=RESAMPLES)

    root = write_arms(tmp_path / "arms")
    argv = ["score", "--out-root", str(root), "--resamples", str(RESAMPLES)]
    assert main(argv) == 0
    first = {
        name: (root / name).read_bytes() for name in ("verdict.json", "verdict.md")
    }
    assert main(argv) == 0
    second = {name: (root / name).read_bytes() for name in first}

    assert first == second
    document = json.loads(first["verdict.json"])
    assert document["verdict"]["verdict"] == "NO EDGE"
    assert document["appendix_p"] is False
    assert "NOT Appendix P's bootstrap" in capsys.readouterr().out
    assert not (_ROOT / "tests" / "no-such-out-root").exists()
