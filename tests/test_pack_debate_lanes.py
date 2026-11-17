"""Keep the operator's live debate settings through a full up (DL-325).

Agent: tooling
Role: pin the pack's three lanes, manager wait and one-request premise.
External I/O: reads the tunables pack and deploy script; no network or PowerShell.

DL-277 and DL-274 fixed these two fleet values. Unlike the older general
pack test, these regression guards deliberately fix the numbers: accepting
any bounded value would let a full up silently restore one lane and 120 seconds.
"""

from __future__ import annotations

import json
from pathlib import Path

from kernel.bus_azure_config import AzureServiceBusSettings

_ROOT = Path(__file__).resolve().parents[1]
_PACK = json.loads(
    (_ROOT / "orchestration/packs/trading_tunables.json").read_text("utf-8")
)
_APPS: dict[str, dict[str, str]] = _PACK["apps"]
_DEPLOY = (_ROOT / "infra/deploy-agents.ps1").read_text("utf-8")
_LANES = "DELIBERATOR_DEBATE_CONCURRENCY"
_WAIT = "DELIBERATOR_REQUEST_TIMEOUT_SECONDS"
_RECEIVE_KEY = "RECEIVE_MAX_MESSAGES"


def test_a_full_up_keeps_three_debates_at_once() -> None:
    """DL-325 / DL-277: full up preserves the three live manager lanes."""
    assert _APPS["deliberator-manager"][_LANES] == "3"


def test_only_the_manager_declares_the_lanes() -> None:
    """DL-325: the manager alone declares the lane count."""
    assert [app for app, env in _APPS.items() if _LANES in env] == [
        "deliberator-manager"
    ]


def test_a_full_up_keeps_the_managers_wait_of_240_seconds() -> None:
    """DL-325 / DL-274: full up preserves the manager's live peer wait."""
    assert _APPS["deliberator-manager"][_WAIT] == "240"


def test_the_debaters_keep_their_wait_of_120_seconds() -> None:
    """DL-325: the manager-only wait amendment leaves both peers at 120."""
    for app in ("deliberator-proponent", "deliberator-opponent"):
        assert _APPS[app][_WAIT] == "120"


def test_more_than_one_lane_takes_one_request_a_pass() -> None:
    """DL-325 / DLIB-IDM-04: parallel lanes rely on one request per pass.

    This pins the configuration premise, not the clause's full settlement,
    reply-publication and fail-open behaviour, which has its own tests.
    """
    assert int(_APPS["deliberator-manager"][_LANES]) > 1
    assert AzureServiceBusSettings.model_fields["receive_max_messages"].default == 1
    assert not any(_RECEIVE_KEY in key for env in _APPS.values() for key in env)
    assert _RECEIVE_KEY not in _DEPLOY


def test_the_packs_note_records_both_moves() -> None:
    """DL-325: the pack records both operator moves and their decision."""
    note = _PACK["_measured"]
    assert "DELIBERATOR_DEBATE_CONCURRENCY 1->3" in note
    assert "DELIBERATOR_REQUEST_TIMEOUT_SECONDS 120->240" in note
    assert "DL-325" in note
