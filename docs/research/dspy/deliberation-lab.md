# The deliberation lab: a standalone bench for whether the expert understands its evidence

**Part of:** [R009 · DSPy](INDEX.md) · **Date:** 2026-10-03 · **Status:** PROPOSED, nothing built; scope decisions taken 2026-10-03 (§9)
([DL-264](../../design-log.md)) · **Asked for by:** the operator, 2026-10-03

> *"I want a standalone test environment that allows us to make changes to the prompt and its
> accompanying data, and see that they are understood and used in producing the expert's decision,
> not just use the harness to deliver a verdict."* (operator, 2026-10-03, paraphrased)

The deliberator trio (defender, challenger, judge) is the only place the system relies on "an
expert". This page proposes a lab where one **prompt variant** and one **set of cases** are run
through the trio offline, and the output is not a verdict but a measurement, per role and per
parameter:

1. **Understood:** does the role know what this value means *in this system* (its scale, its direction
   for a buy, the thresholds our gates use)?
2. **Used:** does the role read it and argue from it?
3. **Decisive:** when the value changes, does the decision change, in the direction an expert would
   expect? And does it stay put when something irrelevant changes?

---

## 1. Why the current tooling cannot answer this (measured)

**DSPy as an optimiser has never run.** `DSPyPromptOptimizer.compile_prompt` imports `dspy` only to
check that it is installed (`kernel/dspy_optimizer.py:33`), then joins the instruction and the
few-shot examples into one string (`:34`, `_few_shot_prompt`). No signature, metric, `Evaluate` or
optimiser has ever executed. The only DSPy-shaped part of production is S246: the defender's and
challenger's turns are rendered in DSPy's `ChainOfThought` format, without DSPy, and the judge was left
unchanged on purpose.

**What we already know about understanding** ([three-roles-goal.md](three-roles-goal.md), measured
2026-09-30):

| Finding | Number |
| --- | --- |
| Values are copied correctly | ≥ 93 % of quoted `key=value` pairs match the packet |
| Understanding of our parameters (S119) | **17 %** |
| Judge rulings that name any quant metric | **40 %**; 38 % rest on process facts alone |
| Defender readings that are process facts (gates passed, sizing) rather than market evidence | **78 %**; **0** sentiment readings, although the score was in all 10 packets |
| Turns that asserted a false fact about our code while quoting their numbers correctly | 150 of 936 (fixed in S245) |

**The packet tells the model we don't define our terms.** Every packet carries *"keys keep
producer/vendor names; units/scope are unknown unless the key names them"*
(`agents/deliberator/context_values.py:19`). `pe=30` is a 0–100 sub-score, not a P/E ratio. Two
different metrics are both called `relative_strength`, and `_pct` comes on three scales.

**Every existing tool measures the verdict, not the reasoning behind it:**

| Tool | What it measures | What it cannot tell you |
| --- | --- | --- |
| `scripts/deliberation_eval.py` | Did the challenger name a known flaw (keyword or LLM judge)? | Whether any parameter was understood |
| `scripts/deliberation_quality.py` | Does the veto agree with itself and with the record? | A referee that is consistently wrong passes |
| `scripts/guided_turn_replay.py` | Did the turn parse? How many readings? | Whether the readings are right, or decisive |
| `scripts/compare_deliberation_prompts.py` | Golden-firewall regressions, S119 marker score | Keyword markers, not meaning; no sensitivity |
| Replay fidelity (P17) | Did the replay decide what live decided? | Nothing about the referee; it isn't replayed |

None of them changes one input and watches what the expert does with it. That is the core of this proposal.

---

## 2. The lab in one picture

```text
   CASE SET (data)             PROMPT VARIANT                 MODEL CONFIG
   recorded packets       +    system prompts per role   +    model, effort,
   expert cases                glossary, key names,           max_tokens,
   perturbations               packet layout, examples        repeats
          │                           │                           │
          └──────────────┬────────────┴───────────────────────────┘
                         ▼
              RUNNER  (offline: no graph, no bus, no fleet)
              renders each case with the variant → defender → challenger → judge
              every response cached by content hash; budget enforced
                         ▼
              SCORERS  (code first; answer key = glossary generated from code)
              quiz · readings audit · sensitivity · expert cases
                         ▼
              REPORT   per role × parameter: understood / used / decisive
                       A vs B diff between two variants · misreadings quoted · cost
```

**Three inputs, each a versioned file, each swappable on its own:**

- **Case set:** frozen packets. Sources: recorded packets exported once from the graph (read-only),
  expert cases you write, and perturbations generated from both.
- **Prompt variant:** everything that shapes what the expert sees. That covers each role's system
  prompt, the few-shot examples, the glossary, a key-renaming map (`pe` → `pe_subscore_0_100`), the
  packet's layout (grouping, order, units shown) and the reasoning schema. **The baseline variant is
  production's own renderer** (`agents/deliberator/context*.py`), so the lab measures exactly what
  the fleet sends. Other variants layer changes on top of it.
- **Model config:** model, effort (production runs `high`, not the code default `max`), token
  ceiling, and number of repeats.

A run is identified by **case hash × variant hash × config**. Responses are cached on that key, so
re-scoring, re-reporting and comparing cost nothing after the first run.

---

## 3. The four tests

### Test 1: the comprehension quiz (understood, separated from deciding)

For each parameter in a packet, the role receives its own variant's system prompt and glossary, then
answers structured questions. The answers are typed, so code can mark them:

| Question | Answer type |
| --- | --- |
| What is this? | enum: `sub_score_0_100`, `ratio`, `percent`, `fraction_0_1`, `z_score`, `count`, `days`, `price`, … |
| For a buy, is a higher value better? | enum: `higher_better`, `lower_better`, `band` (contrarian), `not_directional` |
| Is *this* value favourable for *this* order? | enum: `favourable`, `unfavourable`, `neutral` |
| Does one of our gates use it, and at what threshold? | name and number, or `none` |

The answer key comes from the glossary (§4). This is cheap: many parameters fit in one call. It
answers **"is the prompt understood?"** directly, before any argument is involved. A parameter the
role cannot explain in a quiz is noise in a debate.

### Test 2: the readings audit (understood and used, inside a real deliberation)

The full trio runs in guided format, **with the judge guided too**. Every reading is checked:

- **Truth:** the value equals the packet's.
- **Meaning:** the reading carries the quiz's typed fields, so `scale` and `direction` are checked
  against the glossary by code. This replaces the free-text `meaning_here` marker match that S119 used.
- **Correct use:** `bears_on` agrees with the glossary's direction for this value.
- **Used:** the argument or the ruling cites the reading.
- **Coverage:** which material parameters no role read, and whether a missing parameter is named as a gap.

### Test 3: counterfactual sensitivity (decisive)

**This answers "does the combination of parameters determine the decision".**

- **One-at-a-time perturbation.** Take a case and move **one** parameter to a value the glossary marks
  clearly favourable or clearly unfavourable. Examples: RSI score 25 → 80, sentiment +0.5 → −0.6,
  earnings in 20 days → 2 days, correlation with a holding 0.3 → 0.85, stop-first probability 0.30 →
  0.55 (once item 99 allows it). Derived values are kept consistent: if the score moves, the composite
  that uses it moves too.
- **Placebo perturbation.** Change things that must not matter: the ticker name, the order of lines,
  an irrelevant field, a value inside its neutral band. The decision should not move. If it does, that
  is noise or position bias.
- **Ablation.** Remove a parameter. Does the ruling change? Does a role name it as a gap?
- **Repeats.** Run the unperturbed case N times first. A perturbation counts only if its effect is
  larger than the case's own run-to-run variance.
- **Two modes.** *Judge-isolated:* the debaters' transcripts stay fixed and only the judge sees the
  perturbed packet. This tests whether the judge reads the evidence or only the debate. *Full trio:*
  everyone sees the perturbed packet.

The output is a **sensitivity matrix, parameter × role**: how often the ruling moved, how often it
moved in the expected direction, and the placebo flip rate. A parameter we believe is decisive with a
flat row is evidence the expert ignores it. A placebo row that moves means the expert is unstable.

### Test 4: expert cases (decision correctness)

These are cases you author, where a combination of parameters implies the right ruling. For example:
strong technicals but earnings tomorrow; everything favourable except a 0.85 correlation with an
existing holding; a strongly negative sentiment against a strong score. Each case states the expected
ruling **and the parameters a correct ruling must rest on**. A right ruling for the wrong reason scores
as a miss. You act as the examiner of the expert, which is the one thing code cannot supply.

---

## 4. The answer key: a glossary generated from code

Without it, "understood" cannot be measured. Every check in Tests 1–3 reads from it. This is work-queue
97 (c), and it comes first.

- One entry per packet key (≈ 73 source-owned keys plus the six sentiment keys): definition in this
  system, scale and unit, direction for a buy (including contrarian bands), the thresholds our gates
  apply, and which pillar it feeds.
- **Generated from the code that computes the value**, so it cannot drift from what the analyst
  actually does. A test fails when a computed key has no entry.
- Shown to all three roles identically, as a **dedicated input field**, not in the docstring. That is
  where DSPy puts instructions, and GEPA rewrites instructions, so an optimiser could delete the
  glossary. Field values are never rewritten ([three-roles-goal.md](three-roles-goal.md)).

---

## 5. Where DSPy actually belongs

The lab is where DSPy is used as designed. Production keeps DL-252's rule: no `dspy` in any image,
and a parity-tested renderer.

| Stage | In the lab | In production |
| --- | --- | --- |
| Signatures for all three roles (judge included) | `ChainOfThought(Sig, rationale_field_type=GuidedReasoning)` | Rendered byte-identically without DSPy (S246 pattern) |
| Metric | Tests 1–4 combined into `Prediction(score, feedback)`; the feedback quotes the misreadings | — |
| Evaluation | `dspy.Evaluate` over the case set | — |
| Optimisation | GEPA, judge first, `max_metric_calls` and the dollar budget stated before the run | — |
| Output | A saved program, exported as a frozen prompt artifact | The artifact is loaded and rendered; the ADR-0010 golden firewall still applies |

The lab metric is the thing GEPA needs and the repo has never had. Optimising before it exists would
optimise toward verdict agreement, which is what we already distrust.

---

## 6. Standalone and safe

- **Runs on your machine with only an LLM key.** It needs no graph, bus, fleet or Azure. The graph is
  read once, by a read-only export command, to freeze recorded packets into case files.
- **Fake mode:** a deterministic stand-in model, $0, so the bench and its scorers can be tested in CI
  like any other code.
- **Budget first:** every run prints its call count and estimated cost before starting, and stops at
  the cap. *[estimate, derived from S245's live replay: 10 recorded propositions for $1.45]* Roughly:
  quiz ~$1–3 per variant; readings audit ~$1.50 per 10 cases; a judge-isolated sensitivity sweep of
  10 cases × 12 parameters × 3 repeats ≈ 360 judge calls, of the order of $10–30. To be re-measured on
  the first run.
- **Nothing reaches production by accident.** A variant becomes the champion only when it beats the
  current champion on the lab report against pre-stated thresholds, passes the ADR-0010 golden
  firewall, and goes through the normal sprint cycle.

---

## 7. Build sequence (functional increments)

| Step | Delivers | You can then |
| --- | --- | --- |
| **L0 Glossary** | Answer key generated from code, with a coverage test | Read what each parameter means, in one place |
| **L1 Bench** | Synthetic case files (real-case export comes last), variant files with production's renderer as baseline, runner, cache, budget, fake mode; the judge gets guided reasoning in the lab | Run any prompt variant over any case set offline |
| **L2 Understood + used** | Quiz and readings audit, with a report per role × parameter | See today's champion's baseline: which parameters each role misreads or ignores |
| **L3 Decisive** | Perturbation, placebo, ablation and repeats, and the sensitivity matrix | See which parameters actually move the expert's decision |
| **L4 Workbench** | Expert case library and an A vs B diff report | Change prompt or data presentation and see the effect, parameter by parameter |
| **L5 Optimise** | GEPA against the lab metric, judge first, budgeted | Let the optimiser search instruction space against *understanding*, not agreement |
| **L6 Promote** | Exported artifact, parity test, firewall, sprint | Ship a variant that is proven understood, used and decisive |

L0–L3 answer your question about today's expert. L4 is the tool you asked for. L5–L6 come only after it.

---

## 8. Ruled out, and why

- **Testing on live nights:** one data point a night, inputs cannot be perturbed, and a bad variant
  would decide real orders.
- **Using the fidelity or verdict harness as the test:** it measures agreement with recorded verdicts.
  A referee that is consistently wrong passes.
- **An LLM grader as the main measure of understanding:** it shares the misreadings it is meant to
  catch. Typed answers checked against the code-generated glossary come first. An LLM grader is used
  only on free text, and only with a hand-audited sample.
- **Keyword markers for meaning** (S119's `score_understanding`): `pe=30` read as a P/E ratio can
  contain every marker. They are replaced by typed `scale` and `direction` fields.
- **Glossary in the docstring:** GEPA rewrites docstrings.
- **`dspy` in production images:** DL-252 holds. `diskcache` still comes with it.
- **Optimising first (GEPA before L2):** without the metric, it optimises toward what we distrust.

---

## 9. Decisions (operator, 2026-10-03)

**Decided:**

1. **All three roles from the first pass.** The defender, the challenger and the judge are all guided,
   audited, quizzed and perturbed. That costs about three times the calls of a judge-only pass.
2. **The decision rests on quant data, read and used as an expert would.** Operator: *"I want it to
   be dependent on quant data and expert use of the quant data as a base for decision making."* So a
   ruling or argument whose basis is process facts alone (gates passed, sizing, a missing
   attestation) **scores as a failure in Test 2 by default**. Process facts may support a quant-based
   case, but they are not its basis. The operator did not settle whether any process-only ruling is
   ever legitimate, so the lab **reports process-only rulings as their own column**, with the case
   quoted, so that question is decided later on evidence rather than in the abstract.
3. **The planner drafts the expert cases, and the operator approves** each one's expected ruling and
   decisive parameters.
4. **Synthetic data first, real cases last.** L1–L4 run on synthetic cases built from the glossary.
   Final validation runs on **real, previously seen cases** (recorded packets). Where those live is
   decided when they are first needed, before L4's final run. The default is still OneDrive, because
   real packets carry the account's cash and holdings and the repo is public.
5. **Nothing that exists may break** (§10).

**Still open:** the budget for L2–L3, and later for L5. Each run states its cost before it starts (§6).

---

## 10. Guarantee: the lab does not touch what is there

The operator's condition, 2026-10-03. The lab is **additive**:

- **New code only.** The lab lives in its own folder, inside the module-size and import-linter gates.
  Agent, kernel and orchestration code does not change for the lab. Production's renderer is
  **imported read-only** as the baseline variant, never edited to suit the lab.
- **No writes anywhere live.** It does not write to the graph, publish to the bus, or contact the
  fleet or the broker. The one graph read, the export of real cases, comes at the end and is read-only,
  like `orchestration/replay_corpus.py` today.
- **`dspy` stays out of images.** It is a dev-group dependency used only by the lab (DL-252).
- **Proven by the gate.** `make ci` stays green with all 15 steps, and the existing deliberator tests
  are untouched. A test asserts that the baseline variant renders byte-for-byte what the deliberator
  agent sends today. If production changes, that test turns red, so the lab can never quietly measure
  a prompt the fleet no longer uses.
- **Production changes only through promotion** (L6): a separate sprint, with its own law cycle,
  firewall and deploy.
