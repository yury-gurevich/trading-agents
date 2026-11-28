"""Hold-drill CLI on temporary env files and a synthetic Bot API.

Agent: tooling
Role: prove DL-330 command refusals, exits, bounds and environment isolation.
External I/O: temporary env files and a fake Bot API.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from scripts import run_hold_drill as cli

from orchestration.tests.hold_drill_fakes import (
    FLEET_BOT_VALUE,
    SAFE_NOW,
    TEST_BOT_VALUE,
    FakeBot,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def bot(monkeypatch: pytest.MonkeyPatch) -> tuple[FakeBot, list[str]]:
    """Replace the client-bound sender and the clock; never contact Telegram."""
    fake = FakeBot()
    carried: list[str] = []

    def send(
        value: str, method: str, payload: dict[str, object], timeout: float
    ) -> object:
        carried.append(value)
        return fake(method, payload, timeout)

    monkeypatch.setattr("orchestration.telegram_client.send_request", send)
    monkeypatch.setattr(cli, "_now", lambda: SAFE_NOW)
    monkeypatch.setattr(cli, "_sleep", lambda _: None)
    return fake, carried


def env_file(tmp_path: Path, extra: str = "") -> str:
    """Write invented bot values to a temporary file."""
    path = tmp_path / "drill.env"
    path.write_text(
        f"TELEGRAM_TEST_BOT_TOKEN={TEST_BOT_VALUE}\nTELEGRAM_CHAT_ID=42\n{extra}",
        encoding="utf-8",
    )
    return str(path)


def presses(
    monkeypatch: pytest.MonkeyPatch, fake: FakeBot, *, both: bool = True
) -> None:
    """Inject presses only when the CLI asks to sleep."""
    queued = iter(
        [
            ("run_now", "sched-2026-11-27"),
            *([("skip_today", "sched-2026-11-25")] if both else []),
        ]
    )

    def sleep(_: float) -> None:
        if (press := next(queued, None)) is not None:
            fake.press(*press)

    monkeypatch.setattr(cli, "_sleep", sleep)


def test_a_refused_start_exits_2_and_calls_no_bot(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], bot: tuple[FakeBot, list[str]]
) -> None:
    """DL-330 D1, D5: refuse missing values before any Bot API request."""
    path = tmp_path / "missing.env"
    path.write_text("TELEGRAM_CHAT_ID=42\n", encoding="utf-8")
    assert cli.main(["--env-file", str(path)]) == 2
    assert (
        capsys.readouterr().out
        == "REFUSED: missing drill values: TELEGRAM_TEST_BOT_TOKEN\n"
    )
    assert bot[1] == []


def test_both_rounds_passing_exit_0(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    bot: tuple[FakeBot, list[str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DL-330 D5: both requested presses yield exit zero and exact totals."""
    presses(monkeypatch, bot[0])
    assert cli.main(["--env-file", env_file(tmp_path), "--wait-minutes", "1"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert (
        lines[0]
        == "HOLD DRILL  test bot 7000000001, a poll every 5 s, at most 1 min a round"
    )
    assert lines[-1] == "HOLD DRILL  2 of 2 rounds passed"


def test_a_failed_round_exits_1(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    bot: tuple[FakeBot, list[str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DL-330 D5: a missing second press yields exit one and partial totals."""
    presses(monkeypatch, bot[0], both=False)
    assert (
        cli.main(
            [
                "--env-file",
                env_file(tmp_path),
                "--poll-seconds",
                "30",
                "--wait-minutes",
                "1",
            ]
        )
        == 1
    )
    assert (
        capsys.readouterr().out.splitlines()[-1] == "HOLD DRILL  1 of 2 rounds passed"
    )


def test_the_env_file_is_read_not_loaded(
    tmp_path: Path, bot: tuple[FakeBot, list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """DL-330 D1, D5: no file name enters the environment or fleet key the API."""
    presses(monkeypatch, bot[0])
    for name in (
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_TEST_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "POSTGRES_DSN",
    ):
        monkeypatch.delenv(name, raising=False)
    before = dict(os.environ)
    path = env_file(
        tmp_path,
        f"TELEGRAM_BOT_TOKEN={FLEET_BOT_VALUE}\nPOSTGRES_DSN=postgresql://planted@fleet.invalid/live\n",
    )
    try:
        assert cli.main(["--env-file", path]) == 0
        assert dict(os.environ) == before
        assert bot[1]
        assert set(bot[1]) == {TEST_BOT_VALUE}
    finally:
        os.environ.clear()
        os.environ.update(before)


@pytest.mark.parametrize(
    ("flag", "value"),
    [
        ("--poll-seconds", "0"),
        ("--poll-seconds", "601"),
        ("--wait-minutes", "0"),
        ("--wait-minutes", "31"),
    ],
)
def test_a_poll_outside_its_bounds_is_refused(
    flag: str, value: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """DL-330 D5: reject numbers outside either declared CLI range."""
    with pytest.raises(SystemExit) as refused:
        cli.main([flag, value])
    assert refused.value.code == 2
    assert "must be 1 to" in capsys.readouterr().err
