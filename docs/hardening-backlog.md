<!-- Agent: planning | Role: cross-cutting security/quality backlog (not a feature phase) -->
# Hardening backlog

Cross-cutting supply-chain, security, and code-quality improvements that are **deferred but not
dropped**. Each item names its **unblock trigger** — the event after which it should be picked up —
so it resurfaces at the right time instead of being forgotten. Reviewed whenever a trigger fires or
at sprint boundaries; referenced from `docs/STATE.md` Pointers.

## Done

- **A — least-privilege workflow token** (`permissions: contents: read` in `ci.yml`). Shipped
  2026-06-18 (`chore/dependabot-and-hygiene`).
- **B — GitHub Actions pinned to commit SHAs** (Dependabot `github-actions` ecosystem keeps them
  fresh). Shipped 2026-06-18.
- **Dependabot** (uv / github-actions / docker). Shipped 2026-06-18 weekly; **moved to monthly,
  batched 2026-07-27** (DL-64) after a weekly trickle of solo major PRs was closed unread rather
  than reviewed. Majors now fold into the group everywhere except Python *production* deps, which
  keep a solo PR. ≤3 PRs in a typical month.
- **Dependabot alerts + security updates enabled** 2026-07-27. Previously `disabled` — the CVE net
  was `pip-audit` in `make ci` (Python) plus Trivy HIGH/CRITICAL at image build (image contents),
  leaving **GitHub Actions and base-image advisories unwatched by anything**. Enabled with **zero
  open alerts** at the time (no backlog). Security PRs bypass the monthly schedule and the
  `open-pull-requests-limit`, so a vulnerability still arrives the day the advisory drops.
- **Dependabot auto-merge** (`.github/workflows/dependabot-auto-merge.yml`): non-major dependency PRs
  auto-approve + auto-merge once the required CI checks pass; branch protection on `main` requires
  `quality` + `test` + `security`. Majors stay open for review; docker `python` majors are ignored
  (codebase targets 3.13). Shipped 2026-06-18 (`chore/dependabot-automerge`).
- **C — CodeQL SAST** (`.github/workflows/codeql.yml` plus the CI security lane with
  `GHAS_ENABLED=true`). Enforcing since 2026-07-04; S127 proved zero open error-level findings and
  the security lane remains required alongside `pip-audit` and `detect-secrets`. Evidence:
  [S129 GitHub hardening proof](reports/sprint-129-fixpack/live-proof.md#3-github-hardening-proof).
- **D — dependency review on PRs** (`.github/workflows/ci.yml`). Shipped in S129 with
  `actions/dependency-review-action` pinned to `2031cfc080254a8a887f58cffee85186f0e49e48`
  (`v4.9.0`), failing moderate-or-higher vulnerable additions and the explicit denied package
  `pkg:pypi/pycrypto`. Evidence:
  [S129 GitHub hardening proof](reports/sprint-129-fixpack/live-proof.md#3-github-hardening-proof).
- **E — container image scanning** (`.github/workflows/build-images.yml`). Shipped in S129 with
  Trivy pinned to `ed142fd0673e97e23eac54620cfb913e5ce36c25` (`v0.36.0`), gating HIGH/CRITICAL
  OS/library findings on representative images for the runtime-only, runtime+Azure, and
  forecaster dependency-layer families (`analyst`, `master`, `forecaster`). Accepted findings must
  be documented in `.trivyignore` with sprint/design-log evidence, scope, owner, and expiry.
  Evidence:
  [S129 GitHub hardening proof](reports/sprint-129-fixpack/live-proof.md#3-github-hardening-proof).
- **F — build + push deploy pipeline** (`.github/workflows/build-images.yml` +
  `scripts/record_deploy.py`). The real shipped shape builds and pushes all 14 images to GHCR on
  `main` and manual dispatch, then records deploy currency through the DL-46 `DeployRecord` flow.
  ADR-0007 still names DockerHub; DL-50 surfaces the GHCR drift and queues a formal ADR amendment
  instead of silently rewriting the accepted ADR. Evidence:
  [S129 GitHub hardening proof](reports/sprint-129-fixpack/live-proof.md#3-github-hardening-proof).
- **G — mutation testing (`mutmut`)**. Shipped in S132 as a manual periodic exercise, not a CI
  gate. The scoped decision-engine run improved from 5,282/6,731 killed (78.47%) to 5,376/6,731
  killed (79.87%); the remaining 1,355 survivor/no-test rows are documented-equivalent in the
  report. Re-run after a stable sprint or when decision-engine gate logic changes. Evidence:
  [S132 mutation testing report](reports/sprint-132-mutation-testing/README.md).
- **H — base-image CVE remediation** (`agents/*/Dockerfile`, `orchestration/Dockerfile`, and
  `.github/workflows/build-images.yml`). Shipped in S130: Trivy now ignores unfixed findings while
  still failing fixed HIGH/CRITICAL OS/library findings, `.trivyignore` remains empty, and all 14
  images use two-stage `dhi.io/python:3.13-dev` -> `dhi.io/python:3.13` builds with venv-carrying
  runtimes. Manual `build-images` run `29681635979` built/pushed all 14 `s130-test` images and
  passed every Trivy gate; the actionable finding count dropped from S129's representative `22` to
  `0` gate-blocking findings. Evidence:
  [S130 base-image live proof](reports/sprint-130-base-image/live-proof.md#final-live-run).
- **J — dispatcher image carries only its measured runtime slice.** Shipped in S131:
  `scripts/dispatch_scheduled_run.py` was measured at a 43-file calendar-skip closure and a
  44-file fake-trading-day closure; `orchestration/Dockerfile` now copies `kernel/`,
  `contracts/`, the scheduled-dispatch orchestration files, the two needed agent modules
  (`agents/provider/domain/market_calendar.py`, `agents/scanner/universe.py`), and the
  dispatcher script/universe file instead of wholesale `agents/`, `orchestration/`, and
  `scripts/`. Evidence:
  [S131 blast-radius proof](reports/sprint-131-blast-radius/live-proof.md#row-j-dispatcher-image).
- **K — assertion-strength gap in trade-gating + money-parsing code** (surfaced by S132
  mutation). Closed in S134 over three rounds: R1 killed the alpaca money-parser bucket
  (39 → 7 named default-normalization residuals) plus the PM gate / reward-risk / sector
  boundaries; R2 took the targeted analyst-domain survivors 249 → 127 with a per-module
  before/after table; R3 forced **all 127** into an auditable per-mutant disposition —
  **107 killed, 12 individually justified equivalents, 8 named wording exclusions, 0
  untriaged**. Scoped decision-engine kill-rate 79.87 % → **84.36 %** (5,678/6,731).
  Permanent justified non-targets: the `# pragma: no cover` Alpaca HTTPS transport
  (live/paper-verified), string/render/audit wording survivors, the 7 `_fill_from_order`
  default-normalization residuals, and the 20 R3 residuals named individually in the CSV.
  Evidence: [S134 report](reports/sprint-134-assertion-hardening/README.md) +
  [Round 3 dispositions](reports/sprint-134-assertion-hardening/round-3-dispositions.csv).
- **I — per-agent blast-radius scoping, Postgres + Service Bus.** Part 1 shipped in
  S131: 15 per-agent Neon/Postgres roles with secret-backed `POSTGRES_DSN` delivery.
  Part 2 shipped in S133: the shared Service Bus namespace string was replaced for
  measured bus targets by entity-level topic SAS rules, per-target Key Vault
  primary/bundle secrets, Container Apps secretRefs, and a rollback-only shared
  credential path. The bus carries claim-check refs/RPC envelopes, not data, so this
  is lower severity than the Postgres half; the value is attribution, revocability,
  and removal of the last shared runtime credential. Evidence:
  [S131 Postgres proof](reports/sprint-131-blast-radius/live-proof.md) +
  [S133 Service Bus proof](reports/sprint-133-servicebus-sas/live-proof.md).
- **L — standing container smoke check: every agent image starts its real entrypoint.**
  Shipped 2026-07-22 (`chore-container-smoke`). DRIFT-016/017/018 were the *same* defect three
  times — an agent container not starting its real entrypoint, recorded as "unit gate hid it"
  (×2) and "hidden by local graph demos", each caught only by a live fleet run. A provider-only
  smoke already proved the assertion shape; `build-images.yml` now applies it to **all 12 agent
  images** (`master` performs no master-handshake; `dispatcher` keeps its calendar-skip smoke):
  run with no activation config and require a **non-zero exit** *and* output reaching for the
  master, which proves the entrypoint ran the agent rather than merely that the image exists.
  Adds a 180 s timeout (exit 124) so a hang fails loudly. Verified by dispatch run
  `29904029290` — all 14 jobs green and **all 12 images printed the assertion**, confirming the
  step executed rather than silently skipping (the DL-52 failure mode). Motivated by the R006
  [defect-detection-rate analysis](research/code-quality-tooling/defect-detection-rate.md):
  the unit suite caught **0 of 14** escaped defects, so this was the highest-leverage quality
  work available.
- **L² — `make ci` can fail on a CVE.** (The letter is reused: the entry above is the
  older L from the A–L series; this is L from the 2026-07-23 series.) Was: the Makefile's
  `-uv run pip-audit` made make ignore its exit status, so the *local* gate could not fail on a
  vulnerable dependency. Fixed in `77769ce` (0.75.00, 2026-07-24) — the recipe is now a bare
  `uv run pip-audit`. **Both halves** are closed: `gate_selftest_cases.py` covers it twice —
  `pip-audit-cve` proves the gate *can* fail, and `pip-audit-not-ignored-by-ci` asserts the
  recipe does **not** carry the leading dash, so it cannot come back unnoticed. Verified
  2026-07-27; the row sat stale in *Open* for three days after the fix landed, which is why
  STATE was still advertising it as a live gap.
- **R — law roll-ups are derived and checked.** Closed in S156: the new
  `scripts/check_law_coverage.py` gate hard-fails when `docs/laws/ledger.md` or
  `docs/laws/INDEX.md` disagrees with the counts derived from `agents/*/laws/test-plan.md`.
  Before S156 reconciliation, the checker flagged roll-up mismatches for **12 of 14 agents**
  once both green and total counts were derived from test-plan rows (the original row-R spot
  check found 8 green-count mismatches). After S156, both roll-ups match the derived table:
  book-wide green is **260 / 562 test-plan rows**. The gate is wired into `make ci`,
  `.pre-commit-config.yaml`, and the GitHub `quality` workflow.
- **R² — green rows must cite live tests that cite the clause.** Closed in S156: the new
  law-coverage gate hard-fails dead citations, uncited docstrings, orphan rows, ambiguous
  bare citations, and roll-up drift. Before S156, the live book carried **284 green rows**;
  **29** named rows failed the §3 citation definition, plus S156 found one additional stale
  scanner file citation and the existing `RPT-OBS-03` orphan row. After adjudication, the book
  carries **260 green rows**, the orphan row is gone, and the checker exits 0 with only
  assertion E's deliberate missing-row warning.
- **S — `make ci`'s exit code depended on where stdout goes.** Closed 2026-08-04, and **the
  original diagnosis was wrong in a way worth keeping.** The row said *"every individual recipe
  step returns 0 under `/dev/null`; only the aggregate differs"* — there is no make-level mystery:
  exactly one step differs, `uv run lint-imports`, measured at `devnull=1 file=0`. **Mechanism,
  verified not inferred:** Git-Bash resolves `/dev/null` to Windows `NUL`, a *character device*, so
  `sys.stdout.isatty()` is **True** when stdout is redirected there (measured: `/dev/null` True,
  regular file False, pipe False). `rich` therefore takes its terminal path; `NUL` offers no VT
  sequences, so it falls back to the legacy-Windows renderer, which writes through this host's
  **cp1252** stdio — and import-linter's spinner text is `":brick: Building graph..."`, i.e. 🧱
  (U+1F9F1), which cp1252 cannot encode. `UnicodeEncodeError` is raised in the spinner's teardown.
  **The direction matters and reverses the row's worry:** the crash happens *after* the contracts
  are checked and `Contracts: 4 kept, 0 broken` is printed (confirmed: 4 `KEPT` lines emitted, then
  exit 1). This turns a **green gate red — it can never turn a red gate green**, so no past green
  claim was falsified by it. Fixed with `export PYTHONUTF8 = 1` in the `Makefile`, which also makes
  local stdio match CI (UTF-8 on Linux); proven by `PYTHONUTF8=1 uv run lint-imports` returning
  **0 under both redirections**, where it previously returned 1 under `/dev/null`.
  **The row's second claim stands and is independent:** `make ci | tail` reports `tail`'s exit
  code, not `make`'s. That one is ordinary shell semantics, *can* hide a real failure, and cannot
  be fixed in the Makefile — it is now a written rule in `CLAUDE.md`. Note a pipe sets
  `isatty=False`, so piping *suppressed* this bug while introducing the exit-masking one, which is
  most likely why the two were conflated in one row.
- **T — unit tests no longer transact with production Service Bus.** Closed in S159
  (`0.86.03`): the open question resolved to the worse answer, not the cleanup answer. The
  deliberator peer tests had published 40 production dead-letter messages with the fixture
  `run_id="turn-1"`; those messages were purged with operator approval so dead: 0 became the
  verification instrument. The fix makes the peer tests inject offline settings by construction,
  adds an unconditional pytest send-boundary guard on `AzureServiceBusBus._azure_send`, overrides
  `AzureServiceBusSettings` direct `.env` file loading with `env_file=None` while preserving
  process-env production resolution, and skips live Service Bus pytest entries by default. Evidence:
  [S159 handback](sprints/sprint-159-tests-never-transact.md) and [DL-89](design-log.md).
  **Corrected and completed 2026-08-05 (`chore-s159-residue`, `0.86.04`) — the row and S159 both
  understated the blast radius, and the fix was quieter than it looked.** (1) The suite was also
  performing **topic DDL on the production namespace**, not only publishing:
  `test_bus_azure_receiver_integration.py` gated on a `_CONNECTION` that reads *both* env-var names,
  `.env` supplies the un-prefixed one, `integration` is not deselected, and the credential has Manage
  rights — so it created, used and deleted two topics per local `make ci`. (2) The S159 guard derived
  from `RuntimeError` and `fault_boundary` catches bare `Exception`, so a publish inside
  `reraise=False` was silently converted into a `Fault` and the test still passed — measured, then
  fixed by deriving from `BaseException` and pinned by a planted-violation test. (3) Both live
  Service Bus entry points are now **deleted rather than skipped**; restoring either requires a
  dedicated non-production namespace. Full reasoning, including the deliberately out-of-scope
  `AgentSettings` base-class boundary: [DL-90](design-log.md).
- **M — a pushed branch can produce zero workflow runs.** Closed 2026-08-05 (`chore-run-exists-assertion`, `0.86.05`) by making the check a command instead of a glance: `make gate-ran` resolves the full SHA itself, **refuses an abbreviated one**, and fails unless `CI` and `Security Findings` both exist for that commit and both concluded `success`. `CLAUDE.md`'s merge sequence now names it, and two `gate_selftest` cases plus two invariants keep it honest (self-test 15/15 → **19/19**). **The 2026-07-23 cause now has a strong candidate, but it is not proven and the row should not be read as if it were.** Measured 2026-08-05: the GitHub API's `head_sha` filter matches only the full 40-character SHA — `c145e5e` returns `total_count: 0` while `c145e5e79a3a3aa7435897d5ec80800167884892` returns `2`, both runs green, with no error or warning on the short form. That reproduces the exact symptom without any platform fault, and the row's own note that it was *“confirmed twice a minute apart”* fits a deterministic query bug better than a transient miss. What cannot be recovered is which SHA form that query actually used, so *“the query was wrong”* stays a candidate rather than a finding. The fix is correct either way: it asserts on the full SHA and fails loudly when no run exists. Reasoning: [DL-91](design-log.md).
- **Q — the deploy script's success detection could not be trusted in either direction.** Closed 2026-08-05 (`chore-deploy-state-from-show`). **The row named the right place and the wrong reason.** It blamed a value parsed *out of a merged stream*; measured, a non-`WARNING:` stderr line is harmless on its own — the defect is **ordering**. `Invoke-Az` returned *the last non-empty non-`WARNING:` line*, so any stderr arriving **after** the tsv value became the “state”, whatever it said. All four `Invoke-Az` call sites parse `provisioningState`, which is why every target flipped to `[XX]` at once. Fixed by sending stderr to a file instead of merging (so the value is stdout, no filtering heuristic at all, and stderr is still printed on non-zero exit — DL-85 must not come back), and by reading state from a **separate `az containerapp show`** (`Get-AppState`/`Get-JobState`) rather than from the call that changed the resource. Proven against a stub `az.cmd`: old → the deprecation text (`Succeeded? False`), new → `Succeeded`; failure stub → `$null` with stderr surfaced. ⚠️ **End-to-end confirmation is owed at the next deploy** — the exact production stderr line was not captured because that needs a real deploy (operator-gated); expect `[OK]` on all 17 targets, and any `[XX]` should now carry its stderr. Reasoning and the deliberately-unchanged fail-closed raw-`az` sites: [DL-92](design-log.md).

## Open — with unblock triggers

**Open rows are now N, O and P.** Opened 2026-07-23 — **gates or agent authority**, found while shipping ADR-0016. **L closed 2026-07-27** (see Done); **M closed 2026-08-05**, leaving N. **O and P added 2026-08-01**, **Q added 2026-08-02** — both found while reconciling the law book in S152, both pre-existing and deliberately outside that sprint's scope. **R and R² closed in S156**; O remains open because assertion E is deliberately warn-only until S157 writes the missing rows. **T added 2026-08-04 and closed in S159.** **S added 2026-08-03 and closed 2026-08-04** — its stated diagnosis turned out to be wrong and the correction is recorded in Done, because the wrong half ("only the aggregate differs") is what made it look unfixable.

| ID | Item | Why | Unblock trigger |
| --- | --- | --- | --- |
| N | **Delegated coding agents run with full local authority by default.** `~/.codex/config.toml` carries `approval_policy = "never"` and `sandbox_mode = "danger-full-access"`. Every delegated run so far overrode this with an explicit `--sandbox workspace-write`, confining writes to the worktree, `/tmp` and `~/.codex/memories` — but the *default* for any run launched without that flag is unrestricted disk access with no approval prompt, including `.env`, `infra/`, and `main`. | The repo's whole secrets discipline (CLAUDE.md: credentials never exist as files in the worktree) assumes no process is casually rewriting the tree. An agent with `danger-full-access` and no approvals is outside that assumption, and the protection currently lives in the operator remembering a CLI flag. | Before delegation becomes routine/unattended — i.e. the first time a coding agent is run without a human watching the diff. Decide then: change the config default, or wrap delegation in a script that always passes the sandbox flag. |
| O | **The law test-plans carry fewer rows than their laws have clauses.** S156 made this checkable as assertion E in `scripts/check_law_coverage.py`, but deliberately left it **warn-only**: the corrected book has **101 law clauses with no test-plan row** (provider 22, master 21, execution 13, scanner 13, analyst 12, portfolio_manager 12, monitor 7, reporter 1). | A clause with no row cannot be ⬜ *or* 🟩 — it is simply missing, so the gap never surfaces as an unproven clause in any count. That is the DL-57 shape at document level: *didn't look* rendering identically to *looked and found nothing*. The greens/total ratio reads as honest while under-reporting how much of each constitution has never been considered for testing at all. | **S157**: write the missing test-plan rows, decide the summary-generation question, then flip assertion E from warn-only to hard fail. Until then, `make ci` must print the 101-row warning and still exit 0 when A/B/C/D are clean. |
| P | **`broker_status="partial"` can never upgrade to `filled`.** `_broker_status_props` writes `broker_status` only `if "broker_status" not in node.props` — write-once, and correct under the append-only spine — so a fill that reaches the broker as `partial` keeps that value permanently, even after the broker fills it. S154's selector treats `partial` as non-terminal **by design**, so such a fill re-refreshes every run: the same unbounded `BrokerOrderStatus` growth S154 closed, surviving in one narrow case. | The one live loose end of DRIFT-029, and **no law edit can close it** — S152 declared the boundary (`EXEC-STA-05`) and the boundary is right; the defect is in the *read model*. All three tempting fixes are wrong: terminalizing `partial` freezes a genuinely in-flight order's evidence; rewriting `broker_status` is the exact two-vocabularies-in-one-property collision that stalled the fleet on 2026-07-30 (DL-79); leaving it is the growth. The end-state is deriving current status from the latest `BrokerOrderStatus` fact instead of a write-once `Fill` property — a design change deserving its own sprint and probably an ADR amendment. | **Zero production fills are in this state today**, which is the only reason it is not urgent. Trigger: **the first partial fill to appear in production** (watch for a `Fill` with `broker_status="partial"`), or any sprint touching the refresh path in `agents/execution/reconciliation_store.py`. Also recorded in the DRIFT-029 row and in S154's *road not taken*. |

## Branch protection recommendations (with CodeQL)

When GHAS is enabled and `jobs.security.env.GHAS_ENABLED` is `"true"`:

1. Require these checks on `main`: `quality`, `test`, `security`.
2. Keep `security` required because it now contains `pip-audit`, `detect-secrets`, and conditional CodeQL analysis.
3. Keep Dependabot non-major auto-merge enabled; majors remain manual.
4. Keep "dismiss stale approvals" enabled to force re-review after dependency drift.

## How this list stays alive

1. **Trigger-coupling** (primary): landed items move to **Done** with code/workflow evidence; registry
   or supply-chain design drift is surfaced in the design log before any ADR amendment.
2. **STATE.md pointer**: this file is linked from `docs/STATE.md` Pointers, read every session.
3. **Optional**: mirror D–G as GitHub issues with a `hardening` label if/when issue-tracking is
   adopted (the repo has a GitHub remote). Not required while this doc is the single source.
