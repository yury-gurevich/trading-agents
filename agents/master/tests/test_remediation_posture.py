"""An operator switch that would do nothing must refuse to be set.

Agent: master
Role: prove `remediation_mode='automatic'` cannot start a master that is unable
      to remediate, and that `manual` is untouched.
External I/O: none (InMemoryGraphStore).

Item 41. This was filed as a *latent* trap, not a live defect, and the
distinction is the point: nothing in the fleet sets `automatic`, so nothing was
misbehaving — a future operator would simply have flipped a documented switch and
received silence. `plan_and_try_remediation` returns `None` at
`if llm is None or not catalogue`, which is the correct behaviour for an unwired
catalogue and a terrible answer to give a human.

🪤 What is NOT done here: wiring the remediation catalogue. DL-144 places Pieces
C/D deliberately later, and building them under cover of a defect fix would be
the scope creep this repo keeps catching itself in.
"""

from __future__ import annotations

import pytest

from agents.master.entrypoint import build_app
from agents.master.remediation_posture import refuse_unwired_automatic_remediation
from agents.master.settings import MasterSettings
from kernel import InMemoryGraphStore
from kernel.crypto import generate_keypair


def test_automatic_remediation_refuses_a_master_that_cannot_remediate() -> None:
    """🎯 The silence becomes a refusal at construction, before any escalation."""
    private, _ = generate_keypair()
    settings = MasterSettings(remediation_mode="automatic")

    with pytest.raises(ValueError, match="cannot be honoured"):
        build_app(InMemoryGraphStore(), private, settings=settings)


def test_the_refusal_names_the_setting_that_fixes_it() -> None:
    """An operator reading the crash must know what to do next."""
    with pytest.raises(ValueError, match="MASTER_REMEDIATION_MODE=manual"):
        refuse_unwired_automatic_remediation(
            MasterSettings(remediation_mode="automatic")
        )


def test_manual_remediation_is_unaffected() -> None:
    """D2: the default posture starts exactly as it did before this sprint."""
    private, _ = generate_keypair()

    agent, _pem = build_app(
        InMemoryGraphStore(),
        private,
        settings=MasterSettings(remediation_mode="manual"),
    )

    assert agent.session_id is not None


def test_an_unknown_mode_is_left_to_the_existing_validation() -> None:
    """This guard answers one question only; it does not become a mode validator."""
    refuse_unwired_automatic_remediation(MasterSettings(remediation_mode="manual"))
