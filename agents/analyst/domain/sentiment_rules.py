"""News-headline sentiment scoring rules and their pillar score.

Agent: analyst
Role: score Loughran-McDonald net tone over news headlines into a 0-100 pillar.
External I/O: none (reads the vendored LM word lists bundled under domain/data).
"""

from __future__ import annotations

import re
from pathlib import Path

# Curated finance-news headline terms the Loughran-McDonald master dictionary
# omits: LM was built for 10-K filings, so headline verbs (beat, surge, plunge,
# rally, jump, tumble, profit, record, upgrade, rise, fell, drop, ...) are
# absent. These are unioned with the full LM Positive/Negative lists below; the
# two sources are polarity-disjoint (asserted in tests). See data/README.md.
_HEADLINE_POSITIVE: frozenset[str] = frozenset(
    (  # noqa: SIM905 - compact word list, keeps the module < 200 lines
        "beat beats beating exceed exceeds exceeded surge surges surged soar "
        "soars soared rally rallies rallied gain gains gained profit profits "
        "profitable record records upgrade upgrades upgraded raise raised boost "
        "boosted strong stronger strength growth grew outperform outperformed "
        "rebound rebounds jump jumps jumped rise rises climb climbed win wins "
        "expansion improve improved improves optimistic upbeat bullish "
        "breakthrough approval approved rose higher"
    ).split()
)
_HEADLINE_NEGATIVE: frozenset[str] = frozenset(
    (  # noqa: SIM905 - compact word list, keeps the module < 200 lines
        "miss misses missed plunge plunges plunged slump slumps slumped fall "
        "falls fell drop drops dropped decline declines declined loss losses "
        "weak weaker weakness cut cuts downgrade downgrades downgraded lawsuit "
        "lawsuits investigation investigations probe probes fraud bankruptcy "
        "bankrupt default defaults warning warn warns warned recall recalls "
        "recalled layoff layoffs deficit breach litigation sue sued sinks sank "
        "tumble tumbles tumbled crash crashes crashed slide slides slid halt "
        "halted delay delayed shortfall concern concerns fear fears risk risks "
        "downturn recession selloff plummet plummeted slowdown struggle "
        "struggles struggling disappointing disappoint disappoints scandal "
        "resign resigns resigned bearish pessimistic lower weighed woes"
    ).split()
)

_DATA_DIR = Path(__file__).parent / "data"


def _load_lexicon(name: str) -> frozenset[str]:
    """Load a vendored LM word list: one lowercased word per line."""
    return frozenset((_DATA_DIR / name).read_text(encoding="utf-8").split())


# The binding sentiment lexicon: the full Loughran-McDonald master dictionary
# (Positive 354, Negative 2355) unioned with the curated headline terms. The two
# sources are polarity-disjoint, so the union needs no conflict resolution.
_POSITIVE: frozenset[str] = _load_lexicon("lm_positive.txt") | _HEADLINE_POSITIVE
_NEGATIVE: frozenset[str] = _load_lexicon("lm_negative.txt") | _HEADLINE_NEGATIVE


def _tokens(headline: str) -> list[str]:
    """Lowercase alphabetic tokens of one headline."""
    return re.findall(r"[a-z]+", headline.lower())


def _bounded(value: float) -> float:
    return max(0.0, min(100.0, value))


def score_sentiment(
    headlines: tuple[str, ...],
) -> tuple[float | None, dict[str, float]]:
    """Average the net-tone sub-score of each headline that carries a lexicon word.

    A headline's sub-score is ``50 + 50 * (pos - neg) / (pos + neg)`` (all-positive
    -> 100, balanced -> 50, all-negative -> 0). Headlines with no lexicon word carry
    no signal and are skipped (never diluted toward neutral). Returns ``(None, {})``
    when the input is empty or no headline is scored. Never raises.
    """
    sub_scores: list[float] = []
    total_pos = 0
    total_neg = 0
    for headline in headlines:
        tokens = _tokens(headline)
        pos = sum(1 for token in tokens if token in _POSITIVE)
        neg = sum(1 for token in tokens if token in _NEGATIVE)
        if pos + neg == 0:
            continue
        sub_scores.append(_bounded(50.0 + 50.0 * (pos - neg) / (pos + neg)))
        total_pos += pos
        total_neg += neg
    if not sub_scores:
        return None, {}
    mean = sum(sub_scores) / len(sub_scores)
    return mean, {
        "sentiment_articles": float(len(sub_scores)),
        "sentiment_positive": float(total_pos),
        "sentiment_negative": float(total_neg),
    }
