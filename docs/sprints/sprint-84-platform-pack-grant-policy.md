# Sprint 84 — Platform/pack separation: relocate the grant policy out of the substrate

**Phase:** P15 (multi-agent container split) → ADR-0012 platform/pack wall
**Branch:** `sprint-84-platform-pack-grant-policy`
**Status:** in progress

---

## Goal

Close the first named platform/pack leak (DL-12). The **master is substrate** — fleet bootstrap
mechanism — yet `agents/master/grants.py::DEFAULT_GRANTS` hardcodes all 12 **trading** agent types
and their domain capabilities (`broker`, `data_feeds`, `ohlcv`, …) inside the substrate. S83 (step 1)
made the policy *injectable* (`MasterAgent(grant_policy=…)`); this sprint **removes the trading data
from the substrate** so the master knows no agent types until a pack supplies them.

---

## The constraint that shapes the design

The master's container bootstrap, `agents/master/entrypoint.py`, lives in the **agents** layer and
**cannot import** `orchestration/packs/` (import-linter: `agents ↛ orchestration`). So the trading
policy must reach the master as **data, not a Python import** — which also matches the LOCKED
container-per-agent model ("agents start braindead, configured by data").

```text
orchestration/packs/trading_grants.json   ← pack data (the 12-agent grant table)
        │  path, not import
        ▼
MasterSettings.grant_policy_path  →  load_grant_policy(path)  →  MasterAgent(grant_policy=…)
        │
substrate default when no path:  EMPTY policy  (master alone knows no agent types)
```

A file **read by path** crosses no import boundary; the substrate gains a generic
"load a grant policy from JSON" mechanism, the trading pack supplies the content.

---

## Scope (grant policy only)

- **`orchestration/packs/trading_grants.json`** — the 12-agent grant table, content moved verbatim
  from `DEFAULT_GRANTS`.
- **`agents/master/grants.py`** — delete `DEFAULT_GRANTS`; keep the `GrantPolicy` type; add
  `load_grant_policy(path) -> GrantPolicy` (read JSON, validate it is a dict-of-dicts).
- **`agents/master/settings.py`** — `grant_policy_path: str = ""` tunable (`MASTER_GRANT_POLICY_PATH`).
- **`agents/master/agent.py`** — when `grant_policy is None`, default to an **empty** policy (was
  `DEFAULT_GRANTS`). The substrate no longer ships trading knowledge.
- **`agents/master/entrypoint.py`** — load the policy from `settings.grant_policy_path` and inject it.
- **Tests** — master tests that relied on the substrate knowing "scanner"/"analyst" now inject a test
  policy; a new test loads the real `trading_grants.json` and asserts all 12 types + their caps
  (regression: the production policy is complete and matches the old `DEFAULT_GRANTS`).

## Out of scope (follow-ups)

- **`agents/master/secret_map.py`** — the *second* leak (also enumerates trading agent types). Same
  data-vs-import treatment, next sprint (S85).
- **Deploy plumbing** — getting `trading_grants.json` into the master image + setting
  `MASTER_GRANT_POLICY_PATH` in `infra/deploy-agents.ps1` / the master `Dockerfile`. Noted here;
  not CI-tested, done as a deploy follow-up.
- **Top-level `packs/` package** — deferred until a 2nd pack justifies it (ADR-0012: de jure now,
  de facto later). `orchestration/packs/` is the current home.

---

## Exit criteria

- [ ] `DEFAULT_GRANTS` no longer exists in `agents/master`; no substrate module names a trading type.
- [ ] `load_grant_policy` reads `trading_grants.json`; a test asserts the 12 types + caps match the
      old table (no behavior change for the deployed fleet).
- [ ] `MasterAgent` with no injected policy rejects every agent type (substrate knows nothing).
- [ ] `make ci` green; 100 % coverage; every module ≤ 200 lines; import-linter unchanged.

---

## Version bump

Refactor / internal boundary move, no new capability and no behavior change for the deployed fleet
→ **PATCH** (last two digits) per the HARD RULE. 0.23.00 → 0.23.01.

---

## Why this is the right first cut

It is the smallest change that actually *moves trading code out of the substrate* (not just adds a
seam). It is reversible, fully CI-provable, and establishes the data-file pattern that the second
leak (`secret_map.py`) reuses. See DL-12 in `docs/design-log.md`.
