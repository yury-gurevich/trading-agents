# Project State — Archive (STATE-03)

**Continuation of [STATE.md](../STATE.md).** This file holds the etalon-era detail for **Sprints 77–96** —
the graph-pull data-path arc (DL-08, S77–S83), the substrate/pack extractions (S84–S85), and the P16
continuous-improvement build: the deliberation drift-firewall, the pipeline observatory, Layer-3
acceptance going 🟩 at S&P-100 then the full S&P-500, and the DL-31 deliberation understanding-gate +
challenger-veto (S96). Split out on 2026-07-02 when STATE.md was trimmed to a lean live dashboard. Earlier
history: **Sprints 37–76** → [STATE-02.md](STATE-02.md); **Sprint 36 → P0** + retired components →
[STATE-01.md](STATE-01.md). The live dashboard (current focus / Recent / Now / Next / Pointers) stays in
[STATE.md](../STATE.md).

> *Snapshot of STATE.md as of 2026-07-01 13:41 AEST, superseded by the live file. Any item in the "Next"
> section below that is still open now lives (compressed) in STATE.md — read STATE.md for current status.*

---

## Direction at the time — etalon-first (DL-19)

**DIRECTION PIVOTED (DL-19). The goal is now to perfect the trading-agents bundle so it becomes
*etalon v0.1* — the hand-crafted reference the platform will one day reproduce (`ops/agent-genesis.md`).
**🟩 LAYER-3 ACCEPTANCE GREEN at S&P-100 (0.35.02): the full pipeline runs end-to-end on real data
→ Aura, 5 positions opened, `ACCEPTANCE PASS` — the law ledger's definition of "the system works."
🟩 at the FULL S&P-500 (0.37.01, proven live 2026-06-26): after the [DRIFT-014](../laws/drift-register.md)
per-ticker-quality fix, a live S&P-500 → Aura acceptance run returned `ACCEPTANCE PASS` (provider excluded
the lone outlier `anomalous SMCI`, batch stayed `quality ok returned=502/503`, 2 positions opened, 9.4s
OHLCV-only). DRIFT-013 (silent caps) CORRECTED: the concentration caps fired live (INTC SKIP) off a warmed
sector cache.**

Governance scaffolding shipped this session (v0.24.00→0.35.02): ADR-0013 continuous-improvement
system + P16/CI-1..CI-6 specs; Experimentation, Housekeeping & Deliberation charters; `librarian` +
`tuner` subagents; the **deliberation drift-firewall arc** — an LLM defend/attack/judge harness, an
eval harness scoring debates against a manufactured answer key, a Class-1 case library + LLM-judge scorer,
and a **runnable model-swap gate** (0.29→0.32); the **DL-19 no-cages audit + discovery-surface register**;
a **pipeline observatory** (0.34.x) that prints each stage's outputs + floor/ceiling WARNs (DL-27);
the etalon. Pipeline: Alpaca primary OHLCV + chunked ingest. **The bundle now TRADES** — the validate-once
fix (0.28.01) yielded a clean 99/99 batch that opened 5 positions (2026-06-24), and the firewall's finding
is now **code**: PM-NEV-06 name-correlation cap (0.33.00) stops the correlated-semis basket. So it moves
from *trades cleanly* toward *trades wisely* (quant-methods Part 2/3). **DSPy's first job is now a working
model-drift firewall (DL-24): a model swap must clear `deliberation_gate.py` against a frozen golden — and
gpt-5.4 demonstrably trips it.** Meta-machinery (CI-1..CI-6, the generator) waits behind a perfect etalon
(etalon-first).**

---

## Recent sprints (S77–S96, most recent first)

- **Session 2026-06-27 — S96 Part B: veto transcript persistence + live `--veto` run (0.41.00→0.42.00).**
  *Proven results (`make ci` green, 100% coverage, 1156 tests):* the veto now **persists the full debate
  transcript** per order on the `DeliberationRun` (`debates` prop: per-ticker verdict + rationale + turns)
  — the auditable "why was this blocked", not just the verdict. `scripts/run_local.py --veto` runs the live
  challenger-veto (real model per `.env`) in the cascade and prints the persisted verdicts. So a real run
  writes a queryable `DeliberationRun` with the transcript to Neo4j/Aura.
- **Session 2026-06-27 — S96 Part B: runtime challenger-veto, mechanism (0.40.00→0.41.00).** *Proven
  results (`make ci` green, 100% coverage, 1156 tests):* DL-31 Part B — an **opt-in asymmetric
  challenger-veto** in the cascade. `orchestration/veto.py` debates each PM-approved order between PM and
  execution, records a `DeliberationRun` (per-order verdicts + the vetoed/subtracted set); the judge may
  only **subtract**, never originate/resize. Execution honours it (`_drop_vetoed`, EXEC-NEV-01 — executes
  the survivors, never decides). `cascade_once(deliberation_llm=...)` adds the stage **only when an LLM is
  injected**, so the deterministic cascade is unchanged; **fail-open** on LLM outage (an error upholds).
  **Proven live:** with gpt-5.5 the veto fired and execution submitted 0. **KEY FINDING:** with a thin
  proposition the LLM revised *everything* (blanket block) — so the veto stays **off by default** and is
  not yet safe for live capital; it needs (a) a **grounded** proposition (the order rationale + Part A's
  parameter answer key) and (b) verdict semantics (`revise` flag vs `reject` block). That grounding is the
  bridge back to Part A and the real remaining work.
- **Session 2026-06-27 — S96 Part A: deliberation understanding gate (0.39.00→0.40.00).** *Proven results
  (`make ci` green, 100% coverage, 1151 tests):* DL-31 Part A — make the expert-LLM deliberation **define
  each parameter then justify**, and **score the definitions** against ground truth.
  `kernel/deliberation.py` prompts now require define-then-justify; `kernel/deliberation_understanding.py`
  (`ParameterTruth`/`score_understanding`/`understanding_rate`/`misread_parameters`, substrate) grades a
  transcript; `orchestration/packs/trading_parameter_truths.py` is the answer key (from
  `llm-interpretation-deltas.md`); `scripts/deliberate.py --score` prints it. **Proven live:** gpt-5.5 gave
  a fluent UPHOLD on "Buy AMD" yet scored **0–33% understanding** — vague on `max_daily_move_sigma` (never
  "pooled cross-sectional") and `base_min_confidence` (never "regime-modulated"), the exact Class-1 deltas.
  *Confidence by measurement, not eloquence* — demonstrated. The live run also surfaced + fixed a scorer
  false-positive (a misread now requires the param be cited). **Part B (runtime challenger-veto) is the
  remaining half of S96.**
- **Session 2026-06-26 — forecaster activated (advisory shadow predictor, 0.38.00→0.39.00).** *Proven
  results (`make ci` green, 100% coverage, 1143 tests):* the forecaster was a *fully built* agent (FinBERT +
  LightGBM + scorecards) that **nothing ever called** — it `idle_loop()`d. Now activated as an
  **orchestrator-triggered cascade stage** (DL-30): after the analyst writes its `RecommendationSet`, a new
  `forecaster` stage calls it over a shared bus (`forecast` + `forecast_return`) per recommendation →
  `ShadowPrediction` per leg, `shadow=True`, linked under a `ForecasterRun` (`FORECAST_BY`, idempotent). It's
  a **side branch** — the integration tests prove it never touches the PM/execution path. Respects
  `FORE-TRG-01/02` (RPC-triggered, never self-triggers) and leaves the LOCKED analyst untouched.
  **Finding:** there is **no distributed RPC-serve transport** (only `idle_loop`/`work_loop`), so the
  forecaster is activated *in the in-process cascade*, not yet as a live container service — that gap is the
  real prerequisite for activating all 5 RPC control-plane agents (DL-30). *Deferred (noted): an observatory
  advisory `[forecaster]` line.*
- **Session 2026-06-26 — OHLCV-only fast mode shipped (0.37.01→0.38.00).** *Proven results (`make ci`
  green, 100% coverage, 1137 tests):* the live S&P-500 🟩 used a throwaway monkeypatch to request only the
  `ohlcv` field (9.4s vs ~33 min); that fast mode is now **first-class**. New `provider.ingest_ohlcv_only`
  setting (`PROVIDER_INGEST_OHLCV_ONLY`) + a `--ohlcv-only` flag on `run_local.py`; `_ingest_fields(settings)`
  narrows the request to `("ohlcv",)` (else `MARKET_FIELDS`), threaded through both single-shot and chunked
  ingest. `collect_optional_fields` already gates each enrichment pillar by `field in fields`, so OHLCV-only
  makes **zero** Finnhub calls. Proven: `test_ingest_ohlcv_only_skips_enrichment_keeps_bars` (bars delivered,
  sectors/fundamentals empty) + `_ingest_fields` unit. A supported fast S&P-500 acceptance is now a one-liner
  (`run_local.py --real --ohlcv-only --universe scripts/universe_sp500.txt`), not a scratchpad script.
- **Session 2026-06-25 (cont.) — DRIFT-014: per-ticker OHLCV quality (0.37.00→0.37.01).** *Proven results
  (on `sprint-drift014-per-ticker-quality`; `make ci` green, 100% coverage, 1134 tests):* the S&P-500
  acceptance `FAIL` (one >8σ name tainted all 503 → analyst scored 0) is **fixed in code**. `validate_bars`
  now attributes the pooled cross-sectional outlier to its **own ticker** and **excludes** it (new
  `DataQualityTrace.anomalous_tickers`), exactly like `stale_tickers` — a *partial* degradation, not a
  whole-batch fallback. `used_fallback` is set only by a genuine whole-batch failure (a tainting note, or
  `returned == 0`), so the analyst scores the clean survivors. The **pooled detector is unchanged** (still
  the data-integrity gate); only the *consequence* changed (DL-29). The exclusion is **observable**
  (DRIFT-013 lesson): the observatory prints `anomalous <tickers>` and the batch stays `quality ok`. Proven
  by `test_integrity_excludes_anomalous_ticker_keeps_clean_remainder` + the observatory
  `test_anomalous_ticker_is_excluded_and_shown_not_degraded`. **PROVEN LIVE (2026-06-26) — Layer-3 🟩 at the
  full S&P-500:** a live S&P-500 → Aura acceptance run returned `ACCEPTANCE PASS` (provider excluded the lone
  outlier `anomalous SMCI`, batch `quality ok returned=502/503`, scanner 503→5, **2 positions opened**). The
  run also validated an **OHLCV-only fast mode** (9.4s vs ~33 min — requesting only `ohlcv` skips the ~2000
  Finnhub enrichment calls); a CLI/env toggle for it is the small remaining follow-up.
- **Session 2026-06-25 (cont.) — DRIFT-013 corrected + S&P-500 scale (0.35.02→0.37.00).** *Proven results
  (merged to main, GitHub CI green every push):* (1) **DRIFT-013 visibility (0.36.00)** — the silent
  PM-cap bypass is now **loud**: a `sectors N/M classified (0 = caps INACTIVE)` observatory line + a
  `sector_coverage` **WARN** via a new **advisory severity** (`Check(severity="warn")` — surfaced,
  non-blocking). (2) **DRIFT-013 robustness (0.37.00)** — `agents/provider/sector_cache.resolve_sectors`
  treats a ticker's sector as **cached reference data** (`Sector` nodes, first-write-wins), filling the
  universe's gaps from the graph so the caps have data even when Finnhub rate-limits. **PROVEN LIVE:** a
  paced S&P-100 run cached **99/99** sectors in Aura; a later single-shot run (live sectors rate-limited)
  still showed `sectors 99/99 classified` and **PM-NEV-06 fired** — `INTC SKIP sector_name_count`. So the
  bundle now trades *wisely* (caps active on real correlated names), not just cleanly. (3) **S&P-500 scale**
  — committed `scripts/universe_sp500.txt` (503 authoritative names); the run pulled **503/503 OHLCV (the
  data layer scales)** but `ACCEPTANCE FAIL`: **[DRIFT-014](../laws/drift-register.md)** — the per-batch
  `daily_move_sigma_anomaly` taint is batch-level, so one >8σ name rejects every clean survivor. Recorded
  OPEN with the fix direction (per-ticker quality: exclude the anomalous bars, not the batch). Layer-3
  ledger: 🟩 at S&P-100, 🟨 at the literal S&P-500. *Next: DRIFT-014 per-ticker quality + an OHLCV-only
  fast mode (the single-shot run makes 503×4 enrichment calls acceptance doesn't need).*
- **Session 2026-06-25 (cont.) — 🟩 Layer-3 acceptance: "the system works" (0.34.01→0.35.02).** *Proven
  results (merged to main, GitHub CI green every push):* (1) **Acceptance gate (DL-28, 0.35.00)** —
  `observatory.accept` → PASS/FAIL over per-stage invariants **+ cross-stage conservation** (no agent
  fabricates/overruns its input); `scripts/accept.py` exits non-zero on FAIL; deterministic CI guard.
  (2) **Proven LIVE on a full S&P-100 → Aura run** — all 99 names × 41 real bars, provider→reporter, **5
  positions opened**, `OBSERVATORY OK` + `ACCEPTANCE PASS`. **The law ledger's Layer-3 row is now 🟩 — the
  definition of "the system works."** (3) Getting there fixed **three live-only bugs the 100%-coverage
  in-memory suite hid**: **DRIFT-011** (same-day re-ingest collided on Neo4j's immutable `snapshot` → key
  by run_id, 0.35.01) and **DRIFT-012** (optional-field over-taint + too-tight sigma blocked all trading on
  clean OHLCV → `_fetch_optional` never taints, sigma 4.0→8.0, 0.35.02). **Caveat (DRIFT-013, not
  blocking):** the 5 names are correlated and PM-NEV-06 silently bypassed (empty `sectors` from a Finnhub
  rate-limit) — trades cleanly, not yet wisely. **1128 tests, 100% coverage.** *Next: S&P-500 scale +
  DRIFT-013 (observatory should flag "caps inactive" / a sector-data fallback).*
- **Session 2026-06-25 (cont.) — Class-1 close-out + pipeline observatory (0.33.00→0.34.01).** *Proven
  results (merged to main, GitHub CI green every push):* (1) **Class-1 honesty verified.** The two
  remaining firewall "honesty" cases are *already correct + test-locked* (Alpha158 weight=0 is gated off
  in `analyze.py`; the forecaster's signals are `shadow=True` structural and unconsumable as a gate) —
  recorded as a case-status ledger in EXP-004. The firewall's catalogue of real gaps now collapses to one:
  `fixed-fraction-size` (vol-aware sizing, needs a vol field analyst→PM). (2) **Pipeline observatory (DL-27,
  0.34.00→0.34.01).** `orchestration/observatory.py` (substrate: Check/StageView/breaches/render) +
  `packs/trading_observatory.py` (pack: **full provider→reporter spine** extractors + floor/ceiling
  invariants) + `scripts/observatory.py`. Prints **each stage's output artifacts** (tickers, scores, recs,
  orders, fills, monitor checks, the report) with **floor/ceiling WARNs inline** — a degraded run reads
  top-to-bottom from `quality DEGRADED` to `WARN evaluated:0`. The firewall pattern (baseline +
  floor/ceiling) applied to the data pipeline. `run_local.py --observe` runs+monitors in one command
  (0.34.03). **VALIDATED LIVE against the free Aura (`c3ce91d0`) with real Tiingo data** (2026-06-25):
  a 3-ticker run pulled 41 bars/name, opened `AAPL qty=34 est=$293.32`, reported `OBSERVATORY OK`. **100%
  coverage; 1122 tests.** *Next (DL-27): a frozen golden run + diff; WARN→FAIL gate.* Also: DL-10 closed
  (S87 fix verified); worktree churn flushed. Usage: `docs/observability.md` §2a.
- **Session 2026-06-25 (cont.) — firewall hardened + first finding→code + DL-19 (0.31.00→0.33.00).**
  *Proven results (merged to main, GitHub CI green every push):* (1) **EXP-006 — N-run hardening
  (0.32.00).** `pass_fractions`/`robust_passing`/`check_robust` + `--runs N`. N=3 revealed
  `calendar-staleness` is *champion-flaky* (gpt-5.5 1/3) → EXP-005's single-run trip there was partly
  noise; the robust golden drops it, yet gpt-5.4 **still** regresses on the *stable* `name-correlation`
  (2/3→1/3). Found+fixed a 400-token truncation. (2) **PM-NEV-06 — name-correlation gate (0.33.00).** The
  first firewall finding translated to **code** (DL-25): a per-sector name-**count** cap (`SectorBook`,
  `max_names_per_sector`=3) — the penalty the dollar cap missed — + a new law clause + cited tests; moves
  the bundle toward *trades wisely*. (3) **DL-19 tackled (docs).** No-cages audit (**none found** — the
  constraint surface is healthy boundaries) + discovery-surface register (names each discoverer's space) +
  DL-26 (the cage test is role-relative). (4) **DL-10 closed.** Verified the S87 trading-session staleness
  fix and flipped its design-log status (was left OPEN). **1111 tests, 100% coverage.**
- **Session 2026-06-25 — drift firewall armed + operational (0.29.00→0.31.00).** *Proven results (merged
  to main, GitHub CI green every push):* (1) **EXP-004 — firewall armed (0.30.00).** `LLMJudgeScorer`
  (semantic "did it catch THIS flaw?") + `run_debates` (kernel-pure) + a 6-case **Class-1 library** (flaws
  only our implementation reveals, each citing its source). Live gpt-5.5: grounding Δ on Class-1 = **+50 pp
  (keyword) / +83 pp (judge)**; the judge is sharper (blind judge 0% vs keyword's false 33%). The grounding
  ROI EXP-003 couldn't show on textbook flaws is total on Class-1. (2) **EXP-005 — firewall operational
  (0.31.00).** `kernel/deliberation_gate.py` (`check_baseline`→`BaselineCheck`) + `scripts/deliberation_gate.py`
  (`--freeze`/`--check`, judge held fixed at champion) + a committed golden baseline. **Live A/B: gpt-5.4
  debater regressed `calendar-staleness` (4/6) vs the gpt-5.5 golden (5/6) — the firewall TRIPS on a real
  near-peer side-grade.** DL-24 is now a runnable command + DSPy's compile metric. **1102 tests, 100%
  coverage.** *Honest limit (EXP-005): single-run is noisy → N-run hardening next (folds into CI-4/S93).*
- **Session 2026-06-24/25 — deliberation eval harness + model-drift gate (0.28.01→0.29.00).** *Proven
  results (merged to main, GitHub CI green both pushes):* (1) **Eval harness** (0.29.00) —
  `kernel/deliberation_eval.py` (`EvalCase`/`EvalScore`/`score_debate`/`run_eval`/`pass_rate`, kernel-pure)
  scores a debate against a manufactured answer key *without* trade outcomes (DL-23 Path B); trading cases
  live caller-side (`scripts/deliberation_eval.py`, pack wall). **1093 tests, 100% coverage.** (2) **EXP-003**
  records the build + an honest finding: gpt-5.5 catches *textbook* flaws blind, so grounding's measurable
  ROI is **Class-1** (our-implementation facts), not Class-2 — known *before* investing in DSPy. (3) **DL-24
  - Deliberation charter v0.2:** DSPy's first job reframed as a **model-drift firewall**; `model` is now a
  **GATED** parameter (a downgrade/side-grade must pass the eval — no silent report drift). *Next experiment
  queued: Class-1 case library + a sharper (LLM-judge) scorer to arm the firewall.*
- **Session 2026-06-24 — pipeline + governance + housekeeping (0.24.00→0.27.00).** *Proven results
  (all merged to main, CI green):* (1) **Alpaca primary OHLCV** (0.26.00) — batch, no per-symbol
  throttle. (2) **Chunked ingest** (0.27.00) — paced sub-batches reassembled into one batch; **1080
  tests, 100% coverage**. (3) **ADR-0013** continuous-improvement system (all state on the graph) +
  **P16 / S90–S95** specs. (4) **Experimentation** & **Housekeeping** charters (`ops/departments/…`)
  - **`librarian`** & **`tuner`** subagents (`.claude/agents/…`) + the **etalon** (`ops/agent-genesis.md`).
  (5) **Housekeeping:** research docs → folder-per-topic; CodeQL → self-contained `codeql/` tool; root
  swept; **~1.3 GB reclaimed** (2.0 G→719 M); merged branches pruned both ends (local 89→4, remote 51→9). (6)
  **Dependabot** auto-merge fixed (Actions can't approve PRs) — all 6 PRs merged, image-build green.
  *Captured: DL-15…DL-20.* *Not done (verified failing): a real trade — DL-17 run 3 = INCONCLUSIVE.*
- **S85 — secret map out of the substrate (DL-12 leak #2; 0.23.01→0.23.02, PATCH).** `AGENT_SECRETS`
  deleted from `agents/master`; the `(kv_name, env_name)` table moved to
  `orchestration/packs/trading_secrets.json`, loaded via `MasterSettings.secret_map_path`
  (`load_secret_map`) and injected; `resolve_config(agent_type, store, secret_map)` takes the map as a
  param. The master substrate now names zero trading concepts. **1054 tests**, 100% coverage. On branch
  `sprint-85-platform-pack-secret-map`, green locally (not yet merged).
- **S84 — grant policy out of the substrate (DL-12 leak #1; 0.23.00→0.23.01, PATCH).** `DEFAULT_GRANTS`
  deleted; the 12-agent grant table moved to `orchestration/packs/trading_grants.json`, loaded via
  `MasterSettings.grant_policy_path` (`load_grant_policy`) and injected — read by path, never imported,
  so the `agents↛orchestration` boundary holds. Merged to main, GitHub CI green.
- **post-S83 (on the sprint-83 branch; 0.22.00→0.23.00) — batch-trace + live-Neo4j hardening.**
  `orchestration/batch_trace.py` + `scripts/trace_run.py` + `run_local.py --real/--trace` walk the
  provenance chain and print per-stage numbers (incl. the provider `quality` block and per-ticker analyst
  REJECT reasons). First **live Aura run** found + fixed **2 real Neo4j bugs the in-memory store hid**:
  nested-map node properties (JSON-encode at the store boundary, `kernel/graph_support.py`) and a
  list/tuple idempotency mismatch in `_append_props`. Backup/restore proven via a sentinel node. Captured
  DL-09 (filter training source), DL-10 (staleness gate counts calendar days but means trading sessions),
  DL-11 (Aura ops). Merged to main.
- **S83 — graph-pull orchestration trigger + e2e demonstrator (0.22.00).** Dispatcher writes one
  `RunRequest`; the provider is now graph-pull on it; every downstream agent wakes off its prerequisite
  gate. `orchestration/start.py` (`preflight` + `place_run_request`), `local_pipeline.cascade_once`,
  `scripts/run_local.py`, `test_graph_pull_e2e.py`. Closes DL-08's explicit-start gap.
- **S82 — execution+monitor+reporter graph-pull (0.21.00).** Final three agents move bus→graph data path;
  **closes DL-08 end-to-end** (provider→…→reporter all graph-pull).
- **S81 — analyst→PM graph-pull (0.20.00).** PM reads the `RecommendationSet` + market from the graph.
- **S80 — scanner→analyst graph-pull (0.19.00).** Provider persists full `RegimeContext`; scanner persists
  full `CandidateSet`; analyst reads all three from the graph. Scoring core extracted to
  `agents/analyst/run.py` shared by the bus + graph paths.
- **S79 — provider→scanner vertical slice + `work_loop` (0.18.00, DL-08b).** Provider persists the full
  `MarketData` payload; scanner reads market data from the graph (`agents/scanner/poll.py`), not bus RPC;
  reusable `kernel/work_loop.py`.
- **S78 — provider standalone graph-ingestor (0.17.00).** `kernel/graph_env.build_graph_from_env`;
  `agents/provider/ingest.py` (`universe_from_env`/`ingest_once`/`ingest_loop`); provider entrypoint
  replaces `idle_loop` with real ingest.
- **S77 — credential-naming reconciliation (0.16.1, PATCH).** `secret_map.py` emits
  `PROVIDER_TIINGO_API_KEY` (not bare); aligned the three entitled agents' env-var names; Neo4j integration
  test skips gracefully when Aura is smart-paused.

---

## Now (as of 2026-07-01)

**INTENT: perfect the trading-agents bundle until it is *etalon v0.1* (DL-19, `ops/agent-genesis.md`).**
On `main`, no active sprint branch. Success factors (the verifiable definition-of-done — each must be
*proven*, not asserted):

- **A real trade — ✅ DONE (proven 2026-06-24 21:09 AEST).** A clean 99-ticker batch
  (`quality ok returned=99/99`) flowed provider→scanner→analyst→PM→execution and **opened 5 positions**
  (C, QCOM, CSCO, AMD, INTC). Unblocked by the **validate-once fix** (0.28.01 — chunked ingest
  re-validates the reassembled batch once) + `sigma=8.0` + BK dropped + conservative pacing (chunk 10 /
  delay 70). *New finding:* the 5 names are 4 semis + 1 bank — **correlated concentration** the pipeline
  has no penalty for (the gap [quant-methods](../research/quant-methods/quant-methods.md) Part 2/3 flags;
  what a Deliberation Challenger would attack). **Closed in code + PROVEN LIVE:** PM-NEV-06 name-count cap
  (0.33.00, DL-25) fired on a real S&P-100 run off a warmed sector cache — `INTC SKIP sector_name_count`
  (DRIFT-013 corrected, 0.37.00). So: now *trades wisely*, not just cleanly.
- **Laws green.** Remaining gray law clauses → green with cited tests (ledger: provider 23/43, scanner
  18/39, PM 23/43, analyst 24/43, …).
- **No cages — ✅ DONE (2026-06-25).** All ~67 prohibitions audited (`docs/laws/cage-audit.md`); **none is
  a cage** — every NEVER is a role/safety boundary. Discovery surfaces named in
  `docs/laws/discovery-surfaces.md`; the cage test sharpened to role-relative (DL-26). Open follow-ups are
  *positive* (promote a per-charter Discovery-surface section; give re-composition a mechanism), not walls.
- **CI green throughout** (`make ci` + GitHub) at every step.

**Architecture (DL-08): graph-as-queue / pull model.** Provider writes all data to Neo4j; other agents
poll the graph for unprocessed work. Full detail in `docs/design-log.md`.

## Next (backlog as of 2026-07-01)

*The "finish the bundle" backlog — what perfection still needs:*

- **🚀 FLEET ACTIVATION ARC — S97–S103 (DL-35, direction pivoted 2026-07-01; planned, not started).**
  Close the distributed-platform gap in one consistent arc, in-process before distributed: **S97** kernel
  `serve_loop` primitive → **S98–S99** the 5 control-plane agents served in-process (retires every
  `idle_loop()`) → **S100** Azure Service Bus receiver + parity (etalon-first cut line) → **S101** permanent
  Neo4j → **S102** 13-container run-through + distributed `ACCEPTANCE PASS` → **S103** dispatcher cron.
  Reverses the DL-19 etalon-first pause **for the fleet workstream only** (the generator meta-work still
  waits). Handovers: `docs/sprints/sprint-97…103-*.md`.
- **S86 deploy wiring — ✅ DONE (verified in code 2026-07-01).** `infra/deploy-agents.ps1` L155 passes
  `MASTER_GRANT_POLICY_B64` + `MASTER_SECRET_MAP_B64` to the master container; `agents/master/entrypoint.py`
  `_resolve_pack` consumes them (b64 wins → image stays pack-agnostic). DL-34's "gap (1)" was stale.
- **Findings→code loop (DL-25)** — translate the remaining firewall Class-1 gaps into code: fixed-fraction
  sizing → vol-adjusted; Alpha158 weight=0 (wire it, or stop presenting it as "enabled"); LightGBM shadow
  labelling (so it can't read as confirmation). Each a small law + code unit, like PM-NEV-06.
- **DL-19 discovery surface → template** — promote a per-charter "Discovery surface" section into the
  LOCKED `_TEMPLATE.md` (a deliberate law cycle); the register (`docs/laws/discovery-surfaces.md`) is its
  substrate. Then give *re-composition* search a mechanism (gated on CI-6).
- **DL-09 filter training source** — per-ticker verdict + bypass + dual labels → curator dataset.
- **Permanent graph store** — self-host Neo4j on a small Azure VM for the fleet to run durably (Enterprise
  if the dev licence lands, else Community).
- **Fleet run-through on real store** — full `provider→reporter` cascade against the permanent store.
- **Dispatcher cron** — schedule the daily `RunRequest` so the fleet runs hands-off.
- **Distributed RPC-serve transport (DL-30) — now scoped as S97–S100** in the Fleet Activation arc above.
  DL-30's finding stands (no `serve_loop`/bus-consume primitive — only `idle_loop` + `work_loop`); S97
  builds the primitive, S98–S99 serve all 5 control-plane agents in-process, S100 adds the Service Bus
  receiver. The forecaster stays RPC-triggered (`FORE-TRG-02`), never graph-pull.
- **Observatory `[forecaster]` advisory line** (DL-30 deferred) — show the shadow-prediction count per run,
  advisory/never-FAIL, without entangling the trade-spine conservation view.
- **P12 scorecard-run + challenger promotion** (DEFERRED, not abandoned — P12 is otherwise SHIPPED:
  champion binding, challengers advisory, forecaster live; DL-32). Needs a live **news-accrual runway**
  not being accrued under the etalon-first pivot. P13 (cross-asset/macro graph) is downstream of this.
- **`contracts/` substrate/pack split** — the remaining ADR-0012 mix; deferred until a 2nd pack.
- **DEFERRED behind a perfect etalon (etalon-first, DL-19):** CI-1..CI-6 (ADR-0013 machinery, S90–S95)
  · the bundle **generator** · the **Research & Solution-Design** bundle (DL-20). Do not start these
  until the bundle is demonstrably perfect — a copier of an imperfect reference only reproduces gaps.

## Workflow

Each sprint/chore on its own branch (`sprint-NN-<slug>`); merge to `main` is the deploy trigger. This
cycle the operator implements sprints end-to-end (code+tests+CI+commit). See `docs/sprints/README.md`.

## Parked

- **Branch cleanup (2026-06-26): the 3 stale sprint branches are resolved.** Verified every feature was
  already byte-identical in `main` (S56 LM dictionary, S57 forecaster scorecard, S69 deps bump); the only
  branch-unique content was superseded local-observability infra (Prometheus/Grafana/neo4j-compose). Archived
  each tip as `archive/sprint-56|57|69-*` (recoverable via `git checkout archive/...`) and deleted the
  branches. ~48 other merged local branches remain as harmless leftovers (their work is all in `main`) — a
  one-shot `git branch -d` sweep whenever desired.
