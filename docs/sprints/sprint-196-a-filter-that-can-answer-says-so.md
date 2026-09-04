<!-- Agent: planning | Role: sprint record — make a known-absent earnings date a pass, not a skip -->
# Sprint 196 — a filter that can answer says so

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-196-a-filter-that-can-answer-says-so`
**Status:** BUILT
**Version:** next available PATCH at merge — `0.94.10`
**Effort:** S
**Decisions:** [`DL-152`](../design-log.md) — the earnings map declares its own scope, and why the
scanner may not infer it.

---

## Goal

`earnings_window` records a **pass** when the producer's earnings horizon proves no earnings are due,
and records **skipped** only when it genuinely does not know.

## Why (context)

### Measured, 2026-09-04 — on the live `verify-2026-09-04-s195-beta` run

- **This is the last thing blocking a trade.** S195 made `max_beta` evaluate (20/20 candidates, two
  names dropped). The deliberator still vetoed both approved buys, and its stated ground reduced to
  one clause: *"earnings_window was skipped, not passed — USB was never tested against an earnings
  date"*, and for AVGO *"the earnings_window check never ran"*. Four consecutive nights, **zero**
  submissions.
- **It is not a feed defect.** `finnhub_earnings_lookahead_days` is **30**
  (`agents/provider/settings_feeds.py:124`); `earnings_exclusion_days` is **5**
  (`agents/scanner/settings.py:70`). On `sched-2026-09-03` the map held 6 dates for 99 tickers, all
  genuinely in September — the correct answer to a 30-day question, with `quality.notes` empty.
- **The gate throws that answer away.** `evaluate_filters` branches on `"days_to_earnings" in
  features` and files every absence under `skipped`, so a ticker *proven* to have no earnings for 30
  days is reported identically to one nobody asked about. **20 of 20** candidates, every run.

## Scope — and what is deliberately NOT here

In scope: the producer states the horizon its earnings map covers; the scanner reads absence inside
that horizon as an answer.

### Out of scope

- Widening `earnings_lookahead_days` or narrowing `earnings_exclusion_days`. Both are tunables with
  live consequences; this sprint changes what the existing numbers *mean to a reader*, not the numbers.
- The same treatment for other skipped gates. `max_beta` is the only other one and S195 fixed it at
  the source; no third gate currently skips.
- Anything about the deliberator. If it still vetoes after this, that is a verdict about the trade,
  not about missing evidence — and that is S173's question, not this one.

### The road not taken (LAW-06)

- **Let the scanner assume a 30-day horizon.** Rejected: the scanner cannot import provider settings
  (agents are islands), and hardcoding a second copy of the number is the PARAM-divergence class of
  work-queue item 33. Worse, it would be *wrong the moment the tunable moves*, and silently so.
- **Have the provider write a sentinel date (e.g. `9999-12-31`) for "none due".** Rejected: it puts a
  fabricated fact in a data map, and every consumer must then know the sentinel. The horizon is
  metadata about the map, so it belongs beside the map, not inside it.
- **Treat absence as a pass unconditionally.** Rejected outright: that is the failure mode this
  repo exists to avoid. A degraded feed produces gaps that look exactly like "no earnings due", and
  passing them would certify risk nobody measured.

## Design decisions

1. **Who knows the horizon?** The provider — it issued the query. It now publishes
   `MarketData.earnings_horizon_days`, and the docstring states the contract: a number means the map
   is *complete* for that many days; `None` means absence proves nothing.
2. **When may it claim one?** Only on a clean fetch. Unrequested → `None`. Any `earnings_degraded`
   note → `None`. In the chunked path, the horizon survives only if **every** chunk agrees, because
   the reassembled batch is one unit downstream.
3. **When is absence an answer?** When the horizon **strictly exceeds** `earnings_exclusion_days`.
   An equal horizon leaves the boundary day unproven, so it stays a skip.

## Blast radius — line counts measured 2026-09-04 after the change

| File | Lines | Change |
| --- | --- | --- |
| `contracts/provider.py` | 165 | `MarketData.earnings_horizon_days` + its meaning |
| `agents/provider/market_fields.py` | 166 | `_earnings_horizon` — clean fetches only |
| `agents/provider/agent.py` | 163 | Supplies the settings value, publishes the result |
| `agents/provider/ingest_chunked.py` | 159 | `_merged_earnings_horizon` — unanimous or nothing |
| `agents/scanner/domain/filter_attestation.py` | 64 | `_absence_is_an_answer`, the gate decision |
| `agents/scanner/domain/filters.py` | 139 | Threads the horizon to the gate |
| `agents/scanner/poll.py` | 78 | Graph-pull path (the deployed one) |
| `agents/scanner/agent.py` | 184 | In-process path |

All under the 200 hard block. `MarketData` is not one of the seven property-enforced labels, so the
vocabulary pack does not move and the deploy stays an image-only retag.

## Test plan

| # | Test | Proves |
| --- | --- | --- |
| 1 | `test_absence_passes_when_the_horizon_covers_the_exclusion_window` | the fix |
| 2 | `test_absence_is_skipped_when_no_horizon_was_declared` | silence still means silence |
| 3 | `test_absence_is_skipped_when_the_horizon_only_equals_the_window` | the boundary day stays unproven |
| 4 | `test_a_known_date_still_decides_regardless_of_horizon` | the horizon speaks only about absence |
| 5 | `test_graph_pull_scan_passes_the_gate_when_the_snapshot_declares_a_horizon` | **the tripwire**, on the deployed path |
| 6 | `test_graph_pull_scan_skips_the_gate_without_a_horizon` | the pre-S196 shape, pinned |
| 7 | `test_a_clean_earnings_fetch_declares_the_settings_horizon` | the claim matches what was queried |
| 8 | `test_an_empty_but_clean_earnings_fetch_still_declares_the_horizon` | the common case is an answer |
| 9 | `test_an_unrequested_earnings_feed_declares_nothing` | no query, no claim |
| 10 | `test_a_degraded_earnings_feed_withholds_the_horizon` | **the safety guard** |
| 11 | `test_chunked_merge_keeps_a_horizon_every_chunk_agrees_on` | the deployed chunked path |
| 12 | `test_chunked_merge_drops_the_horizon_when_one_chunk_degraded` | one bad chunk taints the claim |

## Success factors

- `earnings_window` appears in `survived_filters` on the next deployed run.
- A degraded earnings feed still produces `skipped`, not a false pass.
- `make ci` exit 0 with the 100 % floor intact.

## Traps

- 🪤 **A false pass is worse than a skip.** The skip was over-cautious; certifying an unmeasured
  earnings date would be dishonest in the direction that loses money. Test 10 is the one that matters.
- 🪤 **The chunked path is the deployed path.** 99 tickers exceed `ingest_chunk_size`, so a horizon
  set only in `ingest_once` would change nothing in the fleet.
- 🪤 `agents/scanner/agent.py` is one of **11 committed `.py` files carrying CRLF** while the rest of
  the repo is LF. A byte-level edit there must preserve `\r\n` or the diff explodes. Filed separately.

## Law reading record

`agents/scanner/laws/laws.md` (LOCKED v1, S70) and `agents/provider/laws/laws.md` (LOCKED v1, S69)
read before coding. No clause changes. The scanner's duty to attribute every drop is unchanged; this
sprint makes an attribution *more* accurate. The provider's duty to be honest about data quality is
strengthened, not altered — it now declines to claim a horizon it cannot stand behind.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/AppData/Local/Temp/wt-s196`,
branch `sprint-196-a-filter-that-can-answer-says-so`, `.env` **no**.

**Result:** the provider declares how far its earnings map reaches and withholds that claim on any
degraded or unrequested fetch; the scanner reads absence inside a covering horizon as a pass. On the
graph-pull path — the deployed one — `earnings_window` moves from `skipped_filters` to
`survived_filters` when, and only when, the snapshot carries a horizon.

**Files changed:** `contracts/provider.py`, `agents/provider/market_fields.py`,
`agents/provider/agent.py`, `agents/provider/ingest_chunked.py`,
`agents/scanner/domain/filter_attestation.py`, `agents/scanner/domain/filters.py`,
`agents/scanner/poll.py`, `agents/scanner/agent.py`,
`agents/scanner/tests/test_scanner_earnings_horizon.py` (new),
`agents/provider/tests/test_provider_earnings_horizon.py` (new), `pyproject.toml`, `uv.lock`.

**Design decisions:** recorded as [`DL-152`](../design-log.md).

**Proof — the red run first** (implementation stashed, tests left in place):

```text
E   TypeError: evaluate_filters() takes 2 positional arguments but 3 were given
E   TypeError: collect_optional_fields() got an unexpected keyword argument
    'earnings_lookahead_days'
12 failed
```

**Proof — the green run:**

```text
2487 passed, 6 skipped in 93.64s
TOTAL   15680   0   3374   0   100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
```

**Guards planted:** test 6 pins the pre-S196 shape (no horizon → `skipped`, never `survived`), and
test 10 pins the safety direction (degraded feed → no horizon → no pass). Both were verified failing
against the stashed implementation before being trusted.

**`make ci`:** redirected to a file, exit code **0**. 2487 passed, 6 skipped, coverage 100.00 %.
pip-audit clean, detect-secrets clean.

**`make gate-ran`:** recorded at merge in `docs/STATE.md`.

**Not met / verified failing:** not yet observed in the fleet — the running images are `:s195`. And
this sprint does not promise a trade: it removes the deliberator's *stated* objection, but the judge
may find another. That is the honest limit of what a labelling fix can claim.

---

## Return notes

- Built in the same session as S195, for the same reason: Codex is out of quota until 2026-09-07.
- The pair is one story. S195 gave the beta gate its denominator; S196 lets the earnings gate report
  what it already knew. Both were a producer failing to state something a consumer needed.
- If tonight's run still submits nothing, the next question is the deliberator's own standard, not
  the scanner's evidence — S173, not another gate fix.
