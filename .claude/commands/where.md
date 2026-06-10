---
description: Show "you are here" — active branch, active sprint, next up, parked work
---

# Where Command

You are answering the question "where am I?" for a solo developer who has lost track of which branch, sprint, and effort is active. Output must be scannable in under 10 seconds.

## Steps

1. Read `docs/STATE.md` — source of truth for *intent*.
2. Run `git branch --show-current` and `git status --short` to get *reality*.
3. Run `git log --oneline -5` on the current branch and on `main` (if different).
4. Read the sprint index table in `docs/sprints/README.md` — note which sprint is **active**.
5. Note the **freshness** of STATE.md (last-updated line vs. today). If >3 days stale, flag it.
6. Reconcile intent vs. reality. If STATE.md says "Now: branch X" but current branch is Y, call that out. If the working tree has uncommitted changes that don't match STATE.md's described work, call that out.

## Output format

Keep to ~15 lines. Use this shape:

```text
YOU ARE HERE
────────────
Branch:   <current-branch>  (<clean|N files changed>)
Sprint:   <active sprint slug from index, or "between sprints">
Effort:   <one-line summary of what this sprint is for, from STATE.md>
Blocker:  <next step or blocker, from STATE.md>

Next up:  <1-3 bullets from STATE.md Next section>
Parked:   <count> items — <one-line each if ≤3, else "see STATE.md">
Shipped:  <last 1-2 items from STATE.md Shipped>

STATE.md: <fresh | N days stale — suggest refresh>
Mismatch: <none | describe any drift between STATE.md and git reality>
```

## Rules

- Do not make up state. If STATE.md is missing, say so and offer to create it.
- Do not re-summarize memory files — STATE.md is the summary.
- If the user has uncommitted changes on a branch whose STATE.md description says it's parked or shipped, flag it — that is drift worth surfacing.
- No emojis. No markdown fluff. Just the block above.
