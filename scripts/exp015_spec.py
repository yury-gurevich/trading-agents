"""EXP-015's fixed constants: the features, folds, models, inference and bar (S289).

Agent: tooling
Role: hold every number EXP-015's Process fixes, and the gaps DL-313 filled.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

EXPERIMENT = "EXP-015"
# The fifteen line features, then the five return features ranked within the sector.
RETURN_FEATURES = ("ret_5", "ret_20", "ret_60", "ret_120", "ret_252_21")
LINE_FEATURES = (
    *RETURN_FEATURES,
    "dist_252_high",
    "vol_20",
    "vol_60",
    "atr_pct",
    "beta_60",
    "resvol_60",
    "volratio_5_60",
    "volratio_20_120",
    "dollar_volume",
    "rs_120",
)
SECTOR_FEATURES = tuple(f"sector_{name}" for name in RETURN_FEATURES)
FEATURES = LINE_FEATURES + SECTOR_FEATURES
FEATURE_LOOKBACK = 252  # sessions the longest feature reads (DL-313 D4)
ATR_SESSIONS = 14  # DL-313 D3: the pre-registration names ATR % without a window
DOLLAR_VOLUME_SESSIONS = 20  # DL-313 D3

HORIZON = 10
HORIZONS = (5, 10, 20)  # 10 is barred; 5 and 20 report decay
MIN_SECONDARY_BARS = 253
FOLD_YEARS = tuple(range(2018, 2025))
HOLDOUT_START = date(2025, 1, 2)
PURGE_SESSIONS = 10
EMBARGO_SESSIONS = 5

RIDGE_LAMBDA = 1.0
LGBM_ROUNDS = 200
LGBM_PARAMS = {
    "objective": "regression",
    "max_depth": 3,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_data_in_leaf": 500,
    "feature_fraction": 0.8,
    "seed": 0,
    "deterministic": True,  # DL-313 D7: reproducible, not a tuning choice
    "num_threads": 1,
    "force_col_wise": True,
    "verbosity": -1,
}
MODELS = ("composite", "ridge", "lightgbm")

MIN_NAMES = 10  # DL-313 D6: a session ranks at least ten names, or it has no IC
STEP_SESSIONS = 10  # every 10th session: non-overlapping for inference and rebalancing
BLOCK = 20
RESAMPLES = 10_000
SEED = 0
COST_BPS = 25
DECILES = 10
BAR_IC_DIFFERENCE = 0.01
BAR_FOLDS_WON = 5
