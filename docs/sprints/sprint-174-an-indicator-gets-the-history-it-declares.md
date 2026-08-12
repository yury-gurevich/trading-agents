<!-- Agent: provider | Role: sprint spec — deliver the history the indicators declare, and stop asserting inputs that were never used -->
# S174 — an indicator gets the history it declares

**Closes:** item 2 of the work queue · **Opens from:** [DL-104](../design-log.md) class 3 (the one
veto class that checked out correct) · **Type:** fix ·
**Target version:** next available PATCH at merge — **do not pin it in this file**; three specs have
now been renumbered because they did ·
**Branch:** `sprint-174-an-indicator-gets-the-history-it-declares`

> Handover to a delegated coding agent. Everything under **Measured** was read off this repo or the
> live spine on 2026-08-12. Everything marked **Assumed** has **not** been verified — check it
> before building on it. Do not treat an unmarked claim as measured.

## Why

**Two of the five momentum indicators have never once computed in production, and the recommendation
text claims both of them by name.**

**Measured — the supply.** There are two paths to market data, and they disagree:

| Path | Window | Used in production? |
| --- | --- | --- |
| Request/response — [`analyst/agent.py:94`](../../agents/analyst/agent.py) sends a `DataRequest` carrying `_window()`, built from `lookback_days` **260**; [`provider/agent.py:97`](../../agents/provider/agent.py) honours it | **260 days** | **No** |
| Graph-pull — [`provider/poll.py:38`](../../agents/provider/poll.py) → `ingest_once` → [`ingest.py:143`](../../agents/provider/ingest.py) calls `_today_window()` with **no argument**, so `_DEFAULT_LOOKBACK_DAYS = 60`; the analyst reads the snapshot straight off the graph at [`analyst/poll.py:103`](../../agents/analyst/poll.py) | **60 days** | **Yes** |

The analyst's declared requirement travels correctly on the path we do not use, and is silently
dropped on the path we do. `_DEFAULT_LOOKBACK_DAYS` is also a **bare module literal** where
`kernel/config.py` requires a `tunable()` — *"every constant that influences processing or a
forecast"*. Nothing enforces that rule, which is why it was never caught.

**Measured — the consequence.** 60 calendar days ≈ **41 trading bars** (`sched-2026-08-11` delivered
exactly 41 for all 99 tickers). Against the declared periods:

| Indicator | Needs | At 41 bars |
| --- | --- | --- |
| `rsi_period` 14 | 15 | ✅ |
| `bollinger_window` 20 | 20 | ✅ |
| `macd_slow` 26 + `macd_signal` 9 | ≈35 | ✅ — 6 bars of margin |
| `ema_long_period` **50** | 50 | ❌ **never computes** |
| `sma_long_period` **200** | 200 | ❌ **never computes** |

[`technical_rules.py:139-148`](../../agents/analyst/domain/technical_rules.py) appends each score only
`if x is not None`, so the two absent indicators leave **no trace at all** — not a fault, not a note,
not a lower confidence. `min_history_bars = 2` passes everything through.

**Measured — the false claim.** Two hardcoded strings assert the missing inputs by name:
[`recommend.py:98-102`](../../agents/analyst/domain/recommend.py) (*"composite technical score (RSI,
MACD, Bollinger, SMA-200 distance, and EMA crossover)"*) and
[`agent.py:120`](../../agents/analyst/agent.py). Every recommendation the system has ever produced
carries one. The LLM veto found this; our own gates cannot see it.

## The design decision this sprint has to make

The analyst may not import the provider and vice versa. Pick **one** route for the requirement to
travel, and record the rejected ones in `docs/design-log.md` per LAW-06:

1. **Stamp the window on the `RunRequest`** — the dispatcher already places `tickers`, and
   `poll.py:41` already reads them. Symmetrical, typed, one authority per run. **Recommended.**
2. **Put the required history in the pack** (`orchestration/packs/`) — also legal, but adds a second
   place the number lives.
3. **A provider `tunable()` set to 260** — cheapest, and duplicates the analyst's number by
   construction. If you choose this, say in the `why=` that it must track `sma_long_period`.
4. **Derive it** from the largest declared indicator period × a calendar-to-trading-day factor —
   self-maintaining, and the only option that cannot drift when someone changes `sma_long_period`.

Whichever wins, `_DEFAULT_LOOKBACK_DAYS` must stop being a bare literal.

## Steps, in order

1. **Reproduce before changing anything.** Score one ticker off `sched-2026-08-11`'s snapshot and
   record which indicators returned `None`. This is the before half of the proof.
2. **Fix the supply** by the route chosen above. The provider must fetch enough bars for
   `sma_long_period`, not a number that happens to be 260.
3. **Make a short series visible, not silent.** When an indicator cannot compute, the recommendation
   must carry that fact. 🪤 Read the pack trap below before choosing where to put it.
4. **Stop the rationale asserting inputs it did not use.** Build the summary from the indicators that
   actually scored. Both strings.
5. **Raise `min_history_bars`, or justify leaving it at 2** in its `why=`. At 2 it is not a guard.
6. **Full CI cycle** — Python changes, so `make ci` (redirected to a file, never piped), push the
   branch, `make gate-ran` from the worktree, then merge.

## Success factors

- [ ] A run scored with **≥ 200 bars per ticker**, measured off the graph, not inferred from config.
- [ ] `sma_distance_pct` and `ema_spread_pct` both present in a real recommendation's scores — the
      first time either has appeared in production.
- [ ] The before/after scored-indicator list for one named ticker, quoted in the closeout.
- [ ] No recommendation text names an indicator that did not score. Add a test that would have caught
      today's defect — assert the **rendered string against the scored set**, not against config.
- [ ] `_DEFAULT_LOOKBACK_DAYS` is gone as a bare literal.
- [ ] The rejected routes recorded in `docs/design-log.md`.
- [ ] `make ci` green with the 100 % coverage floor; `make gate-ran` exits 0 on the final SHA.

## Traps

- 🪤 **Check whether your step-3 choice moves the vocabulary pack.** `RunRequest` is **not**
  property-enforced, so route 1 is safe. **`Recommendation` is** — its enforced properties are
  `action`, `confidence`, `quant_metrics`, `technical_score`, `exit_trigger` and the
  `stop_target_*` family. A **new top-level property on `Recommendation` moves the pack**, which
  forces a full `pwsh infra/deploy-agents.ps1 up` instead of an image-only retag — and a full `up`
  still discards operator env until [S169](sprint-169-one-switch-and-a-deploy-that-keeps-it.md)
  lands (`MAX_POSITION_PCT` 0.01 → 0.10 is a 10× position size, silently). **Assumed:** that riding
  inside the existing `quant_metrics` avoids the pack move — verify before relying on it. If you
  cannot avoid the move, say so in the closeout and stop; do not deploy past S169.
- 🪤 **The payload gets roughly 5× bigger.** 41 → 200+ bars × 99 tickers takes the snapshot from
  **4,059** bars to **≈20,000**, stored as one JSON property on the `MarketData` node. **Assumed:**
  that Postgres and the bus carry it unchanged. Measure node size and ingest duration before and
  after, and quote both.
- 🪤 **Vendor cost and limits are unmeasured.** Alpaca is the primary batch OHLCV source, Tiingo the
  fallback at **500 symbols/month, 50 requests/hour** (`docs/laws/tiingo-usage-limits.md`). A 5×
  history request may change request counts, or may cost nothing extra because of batching.
  **Measure it; do not assume either way.**
- 🪤 **A longer window changes scores, so it changes trades.** Two new indicators start contributing
  to every composite. Expect the candidate set and the confidences to shift, and do not read that
  as a regression.
- 🪤 **MACD has only ~6 bars of margin today.** If the window ever shortens again, MACD is the next
  silent casualty. A test pinning *bars available ≥ largest declared period* is worth more than one
  pinning 260.

## Handover — paste this to Codex

Everything below is the whole brief. It deliberately repeats the rules Codex cannot infer from the
code, and nothing else — the reasoning lives above and is meant to be read, not summarised.

```text
Work item: S174 — an indicator gets the history it declares.
Repo: trading-agents. Read docs/sprints/sprint-174-an-indicator-gets-the-history-it-declares.md
in full before writing anything. Read CLAUDE.md. Read docs/INDEX.md before opening any docs folder.

WHAT IS WRONG
Two of five momentum indicators (SMA-200 distance, EMA crossover) have never computed in
production, because the graph-pull path fetches 60 calendar days (~41 bars) while the indicators
need 200 and 50. They return None and are dropped silently. Two hardcoded strings claim both
indicators by name on every recommendation. Fix the supply, make a short series visible instead of
silent, and stop the text asserting inputs that did not score.

HOW TO WORK
- Branch first, before any code: sprint-174-an-indicator-gets-the-history-it-declares.
  Never commit sprint work to main. Work in a git worktree.
- The spec names four routes for carrying the history requirement across the agent boundary and
  recommends one. Choose deliberately, then record the routes you rejected and why in
  docs/design-log.md (LAW-06). A decision discussed but unrecorded counts as not made.
- uv only: `uv pip`, `uv run`. Bare pip resolves the wrong interpreter.
- Agents never import other agents. They talk via typed messages. import-linter enforces it.
- Modules hard-block at 200 lines. Split before you hit it. Never use noqa to bypass.
- Every constant that influences a forecast is declared with kernel.config.tunable(), with a `why=`.
  That rule is exactly what this sprint is fixing; do not add a new bare literal while fixing one.

HOW TO PROVE IT (this is the part that gets rejected if skipped)
- LAW-02: success is proven, never assumed. Do not report an intent as an outcome.
- Run the full gate: `make ci > ci.txt 2>&1 ; echo $?` then READ ci.txt. Never `make ci | tail` —
  a pipe reports tail's exit code, so a real failure reads as green. All 11 steps, 100% coverage.
- Push the branch, then run `make gate-ran` FROM THE WORKTREE whose HEAD is the commit you are
  proving. It ignores any SHA= argument and resolves from the working directory; run it from the
  wrong directory and it proves main instead, greenly. Check the SHA it prints against
  `git rev-parse HEAD`. Merge only after it exits 0. No PR is required.
- Measure before and after. The before half (which indicators returned None on sched-2026-08-11)
  is a required deliverable, not a nicety.
- Fill in the "Closeout — evidence" block at the bottom of the spec with real measurements before
  handing back. A handback with the placeholder comment still in it is not accepted.

WHEN TO STOP AND ASK
- If your chosen design adds a new top-level property to the Recommendation label, the vocabulary
  pack moves, which forces a full `deploy-agents.ps1 up` — and a full `up` still silently discards
  operator env (S169, unfixed). Do not deploy past that. Say so in the closeout and stop.
- If the 5x larger market-data payload breaks or materially slows the graph write, stop and report
  the measurement rather than working around it.
- Anything marked "Assumed" in the spec is unverified. Verify it or say you did not.
```

## Closeout — evidence

**Result:** implemented on branch `sprint-174-an-indicator-gets-the-history-it-declares`.

**Files changed:** `agents/analyst/history_requirements.py`,
`agents/analyst/domain/recommend_summary.py`, `orchestration/history_window.py`,
`orchestration/tests/test_history_window.py`, plus focused edits in
`agents/analyst/{agent.py,settings.py,domain/recommend.py,domain/technical_rules.py}`,
`agents/provider/{ingest.py,ingest_chunked.py,poll.py}`,
`contracts/provider.py`, `orchestration/start.py`, matching tests, `docs/design-log.md`,
`docs/STATE.md`, `pyproject.toml`, and `uv.lock`.

**Route chosen:** [DL-107](../design-log.md#dl-107---s174-carries-declared-indicator-history-on-the-runrequest---status-decided-2026-08-12)
uses `RunRequest.lookback_days` plus `RunRequest.required_history_bars`. The dispatcher derives the
calendar lookback from analyst-declared bar requirements and the NYSE session calendar, with the
provider `max_staleness_days` buffer so a same-day unpublished bar does not drop the retained series
below the required bar count. The provider graph-pull path rejects missing, non-positive, or too
short declarations before ingest.

**Routes rejected:** pack-level history was rejected because it would duplicate analyst policy;
provider-owned `tunable(260)` was rejected because it recreates the drift bug; provider-side
derivation was rejected because provider does not own indicator policy; a new top-level
`Recommendation` property for missing indicators was rejected because `Recommendation` is
property-enforced. Short-series evidence is carried inside existing `Recommendation.quant_metrics`
as `*_missing_bars`.

**Before measurement, production graph (`sched-2026-08-11`):**

```text
before_run_id=sched-2026-08-11
before_tickers=99
before_total_bars=4059
before_bars_min=41
before_bars_max=41
before_snapshot_json_bytes=635151
before_ingest_duration_recorded=False
before_named_ticker=XOM
before_named_bars=41
before_named_scored=rsi,macd_histogram,bollinger_position
before_named_missing=sma_distance_pct,ema_spread_pct
```

The graph node had no ingest-duration property, so production before duration is **not recorded**.
For an apples-to-apples local live-source graph probe of the same 60-day OHLCV window:

```text
local_before_60d_duration_seconds=2.037
local_before_60d_total_bars=3960
local_before_60d_bars_min=40
local_before_60d_bars_max=40
local_before_60d_snapshot_json_bytes=447617
local_before_60d_alpaca_pages=1
```

**After measurement, local live-source graph probe:** no live production work item was enqueued,
because an unscanned `MarketData` node is consumed by the deployed graph-pull fleet. The probe used
`InMemoryGraphStore` plus the live Alpaca OHLCV source and the same provider/analyst contracts.

```text
after_as_of=2026-08-12
after_lookback_days=295
after_duration_seconds=5.381
after_total_bars=19796
after_bars_min=0
after_bars_max=202
after_snapshot_json_bytes=2231143
after_alpaca_pages=2
after_quality_used_fallback=False
after_quality_notes=
after_named_ticker=XOM
after_named_bars=202
after_named_scored=rsi,macd_histogram,bollinger_position,sma_distance_pct,ema_spread_pct
after_named_missing=
after_recommendations=60
after_rejections=39
after_real_rec_ticker=AAPL
after_real_rec_metrics=bollinger_position,ema_spread_pct,macd_histogram,rsi,sma_distance_pct
after_real_rec_summary=AAPL cleared the neutral confidence gate on its composite technical score (RSI, MACD, Bollinger, SMA-200 distance, and EMA crossover).
after_rationale_ok=True
```

The all-99 after probe retained 98 tickers: `CHTR` was excluded by the existing anomalous-ticker
guard, not by short history:

```text
lookback_days=295
requested=99
total_bars=19796
bars_min=0
bars_max=202
zeros=CHTR
short=
quality_requested=99
quality_returned=98
quality_used_fallback=False
quality_anomalous=CHTR
```

A clean retained-universe probe excluding that anomalous ticker proved `>= 200` bars per ticker:

```text
clean_after_tickers=98
clean_after_lookback_days=295
clean_after_duration_seconds=5.519
clean_after_total_bars=19796
clean_after_bars_min=202
clean_after_bars_max=202
clean_after_snapshot_json_bytes=2231137
clean_after_alpaca_pages=2
clean_after_quality_used_fallback=False
clean_after_quality_anomalous=
clean_after_recommendations=60
clean_after_rejections=38
clean_after_real_rec_ticker=AAPL
clean_after_real_rec_metrics=bollinger_position,ema_spread_pct,macd_histogram,rsi,sma_distance_pct
clean_after_real_rec_summary=AAPL cleared the neutral confidence gate on its composite technical score (RSI, MACD, Bollinger, SMA-200 distance, and EMA crossover).
clean_after_rationale_ok=True
```

**Vocabulary pack:** did **not** move. `orchestration/packs/trading_graph_vocabulary.json` is
unchanged. The verified pack assumption holds because `Recommendation.quant_metrics` is already an
allowed property; no new top-level `Recommendation` property was added.

**Vendor/limit measurement:** Alpaca OHLCV pages changed from 1 page for the 60-day probe to 2 pages
for the 295-day S174 probe. Tiingo fallback was not called because Alpaca succeeded. Full Finnhub/AV
enrichment was not remeasured in the after probe; the safe proof intentionally used OHLCV-only to
avoid injecting live work or spending per-ticker enrichment quota. That unmeasured part is called out
here rather than assumed.

**`make ci` evidence:** ran unpiped as `make ci > ci.txt 2>&1; $exit = $LASTEXITCODE; Write-Output
$exit` from the S174 worktree; exit code `0`.

```text
uv run ruff check . --output-format=github
uv run ruff format --check .
973 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
Success: no issues found in 802 source files
uv run lint-imports
Contracts: 4 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run pytest
TOTAL                                                14519      0   3078      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
================= 2234 passed, 6 skipped in 70.80s (0:01:10) ==================
uv run pip-audit
No known vulnerabilities found
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 5 new file(s)
```

**Remote gate:** `make gate-ran` must be run after the final commit is pushed from the worktree
whose `HEAD` is being proved. Its output is intentionally not pre-pasted into this committed
closeout, because editing this file after the gate would change the SHA the gate proved.
