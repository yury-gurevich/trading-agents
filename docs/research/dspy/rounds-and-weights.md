# Rounds and weights: what DSPy offers a debate, and what the debaters are not told

**Part of:** [R009 · DSPy](INDEX.md) · **Date:** 2026-10-06 · **Status:** read and measured; nothing
built.

> *"Can we make LLM understand and assign "weights" to the quant values we send them … not only the
> value, but general significance of an indicator in relation of other indicators."* And: *"DSPy
> examples on their site have examples on how they handled discussion rounds. Read it and tell me
> what you think."* (operator, 2026-10-06)

**Sources.** DSPy's docs source and package source at tag `3.4.0`:
`tutorials/conversation_history`, `api/primitives/History`, `dspy/adapters/types/history.py`,
`api/experimental/DecisionTypes.md` and `api/experimental/ReAnchor.md`. The tutorial
*Decision-Making with Jev Types* is on `main` only (merged 2026-09-27, after the tag). The installed
3.4.0 source was read for the decision types (`dspy/adapters/decision.py`, `decision_state.py`), and
one offline probe was run against it with no LLM call (section 2). `dspy.History` was read, not run.
The measurements in section 3 are from this repo's code and its recorded debates, with no LLM call.

## 1. Rounds: DSPy has no debate example; it has `dspy.History`

The site has no tutorial in which roles argue. The nearest is *Managing Conversation History*.

- **The mechanism.** An input field typed `dspy.History` holds `messages: list[dict]`, each entry
  keyed by the signature's own fields. The adapter writes each earlier entry as a real user message
  (its inputs) followed by an assistant message (its outputs, in the output format), then the
  current inputs as the last user message. DSPy does not keep the history: the program appends to it
  after each call. Inside a few-shot example a history is not expanded; it is one JSON value.
- **What we do instead.** `render_transcript` joins every earlier turn into one string and passes it
  as the `transcript` input (`kernel/deliberation_guided_render.py`). Each role is sent the whole
  packet (about 9,500 characters) and the whole text again on every turn.
- **What a history per role would change.** The role's earlier turn returns as its own answer in the
  typed format, which demonstrates the format (the one unreadable turn in 36 was a round 2). The
  other side's latest turn becomes the new input this turn answers. The packet is sent once, in a
  first message that does not change, which is the shape the prompt cache needs.
- **What it does not give.** Nothing in `History` makes a role answer a point. A reply is an output
  field we would have to add ([DL-264](../../design-log.md), goal a).

Other round-shaped tools are already in these notes: `Refine` and `BestOfN` (retry against a reward
function) and `MultiChainComparison` ([concepts.md](concepts.md)). The site's finance tutorial is a
tool-using agent that fetches news, which DL-250's amendment 2 ruled out for the debate roles.

## 2. Weights: the decision types (3.4, experimental)

`dspy.experimental` has three output types that turn a judgement into numbers:

| Type | The model gives | Derived locally | Tunable |
| --- | --- | --- | --- |
| `Noul` | P(true) | the yes or no | `threshold` |
| `Score[...]` (2 to 10 ordered levels) | a probability for each level | value = the mean level; a level | `cuts` |
| `Choice[...]` (closed options) | a probability for each option | the option with the largest probability × weight | `weights` |

- With a generative model the adapter asks for those probabilities as JSON and derives the value in
  code. `Choice` and `Score` keep the backend's confidence, *"including LLM self-reports"*.
- **`ReAnchor`** fits the thresholds, cuts and weights to a metric over labelled examples. It keeps a
  change only when it also wins on held-out folds (up to five), and it never rewrites instructions.
  The numeric settings are not part of the request, so re-fitting reuses cached answers.

**Checked offline** *[measured 2026-10-06, DSPy 3.4.0 in a throwaway environment, no LLM call]*. A
turn signature was built as `ChainOfThought(Turn, rationale_field_type=GuidedReasoning)` with two
`Score` weights, one `Choice` and the free-text argument:

- The output order is `reasoning`, the weights, `hinge`, `argument`: the readings are still written
  first.
- A weight reaches the model as its instruction and its level descriptions, and the model is asked
  for `{"probabilities": {"0": …, "1": …, "2": …}, "confidence": …}`.
- A canned completion parsed and decoded beside the typed reasoning: probabilities 0.1 / 0.7 / 0.2
  gave value 1.1 and level 1, and the `Choice` returned its option with the whole distribution.
- The decoding is a few lines of arithmetic (`decision_state.py`), so the runtime can reproduce it
  without DSPy, as S246 does for the turn's text.

**Four limits that shape any design here:**

1. **Only top-level output fields are decoded from probabilities.** Inside a `list` or `dict` *"the
   LM generates values and confidence directly; thresholds, cuts, and weights are not applied"*. A
   weight on each entry of our `readings` list cannot use these types. A small fixed set of fields
   can. 🪤 A `Score` placed inside a Pydantic reading model got no decoding **and no warning** in the
   probe.
2. **`ReAnchor` needs labels.** It calibrates toward a reference; it does not supply one.
3. **`TypeSafe("jev-latest")` answers closed-set outputs only**: no free text, no `Refine`, no
   `BestOfN`, no generative optimiser. It cannot write a reading or an argument. EXP-016 measured Jev
   as a forecaster of stop and target probabilities and found no skill; grading evidence is a
   different job and is not measured.
4. **A stated probability is not evidence.** These types make a weight recordable and comparable.
   They do not make it right.

## 3. What our code already knows, and the packet does not say

**The score is arithmetic** (`agents/analyst/domain/scoring.py`, `technical_rules.py`,
`fundamental_rules.py`):

- technical = 0.8 × the mean of the available indicator sub-scores + 0.2 × the relative-strength score
- fundamental = the mean of its sub-scores
- composite = 0.50 × technical + 0.30 × fundamental + 0.20 × sentiment, renormalised over the pillars
  present
- confidence = 0.30 + 0.60 × composite
- **The VIX is in nothing.** It picks the regime label (thresholds at 15, 20, 25 and 35), and the
  label is only printed. The floor, the base stop, the base target and the holding window are the
  same settings constants under every label (`agents/provider/agent.py`, `domain/regime.py`).
  🩹 *Corrected 2026-10-06:* this note first said the regime sets them, which is what the packet's
  `Regime:` line suggests and no code does.

The packet shows the three pillar scores, the composite and the confidence. It shows **no weight and
no formula**.

**GILD, `sched-2026-10-05`** *[measured 2026-10-06, recomputed from the packet's own sub-scores]*:

| Pillar | Score | Weight | Contribution | Share |
| --- | --- | --- | --- | --- |
| Technical | 0.587 | 0.50 | 0.294 | 54 % |
| Fundamental | 0.342 | 0.30 | 0.103 | 19 % |
| Sentiment | 0.750 | 0.20 | 0.150 | 27 % |
| Composite | | | **0.546** | |

Confidence = 0.30 + 0.60 × 0.546 = **0.628** against a floor of 0.600, the packet's own figure to four
places. **With the sentiment score at a neutral 0.50 the confidence is 0.598, and with no sentiment
pillar 0.597: the order clears the floor only because of the sentiment score** (it needs 0.519 or
more). In the debate the challenger attacked *"an undisclosed mapping"* from 0.5462 to 0.6277, the
defender answered that the two are *"separate source-owned"* fields, and the sentiment score was named
once, in passing, by the defender. The news list in the packet includes headlines about other
companies (Compugen, BioMarin, Pfizer).

**The nine debates that store their packet** *[measured 2026-10-06; 2026-10-01 to 10-05]*:

- The confidence is reproduced from the code's weights in **9 of 9**, so the fleet runs the defaults.
- **5 of 9 would fail the floor with one pillar set to neutral**: sentiment in 3 (DE, MRK, GILD),
  technical in 2 (DE, EMR). TGT cleared by 0.008.
- In the 3 that hinge on sentiment, the judge's ruling mentions sentiment or news in **0**. The
  defender's argument mentions it in 3 and the challenger's in 2. 🪰 Word matches, so upper bounds.

## 4. What this suggests (the planner's reading; not decided)

1. **Facts in.** The packet states the arithmetic above for the order: each pillar's weight and
   contribution, the formula, the margin over the floor, which pillar the outcome hinges on, and
   that the VIX sets nothing. Generated from code and the same for all three roles, so it is a definition
   (DL-250's rule), not a hint. It belongs with work-queue 98 and 97 (c).
2. **Weights out, typed.** After its readings a debater states how much each evidence family bears
   on this order (technical, fundamental, sentiment, regime, the stop and target, the book) and
   which one decides. A fixed set of top-level `Score` fields and one `Choice` fit limit 1.
3. **The proof is a changed input.** Re-run a recorded turn with one value changed. A role that
   understands significance moves its weights and its argument when the hinge moves, and holds them
   when a value with no weight moves. The code's own arithmetic says which is which.
4. **First as an experiment on recorded packets**, in two arms (today's packet; the packet plus the
   arithmetic), with the call count and the dollar budget stated before the run.

**Not answered here.** Whether 0.50 / 0.30 / 0.20 are the right weights. Only outcomes can say, and
the replay cache holds prices and the VIX but no fundamentals or sentiment history (DL-232).
