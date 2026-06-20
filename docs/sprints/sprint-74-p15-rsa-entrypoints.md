# Sprint 74 — P15 RSA signing + agent entrypoints

**Phase:** P15 (multi-agent container split)
**Branch:** `sprint-74-p15-rsa-entrypoints`
**Status:** shipped

---

## Goal

Wire RSA-PSS signing into the master/agent handshake and give every agent container
an executable entrypoint. Agents can now boot, call `POST /ehlo`, receive a signed
`ACTIVATE` payload, verify the master's identity, and block in an idle loop until
the event-loop is wired (S75+). Key Vault integration deferred to S75.

---

## What shipped

### New files

| File | Description |
| --- | --- |
| `kernel/crypto.py` | `generate_keypair()`, `sign_pss()`, `verify_pss()` — RSA-PSS (2048-bit, SHA-256, MAX\_LENGTH salt) |
| `kernel/bootstrap.py` | `activate_agent()` (injectable `_send`), `_verify_signature()`, `_http_post()` (scheme-guarded), `idle_loop()` |
| `agents/master/http_server.py` | `handle_health()`, `handle_ehlo()` (pure testable), `serve()` (pragma: no cover) |
| `agents/master/entrypoint.py` | `build_app()` (testable), `main()` (pragma: no cover) |
| `agents/{name}/entrypoint.py` | 12 trading-agent entrypoints (scanner/analyst/pm/execution/monitor/reporter/forecaster/operator/supervisor/curator/researcher/provider) |
| `tests/test_crypto.py` | 6 tests — keypair PEM format, round-trip, tamper detection, URL-safe base64 |
| `tests/test_bootstrap.py` | 8 tests — EHLO POST, payload return, capability declaration, URL stripping, scheme guard, signature verify/reject |
| `agents/master/tests/test_http_server.py` | 5 tests — health 200, EHLO 200 + signature, EHLO 400 missing field, EHLO 422 unknown agent |
| `agents/master/tests/test_master_entrypoint.py` | 2 tests — `build_app()` starts session, accepts custom settings |
| `tests/test_entrypoints.py` | 24 parametrised tests (12 agents × 2) — correct `agent_type` passed, `idle_loop()` called after activate |

### Modified files

| File | Change |
| --- | --- |
| `pyproject.toml` | `cryptography>=44.0` added to base deps; version `0.11.0 → 0.12.0` |
| `docker-compose.yml` | `x-agent-common` YAML anchor (DRY); `MASTER_URL` + `MASTER_PUBLIC_KEY_PEM` env vars on all trading agents |

### Key design decisions

- **Injectable `_send`** on `activate_agent()` — tests inject a fake callable; no monkeypatching of `urllib`.
- **Pure HTTP handlers** — `handle_health()` and `handle_ehlo()` are pure functions; HTTP wiring (`serve()`) is `# pragma: no cover`.
- **`build_app()` testable** — separates injected deps (graph + PEM) from env I/O so tests bypass `main()`.
- **Dev keypair fallback** — if `MASTER_PRIVATE_KEY_PEM` unset, master generates an ephemeral keypair and logs the public key; agents read `MASTER_PUBLIC_KEY_PEM` env var.
- **`idle_loop()` placeholder** — trading agents block after `ACTIVATE` until the event loop is wired (S75+).
- **Key Vault deferred** — `config={}` in `ACTIVATE` remains empty; deferred to S75 as `DRIFT-002`.

### Tests

951 tests (950 passed, 1 skipped-network). 100% coverage.

New clause citations: `MST-STA-01` (build\_app starts session).

### Version bump

`0.11.0 → 0.12.0` — **feat/MINOR** (new runtime capability: containers can boot, handshake, and verify master identity).

---

## Deferred (S75)

- Azure Key Vault integration: master resolves per-agent secrets and populates `config={}` in `ACTIVATE`.
- Push agent images to DockerHub; wire Azure Container Apps deploy manifest.
- Neo4j retry / exponential backoff on master startup failure.
- Durable handshake queue (replace in-process queue with Azure Service Bus).
