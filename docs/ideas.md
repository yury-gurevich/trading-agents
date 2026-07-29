# Ideas — parking lot

Quick capture for ideas that arrive mid-flow and must not derail the current
sprint. Smaller than a moonshot (`docs/moonshots.md`), earlier than a design-log
thread (`docs/design-log.md`): one dated entry, a few lines, no commitment.

**Convention:** each idea is a `### YYYY-MM-DD — <short title>` heading followed
by 1–5 lines of context. Capture with `/idea`. When an idea graduates, move it to
the design log (open thread) or a sprint handover, and delete the entry here.

---

## Parked

### 2026-07-29 — audit every fan-out stage for per-item containment

DL-71's general lesson, never scheduled. Execution was a fan-out stage with no per-item
containment: one ticker's write failure cost three stages, a night's trading, and the
reconciliation that would have prevented it. S145 fixed *execution*. The same shape is
DRIFT-014 / S128 restated (*one 429 costs one ticker, not the feed*), which means it has now
appeared twice in different stages. Worth walking the cascade — scanner, analyst, PM, monitor,
reporter — and asking of each: does one item's failure take the stage down? Cheap to check,
and the failure mode is a whole run lost.
