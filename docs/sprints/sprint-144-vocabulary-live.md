<!-- Agent: planning | Role: sprint handover -->
# Sprint 144 — Vocabulary guard: deployable, and provably complete

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-144-vocabulary-live`
**Status:** SPEC
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

_To be filled on completion. Success factors (LAW-02):_

- [ ] `make ci` green — all 9 steps, 100 % coverage floor held.
- [ ] Both remote gates (`quality` / `test` / `security` / `gate`) green on the pushed branch
      **before** merge.
- [ ] The static completeness check **verified failing** on a deliberately undeclared label
      (a check that cannot fail is not a check — DL-65).
- [ ] The e2e conformance test exercises the broker-stop path and passes against the pack.
- [ ] Functionality check: an agent runs with `GRAPH_VOCABULARY_B64` set, writes to the real
      graph, and the write is guarded — recorded in `docs/laws/functionality-checks.md`.
- [ ] Fleet enabled after tonight's ADR-0015 §3 proof; tag and verification output recorded here.
