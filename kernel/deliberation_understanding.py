"""Deliberation understanding scorer — does the debate define our parameters right?

Agent: kernel
Role: grade a debate transcript's *parameter definitions* against a known-truth
      answer key. EXP-001/003 proved the model confidently misreads our parameters
      (it calls a pooled cross-sectional gate a per-stock vol filter); a fluent
      justification can be confidently wrong. This turns "it explained itself" into
      a measured understanding score — confidence by measurement, not eloquence
      (DL-31). Decision-agnostic substrate: the trading answer key lives in a pack.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParameterTruth:
    """The answer key for one parameter the deliberation may invoke.

    ``correct_markers``: any one present (case-insensitive) signals the debate framed
    the parameter the way our code actually behaves. ``misread_markers``: any one
    present signals a known wrong reading (a Class-1/Class-2 delta). A definition that
    hits a misread marker is *not* counted understood even if it also hits a correct
    one — the known error dominates.
    """

    name: str
    correct_markers: tuple[str, ...]
    misread_markers: tuple[str, ...]


@dataclass(frozen=True)
class UnderstandingScore:
    """How one parameter was treated in a transcript."""

    name: str
    cited: bool
    understood: bool
    misread: bool


def score_understanding(
    text: str, truths: tuple[ParameterTruth, ...]
) -> tuple[UnderstandingScore, ...]:
    """Score each truth against the transcript text (defender + challenger turns).

    A parameter is *cited* when its name appears; *misread* when a misread marker
    appears; *understood* when a correct marker appears and no misread marker does.
    """
    low = text.lower()
    scores: list[UnderstandingScore] = []
    for truth in truths:
        cited = truth.name.lower() in low
        # A parameter can only be misread/understood if it was actually invoked — a
        # generic marker word elsewhere in the debate is not a reading of THIS param.
        misread = cited and any(m.lower() in low for m in truth.misread_markers)
        understood = (
            cited
            and not misread
            and any(c.lower() in low for c in truth.correct_markers)
        )
        scores.append(UnderstandingScore(truth.name, cited, understood, misread))
    return tuple(scores)


def understanding_rate(scores: tuple[UnderstandingScore, ...]) -> float:
    """Fraction of *cited* parameters that were understood (0.0 when none cited).

    Scored over cited params only: a debate is judged on the parameters it actually
    invoked, not on every parameter in the key.
    """
    cited = [s for s in scores if s.cited]
    if not cited:
        return 0.0
    return sum(1 for s in cited if s.understood) / len(cited)


def misread_parameters(scores: tuple[UnderstandingScore, ...]) -> tuple[str, ...]:
    """Names of parameters read in a known-wrong way — the gate's teeth."""
    return tuple(s.name for s in scores if s.misread)
