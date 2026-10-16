"""S281 manifest arms and their conditional exit arguments and records.

Agent: tooling
Role: prove declared exits reach the runner and only declared exits reach arm.json.
External I/O: synthetic cache and arm files under pytest's external tmp_path only.
"""

from __future__ import annotations

import json

from scripts.replay_arms import load_manifest, run_arm
from scripts.replay_arms_record import RepoState
from scripts.replay_exits import STOPS_ONLY, ExitPolicy
from tests.replay_exit_fixtures import SESSIONS, write_cache


def test_a17_only_an_arm_that_declares_exits_passes_and_records_them(tmp_path):
    """S281-A17: a two-arm manifest preserves the legacy keyword set and arm record."""
    policy = {
        "take_profit": True,
        "time_exit_sessions": 2,
        "trailing_stop": True,
        "reentry_cooldown_sessions": 3,
    }
    manifest_path = tmp_path / "arms.json"
    manifest_path.write_text(
        json.dumps(
            {
                "experiment": "S281-fixture",
                "start": SESSIONS[0].isoformat(),
                "require_history": False,
                "arms": [
                    {"name": "stops", "slippage_bps": 10, "overrides": []},
                    {
                        "name": "exits",
                        "slippage_bps": 25,
                        "overrides": [],
                        "exits": policy,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest = load_manifest(manifest_path)
    assert manifest.arms[0].exits == STOPS_ONLY
    assert manifest.arms[1].exits == ExitPolicy(**policy)
    cache = write_cache(tmp_path / "cache")
    calls = []

    def runner(**kwargs):
        calls.append(kwargs)
        out = kwargs["out"]
        out.mkdir(parents=True)
        (out / "equity.csv").write_text(
            "date,equity_cents,long_cents\n"
            + "".join(f"{day},10000000,20000\n" for day in SESSIONS),
            encoding="utf-8",
        )
        return {}

    records = []
    for spec in manifest.arms:
        out = run_arm(
            spec,
            manifest,
            cache_dir=cache,
            out_root=tmp_path / "outputs",
            runner=runner,
            repo=lambda: RepoState("a" * 40, False),
            progress_every=0,
        )
        expected = {
            "cache_dir": cache,
            "out": out,
            "start": SESSIONS[0],
            "end": None,
            "overrides": (),
            "slippage_bps": spec.slippage_bps,
            "progress_every": 0,
            "require_history": False,
        }
        if spec.name == "exits":
            expected["exits"] = ExitPolicy(**policy)
        assert calls[-1] == expected
        records.append(json.loads((out / "arm.json").read_text(encoding="utf-8")))
    assert "exits" not in records[0]
    assert records[1]["exits"] == policy
    assert set(records[1]) == set(records[0]) | {"exits"}
    assert len(calls) == 2
