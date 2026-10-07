<!-- Agent: planning | Role: sprint handover -->
# Sprint 255 — The evidence packet states how the confidence score was computed, from what the analyst and the provider recorded

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-255-the-packet-states-the-score-arithmetic`
**Status:** BUILT
**Build disposition:** BUILT after the planner's correction of 2026-10-07. The original stop and DL-270 stand; the corrected scale clause is pinned by A9 and DRIFT-103 is CLOSED. All local proof is recorded below; the dependency audit is explicitly NOT RUN offline.
**Version:** *next available MINOR at merge*
**Effort:** M
**Decisions:** [DL-269](../design-log.md) (decisions D1 to D7 this sprint builds) · work-queue **107** ·
[DL-264](../design-log.md) and its amendments 5 to 7 (step 2 of the order of work, first of three pieces) ·
[EXP-019](../research/experiments/EXP-019-do-the-debaters-know-what-an-order-hinges-on.md) (the text
this sprint ships is its arm B) · [ADR-0010](../decisions/0010-llm-interaction-quality-gate.md) (a
change to the evidence a model reads is gated)

> **Why this bump kind.** Two records gain what they did not carry: a recommendation states the
> constants its confidence was computed with, and a regime states the thresholds its label was selected
> with. The packet gains a capability built on them.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build**, except the amendments this spec names. A clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: analyst **`ANLZ-OUT`**, **`ANLZ-TYP`**; provider **`PROV-OUT`**; deliberator
**`DLIB-OUT`**, **`DLIB-NEV`**, **`DLIB-OBS`**.

### The rule

1. **Before writing code**, read every law file in the map below, whole file, first time.
2. Read each agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides what this sprint owes.
5. **Write the Law reading record** (at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row (next free: DRIFT-102).
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**The planner's answer: Yes, twice in `contracts/` (both additive) and three guarantees.** Exactly this
is owed, in the same unit of work:

- **`ANLZ-OUT-10`** (new) in `agents/analyst/laws/laws.md`: *"Each recommendation that carries quant
  metrics also records the constants its confidence was computed with (the pillar weights, the
  relative-strength weight, the confidence floor and span) and the names of the sub-scores averaged
  into its technical and fundamental scores."* The book goes to **v1.9**.
- **`PROV-OUT-02`** (amended) in `agents/provider/laws/laws.md`: the regime context also carries *"the
  VIX thresholds its label was selected with"*. The book goes to **v1.9**. If conventions prefer a new
  clause to an amended one, add the next free `PROV-OUT` clause instead and say so.
- **`DLIB-OUT-08`** (new) in `agents/deliberator/laws/laws.md`: *"When the analyst's record carries its
  score arithmetic, each debated order's evidence packet states it: the rule, this order's numbers and
  the regime rule, computed only from recorded values, and only when that rule reproduces the recorded
  confidence. Otherwise the packet says in one line why it is withheld."* The book goes to **v1.14**.
- Each book: a Changelog line naming S255 and DL-269, a `test-plan.md` row per clause, the clause ID in
  the docstrings of the tests that prove it.
- The rollups in **both** `docs/laws/ledger.md` and `docs/laws/INDEX.md`, for all three books. Let
  `make ci` tell you the numbers.
- **`DLIB-NEV-09`** already binds every sentence the packet now states about the code. It is not
  amended: it is obeyed, with a pin per sentence (tests A6, A8, A9).

Edit no other clause. If your reading finds that an existing clause already makes one of these
guarantees, name it in the Law reading record, cite it, and do not add a duplicate.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `contracts/analyst.py`, `agents/analyst/domain/scoring.py`, `recommend.py` | `agents/analyst/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `ANLZ-OUT-03` and `ANLZ-TYP-01` (what a recommendation carries and its types); the new `ANLZ-OUT-10`. **No score, confidence or action may change** |
| `contracts/provider.py`, `agents/provider/agent.py` | `agents/provider/laws/laws.md` + `test-plan.md` | `PROV-OUT-02`: the regime context states the classification and the inputs behind it. The thresholds are part of how it was classified |
| `agents/deliberator/context.py` and the new `context_arithmetic.py` | `agents/deliberator/laws/laws.md` + `test-plan.md` | `DLIB-OUT-07` (the record carries the packet the roles were given); `DLIB-NEV-08` (no verdict for a comparison no agent enforces); `DLIB-NEV-09` (every statement about the code is pinned by a test); the new `DLIB-OUT-08` |
| `agents/deliberator/prompt_recipe.py` | same | `DLIB-OBS-07`: the digest identifies the code that rendered the prompt, so the new module joins it |

⚠️ **The three lines are frozen text.** They are EXP-019's arm B with one clause of the first line
corrected (the planner's correction, below). If a sentence cannot be pinned
to the code as written, or a number cannot be reproduced from the record, stop and report. Do not
reword a line to make it pass.

---

## Goal

At merge, an order whose analyst and provider records carry the new fields is debated on a packet that
ends with three more lines: the rule the confidence is computed by, this order's numbers through that
rule, and what the regime label does and does not change. The lines are byte for byte what EXP-019's
arm B added. Nothing else in the packet moves, no score changes, and an order whose records predate
the fields gets the packet it gets today.

## Why (context)

The operator, 2026-10-06: *"Can we make LLM understand and assign 'weights' to the quant values we
send them … not only the value, but general significance of an indicator in relation of other
indicators."* The packet prints the three pillar scores and the confidence with no weight and no
formula. GILD on `sched-2026-10-05` cleared its floor only on the sentiment score, and its debate
argued about *"an undisclosed mapping"*. This is the first of three pieces of step 2 in
[DL-264](../design-log.md) amendment 5. The other two (the withheld facts, the risk figures) are not
measured yet and are their own sprints.

### Measured, 2026-10-07 — read these before designing

No LLM call. Rows marked *live graph* were measured by the planner with the graph's credentials and
cannot be re-run in a worktree. The Appendix script reproduces the rows marked *Appendix* with no
`.env`.

| Claim | Value | How it was measured |
| --- | --- | --- |
| The arithmetic, in code | technical = 0.80 × (mean of the technical sub-scores / 100) + 0.20 × (`rs_score` / 100); fundamental = mean of the fundamental sub-scores / 100; composite = 0.50 technical + 0.30 fundamental + 0.20 sentiment over the sum of the weights of the pillars present; confidence = 0.30 + 0.60 × composite | *[measured, read]* `agents/analyst/domain/scoring.py` (`score_candidate`, `_apply_relative_strength`, `_composite`), `technical_rules.score_technical`, `fundamental_rules.score_fundamental`, and the defaults in `agents/analyst/settings.py` |
| Whether the fleet changes those constants | no: `orchestration/packs/trading_tunables.json` sets two analyst keys, neither of them one of these | *[measured, read]* |
| Where a deliberator can read the constants today | nowhere. They are tunables in `agents/analyst/settings.py` and `agents/provider/settings.py`; no contract field and no run record carries them, and an agent may not import another | *[measured]* `git grep` over `contracts kernel agents orchestration` |
| The stated rule reproduces the recorded numbers | **1,765 of 1,765** recommendations that carry quant metrics (85 analyst runs, 2026-07-20 to 2026-10-06): recomputed confidence and `technical_score` within 1e-9 of the record; the largest difference is 1.1e-16. Thirteen older recommendations carry no quant metrics | *[measured, live graph]* |
| The same, on the nine orders of EXP-019 | 9 of 9 | *[measured, Appendix]* |
| Lines built from the record against EXP-019 arm B's | **9 of 9 byte-equal**, as first measured. Since the correction: the second and third lines are arm B's byte for byte, and the first is arm B's with one clause inserted, 9 of 9 | *[measured, Appendix]* |
| Which keys ending in `_score` are on a 0-1 scale | exactly four of the 20 recorded: `technical_score`, `fundamental_score`, `sentiment_score`, `composite_score`. The other 16 are band scores, observed between 20 and 80 | *[measured, live graph]* 1,765 recommendations, 2026-10-07 |
| Where arm B put the lines | at the end: its packet is the recorded packet, a newline, the three lines | *[measured, read]* `exp019_run.py` in the experiment's Appendix S |
| Today's code rebuilds the nine recorded packets | 9 of 9 byte-equal | *[measured, live graph]* `build_veto_context` on `main` at `78c9b419` |
| What the lines add | 1,579 to 1,601 characters, to a packet of about 9,500 | *[measured]* the fixture |
| Branches of the scoring, over the 1,765 | no `rs_score`: 946, none since 2026-09-04; no fundamental pillar: 16; no sentiment pillar: 17; the alpha158 pillar: 0 (its weight is 0.00 and the fleet does not set it); most metrics on one recommendation: 56, against a cap of 128 | *[measured, live graph]* |
| The same since 2026-09-20 | 449 recommendations; all 38 buys have three pillars and `rs_score`; 9 holds lack one pillar | *[measured, live graph]* |
| The order the analyst averages fundamentals in | `pe, roe, net_margin, current_ratio, pb, debt_equity, eps_growth, revenue_growth`, which is the order arm B prints | *[measured]* `fundamental_rules._FUNDAMENTAL_RULES` |
| The order `quant_metrics` is recorded in | alphabetical by name | *[measured, read]* `recommend._quant_metrics` sorts |
| The regime rule | `extreme_volatility` from 35, `high_volatility` from 25, `risk_off` from 20, `risk_on` at or below 15, `neutral` otherwise and when the VIX is missing; the four `base_*` values come from settings whatever the label | *[measured, read]* `agents/provider/domain/regime.py`, `agents/provider/agent.py` |
| A reader on older code, given a record with a field it does not know | reads it and ignores the field | *[measured]* `QuantMetric.model_validate` with an extra key |
| Who reads the two records | 14 call sites of `RecommendationSet.model_validate` and `RegimeContext.model_validate` in the analyst, the deliberator, the forecaster, the PM, the provider and `orchestration/` | *[measured]* `git grep`, tests excluded |
| EXP-019 so far | interim, not a verdict: with the lines 45 of 45 answers right; without them 34 of 45, all 11 errors false alarms; 31 of 52 calls made | *[measured 2026-10-06]* the experiment's Appendix R |
| Module sizes | `agents/provider/agent.py` **189**, `agents/analyst/domain/recommend.py` **183**, `scoring.py` **182**, `contracts/provider.py` **176**, `agents/deliberator/context.py` **133**, `context_pm.py` **129**, `contracts/analyst.py` **119** | *[measured]* |
| A model reads the lines as intended on `gpt-5.5` | *[ASSUMED]* EXP-019 runs on Opus. The fleet debates on `gpt-5.5` this week | not measured |

---

## Scope — and what is deliberately NOT here

1. **The failing test first (A1).** The nine recorded orders, each with its recommendation, its
   arithmetic and the regime's thresholds, render the fixture's three lines.
2. **The analyst records its arithmetic** (D1): `Recommendation.score_arithmetic`, written wherever a
   recommendation is built from a score that has metrics. No score, confidence, action, rationale or
   existing metric changes.
3. **The provider records the thresholds** (D2): `RegimeContext.vix_thresholds`, set from the settings
   in force wherever a regime context is built.
4. **The deliberator states the arithmetic** (D3): a new module
   `agents/deliberator/context_arithmetic.py`, called last by `build_veto_context`. Three lines, at the
   end of the packet.
5. **Only when it is true** (D4, D5): the lines are printed when the stated rule reproduces the
   recorded confidence and `technical_score`. Otherwise one line says why they are withheld. A
   recommendation without `score_arithmetic` adds nothing: its packet is today's packet.
6. **Every sentence is pinned** (`DLIB-NEV-09`): tests A6, A8 and A9.
7. **The recipe digest covers the new module** (D7, `DLIB-OBS-07`).
8. **The law cycle**, three books.

### Out of scope (do NOT build this sprint)

- **`pyproject.toml` and `uv.lock`.** Do not touch either. The planner bumps the version at merge.
- **Any other line of the packet**, including the `Portfolio/batch context: unavailable` line and the
  `quant_metrics=` line. Work-queue 98 (the withheld facts) and the risk figures are separate sprints.
- **The role prompts**, `kernel/deliberation_prompts.py`, the guided turn, the DSPy engine and program,
  the judge. Nothing a role is instructed changes.
- **How anything is scored.** If you find a defect in the scoring, report it. Do not fix it here.
- **A typed weight on the debater's turn.** It is step 3 of the order of work and waits for EXP-019.
- **Wording for the branches EXP-019 did not measure:** an order with no `rs_score`, an active alpha158
  pillar, no technical sub-score. They are withheld (D4), not stated.
- **A glossary** of the 73 source-owned keys (work-queue 97 c).
- **EXP-019's scripts and data.** They are frozen.
- **The merge.** It waits for EXP-019's verdict (operator, 2026-10-07). Commit on the branch and hand
  back.

### The road not taken (LAW-06)

- **Hard-code the weights and the sub-score lists in the deliberator**, as the experiment's script did.
  Rejected: the weights are tunables, so a deploy that changes one would make the packet state a false
  rule; and a new indicator in the analyst would fall out of a list kept in another agent.
- **Carry the weights as extra `quant_metrics` entries.** Rejected: it changes the `quant_metrics=`
  line the model already reads, and a weight is not a metric of the ticker.
- **One object on the recommendation set** instead of on each recommendation. Rejected: the sub-score
  names differ by candidate, and the deliberator reads one recommendation.
- **The regime line without its thresholds.** Rejected: it is not the text that was measured.
- **Print "unavailable" for a record that predates the fields.** Rejected: a rebuilt old packet would
  stop being byte-equal to the one that was debated.
- **Recompute silently and print whatever comes out.** Rejected: the rule is a statement about the
  analyst's code, and the cheapest proof that it is true for this order is that it reproduces this
  order's recorded number.

---

## The design decisions — made, and recorded in DL-269

The planner made these and measured each in the Appendix script or on the live graph. **Build them as
written.** Record in `docs/design-log.md` (next free: **DL-270**) only a decision the spec did not
make, or a place where you had to depart from one of these, with the reason.

| # | Decision | Rejected |
| --- | --- | --- |
| D1 | `contracts/analyst.py` gains a frozen `ScoreArithmetic` with nine fields: `technical_weight`, `fundamental_weight`, `sentiment_weight`, `alpha158_weight`, `relative_strength_weight`, `confidence_floor`, `confidence_span`, `technical_sub_scores: tuple[str, ...]`, `fundamental_sub_scores: tuple[str, ...]`. `Recommendation.score_arithmetic: ScoreArithmetic \| None = None`. The names are the `quant_metrics` names that were averaged; the fundamental names are in the order they were averaged | see the road not taken |
| D2 | `contracts/provider.py` gains a frozen `VixThresholds` with `risk_on_at_or_below`, `risk_off_from`, `high_volatility_from`, `extreme_volatility_from`. `RegimeContext.vix_thresholds: VixThresholds \| None = None` | thresholds read in the deliberator: they are the provider's tunables |
| D3 | The deliberator appends three lines to the end of the packet, in this order: the rule, this order's numbers, the regime rule. The text and the number formats are the Appendix script's `arithmetic_lines`: EXP-019's `block` with the scale clause of its first line corrected | a place inside the packet: arm B appended |
| D4 | The lines are printed only if all of these hold, checked in this order; the first that fails is the reason on one line, `Score arithmetic: withheld; <reason>.` (1) the regime record exists: *no regime record*; (2) it carries thresholds: *the regime record carries no label thresholds*; (3) the alpha158 pillar took no part (no `alpha158_score` metric): *the alpha158 pillar is active*; (4) at least one technical sub-score is named and every named sub-score is among the metrics: *the recorded sub-scores are incomplete*; (5) `rs_score` is among the metrics: *this order has no rs_score*; (6) the rule reproduces the record: *the stated rule does not reproduce the recorded confidence_score*. A recommendation with `score_arithmetic` of `None`, or no recommendation, adds no line at all | raising: the builder runs inside the order's fault boundary, so an exception would fail the order open |
| D5 | "Reproduces" means the recomputed confidence and the recomputed `technical_score` are each within `1e-9` of the recorded value | comparing the printed four decimals: it hides a real difference |
| D6 | Both new fields are optional and default to `None`. No reader is changed to require them | a required field: 85 recorded analyst runs would stop validating |
| D7 | `agents/deliberator/context_arithmetic` joins `PROMPT_MODULES` in `agents/deliberator/prompt_recipe.py` | leaving it out: the digest would not move when the text does |

---

## Blast radius — measured 2026-10-07

| What | Detail |
| --- | --- |
| Files changed | `contracts/analyst.py` **119**, `contracts/provider.py` **176**, `agents/analyst/domain/scoring.py` **182**, `agents/analyst/domain/recommend.py` **183**, `agents/provider/agent.py` **189**, `agents/deliberator/context.py` **133**, `agents/deliberator/prompt_recipe.py` **75**. New: `agents/deliberator/context_arithmetic.py`, the tests. Three law books, three test plans, the two rollups. The fixture `tests/fixtures/score_arithmetic_nine_orders.json` is already on the branch |
| Agents affected | the analyst, the provider and the deliberator. No agent imports another |
| Contract change? | yes, additive: one optional field on `Recommendation`, one on `RegimeContext`. The law cycle is owed for both |
| Graph vocabulary change? | no. The fields ride inside payloads the graph already stores |
| New env keys / tunables | none |
| Deploy implication | image-only retag. Any order of apps works: an agent on older code ignores a field it does not know (measured). Until the analyst and the provider run the new code, records carry no new field and every packet is today's packet |
| Rollback | retag the fleet to the tag it ran before. Records written meanwhile keep their extra fields, which older code ignores. Nothing beyond the retag |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Run the Appendix script** in your worktree and paste its output into the Closeout. It must print
   `lines equal to the fixture's 9, second and third lines equal to EXP-019 arm B's 9, rule reproduces the
   recorded confidence and technical_score 9`.
   If it does not, stop and report: your tree differs from the one this spec was measured in.
3. **Plant the failing test first** (A1) and watch it fail. Paste the red output.
4. **Implement** D1 to D7.
5. **Law cycle:** three books, their test plans, both rollups.
6. **Prove the guards can fail (DL-70):** break each guarded property, watch the guard go red, restore.
7. **`make ci`**, every step of the `ci:` target, **redirected to a file, never piped**. Name any step
   your sandbox cannot run as NOT RUN.
8. **Fill the handback sections** at the bottom of this file and set Status to `BUILT`, here and in
   this sprint's `README.md` row.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 The nine recorded orders render the measured text | The fixture: each order's recommendation with its `score_arithmetic`, its floor, and the thresholds | The deliberator's three lines equal `arithmetic_lines` in the fixture, 9 of 9, compared as whole strings (`DLIB-OUT-08`) |
| A2 | The lines are the end of the packet and move nothing else | A lineage in the in-memory store whose records carry both fields; the same lineage without them | The packet with the fields is the packet without them, a newline, and the three lines (`DLIB-OUT-08`, `DLIB-OUT-07`) |
| A3 | A record that predates the fields gets today's packet | A recommendation with `score_arithmetic` of `None`; and no recommendation for the ticker | No new line; the packet equals what `main` builds for the same lineage (`DLIB-OUT-08`) |
| A4 | Each reason is withheld in one line | One planted record per condition (1) to (6) of D4, including a recorded confidence moved by `2e-9` | Exactly one line, `Score arithmetic: withheld; <that reason>.`, none of the three lines, and no exception (`DLIB-OUT-08`, `DLIB-NEV-09`) |
| A5 | The analyst records what it used | Candidates scored on planted bars, fundamentals and news, under the default settings and under settings with every one of the seven constants moved | `score_arithmetic` holds the seven constants in force; `technical_sub_scores` is exactly the sub-scores `score_technical` averaged; `fundamental_sub_scores` is exactly those `score_fundamental` averaged, in its order (`ANLZ-OUT-10`) |
| A6 | 🪤 The stated rule is the analyst's rule | The analyst's own output for candidates with three pillars, with no fundamentals, and with no news, under default and moved weights | For each, the deliberator's recomputation is within `1e-9` of the analyst's confidence and `technical_score`, and the lines are printed, not withheld (`DLIB-NEV-09`, `ANLZ-OUT-10`) |
| A7 | The provider records the thresholds it used | A regime built under default and under moved thresholds, with a VIX on each side of each threshold | `vix_thresholds` holds the four values in force, and the label is the one those values select (`PROV-OUT-02`) |
| A8 | 🪤 The regime sentences are true | Regimes under every label; one candidate scored under two different regime labels | The four `base_*` values are equal under every label; the candidate's confidence and scores are equal under both labels (`DLIB-NEV-09`) |
| A9 | 🪤 The remaining sentences are true | The analyst's neutral constants; recommendations on each side of the floor; the analyst's own output for the candidates of A6 | A band score of 50 is the analyst's neutral value; an order is a buy only when its confidence is at least `base_min_confidence`; **every recorded key ending in `_score` is either one of the four the first line names, with a value between 0 and 1, or a band score between 0 and 100** (`DLIB-NEV-09`) |
| B1 | 🪤 Every reader reads an old record and a new one | A recorded payload without the fields and the same payload with them, for `RecommendationSet` and `RegimeContext` | Both validate; the PM's, the forecaster's and the provider's existing tests pass with no edit |
| B2 | 🪤 The recipe digest follows the new module | The module's source, then a changed copy | The deliberator's digest differs; the operator agent's digest does not (`DLIB-OBS-07`) |
| B3 | No score moves | The analyst's existing tests | They pass with no edit to an expected score, confidence, action or rationale |
| B4 | Nothing a role is instructed moves | `kernel/deliberation_prompts.py`, the guided turn, the DSPy engine and program | `git diff` against `main` is empty for them; S254's parity tests pass with no edit |

No test may skip when a dependency is missing. A skipped proof is not a proof.

---

## Success factors

- [x] The nine recorded orders render the corrected fixture byte for byte; their second and third lines equal EXP-019 arm B's (A1).
- [x] The three lines are the end of the packet, and every earlier line is unchanged.
- [x] A recommendation without `score_arithmetic` gets today's packet.
- [x] Each of the six conditions withholds the lines in one line that names it, and never raises.
- [x] The analyst records the seven constants in force and the sub-scores it averaged; no score moves.
- [x] The provider records the four thresholds in force.
- [x] Every sentence of the three lines has a pin that fails when the code it describes changes.
- [x] The recipe digest covers the new module; the operator agent's digest does not move.
- [x] `pyproject.toml`, `uv.lock`, the role prompts and the DSPy modules are untouched.
- [x] Law cycle done in three books, or an existing clause named in a new one's place.
- [x] Every new guard planted, watched to fail, restored, stated per guard.
- [x] Every touched module < 200 lines (final measured counts and size/format gates below).
- [x] `make ci` exit 0, 100.00 % coverage, or each step that could not run named as NOT RUN.

---

## Traps

🪤 **Four modules are within 25 lines of the block.** `agents/provider/agent.py` is at 189,
`recommend.py` at 183, `scoring.py` at 182, `contracts/provider.py` at 176. Put new code in a new
module where one of them would pass 200. Do not compress code to fit.
🪤 **`quant_metrics` is recorded sorted by name.** The order of the fundamental names in the lines is
the analyst's rule order, not alphabetical. Take it from `score_arithmetic`, never from the metrics.
🪤 **`technical_score` is the blended value.** The technical sub-scores' mean is not the score: the
relative-strength blend comes after it, and the analyst bounds both to the range 0 to 1.
🪤 **A pillar can be absent.** The composite then divides by the weights of the pillars present, and
the order's line leaves the absent pillar out. EXP-019's nine orders all have three pillars, so the
fixture does not exercise this: test A6 does.
🪤 **Number formats are part of the frozen text.** Weights and the two confidence constants print with
two decimals, scores with four, the floor with three, the margin with a sign and four, sub-scores and
thresholds with `g`. Copy the Appendix's format strings.
🪤 **`contracts/` may not import an agent, and an agent may not import another.** The pins that
compare the analyst with the deliberator live in `tests/`, which may import both.
🪤 **A lineage with no regime node exists.** `regime_context` returns `None` then. That is condition
(1) of D4, not an exception.
🪤 **The packet builder must not raise.** It runs inside the order's fault boundary: an exception fails
the order open, which is the opposite of what a missing number deserves.
🪤 **An existing test may assert a whole packet.** If one fails because a planted lineage now carries
the new fields, the planted record is wrong, not the expected packet. Name every existing test you
edit, with the reason.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: `kernel.tunable(..., why=...)` with bounds. This sprint adds no tunable. The
  `1e-9` of D5 is a float-equality tolerance, named as a module constant with its reason.
- Faults, not silent failure: `kernel.fault_boundary`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Secrets never through the worktree. A worktree has **no `.env`**, and nothing here needs one.
  **State which tree you ran in.**

---

## Sequencing after merge

Owed by the planner, in this order:

1. Review against the checklist; Windows `make ci`, all steps; push the branch; **`make gate-ran` exits
   0** from the worktree whose `HEAD` is the commit being proven; the branch's open CodeQL alerts
   compared with `sprint-254-each-debater-turn-is-run-by-dspy`'s 127.
2. **The merge waits for EXP-019's verdict** (operator, 2026-10-07). The experiment resumes on Opus
   when that account is funded; the operator approved its remaining $2.80. A second run of the same
   frozen cases on `gpt-5.5` is proposed in [DL-264](../design-log.md) amendment 7 and not yet funded.
3. Merge, the MINOR bump, the tag.
4. **F1, before any retag, no cost.** The merged code rebuilds the nine recorded packets from the live
   graph: 9 of 9 byte-equal to the recorded ones, because those records predate the fields.
5. **Deploy:** image-only retag, with whatever else is owed then. The rollback tag is recorded.
6. **F2, the first scheduled night after the retag.** Every recommendation carries `score_arithmetic`
   and the regime carries its thresholds; the rule reproduces every recommendation's confidence; each
   debated order's recorded packet ends with the three lines and none is withheld; no order fails open.
   The packet is about 1,600 characters longer, so the output tokens of each turn are read against the
   8,192 cap (work-queue 111).

---

## Planner's correction, 2026-10-07 20:35 AEDT — and how the build resumes

**The defect was the spec's, and before that the experiment's.** The first of the three lines said that
inside `quant_metrics` *each key ending in `_score`* is a 0-100 band score. The planner wrote that
sentence for EXP-019's arm B and carried it into this spec as frozen text without checking it against the
keys. Four keys ending in `_score` are on a 0-1 scale. The builder found it while pinning the sentence
and stopped, as the handover told it to ([DL-270](../design-log.md), DRIFT-103).

**Measured after the stop, on the live graph:** over 1,765 recorded recommendations there are 20 distinct
keys ending in `_score`. Exactly four never exceed 1.0: `technical_score`, `fundamental_score`,
`sentiment_score` and `composite_score`. The other 16 are band scores, observed between 20 and 80.

**The correction.** One clause is inserted in the first line, after *"is a 0-100 band score in which 50
is neutral"*:

```text
, except technical_score, fundamental_score, sentiment_score and composite_score, which are on a 0-1 scale
```

Nothing else in the three lines changes. The second and third lines are EXP-019's byte for byte.

**What the planner changed on this branch:** the fixture (`arithmetic_lines` carries the corrected first
line; `exp019_arm_b_lines` keeps the experiment's text); the Appendix script and its expected output;
decision D3's wording; test A9, which now also pins the corrected clause; the Measured table.

**What stands from the first pass, and is not redone:** the Law reading record, DRIFT-102, DL-270, A1's red
run, and the partial prototype in the worktree.

**The stop rule, made narrower.** Stop when a sentence is *false* in the code, as this one was. A pin that
is true but indirect is not a reason to stop: write it, say in Return notes why it is the best pin the
code allows, and continue. For *"50 is neutral"*: the analyst's `_NEUTRAL` constants are 50, and
`signal_selection` gives a band score of 50 a contribution of zero; for `rs_score`, 50 / 100 is the
neutral 0.50 of a pillar.

**The gate.** The corrected line is not the line EXP-019 and EXP-020 measured. Whether the corrected text
is measured again before the merge is the operator's decision, and it does not hold the build.

### Resume — paste this to Codex

```text
Sprint 255, resumed. Same worktree and branch: ../ta-s255,
sprint-255-the-packet-states-the-score-arithmetic. The planner has committed on top of your 97697370:
pull nothing, read `git log -3` and the spec's section "Planner's correction". Your stop was right. The
sentence was false, and it was the planner's: four keys ending in _score are on a 0-1 scale
(technical_score, fundamental_score, sentiment_score, composite_score; measured over 1,765 recorded
recommendations).

The first line now carries one more clause, after "is a 0-100 band score in which 50 is neutral":
  , except technical_score, fundamental_score, sentiment_score and composite_score, which are on a 0-1 scale
Nothing else in the three lines changed. The fixture's `arithmetic_lines` is the corrected text, so your
A1 is red again until your renderer prints the clause. The Appendix script is corrected: run it again and
paste its output; it must print three nines.

Everything from your first pass stands and is not redone: the Law reading record, DRIFT-102, DL-270,
A1's first red run, and your uncommitted prototype, which the planner did not touch.

Continue from Step 4 of the spec (implement D1 to D7), then Steps 5 to 8. Test A9 now also pins the
corrected clause: every recorded key ending in _score is either one of those four, with a value between
0 and 1, or a band score between 0 and 100. Close DRIFT-103 in the register when A9 passes.

The stop rule is narrower now: stop when a sentence is FALSE in the code. A pin that is true but
indirect is not a reason to stop: write it, say why in Return notes, continue. For "50 is neutral" pin
the analyst's _NEUTRAL constants and signal_selection's zero contribution at 50; for rs_score, 50 / 100
is the neutral 0.50.

Unchanged rules: no network, no .env, do not touch pyproject.toml or uv.lock, do not push, do not merge,
no LLM call in any test, no prompt and no other packet line changes, no score changes. New: do not edit
docs/STATE.md again; put intent and results in the spec's Closeout. Set Status to BUILT (spec and README
row) only when the 12-item checklist is met.
```

---

## Handover — paste this to Codex

```text
Sprint 255 — the evidence packet states how the confidence score was computed, from what the analyst
and the provider recorded. Spec:
docs/sprints/sprint-255-the-packet-states-the-score-arithmetic.md on main (read ALL of it, then
CLAUDE.md). Repo: yury-gurevich/trading-agents, local checkout.

Your worktree already exists: ../ta-s255, on branch sprint-255-the-packet-states-the-score-arithmetic,
cut from main, with its venv synced to the lock. The planner has committed one file on the branch:
tests/fixtures/score_arithmetic_nine_orders.json. Work only there, never in the main checkout and
never on main. You have no .env and no network: every proof is a unit test, and no test calls an LLM.
`uv run` is safe. Do not touch pyproject.toml or uv.lock, and say so: the planner bumps the version at
merge. Do not push and do not merge: commit on the branch and hand back. The merge waits for an
experiment's verdict. If a make ci step cannot run in your sandbox (the dependency audit needs the
network), do not bypass it silently: name the step as NOT RUN in the handback.

This handover is complete: nobody will send you follow-up messages. Two tiers:
- A wrong command, count, path or clause number whose intent is plain from the spec's Scope and
  Success factors is NOT a reason to stop: follow the intent, record the correction in Return notes,
  continue.
- STOP and report, without improvising, when: one of the three lines cannot be rendered byte for byte
  from the record; a sentence of them cannot be pinned to the code as written; any score, confidence
  or action would change; a law contradicts the spec; or the Appendix script does not print 9 and 9.

What and why: the packet prints three pillar scores and a confidence with no weight and no formula,
and a debate argued about "an undisclosed mapping". An experiment (EXP-019) is measuring whether
three more lines fix that: the rule, this order's numbers through the rule, and what the regime label
does not change. This sprint makes production able to print exactly those lines. The constants the
lines need are tunables of the analyst and the provider, and the deliberator may import neither, so
each of those agents first records what it used. The planner measured it: built from the recorded
recommendations, the lines equal the experiment's for 9 of 9 orders, and the rule reproduces the
recorded confidence for 1,765 of 1,765 recommendations.

MUST RULE before any code: read, whole, the laws.md and test-plan.md of the analyst, the provider and
the deliberator, docs/laws/conventions.md, docs/laws/drift-register.md, and DL-269 and DL-264
(amendments 5 to 7) in docs/design-log.md. Fill the Law reading record first. Law-cycle answer: YES.
Owed: ANLZ-OUT-10 (new, analyst v1.9), PROV-OUT-02 amended (provider v1.9), DLIB-OUT-08 (new,
deliberator v1.14), each with a Changelog line naming S255 and DL-269, a test-plan row, the clause ID
in the proving tests' docstrings, and both rollups (docs/laws/ledger.md and docs/laws/INDEX.md). The
wording of each clause is in the spec. Edit no other clause. DLIB-NEV-09 is obeyed, not amended.

Order (the spec's Steps): laws -> run the Appendix script (must print 9 and 9) -> plant A1, watch it
fail, paste the red -> implement -> law cycle -> break and restore every guard -> make ci to a file.

Build (decisions D1-D7 are made; build them as written, the Appendix script is the reference):
1. contracts/analyst.py: frozen ScoreArithmetic (seven floats, two tuples of names) and
   Recommendation.score_arithmetic, optional, default None. The analyst sets it wherever it builds a
   recommendation from a score that has metrics: the seven constants from the settings in force, the
   technical sub-score names that score_technical averaged, the fundamental sub-score names that
   score_fundamental averaged, in its order. No score, confidence, action, rationale or metric
   changes.
2. contracts/provider.py: frozen VixThresholds (four floats) and RegimeContext.vix_thresholds,
   optional, default None. The provider sets it from the settings in force wherever it builds a
   regime context.
3. agents/deliberator/context_arithmetic.py (new): given the recommendation, the regime and the
   ticker, return the three lines, or one withheld line, or nothing (decision D4, conditions in that
   order, reasons as written). The self-check of D5 uses 1e-9 on confidence and technical_score.
   build_veto_context calls it last. The text and the number formats are the Appendix's.
4. agents/deliberator/prompt_recipe.py: the new module joins PROMPT_MODULES.
5. Tests A1-A9 and B1-B4 from the spec's Test plan, each citing its clause. The pins that compare the
   analyst's code with the deliberator's text live in tests/, which may import both agents.

DO NOT: reword, reorder or reformat any of the three lines; change any other line of the packet;
change how anything is scored; touch the role prompts, the guided turn, the DSPy engine or program,
the judge, or EXP-019's scripts; make either new field required; let the packet builder raise; import
one agent from another; state a rule for an order with no rs_score or with the alpha158 pillar active
(withhold instead); pin a version number.

Handback checklist (the handback is returned against these, one by one):
 1. Law reading record filled before the first code change.
 2. The Appendix script's output pasted, with the tree it ran in.
 3. A1's red output pasted, from before the implementation.
 4. Test plan results: one row for each of A1-A9 and B1-B4, with file, status and clause.
 5. Every guard's break-and-restore stated, one line per guard.
 6. ANLZ-OUT-10 and v1.9; PROV-OUT-02 amended and v1.9; DLIB-OUT-08 and v1.14; three Changelog lines;
    test-plan rows; both rollups; no other clause edited.
 7. This prints nothing, and you say so:
    git diff main -- pyproject.toml uv.lock kernel/deliberation_prompts.py kernel/deliberation_program.py kernel/dspy_engine.py agents/deliberator/guided_turn.py
 8. The output of the A1 test pasted: 9 of 9 orders equal.
 9. Every EXISTING test file you edited, named, with the reason for each edit. "None" if none.
10. The JSON size of one recommendation's score_arithmetic, in bytes, measured on a fixture order.
11. make ci output file named, exit code stated, every NOT RUN step named with its reason.
12. Module line counts for every touched module; Status BUILT here and in the README row.
State anything not met as "not done" or "verified failing". Never write a Result for work not done.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| Analyst contracts and score/recommendation construction | `agents/analyst/laws/laws.md` and `test-plan.md`, whole files (LOCKED v1.8); `docs/laws/conventions.md` and `drift-register.md`, whole files | `ANLZ-OUT-02`, `ANLZ-OUT-03`, `ANLZ-TYP-01`, `ANLZ-IDM-01`, `ANLZ-NEV-03`; new `ANLZ-OUT-10` | No duplicate guarantee exists. Record the settings and the actual averaged sub-score names without changing existing values. `ANLZ-OUT-07/08` and `ANLZ-OBS-01/02/03` remain gray; this sprint does not claim their full proof. |
| Provider contract and regime construction | `agents/provider/laws/laws.md` and `test-plan.md`, whole files (LOCKED v1.8) | `PROV-OUT-02`, `PROV-NEV-07`, `PROV-FAIL-01` | Amend only `PROV-OUT-02` to include the thresholds used. Its existing proof is green; `PROV-TYP-01` remains gray. |
| Deliberator packet and recipe digest | `agents/deliberator/laws/laws.md` and `test-plan.md`, whole files (LOCKED v1.13) | `DLIB-OUT-07`, `DLIB-NEV-05/08/09`, `DLIB-OBS-07`; new `DLIB-OUT-08` | The existing clauses are green or structural, but none promises the arithmetic lines. Add the named clause and pin every code statement in tests that may import both agents. |
| Decisions and workflow | `docs/design-log.md`: DL-269 and DL-264 amendments 5, 6 and 7; sprint brief whole; worktree `CLAUDE.md` and `AGENTS.md`; docs, sprints and laws indexes | D1-D7, LAW-02, LAW-06 | Follow the decided design. Work only in `../ta-s255`; no network, LLM, version edit, push or merge. Active tracker is `docs/STATE.md`. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** YES: two additive optional contract fields and three named guarantees. Owed: analyst v1.9 / `ANLZ-OUT-10`, provider v1.9 / amended `PROV-OUT-02`, deliberator v1.14 / `DLIB-OUT-08`, three Changelog lines, cited test-plan rows and both rollups. `DLIB-NEV-09` is obeyed, not amended.

**Contradictions found between a law and this spec:** Initial book reading found no contradictory scoped amendment. Source pinning then found that the original frozen first line cannot satisfy `DLIB-NEV-09`: it describes every `quant_metrics` key ending in `_score` as a 0-100 band with neutral 50, but the code also records normalized pillar scores under such keys (neutral 0.50). This triggered the original explicit STOP; see DL-270 / DRIFT-103. On resume the planner corrected the clause, A9 pins it and DRIFT-103 is CLOSED. The short AGENTS gate count is 14, while CLAUDE and the actual `ci:` target name 15; use the target. The element map's `ANLZ-OUT-03` governs rejection; the recommendation fields are in `ANLZ-OUT-02` and `ANLZ-TYP-01`.

**Laws found silent where a decision was needed:** The current books do not require recorded score constants, recorded VIX thresholds, or their packet rendering. D1-D7 settle that silence; DRIFT-102 records the three additions. No additional design choice has been made before code.

**Reading boundary:** This record was written before the Appendix extraction, A1 or any source/test change. The worktree started clean at `41af388f6beac807b91854e6206dcc941fbfdd5b` (planner fixture); local `main` and `origin/main` were `ace8d6289484f4bb6f707725db171fb0e2531e8a`. `.env` is absent. `pyproject.toml` and `uv.lock` are explicitly excluded; the planner owns the bump at merge.

**Clauses that were ⬜ and are now proven:** No existing gray clause was promoted. New `ANLZ-OUT-10` and `DLIB-OUT-08` are authored and proven green; amended `PROV-OUT-02` is re-proven and remains green. All unrelated gray clauses stay gray.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_nine_orders_render_the_measured_text` | `tests/test_score_arithmetic.py` | PASS: 9 of 9 whole blocks | `DLIB-OUT-08` |
| A2 | `test_arithmetic_is_appended_without_changing_an_earlier_line` | `tests/test_score_arithmetic.py` | PASS: whole prefix unchanged | `DLIB-OUT-08, DLIB-OUT-07` |
| A3 | `test_old_and_missing_recommendations_keep_the_main_packet` | `tests/test_score_arithmetic.py` | PASS: both frozen main packets | `DLIB-OUT-08` |
| A4 | `test_each_failed_condition_withholds_one_line; test_first_failed_condition_wins_and_old_records_add_nothing; test_small_unrounded_differences_are_within_the_tolerance; test_partial_lineage_withholds_without_moving_existing_lines` | `tests/test_score_arithmetic_guards.py` | PASS: 15 cases, no exception | `DLIB-OUT-08, DLIB-NEV-09, DLIB-OUT-07` |
| A5 | `test_analyst_records_every_constant_and_the_actual_mean_order; test_each_recommendation_path_keeps_the_scored_arithmetic; test_a_stop_sale_with_short_history_records_constants_and_empty_means` | `tests/test_score_arithmetic_analyst.py` | PASS: all seven constants moved; real means and all construction paths | `ANLZ-OUT-10, ANLZ-IDM-01` |
| A6 | `test_the_packet_formula_reproduces_real_analyst_outputs` | `tests/test_score_arithmetic_analyst.py` | PASS: default/moved x all pillars/no fundamentals/no sentiment/neither | `DLIB-NEV-09, ANLZ-OUT-10` |
| A7 | `test_provider_records_the_thresholds_at_every_classification_boundary` | `tests/test_score_arithmetic_regime.py` | PASS: 26 RPC regimes, default/moved boundaries and missing VIX | `PROV-OUT-02` |
| A8 | `test_all_regime_labels_keep_the_same_four_policy_constants; test_vix_and_regime_labels_do_not_change_real_analyst_scores` | `tests/test_score_arithmetic_regime.py` | PASS: all labels and actual batch scoring | `DLIB-NEV-09, PROV-NEV-07` |
| A9 | `test_band_neutral_constants_and_zero_signal_contribution_are_fifty; test_neutral_bands_and_rs_fifty_normalize_to_a_neutral_pillar; test_buy_admission_is_inclusive_at_the_regime_confidence_floor; test_recorded_score_keys_obey_the_corrected_four_exceptions` | `tests/test_score_arithmetic_pins.py` | PASS: 7 cases; all fixture and A6 score keys; corrected clause; DRIFT-103 CLOSED | `DLIB-NEV-09, ANLZ-OUT-02` |
| B1 | `test_old_and_new_recommendation_sets_and_regimes_validate; test_arithmetic_and_threshold_records_are_frozen_and_finite; existing PM, forecaster and provider suites` | `tests/test_score_arithmetic_compat.py; agents/portfolio_manager/tests; agents/forecaster/tests; agents/provider/tests` | PASS: old/new records; existing unit suites in full CI, no edits; live checks excluded below | `ANLZ-OUT-10, PROV-OUT-02, DLIB-OUT-08` |
| B2 | `test_arithmetic_source_changes_only_the_deliberator_recipe` | `tests/test_score_arithmetic_compat.py` | PASS: deliberator changes, operator stable | `DLIB-OBS-07` |
| B3 | `existing analyst suite, including test_sufficient_history_scores_from_technical_composite and test_score_candidate_reports_insufficient_history` | `agents/analyst/tests/test_analyst_domain.py; agents/analyst/tests` | PASS: full CI; no existing test or expectation edited | `ANLZ-IN-05, ANLZ-IDM-01; new capture proof ANLZ-OUT-10` |
| B4 | `test_the_system_message_is_byte_identical_to_dspys; test_the_user_message_is_byte_identical_to_dspys; existing S254 turn parity suite` | `tests/test_deliberation_guided.py; agents/deliberator/tests/test_dspy_turn_parity.py` | PASS: full CI, no edits; protected diff empty | `DLIB-OUT-06, DLIB-OBS-06, DLIB-NEV-09` |

**Tests added beyond the plan:** The same A4/A5/A6 obligations also cover a zero denominator, both missing optional pillars, the inclusive unrounded tolerance, partial scan/market lineage, every buy/hold/sell path and a forced stop sale with short history. B1 additionally proves the frozen finite constants. None of the 48 sprint cases skips, uses credentials, performs network I/O or calls a model. All nine Python test/support modules and the frozen main-packet fixture are new to this branch. No existing tracked test file was edited.

---

## Closeout — evidence

**Status:** BUILT — the twelve-item handback is met with the handover's explicit offline exception for the dependency audit. This is a local branch build; `make ci` does not exit 0 while that audit is unavailable.

**Resume intent (2026-10-07):** Continue the retained D1-D7 prototype on planner commit `8195b21b`, without a pull, network, `.env`, model call, version edit, push or merge. Preserve the law reading record, DRIFT-102, DL-270, original A1 red and prototype; finish the remaining tests, named law cycle, break/restore guards and redirected gate. Intent and results are here; `docs/STATE.md` was not edited again.

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\ta-s255`, branch `sprint-255-the-packet-states-the-score-arithmetic`. `.env` is absent. Final Python proof processes set `UV_OFFLINE=1`, `UV_NO_SYNC=1`, `PYTHONUTF8=1`, `PYTHON_DOTENV_DISABLED=1`; a local ignored `sitecustomize` blocks external DNS/connect before access. All data and clients are fixtures or injected fakes. No external feed, database, LLM or remote gate was called.

**Result:** D1-D7 are implemented. The analyst captures seven constants and the actual ordered mean names; every recommendation construction path carries that record. The provider captures its four active thresholds. The packet appends the corrected three lines only after confidence and blended technical score reproduce within `1e-9`; otherwise it appends exactly the first withheld reason. Old packets and existing scores, actions, rationales and metrics are unchanged. The corrected Appendix prints three nines; A1 prints 9 of 9 orders equal; all 48 sprint cases pass; all 27 mutations go red and restore exact bytes; the full suite passes at 100.00% coverage. DRIFT-102 is CORRECTED and DRIFT-103 is CLOSED.

**Files changed in the resumed build:** Production: `contracts/analyst.py`, `contracts/provider.py`, `agents/analyst/domain/scoring.py`, `agents/analyst/domain/recommend.py`, new `agents/analyst/domain/score_arithmetic.py`, `agents/provider/agent.py`, new `agents/provider/regime_arithmetic.py`, `agents/deliberator/context.py`, `agents/deliberator/prompt_recipe.py`, new `agents/deliberator/context_arithmetic.py`. Proof: the nine Python test/support modules measured below and new `tests/fixtures/score_arithmetic_main_packets.json`. Law cycle: the three books and test plans, `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md`. Handback: this spec and `docs/sprints/README.md`. The corrected nine-order fixture is the planner's committed file and was not edited by the builder. `docs/design-log.md` and `docs/STATE.md` are unchanged in this resumed pass.

**Design decisions:** D1-D7 remain [DL-269](../design-log.md). [DL-270](../design-log.md) retains the initial stop and rejected workarounds. The planner's corrected clause is implemented verbatim. Return notes explain the true but indirect pins. No additional scoring or policy decision was made.

**Appendix output, resumed:** Extracted without edits from this spec into `.tools/s255/reference-resumed.py`; `PYTHONPATH=.`, `uv run --no-sync python .tools/s255/reference-resumed.py`, exit 0 in the tree above.

```text
orders 9: lines equal to the fixture's 9, second and third lines equal to EXP-019 arm B's 9, rule reproduces the recorded confidence and technical_score 9
```

**Original A1 red, retained from before implementation:** `uv run --no-sync pytest tests/test_score_arithmetic.py --no-cov -q -s`, exit 1. This run was not redone.

```text
F
================================== FAILURES ===================================
__________________ test_nine_orders_render_the_measured_text __________________
tests\test_score_arithmetic.py:23: in test_nine_orders_render_the_measured_text
    from agents.deliberator.context_arithmetic import arithmetic_lines
E   ModuleNotFoundError: No module named 'agents.deliberator.context_arithmetic'
=========================== short test summary info ===========================
FAILED tests/test_score_arithmetic.py::test_nine_orders_render_the_measured_text
1 failed in 12.20s
```

**Corrected-clause A1 red on resume:** The unchanged prototype failed the planner's corrected fixture before the renderer clause was added; same command, exit 1.

```text
F
================================== FAILURES ===================================
__________________ test_nine_orders_render_the_measured_text __________________
tests\test_score_arithmetic.py:42: in test_nine_orders_render_the_measured_text
    assert actual == order["arithmetic_lines"], order["ticker"]
E   AssertionError: TGT
E   assert 'Score arithm...to any score.' == 'Score arithm...to any score.'
E
E     Skipping 225 identical leading characters in diff, use -v to show
E     - is neutral, except technical_score, fundamental_score, sentiment_score and composite_score, which are on a 0-1 scale; technical_score = 0.80 x (mean of the technical sub-scores / 100) + 0.20 x (rs_score / 100); fundamental_score = (mean of the fundamental sub-scores) / 100; composite_score = 0.50 x technical_score + 0.30 x fundamental_score + 0.20 x sentiment_score, divided by the sum of the weights of the pillars that are present; confidence = 0.30 + 0.60 x composite_score; a pillar score of 0.50 is neu...
E
E     ...Full output truncated (6 lines hidden), use '-vv' to show
=========================== short test summary info ===========================
FAILED tests/test_score_arithmetic.py::test_nine_orders_render_the_measured_text
1 failed in 4.16s
```

**Final A1 output:** `uv run --no-sync pytest tests/test_score_arithmetic.py::test_nine_orders_render_the_measured_text --no-cov -q -s`, exit 0.

```text
9 of 9 orders equal
.
1 passed in 1.99s
```

**All sprint proofs:** The six `tests/test_score_arithmetic*.py` files, `--no-cov -q -s`, exit 0; zero skipped cases.

```text
9 of 9 orders equal
................................................
48 passed in 3.94s
```

**Law cycle:** Analyst LOCKED v1.9 / new `ANLZ-OUT-10` (**29 / 52**); provider LOCKED v1.9 / amended `PROV-OUT-02` (**24 / 67**, unchanged count); deliberator LOCKED v1.14 / new `DLIB-OUT-08` (**29 / 61**). Each has its S255 / DL-269 Changelog entry and cited green test-plan row; both rollups agree. `uv run --no-sync python scripts/check_law_coverage.py` exited 0. The law diff changes only the three named clauses, book versions and Changelog entries. `DLIB-NEV-09` and every other clause are unchanged.

**Every new guard and source pin, break → red → exact-byte restore:** `.tools/s255/prove-guards.py` and `prove-pins.py`, each exit 0. One actual result line per property follows; each red run is logged at `.tools/s255/guard-<name>-red.txt`.

```text
no_recommendation: planted red exit 1; exact bytes restored
no_arithmetic: planted red exit 1; exact bytes restored
regime: planted red exit 1; exact bytes restored
thresholds: planted red exit 1; exact bytes restored
alpha: planted red exit 1; exact bytes restored
empty_technical: planted red exit 1; exact bytes restored
incomplete_names: planted red exit 1; exact bytes restored
rs: planted red exit 1; exact bytes restored
confidence_check: planted red exit 1; exact bytes restored
technical_check: planted red exit 1; exact bytes restored
zero_denominator: planted red exit 1; exact bytes restored
tolerance_too_wide: planted red exit 1; exact bytes restored
tolerance_too_narrow: planted red exit 1; exact bytes restored
recorded_constants: planted red exit 1; exact bytes restored
fundamental_order: planted red exit 1; exact bytes restored
present_pillar_divisor: planted red exit 1; exact bytes restored
recorded_thresholds: planted red exit 1; exact bytes restored
risk_on_boundary: planted red exit 1; exact bytes restored
regime_policy_invariance: planted red exit 1; exact bytes restored
vix_score_independence: planted red exit 1; exact bytes restored
band_neutral: planted red exit 1; exact bytes restored
inclusive_buy_floor: planted red exit 1; exact bytes restored
normalized_score_units: planted red exit 1; exact bytes restored
optional_analyst_field: planted red exit 1; exact bytes restored
optional_provider_field: planted red exit 1; exact bytes restored
recipe_membership: planted red exit 1; exact bytes restored
append_only_packet: planted red exit 1; exact bytes restored
```

**Restored proof outputs:**

```text
...............                                                          [100%]
15 passed in 2.25s
restored guard suite exit 0
................................................                         [100%]
48 passed in 3.02s
restored sprint suite exit 0
```

**Module line counts:** Every touched Python module is below 200; no size baseline change. `Path.read_text(...).splitlines()` output; the final line also measures compact UTF-8 JSON for the TGT fixture order.

```text
agents/analyst/domain/recommend.py 184
agents/analyst/domain/score_arithmetic.py 38
agents/analyst/domain/scoring.py 187
agents/deliberator/context.py 147
agents/deliberator/context_arithmetic.py 163
agents/deliberator/prompt_recipe.py 77
agents/provider/agent.py 191
agents/provider/regime_arithmetic.py 25
contracts/analyst.py 134
contracts/provider.py 186
tests/score_arithmetic_analyst_support.py 88
tests/score_arithmetic_regime_support.py 54
tests/score_arithmetic_support.py 88
tests/test_score_arithmetic.py 75
tests/test_score_arithmetic_analyst.py 154
tests/test_score_arithmetic_compat.py 88
tests/test_score_arithmetic_guards.py 137
tests/test_score_arithmetic_pins.py 140
tests/test_score_arithmetic_regime.py 116
TGT score_arithmetic compact UTF-8 JSON bytes 586
```

**Protected-file proof:** This exact command printed nothing and exited 0:

```text
git diff main -- pyproject.toml uv.lock kernel/deliberation_prompts.py kernel/deliberation_program.py kernel/dspy_engine.py agents/deliberator/guided_turn.py
```

`git diff --exit-code HEAD -- docs/STATE.md` also printed nothing and exited 0. `pyproject.toml` and `uv.lock` are untouched; the planner owns the merge-time bump.

**Existing test files edited:** None. The existing analyst, PM, forecaster, provider and S254 parity tests pass without expectation edits. The full suite's seven existing live/configuration skips are listed below and are not used as sprint proof.

**Main-packet freeze:** Retained from before implementation, when the original five renderers matched `main`: `recommendation` 3,327 bytes and `no_recommendation` 2,614 bytes. A3 now proves both frozen strings byte-equal.

**`make ci`:** `make ci > ci.txt 2>&1`, exit **2**, from the tree above. Steps 1-12 passed; step 13 was blocked before network access. Steps 14-15 were then executed explicitly and passed, because make stops at step 13. `ci.txt` holds the final complete attempted gate; `.tools/s255/ci-secret-tail.txt` holds the continued checks. The audit is **NOT RUN** as a fresh vulnerability audit: the handover forbids the network it requires. No clean dependency-audit or all-15-green claim is made.

| CI step | Result | Evidence |
| --- | --- | --- |
| 1. ruff lint | PASS | `ci.txt`; next step reached |
| 2. ruff format | PASS | `ci.txt`; next step reached |
| 3. mypy | PASS | `ci.txt`; next step reached |
| 4. import-linter | PASS | `ci.txt`; next step reached |
| 5. module size | PASS | `ci.txt`; next step reached |
| 6. module header | PASS | `ci.txt`; next step reached |
| 7. law coverage | PASS | `ci.txt`; next step reached |
| 8. PARAM/settings sync | PASS | `ci.txt`; next step reached |
| 9. sprint status | PASS | `ci.txt`; next step reached |
| 10. Markdown links | PASS | `ci.txt`; next step reached |
| 11. version scheme | PASS | `ci.txt`; next step reached |
| 12. pytest / coverage | PASS | `ci.txt`; next step reached |
| 13. dependency audit | NOT RUN | Attempt blocked before DNS/connect; no network permitted |
| 14. detect-secrets | PASS | Explicit continuation, exit 0 |
| 15. untracked secrets | PASS | Explicit continuation, exit 0 |

**Actual final gate output:**

```text
TOTAL                                                           20072      0   4244      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
SKIPPED [1] tests\test_bus_azure_config.py:21: Service Bus dotenv isolation proof requires local .env
SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
SKIPPED [1] tests\test_deliberator_servicebus_peer.py:36: A1 proof requires .env present; CI has no local secrets file
SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
SKIPPED [1] tests\test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
SKIPPED [1] agents\provider\tests\test_sources.py:159: FINNHUB_TEST_NETWORK=1 is not set
SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
========= 4304 passed, 7 skipped, 2470 warnings in 320.36s (0:05:20) ==========
uv run python scripts/check_dependency_audit.py
dependency audit failed: WARNING:pip_audit._cli:--no-deps is supported, but users are encouraged to fully hash their pinned dependencies
WARNING:pip_audit._cli:Consider using a tool like `pip-compile`: https://pip-tools.readthedocs.io/en/latest/#using-hashes
S255 proof: network access disabled before DNS/connect
make: *** [Makefile:59: ci] Error 1
```

**Actual continued secret-check output:**

```text
Detect secrets...........................................................Passed
detect-secrets tracked exit: 0
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 13 new file(s)
untracked secrets exit: 0
```

**Resolved dependency-only skip:** The first gate had 4,303 passes and eight skips because SciPy was absent in this isolated venv. `uv pip install --offline scipy` used the local cache only; no project or lock file changed. The formerly skipped oracle passes, then the final full gate has 4,304 passes and seven live/configuration skips.

```text
Resolved 2 packages in 26ms
Installed 1 package in 3.12s
 + scipy==1.18.1
.                                                                        [100%]
1 passed in 17.10s
```

**Twelve-item checklist:**

| # | Evidence above | Result |
| --- | --- | --- |
| 1 | Original law reading boundary retained | MET |
| 2 | Corrected Appendix output and exact tree pasted | MET |
| 3 | Original pre-implementation A1 red retained and pasted | MET |
| 4 | A1-A9 and B1-B4 named in the result table | MET |
| 5 | 27 per-property red/restored outputs pasted | MET |
| 6 | Three named law amendments, versions, Changelogs, test plans and both rollups | MET |
| 7 | Exact protected diff empty; version files untouched | MET |
| 8 | Final A1 prints 9 of 9 orders equal | MET |
| 9 | Existing test edits: None | MET |
| 10 | TGT arithmetic JSON measured: 586 bytes | MET |
| 11 | ci.txt / exit 2; dependency audit explicitly NOT RUN; other 14 steps pass | MET |
| 12 | All 19 Python modules below 200; spec and README set BUILT | MET |

**Stages still owed:** Push, remote CI/CodeQL/Security Findings and exact-head `make gate-ran`, experiment verdict/re-measure decision, merge and MINOR bump, tag, deploy, live F1/F2: **not done**, outside this branch-only handback. The dependency audit needs the planner's network-enabled gate before the push/merge stages. No push, pull or merge was made.

---

## Return notes

The first stop and its evidence stand. The planner's `8195b21b` correction supplies the one missing scale clause; A1's resumed red caught its absence, and A9 now pins the four exceptions on all nine recorded orders and all actual default/moved A6 outputs. The fixture's second and third lines stay EXP-019 arm B's byte for byte. The corrected first line has not been re-measured with a model here; that decision and the experiment verdict remain the operator's merge gate.

The neutral-value pin is true but indirect for RS. The analyst's `_NEUTRAL` constants are 50, and `signal_selection._contribution` is zero at 50 for each pillar. The RS band table emits 20, 40, 60 and 80; its scale's neutral reference point is still 50 / 100 = 0.50. A9 plants all bands and RS at 50, checks the blend and the analyst's `_composite` at 0.50 under default/moved settings, and proves the statement without adding a new RS band or changing a score. The confidence-floor sentence is pinned at the buy-admission branch, below/at/above its floor; existing held-position stop/thesis exits keep their own rules.

The seven constants are captured where `score_candidate` actually computes them and carried through the shared recommendation constructor. The moved-settings tests also move the inactive alpha weight while passing no alpha score at this scoring boundary; any recorded `alpha158_score` withholds the lines. Fundamental names are captured before the combined metric payload is sorted. Partial scan/market lineage uses the same no-regime reason at the end, so a recorded arithmetic object cannot silently disappear at an early return. Old lineage prefixes are unchanged.

Routine invocation corrections from the first pass remain recorded: the Appendix needed `PYTHONPATH=.` and the newly written fixture test needed `Provenance.run_id`. The actual CI target has 15 steps, while the short AGENTS count is 14; `ANLZ-OUT-02` / `ANLZ-TYP-01` govern recommendation fields, and `ANLZ-OUT-03` governs rejection. The law-coverage gate caught a blank line separating the new analyst test-plan row from its table; joining the row restored the gate, with no clause or count relaxed. All mutation scripts restore original bytes in `finally` and assert the restored hash.

The offline venv's SciPy gap was resolved from its local cache, then its oracle and the full suite were rerun. The seven remaining skips are existing live/configuration checks, listed in Closeout. None of the sprint's 48 cases skips. The audit is unavailable under the no-network instruction and is named NOT RUN; its failure did not silently prevent the last two secret checks. `.env` loading is disabled for the final gate, and the ignored process guard blocks external DNS/connect. No model or live-data call, version/lock edit, existing-test edit, push or merge occurred. `docs/STATE.md` was left unchanged during the resume.

Local `main` and the stored `origin/main` ref were `41916311b68e2f8b5eab2585a48243d15bd10e27` at the protected-diff proof; they advanced outside this resumed branch work. No remote freshness is inferred from that stored ref. The implementation and evidence are prepared for one commit on the existing local sprint branch; the actual committed SHA is reported in the handback message.

---

## Planner's review and merge-time work — 2026-10-08 08:49 AEDT

**The handback is accepted.** Re-measured by the planner, not read from the builder's logs. The builder's
commit is `7f8843ba`.

| Claim | Value | How it was measured |
| --- | --- | --- |
| The Appendix script | three nines | *[measured]* extracted from this spec on the branch and run in `../ta-s255`, no `.env` |
| The sprint's tests | 48 passed, none skipped | *[measured]* the six `tests/test_score_arithmetic*.py` files, re-run by the planner |
| The guards can fail | 9 properties of the planner's own choosing, broken one at a time, each red, each file restored byte for byte: the scale clause dropped from the first line; the tolerance widened to `1e-6`; the composite divided by all three weights; the renderer left out of `PROMPT_MODULES`; the fundamental names recorded sorted; a weight recorded as its default, not the one in force; a wrong threshold recorded; the lines put first, not last; an old record given a line | *[measured]* one script, one replacement per case |
| A3's two frozen strings are what `main` builds | both equal, 3,327 and 2,614 bytes | *[measured]* the same lineage built in the main checkout at `41916311`, whose tree has no `context_arithmetic.py` and whose `Recommendation` has no `score_arithmetic` |
| The branch rebuilds the nine recorded packets | **9 of 9 byte-equal**, and none gained a line | *[measured, live graph]* read-only, the branch's `build_veto_context` on the nine orders of EXP-019 |
| Every recorded analyst run reads under the branch's contract | 85 of 85; 1,778 recommendations, none carrying `score_arithmetic` | *[measured, live graph]* `RecommendationSet.model_validate` |
| Existing tests edited | none: every file of the diff under `tests/` is added | *[measured]* `git diff --name-status` against the merge base |
| The protected files | an empty diff against `main` for the role prompts, the DSPy program and engine, the guided turn, the secrets baseline, the size baseline, the `Makefile` and the workflows | *[measured]* |
| Windows `make ci`, on this commit's tree | exit 0, all 15 steps; 4,304 passed, 7 skipped, 100.00 %; the dependency audit ran: no unaccepted vulnerability, one accepted advisory re-checked | *[measured]* redirected to a file, the exit code read from the file |

**Done by the planner on this branch.** Version `0.123.00`. `uv lock`: 180 packages before and after, and
the only version that moved is this package's. The lock's other changed lines are the local uv writing
dependency markers and wheel lists back as they were before Dependabot's `0f2cef72` rewrote them.

**Read in the diff, and accepted as built.**

- **The withheld line is also written on the two partial-lineage returns** (no `ScanRun`, no
  `MarketData`), with the reason *no regime record*. The spec said the builder calls the renderer last.
  The builder's reading is the better one: a record that carries its arithmetic never loses it without a
  line saying so. An old record still adds nothing there (pinned).
- **A short-history score records the seven constants and no names.** If such an order were ever debated,
  the packet would read *the recorded sub-scores are incomplete*. Correct, and pinned.
- **`scripts/replay_day.py` builds a regime without thresholds.** It is not the provider and nothing in a
  replay is debated, so it is left as it is. A replay that one day renders packets would read *the
  regime record carries no label thresholds*, which is true of it.
- **The local run has 7 skips where the remote run has 8.** The builder installed SciPy into this
  worktree's venv from its cache, so the forecaster's oracle test runs here. The lock does not install
  it by default.

**Not recorded on this branch, on purpose:** the remote gate for this commit and the comparison of the
branch's open CodeQL alerts with `sprint-254-each-debater-turn-is-run-by-dspy`'s 127. A commit added
above the gated one would be unproven, so both are recorded on `main`.

**The merge is held** (operator, 2026-10-07). The corrected first line is measured on `gpt-5.5`
(EXP-021, recorded on `main` after this branch was cut:
54 of 54 right, 54 of 54 on the same side as the uncorrected line). It is not measured on Opus. Whether
the merge goes on that evidence is the operator's decision.

---

## Appendix — the reference shape, and the script behind the Measured table

`recompute` is the self-check of decisions D4 and D5. `arithmetic_lines` is the text and the number
formats of decision D3, with the first line's corrected clause. Expected output: `orders 9: lines equal to
the fixture's 9, second and third lines equal to EXP-019 arm B's 9, rule reproduces the recorded confidence
and technical_score 9`.

```python
"""S255 reference shape and its proof: the score arithmetic rendered from recorded values.

Run from the sprint's worktree; no `.env`, no network, no LLM call:
  PYTHONPATH=. uv run --no-sync python <this file>
It reads tests/fixtures/score_arithmetic_nine_orders.json: the nine orders of EXP-019, each with the
recommendation the analyst recorded, the arithmetic the analyst will record from this sprint on, the
three lines EXP-019's arm B added to the packet, and those lines with the first one's scale clause
corrected (DL-270), which is the text this sprint ships.
"""

from __future__ import annotations

import json
from pathlib import Path

from contracts.analyst import Recommendation

TOLERANCE = 1e-9
fixture = json.loads(Path("tests/fixtures/score_arithmetic_nine_orders.json").read_text(encoding="utf-8"))


def recompute(rec: Recommendation, sa: dict) -> dict:
    """Apply the stated rule to the recorded values (the reference for decision D4's self-check)."""
    q = {m.name: m.value for m in rec.quant_metrics}
    tech = [q[name] for name in sa["technical_sub_scores"]]
    w = sa["relative_strength_weight"]
    technical = (1 - w) * (sum(tech) / len(tech) / 100) + w * q["rs_score"] / 100
    fund = [q[name] for name in sa["fundamental_sub_scores"]]
    pillars = {
        "technical": technical,
        "fundamental": sum(fund) / len(fund) / 100 if fund else None,
        "sentiment": rec.sentiment_score,
    }
    present = {name: value for name, value in pillars.items() if value is not None}
    total = sum(sa[f"{name}_weight"] for name in present)
    composite = sum(sa[f"{name}_weight"] * value for name, value in present.items()) / total
    return {
        "q": q, "tech": tech, "fund": fund, "pillars": pillars, "present": present, "total": total,
        "composite": composite, "confidence": sa["confidence_floor"] + sa["confidence_span"] * composite,
    }


def arithmetic_lines(rec: Recommendation, sa: dict, floor: float, vix: dict) -> list[str]:
    """The three lines: EXP-019 arm B's, with the first line's scale clause corrected (DL-270)."""
    r = recompute(rec, sa)
    q, rsw = r["q"], sa["relative_strength_weight"]
    rule = (
        "Score arithmetic, the rule for every order (definitions from the analyst's code, the same for every "
        "reviewer): inside quant_metrics each key ending in _score, and each fundamental sub-score, is a 0-100 band "
        "score in which 50 is neutral, except technical_score, fundamental_score, sentiment_score and composite_score, "
        f"which are on a 0-1 scale; technical_score = {1 - rsw:.2f} x (mean of the technical sub-scores / 100) + "
        f"{rsw:.2f} x (rs_score / 100); fundamental_score = (mean of the fundamental sub-scores) / 100; "
        f"composite_score = {sa['technical_weight']:.2f} x technical_score + {sa['fundamental_weight']:.2f} x "
        f"fundamental_score + {sa['sentiment_weight']:.2f} x sentiment_score, divided by the sum of the weights of "
        f"the pillars that are present; confidence = {sa['confidence_floor']:.2f} + {sa['confidence_span']:.2f} x "
        "composite_score; a pillar score of 0.50 is neutral; an order is recommended only if confidence >= "
        "base_min_confidence_score."
    )
    parts = [
        f"technical sub-scores ({len(r['tech'])}): mean {sum(r['tech']) / len(r['tech']):.2f}",
        f"rs_score={q['rs_score']:g}",
        f"technical_score={r['pillars']['technical']:.4f}",
    ]
    if r["fund"]:
        subs = ", ".join(f"{name}={q[name]:g}" for name in sa["fundamental_sub_scores"])
        parts += [f"fundamental sub-scores ({len(r['fund'])}): {subs}",
                  f"fundamental_score={r['pillars']['fundamental']:.4f}"]
    if rec.sentiment_score is not None:
        parts.append(f"sentiment_score={rec.sentiment_score:.4f}")
    shares = ", ".join(f"{name} {sa[f'{name}_weight'] * value / r['total']:.4f}" for name, value in r["present"].items())
    parts += [
        f"contributions to composite_score: {shares}",
        f"composite_score={r['composite']:.4f}",
        f"confidence={r['confidence']:.4f}",
        f"base_min_confidence_score={floor:.3f}",
        f"margin over the floor={r['confidence'] - floor:+.4f}",
    ]
    regime = (
        "Regime, the rule for every order: vix_index only selects the regime label (risk_on at or below "
        f"{vix['risk_on_at_or_below']:g}, risk_off from {vix['risk_off_from']:g}, high_volatility from "
        f"{vix['high_volatility_from']:g}, extreme_volatility from {vix['extreme_volatility_from']:g}, neutral "
        "otherwise). The label is printed and changes no number: base_min_confidence_score, base_stop_loss_pct, "
        "base_take_profit_pct and base_max_holding_days are the same constants under every label, and the VIX is "
        "not an input to any score."
    )
    return [rule, f"Score arithmetic for {rec.ticker}: " + "; ".join(parts) + ".", regime]


equal = unchanged = reproduced = 0
for order in fixture["orders"]:
    rec = Recommendation.model_validate(order["recommendation"])
    sa = order["score_arithmetic"]
    r = recompute(rec, sa)
    reproduced += (
        abs(r["confidence"] - rec.confidence) <= TOLERANCE
        and abs(r["pillars"]["technical"] - rec.technical_score) <= TOLERANCE
    )
    lines = arithmetic_lines(rec, sa, order["base_min_confidence"], fixture["vix_thresholds"])
    equal += "\n".join(lines) == order["arithmetic_lines"]
    unchanged += lines[1:] == order["exp019_arm_b_lines"].split("\n")[1:]
    if "\n".join(lines) != order["arithmetic_lines"]:
        print("DIFF", order["ticker"])
n = len(fixture["orders"])
print(f"orders {n}: lines equal to the fixture's {equal}, second and third lines equal to EXP-019 arm B's "
      f"{unchanged}, rule reproduces the recorded confidence and technical_score {reproduced}")
```
