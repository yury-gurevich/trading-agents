"""News-headline sentiment scoring rules and their pillar score.

Agent: analyst
Role: score Loughran-McDonald net tone over news headlines into a 0-100 pillar.
External I/O: none.
"""

from __future__ import annotations

import re

# Fixed reference rule (the rule itself, not tunable policy): a compact, curated
# finance-news lexicon drawn from the Loughran-McDonald positive/negative master
# categories (https://sraf.nd.edu/loughranmcdonald-master-dictionary/). High-signal
# headline terms only — the baseline champion; expanding to the full LM dictionary
# later is a sanctioned upgrade that does not change this interface.
_POSITIVE: frozenset[str] = frozenset(
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
_NEGATIVE: frozenset[str] = frozenset(
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
