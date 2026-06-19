"""Offline LightGBM return-model training script.

Reads a price_cache CSV export, builds feature/label pairs with a walk-forward
split, trains a LightGBM booster, and saves the artifact.

Usage
-----
    python scripts/train_lgbm_return.py \\
        --input  price_cache.csv \\
        --output models/lgbm-return-v1.txt \\
        --forward-days  5 \\
        --train-fraction 0.7

Getting the CSV from Postgres (v1 price_cache)
----------------------------------------------
    psql $DATABASE_URL -c "\\copy (
        SELECT date::text, ticker, open, high, low, close, volume
        FROM price_cache ORDER BY ticker, date
    ) TO 'price_cache.csv' WITH CSV HEADER"

The script expects columns: date, ticker, close, volume (open/high/low ignored).
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Keep sys.path clean: run from the repo root so the package is importable.
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.forecaster.domain.return_labels import build_label_rows
from agents.forecaster.model_trainer import train_and_save

_DEFAULT_HORIZONS = (1, 5, 20)
_DEFAULT_VOL_WINDOW = 20
_DEFAULT_MOM_WINDOW = 20


def _load_csv(path: str) -> dict[str, list[tuple[str, float, float]]]:
    """Read price_cache CSV into {ticker: [(date, close, volume), ...]}."""
    ticker_bars: dict[str, list[tuple[str, float, float]]] = {}
    with Path(path).open(newline="") as fh:
        for row in csv.DictReader(fh):
            ticker = row["ticker"]
            ticker_bars.setdefault(ticker, []).append(
                (row["date"], float(row["close"]), float(row["volume"]))
            )
    # Each ticker's bars arrive in date order from the ORDER BY clause; sort
    # defensively so the script is correct even without the ORDER BY.
    for bars in ticker_bars.values():
        bars.sort(key=lambda t: t[0])
    return ticker_bars


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description="Train the LightGBM return model.")
    parser.add_argument("--input", required=True, help="Path to price_cache CSV")
    parser.add_argument(
        "--output",
        default="models/lgbm-return-v1.txt",
        help="Booster artifact output path",
    )
    parser.add_argument(
        "--forward-days", type=int, default=5, help="Forward-return horizon in bars"
    )
    parser.add_argument(
        "--train-fraction",
        type=float,
        default=0.7,
        help="Walk-forward train/test split (0 < f < 1)",
    )
    args = parser.parse_args()

    print(f"Loading bars from {args.input} …")
    ticker_bars = _load_csv(args.input)
    n_bars = sum(len(v) for v in ticker_bars.values())
    print(f"  {n_bars} bars across {len(ticker_bars)} tickers")

    print(f"Building label rows (forward_days={args.forward_days}) …")
    rows = build_label_rows(
        ticker_bars,
        forward_days=args.forward_days,
        horizons=_DEFAULT_HORIZONS,
        volatility_window=_DEFAULT_VOL_WINDOW,
        momentum_window=_DEFAULT_MOM_WINDOW,
    )
    print(f"  {len(rows)} label rows")
    if not rows:
        print("No label rows — check that the CSV has enough history per ticker.")
        sys.exit(1)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    print(f"Training booster (train_fraction={args.train_fraction}) …")
    report = train_and_save(rows, args.output, train_fraction=args.train_fraction)

    print(
        f"Done.  train={report.train_size}  test={report.test_size}"
        f"  oos_ic={report.oos_ic:.4f}" if report.oos_ic is not None
        else f"Done.  train={report.train_size}  test={report.test_size}  oos_ic=N/A"
    )
    print(f"Artifact saved to {args.output}")


if __name__ == "__main__":
    main()
