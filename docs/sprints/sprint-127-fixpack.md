<!-- Agent: planning | Role: sprint handover -->
# Sprint 127 — Fixpack: flag lifecycle, approve routing, currency semantics, warning links (backlog rows 4, 9, 10, 11, 12)

**Phase:** Etalon-first continuous improvement (DL-19); first sprint after the DL-47 arc closed
**Branch:** `sprint-127-fixpack`
**Status:** ready for handover (packaged 2026-07-15)
**Effort:** M

---

## Why this sprint

Five confirmed items sit in `docs/sprints/s127-fixpack-backlog.md` with evidence attached; together
they justify the batch sprint the backlog was collecting toward. Two are operator-blocking
(pending flags are visible but not actionable — rows 10+11), one is a truth defect in the new
S126 tripwire (row 12), one is a navigation gap (row 4), one is a test-hygiene defect (row 9).

Explicitly **not** in this sprint: backlog row 3 (quant-evidence persistence for deliberation) —
deliberation domain, graduates to its own sprint; anything tier-2 (wake-fleet, rebuild buttons).

## What already exists (read before estimating)

- **S126 shipped and deployed**: fleet runs `:s126`; `DeployRecord` exists; the currency judgement
  (`surfaces/dashboard/projections_currency.py`) and tri-state health are live. Chat/confirm
  machinery (S125) carries typed intents end-to-end with `CommandAudit`.
- **Flag views are resolution-aware** (0.69.05): `FlagResolution` append-nodes; resolved flags stop
  reading pending. The graph currently holds 3 pending critical broker-divergence flags (operator's
  to ack) + stale inert `Confirm the typed resume intent` warn flags from the S126 live check.
- **The `approve` command exists** and dispatches through the supervisor gate (proven 2026-07-14 via
  the CLI direct-TypedIntent path) — only the operator grammar's *interpret* misroutes it (row 11).
- **The dispatcher's currency tag** comes from `job_row()` in
  `surfaces/dashboard/projections_azure.py`, which reads the latest *execution* image; the job
  *template* image is not currently read by the Azure port.

## Decisions taken at packaging (LAW-06)

1. **Row 12 — currency judges the job by its *template* image; the last execution renders as
   evidence.** The template is the configured truth ("what will run tonight"); the execution is
   history. The Azure read port gains one bounded method (job template image via the existing
   job-show REST read); `running_tags` uses it; the infra job card keeps showing the last
   execution's tag as an evidence line ("last execution ran :sNNN"). *Ruled out:* judging on the
   execution (a fresh deploy reads `behind` for up to 24 h — observed 2026-07-15); dropping the
   execution tag from the UI (it is real history and stays visible as evidence, not judgement).
2. **Row 10 — flag ack/resolve goes through the operator `approve` command, never a new write
   path.** Dashboard flags panel gains an "Acknowledge" affordance per pending flag that posts the
   bounded `approve <flag-key>` command through the existing S125 chat/confirm machinery
   (typed-intent echo + explicit confirm); the result is an appended `FlagResolution`, never a
   mutation. Depends on row 11 landing first. *Ruled out:* a `/api/flags/<id>/resolve` endpoint
   (bypasses operator audit + gates — same reasoning as S126 decision 3).
3. **Row 11 — fix interpret, prove with a routing table.** `approve <subject-ref>` (plain and
   steered phrasings) must produce an `approve` intent; add a regression table over the misrouted
   transcripts of 2026-07-14 plus the `resume`/`run`/`status` neighbours so the fix cannot regress
   silently. Grammar work happens *after* reading the S126 grammar diff (the in-flight changes the
   backlog row warned about are now merged).
4. **Row 4 — warning rows become client-side anchor links.** Map each existing machine `code` to
   its evidence panel (pending_flags → Trading/Flags; degraded_feeds → provider stage;
   deploy_behind/deploy_unverified + bus codes → Infrastructure); switch section, scroll, brief
   highlight. No new server fields. *Ruled out:* server-side URLs in the verdict payload (jargon
   guard + coupling for zero gain).
5. **Row 9 — optional-extra absence is a skip, not a failure.** `pytest.importorskip` (or guarded
   import) in `tests/test_bus_azure_receiver_integration.py` before any azure import executes.

## Codex kickoff (paste this)

> Execute **Sprint 127 — fixpack** exactly as specified in this file
> (`docs/sprints/sprint-127-fixpack.md`). Read first: `docs/sprints/s127-fixpack-backlog.md`
> (rows 4, 9, 10, 11, 12 — the evidence pointers are the spec); design-log **DL-48** (the process
> contract this kickoff enforces); `agents/operator/domain/grammar.py` + its S126 diff (row 11);
> `surfaces/dashboard/projections_azure.py` + `projections_currency.py` (row 12);
> `surfaces/dashboard/static/verdict.js` + `app.js` flags panel + the S125 chat machinery (rows
> 4, 10); `docs/laws/functionality-checks.md` (the evidence register you will append to).
>
> **Contract (DL-48 — read before starting, it is enforced):**
> - **Start:** `git pull` on `main` — `pyproject.toml` must read **0.70.00** (stop and report if
>   not). Branch `sprint-127-fixpack`. Bump **MINOR → 0.71.00** (rows 4+10 add capability) +
>   `uv lock`.
> - **Drift rule:** before handback, `git fetch` — if `origin/main` has moved, merge it into your
>   branch, resolve (version stays 0.71.00), re-run the full gate on the merge result, and record
>   what moved in the Return notes. A handback based on a stale main is not accepted.
> - **Secrets rule (CLAUDE.md "Secrets — never through the worktree"):** no credential ever
>   becomes a file in the repo tree. Everything you need is already in `.env`.
> - **Handback rule:** the **last two things you do** are (a) fill the Closeout block with proven
>   results and (b) write the Return notes. A handback with either missing is returned unmerged.
> - Hard gate throughout: `make ci` green (capture the **exit code**, never through a pipe that
>   masks it), 100 % coverage, ≤200-line modules, headers, tunables for any threshold.
>
> **Work items (row 11 before row 10):**
> - **A (row 11):** fix `approve <subject-ref>` interpret routing; regression table over the
>   2026-07-14 misrouted phrasings + neighbours (`resume`, `run`, `status`), each case asserting
>   the full typed intent, not just the family.
> - **B (row 10):** per-pending-flag "Acknowledge" affordance in the flags panel posting the
>   bounded `approve <flag-key>` through the existing chat/confirm machinery; confirm dialog
>   renders the typed intent verbatim; result is an appended `FlagResolution`; the panel and
>   vitals count update on the next poll. Render the affordance only where wired (S124 rule:
>   never show unwired controls).
> - **C (row 12):** Azure port gains a job-template-image read; `running_tags` judges the job by
>   template; job card shows "last execution ran :sNNN" as evidence; unit truth-table covering
>   template=s126/execution=s121 → `current`, template behind → `behind`, template unreadable →
>   `unverified`.
> - **D (row 4):** warning-code → anchor map in the client; every S124–S126 warning code mapped
>   (pending_flags, degraded_feeds, deploy_*, bus_*); jargon guard still passes.
> - **E (row 9):** importorskip guard; prove by running that one test file with the azure extra
>   absent (fresh venv or uninstall in a throwaway env) → SKIPPED, not FAILED.
> - **Functionality check (LAW-02), against the live spine, read-only toward broker/Azure
>   control-plane:** (1) live interpret of the row-11 phrasings → `approve` intents with fresh
>   audit IDs; (2) from the dashboard, acknowledge **exactly one** stale S126 confirm-intent warn
>   flag (they are inert; suffixes in
>   `docs/reports/sprint-126-resume-and-tripwire/live-proof.md`) — do **NOT** touch the three
>   critical broker-divergence flags, they are the operator's; screenshot before/after (pending
>   count drops by one, flag renders `resolved`); (3) currency: show the judgement with template
>   semantics live — after the 07-15 22:30 UTC fire both template and execution read `:s126`, so
>   also cite the unit truth-table as the `behind`-case proof; screenshot the vitals line;
>   (4) warning-link click lands on the right panel — screenshot. Record everything in
>   `docs/laws/functionality-checks.md` + screenshots under `docs/reports/sprint-127-fixpack/`;
>   name every node created and which are retained (the `FlagResolution` + audit trail are
>   retained provenance) vs torn down.
> - **Wrap up:** update the five backlog rows to **FIXED (0.71.00)** with proof pointers; README
>   index row; fill the **Closeout** block and append **Return notes** (both mandatory — the
>   handback is bounced otherwise, per DL-48); push, hand back. **Do not merge.**

## Guardrails

- No new write paths from surfaces to graph or Azure — every action routes through the operator's
  bounded dispatch (rows 10, 12 read-only additions excepted on the Azure *read* port).
- Never delete or overwrite graph state — `FlagResolution` is append-only supersession.
- The live check acknowledges only the named inert warn flags; critical divergence flags are the
  operator's to ack. No broker writes anywhere.
- The master light stays binary; no new colors.
- Module size: split before 200 lines; no `# noqa`.

## Definition of done

1. `approve <subject-ref>` routes correctly with a regression table pinning it.
2. A pending flag can be acknowledged from the dashboard through the audited operator command,
   proven live on one inert flag.
3. Deploy currency judges the dispatcher by template image; a fresh retag reads `current` the
   moment the fleet is retagged; the last execution stays visible as evidence.
4. Verdict warnings deep-link to their evidence panels.
5. The bus integration test skips (not fails) without the azure extra.
6. `make ci` green at 100 % (exit code captured); backlog rows updated; live check + screenshots
   recorded; closeout + return notes filled.

## Closeout (coding agent fills; planning agent verifies before merge)

```text
CLOSEOUT — Sprint 127
Branch / merge commit:   sprint-127-fixpack / <pending>
make ci:                 <exit code + counts>
Functionality check:     <row-11 routing proof + live flag ack + currency semantics + warning
                          links + skip proof + where recorded + retained-vs-torn-down inventory>
Version:                 0.70.00 → 0.71.00 (MINOR); uv.lock refreshed
Backlog rows:            <4, 9, 10, 11, 12 status lines as committed>
Drift rule:              <"main unmoved" | what moved + merge + re-gate evidence>
Deviations from spec:    <none | list>
```

## Return notes (coding agent appends at handback — mandatory)

Append below, at the very end of this file, everything the next session needs that the closeout
numbers don't carry: surprises found in the code, decisions taken in-flight and why, drift
observed elsewhere, follow-ups you would queue. A handback is not accepted while this section is
empty or the closeout placeholder is unfilled (LAW-02 + DL-48: the handback must prove, not
restate intent — and an incomplete handback is bounced, not repaired).

<!-- return notes go below this line -->
