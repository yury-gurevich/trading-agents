# Sprint 108 — .env → Key Vault seeder, tested-before-insert (DL-36 family)

**Phase:** Credential-validated activation (DL-36)
**Branch:** `sprint-108-vault-seeder`
**Status:** planned
**Effort:** M–L

---

## Codex kickoff (paste this)

> Execute **Sprint 108 — .env → Key Vault seeder** exactly as specified in this file
> (`docs/sprints/sprint-108-vault-seeder.md`). It is a complete, self-contained handover.
>
> - **Start:** from `main` (`git pull`), `git checkout -b sprint-108-vault-seeder`. Read the files named
>   under *Execution notes* first.
> - **Hard gate every commit:** `make ci` green — 9 steps, **100 % coverage**, modules **≤ 200 lines**,
>   coding-agent `Agent:`/`Role:` headers. Bump `pyproject.toml` + `uv lock`.
> - **Core rule:** a secret is written to Key Vault **only if its live working-check passes**; a failing
>   or empty credential is **rejected/skipped, never written**. Default is **dry-run**; `--apply` writes.
> - **Real-environment check** (sprint-close rule): live against the **provisioned Azure Key Vault** +
>   real credentials, using throwaway `seedcheck-*` secret names, then **delete them** (leave the vault as
>   found). Record the row in `docs/laws/functionality-checks.md`.
> - **Boundaries:** the seed *mechanism* (`agents/master`) imports no agent/pack code; probes + manifest
>   are **injected**/pack data; only the `scripts/` composition root wires them together.
> - **Do NOT merge or push to `main`** — commit on the branch only, and stop for operator confirmation.
> - Read the *Session gotchas* before writing code. When done, append a **Closeout evidence** block (like
>   S107's) with the `make ci` result + the live-check evidence, and set **Status** to shipped.

---

## Goal

Seed the (already-provisioned) Azure Key Vault from `.env`, but **test each credential before it is
inserted** — only a credential whose live working-check passes is written; anything that fails or is empty
is **rejected**, never stored. This is DL-36 applied one step earlier: today the master tests a credential
*before handover*; this ensures only *working* credentials ever *enter* the vault, so the master's
handover-time test (S104) becomes defence-in-depth rather than the first line. The operator gets a clear
report of what was seeded, rejected, and skipped, and nothing is written by default (dry-run) until
`--apply`.

**Operator decisions (2026-07-02):**

- **Live working-check, not presence.** "Check if they are working — insert; if not, reject." Each secret
  has a real auth/connectivity probe; a probe failure blocks the write.
- **Key Vault is provisioned now** → the functionality check live-seeds + verifies against the real vault
  (using disposable `seedcheck-*` names, then deletes them).
- **Delivery:** Codex builds it from this handover.

## Scope

### In

**Substrate mechanism (master — the sole Key Vault accessor; pack-agnostic, injected probes):**

- `agents/master/vault_seed.py`:
  - `ProbeResult` (frozen): `ok: bool`, `message: str`.
  - `SeedEntry` (frozen): `kv_name`, `env_var`, `probe` (probe name). Loaded from a pack manifest.
  - `SeedOutcome` (frozen): `kv_name`, `status` (`seeded` | `rejected` | `skipped`), `message`.
  - `seed_vault(entries, env, probes, writer, *, apply) -> tuple[SeedOutcome, ...]`: for each entry,
    resolve `value = env.get(env_var, "")`; **empty → `skipped`**; else run `probes[probe](env)` (the probe
    may read companion creds from `env` — e.g. Alpaca needs id+secret, Neo4j needs uri+user+pass+db);
    **probe fail → `rejected` (never write)**; **pass → `writer.set_secret(kv_name, value)`** (only when
    `apply`) → `seeded`. An unknown probe name or a probe that raises = `rejected` (fail-closed — never
    write an unverified secret). The substrate ships **no** probes and **no** manifest.
  - `parse_seed_manifest` / `load_seed_manifest(path)` (pack JSON loader, like `load_remediations`).
- `agents/master/key_vault.py`: a `VaultWriter` Protocol (`get_secret`, `set_secret`, `delete_secret`);
  add `set_secret(name, value)` + `delete_secret(name)` to `AzureKeyVaultSecretStore` (currently
  read-only). The Azure calls stay `# pragma: no cover`; the seeder mechanism is tested against a
  **fake in-memory writer** so coverage holds at 100 %.

**Pack (trading, injected — ADR-0012):**

- `orchestration/packs/trading_vault_seed.json` — the manifest: one entry per KV secret (`kv_name`,
  `env_var`, `probe`). Seed the agent API-key names already listed in `trading_secrets.json` (Tiingo,
  Finnhub, FMP, the two Alpaca creds, Anthropic) plus the OpenAI key; **verify each `env_var` against the
  real `.env`** (the value to store lives there). Optionally add the master bootstrap credentials
  (`neo4j-*`) as a separate, clearly labelled group.
- `orchestration/packs/trading_vault_probes.py` — the live probes (orchestration may import `agents`):
  reuse existing clients, don't reinvent auth —
  - `neo4j` → `kernel.startup.graph_reachable` against a `build_graph_from_env()` store;
  - `tiingo` / `fmp` / `alpaca` (data) → `agents/provider/{tiingo,fmp,alpaca_data}.py` clients (a cheap
    authed GET / a 1-symbol fetch);
  - `alpaca` (broker) → `agents/execution/alpaca.py` `AlpacaBroker` account/status call;
  - `finnhub` → the provider Finnhub client (`agents/provider/fundamentals.py` or `sources.py`);
  - `openai` / `anthropic` → a minimal auth call via the `scripts/deliberate.py::_build_llm` pattern
    (models-list / 1-token completion). Each probe returns `ProbeResult(ok, message)` and **must not
    raise** on a bad credential (catch → `ok=False`).

**Composition root + CLI (`scripts/` — tooling, may import any layer):**

- `scripts/seed_key_vault.py`: load `.env` (explicit path), load the manifest + probes, build the
  `VaultWriter` (`AzureKeyVaultSecretStore(MASTER_KEY_VAULT_URL)`; auth via `DefaultAzureCredential`,
  which picks up the `AZURE_TENANT_ID`/`AZURE_CLIENT_ID`/`AZURE_CLIENT_SECRET` SP already in `.env`), run
  `seed_vault(apply=args.apply)`, print a **summary table** (seeded / rejected / skipped + messages).
  Flags: `--apply` (default dry-run), `--vault-url` (else `MASTER_KEY_VAULT_URL`), `--only <kv_name>…`.

### Out

- **Secret rotation / deletion of real secrets** (this only seeds/upserts). Destructive KV ops stay manual.
- **Reading secrets back into agents** — that is the master's existing `AzureKeyVaultSecretStore.get_secret`
  path (S104/S105); unchanged.
- Non-secret `.env` config (`LLM_PROVIDER`, `OPENAI_MODEL`, `MASTER_GRAPH`, the `AZURE_*` observability
  keys, …) — the manifest is an **allowlist**; only genuine agent/bootstrap secrets are seeded.
- A GUI; scheduled/automatic re-seeding.

## Deliverables

- `agents/master/vault_seed.py` (mechanism) + `VaultWriter` protocol + `set_secret`/`delete_secret` on
  `AzureKeyVaultSecretStore`.
- `orchestration/packs/trading_vault_seed.json` (manifest) + `orchestration/packs/trading_vault_probes.py`
  (live probes) + `scripts/seed_key_vault.py` (CLI/composition).
- Unit tests (fake writer + fake probes): pass → seeded (write called once with the right name/value);
  fail → rejected (**write never called**); empty → skipped; unknown/raising probe → rejected
  (fail-closed); dry-run never writes; `--only` filters; manifest parse errors. `make ci` green, 100 %
  coverage, modules ≤ 200 lines.

## Functionality check (sprint-close rule)

**Live against the provisioned Azure Key Vault + real credentials**, using disposable `seedcheck-*` secret
names so real secrets are never touched:

1. **Insert-on-pass:** a **real working** credential (e.g. the live Tiingo key from `.env`) under
   `seedcheck-tiingo` → its probe passes → `--apply` → **read it back** from the vault → present + equal.
2. **Reject-on-fail:** a deliberately **broken** credential (garbage value) under `seedcheck-badkey` → its
   probe fails → confirm **nothing was written** (`get_secret` returns empty / not-found).
3. **Dry-run:** the same pass case without `--apply` → reports `would seed`, **writes nothing** (read-back
   absent).

Capture the summary table as evidence. **Tear down:** `delete_secret` every `seedcheck-*` entry → vault
left exactly as found. Record the row in `docs/laws/functionality-checks.md`. (Auth: the `.env` SP needs
the **Key Vault Secrets Officer** role on the vault — note it in the closeout if a grant was required.)

## Dependencies

- **S104/S105** (`AzureKeyVaultSecretStore`, `resolve_config`, the secret map), DL-36. Reuses the
  `credential_test` pattern (injected working-checks) and the pack-data injection pattern
  (`load_remediations`/`load_secret_map`). `azure` extra (`azure-keyvault-secrets`, `azure-identity`) for
  the live writer.
- Requires `MASTER_KEY_VAULT_URL` in `.env` (add it) or `--vault-url`.

## Version bump

New capability (a seeding utility). **0.49.00 → 0.50.00** (feat → MINOR).

## Execution notes (for the coding agent — cold-start handover)

**Start.** From `main` (`git pull`; HEAD ≥ `a04c7ec`): `git checkout -b sprint-108-vault-seeder`. Read
`agents/master/{key_vault,secret_map,credential_test}.py`, `agents/master/entrypoint.py` (how the KV store
+ SP auth are already built), `orchestration/packs/trading_secrets.json`, `scripts/deliberate.py`
(`_build_llm`), `agents/provider/{tiingo,fmp,alpaca_data}.py`, `agents/execution/alpaca.py`, and the S104/
S105/S107 rows in `docs/laws/functionality-checks.md`.

**Gate.** `make ci` green — 9 steps, **100 % coverage**, modules ≤ 200 lines, coding-agent headers. Bump
`pyproject.toml` 0.49.00 → 0.50.00 + `uv lock`.

**Boundaries.** `agents/master/vault_seed.py` imports **no** agent/pack code (probes + manifest injected).
Probes live in `orchestration/packs/` (orchestration may import `agents`). `scripts/` is the only place
that wires probes + manifest + the real Azure writer together. Keep `make ci`'s import-linter green.

**Commit.** Branch-per-sprint; commit only your own files; conventional message ending with
`Co-Authored-By: …`. Do **not** merge/push to `main` without operator confirmation.

**Session gotchas (carried from S104–S107 + the DL-36 integration check):**

1. **`build_graph_from_env()` returns `InMemoryGraphStore` unless `NEO4J_URI` is in `os.environ`.** Any
   scratch/live script must `load_dotenv("<repo>/.env")` by explicit path.
2. **Aura** = instance `bce05bd6`; **user AND database are `bce05bd6`, not `neo4j`**. The Neo4j probe uses
   `graph_reachable` (a cheap read) — never hammer it with bad auth (the frenzy risk).
3. **Real LLM = GPT-5.5** via `scripts/deliberate.py::_build_llm` (`.env`, `LLM_PROVIDER=openai`); the
   openai/anthropic probes need `--extra llm`. Unit tests use fakes.
4. **`detect-secrets`** false-positives on `password`/`secret`/`key`/`token` next to a string literal in
   fixtures — use neutral names or `# pragma: allowlist secret`. The manifest/tests handle real secret
   *names* (`tiingo-api-key`) — keep **values** out of the repo (they live only in `.env` / the vault).
5. **`AzureKeyVaultSecretStore` is `# pragma: no cover`** (needs Azure); the seeder mechanism must be
   tested against a **fake in-memory `VaultWriter`** so the coverage floor holds. `set_secret`/
   `delete_secret` Azure calls stay pragma-excluded.
6. **mypy `--strict` covers `agents/**` tests**; annotate; `if TYPE_CHECKING:` for annotation-only imports.
   Agent test files under `agents/**/tests/` need the `Agent:`/`Role:` header; root `tests/` do not.
7. **Fail-closed:** an unknown probe, a raising probe, or any doubt = **do not write** the secret (the
   opposite of the remediation planner's fail-*open*: there we wanted a safe null plan; here a false
   "working" would poison the vault, so we refuse).
8. **Live check hygiene:** use `seedcheck-*` names only; `delete_secret` them all in teardown; never write
   or delete a real production secret name during the check.
9. `jq` is installed + allowed (`Bash(jq:*)`); `gh --jq` also works.

## Notes

This closes the credential lifecycle at the *source*: DL-36 made the master refuse a bad credential at
handover and self-heal within rails; this utility ensures a bad credential never reaches the vault in the
first place. Same principle (a credential is trusted only once proven to work), one step upstream —
fail-**closed** here (never write an unverified secret) as the mirror of the planner's fail-open.
