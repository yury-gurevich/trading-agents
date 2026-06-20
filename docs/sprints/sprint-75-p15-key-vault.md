# Sprint 75 — P15 Azure Key Vault secret distribution

**Phase:** P15 (multi-agent container split)
**Branch:** `sprint-75-p15-key-vault`
**Status:** shipped

---

## Goal

Master resolves per-agent secrets from Azure Key Vault (prod) or env vars (dev) and
injects them into `config={}` in every `ACTIVATE` message. Closes the `DRIFT-002`
law violation opened in S73 and filled in with `config={}` stub in S74.

---

## What shipped

### New files

| File | Description |
| --- | --- |
| `agents/master/key_vault.py` | `SecretStore` Protocol + `NullSecretStore` + `EnvVarSecretStore` + `AzureKeyVaultSecretStore` (lazy azure SDK imports, `# pragma: no cover`) |
| `agents/master/secret_map.py` | `AGENT_SECRETS` per-agent entitlement table + `resolve_config(agent_type, store)` — fetches entitled secrets, skips empty values, returns flat `dict[str, object]` keyed by `UPPER_SNAKE` |
| `agents/master/tests/test_key_vault.py` | 9 tests — NullSecretStore Protocol membership, env var conversion, set/unset/deleted env vars |
| `agents/master/tests/test_secret_map.py` | 9 tests — null store + unknown agent → `{}`, env var resolution, skip-empty, entitlement table, MasterAgent integration (MST-DEP-02 citation) |

### Modified files

| File | Change |
| --- | --- |
| `agents/master/agent.py` | Added `secret_store: SecretStore | None = None` param; `activate()` calls `resolve_config(agent_type, self._secret_store)` to populate `config` |
| `agents/master/entrypoint.py` | `build_app()` gains `secret_store` param; `main()` selects `AzureKeyVaultSecretStore` when `MASTER_KEY_VAULT_URL` is set, else `EnvVarSecretStore` |
| `agents/master/grants.py` | Removed stale "S74" comment |
| `agents/master/laws/laws.md` | DRIFT-001 → RESOLVED S74; DRIFT-002 → RESOLVED S75; changelog bumped to v1.1 |
| `contracts/master.py` | `ACTIVATEMessage.signature` docstring corrected (no longer says "stub") |
| `pyproject.toml` | Version `0.12.0 → 0.13.0`; azure extra: `azure-keyvault-secrets>=4.8`, `azure-identity>=1.16`; mypy overrides extended for `azure.*` modules |
| `docker-compose.yml` | Master service gets `MASTER_KEY_VAULT_URL: ${MASTER_KEY_VAULT_URL:-}` env var |
| `uv.lock` | `uv lock` added azure-identity v1.25.3, azure-keyvault-secrets v4.11.0, msal v1.37.0, msal-extensions v1.3.1 |
| `docs/build-plan.md` | P15 phase section + 4 missing status rows (Qlib Q1, law backfill, ADR-0010, P15) |

### Key design decisions

- **`SecretStore` Protocol** — `runtime_checkable` so isinstance checks work in tests without importing
  concrete implementations. Three impls: `Null` (tests), `EnvVar` (local dev), `AzureKeyVault` (prod).
- **Secret name convention** — kebab-case in Key Vault (`tiingo-api-key`), `UPPER_SNAKE` in
  `ACTIVATE.config` (`TIINGO_API_KEY`). Conversion: `name.upper().replace("-", "_")`.
- **Only 3 agents have external creds** — `provider`, `execution`, `operator`. All others receive
  `config={}`. This matches the minimum-privilege principle from the master laws.
- **Lazy azure SDK imports** — `AzureKeyVaultSecretStore.__init__` imports inside the method body so
  the azure SDK is not required in the dev environment; the entire class is `# pragma: no cover`.
- **`NullSecretStore` backward compat** — returns `""` for all queries → `resolve_config` skips all
  → `config={}`. Every existing test checking `msg.config == {}` passes unchanged.
- **`EnvVarSecretStore` as local-dev default** — `main()` falls back to `EnvVarSecretStore` when
  `MASTER_KEY_VAULT_URL` is unset, so the system works in dev without Key Vault creds.

### Tests

971 tests (971 passed, 4 skipped-network). 100% coverage.

New clause citations: `MST-DEP-02` (master resolves Key Vault secrets, injects into config).

### Version bump

`0.12.0 → 0.13.0` — **feat/MINOR** (new runtime capability: master distributes per-agent
minimum-privilege secrets via `ACTIVATE.config`).

---

## Deferred (S76+)

- Push agent images to DockerHub; wire Azure Container Apps deploy manifest.
- Neo4j retry / exponential backoff on master startup failure.
- Durable handshake queue (replace in-process queue with Azure Service Bus).
- Secret rotation: re-ACTIVATE on Key Vault event notification.
