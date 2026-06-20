# Project State

**Last updated:** 2026-06-20 19:26 AEST

**S72 shipped: ADR-0010 immediate close — `system_prompt` tunable on operator + forecaster.**
`system_prompt: str = tunable("")` added to `OperatorSettings` (champion slot for DSPy-compiled
interpret prompt; empty = dynamic `build_interpret_system()`, non-empty = DSPy-promoted static
override) and wired into `_interpret_command`. Pre-declared on `ForecasterSettings` (unused until
P13 LLM path ships). Both agent law PARAM sections updated. No version bump (no new capability).

**Now:** — (S72 complete). Next: S73 — P15 container-per-agent split or P12/P13 DSPy harness.

---

**S71 shipped: per-agent law backfill (remaining 7 of 11) — monitor/reporter/forecaster/
operator/supervisor/curator/researcher LOCKED v1.** Laws authored from first principles for all
7 remaining agents (18 sections each: IDN/IN/TRG/OUT/NEV/STA/IDM/ORD/FAIL/TYP/SEC/DEP/OBS/PERF/
CAP/PARAM + divergence register + changelog). Citation pass across 18 test files; 124 new green
clauses (MON 19/40, RPT 17/40, FORE 15/46, OPR 14/51, SUP 21/49, CUR 20/48, RES 18/44). 7
test-plan.md files created. All 7 laws.md LOCKED v1. No version bump (docs-only sprint).
**All 11 non-provider agents now have LOCKED v1 laws.**

**Now:** — (all agents locked; law cycle complete). Next: S72 — see `docs/sprints/INDEX.md`.

---

**S70 shipped: per-agent law backfill (4 of 11) — scanner/analyst/PM/execution LOCKED v1.**
Laws authored from first principles for 4 core trading-loop agents (18 sections each: IDN/IN/TRG/
OUT/NEV/STA/IDM/ORD/FAIL/TYP/SEC/DEP/OBS/PERF/CAP/PARAM + divergence register + changelog).
Citation pass across 12 test files; 95 new green clauses (SCAN 18/39, ANLZ 24/43, PM 23/43,
EXEC 30/49). `test_scanner_explain.py` split out to stay under 200-line hard block. All 4
laws.md LOCKED v1. **895 tests**, 100% coverage. No version bump (docs-only sprint).

**S69 shipped: provider law cycle — template locked (v0.10.0→0.11.0).** Two OPEN drifts
corrected: DRIFT-006 (benchmark promoted to first-class `DataRequest.benchmark_ticker` field +
`MarketData.benchmark`; `taint=False` so a degraded benchmark never sets `used_fallback` on
candidate quality; analyst uses `market.benchmark` directly); DRIFT-007 (`caller_authorized`
predicate + `allowed_callers` gate in all three buses — InProcess, Celery, Azure Service Bus;
`AgentBase.bind()` threads it; provider capability matrix now enforced for `get_market_data`
and `get_regime`). Law-ID citation pass across 7 provider test files; `test-plan.md` updated
to 23/43 clauses 🟩. `agents/provider/laws/laws.md` LOCKED v1; `docs/laws/_TEMPLATE.md` lock
comment added — safe to copy to the 11 remaining agents. **894 tests**, 100 % coverage.
**version 0.10.0→0.11.0** (feat/MINOR, HARD RULE).

**S68 shipped: analyst Alpha158 feature pillar (qlib Phase Q2).** `AlphaFeatureRow` dataclass
(22 fields: ROC/STD/MAX/MIN/IMAX/IMIN at 4 horizons) + `compute_alpha_features()` (returns None
< 62 bars) + `score_alpha158()` (cross-sectional z-score → logistic 0–100); `ScoreBreakdown`
gains `alpha158_score`; `_composite()` renormalised over present pillars; pillar off by default
(`alpha158_pillar_weight=0.00`); operator enables after 20-day IC validation; pyqlib-free (3.13
constraint). **890 tests**, 100 % coverage. **version 0.9.0→0.10.0** (feat/MINOR, HARD RULE).

**P14 complete — inter-agent comms re-architecture (S60–S67).** Replaced synchronous
RPC hand-offs with event-driven publish/subscribe + claim-check (ADR-0005). All 7 agents
migrated to dual-mode (RPC retained + pub/sub added via `bind()` override); kernel gains
`claim_check_write/read` primitive and `ReadyEvent`; dispatcher rewritten as a
trigger-emitter (publishes `run.trigger`, subscribes `report.snapshot.ready`, step
sequencing removed); `AzureServiceBusBus` + `AzureServiceBusSettings` shipped as optional
`azure` dep (in-process shim for RPC; Azure I/O path `# pragma: no cover`; parity test
skips without creds). `pm_run_id` threaded through execution→monitor→reporter props so
the PMRun node is found correctly by reporter. **863 tests**, 100 % coverage,
**version 0.8.0→0.9.0** (feat/MINOR, HARD RULE). `build-plan.md` P14 → **complete**.

**S59 shipped: forecaster LightGBM training pipeline + return IC scorecard (qlib Q1
follow-on).** `build_label_rows` + walk-forward `split_rows` + `train_and_save` offline
script; new `return_scorecard` capability (Pearson IC + hit_rate + directional quartile
breakdown vs injected forward returns); CONTRACT 0.3.0→0.4.0; **version 0.7.0→0.8.0**.
Not news-runway blocked — consumes `price_cache` OHLCV only.

**S58 shipped: forecaster LightGBM price/return shadow signal (qlib Phase Q1).** `ReturnModel`
Protocol + lazy `LightGBMReturnAdapter` + pure `_features.py` (5 price-derived features) +
provider OHLCV request → `ShadowPrediction` (shadow, never gates) + `Model` node;
`lightgbm`-direct (`pyqlib` is 3.13-incompatible — confirmed R001); CONTRACT 0.2.0→0.3.0;
**version 0.6.0→0.7.0**.

**S57 shipped: forecaster sentiment scorecard harness (P12).** New `sentiment_scorecard` capability on
the forecaster compares the three scorers (lexicon + provider `SentimentReading`, FinBERT
`ShadowPrediction`) vs injected forward returns: pure-Python Pearson + 2-regressor OLS
(`domain/statistics.py`), `comparison_metrics` (`domain/scorecard.py`) for pairwise correlations,
per-scorer IC, FinBERT-on-the-other-two regression + residual std + **incremental IC**; `comparison.py`
inner-joins readings by `{analyst_run}:{ticker}`; forward returns are injected (never a runtime
dependency). Advisory only (`promotion_eligible` always False). forecaster CONTRACT 0.1.0 -> 0.2.0
(reads only, owns_graph unchanged); `feat` -> project version 0.5.0 -> 0.6.0. **756 tests** (+17), floor
100.00. **P12 is code-complete** - remaining work is operational (live news runway), then run the
harness and decide promotion via P10.

**S56 shipped: analyst champion upgraded to the full Loughran-McDonald master dictionary (P12).** The
binding sentiment pillar (`sentiment_rules.py`) now loads the genuine LM master dictionary (Positive
354, Negative 2355; vendored under `agents/analyst/domain/data/`, counts match the published
dictionary) **unioned** with the prior curated headline terms - LM omits headline verbs (beat, surge,
plunge, rally, jump, tumble, profit, record, upgrade, rise, fell, drop), kept via the union; the two
sources are polarity-disjoint (asserted). `score_sentiment` interface + behaviour unchanged (the union
is additive for the fixtures, so no pinned score re-pinned). `feat` -> **project version 0.4.0 ->
0.5.0** (MINOR, HARD RULE); **739 tests** (+4), floor 100.00. **P12 remaining is now just the
scorecard harness** (data-runway-gated); the full-LM-dictionary champion upgrade is done.

**S55 shipped: reporter re-point to real $ PnL — P11 COMPLETE** (the reporter's trade-outcome metrics
now read the monitor's realized pnl_cents (S43) off each CloseDecision instead of S41's trigger-derived
%; collect_trade_outcomes(close_decisions) → dollar profit_factor + expectancy_cents +
closed_trades_with_pnl across all triggers incl. time (the % approx dropped time exits);
expectancy_pct → expectancy_cents rename, no contract change; the_implied_pnl_pct derivation +
position pairing removed. feat → **project version 0.3.0→0.4.0** (MINOR, HARD RULE); **735 tests**,
floor 100.00. **P11 (deterministic-logic depth) is complete** — analyst engine, PM gates, scanner
(beta+earnings), reporter metrics, monitor realized PnL all ported). **PR automation live:** Dependabot
non-major PRs auto-merge once CI passes (branch protection: quality/test/security; majors stay open).
**CodeQL restored:** codeql.yml re-added; CI security lane now includes conditional CodeQL steps gated
by jobs.security.env.GHAS_ENABLED (private repo still requires GHAS/code scanning enablement).

**S43 shipped: monitor realized PnL** (P11 — pure `realized_pnl_cents=(exit-entry)xqty` integer cents;
`CloseDecision.pnl_cents`; decision logic extracted to `decide.py`; **CONTRACT 0.1.0 to 0.2.0**;
version 0.2.0 to 0.3.0).

**S54 shipped: scanner earnings-window exclusion** (P11 — consumes S42's `MarketData.earnings`; drops
candidates with earnings within `earnings_exclusion_days` (5) of the scan as-of; additive + dormant;
the scanner earnings pair (S42->S54) complete; version 0.1.0 to 0.2.0).

**S42 shipped: provider earnings-calendar feed** (P11 — `DataSource.fetch_earnings` via Finnhub
`/calendar/earnings`, pure `_parse_next_earnings` -> earliest upcoming date, field-gated into
`MarketData.earnings`; CONTRACT 0.3.0 to **0.4.0**; the five optional field-gates extracted to
`market_fields.py` dropping provider `agent.py` 197->131L; additive + dormant).

**S41 shipped: reporter profit-factor + expectancy** (P11 — new `agents/reporter/domain/trade_outcomes.py`
pairs Position<->CloseDecision, derives `profit_factor`/`expectancy_pct`/`closed_trades_with_pnl` from
`stop_pct`/`target_pct` props; time exits excluded; merged into `RunSnapshot.portfolio_metrics` on both
the live and degraded paths; no contract change, no new dep). Follow-up unchanged: S43 monitor `pnl_cents`
-> reporter re-point to real $ PnL (memory `realized-pnl-sequencing`).

**S53 shipped: provider laws CAP + PARAM sections** (ADR-0007 backfill — runtime capability declaration

+ 20-entry parameter table for `agents/provider/laws/laws.md`; establishes pattern for all 11 remaining
agent backfills; ADR-0007 docs committed).

**ADR-0007 accepted: container-per-agent + master bootstrap** (one Docker image per agent → DockerHub →
Azure Container Apps; master agent is sole Key Vault accessor; agents start braindead, activate via
signed EHLO/ACTIVATE handshake; Neo4j is the operational registry; law files gain CAP + PARAM sections;
full risk assessment + mitigations in `docs/decisions/0007`; P14 milestone).
**Graph store: local Neo4j Enterprise Docker.** `infra/neo4j/local/docker-compose.yml`, db
`traiding-agents`, `bolt://localhost:7687`. **DEP-NEO4J 01/02/03 all GREEN** against local. Aura instance
`02812797` was empty at cutover → **deleted 2026-06-19**. Details: memory `neo4j-aura-to-local-migration`.

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* =
exists but inactive. *Shipped* = landed. Update at every transition.

---

## Now

**S71 — Per-agent law backfill cont. (remaining 7 agents).** S70 locked scanner/analyst/PM/
execution. S71 authors laws for monitor, reporter, forecaster, operator, supervisor, curator,
researcher — same 18-section depth, same cite→test→lock cycle.

Also pending (small, separate chore): add `system_prompt` as a `tunable` to
`agents/operator/settings.py` and pre-declare it on `agents/forecaster/settings.py`
(ADR-0010 immediate consequence; chore-branch off main).

## Next

+ **P12 — Sentiment: code-complete; awaiting live news-accrual runway.** All three scorers
  (lexicon S37/S56, provider S47/S48, FinBERT S49) + `sentiment_scorecard` harness (S57)
  shipped. Remaining is operational: accrue real headlines live (the S36 feed scored forward),
  then run `sentiment_scorecard` on `price_cache` forward returns and decide promotion via the
  P10 predictor-registry gate. Spec: ADR-0002.
+ **P13 — Cross-asset & macro signal graph** (later; sector contagion + signed tariff/sanction
  event propagation over Neo4j; contingent on P12 + news+returns data runway; ADR-0002).
+ Build-when-needed: RAG vector index (deferred; no sprint planned).

## Workflow

The planning agent writes sprint handovers and maintains documentation
and progress; a coding agent implements one active sprint at a time on its
own branch and hands back. See `docs/sprints/README.md`.

## Parked

+ (none)

## Shipped

+ **Sprint 70 — Per-agent law backfill (4 of 11)** (implemented directly — no coding agent
  this cycle). Laws authored from first principles for scanner (SCAN, 39 clauses), analyst
  (ANLZ, 43), portfolio_manager (PM, 43), execution (EXEC, 49). Citation pass across 12 test
  files; 95 green clauses (18+24+23+30). `test_scanner_explain.py` split to resolve 200-line
  hard block. All four `laws.md` files LOCKED v1. No code change; no version bump (docs-only).
  895 tests, 100% coverage.
+ **P14 complete — Inter-agent comms re-architecture (S60–S67)** (ADR-0005; implemented
  directly — no coding agent this cycle). `InProcessBus.publish/subscribe` + fan-out (S60);
  kernel `claim_check_write/read` + `ReadyEvent` (S61); provider (S62), scanner + analyst
  (S63), PM + execution (S64), monitor + reporter (S65) migrated to pub/sub dual-mode;
  dispatcher → trigger-emitter, step sequencing removed (S66); `AzureServiceBusBus` +
  `AzureServiceBusSettings` + `azure-servicebus>=7.12` optional dep (S67). `pm_run_id`
  threaded execution→monitor→reporter. 8 per-agent pubsub test files + `test_bus_azure` +
  `test_bus_pubsub` + `test_claim_check` + `test_steps`; dispatcher unit + daily-loop tests
  rewritten. `contracts/` `owns_graph` += `OrderIntentResult`, `ExecutionResultEvent`,
  `MonitorDecisionResult`, `ReportSnapshotResult`. `feat` → **version 0.8.0→0.9.0**
  (MINOR, HARD RULE). **863 tests**, floor 100.00. `build-plan.md` P14 → **complete**.
+ **Sprint 59 — Forecaster: LightGBM training pipeline + return IC scorecard** (qlib Q1
  follow-on; implemented directly). `build_label_rows` (1-day forward return, no look-ahead)
  + walk-forward `split_rows` + `train_and_save` offline script. New `return_scorecard`
  capability: Pearson IC + hit_rate + directional quartile breakdown vs injected forward
  returns. `promotion_eligible=False` throughout. CONTRACT 0.3.0→0.4.0; `feat` →
  **version 0.7.0→0.8.0** (MINOR, HARD RULE).
+ **Sprint 58 — Forecaster: LightGBM price/return shadow signal** (qlib Phase Q1;
  implemented directly). `ReturnModel` Protocol + lazy `LightGBMReturnAdapter` (pickled
  booster, `# pragma: no cover` on I/O); pure `_features.py` (return_1d/5d/10d, vol_5d,
  close_to_high); provider OHLCV request → `ShadowPrediction` (shadow=True, never gates)
  + `Model` node. `lightgbm`-direct — `pyqlib` 3.13-incompatible (R001). CONTRACT
  0.2.0→0.3.0; `feat` → **version 0.6.0→0.7.0** (MINOR, HARD RULE).
+ **Sprint 57 - Forecaster: sentiment scorecard harness** (P12; implemented directly - no coding agent
  this cycle). New `sentiment_scorecard` capability comparing the three champion-challenger scorers vs
  injected forward returns. Pure stats domain: `agents/forecaster/domain/statistics.py` (`pearson`
  with undefined->None on <2 points or a constant series; population `std`; `ols2` closed-form
  2-regressor OLS, None on <3 points or collinear regressors) and
  `agents/forecaster/domain/scorecard.py` (`Observation` + `comparison_metrics` -> `complete_cases`,
  pairwise `corr_*`, per-scorer `ic_*`, the OLS `finbert_alpha/beta_provider/beta_lexicon/residual_std`,
  and `incremental_ic_finbert` = the IC of FinBERT's residual after regressing out provider+lexicon;
  each metric **omitted when undefined**, so a present key is always meaningful).
  `agents/forecaster/comparison.py` reads SentimentReading (analyst) + ShadowPrediction (own) from the
  graph and **inner-joins** complete cases by `{analyst_run}:{ticker}`; forward returns are **injected**
  via the request (never a runtime dependency). The handler emits the existing `Scorecard` (free-form
  `metrics` dict -> no response change) with `promotion_eligible=False` - never gates; promotion stays
  the curator's P10 registry. New inbound `SentimentScorecardRequest`; **forecaster CONTRACT 0.1.0 ->
  0.2.0** (new capability; `owns_graph` unchanged - reads the analyst's label only, no single-writer
  change). `feat` -> **project version 0.5.0 -> 0.6.0**. 756 tests (was 739; +17 - statistics
  known-values + None edges, comparison_metrics branches, agent alignment/skip + never-promotes), floor
  100.00; every module < 200L.
+ **Sprint 56 - Analyst: full Loughran-McDonald master dictionary** (P12 champion deepened;
  implemented directly - no coding agent this cycle). The binding lexicon in
  `agents/analyst/domain/sentiment_rules.py` now loads the genuine LM master dictionary - **Positive
  354, Negative 2355** - vendored as `agents/analyst/domain/data/lm_positive.txt` and
  `lm_negative.txt` (lowercased, sorted, one word per line; counts match the published 2014 master
  dictionary exactly; provenance + citation in `data/README.md`) via a tiny `_load_lexicon` reader,
  **unioned** with the prior curated headline terms (renamed `_HEADLINE_POSITIVE` /
  `_HEADLINE_NEGATIVE`). LM was built for 10-K filings, so high-signal headline verbs (beat, surge,
  plunge, rally, jump, tumble, profit, record, upgrade, rise, fell, drop - 42 pos + 41 neg) are
  **absent** and are kept via the union; the two sources are **polarity-disjoint** (no curated word
  clashes with LM's opposite polarity - verified empirically and asserted by
  `test_positive_and_negative_lexicons_are_disjoint`), so the union needs no conflict resolution.
  `score_sentiment`'s interface and behaviour are unchanged - the union is purely additive for the
  existing fixtures (every prior "neutral" headline still has zero LM hits), so **no pinned score was
  re-pinned**. **No contract change** (analyst 0.1.0); the `.txt` assets are exempt from the
  size/header guards (Python-only) and well under the 500 KB added-file limit. `feat` -> **project
  version `0.4.0 -> 0.5.0`** (MINOR, HARD RULE). 739 tests (was 735; +4 - LM-only pos/neg scoring,
  dictionary-loaded sanity, disjointness invariant), floor 100.00; every module < 200L. **P12
  remaining: the scorecard harness only** (data-runway-gated).
+ **Sprint 55 — Reporter: re-point to real $ PnL** (**P11 COMPLETE**; implemented directly — no coding
  agent this cycle). `agents/reporter/domain/trade_outcomes.py` rewritten: `collect_trade_outcomes`
  now takes **only** `close_decisions` and reads the monitor's realized `pnl_cents` (S43) off each
  `CloseDecision` (pure `_pnl_cents` guards non-int/None), bucketing by **sign** into dollar-based
  `profit_factor` (gross wins ÷ gross losses), **`expectancy_cents`** (mean realized PnL), and
  `closed_trades_with_pnl` — across **all** triggers **including time exits**, which S41's
  trigger-derived `%` approximation had to drop. The `_implied_pnl_pct`/`_pct` derivation and the
  Position↔CloseDecision pairing are gone (PnL lives on the close node). `result.py` call sites
  updated (one arg). **`expectancy_pct → expectancy_cents`** rename (unit changed; `portfolio_metrics`
  is a free-form dict → **no contract change**). `test_trade_outcomes.py` rewritten (incl. a time-exit
  and a break-even case); the reporter-agent fixture seeds `pnl_cents`. `feat` → **project version
  `0.3.0 → 0.4.0`** (MINOR, HARD RULE). 735 tests, floor 100.00; every module < 200L. **Closes P11.**
+ **Sprint 43 — Monitor: realized PnL on close** (P11; implemented directly — no coding agent this
  cycle; the real realized-outcome substrate). New pure
  `realized_pnl_cents(exit_price_cents, entry_price_cents, quantity) = (exit − entry) × quantity` in
  `domain/exit_rules.py` (integer cents, gross, long-only, never raises). The per-position decision
  logic was extracted from `agent.py` into a new `agents/monitor/decide.py::evaluate_one` (evaluate →
  write check → compute PnL on a close → build the `CloseDecision`), dropping `agent.py` **198 →
  171L**. `CloseDecision` gains `pnl_cents: int | None = None` (contract field **and** graph node
  prop, persisted by `write_close_decision`); holds carry `None`. **Monitor CONTRACT `0.1.0 → 0.2.0`**
  (`owns_graph` unchanged → boundary meta-test green); no other agent changed; existing
  `(decision, trigger)` slice assertions stayed green (additive). The stop/target/time agent tests
  gained exact PnL assertions (−600 / +1100 / 0 on the 10000c-entry qty-1 fixture). `feat` → **project
  version `0.2.0 → 0.3.0`** (MINOR, HARD RULE). 738 tests (+5), floor 100.00; every module < 200L.
  **Next: reporter re-point** to read this `pnl_cents` for $-based metrics across all triggers.
+ **Sprint 54 — Scanner: earnings-window exclusion** (P11; implemented directly — no coding agent this
  cycle; consumes the S42 feed, completing the earnings two-sprint pair). The scanner requests the
  `"earnings_calendar"` field and **drops candidates whose next earnings date is within
  `earnings_exclusion_days` (5, tunable) of the scan as-of**, attributing `earnings_window` in the
  filter trace. New pure `_days_to_earnings(ticker, earnings, as_of) -> int | None` (`None` when
  unknown or already past); the gate runs **after** the beta cap in `apply_filters`; `_survivor`
  records a `days_to_earnings` metric + an `earnings_window` survived-filter **only when earnings data
  is present** — mirroring the beta cap so the gate is **additive + dormant** (no earnings data →
  nothing changes → every existing scanner + pipeline test stayed green untouched).
  `request_market_data` now requests `("ohlcv", "earnings_calendar")`; the agent computes the scan
  window once and threads `market.earnings` + `window.end` through. **No contract change** (Candidate
  already carries `metrics`); no boundary-map change; provider already serves the field (S42). `feat`
  → **project version `0.1.0 → 0.2.0`** (MINOR bump — the HARD RULE's first application). 733 tests
  (was 726; +7 — 6 filter-branch + 1 agent end-to-end), floor 100.00; every module < 200L (filters
  127, agent 170). The scanner deterministic port (beta S50 + earnings S54) is now complete.
+ **Sprint 42 — Provider: earnings-calendar feed** (P11; implemented directly — no coding agent this
  cycle; unblocks the scanner earnings-window exclusion). New
  `DataSource.fetch_earnings(tickers, window) -> dict[Ticker, date]` across the Protocol +
  `FakeDataSource` (fixture + `fail_earnings`); the **real** `FinnhubDataSource.fetch_earnings`
  (`/calendar/earnings`, `_download_earnings` `# pragma: no cover`, `earnings_lookahead_days` init
  param) via a pure `_parse_next_earnings(raw, on_or_after)` — earliest ISO date ≥ as-of, never raises
  — plus `_parse_iso_date`, both in `fundamentals_parse.py`; stubs on tiingo/stooq/fmp/av_sentiment +
  the orchestration double; composite delegates to Finnhub and threads
  `finnhub_earnings_lookahead_days` (tunable, 30). Agent field-gates `"earnings_calendar"` →
  `MarketData.earnings` with the same degrade-to-empty + `"earnings_degraded"` note + `used_fallback`
  semantics as news/sectors. **Refactor:** the five optional field-gates were extracted from
  `agent.py` into a new focused `market_fields.py` (`collect_optional_fields` + a PEP-695-generic
  `_fetch_optional`) — behaviour-preserving (existing field-gate tests untouched), dropping provider
  `agent.py` **197 → 131L**. CONTRACT `0.3.0 → 0.4.0`; `external_io` unchanged; boundary meta-test
  green; **no other agent changed** (every existing caller requests neither field → `earnings == {}`,
  no re-pin). 726 tests (was 714; +12), floor 100.00; every module < 200L. Next: the **scanner**
  earnings-window exclusion consumes `MarketData.earnings`.
+ **Sprint 41 — Reporter: profit-factor + expectancy** (P11; implemented directly — no coding agent
  this cycle). New pure `agents/reporter/domain/trade_outcomes.py` (70L): `collect_trade_outcomes`
  pairs each `Position` to its `CloseDecision` by `position_id`, buckets by trigger
  (`target` → win `+target_pct`, `stop` → loss `−stop_pct`), and returns `profit_factor`,
  `expectancy_pct`, `closed_trades_with_pnl`. **Time exits are excluded by design** (their implied PnL
  needs the `PositionCheck` exit price — out of scope; documented in the module header); the counter
  tells callers whether the metrics are meaningful. `profit_factor` and `expectancy_pct` use the
  `0.0` zero-denominator/empty sentinel (mirrors `approval_rate`); the function never raises. Wired
  into `result.py` — `build_snapshot` **and** `degraded_snapshot` both merge the three keys into
  `RunSnapshot.portfolio_metrics`, so callers never KeyError on either path. PnL is derived purely
  from `stop_pct`/`target_pct` props already on `Position` (written by the monitor) — **no new graph
  traversal, no new contract field** (reporter CONTRACT 0.1.0, `owns_graph` untouched), **no new
  dependency**. Shared `seed_full_graph` Position deliberately left without pct props → existing
  snapshot test unaffected (**no value re-pinned**). 714 tests (was 703; +11 — 9 unit + 2 snapshot
  integration), floor 100.00. Next: S43 monitor `pnl_cents` (now unblocked) → reporter re-point to
  real $ PnL across all triggers (memory `realized-pnl-sequencing`).
+ **Sprint 53 — Provider laws: CAP + PARAM sections** (ADR-0007 backfill; S53). Two new law
  sections added to `agents/provider/laws/laws.md`: `CAPABILITY DECLARATION (CAP)` — a JSON
  schema describing the provider's four runtime interface needs (messaging subscribe/publish, graph
  append-write, external HTTPS read, secrets) in interface-first terms; `PARAMETERS (PARAM)` — a
  full 20-entry table covering 16 tunable constants (regime defaults, validation thresholds, VIX
  levels, request limits, network timeouts) and 4 non-tunable base URLs. Laws.md bumped to v0.4.
  **Establishes the template for all 11 remaining agent law backfills** (required before P14 master
  sprint). No code change; no contract change; no test count change.

> **↓ Older shipped history archived.** The full sprint-by-sprint ledger for **Sprint 36 and
> earlier (down to P0)**, plus the **retired-components log**, lives in
> [STATE-01.md](STATE-01.md) — a continuation of this file. As this list grows, move older
> entries there; keep only the most recent ~8 sprints here.

---

## Pointers

+ Product intent: `docs/PRD.md`
+ Structure & rules: `docs/architecture.md`
+ Sequenced plan: `docs/build-plan.md`
+ Configuration governance: `docs/configuration.md`
+ Error handling: `docs/error-handling.md`
+ Observability & historical data: `docs/observability.md`
+ Hardening backlog (deferred security/quality, with unblock triggers): `docs/hardening-backlog.md`
+ Per-agent charters: `agents/<name>/mission.md`
+ Machine boundaries: `contracts/<name>.py`
