# Sprint 06 — Analyst agent (closes the P2 vertical slice)

**Status:** shipped (merged to `main` @ `d44f8f2`; **P2 exit met**) · **Branch:** `sprint-06-analyst-agent` · **Build phase:** P2 (first vertical slice — exit)

## Goal

Implement the **`analyst`** agent: turn a scanner `CandidateSet` into scored,
evidence-backed `Recommendation`s (or clear `Rejection`s), by requesting market data **and**
the regime from `provider` over the bus, gating confidence against the regime's
`base_min_confidence`, and writing `Recommendation -DERIVED_FROM-> Candidate` provenance.
This **closes the `provider → scanner → analyst` slice** and meets the **P2 exit criterion**:
*a request produces explained recommendations with full provenance, with no agent importing
another.* A full-slice integration test (all three agents on one bus) demonstrates it.

## Why (context)

- `analyst` is the last P2 agent and the first to depend on **two** agents
  (`depends_on=("scanner", "provider")`): it *consumes* the scanner's `CandidateSet` (the
  `analyze` request payload) and *calls* `provider` over the bus for the OHLCV and the regime.
- Producing `Recommendation` nodes linked back to `Candidate` nodes yields the
  `Recommendation → Candidate → ScanRun → MarketSnapshot` chain — the provenance the P2 exit
  asserts.
- Read first: `docs/sprints/README.md` (guardrails + gate); **`contracts/analyst.py`** (THE
  contract — `Recommendation`/`Rejection`/`RecommendationSet`, implement exactly) and the
  payloads it builds on — `contracts/scanner.py` (`CandidateSet`/`Candidate`),
  `contracts/provider.py` (`DataRequest`/`MarketData`, `RegimeRequest`/`RegimeContext`),
  `contracts/common.py` (`Action`, `Explanation`, `Provenance`); the **scanner** as the
  exact pattern to copy — `agents/scanner/agent.py` (the inter-agent bus call) and
  `agents/scanner/store.py` (cross-agent lineage via parsing `provenance.graph_node_id`);
  `kernel/agent.py`, `kernel/bus.py`, `kernel/envelope.py`, `kernel/graph.py`,
  `kernel/config.py`; `agents/analyst/mission.md`; ADR-0001.
- Porting source: v1 `src/trading_v2/` analyst — technical indicators + the composite/
  confidence scoring. Port the *logic* into <200-line modules; do not copy structure.

## Key design constraints (do not break)

- **Implement `contracts/analyst.py` exactly** — `analyze(CandidateSet) -> RecommendationSet`
  and `explain_recommendation(CandidateSet) -> Explanation`. Don't change the contract or the
  boundary map (meta-test stays green).
- **The one rule — twice.** `agents/analyst/` imports `kernel` + `contracts` only; it reaches
  `provider` **only** via `self.bus.request(...)` (two calls: `get_market_data` and
  `get_regime`). It must **never import `agents.scanner`, `agents.provider`, or
  `agents.portfolio_manager`** (the last is the explicit legacy leak this rebuild removes —
  see the contract `never`). `import-linter` enforces "agents may not import one another".
- **No external I/O.** All data comes from `provider`.
- **Confidence gating + explainable silence.** A candidate becomes a `Recommendation` only if
  its confidence clears the regime's `base_min_confidence`; otherwise it is a `Rejection`
  with a reason. `RecommendationSet.explanation` states why these (or why none today). Every
  recommendation carries a grounded `rationale` (`Explanation`).
- **Deterministic + faults.** Technical scoring and the confidence model are deterministic
  with **justified tunables** (no magic numbers, no LLM). Wrap the provider calls + scoring
  in `fault_boundary`; degraded/failed provider data yields an honest, explained empty/
  rejection result, never a crash.
- **Provenance lineage.** Write `AnalystRun` + `Recommendation` nodes, and the
  `Recommendation -DERIVED_FROM-> Candidate` edge. Reconstruct each `Candidate` node key from
  the incoming `CandidateSet.provenance.graph_node_id` (`"ScanRun:<scan_run_id>"`) +
  the candidate ticker → `f"{scan_run_id}:{ticker}"` → `get_node("Candidate", key)` →
  `add_edge`. Skip gracefully if not found. (Key-format coupling on the scanner's convention
  is a known, flagged limitation.)
- **Never** size positions, set quantities, approve/portfolio-reject/submit orders, or import
  PM sizing. The analyst only scores and recommends.
- **Small files, headers, < 200 lines**; secrets n/a.

## Deliverables

1. **`agents/analyst/agent.py`** — `AnalystAgent(AgentBase)` (inject `graph`, `settings`,
   `sink`). `analyze`: from the `CandidateSet`, request `get_market_data` (candidate tickers
   over a tunable window) **and** `get_regime` from provider over the bus → score each
   candidate → gate by `regime.base_min_confidence` into `Recommendation` or `Rejection` →
   write provenance → return `RecommendationSet`. `explain_recommendation`: return a grounded
   `Explanation`.

2. **`agents/analyst/settings.py`** — `AnalystSettings(AgentSettings)`, `env_prefix=
   "ANALYST_"`. Justified tunables: lookback window (days), technical-indicator params (e.g.
   moving-average windows), and the confidence-model weights/mapping. All via
   `kernel.tunable(why=..., bounds)`.

3. **`agents/analyst/domain/`** — deterministic logic:
   - `scoring.py`: technical indicators over the OHLCV → a `technical_score` and a
     `confidence` in [0,1]. (`sentiment_score`/`fundamental_score` stay `None` this slice.)
   - `recommend.py`: turn (candidate, scores, regime) into a `Recommendation` (action,
     confidence, `suggested_stop_pct`/`suggested_target_pct` from the regime's
     `base_stop_loss_pct`/`base_take_profit_pct`, rationale) or a `Rejection` when confidence
     is below `base_min_confidence`.

4. **`agents/analyst/store.py`** — `AnalystRun` + `Recommendation` nodes and the
   `Recommendation -DERIVED_FROM-> Candidate` edges (per the lineage rule above); return
   `Provenance`.

5. **`agents/analyst/__init__.py`** — export `AnalystAgent`. Update
   `agents/analyst/mission.md`: replace the stale **Postgres** ownership line with the graph
   model (ADR-0001).

6. **`agents/analyst/tests/`** — infra-free (`InProcessBus` + `InMemoryGraphStore`):
   - **Unit** (a real `ProviderAgent` on a `FakeDataSource` + the analyst; a `CandidateSet`
     fixture): `analyze` returns scored `Recommendation`s with `rationale` + `provenance`;
     a candidate below `base_min_confidence` becomes a `Rejection`; the run-level
     `explanation` is populated; a degraded/failed provider yields an honest explained result
     (no crash) and records a fault.
   - **Full-slice integration (the P2 exit):** wire **`provider` + `scanner` + `analyst`** on
     one bus; drive `run_scan` → feed the `CandidateSet` into `analyze`; assert a
     `RecommendationSet` and the **full provenance chain**
     `Recommendation -DERIVED_FROM-> Candidate -SURVIVED-> ScanRun -DERIVED_FROM->
     MarketSnapshot` (traverse with `ancestors`/`descendants`), with **no agent importing
     another** (the boundary meta-test + import-linter already guard this).
   - `explain_recommendation` returns a grounded `Explanation`.

7. **Coverage floor** — re-tune to the new measured value in `pyproject.toml`
   (`--cov-fail-under` + `[tool.coverage.report] fail_under`); never lower it.

## Steps

1. Branch `sprint-06-analyst-agent` off `main`.
2. `settings.py`; `domain/scoring.py` + `domain/recommend.py`.
3. `store.py` (provenance + candidate lineage); `agent.py` (the two handlers + the two
   provider bus calls); `__init__.py`; refresh `mission.md`.
4. Write `agents/analyst/tests/` (unit + the full-slice integration test).
5. Run the gate; re-tune the coverage floor. Push; hand back. Do not merge to `main`.

## Acceptance criteria

- Both capabilities answer over the bus; the analyst obtains data **only** via
  `self.bus.request` to provider; `import-linter` "agents may not import one another" KEPT;
  boundary meta-test green.
- Confidence gating works (below-floor candidates → `Rejection`); explainable silence holds
  (run-level `explanation` + per-`Rejection` reasons); degraded provider → honest result, no
  crash.
- The full-slice integration test passes, asserting the `Recommendation → Candidate →
  ScanRun → MarketSnapshot` provenance chain — the **P2 exit**.
- All modules headered, < 200 lines; tunables justified; no magic numbers.
- `make ci` green at/above the re-tuned floor; no external infra.

## Out of scope (do NOT build this sprint)

Sentiment + fundamental scoring (need provider news/fundamentals + a FinBERT-class scorer —
later, behind the established port); the forecaster's shadow ML; calibration; the
`portfolio_manager` (P3); `analysis_completed` as a real pub/sub message (no pub/sub until
P4 — record it in provenance for now); MCP (`mcp.py`); putting candidate graph-node ids into
the `CandidateSet` payload to remove the key-format coupling (a contract change — flag it).

## Handback report (paste into the PR / reply)

- Files added/changed and final line counts; the scoring/confidence model implemented; how
  the two provider calls + the candidate-lineage edge are done.
- New coverage % and the re-tuned floor; confirmation the **full-slice P2 integration test**
  passes with the provenance-chain assertion.
- Any design decision worth recording or anything that felt out of scope.

The planning agent will review, merge to `main`, **declare the P2 exit met**, and update
`docs/STATE.md` + `docs/build-plan.md`.
