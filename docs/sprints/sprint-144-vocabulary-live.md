<!-- Agent: planning | Role: sprint handover -->
# Sprint 144 — Vocabulary guard: deployable, and provably complete

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-144-vocabulary-live`
**Status:** SHIPPED 0.80.00 — merged `d215a76`, `make ci` 1851 passed / 100.00 %, all four remote
gates green before merge, functionality check PROVEN on the live Neon store. **Fleet enablement
still open** — one dated action after tonight's ADR-0015 §3 proof (see Closeout).
**Effort:** M
**Decisions:** [DL-68](../design-log.md) · completes [S143](sprint-143-graph-vocabulary.md) ·
pattern from [DL-65](../design-log.md) · delivery precedent S86 / [DL-12](../design-log.md)

---

## Why this sprint

S143 shipped the vocabulary guard and closed with an honest admission: `GRAPH_VOCABULARY_PATH`
is unset everywhere, so **the guard guards nothing**. That is the sixth instance of the DL-65
pattern in a week — *a guard can be present, documented, and still not guard* — and this one was
self-inflicted by construction.

Turning it on turned out to be two defects deep.

### Defect 1 — the guard is not deployable at all

`GRAPH_VOCABULARY_PATH` names a file. **No agent image contains one.** Every agent Dockerfile
copies exactly `kernel/`, `contracts/`, and its own `agents/<name>/`:

```dockerfile
COPY kernel/ kernel/
COPY contracts/ contracts/
COPY agents/scanner/ agents/scanner/
```

`orchestration/packs/` is in none of the 13 images. Setting the variable to the pack path would
not enable the guard — it would raise `FileNotFoundError` inside `build_graph_from_env` and take
the agent down at boot. The path-only interface made the feature undeployable on the day it
shipped, and nothing failed, because nothing set it.

The repo already solved this exact problem once. Master receives its trading pack as **base64 env
content**, with a path as the local-dev fallback (S86 / DL-12):

```powershell
$secretB64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $packs "trading_secrets.json")))
"MASTER_GRANT_POLICY_B64=$grantB64", "MASTER_SECRET_MAP_B64=$secretB64"
```

S143 invented a new, weaker delivery mechanism instead of following it.

### Defect 2 — the vocabulary cannot cover code that has not run yet

The pack was derived from the **live graph** (36 labels, 25 edge types, 31 observed triples) plus
code literals and the law files. Observed edges only. So any write path that has never executed in
production is, by construction, missing from `edge_signatures`.

That is not theoretical. ADR-0015 §3 broker-native stops merged Friday and **has never placed a
stop** — nine positions currently hold none. Its two write edges are undeclared:

```text
('Fill',     'STOPS_WITH',   'BrokerStopOrder')  -> declared: False
('Position', 'PROTECTED_BY', 'BrokerStopOrder')  -> declared: False
```

Both *labels* and both *edge types* are declared; only the signatures are missing, which is
precisely what `check_edge` rejects last. **Enabling the guard before this sprint would have
thrown `VocabularyError` at the moment execution placed the first real stop tonight** — destroying
the ADR-0015 §3 functionality check that has been pending since Friday, in the name of a guard
that was supposed to prevent damage.

A vocabulary derived from history is a trailing indicator. It needs a mechanical check that it is
a **superset of what the code can write**, or every future sprint re-arms this trap.

---

## What ships (spec)

1. **`GRAPH_VOCABULARY_B64`** — base64 pack content, resolved *before* `GRAPH_VOCABULARY_PATH`,
   which stays as the local-dev fallback. Same shape as master's `_resolve_pack` (S86 / DL-12), so
   agent images stay pack-agnostic and the guard becomes deployable without touching 13 Dockerfiles.
2. **The two missing stop signatures** added to `orchestration/packs/trading_graph_vocabulary.json`.
3. **A static completeness check** — every node label and edge type reachable as a literal or
   module constant in shipped (non-test) code must be declared. This is the durable fix for
   defect 2: it fails in `make ci` when a sprint adds a label the pack does not know, instead of
   at 22:30 UTC in production.
4. **Broker-stop coverage in the e2e conformance test** — `cascade_once` does not touch the stop
   path, which is exactly why the gap survived S143's "6/6 passing" e2e run.
5. **`infra/deploy-agents.ps1` injects the vocabulary** for every agent, so a full re-provision
   carries it the way it already carries grants and the secret map.

**Explicit non-goals:** no reasoner (R007 stands), no ownership enforcement yet (`owners: {}`
until the 8 `labels_owned` declarations are reconciled — that is the next sprint), no Dockerfile
changes, no change to ADR-0014.

---

## Enablement sequencing — deliberate, and dated

The guard is **not** switched on in the same change that makes it switchable. Tonight's 22:30 UTC
run is the first session-day run since the broker-stops deploy and the pending ADR-0015 §3 proof;
nine positions hold no protective stop. Introducing a new fail-closed write path into that run
trades a large, immediate, capital-protection proof for a small, deferrable one.

**Fixes before features: the stop proof outranks the guard.** Enablement is therefore one dated
action after tonight's run, recorded in the Closeout below. This sprint is **not closed** until
that action is taken and proven — "shipped but unset" is the exact failure S143 logged, and
repeating it deliberately would be worse than the original.

---

## Closeout — evidence

**Files changed:** `kernel/graph_env.py` (`GRAPH_VOCABULARY_B64`, resolved before the path),
`scripts/vocabulary_coverage.py` (new), `scripts/vocabulary_signatures.py` (new),
`orchestration/packs/trading_graph_vocabulary.json` (34 → 37 signatures),
`infra/deploy-agents.ps1` (`Get-VocabularyEnv`, injected for master, all 13 agents, dispatcher),
`scripts/gate_selftest_cases.py` (+`graph-vocabulary-injected-at-deploy`),
`tests/test_graph_vocabulary_completeness.py` (new), `tests/test_graph_vocabulary_env.py` (new,
split out to stay under the 200-line block), `orchestration/tests/test_graph_vocabulary_e2e.py`
(broker-stop path), `agents/execution/tests/broker_stop_helpers.py` (`position` widened to
`GraphStore`).

**Proven (LAW-02):**

- ✅ `make ci` — **1851 passed / 6 skipped / 100.00 % coverage**, pip-audit clean, detect-secrets
  clean. Gate self-test **14/14**.
- ✅ Remote gates green **before** merge, on `9878d02`: `quality` ✅ `test` ✅ `security` ✅ `gate` ✅.
  Merged `d215a76`.
- ✅ The completeness checks are **verified able to fail**: the planted-package tests assert the
  scan reports `PlantedRun` / `PlantedItem` / `PLANTED_EDGE` and the triple
  `PlantedItem -PLANTED_EDGE-> PlantedRun` as undeclared. A check never observed failing is
  indistinguishable from one examining nothing (DL-52, DL-65).
- ✅ The static pass recovers `Fill -STOPS_WITH-> BrokerStopOrder` — **the defect that would have
  broken tonight is inside the check's reach**, not merely fixed by hand this once.
- ✅ The e2e conformance test runs `place_stop` under a `GuardedGraphStore` and both stop edges pass.
- ✅ **Functionality check PROVEN** (2026-07-27 19:28 AEST) — against the live Neon spine, base64
  only, no file on disk:

  ```text
  1. store type            : GuardedGraphStore
  2. wrapped store         : PostgresGraphStore      <- the real spine, not in-memory (S98 lesson)
  3. rejected typo'd label : VocabularyError: undeclared node label 'Postion'
  4. rows for 'Postion'    : 0 (must be 0)
  5. accepts Fill -STOPS_WITH-> BrokerStopOrder
  5. accepts Position -PROTECTED_BY-> BrokerStopOrder
  6. live BrokerStopOrder  : 0
     live Position nodes   : 21
  ```

  No artifacts created — the only write attempted was one that had to be refused, so there was
  nothing to tear down.

**Not done, deliberately — this sprint stays OPEN until it is:**

- ⬜ **Fleet enablement.** The running fleet is `:s143` (0.78.00) and does not contain the code that
  reads `GRAPH_VOCABULARY_B64`, so enabling requires a build + retag at 0.80.00. That was **not**
  done before tonight's 22:30 UTC run: it is the first session-day run since the broker-stops
  deploy, `BrokerStopOrder` is still **0** with **21 Position nodes** in the book, and a new
  fail-closed write path does not belong in that run. Fixes before features — the stop proof
  outranks the guard.
- ⬜ **Ownership (`owners: {}`).** Unchanged from S143; reconciling the 8 `labels_owned` declarations
  is the next sprint.

**The dated action.** After tonight's run has been checked for a real `BrokerStopOrder`: build
images at the next `:sNNN` tag from `main`, retag the 13 apps + dispatcher, confirm 14/14 on tag,
and verify `GRAPH_VOCABULARY_B64` is present on an agent's env. Then this sprint closes — and not
before. "Shipped but unset" is exactly what S143 recorded; repeating it knowingly would be worse
than the original.
