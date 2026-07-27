<!-- Agent: planning | Role: sprint handover -->
# Sprint 143 — Graph vocabulary: constraints wired, inference refused

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-143-graph-vocabulary`
**Status:** SHIPPED 0.79.00 — merged `798bfd4`, `make ci` 1841 passed / 100.00 %, both remote gates
green. **Not deployed** — no fleet behaviour change (see Closeout).
**Effort:** M
**Decisions:** [DL-66](../design-log.md) · implements the constraint half of
[R007](../research/ontology-guardrails/) · pattern from [DL-65](../design-log.md)

---

## Why this sprint

R007 evaluated Frank Coyle's *"Why Agentic Systems Need Ontologies"* against this platform and
split the idea in two. **"OWL constrains" is worth having; "RDFS infers" is refused permanently** —
a reasoner asserts facts nobody observed, and this graph is an append-only *evidence* store
governed by LAW-02. Every expensive bug of July 2026 was an unasserted fact treated as fact: a
`CloseDecision` read as evidence of closure (DL-60, four stranded positions), `pnl_cents` computed
at decision time (0.74.03). Inference would industrialise that failure mode.

The constraint half had a concrete, already-authored hook. **`labels_owned` / `labels_read` are
declared in eight agents' law files and read by zero lines of Python** — an ownership ontology
written down and never wired. That is the fourth instance in a single day of the DL-65 pattern:
*a guard can be present, documented, and still not guard.*

Underneath it, a plainer defect: labels and edge types are bare string literals at ~384 call
sites. Nothing closes the vocabulary, so a typo does not fail — `list_nodes("Postion")` returns an
empty tuple forever, the same silent-empty shape as the P6 `list_nodes` gap.

---

## What shipped (spec)

1. **`kernel/graph_vocabulary.py`** — a `Vocabulary` value object over a closed set of labels, edge
   types, and `(parent, edge, child)` signatures, plus `check_node` / `check_edge`. Raises
   `VocabularyError`. **Deliberately domain-free (ADR-0012): it never names a trading concept.**
2. **`kernel/graph_guarded.py`** — `GuardedGraphStore` wraps any `GraphStore` and validates
   `merge_node` / `add_edge` **before delegating**. Reads pass straight through. It only ever says
   no: it never adds a node, an edge, or a derived fact.
3. **`orchestration/packs/trading_graph_vocabulary.json`** — the vocabulary as *pack data*, derived
   from evidence rather than hand-written: the live Neon graph (36 labels, 25 edge types, 31
   observed triples) ∪ code literals and constants ∪ the law files' `labels_owned` / `labels_read`.
   Result: **71 labels, 42 edge types, 34 signatures.**
4. **One composition root** — `build_graph_from_env` wraps whichever store it built when
   `GRAPH_VOCABULARY_PATH` is set. Unset ⇒ unguarded, so no caller changes behaviour by default.
5. **Ownership built but not enabled** — `check_node(writer=)` is implemented and tested; the pack
   ships `owners: {}`. See Closeout for why, and what closes it.

**Explicit non-goals:** no reasoner, no RDF/OWL library, no triple store, no change to ADR-0014.

---

## Closeout — evidence

- **Files changed:** `kernel/graph_vocabulary.py` (new), `kernel/graph_guarded.py` (new),
  `kernel/graph_env.py` (guard wiring + `GRAPH_VOCABULARY_PATH`),
  `orchestration/packs/trading_graph_vocabulary.json` (new),
  `tests/test_graph_vocabulary.py` (new), `orchestration/tests/test_graph_vocabulary_e2e.py` (new),
  `docs/research/ontology-guardrails/ontology-guardrails.md` (§0 plain-language section),
  `docs/design-log.md` (DL-66), `pyproject.toml`.
- **`make ci`:** **1841 passed / 6 skipped / 100.00 % coverage**, all 9 steps, exit 0. Both remote
  gates green on the merged SHA `798bfd4` — verified by `headSha`, not by glancing at the run list.
- **The guard found a real gap on first contact.** Running the actual cascade under it raised
  `VocabularyError: edge 'FORECAST_BY' is not declared to run AnalystRun -> ForecasterRun`.
  `ForecasterRun` is **not among the 36 labels in the live graph** — the forecaster path exists and
  has never written to production. **A vocabulary built from live observation alone would have
  looked complete and been wrong.** Closed by recording what the cascade actually writes and
  merging it in (31 → 34 signatures).
- **One proof attempt is recorded as worthless, because it was.** Setting `GRAPH_VOCABULARY_PATH`
  and re-running the existing e2e tests passed 6/6 — but those tests construct
  `InMemoryGraphStore()` **directly**, bypassing `build_graph_from_env`, so the guard never
  engaged. A green result proving nothing is the DL-65 pattern one layer up, and it was caught only
  by asking *did the thing I just enabled actually run?*
- **The gate is proven able to fail.** `test_the_guard_can_actually_reject_a_write` drops
  `RunRequest` from the declaration and asserts the cascade raises. Same principle as
  `pip-audit-cve` in `gate_selftest_cases.py`: a gate that cannot be shown to fail is not a gate.
  The positive tests are the weak ones here; this is the load-bearing one.
- **Ownership deliberately left off — named, not dormant.** The eight law declarations are not
  accurate enough to enforce: `reporter` lists a **read**-set of 13 labels it mostly does not
  write, and `supervisor` declares the literal string `"all"`. Turning ownership on today would
  break agents on bad data. **Next step:** run each agent under a recording store to measure what
  it actually writes, reconcile the eight declarations against that, then set `owners`. That is the
  remaining half of R007's item 1.
- **Deploy: none, deliberately.** `GRAPH_VOCABULARY_PATH` is unset everywhere, so the deployed
  fleet is byte-identically unaffected and no retag is warranted. The fleet stays on `:s143`
  (0.78.00, `818e7a9`). **Functionality check therefore N/A** — there is no live behaviour to
  prove. It becomes due the moment the env var is set on a real agent, and that is a separate,
  deliberate act.
