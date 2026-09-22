"""Evidence-envelope declaration tests."""

from __future__ import annotations

import pytest

from agents.analyst.settings import AnalystSettings
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.provider.settings import ProviderSettings
from kernel import describe, tunable


def test_envelope_below_inclusive_lower_rail_is_refused():
    """DD-04: An envelope cannot include a value below its field's ge rail."""

    with pytest.raises(ValueError, match=r"\(13\.0, 60\.0\).*ge=20"):
        tunable(
            50,
            why="Synthetic configuration to prove the lower rail is enforced.",
            ge=20,
            le=250,
            envelope=(13.0, 60.0),
            source="Synthetic evidence source.",
        )


def test_envelope_below_exclusive_lower_rail_is_refused():
    """DD-04: An envelope cannot include a value equal to its field's gt rail."""

    with pytest.raises(ValueError, match=r"\(0\.0, 0\.5\).*gt=0"):
        tunable(
            0.25,
            why=(
                "Synthetic configuration to prove the exclusive lower rail is enforced."
            ),
            gt=0.0,
            le=1.0,
            envelope=(0.0, 0.5),
            source="Synthetic evidence source.",
        )


def test_envelope_above_upper_rail_is_refused():
    """DD-04: An envelope cannot include a value above its field's le rail."""

    with pytest.raises(ValueError, match=r"\(60\.0, 252\.0\).*le=250"):
        tunable(
            120,
            why="Synthetic configuration to prove the upper rail is enforced.",
            ge=20,
            le=250,
            envelope=(60.0, 252.0),
            source="Synthetic evidence source.",
        )


def test_valid_and_unrailed_envelopes_are_accepted():
    """DD-04: In-rail, rail-equal, and unrailed envelopes remain valid."""

    for kwargs in (
        {"ge": 20, "le": 250, "envelope": (60.0, 120.0)},
        {"ge": 20, "le": 250, "envelope": (20.0, 250.0)},
        {"envelope": (1.0, 2.0)},
    ):
        assert (
            tunable(
                50,
                why="Synthetic configuration to prove valid envelopes stay valid.",
                source="Synthetic evidence source.",
                **kwargs,
            )
            is not None
        )


def test_all_declared_envelopes_stay_inside_their_rails():
    """DD-04: All thirteen declared evidence envelopes fit their field rails."""

    envelopes = [
        row
        for settings_cls in (
            PortfolioManagerSettings,
            ProviderSettings,
            AnalystSettings,
        )
        for row in describe(settings_cls)
        if row.envelope_min is not None
    ]

    assert len(envelopes) == 13
    assert all(
        (row.minimum is None or row.envelope_min >= row.minimum)
        and (row.maximum is None or row.envelope_max <= row.maximum)
        for row in envelopes
    )


def test_correlation_threshold_envelope_cites_the_ramp_evidence():
    """DD-04: The correlation-ramp floor cites ADR-0030 and EXP-008 evidence."""

    threshold = next(
        row
        for row in describe(PortfolioManagerSettings)
        if row.name == "correlation_threshold"
    )

    assert threshold.default == 0.50
    assert (threshold.envelope_min, threshold.envelope_max) == (0.50, 0.70)
    assert threshold.source is not None
    assert "ADR-0030" in threshold.source
    assert "EXP-008" in threshold.source
    assert "Effect magnitudes" not in threshold.source
