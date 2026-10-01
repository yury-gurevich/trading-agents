"""Divergence episodes: which broker-divergence Flag is open, read in memory.

Agent: execution
Role: parse a divergence Flag's subject into (kind, ticker), and group the
      unresolved family Flags into open episodes by the (subject_ref, severity)
      join every reader uses (EXEC-OBS-07, DL-254 D3).
External I/O: none (pure functions over nodes already read).
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import Node

PREFIX = "broker-position-divergence:"
# Flags written before S178 keyed their subject on the per-run snapshot, so each
# run minted a unique one. They cannot match a live divergence and are retired by
# scripts/sweep_divergence_flags.py, never by a run. No kind is named
# `broker-position-snapshot`, so an episode subject never starts with this.
LEGACY_PREFIX = f"{PREFIX}broker-position-snapshot:"

Episode = dict[str, "Node"]


def flag_join(node: Node) -> tuple[str, str]:
    """Return (subject_ref, severity): the props readers join a resolution on."""
    props = node.props
    return str(props.get("subject_ref", "")), str(props.get("severity", "critical"))


def identity(subject_ref: str) -> tuple[str, str]:
    """Return (kind, ticker): the first two fields after the family prefix.

    An episode subject carries the first-sight snapshot key after them; a
    suffix-less subject (S178 to S248) carries nothing, and parses the same.
    """
    kind, _, rest = subject_ref.removeprefix(PREFIX).partition(":")
    return kind, rest.split(":", 1)[0]


def open_episodes(
    flags: tuple[Node, ...], resolutions: tuple[Node, ...]
) -> dict[tuple[str, str], Episode]:
    """Group unresolved, non-legacy family Flags by (kind, ticker), then severity."""
    resolved = {flag_join(node) for node in resolutions}
    episodes: dict[tuple[str, str], Episode] = defaultdict(dict)
    for flag in flags:
        subject_ref, severity = flag_join(flag)
        if not subject_ref.startswith(PREFIX) or subject_ref.startswith(LEGACY_PREFIX):
            continue
        if (subject_ref, severity) not in resolved:
            episodes[identity(subject_ref)][severity] = flag
    return episodes
