<!-- Agent: planning | Role: sprint handover -->
# Sprint 126 — Operations dashboard, slice 5: resume-from-stage + the deploy-currency judgement (DL-47 / DL-46)

**Phase:** Operations dashboard (DL-47 slice 5, final; S122–S125 shipped, 0.66.00→0.69.00)
**Branch:** `sprint-126-resume-and-tripwire`
**Status:** ready for handover (packaged 2026-07-14)
**Effort:** L

---

## Why this sprint

Two DL-47 requirements remain open, plus one honesty defect the S125 handback recorded.

1. **Req 8 — "restart a run from the point of failure onwards."** Today a stalled run resumes
   naturally (graph-pull: agents poll for unconsumed artifacts), but **redoing a completed
   stage** is planning-agent surgery with no bounded primitive (`.claude/skills/resume-run`
   Case 2 explicitly defers to this sprint). Airflow's "clear task & downstream" is the model.
2. **DL-46 — the deploy gap's tripwire needs a judgement, not a display.** The 2026-07-08
   incident (fleet ran `:s103` while three merges sat built-but-undeployed; PM double-bought
   CSCO) was silent because nothing *measured* currency. S123 surfaced the raw tags; nothing
   yet says **current / behind**. DL-46's recorded leaning is option C (keep tag-pinning, add a
   loud tripwire) with option A (deploy step in CI) as a later end state — this sprint
   implements C and thereby **closes DL-46's open decision as "C now, A later" (record it)**.
3. **S125 follow-up — bus health lies when unverified.** The verdict maps an unavailable Azure
   job read to "Activation bus is unreachable" even when the graph holds active activation
   records. Unverified is not an outage (same principle as the 0.68.02 Azure verify-retry fix).

Explicitly **not** in this sprint: the S125 quant-evidence follow-up (persist the analyst
`ScoreBreakdown.metrics` payload for the deliberation roles) — deliberation domain, separately
queued; and tier-2 repair (repo-checkout sessions, rebuild buttons) — later slice.

## What already exists (read before estimating)

- **Graph-pull persistence**: every stage's artifact is a node keyed by run id; consumption is
  edges; day-keyed `RunRequest`s merge-dedupe (double-fire proven S103); broker idempotency via
  `client_order_id`.
- **The GraphStore port has no delete and props are append-only** (Postgres store forbids
  overwriting a written prop with a different value). "Clear + downstream" therefore **cannot**
  be implemented as deletion — see decision 1.
- **Operator grammar**: `IntentFamily` already contains `"resume"` (and `"run"`); S125's
  `/api/chat` carries the confirm round-trip end-to-end; `dispatch_tool` is the bounded surface
  dispatch; every command writes `CommandAudit`.
- **Deploy machinery (DL-46)**: merge to main builds images tagged `:latest` **and**
  `:<git-sha>`; the fleet is pinned to named tags (`:s121`) moved only by the bounded
  `/deploy-fleet` procedure; `/check-fleet` is the manual currency audit.
- **Dashboard**: threading WSGI app, Azure read port (apps + tags + job executions), vitals
  line already carries the raw image tags, S125 chat dock with confirm machinery.

## Decisions taken at packaging (LAW-06)

1. **Resume = supersession, never deletion.** A resume from stage N mints a **child
   `RunRequest`** (new run id derived from the original, e.g. `<run>-r2`) carrying
   `resume_from: <stage>` and a `RESUMES` edge to the original run. Stages **before** N are not
   redone: the primitive links the original's upstream artifacts into the child's lineage so
   downstream agents consume them as-is. Stages **from** N re-derive under the child run id.
   The original run's artifacts remain untouched history. *Ruled out:* deleting artifacts or
   consumption edges (the port cannot, and provenance immutability is a law); editing props to
   "mark stale" (append-only store forbids overwrite).
2. **A redone trade path places real orders, and says so.** A child run id means new
   `client_order_id`s — broker dedup will **not** suppress re-submission; that is what "redo"
   means. The confirm round-trip must render this consequence verbatim ("re-running from
   portfolio manager will submit new orders at the broker") and resume of any stage at or
   before execution is **double-gated**: the typed intent echo plus an explicit second
   confirmation naming the broker consequence. *Ruled out:* silently skipping execution on
   resumed runs (a resume that cannot trade is a different feature and would lie about itself).
3. **The primitive lives in `orchestration/`, invoked only through the operator.** Dashboard →
   `/api/chat` command (or the run view's "Resume from <stage>" affordance posting the same
   bounded command) → operator `interpret` (family `resume`) → supervisor validation →
   orchestration primitive. No new write path from surfaces to the graph. *Ruled out:* a
   dashboard endpoint that calls the primitive directly (bypasses the operator's audit + gates).
4. **Resume places graph state; the fleet picks it up at its next wake.** The primitive writes
   the child RunRequest; scale-to-zero agents consume it at the next KEDA window, or the
   operator wakes the fleet with the existing documented command
   (`az containerapp job start -n dispatcher-cron -g trading-agents`). *Ruled out for this
   slice:* the dashboard issuing Azure control-plane writes to wake the fleet — surfaces keep
   zero Azure write scope; a wake affordance is tier-2 territory.
5. **Deploy currency is judged from a graph-recorded deploy fact, not inferred.** The bounded
   `/deploy-fleet` procedure gains one step: append a **`DeployRecord`** node (tag, git sha it
   was built from, deployed_at, actor). The dashboard judgement is then two provable
   comparisons: (a) every running app/job tag equals the latest `DeployRecord.tag` — else
   **behind/mixed**; (b) the latest `DeployRecord.git_sha` equals the sha of the newest
   successful main image build (one read-only GitHub API call, token via `GITHUB_TOKEN` env) —
   else **behind**. Token absent or the read fails → **unverified**, stated as such. *Ruled
   out:* GHCR digest comparison (new registry credential + digest plumbing for the same
   answer); inferring currency from tag string shapes (unprovable).
6. **Tri-state health language everywhere this sprint touches: `current/behind/unverified` for
   deploy currency, `reachable/unreachable/unverified` for the bus.** The bus claim
   "unreachable" now requires a real failed probe/read of bus-backed evidence, not an
   unavailable Azure management read; an unavailable read renders "unverified" and never flips
   the master light by itself (warning-class, per the S124 binary-light decision). The vitals
   and verdict warnings adopt the same words. *Ruled out:* a third light color (S124 decision 1
   stands — binary light, warnings badge).

## Codex kickoff (paste this)

> Execute **Sprint 126 — resume-from-stage + deploy-currency judgement** exactly as specified
> in this file (`docs/sprints/sprint-126-resume-and-tripwire.md`). Read first: DL-47 ("why
> restart-from-stage is cheap here") and DL-46 (the deploy-gap incident + option C) in
> `docs/design-log.md`; `.claude/skills/resume-run/SKILL.md` (Case 2 is what you are building);
> `.claude/skills/deploy-fleet/SKILL.md` + `.claude/skills/check-fleet/SKILL.md` (the manual
> procedures you are automating the judgement for); `orchestration/scheduled_dispatch.py` +
> the agents' work-loop polling (the consumption semantics resume must respect);
> `contracts/operator.py` + `surfaces/mcp_tools.py`/`surfaces/operator_tools.py` (the S125
> command path you are extending); `surfaces/dashboard/projections_infra.py` +
> `projections_verdict.py` (where the judgement and tri-state land).
>
> - **Start:** from `main` (`git pull`) — `pyproject.toml` must read **0.69.00** (stop and
>   report if not). Branch `sprint-126-resume-and-tripwire`. Hard gate: `make ci` green, 100 %
>   coverage, ≤200-line modules, headers, tunables for any threshold. Bump **MINOR**
>   (→ 0.70.00) + `uv lock`.
> - **Part A — resume primitive** per decisions 1, 2, 4 in `orchestration/`: child RunRequest
>   with `resume_from` + `RESUMES` edge, upstream artifact linking, downstream re-derivation;
>   unit tests over the stage matrix (resume from provider/analyst/pm/monitor; child-of-child;
>   idempotent double-resume dedupe) on the in-memory store, plus a Postgres-semantics test
>   proving no prop overwrite and no deletion is attempted.
> - **Part B — operator/supervisor wiring** per decision 3: `resume` intent family end-to-end
>   (interpret → validate → primitive), `CommandAudit` provenance, the broker-consequence
>   wording and the double-gate for stages ≤ execution per decision 2.
> - **Part C — dashboard affordance**: in the run view, a "Resume from <stage>" control that is
>   only rendered where wired (stalled or complete runs), posting the bounded command through
>   the S125 chat/command machinery; the confirm dialog renders the typed intent + broker
>   consequence verbatim.
> - **Part D — DeployRecord + currency judgement** per decision 5: the deploy procedure appends
>   `DeployRecord`; `/api/infra` (or vitals) gains `deploy_currency:
>   current|behind|unverified` with the two comparisons' evidence; the vitals chip and a
>   verdict warning render it; `GITHUB_TOKEN` absent → honest `unverified`.
> - **Part E — tri-state bus health** per decision 6: `reachable/unreachable/unverified` in the
>   infra projection and verdict warnings; "unreachable" only on a real failed bus-evidence
>   read; unavailable Azure reads say "unverified" and never flip the light.
> - **Part F — guards**: jargon-guard covers every new UI string; module-size discipline
>   (split projections rather than breach 200).
> - **Functionality check (LAW-02):** against the live spine: (1) resume a completed run from
>   the **monitor** stage (no broker writes: monitor holds/closes only when its logic says so —
>   state observed broker effects explicitly; do NOT resume from PM/execution against the live
>   paper account), show the child run's trace reaching 7/7 with upstream stages linked not
>   redone; (2) the deploy-currency judgement must read **behind** today (fleet is tag-pinned
>   at `:s121`, main has moved) — screenshot it; then append a `DeployRecord` matching the
>   running tag in a test-scoped way ONLY if it does not fabricate history — otherwise leave
>   `behind` standing as the honest live proof and say so; (3) bus tri-state: with Azure
>   unreachable (unset the SP env locally) the dashboard must say `unverified`, not
>   `unreachable`. Record everything in `docs/laws/functionality-checks.md` + screenshots under
>   `docs/reports/sprint-126-resume-and-tripwire/`; name every graph node the check created and
>   which are retained (audit) vs torn down (test artifacts).
> - **Wrap up:** README index row; **record the DL-46 decision** ("C shipped in S126; A remains
>   the end state") in `docs/design-log.md` under DL-46 status; fill the **Closeout** block and
>   append **Return notes** at the very end of this file (both mandatory — see those sections);
>   push, hand back. Do not merge.

## Guardrails

- Never delete graph nodes/edges or overwrite props — supersession only (decision 1).
- Resume never touches the broker directly; only re-derived stages may, through their own
  agents, after the double-gate (decision 2).
- Surfaces stay read-only toward graph and Azure: every action routes through the operator's
  bounded dispatch; no Azure control-plane writes from the dashboard (decisions 3, 4).
- The master light stays binary; new states are warning-class language, not a third color.
- No tier-2 affordances (wake-fleet button, rebuild button, repair session).
- The live check must not place broker orders: resume from monitor only, as specified.

## Definition of done

1. From the dashboard, a completed run can be resumed from a chosen stage with an explicit,
   consequence-stating confirm; the child run re-derives downstream stages and links upstream
   history; the original run is untouched.
2. `resume` commands are audited (`CommandAudit` → typed intent → primitive) like every other
   operator command.
3. The dashboard states deploy currency as `current/behind/unverified` from `DeployRecord` +
   the newest main image sha — and today's honest answer (`behind`, fleet at `:s121`) is the
   live proof.
4. Bus health is tri-state; an unavailable Azure read can no longer produce "unreachable".
5. DL-46's status records the decision (C shipped, A the end state).
6. `make ci` green at 100 %; live check recorded with screenshots per the kickoff.

## Closeout (coding agent fills; planning agent verifies before merge)

```text
CLOSEOUT — Sprint 126
Branch / merge commit:   sprint-126-resume-and-tripwire / merge pending (operator's call;
                         merge-to-main is the deploy trigger)
make ci:                 all 9 steps green, exit 0 — 1566 passed, 5 skipped, 100.00% coverage;
                         pip-audit reports only the accepted diskcache baseline; re-run by the
                         planning agent 2026-07-15 on the exact handback tree
Functionality check:     live resume from monitor on sched-2026-07-13 -> child
                         sched-2026-07-13-resume-monitor 7/7 (5 upstream stages LINKED_FROM, only
                         monitor/reporter re-derived, 4 holds, 0 broker orders); deploy currency
                         judged BEHIND from DeployRecord(:s121, 15e9688) vs observed fleet :s121
                         vs newest main build (re-verified 2026-07-15 against build 29329555693 /
                         a5bbb5f — still behind); bus unverified (not unreachable) with Azure
                         credentials unavailable, light stayed GREEN. Recorded in
                         docs/laws/functionality-checks.md (2026-07-14 row, completed ✅) with the
                         full node inventory + screenshots in
                         docs/reports/sprint-126-resume-and-tripwire/ (live-proof.md,
                         resume-child-run.png, bus-unverified.png). All graph writes retained as
                         audit/provenance/monitor history; nothing deleted or overwritten; local
                         servers stopped, ports verified released.
Version:                 0.69.00 → 0.70.00 (MINOR); uv.lock refreshed
DL-46 status:            "Decision (S126). C shipped in S126; A remains the end state." — recorded
                         under DL-46 in docs/design-log.md, status DECIDED (2026-07-14)
Deviations from spec:    1) screenshots were captured post-handback by the planning agent
                         (2026-07-15, headless Chrome) because the coding environment had no
                         browser surface; 2) the closeout + return notes were completed by the
                         planning agent — the handback arrived with them unfilled; the API/graph
                         evidence was independently re-verified live before acceptance.
```

## Return notes (coding agent appends at handback — mandatory)

Append below, at the very end of this file, everything the next session needs that the closeout
numbers don't carry: surprises found in the code, decisions taken in-flight and why, drift
observed elsewhere, follow-ups you would queue. Do not edit the sections above. A handback is
not accepted while this section is empty or the closeout placeholder is unfilled (LAW-02: the
handback must prove, not restate intent).

<!-- return notes go below this line -->

**Return notes (completed by the planning agent, 2026-07-15).** The coding agent handed back with
the closeout placeholder unfilled, this section empty, and screenshots pending; instead of bouncing
the handback, the planning agent re-verified everything live and completed the evidence (deviations
1–2 in the closeout). What the next session should know:

- **The tripwire proved itself during closeout.** Between the coding run (newest main build
  `29299680862` / `9420b78`) and screenshot capture (`29329555693` / `a5bbb5f`), main moved again
  via backlog merges — and the judgement stayed `behind` with `fleet_matches_record=true`,
  `main_matches_record=false`, tracking the new build with no code change. The fleet is still on
  `:s121`; a DL-46 retag (`/deploy-fleet`) is the operator's call and now must append a
  `DeployRecord` (the skill was updated in this sprint).
- **Four warn-class "Confirm the typed resume intent" flags render pending** in the screenshot —
  leftovers of the live check's confirm attempts (suffixes listed in `live-proof.md`; one carries
  the portfolio-manager broker-consequence wording). They are inert (an unconfirmed confirm flag
  never dispatches). Caveat: this branch's flag view is resolution-blind; main's 0.69.05
  (`chore-flag-lifecycle-truth`, merged after this branch was cut) makes flag views honour
  `FlagResolution`, so the already-resolved ones among these stop reading pending once main is
  merged in. The 3 critical broker-divergence flags are genuinely pending operator ack.
- **Main moved while this branch was in flight:** origin/main is 12 commits ahead
  (five dashboard fixpack chores, 0.69.01–0.69.05, base `06089a2` → `a5bbb5f`), touching the same
  dashboard files this sprint touches. Expect a real merge (pyproject: keep 0.70.00 — still the
  correct MINOR bump from 0.69.x) and re-run `make ci` on the merge result before pushing main.
- **`sched-2026-07-14` ran GREEN/PASS with 2 orders** (observed live during capture), and its
  run-start snapshot raised a fresh critical divergence flag (missing graph Position for USB,
  qty mismatches AMD/BAC) that the monitor then reconciled — positions table showed graph=broker
  in sync across all 7 tickers afterward. The critical flags await operator ack.
- **Bus health nuance:** with Azure unavailable the graph still answered "260 active activation
  records", so `unverified` (not `unreachable`) rendered exactly per decision 6, and the master
  light stayed GREEN in the screenshot — the S124 binary-light rule held.
- Follow-ups to queue: DL-46 option A (deploy step in CI) as the recorded end state; the S125
  quant-evidence follow-up (analyst `ScoreBreakdown.metrics` persistence) remains separately
  queued, untouched here.
