<!-- Agent: planning | Role: sprint handover -->
# Sprint 128 — Feed resilience: DRIFT-021 (per-request pacing, per-ticker degradation, durable feed faults)

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-128-feed-resilience`
**Status:** ready for handover (packaged 2026-07-16)
**Effort:** M

---

## Why this sprint

**Every scheduled fleet run since 2026-07-07 has run at half signal.** All four Finnhub
enrichment feeds (fundamentals/news/sectors/earnings) arrive `*_degraded` nightly, so the
analyst scores on technicals alone — on `sched-2026-07-10` the top candidate hit 0.595 vs the
0.600 floor and the day traded nothing for a reason that was partly infrastructure, not market.
The diagnosis is closed (DRIFT-021, 2026-07-12 `/diagnose-feeds`): ~99 tickers × 4 Finnhub
endpoints ≈ 400 sequential calls against the 60 req/min free tier with **no per-request
pacing**, and one 429 inside a feed's single fault boundary discards the **whole feed**,
partial results included. The faults are also invisible after scale-to-zero: one console line
in Log Analytics, zero graph evidence beyond the bare note.

Strategic kicker: a working nightly news feed is the "live news runway" the P12 sentiment
scorecard-run has been parked behind.

> **BLOCKER NOTE (2026-07-16, DRIFT-023):** the Neon spine is quota-blocked (free-tier data
> transfer exhausted). Parts A–C (code + unit gate) can proceed; the **functionality check
> requires the spine restored** — do not start the live check until DRIFT-023 reads resolved
> in `docs/laws/drift-register.md`.

## What already exists (read before estimating)

- **The whole-feed boundary**: `agents/provider/market_fields.py::_fetch_optional` wraps each
  feed's *entire* multi-ticker fetch in one `fault_boundary`; the per-ticker loops live in the
  Finnhub source (`agents/provider/fundamentals.py` — `for ticker in tickers` in each
  `fetch_*`). `market_fields.py` is at 151 lines (warning threshold) — new logic goes in the
  source layer, not there.
- **The precedent to extend — DRIFT-014**: pooled OHLCV anomalies stopped tainting the batch by
  attributing the fault to its own ticker (`DataQualityTrace.anomalous_tickers`), excluding it,
  and keeping the clean remainder. Same shape here, per feed.
- **DRIFT-012 invariant (must survive)**: an optional-field fault never sets `used_fallback` —
  a degraded enrichment field forgoes that signal, never the whole analysis.
- **Chunked ingest**: `ingest_chunked.py` sleeps only **between chunks** and merges per-chunk
  `*_degraded` notes across the merge — any new note format must survive that merge.
- **Sector caps** already survive vendor loss via the DRIFT-013 sector cache.
- **Sentiment** is a separate vendor path (`av_sentiment.py`) and is NOT in scope; the four
  Finnhub feeds are.
- **Quality trace** already reaches the graph inside the MarketData artifact — notes persisted
  there are durable and readable by `/diagnose-feeds` and the dashboard.

## Decisions taken at packaging (LAW-06)

1. **Pace Finnhub per request, inside the source.** A blocking rate budget in the Finnhub data
   source (default **55 req/min** — safety margin under the vendor's 60), declared as a
   `tunable(..., why=...)` with an env override, applied to every Finnhub HTTP call. At ~99
   tickers × 4 feeds ≈ 396 calls this is ~7¼ minutes — comfortably inside the 22:25–00:30
   fleet window. *Ruled out:* paying for the Finnhub tier (pacing is free and sufficient at
   this universe size); swapping vendors (ADR-0006 stands); pacing at the chunk level only
   (the 60/min limit is per-request — chunk sleeps demonstrably don't prevent 429s).
2. **Per-ticker fault granularity, DRIFT-014 style.** Each per-ticker fetch inside a feed
   catches its own failure, attributes it to the ticker, and keeps every other ticker's
   result. A feed note upgrades from the bare `fundamentals_degraded` to a bounded attributed
   form `fundamentals_degraded:<n>:<t1,t2,…>` (first N tickers, N a tunable, so notes stay
   bounded at S&P-500 scale); a whole-feed note remains only for a genuinely whole-feed
   failure (auth, transport, zero results). The DRIFT-012 invariant is untouched. Notes must
   merge correctly across `ingest_chunked`. *Ruled out:* moving the per-ticker boundary into
   `market_fields.py` (module at its size limit; granularity is knowledge the source layer
   owns); retrying failed tickers inside the run (pacing removes the cause; retry loops on a
   free tier invite thundering-herd 429s).
3. **Durability rides the quality trace — no new node type.** The attributed notes persist in
   the MarketData artifact already on the graph, making the *which tickers, which feed* story
   durable after scale-to-zero; the fault exception class is appended to the note detail
   (e.g. `…:429`). The existing FaultSink routing stays as-is. *Ruled out (this sprint):* a
   new graph `Fault` node type or Log Analytics ingestion pipeline — the trace answer is
   sufficient for diagnosis and this stays a PATCH-sized fix.
4. **The live rate limit is the fault injector.** The per-ticker granularity proof runs the
   real full universe against live Finnhub **once with pacing disabled** — today's nightly
   behavior — and must show per-ticker 429 attribution with the successful majority kept.
   No mocked 429s in the live check (unit tests mock; the functionality check does not).

## Codex kickoff (paste this)

> Execute **Sprint 128 — feed resilience** exactly as specified in this file
> (`docs/sprints/sprint-128-feed-resilience.md`). Read first: **DRIFT-021** in
> `docs/laws/drift-register.md` (the diagnosis is the spec) and DRIFT-012/013/014 (the
> invariants and the pattern you are extending); `agents/provider/market_fields.py` (the
> boundary you are NOT growing), `agents/provider/fundamentals.py` (the source loops you are
> hardening), `agents/provider/ingest_chunked.py` (the note-merge your format must survive),
> `agents/provider/settings.py` (where the tunables live);
> `docs/laws/tiingo-usage-limits.md` for the vendor-budget precedent; design-log **DL-48**
> (the process contract this kickoff enforces).
>
> **Contract (DL-48 — enforced):**
>
> - **Start:** `git pull` on `main` — `pyproject.toml` must read **0.71.00** (stop and report
>   if not). Branch `sprint-128-feed-resilience`. Bump **PATCH → 0.71.01** (drift correction,
>   DRIFT-014 precedent) + `uv lock`.
> - **Drift rule:** before handback, `git fetch`; if `origin/main` moved, merge it into the
>   branch, re-run the full gate on the merge result, record what moved in the Return notes.
> - **Secrets rule** (CLAUDE.md): no credential ever becomes a file in the repo tree; the
>   Finnhub key is already in `.env`.
> - **Handback rule:** the last two things you do are the Closeout block and the Return
>   notes; an incomplete handback is bounced, not repaired.
> - Hard gate: `make ci` green with the **exit code captured** (never through a masking
>   pipe), 100 % coverage, ≤200-line modules (`market_fields.py` must not grow past its
>   current 151), headers, tunables for every threshold.
>
> **Work items:**
>
> - **A (pacing):** a per-request rate budget on every Finnhub HTTP call, default 55 req/min,
>   `tunable(..., why=...)` in provider settings with env override; injectable clock/sleep so
>   unit tests run instantly; unit truth-table (bursts under the budget pass unpaced, the
>   N+1th call inside the window waits, budget disabled = no waits).
> - **B (per-ticker granularity):** per-ticker failure attribution inside each of the four
>   Finnhub feed loops (fundamentals/news/sectors/earnings): one ticker's failure keeps every
>   other ticker's result; bounded attributed note
>   `<feed>_degraded:<count>:<first-N-tickers>:<error-class>`; whole-feed note only on
>   genuinely whole-feed failure; DRIFT-012 invariant pinned by test (`used_fallback` never
>   set by enrichment faults); notes merge correctly across `ingest_chunked` (test the merge).
> - **C (consumers keep working):** `/diagnose-feeds` skill doc, the dashboard degraded-feeds
>   vital, and the verdict warning all still parse the new note format — update the note
>   parser(s) in one place if they string-match; add a regression test that the old bare form
>   and the new attributed form both count as "degraded feed" where counting happens.
> - **Functionality check (LAW-02), live Finnhub + live Neon, provider stage ONLY — no
>   scanner/PM/execution, no broker calls, no `sched-*` run ids:** (1) **paced full-universe
>   ingest** (the committed sp100 file, all four feeds) under a disposable run id → all four
>   feeds populated, **zero whole-feed degraded notes**, any per-ticker attributions named;
>   record elapsed time and that it fits the fleet window; (2) **granularity proof**: one
>   unpaced full-universe ingest (today's nightly behavior) → per-ticker 429 attributions
>   with the successful majority kept and `used_fallback` false — the live rate limit is the
>   fault injector, do not mock it; (3) query the MarketData node on Neon and show the
>   attributed notes persisted (durability after scale-to-zero). Record in
>   `docs/laws/functionality-checks.md` + evidence under
>   `docs/reports/sprint-128-feed-resilience/`; name every node created; **tear down** the
>   disposable-run artifacts to zero and show the sweep count.
> - **Wrap up:** update **DRIFT-021 → CORRECTED** in `docs/laws/drift-register.md` citing the
>   regression tests + live proof (follow the DRIFT-014 row's format); README index row;
>   Closeout + Return notes; push, hand back. **Do not merge.**

## Guardrails

- Provider stage only in the live check: no broker, no downstream agents, no production
  `sched-*` run ids; disposable artifacts torn down to zero.
- `market_fields.py` does not grow; the DRIFT-012 invariant (`used_fallback` untouched by
  enrichment faults) is pinned by an explicit test.
- Pacing values, note-attribution bounds, and any timeout are `tunable(..., why=...)` — no
  bare literals.
- Do not touch the sentiment (AlphaVantage) path, the Tiingo/Alpaca OHLCV paths, or the
  DRIFT-013 sector cache semantics.
- The Finnhub free tier is a shared budget: at most **two** full-universe live ingests (one
  paced, one unpaced) — do not iterate the live check to green by burning quota.

## Definition of done

1. A full-universe enrichment ingest against live Finnhub completes with zero whole-feed
   degraded notes, inside the fleet window, under the paced budget.
2. One ticker's failure costs exactly that ticker's enrichment: attributed note, majority
   kept, `used_fallback` untouched — proven live against the real rate limit.
3. The attribution is durable on the graph and legible to `/diagnose-feeds`, the dashboard
   vital, and the verdict warning.
4. DRIFT-021 reads CORRECTED with cited tests + live proof.
5. `make ci` green at 100 % (exit code captured); closeout + return notes filled.

## Closeout (coding agent fills; planning agent verifies before merge)

```text
CLOSEOUT — Sprint 128
Branch / merge commit:   sprint-128-feed-resilience / not merged by instruction
make ci:                 MAKE_CI_EXIT_CODE=0; 1590 passed, 5 skipped;
                          total coverage 100.00 %
Functionality check:     Code proof complete; live paced/unpaced full-universe Finnhub + Neon
                          proof blocked before ingest by DRIFT-023 and the read-only uv
                          Postgres probe returning DEP-POSTGRES-01 RED postgres:
                          reachable OperationalError. No full-universe Finnhub run started,
                          no disposable run id created, no graph nodes written, teardown sweep
                          count 0. Recorded in docs/laws/functionality-checks.md and
                          docs/reports/sprint-128-feed-resilience/code-and-live-preflight.md.
Version:                 0.71.00 → 0.71.01 (PATCH); uv.lock refreshed
DRIFT-021:               OPEN — S128 code proof complete on branch
                          sprint-128-feed-resilience (0.71.01); live correction blocked by
                          DRIFT-023 / Neon OperationalError. Paced/unpaced full-universe live
                          Finnhub + Neon proof still required before CORRECTED.
Drift rule:              main unmoved after git fetch; branch base and origin/main both da125fb;
                          no merge and no post-fetch re-gate required.
Deviations from spec:    Live LAW-02 functionality check and DRIFT-021 → CORRECTED update were
                          not completed because the sprint file's own DRIFT-023 precondition
                          still failed and Neon was unreachable. Everything code/test/doc-local
                          in Sprint 128 completed on branch.
```

## Return notes (coding agent appends at handback — mandatory)

Append below, at the very end of this file, everything the next session needs that the
closeout numbers don't carry: surprises found in the code, decisions taken in-flight and why,
drift observed elsewhere, follow-ups you would queue. A handback is not accepted while this
section is empty or the closeout placeholder is unfilled (LAW-02 + DL-48: the handback must
prove, not restate intent — and an incomplete handback is bounced, not repaired).

<!-- return notes go below this line -->

2026-07-16 handback:
- Implemented Sprint 128's code-side correction on `sprint-128-feed-resilience`: Finnhub HTTP calls now go through an injectable per-request minute budget (`PROVIDER_FINNHUB_REQUEST_BUDGET_PER_MINUTE`, default 55, `0` disables), with deterministic clock/sleep tests for under-budget bursts, the N+1 wait, and disabled pacing.
- Hardened all four Finnhub enrichment loops (fundamentals, news, sectors, earnings) so one ticker failure is attributed and skipped while the rest of the feed survives. The bounded note format is `<feed>_degraded:<count>:<first-N-tickers>:<error-class>`; the ticker cap is tunable via `PROVIDER_FINNHUB_DEGRADED_NOTE_TICKER_CAP`.
- Added the shared note parser in `contracts/feed_notes.py`; `ingest_chunked`, the dashboard degraded-feeds vital, and source-owned provider notes use it so both legacy bare notes and attributed notes count as degraded feeds. The DRIFT-012 invariant is pinned: enrichment faults do not set `used_fallback`.
- Kept `agents/provider/market_fields.py` as the boundary, not the growth point; it is 131 lines after the change, below the sprint cap of 151 and under the 200-line hard gate.
- Green evidence before handback: focused resilience/provider tests passed (`6 passed`), full `make ci` passed with `MAKE_CI_EXIT_CODE=0`, `1590 passed, 5 skipped`, total coverage `100.00 %`. The Makefile still reports the known ignored `pip-audit` diskcache advisory after the successful gate.
- Live proof was not run: DRIFT-023 still reads OPEN and the safe read-only Postgres preflight returned `DEP-POSTGRES-01 RED postgres: reachable OperationalError` with DSN suppressed. Because the sprint file says not to start the live check until DRIFT-023 is resolved, no paced/unpaced Finnhub full-universe run, MarketData durability query, or graph teardown sweep was attempted; created nodes/run ids/sweep count are all zero.
- Next session should first resolve or verify DRIFT-023, then run exactly the two permitted provider-stage live ingests under non-`sched-*` disposable run ids: paced first, unpaced second using the live Finnhub rate limit as injector, then query Neon for the attributed notes and tear down every named artifact before marking DRIFT-021 CORRECTED.
