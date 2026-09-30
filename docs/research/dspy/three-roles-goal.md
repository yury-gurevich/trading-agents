# The goal: all three deliberators understand quant and sentiment evidence and argue from it

**Part of:** [R009 · DSPy](INDEX.md) · **Date:** 2026-09-30 · **Status:** measured baseline and a
proposed sequence; nothing here is built yet.

> *"The main goal right now is to confirm that deliberators, all three, understand quant and
> sentiment data and USE IT IN DELIBERATION as arguments to prove their positions."* (operator,
> 2026-09-30)

The three roles are the **defender** (served by `deliberator-proponent`), the **challenger**
(`deliberator-opponent`) and the **judge** (`deliberator-manager`). The goal has three parts, and
each needs a different kind of proof:

| Claim | What would prove it | Can code check it? |
| --- | --- | --- |
| **Read:** the role took the value from the packet | The reading names the metric and copies its value exactly | **Yes.** The packet is the ground truth |
| **Understood:** the role knows what the value means *here* | The stated meaning matches what our code computes | Only against a ground truth for meaning: **the glossary, not built yet** |
| **Used:** the value is an argument for the role's position | The reading bears on the decision and the argument or ruling rests on it | **Yes**, from the readings plus the argument text |

---

## Where the three roles stand (measured)

*[measured 2026-09-30, read-only, no LLM call]* Every real debated order with a full analyst packet,
not failed open: **229 orders**. Each role's text was checked against *its own* packet. The defender
and challenger texts are their transcript turns; the judge's is the ruling's recorded `rationale`.

| Role | Names a quant metric | Quant metrics per order | Mentions sentiment or news | Quotes the sentiment score | Argues only from process |
| --- | --- | --- | --- | --- | --- |
| Defender | 80.8 % | 4.09 | 69.4 % | 61.6 % | 0.0 % |
| Challenger | 76.0 % | 3.68 | 52.4 % | 28.4 % | 5.2 % |
| **Judge** | **40.2 %** | **0.57** | **20.1 %** | **3.5 %** | **38.0 %** |

- *Quant metric:* a technical or fundamental metric from the order's own packet (`rsi`,
  `macd_histogram`, `peTTM`, …).
- *Sentiment or news:* the words sentiment, news or headline.
- *Process only:* argues from gates, filters, sizing or the regime floor, with no quant metric and no
  sentiment.

**How to read it:**

- **The judge, the role that decides, is the one that barely uses market evidence.** Six rulings in
  ten name no quant metric, and **38 %** rest on process facts alone. The judge's rationale averages
  **237 characters** (the debaters write about 2,900 per order). One real example:
  *"NEE's survived_filters lists only min_price/min_average_volume/min_relative_strength — no
  earnings_window attestation — and the 0.01 sizing cap is fixed-fraction notional…"*
- **The debaters cite a lot.** Earlier the same day, 759 of 772 recorded turns (98.3 %) quoted at
  least one packet number verbatim (DL-250 amendment 2).
- 🪰 **These are upper bounds, not proof of understanding.** Naming `rsi_score` is not reading it
  correctly. S119 measured understanding at **17 %**, and 150 turns asserted the false calendar-day
  fact while quoting their numbers correctly.
- **S246 covers two roles of three.** It gives the defender and the challenger a typed
  `GuidedReasoning`, but the judge's prompt, message and parse were left unchanged on purpose (its
  test B7). **The role that decides records no readings at all.**

**Measured directly in the guided format, at production effort.** *[measured 2026-09-30, `effort=high`, the
10 most recent real packets, every reading saved and classified by its content]*

| | Defender (88 readings, 10 turns) | Challenger (71 readings, 9 turns) |
| --- | --- | --- |
| Process (gates, sizing, stop basis, regime thresholds) | **78 %**, 66 of them `supports` | 52 % |
| Quant (technical, fundamental, scanner, market) | 19 % | 39 %, all `against` |
| **Sentiment** | **0**, although the sentiment score was in all 10 packets | 3 readings |
| Quoted `key=value` pairs equal to the packet | at least 93 % | at least 93 % |
| `metric` written as an exact packet key | 3 % | 23 % |
| Turns whose gaps name missing risk or portfolio evidence | **10 / 10** | **8 / 9** |

- **Values are copied accurately.** At least 93 % of the quoted pairs match. Most of the listed
  mismatches are a closing parenthesis caught by the parser, not the model's error.
- **Some meanings are right.** The TMO defender read `rsi=87.19` as *"already penalized inside the
  composite (rsi_score=25)"*: the contrarian scoring, read correctly.
- **The defender's case is "the process passed".** It argues from gates clearing, not from the
  stock, and it never uses sentiment, even when the sentiment is strongly positive for its side.
- **The `metric` field is not the exact key the schema asks for.** Models write line labels
  (`PM gate outcome: name=cash_available`) and compounds (`atr_pct / applied_stop_pct`). A metric that
  looks up exact names, such as S247's planned check, has to parse the quoted `key=value` pairs
  instead, or the instructions must be made explicit.
- **The models ask for what we withhold.** The TMO challenger's first gap: *"No stop-out probability,
  hit-rate, or MAE/adverse-excursion statistic anywhere."* The forecaster computes exactly that
  ([packet-inventory.md](packet-inventory.md)).

---

## What DSPy offers for each part of the goal

| Part | DSPy mechanism | Status here |
| --- | --- | --- |
| Read | `ChainOfThought(Sig, rationale_field_type=GuidedReasoning)`: typed readings (`metric`, `value`, `meaning_here`, `bears_on`) written *before* the argument | ✅ defender and challenger (S246, merged, not deployed) · ❌ **judge** |
| Read, checked | A deterministic reward: each `value` equals the packet's | Proven offline (below) |
| Understood | Meaning needs a reference. A **glossary** generated from code and given to all three roles, then `score_understanding` (`kernel/deliberation_understanding.py`) checks `meaning_here` against it | Glossary not built (work-queue 97 c) |
| Used | A metric returning `Prediction(score, feedback)` that fails a ruling resting on no market reading | Proven offline (below) |
| Enforced at inference | `dspy.Refine(judge, N=2, reward_fn=..., threshold=1.0)`: retry a failing ruling with generated advice | Proven offline; costs about 2 extra calls per failed ruling |
| Improved | `GEPA` with the feedback metric, judge first, over recorded debates | Needs the metric first; costs in [optimization.md](optimization.md) |

**Where the glossary goes.** DSPy puts the docstring (instructions) in the system message, and **GEPA
rewrites the docstring**. A glossary placed there could be edited or deleted by an optimiser. Field
descriptions are never rewritten, but a description is a fixed sentence about one field. The
DSPy-native place is **a dedicated input field** whose *value* is the glossary. An optimiser cannot
change it, and it appears identically in optimisation runs and in production. The cost: it sits in
the user message, so prompt caching needs the renderer to place it first and put a cache breakpoint
after it. DL-250 preferred the system message; this is the trade-off to settle when the glossary
sprint is specced. The glossary must define the **sentiment** keys as well as the quant ones. The
packet carries six: `analyst_sentiment_score`, `sentiment_score`, `sentiment_articles`,
`sentiment_batch_weighted_articles`, `sentiment_positive_words` and `sentiment_negative_words`.

---

## Checked offline at no cost (DSPy 3.4.0, `DummyLM`)

*[measured 2026-09-30]* A three-role `dspy.Module` was built from S246's own `GuidedReasoning`, with
canned model replies and no real LLM:

1. **All three roles are optimisable predictors.** `named_predictors()` returned
   `defender.predict`, `challenger.predict` and `judge.predict`.
2. **The judge can take the same guided reasoning.** Its system message carries the readings schema
   (2,223 characters).
3. **A deterministic `score + feedback` metric separates the cases:**
   - A process-only judge scored **0.2**, with the feedback *"judge: ruled on process facts only;
     name the quant/sentiment reading that decides it"*.
   - A defender that rounded `0.838` to `0.84` scored **0.8** (*"values not in packet"*).
   - A judge that decided on `rsi_score` and `analyst_sentiment_score` scored **1.0**.
4. **`Refine` confined to the judge** made **3 calls**: the process-only ruling, the advice, then a
   retry that carried a `hint_` input. The retry produced an evidence-based `revise`.
5. **`program.save()`** wrote one entry per role, each with its instructions (the text GEPA would
   rewrite) and its field prefixes.

🪤 **The lesson in 3b.** The check caught `0.84` against `0.838`. It could *not* catch `pe=30` read as
*"a price/earnings ratio of 30"*: that value was copied correctly, and only its meaning was wrong
(`pe` is a 0–100 sub-score, and the ratio is `peTTM`). **Code can prove a value was copied; only a
reference for meaning can prove it was understood.** That is why the glossary is required for the
goal, not an extra.

---

## Proposed sequence (planner's recommendation, not yet approved)

1. **A correct-effort replay of S246** (`effort=high`, as production runs). Save every reading, not
   only the count, and measure each debater's quant and sentiment coverage directly. This is also the
   retag gate.
2. **Give the judge guided reasoning.** This is the gap. `ChainOfThought(Ruling, GuidedReasoning)`
   with `ruling: Literal[...]`, recorded like the other turns. Every ruling also records its
   **evidence basis**: whether it rests on market evidence or on process alone.
3. **The metric** (S247's scope, widened to all three roles). Completeness: readings include quant
   *and* sentiment. Truth: each value equals the packet. Use: `bears_on` is not neutral, the argument
   refers to the reading, and every ruling rests on at least one market reading. It returns
   `Prediction(score, feedback)`, so GEPA can use it unchanged.
4. **Names and the glossary** (work-queue 97 b, c), sentiment included. Meaning becomes checkable.
5. **Measure before and after.** Baseline runs on the recorded format, then the glossary, then the
   same measure again. That comparison is the proof the goal asks for.
6. **Only then GEPA**, judge first, over recorded debates, with `max_metric_calls` and the dollar
   budget stated before the run.
7. **Optionally, `Refine` on the judge at inference**, once the check is stable in production.

**Decisions for the operator:**

- **Is a ruling on process facts alone ever legitimate?** For example, overturning because the
  earnings window was never checked. Step 3's rule (*every ruling rests on at least one market
  reading*) is a policy, not a technical detail.
- The spend for step 1 (≈ $2) and for step 6 (costed in [optimization.md](optimization.md)).

---

## Traps found on the way (all measured 2026-09-30)

- **`scripts/guided_turn_replay.py` picks the wrong subjects.** `latest_subjects()` sorts PMRun
  *keys*, which are not dates, and the tail of that sort is synthetic `verify-*` and `resume-link:`
  runs with no analyst lineage. The replay above used a wrapper that orders by `created_at` instead.
- **The same script takes the code's default `effort` (`"max"`),** but the three deployed deliberator
  apps set `DELIBERATOR_EFFORT=high`. A replay run as written measures a configuration production
  does not use.
- **`max_tokens=8192` is already the declared ceiling** (`le=8192` in `DeliberatorSettings`). At
  `effort=max` the challenger wrote 5,720–8,192 output tokens and hit the cap once in ten turns.
  Before S246 its maximum was 3,026.
- **Strict JSON (DL-252 D6) rejected one reading block of 20** because of a trailing comma. DSPy's
  own parser would have repaired it. The S246 spec's line is *"reconsider if F1 shows parse failures
  above 5 %"*, and 1 in 20 is exactly 5 %.
