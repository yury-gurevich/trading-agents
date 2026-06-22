# Sprint 77 — Canonical credential-naming reconciliation

**Phase:** P15 (multi-agent container split)
**Branch:** `sprint-77-credential-naming`
**Status:** planned

---

## Goal

Align the three sources of truth for credential names so that the KV→ACTIVATE.config→env
pipeline actually lands secrets in the right env-var slots when agents boot.

The config→env bridge (`_apply_config`, shipped 0.16.0) writes `ACTIVATE.config` keys straight
into `os.environ`. If the key names are wrong the env vars sit unused; settings read empty strings.
This sprint fixes the key names — no logic change, just naming.

---

## Background: the mismatch

`resolve_config()` in `secret_map.py` currently converts kebab-case KV names to `UPPER_SNAKE`
with no prefix:

```text
tiingo-api-key  →  TIINGO_API_KEY
finnhub-api-key →  FINNHUB_API_KEY
anthropic-api-key → ANTHROPIC_API_KEY
```

But agent settings use `env_prefix` so they read:

| Agent | Setting field | Env var actually read |
| --- | --- | --- |
| provider | `tiingo_api_key` | `PROVIDER_TIINGO_API_KEY` |
| provider | `finnhub_api_key` | `PROVIDER_FINNHUB_API_KEY` |
| provider | `fmp_api_key` | `PROVIDER_FMP_API_KEY` |
| execution | `alpaca_api_key` | `EXECUTION_ALPACA_API_KEY` (primary alias) |
| execution | `alpaca_secret_key` | `EXECUTION_ALPACA_SECRET_KEY` (primary alias) |
| operator | `anthropic_api_key` | `OPERATOR_ANTHROPIC_API_KEY` |

Also in `.env`: `FNP_API_KEY` is a typo for FMP; `ALPACA_API_KEY` (live) vs
`ALPACA_PAPER_API_KEY` (paper) need to be intentional.

---

## Scope

### 1 — Audit each entitled agent's settings file

Confirm every secret field's final env-var name (including prefix and aliases). Tick off:

- [ ] `ProviderSettings` — tiingo, finnhub, fmp, alphavantage, fred, alpaca (if any)
- [ ] `ExecutionSettings` — alpaca key + secret (primary aliases confirmed above)
- [ ] `OperatorSettings` — anthropic key

### 2 — Update `secret_map.py`

Change `AGENT_SECRETS` from `list[str]` of KV secret names to
`list[tuple[str, str]]` of `(kv_secret_name, env_var_name)`.
Update `resolve_config()` to use the explicit env-var name instead of the
auto-converted UPPER_SNAKE.

Example shape after change:

```python
AGENT_SECRETS: dict[str, list[tuple[str, str]]] = {
    "provider": [
        ("tiingo-api-key",   "PROVIDER_TIINGO_API_KEY"),
        ("finnhub-api-key",  "PROVIDER_FINNHUB_API_KEY"),
        ("fmp-api-key",      "PROVIDER_FMP_API_KEY"),
    ],
    "execution": [
        ("alpaca-key-id",    "EXECUTION_ALPACA_API_KEY"),
        ("alpaca-secret-key","EXECUTION_ALPACA_SECRET_KEY"),
    ],
    "operator": [
        ("anthropic-api-key","OPERATOR_ANTHROPIC_API_KEY"),
    ],
}

def resolve_config(agent_type: str, store: SecretStore) -> dict[str, object]:
    config: dict[str, object] = {}
    for kv_name, env_name in AGENT_SECRETS.get(agent_type, []):
        value = store.get_secret(kv_name)
        if value:
            config[env_name] = value
    return config
```

### 3 — Fix `.env` typo

Rename `FNP_API_KEY` → `FMP_API_KEY` (or `PROVIDER_FMP_API_KEY` once prefix is canonical).
Document paper-vs-live Alpaca stance: use `ALPACA_PAPER_API_KEY` / `ALPACA_PAPER_API_SECRET`
as the `.env` names; execution's `AliasChoices` already resolves them.

### 4 — Update tests

`test_secret_map.py` — update fixtures to use the new tuple structure; assert env-var name
in the resolved config dict, not the old `UPPER_SNAKE` auto-conversion.

### 5 — `make ci` green

No version bump needed for this section if only internal naming changes. If any public
contract field changes, bump patch (MINOR rule does not apply — this is a fix).
Assign 0.17.0 (MINOR) if any new capability is added; otherwise 0.16.1 (PATCH fix).

---

## Files to modify

| File | Change |
| --- | --- |
| `agents/master/secret_map.py` | `AGENT_SECRETS` tuple pairs + `resolve_config` signature |
| `tests/test_secret_map.py` | Update fixtures and assertions |
| `.env` | Fix `FNP_API_KEY` typo; document paper Alpaca names |
| `docs/design-log.md` | Mark DL-07b CLOSED |
| `docs/STATE.md` | Update at closeout |

---

## Exit criteria

- [ ] `resolve_config("provider", store)` emits `PROVIDER_TIINGO_API_KEY`, not `TIINGO_API_KEY`
- [ ] `resolve_config("execution", store)` emits `EXECUTION_ALPACA_API_KEY`
- [ ] `resolve_config("operator", store)` emits `OPERATOR_ANTHROPIC_API_KEY`
- [ ] `make ci` green (all 9 steps)
- [ ] `.env` has no `FNP_` typo

---

## Version bump

Fix — no new capability. **0.16.1** (PATCH, last two digits).

---

## Deferred (S78+)

- Alpaca paper-vs-live call (paper keys safe to seed in KV after this sprint)
- Provider Alpaca fields (if provider needs Alpaca as OHLCV failover, add to `ProviderSettings`)
- Agent work loops (S78 / S79)
