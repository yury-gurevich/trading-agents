"""S239 A2: the forecaster's simulation equals EXP-018's `garch_path_probs`.

Agent: forecaster
Role: use the experiment's own function as the oracle, read at test time from the
      frozen EXP-018 record (Appendix S, `exp018_sim.py`) rather than retyped, and
      demand identical probabilities on the same bars, parameters and seed.
External I/O: reads docs/research/experiments/EXP-018-garch-history-depth.md.

The experiment filters the variance with `scipy.signal.lfilter`; the unit gate has
no scipy. Where scipy is absent, the oracle gets `_reference_lfilter`: scipy's
documented direct-form II transposed recurrence for any `b`, `a` and `zi`, written
from that definition and not from the forecaster's code. Where scipy is present
the real `lfilter` is used and the reference is checked against it. Independently
of both, the golden values below were produced by the experiment's function with
real scipy 1.18.1 and numpy 2.4.6 (builder, 2026-09-28, a scratch environment).
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from agents.forecaster.domain.barrier_garch import daily_moves, garch_path_probs
from agents.forecaster.tests.barrier_fixture import ohlc_series

_ROOT = Path(__file__).resolve().parents[3]
_RECORD = _ROOT / "docs/research/experiments/EXP-018-garch-history-depth.md"
_FUNCTIONS = ("def barrier_probs(", "def garch_path_probs(")

#: (bars, drift, params, stop, target, seed, lo, trimmed from t) -> EXP-018's answer
#: with real scipy (see the module docstring).
GOLDEN = (
    (
        760,
        0.0,
        (0.02, 0.05, 0.06, 0.90),
        0.05,
        0.06,
        12345,
        0,
        0,
        (0.042, 0.013, 0.945),
    ),
    (
        760,
        0.0005,
        (0.01, 0.01, 0.08, 0.919),
        0.03,
        0.03,
        777,
        0,
        0,
        (0.113, 0.217, 0.67),
    ),
    (
        300,
        -0.001,
        (-0.05, 0.1, 0.1, 0.85),
        0.04,
        0.04,
        20260928,
        5,
        3,
        (0.257, 0.075, 0.668),
    ),
)


def _experiment_source() -> str:
    """Return the constants and the two functions from `exp018_sim.py`, verbatim."""
    text = _RECORD.read_text(encoding="utf-8")
    block = text.split("### `exp018_sim.py`", 1)[1].split("```python", 1)[1]
    lines = block.split("```", 1)[0].splitlines()
    keep = [line for line in lines if line.startswith("H, LOOKBACK, ATR_N, N_PATHS")]
    for header in _FUNCTIONS:
        start = next(i for i, line in enumerate(lines) if line.startswith(header))
        end = next(
            (i for i in range(start + 1, len(lines)) if lines[i].startswith("def ")),
            len(lines),
        )
        keep.extend(lines[start:end])
    return "import numpy as np\n" + "\n".join(keep) + "\n"


def _reference_lfilter(
    b: list[float], a: list[float], x: np.ndarray, zi: list[float]
) -> tuple[np.ndarray, np.ndarray]:
    """scipy.signal.lfilter's documented direct-form II transposed recurrence."""
    size = max(len(a), len(b))
    bn = np.pad(np.asarray(b, dtype=float) / a[0], (0, size - len(b)))
    an = np.pad(np.asarray(a, dtype=float) / a[0], (0, size - len(a)))
    z = np.zeros(size - 1)
    z[: len(zi)] = zi
    y = np.empty(len(x))
    for k, xk in enumerate(x):
        yk = bn[0] * xk + z[0]
        for i in range(size - 2):
            z[i] = bn[i + 1] * xk + z[i + 1] - an[i + 1] * yk
        z[size - 2] = bn[size - 1] * xk - an[size - 1] * yk
        y[k] = yk
    return y, z


@pytest.fixture
def experiment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Import EXP-018's functions as a module, with an lfilter they can reach."""
    if importlib.util.find_spec("scipy") is None:
        signal = types.ModuleType("scipy.signal")
        signal.lfilter = _reference_lfilter  # type: ignore[attr-defined]
        scipy = types.ModuleType("scipy")
        scipy.signal = signal  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "scipy", scipy)
        monkeypatch.setitem(sys.modules, "scipy.signal", signal)
    path = tmp_path / "exp018_oracle.py"
    path.write_text(_experiment_source(), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("exp018_oracle", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(count: int, drift: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    _opens, highs, lows, closes = ohlc_series(count, drift=drift)
    return daily_moves(np.array(highs), np.array(lows), np.array(closes))


def test_the_oracle_is_the_experiments_code(experiment: Any) -> None:
    """FORE-OUT-07: the oracle ran is the record's, with its own N_PATHS and H."""
    assert (experiment.N_PATHS, experiment.H) == (1000, 10)
    assert "lfilter([1.0], [1.0, -beta]" in _experiment_source()


def test_daily_moves_are_the_experiments(experiment: Any) -> None:
    """FORE-OUT-07: moves, highs and lows as `run_name` built them (percent logs)."""
    _opens, highs, lows, closes = ohlc_series(40, drift=0.001)
    hi, lo, cl = np.array(highs), np.array(lows), np.array(closes)
    rh, rl, rc = hi[1:] / cl[:-1], lo[1:] / cl[:-1], cl[1:] / cl[:-1]
    expected = (100 * np.log(rc), 100 * np.log(rh), 100 * np.log(rl))
    for ours, theirs in zip(daily_moves(hi, lo, cl), expected, strict=True):
        assert np.array_equal(ours, theirs)


@pytest.mark.parametrize("case", GOLDEN, ids=["full-760", "capped-like", "lo-t-slice"])
def test_the_simulation_equals_exp018(experiment: Any, case: tuple[Any, ...]) -> None:
    """FORE-OUT-07: same bars, parameters and seed give EXP-018's probabilities,
    probability for probability, and both equal the real-scipy golden values."""
    count, drift, params, stop, target, seed, lo, trim, golden = case
    r, lh, ll = _inputs(count, drift)
    t = len(r) - trim
    theirs = experiment.garch_path_probs(
        np.random.default_rng(seed), params, r, lh, ll, lo, t, stop, target
    )
    ours = garch_path_probs(
        np.random.default_rng(seed),
        params,
        r,
        lh,
        ll,
        lo,
        t,
        stop,
        target,
        n_paths=experiment.N_PATHS,
    )
    assert ours == theirs
    assert ours == golden


def test_the_reference_lfilter_is_scipys_where_scipy_exists() -> None:
    """The in-gate stand-in for scipy's lfilter matches it bit for bit."""
    signal = pytest.importorskip("scipy.signal")
    x = 0.05 + 0.06 * np.sin(np.arange(500) * 0.7) ** 2
    expected = signal.lfilter([1.0], [1.0, -0.9], x, zi=[0.9 * 1.3])[0]
    assert np.array_equal(
        _reference_lfilter([1.0], [1.0, -0.9], x, [0.9 * 1.3])[0], expected
    )
