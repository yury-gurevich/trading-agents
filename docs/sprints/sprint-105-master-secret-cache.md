# Sprint 105 — Master Key Vault secret cache (repeated-reference TTL cache)

**Phase:** Credential-validated activation (DL-36, supporting)
**Branch:** `sprint-105-master-secret-cache`
**Status:** shipped (0.45.00 → 0.46.00)
**Effort:** S

---

## Goal

The master fetches the same Key Vault secrets repeatedly (once per entitled agent, and
again with credential-testing, S104). A KV round-trip per repeated reference is wasteful.
**Operator directive (2026-07-01):** the master keeps a **local cache of whatever it fetched
from Key Vault**, with a configurable expiration — **3 / 5 / 10 / 0 minutes (0 = never expires)**
— for repeated references.

## What shipped

- **`agents/master/key_vault.CachingSecretStore`** — a `SecretStore` decorator that wraps any
  inner store (Azure Key Vault / env-var) and caches each fetched value for `ttl_minutes`
  (`0` = never expires). Only **non-empty** fetches are cached, so a missing secret is re-fetched
  and a newly-seeded one is picked up. Injectable clock for deterministic tests.
- **`MasterSettings.secret_cache_ttl_minutes`** — `tunable(5, ge=0, le=60, unit="minutes")`,
  `why` documents the operator dials 3 / 5 / 10 / 0.
- **Wired in `agents/master/entrypoint.main`** — the built secret store (Key Vault or env-var) is
  wrapped in `CachingSecretStore` with the settings TTL before it reaches `MasterAgent`.

## Proof

- `make ci` green: **1173 passed, 100% coverage**. Unit tests: repeated reference served from cache
  (one underlying fetch); TTL expiry re-fetches; `0` never expires; a miss is not cached (re-fetched).
- **Functionality check (real `SecretStore`):** wrapped a real `EnvVarSecretStore`, fetched a secret,
  **deleted the underlying env var**, fetched again → the cache returned the value (`CACHE SERVED THE
  REPEATED REFERENCE: YES`). Proves the repeated reference is served from memory without re-fetching.
  No Aura writes — no teardown beyond the process-local env var. (Live-KV verification awaits a
  provisioned Key Vault; the mechanism is store-agnostic.)

## Notes

Complements S104 (credential-tested activation): the master now tests credentials before handover
**and** caches the fetched values so repeated references don't re-hit Key Vault. Distinct from S104's
`PassCache` (which caches costly *test* results); this caches the fetched *secret values*.
