"""The Service Bus plan does not move when the roster becomes pack data.

Agent: kernel
Role: prove the route list and SAS-grant plan built from the pack roster
      equal the plans built from today's constants, copied here as literals,
      and that every served type maps to an image directory holding a
      Dockerfile (ADR-0012, DL-12, S232).
External I/O: reads local Dockerfiles only.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from scripts import sb_sas_plan
from scripts.served_agent_roster import (
    DELIBERATOR_MANAGER_TYPE,
    DELIBERATOR_PEER_AGENT_TYPES,
    DELIBERATOR_REPLY_AGENT_TYPES,
    SERVED_AGENT_TYPES,
    image_dir_for_served_agent,
)

from kernel.serve_transport import reply_topic, request_topic

if TYPE_CHECKING:
    import pytest

_LITERAL_SERVED_AGENT_TYPES = (
    "curator",
    "deliberator-proponent",
    "deliberator-opponent",
    "forecaster",
    "operator",
    "researcher",
    "supervisor",
)
_LITERAL_DELIBERATOR_PEER_AGENT_TYPES = (
    "deliberator-proponent",
    "deliberator-opponent",
)
_LITERAL_DELIBERATOR_MANAGER_TYPE = "deliberator-manager"
_LITERAL_DELIBERATOR_REPLY_AGENT_TYPES = (_LITERAL_DELIBERATOR_MANAGER_TYPE,)
_LITERAL_IMAGE_DIR_BY_AGENT_TYPE = {
    "curator": "curator",
    "deliberator-proponent": "deliberator",
    "deliberator-opponent": "deliberator",
    "forecaster": "forecaster",
    "operator": "operator",
    "researcher": "researcher",
    "supervisor": "supervisor",
}


def test_the_roster_equals_todays_constants() -> None:
    assert SERVED_AGENT_TYPES == _LITERAL_SERVED_AGENT_TYPES
    assert DELIBERATOR_PEER_AGENT_TYPES == _LITERAL_DELIBERATOR_PEER_AGENT_TYPES
    assert DELIBERATOR_MANAGER_TYPE == _LITERAL_DELIBERATOR_MANAGER_TYPE
    assert DELIBERATOR_REPLY_AGENT_TYPES == _LITERAL_DELIBERATOR_REPLY_AGENT_TYPES


def test_the_request_and_reply_route_list_is_unchanged() -> None:
    routes = [
        *(request_topic(agent_type) for agent_type in SERVED_AGENT_TYPES),
        *(reply_topic(agent_type) for agent_type in DELIBERATOR_REPLY_AGENT_TYPES),
    ]
    literal_routes = [
        *(request_topic(agent_type) for agent_type in _LITERAL_SERVED_AGENT_TYPES),
        *(
            reply_topic(agent_type)
            for agent_type in _LITERAL_DELIBERATOR_REPLY_AGENT_TYPES
        ),
    ]

    assert routes == literal_routes


def test_every_served_type_maps_to_an_image_directory_with_a_dockerfile() -> None:
    for agent_type in SERVED_AGENT_TYPES:
        directory = image_dir_for_served_agent(agent_type)
        assert directory == _LITERAL_IMAGE_DIR_BY_AGENT_TYPE[agent_type]
        assert Path(f"agents/{directory}/Dockerfile").is_file()


def test_the_sas_plan_built_from_the_roster_equals_the_plan_from_literals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """🪤 A6: the roster is a drop-in for the constants it replaced."""
    from_roster = sb_sas_plan.plan_from_repo(".")

    monkeypatch.setattr(sb_sas_plan, "SERVED_AGENT_TYPES", _LITERAL_SERVED_AGENT_TYPES)
    monkeypatch.setattr(
        sb_sas_plan,
        "DELIBERATOR_PEER_AGENT_TYPES",
        _LITERAL_DELIBERATOR_PEER_AGENT_TYPES,
    )
    monkeypatch.setattr(
        sb_sas_plan, "DELIBERATOR_MANAGER_TYPE", _LITERAL_DELIBERATOR_MANAGER_TYPE
    )
    from_literals = sb_sas_plan.plan_from_repo(".")

    assert from_roster == from_literals
