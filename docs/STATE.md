# Project State

**Last updated:** 2026-07-02 18:51 AEST · **Version:** 0.47.00 · **`make ci` + GHCR image build green on `main`.**

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + `STATE-01/02.md` + git). **LAW-02:** an item is "shipped" only when
its success factors are *proven* (tests, `make ci`, the named live check) — never restate intent as outcome.

---

## Current focus

Since P14 the project runs as **etalon-first continuous improvement** (DL-19). Two active arcs (DL-35
reverses the etalon pause for the fleet workstream only):

- **Fleet-serve transport (DL-35)** — give the control-plane agents a real serve/consume path so the
  distributed fleet can run. **S97 `serve_loop` + S98 supervisor/operator served — shipped**; S99–S103 remain.
- **Credential-security + bounded self-healing (DL-36)** — the master tests every credential before
  handover; failure → refuse + `Escalation` → LLM plans a bounded remediation → human / one-shot gate.
  **A/B/C shipped (S104/S105/S106); Piece D (execute→production→documentation) next.**

Layer-3 acceptance is 🟩 at the full S&P-500 (proven live 2026-06-26). The trade spine runs graph-pull
(DL-08). The fleet does **not** run distributed yet (S99–S103).

## Recent (most recent first — detail in each sprint doc)

- **S106 (DL-36 C, 0.47.00)** — bounded-catalogue LLM remediation planner (enum guardrail, fail-open,
  configurable `auto_remediation_scope`); plans + gates, never executes. Executed by Codex, reviewed,
  **live GPT-5.5** check on Aura. Merged `8f74bfa`.
- **DL-36 A/B (0.44.01→0.46.00)** — master **login-frenzy fix** (correct deploy creds +
  `kernel.startup.ensure_reachable_or_halt`, never crash-loop) · **S104** credential-tested activation
  (refuse + `Escalation`) · **S105** KV secret cache (TTL `3/5/10/0`, 0=never).
- **Fleet-serve S97+S98 (0.42.00→0.44.00)** — kernel `serve_loop` primitive; supervisor/operator served
  in-process (`idle_loop()` retired). Also: `jq` approved + documented; merged branches pruned.
- **S96 (0.40.00→0.42.00)** — deliberation define-then-justify + scored understanding gate + asymmetric
  challenger-veto with transcript persistence (DL-31).

Older sprints (S37–S95): `docs/sprints/README.md` + `STATE-02.md`.

## Now

On `main`, no active sprint branch. The etalon north-star holds (DL-19): remaining gray law clauses →
green with cited tests; **every sprint ends with a real-environment functionality check**
(`docs/laws/functionality-checks.md`) + teardown. Each sprint/chore on its own `sprint-NN-<slug>` branch;
merge to `main` is the deploy trigger (rebuilds + pushes agent images). Coding may be done here or handed
to Codex via a self-contained sprint file (proven on S106).

## Next

- **DL-36 Piece D** — the remediation *pipeline* (`test → execute → production → documentation`, the one
  automatic shot). **Highest-risk:** executors act; destructive `rotate-credential`/`recreate-instance`
  need Azure/Aura write + rollback. First cut = **safe executors only** (`refetch`/`resume`); destructive
  stay human-manual. (Handover: `docs/sprints/` — to be written.)
- **Fleet arc S99–S103** — serve forecaster/curator/researcher (S99) · Service Bus receiver + parity
  (S100, etalon cut line) · permanent Neo4j (S101) · 13-container run-through + distributed acceptance
  (S102) · dispatcher cron (S103).
- **Deferred behind a perfect etalon (DL-19):** CI-1..CI-6 (ADR-0013, S90–S95) · the bundle **generator** ·
  P12 scorecard-run (needs a live news runway) · P13 cross-asset graph · `contracts/` substrate/pack split.

## Pointers

Product `docs/PRD.md` · architecture `docs/architecture.md` · phases `docs/build-plan.md` · closed
decisions `docs/decisions/INDEX.md` · open threads `docs/design-log.md` · "does it work"
`docs/laws/{ledger,drift-register,functionality-checks}.md` · per-agent `agents/<name>/mission.md`.
