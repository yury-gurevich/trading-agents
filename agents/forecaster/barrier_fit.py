"""GARCH(1,1)-t fitter port, its deterministic fake, and the `arch` adapter.

Agent: forecaster
Role: isolate the optimiser behind a port so the unit gate proves the barrier
      model with a fake fitter and never imports `arch`; the adapter fits exactly
      EXP-018's specification (constant mean, GARCH(1,1), Student-t, returns in %).
External I/O: the adapter imports `arch` (the optional ``forecaster`` dependency
              group) lazily, on its first fit; the fake touches nothing.
"""

from __future__ import annotations

import importlib
import warnings
from typing import TYPE_CHECKING, Protocol

from agents.forecaster.domain.barrier_garch import RawGarchFit

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


class ConfigurationError(RuntimeError):
    """Raised when the arch fitter cannot run (the package is absent)."""


class GarchFitter(Protocol):
    """Boundary for a GARCH(1,1)-t fit over daily moves in percent."""

    def fit(self, returns_pct: NDArray[np.float64]) -> RawGarchFit:
        """Fit and return the raw estimate; raise when the optimiser fails."""
        ...  # pragma: no cover - protocol declaration only.


class FakeGarchFitter:
    """Deterministic fitter for the unit gate: a fixed estimate, or an error."""

    def __init__(self, raw: RawGarchFit, *, error: Exception | None = None) -> None:
        """Return ``raw`` from every fit, or raise ``error`` when one is given."""
        self._raw = raw
        self._error = error
        self.calls: list[NDArray[np.float64]] = []

    def fit(self, returns_pct: NDArray[np.float64]) -> RawGarchFit:
        """Record the moves it was asked to fit, then answer."""
        self.calls.append(returns_pct)
        if self._error is not None:
            raise self._error
        return self._raw


class ArchGarchFitter:
    """EXP-018's fit, with warnings silenced as the experiment did.

    ``arch_model(r, mean="Constant", vol="GARCH", p=1, q=1, dist="t")``, then
    ``.fit(disp="off")``.
    """

    def fit(self, returns_pct: NDArray[np.float64]) -> RawGarchFit:
        """Fit with arch; a missing package is a ConfigurationError."""
        try:
            arch = importlib.import_module("arch")
        except ModuleNotFoundError as exc:
            raise ConfigurationError("arch is not installed") from exc
        with warnings.catch_warnings():  # pragma: no cover
            warnings.simplefilter("ignore")  # pragma: no cover
            result = arch.arch_model(  # pragma: no cover
                returns_pct, mean="Constant", vol="GARCH", p=1, q=1, dist="t"
            ).fit(disp="off")
        params = result.params  # pragma: no cover
        return RawGarchFit(  # pragma: no cover
            mu=float(params["mu"]),
            omega=float(params["omega"]),
            alpha=float(params["alpha[1]"]),
            beta=float(params["beta[1]"]),
            converged=result.convergence_flag == 0,
        )
