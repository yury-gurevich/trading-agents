---
type: Architecture Decision
status: accepted
closes: "The deliberator returns uphold/overturn/revise but execution collapses everything that is not uphold into one action: drop the order. `revise` is 7.5x more common than `overturn`, nothing is ever revised, and the referee's systemic critiques are therefore spent rejecting individual trades. What should each verdict bind, and what happens when the judge cannot answer at all?"
tags: [deliberator, execution, veto, verdict, llm-judge, control-design, adr-0022, adr-0017, dl-173, dl-125, dl-134, exp-008, exp-011, exp-012]
amends: ADR-0022
---

# ADR 0029 — A `revise` is a finding, an `overturn` is a block

**Status:** Accepted · **Date:** 2026-09-18 · **Decider:** planning agent, under operator delegation
(*"make decisions in accordance to industry best practice. We will test the decision later one by one.
I am not sure I can see far enough to be useful"*, 2026-09-18)

## Context

Four consecutive scheduled sessions closed with **zero fills** (09-14, 09-16 x2, 09-17) while every
stage ran green and `ACCEPTANCE PASS` printed. On `sched-2026-09-17` the PM approved 3 buys and the
deliberator vetoed all 3. The full measurement is [DL-173](../design-log.md); the four facts that matter:

1. **Two verdicts, one action.** `contracts/deliberator.py:18` declares
   `Ruling = Literal["uphold", "overturn", "revise"]`. `agents/deliberator/review_batch.py:87` reduces it
   to binary — `if review.verdict != "uphold": vetoed.append(...)` — and `drop_vetoed`
   (`agents/execution/deliberation_gate.py:83`) then removes every vetoed ticker unconditionally.
   All-time on the spine: **`revise` 164, `uphold` 163, `overturn` 22** across 349 reviewed orders in 63
   runs. The verdict meaning *"change this"* is **7.5x** more common than the one meaning *"this is
   wrong"*, and **nothing is ever changed** — the order dies exactly as if overturned.
2. **Its grounds are true and measured non-actionable.** `reward_risk` cannot fail — and the ratio does
   not predict returns ([EXP-011](../research/experiments/EXP-011-regime-markov-and-barrier-calibration.md),
   47,485 decisions). The correlation gate is a 0.70 cliff — and **no cutoff from 0.70 to 0.50 changes a
   single trade** ([EXP-008](../research/experiments/EXP-008-correlation-cutoff-replay.md)). Sizing caps
   dollars not risk — and fixing it **costs $11,619 over ten years**
   ([EXP-012](../research/experiments/EXP-012-volatility-sizing-ten-year-replay.md), 100 % of bootstrap
   resamples negative). **Three correct criticisms; three fixes that do not pay.**
3. **It has stopped discriminating.** All-time, 17 of 30 acting runs vetoed only *some* orders. **Since
   2026-09-14, 4 of 5 vetoed the entire approved set.**
4. **It is not an outage.** `_parse_verdict` defaults to `revise` on an empty, unparseable or stopped
   judge response (`kernel/deliberation.py:105-115,155`), so plumbing failure and considered judgement
   share one token. Across all 63 runs the narratives contain **one** `unparseable` and **one**
   `defaulting to revise`. The vetoes are real judgements.

**The diagnosis.** The referee is asked to judge an order and is judging the *system* — because
rejecting an order is the only channel it has. A critique of gate design is spent as a trade rejection,
and the book stops trading.

### Why this is a control-design question, not a model question

Standard control practice answers it directly, and all three rules point the same way:

- **A checker objects to the transaction; policy objections escalate to policy owners.** Under
  maker-checker, a reviewer who believes the *policy* is wrong does not express that by rejecting
  transactions one at a time. That is a governance path, not a transaction path.
- **Preventive and detective controls are different instruments.** A transaction-specific objection is
  preventive and should block. A systemic finding is detective: it belongs in a register that gets
  triaged. Routing a detective finding through a preventive control is what produces a control that
  blocks everything.
- **A control that fires on the majority of events has no discriminating power.** At **53 %** all-time
  and 77 % recently, this one is past that line — and the repo has already measured the consequence in
  a different place: [DL-125](../design-log.md) found that a gate red for six straight nights on a
  non-defect trains the operator to ignore it. A veto that blocks everything is the same failure with
  capital attached.

## Decision

### 1 · `overturn` blocks. `revise` does not.

`vetoed_tickers` contains **only** the tickers whose verdict is `overturn`. A `revise` is recorded in
full — verdict, rationale, transcript, exactly as today — and the order **proceeds**.

Said out loud: *the referee may stop a trade it believes is wrong; it may not stop a trade it believes
is merely improvable.*

🚨 **This is a real reduction in an LLM's authority over the capital path, and it is the point.**
`revise` is 88 % of today's blocks, so the expected block rate falls from **53 % to about 6 %**. That
is not a side effect to be discovered later — it is the intended consequence, taken because three
independent experiments show the blocked trades were being rejected for system-level reasons that do
not survive measurement.

### 2 · A block must name a fact about *this* order

An `overturn` must cite something specific to the order under review. A ground that applies identically
to every candidate is, by construction, not a verdict about any of them. This is what keeps decision 1
from being a relabelling exercise: it is not enough to move the word, the blocking verdict has to earn
its blocking power.

### 3 · The judge is told what its verdicts do

The judge prompt states the consequence of each ruling plainly: `overturn` blocks this order, `revise`
records a design objection that is triaged and does not block, `uphold` passes. **Hiding a reviewer's
consequences from it produces miscalibrated verdicts** — a judge that does not know `revise` is fatal
cannot be blamed for using it loosely.

🪤 **This is the tripwire's other half.** Telling the judge that `revise` no longer blocks creates an
obvious hazard: it may simply start saying `overturn`. See *How this will be tested*.

### 4 · A `revise` lands somewhere durable, and does not re-raise itself

Recorded findings that nobody triages become noise, which is DL-125 again. So a `revise` objection is
written as a durable finding, **deduplicated by ground**: where a ground has already been measured and
recorded — the three in fact 2 above — the finding links that evidence instead of creating a new item.
The referee's fifth identical correlation-cliff objection must not become a fifth ticket.

### 5 · A judge that cannot answer is not a judge that said `revise`

🚨 **Required for safety, not optional.** Today a parse failure maps to `revise`, which blocks — so an
unreadable judge response fails *closed*. Under decision 1 that same failure would silently stop
blocking, turning a safety default into a silent fail-open. That is unacceptable and this ADR does not
ship without fixing it.

Therefore: a non-answer (empty, unparseable, unrecognised ruling, stopped response) **must not** be
recorded as `revise`. It routes into the existing **failed-open** path, which already stamps
`deliberation_status="applied_failed_open"` and raises a fault — the machinery
[ADR-0022's 2026-08-13 amendment](0022-the-veto-gates-buys-never-exits.md) built for exactly this
distinction at the run level. This extends that amendment one level down, to the individual verdict.

### 6 · What is unchanged

- **The veto still gates buys and never exits** — ADR-0022's core decision, and ADR-0017's exit
  authority, are untouched.
- **The grace period, the posture selector and the fail-open default** all stand. Note the posture
  switch is irrelevant here: `drop_vetoed` runs *before* `apply_deliberation_posture`, so an arrived
  veto binds identically under both ([DL-134](../design-log.md), item 6b).
- **The deterministic gates still bind.** Removing `revise`'s block does not leave orders unchecked; the
  PM's sizing, sector, cluster, confidence and beta gates are unaffected. The referee is an additional
  layer, not the only one.
- **The LLM can subtract but never add.** The 2026-06-27 founding constraint is preserved and in fact
  strengthened — this decision reduces what it may subtract and adds nothing.

## How this will be tested

The operator's instruction was *"we will test the decision later one by one."* Each is falsifiable:

| # | Test | Passes when | Fails when |
| --- | --- | --- | --- |
| 1 | Null check on the record | Every verdict is still recorded with its rationale and transcript; `revise` verdicts appear in `verdicts` but **not** in `vetoed_tickers` | Any verdict stops being recorded |
| 2 | First scheduled run after deploy | An order with a `revise` verdict reaches the broker; an `overturn`, if any, still blocks | A `revise` still blocks, or an `overturn` does not |
| 3 | 🪤 **Relabelling tripwire**, over the first 10 sessions with a real debate | `overturn` share stays near its historical **6.3 %** | **`overturn` share exceeds 20 %** — the judge has swapped words rather than changed its mind, and decision 3's prompt disclosure is the suspect. Revisit this ADR |
| 4 | Fail-closed on a non-answer | A forced unparseable judge response produces `applied_failed_open` and a fault, **not** a `revise` | A non-answer silently passes |
| 5 | The bar itself | Fills resume on nights the PM approves buys | Zero-fill sessions continue, in which case the cause was never the veto |

🪤 **Test 3 is the one that matters.** Decisions 1 and 3 interact: telling a judge that one verdict is
toothless is an invitation to use the other. If that happens this ADR has not failed *safely* — it has
been routed around — and the honest response is to revisit it, not to tighten the prompt until the
numbers look right.

## Consequences

- **Work-queue items 66 and 67 ([S212](../sprints/sprint-212-a-trace-says-why-nothing-was-submitted.md))
  become more valuable, not less.** A run where an `overturn` blocks something still needs to say so in
  the trace. S212 is unaffected by this ADR and can ship independently.
- **Both law books are touched.** The deliberator's, because what it writes into `vetoed_tickers`
  changes; execution's, because `EXEC-OBS`/`EXEC-NEV` describe how an arrived veto is honoured. The
  sprint that implements this owes the law cycle in the same unit of work.
- **`contracts/deliberator.py` need not change.** The `Ruling` vocabulary is already three-valued; this
  ADR changes only how it is *consumed*. Whether a contract field is needed for the durable finding is
  an implementation question for the sprint.
- 🟠 **This is paper-stage.** `ExecutionSettings.stage` is `paper` and the broker is Alpaca paper, so the
  decision is being taken where a wrong answer costs measurement time rather than money. **It should be
  re-examined before any move to a live stage** — the same evidence would deserve a stricter reading
  with real capital behind it.

## The road not taken

- **`revise` resizes the order smaller.** Rejected, and it was rejected before: the 2026-06-27 founding
  note flagged resize-on-revise as *"edges toward origination, so likely hard-block only"*, and ADR-0017
  makes the analyst the sole author of trade shape. It would make the LLM a sizer, which every prior
  decision has refused.
- **Keep both verdicts binding and accept the book does not trade.** Rejected. It fails the operator's
  standing bar (*trade unattended for a sustained stretch*) on evidence that the blocking grounds do not
  survive measurement. It is recorded because it is the status quo, and a status quo should be chosen
  rather than defaulted into.
- **Fix the gates the referee complains about.** Rejected on measurement — that is precisely what
  EXP-008, EXP-011 and EXP-012 tested. None changes what trades; one costs $11,619.
- **Prompt the referee to judge the trade and not the system, leaving both verdicts binding.** Rejected
  as the *primary* fix: it suppresses criticisms that are correct and that the system should want to
  hear. Decision 4 keeps them, in the register where they belong. The prompt work
  ([the operator's 2026-09-18 thread](../design-log.md)) remains worth doing on its own merits.
- **Flip `deliberation_posture` to `binding` or away from it.** Rejected as a non-lever: measured
  irrelevant to an arrived veto (DL-134).
- **Make `revise` blocking only when it names an order-specific fact** (decision 2 applied to `revise`
  instead of `overturn`). Rejected as too clever: it puts the block/no-block decision inside a natural
  language judgement about another natural language judgement. `overturn` already exists to mean *block*,
  and using the vocabulary as declared is simpler than inferring intent from prose.
