# Project State

**Last updated:** 2026-07-03 12:51 AEST · **Version:** 0.50.00 · **`make ci` + GHCR image build green on `main`.**

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + `STATE-01/02/03.md` + git). **LAW-02:** an item is "shipped" only when
its success factors are *proven* (tests, `make ci`, the named live check) — never restate intent as outcome.

---

## Current focus

Since P14 the project runs as **etalon-first continuous improvement** (DL-19). Two active arcs (DL-35
reverses the etalon pause for the fleet workstream only):

- **Fleet-serve transport (DL-35)** — give the control-plane agents a real serve/consume path so the
  distributed fleet can run. **S97 `serve_loop` + S98 supervisor/operator served — shipped**; S99–S103 remain.
- **Credential-security + bounded self-healing (DL-36) — ARC COMPLETE.** The master tests every
  credential before handover; failure → refuse + `Escalation` → LLM plans a bounded remediation →
  eval-gated auto-execute (one shot) → human. **A/B/C/D shipped (S104/S105/S106/S107)**; **S108** seeds
  Key Vault tested-before-insert (fail-closed) — the credential lifecycle is now closed at the source.

Layer-3 acceptance is 🟩 at the full S&P-500 (proven live 2026-06-26). The trade spine runs graph-pull
(DL-08). The fleet does **not** run distributed yet (S99–S103).

## Recent (most recent first — detail in each sprint doc)

- **S108 (DL-36 family, 0.49.00→0.50.00)** — `.env`→Key Vault seeder, **tested-before-insert**: a secret
  enters the vault only after a live working-check passes; failing/empty/unverifiable creds are rejected
  (fail-closed), dry-run by default. Also fixed a latent secret-map bug (provider Alpaca-secret env var).
  Codex-built, reviewed, `make ci` 100% + **live check** on vault `trading-agents-kv`. Merged `bfd7cf8`.
- **S107 (DL-36 D, 0.47.00→0.49.00)** — eval-gated auto-remediation execution: DSPy behind ADR-0010's
  `PromptOptimizer` port gates the selector; safe executors run the `test→execute→production→documentation`
  loop (one automatic shot then human); + thread-safe activation IDs + composition-root wiring. Codex-built,
  reviewed, `make ci` 100% + **live GPT-5.5** check on Aura (selector 5/5, gate trips, refetch heals). Merged `f980965`.
- **S106 (DL-36 C, 0.47.00)** — bounded-catalogue LLM remediation planner (enum guardrail, fail-open,
  configurable `auto_remediation_scope`); plans + gates, never executes. Live GPT-5.5 check. Merged `8f74bfa`.
- **DL-36 A/B (0.44.01→0.46.00)** — master **login-frenzy fix** (correct deploy creds +
  `kernel.startup.ensure_reachable_or_halt`, never crash-loop) · **S104** credential-tested activation
  (refuse + `Escalation`) · **S105** KV secret cache (TTL `3/5/10/0`, 0=never).
- **Fleet-serve S97+S98 (0.42.00→0.44.00)** — kernel `serve_loop` primitive; supervisor/operator served
  in-process (`idle_loop()` retired).

Older sprints — S77–96 detail → [STATE-03.md](STATE-03.md) · S37–76 → [STATE-02.md](STATE-02.md) ·
S36→P0 → [STATE-01.md](STATE-01.md); full index `docs/sprints/README.md`.

## Now

On `main`, no active sprint branch. The etalon north-star holds (DL-19): remaining gray law clauses →
green with cited tests; **every sprint ends with a real-environment functionality check**
(`docs/laws/functionality-checks.md`) + teardown. Each sprint/chore on its own `sprint-NN-<slug>` branch;
merge to `main` is the deploy trigger (rebuilds + pushes agent images). Coding may be done here or handed
to Codex via a self-contained sprint file (proven on S106).

## Next

- **Remaining DL-36 hardening** — destructive executors (`rotate-credential`/`recreate-instance`) stay
  human-manual until an Azure/Aura write path + rollback + approval UI land; the diskcache CVE from the
  offline DSPy extra → hardening-backlog (not in runtime/images).
- **Fleet arc S99–S103** — serve forecaster/curator/researcher (S99) · Service Bus receiver + parity
  (S100, etalon cut line) · permanent Neo4j (S101) · 13-container run-through + distributed acceptance
  (S102) · dispatcher cron (S103).
- **Deferred behind a perfect etalon (DL-19):** CI-1..CI-6 (ADR-0013, S90–S95) · the bundle **generator** ·
  ADR-0010 reusable predictor registry/promotion (first instance landed in S107) · P12 scorecard-run (needs
  a live news runway) · P13 cross-asset graph · `contracts/` substrate/pack split.

## Pointers

Product `docs/PRD.md` · architecture `docs/architecture.md` · phases `docs/build-plan.md` · closed
decisions `docs/decisions/INDEX.md` · open threads `docs/design-log.md` · "does it work"
`docs/laws/{ledger,drift-register,functionality-checks}.md` · per-agent `agents/<name>/mission.md`.
