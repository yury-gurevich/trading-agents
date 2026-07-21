<!-- Agent: planning | Role: chore handover -->
# Chore — WSL2 development environment (keep PowerShell, don't rewrite)

**Phase:** Etalon-first continuous improvement (DL-19) — dev-environment tooling, not a feature
**Branch:** `chore-wsl2-dev-env`
**Status:** ready for handover (packaged 2026-07-21)
**Effort:** M (repo part S; operator/environment part M)
**Sequence:** execute **only when the sprint queue is empty** — after S134 (0.71.06) and
S133 (0.71.07) have merged. The line-ending renormalisation touches ~every text file, so it
must not overlap an in-flight sprint branch (a giant CRLF↔LF merge conflict otherwise).

---

## Why this chore

Move the **development loop** onto WSL2/Linux — the platform the code already ships and tests
on — chiefly to make `pytest`/`mutmut` fast on a native ext4 filesystem and to get exact
CI/prod parity, without the CRLF and Docker-Desktop friction of NTFS.

The trigger is that mutation testing is now a recurring exercise (S132 backlog row G, S134
row K). `mutmut` copies the whole tree into `mutants/` (~10 MB) and re-runs the suite **per
mutant** — brutally I/O-heavy on NTFS, much faster on ext4. That is the concrete payoff.

## What already exists (read before estimating)

- **The code is already Linux-proven — this is what makes the move low-risk:**
  - **Production runs on Linux.** All 14 images are `dhi.io/python:3.13` (Linux) on Azure
    Container Apps (S130). The Python code has to be Linux-clean; it runs in Linux containers
    every night.
  - **CI runs on Linux.** GitHub Actions runs the full gate on `ubuntu-latest` every push, so
    `ruff / format / mypy / import-linter / module-size / module-header / pytest @ 100 % /
    pip-audit / detect-secrets` **already pass on Linux, continuously.** There is no
    "will the port work" risk — it is proven twice daily.
- **The Makefile is already POSIX.** Every `make ci` step is `uv run …`. The **only**
  Windows coupling is one line — `make codeql-ast` shells out to
  `powershell -ExecutionPolicy Bypass -File scripts/run_codeql_ast.ps1`. `make clean` uses
  `rm -rf` (already POSIX). `make ci` is invoked today through Git Bash.
- **14 `.ps1` files, in three groups** (`git ls-files '*.ps1'`):
  - `infra/*.ps1` (7): `deploy-agents.ps1`, `grant-key-vault-seeder.ps1`, `setup-azure.ps1`,
    `setup-container-apps.ps1`, `setup-github-ci.ps1`, `status.ps1`, `ta.ps1` — Azure `az`
    CLI wrappers. `infra/deploy.sh` already exists as a partial bash deploy.
  - `codeql/scripts/*.ps1` (6): CodeQL local-suite runners.
  - `scripts/test-api-keys.ps1` (1): key smoke-tester.
- **No `.gitattributes`.** Repo text is CRLF (see the `ide-markdown-autoformat` note); with no
  normalisation, the first touch under WSL2 makes git see whole-file CRLF↔LF diffs.
- **Existing WSL2 Ubuntu may be stale/bloated.** An older note recorded the Ubuntu vhdx grown
  to ~128 GB with prune+compact deferred. Two constraints that once blocked WSL2 are now
  **dead** and should be cleared from memory when this lands: the "WSL2 off during Aura trial"
  hold (Aura trial ended ~2026-06-29) and the Neo4j runtime (deleted S118, Postgres/Neon is
  the spine). Nothing blocks turning WSL2 on.
- **The tree is shared with an external coding agent (Codex).** Any environment move has to
  decide where Codex operates, or you get a split-brain (Windows checkout + WSL2 checkout
  drifting).

## Decisions taken at packaging (LAW-06)

1. **Option chosen: WSL2 dev environment, PowerShell kept (run `.ps1` under `pwsh` on Linux).**
   PowerShell 7 (`pwsh`), the `az` CLI, and the CodeQL CLI all run natively on Linux, so the
   14 `.ps1` files run **as-is** — no rewrite.
   **Validated 2026-07-21 on the operator's Ubuntu (pwsh 7.6.3), not assumed:** all 14 parse
   clean; `pwsh` normalises `\`→`/` in **both** `Join-Path` and bare filesystem-cmdlet paths
   (`Join-Path $root "..\.env"` → `.../../.env`; `Set-Content -Path "dir\out.txt"` →
   `dir/out.txt`), so the **infra** scripts run unchanged — including the nightly-critical
   `deploy-agents.ps1` (`..\.env`, `..\orchestration\packs`) and `setup-azure.ps1`'s
   `Set-Content`. **Two codeql-only caveats remain** (matter only if CodeQL is run locally
   *on Linux* — the lowest-value scripts): `run_codeql_ast.ps1:106` uses a `-like "*\...\*"`
   **string** wildcard (string compare does *not* normalise, so it won't match Linux `/`-paths),
   and `.tools\codeql\codeql.exe` needs the `.exe` dropped. Both are small in-place fixes, still
   not a rewrite. *Ruled out:*
   - *Stay on Windows (status quo)* — forgoes the native-ext4 `mutmut`/`pytest` speed-up and
     keeps CRLF/Docker-Desktop friction; the reason the chore exists.
   - *Move to WSL2 **and** rewrite all `.ps1` → `.sh`* — 14 scripts of translation, and the
     `infra/` ones (`deploy-agents.ps1` especially: per-target secret delivery, object/JSON
     handling) port 1:1 in *logic* but need real *syntax* rewrites. High cost, no benefit while
     `pwsh` runs on Linux. Revisit later **only** if a zero-PowerShell repo is an explicit goal;
     it is not coupled to this chore.
2. **Do not tie the move to a PowerShell→bash rewrite** (corollary of #1). The environment move
   and the language choice are independent decisions; conflating them is what makes a WSL2 move
   look expensive when it is not.
3. **Line endings normalised to LF via `.gitattributes`**, one-shot `git add --renormalize .`
   commit, executed when no sprint branch is in flight. *Ruled out:* leaving CRLF and living
   with per-file churn under WSL2 (noisy diffs forever, worst on the shared Codex tree).
   `.ps1` kept CRLF (`*.ps1 text eol=crlf`) so Windows-side execution stays clean.
4. **Clone inside the WSL2 filesystem (`~/…`), never under `/mnt/c/…`.** Files on `/mnt/c`
   are slow for git/uv/pytest and silently erase the perf win. *Ruled out:* editing the
   existing NTFS checkout through `/mnt/c`.
5. **Scope split into a repo part (a coding agent can do) and an environment part (operator
   only).** A coding agent cannot install WSL2 on the operator's machine or recreate secrets;
   those are an operator runbook, kept in this doc, executed by the operator.

## Kickoff (paste this) — REPO PART (coding agent)

> Execute the **repo part** of `chore-wsl2-dev-env` exactly as specified in this file
> (`docs/sprints/chore-wsl2-dev-env.md`). This part makes the repo WSL2-clean; it does **not**
> install WSL2 (that is the operator runbook below). Read first: this file's
> "What already exists" + "Decisions"; the `Makefile`; `git ls-files '*.ps1'`; design-log
> **DL-48**.
>
> **Contract (DL-48 — enforced):**
>
> - **Start:** `git pull` on `main`; record the version it reads (expected **0.71.07** if S133
>   has merged — stop and report if S134/S133 have **not** merged, this chore sequences after
>   both). Branch `chore-wsl2-dev-env`. Bump **PATCH** to the next value + `uv lock`.
> - **Drift / Secrets / Handback rules:** as S131/S133 (fetch+merge+re-gate before handback;
>   no secret in the tree or in output; closeout + return notes last).
> - **Hard gate:** `make ci` green (exit code captured), 100 % coverage, ≤200-line modules,
>   headers. This chore adds no runtime code, so coverage must hold at 100 % with no new
>   `# pragma: no cover`.
>
> **Work items:**
>
> - **A — `.gitattributes`:** add it with `* text=auto eol=lf`, `*.ps1 text eol=crlf`,
>   `*.sh text eol=lf`, and `-text` (binary) for any images/artefacts. Then run
>   `git add --renormalize .` as its **own commit** with a message explaining the one-shot
>   normalisation. Verify no `.py`/`.md`/`.yml` content changed except EOL (`git diff -w` on the
>   renormalise commit is empty).
> - **B — Makefile portability:** change the single `make codeql-ast` recipe from `powershell`
>   to `pwsh` (PowerShell 7, cross-platform; it is also what this repo's tooling already uses).
>   If a Windows-5.1-only fallback is wanted, guard it; otherwise `pwsh` is the correct single
>   choice. Confirm `make ci` is unaffected (it invokes no `.ps1`).
> - **C — setup guide:** write `docs/setup-wsl2.md` (add an INDEX row) — the reproducible
>   operator runbook (mirror the "OPERATOR RUNBOOK" section below into a real doc): distro
>   prune/create, clone into `~`, install `uv`/`make`/Docker(WSL2 integration)/`pwsh`/`az`,
>   recreate `.env` + `infra/*.local.json`, and the smoke tests. Cross-link from
>   `docs/INDEX.md`.
> - **D — docs:** add the chore to the sprints INDEX "Queued / parked" table → move to done
>   with evidence on completion; design-log entry recording the chosen option (WSL2 + keep
>   `pwsh`) and the two roads not taken (stay-Windows, full rewrite). Clear the two dead
>   memory constraints (Aura hold, Neo4j) if any doc still references them as live.
>
> **Functionality check (LAW-02):** run `make ci` on **both** platforms if available — at
> minimum prove it green post-normalisation on the current host — and confirm `git status` is
> clean after a fresh checkout (no phantom CRLF churn). The *native-Linux* smoke test
> (`make ci` + a scoped `mutmut` run inside WSL2, timing captured vs the NTFS baseline) is the
> operator part; record whichever was run under `docs/reports/chore-wsl2-dev-env/`.
>
> **Wrap up:** README/INDEX rows; Closeout + Return notes; push, hand back. **Do not merge.**

## OPERATOR RUNBOOK — ENVIRONMENT PART (only the operator can do)

Not executable by a coding agent (installs software on the operator's machine, handles
secrets). Promote this into `docs/setup-wsl2.md` (work item C) so it is reproducible.

1. **Distro:** prune+compact the bloated Ubuntu vhdx **or** `wsl --install -d Ubuntu` fresh.
   Confirm WSL2 (`wsl -l -v` → VERSION 2).
2. **Toolchain (inside WSL2):** install `uv` (astral installer), `make`, Docker (Docker Desktop
   WSL2 integration *or* native engine), and — for the infra scripts — `pwsh` (PowerShell 7)
   plus the `az` CLI (`pwsh` already present on the operator's Ubuntu, 2026-07-21). `az login` once.
3. **Clone into the Linux home:** `git clone <origin> ~/trading-agents` — **not** under
   `/mnt/c`. `uv sync`.
4. **Secrets, never through the tree:** recreate `.env` and `infra/*.local.json` inside
   `~/trading-agents` from chat/`az keyvault`/the vault, exactly as on Windows (both gitignored;
   detect-secrets is the last line, not the process).
5. **Smoke tests:** `make ci` green natively; a scoped `mutmut` run (S132 decision-engine scope)
   green, with wall-clock captured against the NTFS baseline to quantify the win.
6. **Codex decision (do this before switching daily driver):** either move Codex into WSL2 too
   (single source of truth) or accept a documented split. Do **not** run both hosts against the
   same branch — that reintroduces the shared-tree collision hazard.
7. **Infra flips unchanged:** any `az`/Service Bus/Postgres flip still happens **outside the
   22:25–00:30 UTC KEDA window**; WSL2 changes the shell, not the run-window discipline.

## Guardrails

- **No `.ps1` → `.sh` rewrite** in this chore (decision 1). `pwsh` runs them on Linux.
- **No runtime code change** — tooling/docs/line-endings only; coverage stays 100 % with no new
  `# pragma: no cover`.
- **No secret in the tree or in command output**, on either platform.
- **Timing:** the renormalisation commit only when the sprint queue is empty (no in-flight
  branch to conflict with). Confirm `git branch -a` shows no unmerged sprint before starting.
- **Do not delete the Windows checkout** until the WSL2 checkout has passed `make ci` and the
  Codex decision (runbook #6) is made.

## Definition of done

1. `.gitattributes` present; `git add --renormalize .` committed as a clean EOL-only change
   (`git diff -w` empty on that commit); a fresh clone shows no phantom line-ending churn.
2. `make codeql-ast` uses `pwsh`; `make ci` green on the current host (exit code captured,
   100 % coverage, no new pragmas).
3. `docs/setup-wsl2.md` exists (INDEX row) as the reproducible operator runbook; design-log
   entry records the chosen option + roads not taken; dead constraints (Aura/Neo4j) cleared
   from any doc that still calls them live.
4. Operator part (may trail the merge, recorded when done): WSL2 `make ci` + scoped `mutmut`
   green with timing vs NTFS; Codex home decided.
5. Closeout + return notes filled; no secret in the tree.

## Closeout (coding agent fills; planning agent verifies before merge)

```text
CLOSEOUT — chore-wsl2-dev-env (repo part)
Branch / merge commit:   <branch> / <merge sha or "not merged by instruction">
make ci:                 MAKE_CI_EXIT_CODE=<n>; <passed/skipped>; coverage <pct>
.gitattributes:          <added>; renormalise commit <sha>; git diff -w empty? <y/n>
Makefile:                codeql-ast powershell -> pwsh <done/na>
setup-wsl2.md:           <created + INDEX row>
Version:                 <prev> -> <next> (PATCH); uv.lock refreshed
Drift rule:              <origin/main moved? merged? re-gated?>
Deviations from spec:    <none, or the honest list>
```

## Return notes (coding agent appends at handback — mandatory)

<!-- return notes go below this line -->
