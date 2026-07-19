<!-- Agent: planning | Role: sprint handover -->
# Sprint 129 — Fixpack: quant-evidence persistence, egress reduction, CI hardening (D+E)

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-129-fixpack`
**Status:** ready for handover (packaged 2026-07-19)
**Effort:** M

---

## Why this sprint

Operator directive (2026-07-19): **fixes take priority over new capability.** The drift
register has zero OPEN rows after S128, so this sprint drains the remaining known fix debt:
the last open S127-fixpack row (quant evidence for deliberation — row 3, the only non-FIXED
row), the DRIFT-023 follow-up (egress reduction — the Neon plan is paid now, so every saved
read is money, not quota), and the two hardening-backlog items whose unblock triggers have
already fired (D: dependency-review on PRs; E: container image scanning — unblocked because
`build-images.yml` has been building and pushing all 14 images on merge since the fleet arc).
The hardening backlog itself has status drift to reconcile while we're in there.

## What already exists (read before estimating)

- **Row 3 diagnosis** (S125 return notes, `docs/sprints/sprint-125-operator-chat.md`): all
  three deliberation roles receive the same rendered context, but the analyst
  `ScoreBreakdown.metrics` payload is **not persisted in full** into `Recommendation` /
  rendered by `veto_context` — full quant-signal availability to the debate is unproven.
- **Deliberation context path**: `orchestration/veto.py` + `kernel/deliberation_prompts.py`;
  the Recommendation node is written by the analyst stage. The debate's value rests on the
  transcript's *why* (DL-39 direction) — starving it of quant signal undermines the asset.
- **Dashboard read path**: `surfaces/dashboard/` projections hit Postgres per request;
  `PostgresGraphStore._run` retries once on a fresh connection (0.68.02 chore). There is no
  read cache; the local dashboard plus fleet polling were the likely egress drivers in
  DRIFT-023's quota exhaustion (register row has the list).
- **CI security lane**: CodeQL is ACTIVE and enforcing (PR #27, 2026-07-04; error-level
  findings fail PRs). `build-images.yml` builds + pushes 14 GHCR images on merge and on
  manual dispatch (`image_tag`). `pip-audit` covers Python deps only — nothing scans the
  built image OS layers today.
- **Hardening backlog** (`docs/hardening-backlog.md`): rows C (CodeQL — trigger fired,
  status stale), D (dependency-review-action — "can land any time"), E (Trivy/Grype —
  trigger "when F lands" has fired), F (deploy pipeline — exists as `build-images.yml` +
  the DL-46 DeployRecord flow; GHCR not DockerHub, which ADR-0007 should be checked
  against), G (mutmut — periodic, NOT in this sprint).

## Decisions taken at packaging (LAW-06)

1. **Row 3 stays a fixpack part, not its own sprint.** A typed bounded payload
   (`ScoreBreakdown.metrics` → Recommendation node) + `veto_context` rendering + a
   three-role capture test is M-effort against known files. *Ruled out:* redesigning the
   deliberation context schema (DL-39 will do that with evidence; this fix just stops the
   signal loss).
2. **Egress reduction = short-TTL read cache + leaner polling, both tunable.** A per-process
   TTL cache on dashboard projection reads (tunable seconds, `0` disables) and a widened
   poll interval on the self-heal refetch. *Ruled out:* a caching proxy/Redis (real infra
   for a single-operator dashboard — revisit at multi-agent scale); moving the dashboard
   off live reads (glance-first requires freshness — cache TTL must stay seconds, not
   minutes).
3. **Hardening D + E land in CI, bounded.** `dependency-review-action` on PRs (fails on
   vulnerable/denied deps at review time); Trivy scan of the built images in
   `build-images.yml` gated on HIGH/CRITICAL with the same accepted-findings discipline as
   the security lane. *Ruled out:* scanning all 14 images per merge if wall-clock cost is
   material — scanning one representative image per base-layer set is acceptable; record
   which in the closeout.
4. **Backlog reconciliation is in-scope** (document-management care): move C to Done with
   evidence (enforcing since 2026-07-04), record F's real-world shape (`build-images.yml` +
   DeployRecord; note the ADR-0007 DockerHub→GHCR drift and surface the ADR rather than
   silently amending), re-trigger E→Done when the Trivy step lands. G stays open with its
   periodic trigger.

## Kickoff (paste this)

> Execute **Sprint 129 — fixpack** exactly as specified in this file
> (`docs/sprints/sprint-129-fixpack.md`). Read first: S127 fixpack backlog row 3 and the
> S125 return notes (the debt's evidence); `orchestration/veto.py`,
> `kernel/deliberation_prompts.py`, the analyst Recommendation write path;
> `surfaces/dashboard/` projections + `__main__` serve loop; `docs/hardening-backlog.md`;
> `.github/workflows/build-images.yml` + the CI security lane; design-log **DL-48** (the
> process contract this kickoff enforces).
>
> **Contract (DL-48 — enforced):**
>
> - **Start:** `git pull` on `main` — `pyproject.toml` must read **0.71.01** (stop and
>   report if not). Branch `sprint-129-fixpack`. Bump **PATCH → 0.71.02** (fixes only) +
>   `uv lock`.
> - **Drift rule:** before handback, `git fetch`; if `origin/main` moved, merge it into the
>   branch, re-run the full gate on the merge result, record what moved in the Return notes.
> - **Secrets rule** (CLAUDE.md): no credential ever becomes a file in the repo tree.
> - **Handback rule:** the last two things you do are the Closeout block and the Return
>   notes; an incomplete handback is bounced, not repaired.
> - Hard gate: `make ci` green with the **exit code captured**, 100 % coverage, ≤200-line
>   modules, headers, `tunable(..., why=...)` for every threshold.
>
> **Work items:**
>
> - **A (row 3 — quant evidence persisted):** persist the full `ScoreBreakdown.metrics`
>   payload as a typed bounded structure on the Recommendation node; render it in
>   `veto_context` for all three roles; three-role capture test proving each role's
>   rendered context contains the quant signals; update the S127 backlog row to FIXED.
> - **B (egress reduction):** TTL read cache on dashboard projection reads (tunable
>   seconds, `0` disables, default a few seconds) + widen the rail self-heal refetch
>   interval (tunable); unit truth-table for cache hit/expiry/disable; no staleness
>   regression on the verdict hero (cached ≤ TTL is acceptable by decision 2).
> - **C (hardening D):** `dependency-review-action` on PRs, pinned by SHA per repo
>   convention, failing on vulnerable/denied dependencies.
> - **D (hardening E):** Trivy image scan step in `build-images.yml` gated HIGH/CRITICAL;
>   document the accepted-findings path; scope per decision 3.
> - **E (backlog reconciliation):** hardening-backlog rows C/E/F statuses corrected with
>   evidence links; ADR-0007 surfaced (not amended) re: DockerHub→GHCR — add a design-log
>   note if the ADR needs a formal amendment cycle.
> - **Functionality check (LAW-02), live:** (1) a deliberation run (local, opt-in flags)
>   whose transcript demonstrably cites at least one quant metric that was previously
>   absent; (2) dashboard served locally against live Neon — show cache hits reducing
>   Postgres round-trips (count queries before/after over a fixed interaction script) with
>   the verdict still correct; (3) a PR exercising dependency-review + a `build-images`
>   run showing the Trivy step executing. Record in `docs/laws/functionality-checks.md` +
>   evidence under `docs/reports/sprint-129-fixpack/`; tear down disposable artifacts and
>   show the sweep count.
> - **Wrap up:** README/INDEX rows; Closeout + Return notes; push, hand back.
>   **Do not merge.**

## Guardrails

- No new runtime capability: this is a PATCH fixpack — no new agents, endpoints, or graph
  node types (the Recommendation payload is a field on an existing node).
- Cache TTL stays seconds-scale; the RED/GREEN verdict must never render from a stale
  cache older than the TTL (DL-47 glance-first).
- CI additions must not lengthen the PR-blocking path materially; Trivy runs in
  `build-images.yml` (merge/dispatch), not the PR lane, unless it proves fast.
- Do not touch the S128 feed-resilience paths, the deliberation prompts themselves
  (champion prompts are compiled artifacts — ADR-0010), or safety/capital caps.
- mutmut (backlog G) is explicitly out of scope.

## Definition of done

1. All three deliberation roles demonstrably receive the full quant-signal payload,
   captured by test and shown live in a transcript.
2. Dashboard Postgres round-trips measurably drop under the TTL cache with correct
   rendering; both tunables documented with `why=`.
3. PRs fail on vulnerable/denied new dependencies; image builds run a HIGH/CRITICAL
   Trivy gate.
4. Hardening backlog C/D/E/F rows read true with evidence; S127 backlog row 3 reads FIXED.
5. `make ci` green at 100 % (exit code captured); closeout + return notes filled.

## Closeout (coding agent fills; planning agent verifies before merge)

```text
CLOSEOUT — Sprint 129
Branch / merge commit:   sprint-129-fixpack / not merged by instruction
make ci:                 MAKE_CI_EXIT_CODE=0; 1597 passed, 5 skipped; coverage 100.00%
Functionality check:     PASS. Local opt-in deliberation cited newly persisted quant metrics
                          (`composite_score` among them) in the debate transcript; live Neon
                          dashboard cache proof dropped Postgres calls 18 -> 0 inside the 5 s TTL
                          while the verdict stayed GREEN (`1 order, 1 candidate`); PR #50 security
                          job ran dependency-review successfully; build-images run
                          29679397636 executed the Trivy HIGH/CRITICAL gate on analyst/master/
                          forecaster and failed on real existing findings, proving enforcement.
Version:                 0.71.01 → 0.71.02 (PATCH); uv.lock refreshed
Backlog rows:            S127 row 3 → FIXED (0.71.02); hardening C/D/E/F → Done with evidence
                          links and DL-50 surfacing ADR-0007 DockerHub→GHCR drift.
Drift rule:              `git fetch` before handback found origin/main unchanged at
                          8b3fcd229b1df539653888cb8eb596cc4f6ac0c5; no merge needed; final
                          `make ci` ran on the branch result.
Deviations from spec:    build-images manual proof is red because the new Trivy gate found
                          22 HIGH/CRITICAL findings per representative image. No CVE was accepted
                          or silenced in S129; remediation/accepted-findings review is follow-up.
```

## Return notes (coding agent appends at handback — mandatory)

Append below, at the very end of this file, everything the next session needs that the
closeout numbers don't carry: surprises found in the code, decisions taken in-flight and
why, drift observed elsewhere, follow-ups you would queue. A handback is not accepted while
this section is empty or the closeout placeholder is unfilled (LAW-02 + DL-48).

<!-- return notes go below this line -->

2026-07-19 — Coding-agent return notes

- First-contact surprise: adding the Trivy gate immediately exposed existing Debian base-image
  HIGH/CRITICAL CVEs on the representative images (`analyst`, `master`, `forecaster`). I left
  `.trivyignore` with documentation-only guidance and no accepted CVE entries, so the next move is
  either a base-image/dependency remediation sprint or a formal accepted-findings entry with owner
  and expiry.
- Dashboard cache scope is projection-read only: `GET` read-model routes use `CachingGraphStore`,
  while `/api/chat` still uses the original graph store so audited writes are never hidden behind a
  TTL layer.
- To keep the hard module-size block green, `surfaces/dashboard/static_response.py` now owns static
  asset/index serving and `tests/veto_context_provider_fixtures.py` holds the shared provider
  fixture.
- ADR-0007 was surfaced, not amended. DL-50 records that the real shipped registry/deploy truth is
  GHCR plus `DeployRecord`, while ADR-0007 still says DockerHub; queue a formal ADR amendment if the
  registry decision needs to be made canonical.
- Live checks stayed credential-safe: no DSN/API key/connection string was printed or written into
  the repo tree. The Neon dashboard check was read-only; the local server was stopped; the
  `s129-livecheck` sweep deleted 0 nodes and 0 edges. PR #50 and the GitHub workflow runs remain as
  audit evidence; the branch-tagged GHCR images from `image_tag=s129-fixpack` are CI artifacts.
