# Sprint 85 — Platform/pack separation: relocate the secret map out of the substrate

**Phase:** P15 → ADR-0012 platform/pack wall
**Branch:** `sprint-85-platform-pack-secret-map`
**Status:** shipped (0.23.02)

---

## Goal

Close the **second** named platform/pack leak (DL-12). `agents/master/secret_map.py::AGENT_SECRETS`
enumerates trading agent types (provider/execution/operator) and their domain secret names
(`tiingo-api-key`, `alpaca-*`, `anthropic-api-key`, …) inside the **substrate**. Apply the exact
pattern S84 proved for grants: move the table to a pack data file the master loads **by path**.

---

## Scope

- **`orchestration/packs/trading_secrets.json`** — the per-agent `(kv_name, env_name)` entitlement
  table, content moved verbatim from `AGENT_SECRETS`.
- **`agents/master/secret_map.py`** — delete `AGENT_SECRETS`; add `SecretMap` type +
  `load_secret_map(path) -> SecretMap`; `resolve_config(agent_type, store, secret_map)` gains the
  injected map (was a module global).
- **`agents/master/settings.py`** — `secret_map_path: str = ""` (`MASTER_SECRET_MAP_PATH`).
- **`agents/master/agent.py`** — `MasterAgent` takes an injected `secret_map` (default empty); passes
  it to `resolve_config` in `activate()`.
- **`agents/master/entrypoint.py`** — load the secret map from `settings.secret_map_path`, inject it.
- **Tests** — `resolve_config` calls thread the map; a shared helper loads the real
  `trading_secrets.json`; a loader test covers `load_secret_map` happy + error paths.

## Out of scope

- **Deploy plumbing** — ship `trading_secrets.json` into the master image + set
  `MASTER_SECRET_MAP_PATH` (with the S84 `MASTER_GRANT_POLICY_PATH`) in `infra/deploy-agents.ps1` /
  the master Dockerfile. Both deploy follow-ups land together; not CI-tested.

---

## Exit criteria

- [x] `AGENT_SECRETS` no longer exists in `agents/master`; no substrate module names a trading secret.
- [x] `load_secret_map` reads `trading_secrets.json`; a test asserts the entitlements match the old
      table (no behavior change for the deployed fleet).
- [x] `MasterAgent` with no injected map resolves an empty config for every agent type.
- [x] `make ci` green; 100 % coverage; modules ≤ 200 lines; import-linter unchanged.

---

## Version bump

Internal boundary move, no behavior change → **PATCH**. 0.23.01 → 0.23.02.

---

## Why now

S84 proved the data-file pattern for the grant policy; this is the mechanical repeat that closes the
**last named DL-12 leak** in the master. After this, the substrate's master names zero trading
concepts (grants and secrets both pack-supplied as data). See DL-12 in `docs/design-log.md`.
