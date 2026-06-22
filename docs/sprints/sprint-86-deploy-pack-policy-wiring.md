# Sprint 86 — Deploy wiring: feed the pack policy + secret map to the master

**Phase:** P15 → ADR-0012 platform/pack wall (deploy follow-up to S84+S85)
**Branch:** `sprint-86-deploy-pack-policy-wiring`
**Status:** shipped (0.23.03)

---

## Goal

S84+S85 made the master substrate pack-agnostic: it loads the grant policy and secret map from
injected data, not hardcoded tables. But the deployed master is given **neither** — so a real deploy
would load empty policies and **reject every agent**. This sprint feeds the pack data to the master at
deploy time, **without re-coupling pack data into the substrate image**.

## The key decision — content as config, not baked into the image

The master Docker image copies only `kernel/`, `contracts/`, `agents/master/` — pure substrate. The
naive fix (COPY `orchestration/packs/*.json` into the image) would re-bake trading data into the
substrate image, so the same image could no longer run a different pack — defeating S84/S85.

Instead the pack policy travels as **deploy-time config**, exactly like `MASTER_PRIVATE_KEY_PEM_B64`:

- **Cloud (`deploy-agents.ps1`)** reads the two pack JSONs, base64-encodes them, and passes
  `MASTER_GRANT_POLICY_B64` / `MASTER_SECRET_MAP_B64` to the master container. (b64 avoids the az-CLI
  `--env-vars KEY=VALUE` quoting/newline trap.)
- **Local (`docker-compose.yml`)** mounts `orchestration/packs/` read-only into the master and sets
  the `MASTER_*_PATH` vars.

Either way the **master image stays pack-agnostic** — the pack is injected, never built in.

---

## Scope

- **`agents/master/grants.py`** — extract `parse_grant_policy(text)`; `load_grant_policy(path)` delegates.
- **`agents/master/secret_map.py`** — extract `parse_secret_map(text)`; `load_secret_map(path)` delegates.
- **`agents/master/settings.py`** — add `grant_policy_b64` + `secret_map_b64` (inline base64 JSON content;
  take precedence over the file path).
- **`agents/master/entrypoint.py`** — resolve each policy: **b64 content → path → None**.
- **`infra/deploy-agents.ps1`** (untested by CI) — base64-encode the two pack JSONs, pass them in the
  master's env vars.
- **`docker-compose.yml`** (untested by CI) — mount `orchestration/packs/` ro + set the path vars.
- **Tests** — `parse_*` happy/malformed; the entrypoint b64-precedence path loads a real policy.

## Out of scope

- Multi-pack selection / a top-level `packs/` package — ADR-0012, deferred to a 2nd pack.
- `contracts/` substrate/pack split.

---

## Exit criteria

- [x] Master image (`agents/master/Dockerfile`) unchanged — no pack data baked in; still pure substrate.
- [x] `build_app` loads the grant policy + secret map from base64 env content (test) and from a path
      (existing S85 test), b64 taking precedence (`_resolve_pack`).
- [x] `deploy-agents.ps1` passes `MASTER_GRANT_POLICY_B64` + `MASTER_SECRET_MAP_B64`; compose mounts the
      packs dir read-only + sets the path vars.
- [x] `make ci` green; 100 % coverage; modules ≤ 200 lines; import-linter unchanged.

---

## Version bump

New runtime config capability (load policy from env content) → **PATCH** (no new agent/endpoint, deploy
plumbing). 0.23.02 → 0.23.03.
