"""Alpha158 cross-sectional pillar scoring.

Agent: analyst
Role: map a single ticker's AlphaFeatureRow to a 0-100 score by z-normalising each
      feature across a universe of candidate rows and applying a logistic aggregation.
External I/O: none.
"""

from __future__ import annotations

import dataclasses
import math

from agents.analyst.domain.alpha_features import AlphaFeatureRow

_FIELDS = [f.name for f in dataclasses.fields(AlphaFeatureRow)]


def score_alpha158(
    features: AlphaFeatureRow,
    universe: tuple[AlphaFeatureRow, ...],
) -> float:
    """Return a 0-100 score via equal-weighted cross-sectional z-score aggregation.

    Each of the 22 features is z-normalised across the universe of candidate rows,
    then averaged; the mean z-score is mapped to [0, 100] via the logistic function
    centred at 0 (z=0 → 50, one-sigma above → ~73, two-sigma → ~88).

    When a feature has zero cross-sectional variance its z contribution is 0.0.
    If ``features`` is not already in ``universe`` it is appended before scoring.
    """
    rows = list(universe) if features in universe else [*universe, features]
    n = len(rows)

    z_scores: list[float] = []
    for field in _FIELDS:
        vals = [getattr(r, field) for r in rows]
        mean = sum(vals) / n
        std = math.sqrt(sum((v - mean) ** 2 for v in vals) / n)
        z = (getattr(features, field) - mean) / std if std > 1e-9 else 0.0
        z_scores.append(z)

    mean_z = sum(z_scores) / len(z_scores)
    return 100.0 / (1.0 + math.exp(-mean_z))
