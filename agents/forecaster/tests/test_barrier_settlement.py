"""S241 C1-C4: a claim's outcome is EXP-018's, measured on the settling series alone.

Agent: forecaster
Role: prove the pure settlement rule against `scripts/barrier_testbed.outcome()` (the
      oracle, imported, not retyped): the low is checked first, the entry is the
      settling series' own close on as_of, a raw close ratio outside 0.6-1.67 is a
      suspected corporate action (void, never a stop), and a claim without ten
      settling sessions stays open until 45 days have passed.
External I/O: none.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pytest
from scripts.barrier_testbed import outcome as testbed_outcome

from agents.forecaster.domain.barrier_settlement import (
    CORPORATE_ACTION,
    NO_SETTLING_BARS,
    OUTCOMES,
    VOID,
    Settlement,
    SettlingBar,
    settle,
)
from agents.forecaster.tests.settlement_paths import AS_OF, ENTRY, STOP, TARGET, path

_PASS = AS_OF + timedelta(days=15)
#: session -> (high, low); the stop level is 95.0 and the target level 107.0.
_SCENARIOS = {
    "stop-first": ({3: (100.5, 94.0), 6: (108.0, 99.0)}, "stop"),
    "target-first": ({2: (108.0, 99.0), 5: (100.5, 94.0)}, "target"),
    "neither": ({4: (106.0, 96.0), 8: (106.9, 95.1)}, "neither"),
    "both-in-one-session": ({4: (108.0, 94.0)}, "stop"),
}


def _settle(bars: list[SettlingBar], **overrides: float) -> Settlement | None:
    return settle(
        bars,
        as_of=AS_OF,
        entry_close=float(overrides.get("entry_close", ENTRY)),
        stop_pct=float(overrides.get("stop_pct", STOP)),
        target_pct=float(overrides.get("target_pct", TARGET)),
        pass_date=_PASS,
    )


def _oracle(bars: list[SettlingBar], stop: float, target: float) -> str:
    """EXP-018's outcome on the same bars, entry at the as_of bar (index ``t``)."""
    t = next(i for i, bar in enumerate(bars) if bar.day == AS_OF)
    hi, lo, cl = (
        np.array([getattr(b, f) for b in bars]) for f in ("high", "low", "close")
    )
    return OUTCOMES[testbed_outcome(hi, lo, cl, t, stop, target)]


@pytest.mark.parametrize("name", list(_SCENARIOS))
def test_the_outcome_is_exp018s(name: str) -> None:
    """FORE-OUT-08: stop first, target first, neither, and a session touching both
    (the low is checked first, so it is the stop), equal to the test bed's rule."""
    events, expected = _SCENARIOS[name]
    bars = path(events=events)

    settled = _settle(bars)

    assert settled is not None
    assert settled.outcome == expected == _oracle(bars, STOP, TARGET)
    assert settled.void_reason is None
    assert settled.settled_on == bars[-1].day  # the tenth session after as_of


def test_the_settlement_equals_the_test_beds_outcome_on_random_paths() -> None:
    """FORE-OUT-08: 400 random ten-session paths and barriers, outcome for outcome."""
    rng = np.random.default_rng(20260928)
    for _ in range(400):
        moves = np.exp(rng.normal(0.0, 0.02, 12))
        closes = {s: float(ENTRY * moves[: s + 2].prod()) for s in range(-1, 11)}
        spread = rng.uniform(0.0, 0.03, (12, 2))
        events = {
            s: (closes[s] * (1 + spread[s + 1, 0]), closes[s] * (1 - spread[s + 1, 1]))
            for s in range(-1, 11)
        }
        stop, target = (float(v) for v in rng.uniform(0.01, 0.08, 2))
        bars = path(events=events, closes=closes, entry=closes[0], before=1)

        settled = settle(
            bars,
            as_of=AS_OF,
            entry_close=closes[0],
            stop_pct=stop,
            target_pct=target,
            pass_date=_PASS,
        )

        assert settled is not None
        assert settled.outcome == _oracle(bars, stop, target)


def test_the_entry_is_the_settling_series_own_close() -> None:
    """FORE-OUT-08: the settling series closes 3 % above the claim's entry_close on
    as_of. Measured from its own close (stop 97.85) session 3's low of 97.5 is the
    stop; from the claim's 100 (stop 95, target 107) session 5 would be the target.
    The ratio of the two closes is recorded."""
    bars = path(entry=103.0, events={3: (104.0, 97.5), 5: (108.0, 102.0)})

    settled = _settle(bars, entry_close=100.0)

    assert settled is not None
    assert settled.outcome == "stop" == _oracle(bars, STOP, TARGET)
    assert settled.entry_close_settling == 103.0
    assert settled.entry_ratio == 103.0 / 100.0


@pytest.mark.parametrize("ratio", [0.5, 0.1, 3.0], ids=["2:1", "10:1", "1:3"])
def test_a_split_is_void_never_a_stop(ratio: float) -> None:
    """FORE-FAIL-05: a raw split inside the window (a close ratio of 0.5 or 0.1,
    which the raw rule would score as the stop, or 3.0, the target) settles void,
    suspected_corporate_action, dated the pass that voided it."""
    level = ENTRY * ratio
    bars = path(closes={4: level}, events={4: (level * 1.01, level * 0.99)})
    raw = _oracle(bars, STOP, TARGET)

    settled = _settle(bars)

    assert raw == ("stop" if ratio < 1 else "target")
    assert settled == Settlement(VOID, CORPORATE_ACTION, _PASS, ENTRY, 1.0)


@pytest.mark.parametrize(
    ("close", "void"),
    [(60.0, False), (59.9, True), (167.0, False), (167.1, True)],
    ids=["0.6", "below-0.6", "1.67", "above-1.67"],
)
def test_the_corporate_action_bounds_are_the_specs(close: float, void: bool) -> None:
    """FORE-FAIL-05: below 0.6 or above 1.67 is void; the bounds themselves are not."""
    bars = path(closes={7: close}, events={7: (close * 1.01, close * 0.99)})

    settled = _settle(bars)

    assert settled is not None
    assert (settled.outcome == VOID) is void


def test_too_few_bars_is_not_a_settlement() -> None:
    """FORE-FAIL-05: without the as_of bar, or with 9 sessions after it, the claim
    stays open (None) while it is younger than 45 days."""
    no_as_of = [bar for bar in path() if bar.day != AS_OF]
    nine_after = path(after=9)

    assert _settle(no_as_of) is None
    assert _settle(nine_after) is None


def test_an_unsettled_claim_is_void_45_days_after_as_of() -> None:
    """FORE-FAIL-05: still open on a pass 44 days after as_of it stays open; on the
    pass 45 days after, it is void, no_settling_bars, dated that pass."""
    bars = path(after=9)

    def at(days: int) -> Settlement | None:
        return settle(
            bars,
            as_of=AS_OF,
            entry_close=ENTRY,
            stop_pct=STOP,
            target_pct=TARGET,
            pass_date=AS_OF + timedelta(days=days),
        )

    assert at(44) is None
    day_45 = AS_OF + timedelta(days=45)
    assert at(45) == Settlement(VOID, NO_SETTLING_BARS, day_45, None, None)
