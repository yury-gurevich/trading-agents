---
name: resume-run
description: Resume a stalled pipeline run from where it stopped, or re-fire a day's run safely. Use after /diagnose-run finds a stall whose cause is fixed. Graph-pull makes resume natural — agents poll for unconsumed artifacts; day-keyed RunRequests merge-dedupe.
---

# Resume or re-fire a run

**The architecture does most of this for you.** Every stage's artifact persists on the graph and
each agent polls for *unconsumed* predecessors. A stalled run resumes from the stall point as
soon as the stalled agent runs again — no artifact surgery needed.

## Case 1 — stalled run, cause fixed (the normal case)

1. Confirm the stall point and that the cause is fixed (`/diagnose-run`; if the fix was code,
   `/deploy-fleet` first — the old images would just stall again).
2. Wake the fleet inside or outside the window:
   - **Wait for tonight's window** (default; zero risk), or
   - **Manual wake now:** `az containerapp job start -n dispatcher-cron -g trading-agents` —
     safe: the day-keyed `RunRequest` (`sched-YYYY-MM-DD`) **merge-dedupes** (proven S103:
     double-fire → `run_request_count=1`), and completed stages are not redone because their
     consumption edges exist. Note: as_of = **UTC today**, so a manual fire on a later UTC day
     creates a *new* run rather than resuming yesterday's — resuming yesterday's stall next
     UTC day means the stalled agents will still pick up their pending artifacts, but any
     *new* RunRequest is a separate run. Say which of the two you expect to happen.
3. Verify: `scripts/trace_run.py --run-id <id>` reaches 7/7 and `scripts/accept.py` gives a
   verdict; report both.

## Case 2 — redo a completed stage (bounded supersession)

Use the selected run's **Resume from &lt;stage&gt;** control in the dashboard. It posts through
operator chat, echoes the typed `resume` intent, and requires explicit confirmation. The
bounded primitive creates a child `RunRequest` with a `RESUMES` edge, links immutable upstream
artifacts, and lets stages from the selected point re-derive under the child run. It never
deletes graph history or edits existing properties.

For provider, scanner, analyst, portfolio manager, or execution, the confirmation states the
broker consequence: **re-running from portfolio manager will submit new orders at the broker**.
That consequence is real because the child identity produces new broker idempotency keys. Stop
unless the operator explicitly confirms it. Monitor or reporter resumes do not submit orders.
After confirmation, wait for the fleet's next wake or use the operator-approved manual wake in
Case 1; then trace and accept the child run id.

## Case 3 — the day never fired

Non-session day → nothing to do (calendar gate). Job disabled/failed → fix per
`/diagnose-run` step 2, then `az containerapp job start` as above if the session is still
tradeable, else let tonight's cron take it.

## Report format

Which case · what you did (or deliberately did not do) · run id(s) affected · trace + acceptance
after · anything left pending for the operator.
