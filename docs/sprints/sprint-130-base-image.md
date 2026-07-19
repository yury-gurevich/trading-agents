<!-- Agent: planning | Role: sprint handover -->
# Sprint 130 — Chore: drain the Trivy red gate (ignore-unfixed) + DHI base-image migration

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-130-base-image`
**Status:** ready for handover (packaged 2026-07-19)
**Effort:** S/M

---

## Why this sprint

Backlog **row H**: the S129 Trivy gate immediately found **22 HIGH/CRITICAL Debian
base-image CVEs** per representative image on `python:3.13-slim`, so every `build-images`
run on main is red (images still push — the scan runs post-push). A permanently red gate is
alarm fatigue that erodes the gate's meaning; silently accepting 22 CVEs erodes it worse.
Research **R005** (`docs/research/base-image/INDEX.md`, sources inside) picked the fix:
fail only on *actionable* findings now, then move the fleet onto the industry's current
free near-zero-CVE base — **Docker Hardened Images** (`dhi.io/python:3.13`, Apache 2.0,
free since Dec 2025, Debian/glibc variants — no Alpine/musl wheel problem).

## What already exists (read before estimating)

- **All 14 Dockerfiles are near-identical single-stage builds** (see
  `agents/provider/Dockerfile`): `FROM python:3.13-slim` → `pip install uv==0.4.29` →
  `uv sync --frozen --extra runtime --no-dev` → copy code → `CMD ["uv", "run", ...]`.
  One template change repeats 14×; the dispatcher's lives in `orchestration/Dockerfile`.
- **Trivy step** (S129): `.github/workflows/build-images.yml`, runs after build-and-push on
  representative images `analyst`/`master`/`forecaster`, `exit-code: 1`, HIGH/CRITICAL,
  `trivyignores: .trivyignore` (empty by policy — accepted findings need owner + expiry).
- **Deploys are immutable-tag** (DL-46): images push to GHCR, fleet retags via
  `/deploy-fleet`, `DeployRecord` is the currency evidence. Nothing in this sprint touches
  the running fleet — `:s128` stays deployed until the operator retags.
- **R005** records the ruled-out alternatives (Alpine/musl, Chainguard free tier's
  unpinnable tags, classic distroless) — do not re-litigate them.

## Decisions taken at packaging (LAW-06)

1. **Part A ships even if Part B stalls.** `ignore-unfixed: true` is the industry-standard
   posture (fail only on findings with an available fix); it likely turns the gate green
   today at zero risk change. *Ruled out:* waiting to fix both at once (the red gate is
   live noise on every merge), and severity-downgrading or disabling the gate.
2. **DHI Debian/glibc variant, pinned tag.** `dhi.io/python:3.13` runtime + its `-dev`
   build variant in a **two-stage build**: dev stage runs uv sync into a venv; runtime
   stage copies `/app` (+venv) and runs `python -m …` directly — the minimal runtime image
   has no shell/pip, and must not need one. *Ruled out:* Chainguard free (`latest`-only
   tags break immutable-tag deploys), Alpine (musl), staying on `python:3.13-slim`
   permanently (R005).
3. **Verify DHI pull access from CI before converting all 14.** The catalog is free with
   no stated usage restrictions, but if `dhi.io` pulls require auth/entitlement not
   available to GitHub-hosted runners, **stop and report** with one Dockerfile converted
   as evidence; fallback option (mirror the base into GHCR) is a decision for the planning
   agent, not an improvisation. *Ruled out:* baking any new credential into workflows
   without surfacing it first (secrets rule).

## Kickoff (paste this)

> Execute **Sprint 130 — base image chore** exactly as specified in this file
> (`docs/sprints/sprint-130-base-image.md`). Read first: `docs/research/base-image/INDEX.md`
> (R005 — the decision and its sources), backlog row H in `docs/hardening-backlog.md`,
> `.github/workflows/build-images.yml` (the S129 Trivy step), `agents/provider/Dockerfile`
> (the 14× template), design-log **DL-48** (the process contract this kickoff enforces).
>
> **Contract (DL-48 — enforced):**
>
> - **Start:** `git pull` on `main` — `pyproject.toml` must read **0.71.02** (stop and
>   report if not). Branch `sprint-130-base-image`. Bump **PATCH → 0.71.03** + `uv lock`.
> - **Drift rule:** before handback, `git fetch`; if `origin/main` moved, merge it into the
>   branch, re-run the full gate on the merge result, record what moved in the Return notes.
> - **Secrets rule** (CLAUDE.md): no credential ever becomes a file in the repo tree; if
>   DHI needs CI auth, stop and report (decision 3).
> - **Handback rule:** Closeout block + Return notes last; an incomplete handback is
>   bounced, not repaired.
> - Hard gate: `make ci` green with the **exit code captured**, 100 % coverage, ≤200-line
>   modules, headers.
>
> **Work items:**
>
> - **A (drain the red now):** add `ignore-unfixed: true` to the Trivy step in
>   `build-images.yml`. Keep HIGH/CRITICAL, `exit-code: 1`, empty `.trivyignore`.
> - **B (DHI migration):** convert `agents/provider/Dockerfile` first (decision 3 probe):
>   two-stage build on `dhi.io/python:3.13` (+`-dev` for the build stage), venv-carrying
>   runtime, `CMD` runs `python -m agents.provider.entrypoint` without uv/shell at
>   runtime. Prove a CI build of that one image passes Trivy near-zero, then roll the
>   template to the remaining 13 Dockerfiles. Keep OCI labels, GHCR naming, and matrix
>   structure unchanged.
> - **C (backlog + docs):** row H → Done with evidence; R005 status → ✅ Adopted with the
>   outcome; `.trivyignore` policy comment stays.
> - **Functionality check (LAW-02), live:** (1) manual `build-images.yml` run
>   (`image_tag=s130-test`) — all 14 build+push, Trivy step **green**, record the finding
>   counts before/after (22 → expected ≈0 actionable); (2) local
>   `docker run ghcr.io/...-provider:s130-test` — the entrypoint must start and fail
>   **loudly on missing config** (proves the minimal runtime carries everything the code
>   needs — glibc wheels, venv, tzdata/certs); (3) note image size before/after. Record in
>   `docs/laws/functionality-checks.md` + evidence under
>   `docs/reports/sprint-130-base-image/`; the `s130-test` GHCR tags are CI artifacts —
>   name them; no graph writes expected (state sweep 0).
> - **Wrap up:** README/INDEX rows; Closeout + Return notes; push, hand back.
>   **Do not merge.** Fleet retag stays operator-gated (`/deploy-fleet`) after merge.
>
> **Rollback:** `git revert` — the old base builds unchanged; the fleet is pinned to
> `:s128` regardless.

## Guardrails

- No agent/kernel/contract code changes — Dockerfiles, one workflow, docs only.
- `.trivyignore` stays empty; no CVE is accepted in this sprint.
- No new secret/credential anywhere; DHI auth question → stop and report (decision 3).
- The running fleet is untouched; no `az` calls, no retag, no graph writes.
- If any single image cannot run on the minimal runtime (e.g. a genuine shell/apt need),
  report it — do not bloat the runtime image to paper over it.

## Definition of done

1. `build-images.yml` on main is **green**: Trivy gates HIGH/CRITICAL actionable findings
   only, against a near-zero DHI baseline (counts recorded before/after).
2. All 14 images build two-stage on `dhi.io/python:3.13`, push to GHCR under the existing
   names, and the provider smoke-run proves the minimal runtime works.
3. Backlog row H Done; R005 Adopted; `.trivyignore` still empty.
4. `make ci` green at 100 % (exit code captured); closeout + return notes filled.

## Closeout (coding agent fills; planning agent verifies before merge)

```text
CLOSEOUT — Sprint 130
Branch / merge commit:   <branch> / <merge sha or "not merged by instruction">
make ci:                 MAKE_CI_EXIT_CODE=<n>; <passed/skipped>; coverage <pct>
Functionality check:     <build run id, Trivy counts before/after, smoke-run result,
                          image sizes before/after>
Version:                 0.71.02 → 0.71.03 (PATCH); uv.lock refreshed
Backlog row H:           <status + evidence link>
Drift rule:              <origin/main moved? merged? re-gated?>
Deviations from spec:    <none, or the honest list — incl. any DHI access finding>
```

## Return notes (coding agent appends at handback — mandatory)

Append below, at the very end of this file, everything the next session needs that the
closeout numbers don't carry: surprises found in the code, decisions taken in-flight and
why, drift observed elsewhere, follow-ups you would queue. A handback is not accepted while
this section is empty or the closeout placeholder is unfilled (LAW-02 + DL-48).

<!-- return notes go below this line -->
