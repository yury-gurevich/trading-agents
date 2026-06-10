---
description: One-page project roadmap — vision, phase progress, sprints shipped and remaining
---

# Progress Command

You are producing a **project report for a non-coder solo developer** who wants the whole arc of the project on one screen: where it's going, what's shipped, what's active, what remains, in what order. This is the strategic view. `/where` is the tactical view — do not duplicate it here.

Always render inline. Never save a file.

## Sources (read in this order, in parallel where possible)

1. `docs/PRD.md` — product vision (executive summary, phases A–D)
2. `docs/build-plan.md` — the authoritative phase list with goals, exit criteria, and status table
3. `docs/STATE.md` — current active sprint and Next queue
4. `docs/sprints/README.md` — sprint index (shipped / active / planned rows)
5. `git log --oneline --first-parent main -10` — recent ships on main

If any of sources 1–3 is missing, say so in the **Notes** line at the bottom and carry on with what's available. Do not invent a roadmap from thin air.

## How to compute each section

- **Vision:** one line distilled from PRD.md §1 or the opening paragraph. A paraphrase a non-coder can read — not a quote.
- **Today:** today's date from the environment context. No version tags — this is a pre-release rebuild.
- **Current phase:** infer from STATE.md's Now + the build-plan Status table. Name the phase (P0–P10), not the branch.
- **Active work / Blocker:** direct from STATE.md's Now.
- **Progress list:** merge the build-plan Status table with the sprint index. Each phase gets one of four states:
  - `[✓ done ]` — phase is complete per build-plan Status table
  - `[● now  ]` — matches STATE.md's Now / build-plan "active"
  - `[○ next ]` — next 2-3 open phases in build-plan order
  - `[○ later]` — everything else still open
  Keep to ~10 lines. One line per phase (not per sprint). Where a phase has multiple sprints, summarise them (e.g. "P1 S01 S07 S08 shipped; MCP/RAG remain").
- **Sprints shipped:** count from the sprint index (Status = shipped). Report as a single integer.
- **Sprints remaining in P3:** count open sprints still needed to close P3 (decision loop exit criterion). Report as a single integer with a `~` if approximate.
- **Parked:** defer to `/where` — just a count and a pointer.

## Output format

~25 lines total. Use this exact shape:

```text
PROJECT PROGRESS — trading-agents
══════════════════════════════════
Vision:   <one line, paraphrased from PRD.md>
Today:    <YYYY-MM-DD>

◆ WHERE YOU ARE
  Current phase:  <P-number and name from build-plan>
  Active work:    <STATE.md Now, one line>
  Blocker:        <next step or blocker, one line>

◆ PROGRESS (shipped → next, in order)
  [✓ done ]  P0  Boundary map
  [✓ done ]  P1  Kernel runtime          (partial — MCP/RAG build-when-needed)
  [✓ done ]  P2  First vertical slice    provider → scanner → analyst
  [● now  ]  P3  Decision loop           <active sprint, branch>
  [○ next ]  P3  <remaining P3 sprints>
  [○ next ]  P4  Orchestration
  [○ later]  P5–P10  <phase names, one line>

◆ ESTIMATED PATH TO P3 EXIT
  ~<N> sprints remaining in P3 (decision loop exit criterion met when reporter ships).
  Sprints shipped overall: <M>.

◆ PARKED / ASIDE
  <N> parked items — see STATE.md

Notes: <source gaps, stale docs, drift worth flagging | none>
```

## Rules

- No emojis beyond the ◆ ✓ ● ○ marks shown in the template. Those are the exact glyphs — don't substitute.
- Do not invent sprint counts. If the build-plan doesn't enumerate sprints cleanly, add `~` and note "approximate" in Notes.
- Do not re-summarize STATE.md's full Next list — pick the 2-3 next phases from the build-plan, because the plan knows dependency order.
- This command is read-only. Never write to STATE.md, build-plan.md, or any file.
