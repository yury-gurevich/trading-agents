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

---

## 11. The target trio, fewer rounds, and cheaper models (operator, 2026-10-03, second ask)

> *"The pro and con deliberators get the quant data and make their cases, and submit them to the top
> deliberator. He then makes the decision based on their arguments, adding his own opinion as final,
> together with the reasoning why that particular combination of data and market conditions led to
> that particular decision."* Also: test less powerful models, and see whether fewer iterations will do.
> (operator, 2026-10-03)

### What runs today (read from the code, 2026-10-03)

- **A sequential debate.** The defender argues, then the challenger rebuts having read the defender,
  for `max_rounds` = 2 (`agents/deliberator/settings.py`; the pack does not override it). Then the judge
  rules. That makes **5 calls per order, one after another**: D1 → C1 → D2 → C2 → J.
- **All three roles on `claude-opus-5`** at effort `high`. The pack leaves the three `*_MODEL`
  variables empty, so each resolves to the adapter default (`kernel/llm_factory.py`).
- **The judge returns a ruling and a short rationale**, averaging 237 characters. It records no readings
  and no structured basis for its decision.

### The design the operator described: independent briefs and a deciding judge

```text
              packet + glossary (identical for both)
              ┌──────────────┴──────────────┐
              ▼                             ▼
         DEFENDER (pro)               CHALLENGER (con)        in parallel; neither sees the other
         readings → case              readings → case
              └──────────────┬──────────────┘
                             ▼
                 JUDGE (packet + glossary + both cases)
                 1. its own readings of the packet (its own opinion)
                 2. each case's claims checked against the packet: accepted / rejected, and why
                 3. ruling + DECISION BASIS
```

The **decision basis** is a typed record, not prose, so code can check it:

| Field | Content | Checked by |
| --- | --- | --- |
| `decisive_readings` | the metrics that decided it: value, meaning here, direction, weight (high / medium / low) | value against the packet; meaning and direction against the glossary |
| `market_conditions` | regime, VIX and its as-of date, sector context, earnings horizon | values against the packet |
| `accepted` / `rejected` | each side's claims the judge accepted or rejected, with the reason | every claim traces to a case; every reason cites a reading |
| `own_view` | what the judge read that neither side raised | readings not in either case |
| `ruling` + `rationale` | the decision, and why *this combination* of data and conditions leads to it | — |

**This gives the lab its strongest test: is the stated reason the real reason?** Test 3 perturbs each
parameter. If the judge names `rsi_score` as a high-weight decisive reading, moving it should move the
ruling. If moving it changes nothing, while moving a parameter the judge never named does change the
ruling, then the stated basis is a story told afterwards, not the cause. The lab reports this as
**faithfulness**: the agreement between the claimed decisive readings and the measured sensitivity.

**Cost and speed.** This design needs 3 calls instead of 5, and the two briefs run in parallel. The wall
clock is about two calls long instead of five.

**What it gives up, which the lab measures rather than assumes:** the challenger no longer answers the
defender, so a rebuttal cannot expose a weak defence. That is one of the arms below.

### Arms to compare (same case set, same scorers)

**Topology and rounds:**

| Arm | Calls per order | What it tests |
| --- | --- | --- |
| T0 today: sequential debate, 2 rounds | 5 serial | The baseline |
| T1 sequential, 1 round | 3 serial | What the second round adds |
| T2 independent briefs + deciding judge with decision basis | 3, 2 in parallel | The operator's design |
| T3 T2 + one rebuttal each (each side reads the other's brief once) | 5, in 2 parallel pairs | Whether rebuttal earns its cost |

For each arm the report shows what changed: rulings, new readings, and whether any decisive parameter
appeared only in the extra round. If round 2 introduces no new decisive reading and changes no ruling
beyond the noise floor, it is not paying for itself.

**Models, per role.** Prices are per million input / output tokens, read from the Anthropic price list
cached 2026-09-25:

| Model | $ in / out | Notes for the lab |
| --- | --- | --- |
| `claude-opus-5` (today) | 5 / 25 | Champion |
| `claude-opus-5-5` | 4 / 20 | Newer and cheaper than today's. Its effort defaults to `medium`, so the lab sets effort explicitly |
| `claude-sonnet-5-5` | 2 / 10 | The main "less powerful" candidate |
| `claude-haiku-4-5` | 1 / 5 | Smallest. It does **not** accept the `effort` parameter, which our adapter always sends (`kernel/llm_anthropic.py:101`), and its context is 200K. The lab needs a per-model call profile before it can test Haiku |
| `gpt-5.5` (OpenAI) | — | Already wired as the alternative provider; optional arm |

**Effort:** `low`, `medium` and `high` for each model that supports it. A strong model at lower effort
is often a better trade than a weaker model at higher effort, and both are tested.

### How to search without paying for every combination

1. **Quiz as the entry filter (cheap).** Every candidate model takes the comprehension quiz (Test 1)
   with the champion prompt and glossary. A model that does not understand the parameters does not go
   on to deliberate.
2. **Topology at the champion model.** Run T0–T3 on Opus 5 and pick the topology.
3. **Downgrade one role at a time** on the chosen topology. First the two debaters with the judge
   held on Opus, then the judge.
4. **Effort sweep** on the surviving configurations.
5. **Confirm** the winner on real, previously seen cases (§9, decision 4).

**"Up to the job" has a pre-registered bar,** written before the first run. A cheaper configuration
qualifies only if, against the champion on the same cases:

- understood, used, decisive and faithfulness scores are not worse by more than a stated margin
  (beyond the run-to-run noise measured by the repeats);
- the placebo flip rate is not higher;
- expert-case accuracy is not lower;
- cost or latency, or both, are lower.

It passes all four or it fails, as the experiment records here already do.

### What this does not change

The lab **measures** these arms; it does not deploy them. A new topology, a different model per role,
or fewer rounds in production is a separate sprint, with a deliberator law cycle and a
deploy. §10's guarantee holds: nothing that runs today is touched by the lab.

---

## 12. Worked example: the planner took its own quiz (2026-10-03)

The operator asked whether the planner model understands each quant and what a combination means. The
planner answered first from general finance knowledge, then read the code. Where they differ, the
glossary must carry the code's meaning, and the quiz has a seed question:

| Key | The general-finance reading | What our code computes |
| --- | --- | --- |
| `pe = 30` | a P/E ratio of 30 | a 0–100 **sub-score**: 30 is the default band, so P/E > 25 (expensive). 60 means 10–25, and 80 means under 10. A loss-maker has **no** `pe` key at all (`agents/analyst/domain/fundamental_rules.py`) |
| `rsi_score = 25` | weak momentum | RSI ≥ 70: overbought, scored **low on purpose** (contrarian) (`technical_rules.py`) |
| Bollinger position `0.1` | breaking down | near the lower band, scored **75**, bullish (contrarian) |
| `relative_strength` (scanner) | performance against the market | the stock's **own** total return over the scanner window, as a **fraction** (0.12 = +12 %), with no benchmark (`agents/scanner/domain/filters.py:112`) |
| `relative_strength` (analyst) | the same | the stock's trailing return **minus the benchmark's**, in **percentage points**, then banded 20 / 40 / 60 / 80 (`relative_strength.py`) |

**The combination finding.** The technical score is the **average** of contrarian sub-scores (RSI,
Bollinger: low is bullish) and trend-following sub-scores (SMA-200 distance, EMA spread, MACD: up is
bullish). On those five alone:

- A **strong, extended leader** (RSI 75, upper band, 8 % above SMA-200, EMAs and MACD positive)
  scores (25 + 30 + 75 + 75 + 75) / 5 = **56**.
- A **falling knife** (RSI 28, lower band, 8 % below SMA-200, EMAs and MACD negative) scores
  (80 + 75 + 20 + 25 + 25) / 5 = **45**.

The two opposite market situations land 11 points apart, and the composite does not say which one it
is. An expert reading the combination would name the situation ("extended momentum, pullback risk" or
"downtrend with oversold readings"). A reader of `technical_score` alone cannot. So the glossary needs
**combination patterns** as well as single-key definitions, and Test 3 should perturb parameters
*jointly* along these patterns as well as one at a time.

*Caveat:* whether either pattern predicts returns is not shown here. That is EXP-014 and EXP-015's
question, not the glossary's.

---

## 13. The expert's book (operator, 2026-10-03)

> *"Without a book in finance you cannot interpret it."* (operator, after §12)

§12 showed it: general finance knowledge alone misread our keys. The deliberators need a **book**, the
same one for all three roles, versioned like any other part of a prompt variant. It has three parts,
because each has a different source of truth:

| Part | Content | Source of truth | Who writes it |
| --- | --- | --- | --- |
| **I. Dictionary** | Every packet key: what it is, scale and unit, direction for a buy (contrarian bands included), the thresholds our gates use, which pillar it feeds | **The code.** Generated from it, with a test that fails when a key has no entry | Generated (L0) |
| **II. Interpretation** | Named **combination patterns** in our keys: the extended leader, the falling knife, a breakout on volume, the value trap (cheap `pe` with negative growth), quality at a reasonable price, earnings-event risk, high beta in a high VIX, price against sentiment. For each one: the conditions, what it means for the stock in this market, and what a buy decision must weigh | **Finance literature**, cited, and marked *judgement, not yet evidenced* until the replay shows a pattern predicts anything (EXP-014 / EXP-015) | The planner drafts it; **the operator approves each pattern** |
| **III. House rules** | How our gates work and what they cannot see; what counts as a process fact; the operator's policy that a decision rests on quant data (§9) | Laws and ADRs | Derived from the law books |

**How the lab uses it.** The book is an input field, never the instructions, so an optimiser cannot
rewrite it (§4). It sits first in the message with a cache breakpoint after it, so repeated calls read
it from cache. Most importantly, **the book is itself tested**: the same cases are run with no book,
with Part I only, and with Parts I + II, version against version. That measures whether the book
improves understanding, use and faithfulness, and which chapter does it. A chapter that changes
nothing is cut; a pattern the sensitivity test contradicts is corrected or removed.

**Build order change:** L0 becomes *Book Part I (generated) + Part III*, and Part II is drafted
alongside L1 so it is ready for L2's first comparison.

---

## 14. The decision code: laws that help the deliberators decide (operator, 2026-10-03)

> *"We need a set of laws to help the deliberators decide. A harness of a sort."* (operator)

**What exists and what does not.** `agents/deliberator/laws/laws.md` (`DLIB-*`) governs the
deliberator as **software**: its inputs, triggers, outputs, failures and audit. Nothing tells the
**expert** how to decide: what to read, how to weigh it, when a ruling is allowed. The book (§13) says
what things *mean*. The decision code says what the expert *must do* with them, and code checks that it
did.

### The harness

```text
packet + book (I–III) + decision code
                 │
                 ▼
     role writes typed output (readings, case or decision basis, ruling)
                 │
                 ▼
     LAW CHECKER (code, after every call)
        ├─ passes ─────────────────────────────► accepted; laws applied are recorded
        ├─ breaks a FORM law ─► one retry, with the broken clause quoted ─► still broken: recorded violation
        └─ departs from a JUDGEMENT law ─► allowed only with a stated reason; the departure is recorded
```

The LLM still decides. The harness makes sure it decided **lawfully**: on the packet's true values, by
the method, and against the doctrine. It also records each case where it chose to depart.

### Three tiers

**Tier A: form laws.** Code enforces them, and a ruling that breaks one is not accepted.

| ID | Law |
| --- | --- |
| DEC-FORM-01 | Every value read equals the packet's value. |
| DEC-FORM-02 | Every metric read exists in the dictionary (book Part I), and its stated scale and direction match it. |
| DEC-FORM-03 | Every ruling's decision basis contains at least one high-weight quant or sentiment reading (operator policy, §9). |
| DEC-FORM-04 | An `overturn` names at least one high-weight decisive reading that bears **against** the order. |
| DEC-FORM-05 | An `uphold` names the opposing side's strongest claim and why it was rejected. |
| DEC-FORM-06 | No statement about how our system works contradicts book Part III (the S245 class: "calendar days" when the code counts sessions). |

**Tier B: procedure laws.** The expert's method. Code checks that each step is present and consistent.

| ID | Law |
| --- | --- |
| DEC-PROC-01 | Read before arguing: readings come first, and an argument may use only what was read. |
| DEC-PROC-02 | **Pillar sweep:** state the bearing of each pillar (technical, fundamental, relative strength, sentiment, risk and portfolio), or mark it *absent* with the reason. Absence is evidence, not silence. |
| DEC-PROC-03 | Name the combination pattern from book Part II that fits the stock, or say that none fits. |
| DEC-PROC-04 | State the market conditions: regime, VIX level and its as-of date, earnings horizon. |
| DEC-PROC-05 | Contrarian sub-scores (RSI, Bollinger) are read **with** the trend readings, never alone (§12). |
| DEC-PROC-06 | A gap that would change the ruling if filled is named as such. |
| DEC-PROC-07 | The judge addresses each side's strongest claim, adds its own reading, and explains why **this combination** of data and conditions leads to **this ruling**. |

**Tier C: judgement laws.** The doctrine, drafted from cited literature and **approved one by one by
the operator**. Each is marked *judgement, not evidenced* until the replay shows it earns. Its numbers
come from the dictionary's bands, never from the prompt.

| ID | Law (draft) |
| --- | --- |
| DEC-JUDG-01 | **Falling knife.** Below the 200-day average with negative MACD and negative relative strength: oversold readings do not count as support for a buy. |
| DEC-JUDG-02 | **Extended leader.** Overbought and far above the 200-day average: the case must weigh pullback risk against the stop's distance in ATR. |
| DEC-JUDG-03 | **Value trap.** A favourable valuation sub-score with unfavourable growth sub-scores: valuation alone does not support the buy. |
| DEC-JUDG-04 | **Pillars in conflict.** A strong technical case against strongly negative sentiment, or the reverse, cannot be upheld without resolving the conflict explicitly. |
| DEC-JUDG-05 | **Event inside the holding period.** The scanner excludes earnings within 5 days (`earnings_exclusion_days`); earnings later, but inside the expected holding period, must be weighed. |
| DEC-JUDG-06 | **Risk-off.** In a risk-off regime or a high VIX, a high-beta buy needs a stronger case to be upheld. |
| DEC-JUDG-07 | *(parked with item 99)* When the barrier forecast says the stop is likelier first than the target, the case must answer it. |

### How the lab uses the code

- **Compliance:** the rate at which each law is met, per role, model and topology.
- **Consistency:** when a judgement law's conditions hold in a case, did the ruling follow it, or state
  a departure?
- **The code is tested like the book.** The same cases run with no code, Tier A only, A + B, and
  A + B + C. A law that changes nothing is dropped. A law that makes the expert worse on the expert
  cases is revised.
- **Then the money question.** Does following a judgement law improve outcomes? That is the replay's
  question (P17), not the lab's.

### Where it lives, and the wall

The checker engine is substrate (`kernel`), decision-agnostic like `deliberation_eval.py`. The trading
laws are pack data, which keeps ADR-0012's wall. In the lab the code is part of a prompt variant.
Promotion to production is a law cycle: a `DEC-*` clause family, test-plan rows citing each clause ID,
and the same evidence bar as any other law.

### 🪤 One thing the code cannot fix by itself

Under **ADR-0029, only `overturn` blocks an order. A `revise` is a recorded finding and changes nothing
about the trade.** A judgement law whose conclusion is "revise" therefore has no effect on what is
bought. If a law should *reduce* a position rather than block it, `revise` needs an action, such as a
smaller size. That is capital-risk policy, the operator's.
