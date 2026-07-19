# Sprint 128 Feed Resilience — Code Proof And Live Preflight

Date: 2026-07-16

## Code Proof

- `uv run pytest agents/provider/tests/test_finnhub_resilience.py agents/provider/tests/test_ingest_chunked.py surfaces/tests/test_dashboard_vitals.py --no-cov`
  - Result: 18 passed.
- `uv run pytest agents/provider/tests surfaces/tests/test_dashboard_vitals.py surfaces/tests/test_dashboard_verdict.py --no-cov`
  - Result: 155 passed, 2 skipped.
- `uv run ruff check ...`
  - Result: all touched-file checks passed.
- `uv run mypy agents/provider/fundamentals.py agents/provider/finnhub_resilience.py contracts/feed_notes.py agents/provider/market_fields.py agents/provider/composite.py agents/provider/ingest_chunked.py surfaces/dashboard/projections_vitals.py`
  - Result: success.

Covered behavior:

- Finnhub per-request pacing truth table: under-budget bursts do not sleep; the next request inside the minute sleeps; budget `0` disables sleeps for the unpaced live proof mode.
- Per-ticker failure attribution in `fundamentals`, `news`, `sectors`, and `earnings`; successful tickers remain in the feed payload.
- Bounded attributed notes: `<feed>_degraded:<count>:<first-N-tickers>:<error-label>`, including HTTP `429` labels.
- DRIFT-012 invariant: attributed enrichment faults do not set `used_fallback` when OHLCV is clean.
- `ingest_chunked` keeps both bare and attributed degraded notes through the merge.
- Dashboard degraded-feed counting treats old bare notes and new attributed notes as degraded feeds.

## Live Preflight

The sprint file's blocker note says not to start the full-universe live check until DRIFT-023 reads resolved. It still reads OPEN in `docs/laws/drift-register.md`.

Read-only Postgres preflight, run inside the project environment without printing the DSN:

```text
DEP-POSTGRES-01 RED postgres: reachable OperationalError
```

Decision: no paced or unpaced full-universe Finnhub ingest was started. No disposable run id was created, no graph nodes were written, and no teardown sweep was possible or required for Sprint 128 live artifacts in this session.
