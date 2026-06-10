# Sprint 10 — Audit-truth & rigor hardening (before execution)

**Status:** shipped (merged to `main` @ `3bd1c25`) · **Branch:** `sprint-10-hardening` · **Build phase:** P3 (foundation hardening) · **Effort: L**

## Goal

Harden the foundation **before `execution` lands**, because execution amplifies any audit or
validation ambiguity. This sprint closes the real findings from the Sprint 09 review: make the
durable graph record *why* orders were rejected (the PM's own mission), validate contract values
so a malformed caller can't inject negative money / impossible confidence, make the two
`GraphStore` backends behave identically and the graph deeply immutable, install the Neo4j
uniqueness constraints ADR-0001 assumes, and split the modules that are one edit away from the
200-line limit.

This is a cross-cutting hardening pass (contracts + kernel + a few agents). It is sectioned and
**priority-ordered**: land **A (must)** for sure; **B/C** are the rigor the next phase needs.

## Why / read first

- The findings come from the Sprint 09 coding-agent self-review (recorded in
  `docs/STATE.md`). The mission line that drives item A1 is in
  `agents/portfolio_manager/mission.md` ("record exactly why each was … rejected").
- Read first: `docs/sprints/README.md` (guardrails + gate); `docs/decisions/0001-neo4j-primary-store.md`
  (append-only, money as integer cents, **uniqueness constraints**); `kernel/graph.py`,
  `kernel/graph_support.py`, `kernel/graph_neo4j.py` (the items in B); `agents/portfolio_manager/`
  (store.py, domain/risk.py); the `contracts/` payload modules (A2).
- A real Neo4j is available for the live test: `.env` has `NEO4J_URI`/`NEO4J_USER`/
  `NEO4J_PASSWORD`/`NEO4J_TEST_URI` (Aura). The default gate must still pass **without** it
  (integration tests skip).

## Constraints (unchanged guardrails)

The one rule, < 200-line modules + headers, justified tunables, faults-not-silent, green
before handback. Boundary meta-test must stay green (adding a *new* owned graph label is fine;
it stays single-writer).

---

## A — Audit truth & safety (MUST land)

**A0 — Split the near-limit modules first (prerequisite).** These are one edit from the hard
block, and B adds code to them: `kernel/graph_neo4j.py` (198), `kernel/graph.py` (196),
`kernel/bus_celery.py` (189). Split each to comfortably < 200 (aim < 150): e.g. move
`InMemoryGraphStore` traversal helpers and/or the value types out of `graph.py`; move more Cypher
into `graph_cypher.py`; extract `CeleryBusSettings`/the dispatch task from `bus_celery.py`. Pure
refactor — behaviour and the public API via `kernel/__init__.py` unchanged.

**A1 — Persist PM rejection evidence in the graph.** `agents/portfolio_manager/store.py` records
only a `rejected_count` on `PMRun`. Make rejections durably queryable: add **`"Rejection"`** to
`owns_graph` in `contracts/portfolio_manager.py`, and in `store.py` write a `Rejection` node per
rejected ticker (`{ticker, reason}`) with an edge `Rejection -[:REJECTED_IN]-> PMRun` (and, where
the `Recommendation` node resolves, `Rejection -[:REJECTS]-> Recommendation`). A test asserts the
nodes + reasons exist after a run that rejects.

**A2 — Contract value validators.** Add Pydantic constraints + validators to the payloads so an
invalid caller is rejected at the boundary (not by luck downstream). At minimum:
- `contracts/common.py`: `Money.amount` `ge=0`; `Window` — a `model_validator(mode="after")`
  requiring `start <= end`.
- `contracts/provider.py`: `OHLCVBar` open/high/low/close `gt=0`, `volume` `ge=0`;
  `RegimeContext` `base_min_confidence` in `[0,1]`, `base_stop_loss_pct`/`base_take_profit_pct`
  `ge=0` (`le=1`), `base_max_holding_days` `ge=1`, `vix` `ge=0`.
- `contracts/scanner.py`: `Candidate.rank` `ge=1`; `FilterTrace` counts `ge=0`.
- `contracts/analyst.py`: `Recommendation.confidence` `ge=0,le=1`; `suggested_stop_pct`/
  `suggested_target_pct` `ge=0,le=1`.
- `contracts/portfolio_manager.py`: `OrderIntent.quantity` `ge=1`; `stop_pct`/`target_pct`
  `ge=0,le=1`.
Fix any fixtures that used out-of-range values. (Contracts keep their per-file ruff ignores.)

**A3 — Fix the stop/target truthiness bug.** `agents/portfolio_manager/domain/risk.py` (~line 124)
uses `item.suggested_stop_pct or default_stop_pct` — a deliberate `0.0` is silently replaced.
Use `… if … is not None else …` for both stop and target. (A2 already bounds the fields.)

---

## B — Graph backend rigor

**B1 — Deep-freeze graph props.** `kernel/graph_support.py` `_frozen_props` only wraps the
top-level mapping, so nested lists/dicts in a stored `Node.props` (e.g. provider tickers) stay
mutable. Make it **recursive**: dicts → `MappingProxyType`, lists/tuples → `tuple`, applied to
nested values. Returned nodes are then deeply immutable. Add a test mutating a nested value.

**B2 — Make the two backends agree on edge identity.** `kernel/graph.py` `InMemoryGraphStore.add_edge`
de-dupes by the **full `Edge`** (so same endpoints+type with different props creates a second
edge), while `Neo4jGraphStore.add_edge` uses `MERGE … ON CREATE SET` (idempotent on
**endpoints+type**, ignoring props on an existing edge). Make `InMemory` match Neo4j: an edge is
identified by `(parent.label, parent.key, child.label, child.key, edge_type)`; re-adding with
different props is **idempotent (no-op)** on both backends. Add a **parity test** running the same
add/read sequence against `InMemoryGraphStore` and the fake-driver `Neo4jGraphStore`, asserting
identical edge results.

**B3 — Install Neo4j uniqueness constraints.** ADR-0001 assumes one node per `(label, key)`, but
`Neo4jGraphStore` relies on `MERGE` alone — not concurrency-safe without a constraint. Have the
store **lazily ensure** `CREATE CONSTRAINT IF NOT EXISTS FOR (n:`<label>`) REQUIRE n.key IS UNIQUE`
once per label (cache the set; `_identifier`-quote the label). Test via the fake driver (the
`CREATE CONSTRAINT` is issued once per new label). Aura Free supports node uniqueness constraints,
so the live test (B-optional) can assert it against `NEO4J_TEST_URI`.

---

## C — Provider/analyst/scanner fixes (small)

- **C1 — Stooq missing-volume → clean skip.** `agents/provider/sources.py` `_has_ohlcv` (line 137)
  checks Date/Open/High/Low/Close but `_parse_stooq_rows` reads `Volume` (line 130) → a row with
  no volume crashes into a degraded incident. Add `"Volume"` to `_has_ohlcv` so the row is skipped
  cleanly. Test with a volume-less fixture row.
- **C2 — Analyst long-MA needs enough history.** `agents/analyst/domain/scoring.py` computes a
  "long MA" but only requires `min_history_bars` (= 2) while `long_ma_bars` (= 5); gate the long-MA
  signal on having ≥ `long_ma_bars` bars (else omit/neutralize it), so the signal matches its name.
- **C3 — Scanner tie-break.** `agents/scanner/domain/ranking.py` sorts the whole tuple
  `reverse=True`, so equal scores rank ticker **descending** (MSFT before AAPL). Sort numeric
  fields descending but ticker **ascending** (e.g. sort by ticker asc first, then by the numeric
  keys desc with a stable sort, or negate the numeric keys).

---

## Coverage policy

The floor is currently pinned at **100%** — a degenerate ceiling with no ratchet headroom, which
pushes new defensive/branch code toward `# pragma: no cover` overuse. For this sprint: keep
genuine coverage as high as the work allows, `# pragma: no cover` only for truly unreachable lines
(with a one-line reason). Then **re-tune the floor to the real measured value**; if holding exactly
100% would force pragma-overuse or test contortions, set the floor to the honest measured value
(**≥ 99.5**) with a one-line justification comment. Treat this as a deliberate de-pinning of a
ceiling, not a regression — the "never lower the floor" rule resumes from the new sustainable value.

## Steps

1. Branch `sprint-10-hardening` off `main`.
2. **A0** module splits (so later items don't blow 200). Run the gate green after the refactor.
3. **A1–A3**, then **B1–B3**, then **C1–C3**.
4. Re-tune the coverage floor per the policy above.
5. Run the gate; push; hand back. Do not merge to `main`.

## Acceptance criteria

- A `PMRun` that rejects produces queryable `Rejection` nodes with reasons (A1); boundary
  meta-test green with the new `Rejection` label.
- Invalid contract payloads (negative money, confidence > 1, `start > end`, quantity < 1) raise at
  construction; a test proves each (A2).
- The stop/target `0.0` case is preserved (A3).
- Graph props are deeply immutable (B1); `InMemory` and `Neo4j` edge behaviour matches under a
  parity test (B2); the Neo4j store ensures a per-label uniqueness constraint (B3).
- C1–C3 fixed with tests. All modules headered and **< 200 lines** (the previously-tight ones now
  have headroom).
- `import-linter` 4/4 KEPT; `make ci` green at/above the re-tuned floor; gate needs no external infra.

## Out of scope

`execution`/`monitor`/`reporter` and the paper broker (the *next* P3 sprints); the Celery
distributed-worker registry / non-eager round-trip (P4 orchestration); the MCP binding and RAG
vector (build-when-needed); forecaster. Flag anything you think is needed earlier.

## Handback report (paste into the PR / reply)

- Files changed and final line counts (confirm the split modules); the approach to rejection
  persistence (node label vs props) and to the Neo4j constraint lazy-ensure; the contract
  constraints added and any fixtures fixed.
- New coverage % and the floor you set (and the justification if you de-pinned 100%).
- Confirmation the backend-parity test passes; anything out of scope.

The planning agent will review, merge to `main`, and update `docs/STATE.md` +
`docs/build-plan.md`. After this, P3 resumes with `execution`.
