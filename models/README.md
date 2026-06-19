# models/

Trained model artifacts live here. These files are produced by offline training
scripts and are **not committed to git** (see `.gitignore`).

## Contents

| File | Produced by | Consumed by |
|---|---|---|
| `lgbm-return-v1.txt` | `scripts/train_lgbm_return.py` | `agents/forecaster/LightGBMModel` |

## Training

```bash
# 1. Export price_cache from Postgres
psql $DATABASE_URL -c "\copy (
    SELECT date::text, ticker, open, high, low, close, volume
    FROM price_cache ORDER BY ticker, date
) TO 'price_cache.csv' WITH CSV HEADER"

# 2. Train
python scripts/train_lgbm_return.py \
    --input  price_cache.csv \
    --output models/lgbm-return-v1.txt \
    --forward-days 5 \
    --train-fraction 0.7
```

The script prints the out-of-sample IC after training. The artifact is referenced
by `FORECASTER_RETURN_MODEL_PATH` (default: `models/lgbm-return-v1.txt`).
