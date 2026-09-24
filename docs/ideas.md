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

### 2026-09-23 — TypeSafe AI Jev as a cheap typed-decision challenger

TypeSafe AI Jev ("System One" model, released 2026-09-15, early access) as a cheap challenger
for typed LLM decisions (deliberator approve/veto, sentiment labels, filter verdicts). Returns
typed Choice/Score/yes-no values + calibrated probabilities in one pass, 70–500 ms,
~$0.042/M input tokens, output free; vendor claims 40–400x cheaper/faster than frontier LLMs.
Unverified: no paper, internal benchmarks only, "calibration" measured vs frontier-model
agreement not ground truth; no rationale output (weakens audit trail); max 255 choices. Use
only under ADR-0010 as a challenger, never champion. Cheapest test: replay already-recorded
deliberator decisions / sentiment labels through Jev and score accuracy + calibration against
realized returns. Parked: feature not fix, waitlist-only. Sources:
<https://typesafe.ai/blog/introducing-system-one-models-and-jev>,
<https://en.wikipedia.org/wiki/Jev_(AI_model)>

**Operator, 2026-09-24:** *"want to see how good it is. Will build parallel prediction path (non
breaking) and see if the LLM and JEV agree on the decision. I mean every stage of every decision."*
So the intended test is wider than the replay above: a **shadow path** beside the live one, where
every typed decision at every stage is also put to Jev, with agreement against the LLM recorded per
stage and per decision. Jev never decides anything on that path.

**Access provisioned 2026-09-24.** The operator supplied an API key: it lives in `.env` as
`TYPESAFE_API_KEY` and in Key Vault (`trading-agents-kv`) as `typesafe-api-key`, and the two match.
Probe: `POST https://api.typesafe.ai/v1/systemone` with `Authorization: Bearer`, model `jev-latest`, one
`noul` question → **HTTP 200 in 1.25 s**, served by `jev-1.13.0`, answer 0.97, 287 input / 22 output
tokens. 🟠 **Not yet wired:** no vault-seed entry, no secret-map grant, no master credential probe — those
belong to the sprint that builds the shadow path, so master can test the key before any agent gets it
(DL-36).

**Status:** uncommitted — the operator wants it built; not yet specced or ranked.
