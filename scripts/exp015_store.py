"""EXP-015's panel: one row per line and session, kept as arrays in one .npz (S289).

Agent: tooling
Role: hold the panel's rows (universe flags, baseline, raw line features, raw forward
      returns, SPY's), save it outside the repo, read it back, and digest it.
External I/O: reads and writes `panel.npz` in the output directory it is given.
"""

from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from pathlib import Path

PANEL_FILE = "panel.npz"
_FIELDS = (
    "sessions", "lines", "sectors", "primary", "secondary", "baseline", "features",
    "returns", "spy",
)  # fmt: skip


@dataclass(frozen=True)
class Panel:
    """Rows in session order, then line order; `features` and `returns` are 2-D."""

    sessions: np.ndarray  # ISO dates, '<U10'
    lines: np.ndarray
    sectors: np.ndarray  # '' when the line has no sector
    primary: np.ndarray  # passed the scanner's filters that session
    secondary: np.ndarray  # held at least MIN_SECONDARY_BARS bars
    baseline: np.ndarray  # the analyst's technical score
    features: np.ndarray  # rows x LINE_FEATURES, raw
    returns: np.ndarray  # rows x HORIZONS, raw forward returns
    spy: np.ndarray  # rows x HORIZONS, SPY over the same sessions

    @property
    def excess(self) -> np.ndarray:
        """The forward excess return over SPY, rows x HORIZONS."""
        return self.returns - self.spy

    def take(self, mask: np.ndarray) -> Panel:
        """The rows where mask holds, in order."""
        return Panel(*(getattr(self, name)[mask] for name in _FIELDS))


def save_panel(out_dir: Path, panel: Panel) -> Path:
    path = out_dir / PANEL_FILE
    np.savez_compressed(path, **{name: getattr(panel, name) for name in _FIELDS})
    return path


def load_panel(out_dir: Path) -> Panel:
    with np.load(out_dir / PANEL_FILE, allow_pickle=False) as data:
        return Panel(*(data[name] for name in _FIELDS))


def panel_digest(panel: Panel) -> str:
    """SHA-256 of every array's dtype, shape and bytes in field order (no zip time)."""
    digest = hashlib.sha256()
    for name in _FIELDS:
        array = np.ascontiguousarray(getattr(panel, name))
        digest.update(f"{name}|{array.dtype.str}|{array.shape}|".encode())
        digest.update(array.tobytes())
    return digest.hexdigest()


def shuffled(panel: Panel, seed: int) -> Panel:
    """The panel with each session's forward returns permuted among its rows."""
    rng = np.random.default_rng(seed)
    order = np.arange(len(panel.lines))
    _, starts = np.unique(panel.sessions, return_index=True)
    bounds = [*sorted(starts.tolist()), len(order)]
    for begin, end in itertools.pairwise(bounds):
        order[begin:end] = begin + rng.permutation(end - begin)
    return Panel(
        panel.sessions,
        panel.lines,
        panel.sectors,
        panel.primary,
        panel.secondary,
        panel.baseline,
        panel.features,
        panel.returns[order],
        panel.spy[order],
    )
