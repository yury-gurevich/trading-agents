<!-- Agent: planning | Role: sprint handover -->
# Sprint 246 — Every debate turn records how it read the evidence, before it argued

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-246-every-debate-turn-records-how-it-read-the-evidence`
**Status:** SPEC
**Version:** *next available MINOR at merge*
**Effort:** L
**Decisions:** [DL-250](../design-log.md) and its amendment (the operator's direction) · work-queue **97 (a)** · ADR-0010 (DSPy behind a port) · DL-184 (no image installs `dspy`)

> **Why this bump kind.** A new capability: the deliberator gains a recorded dimension it did not
> have. Each defender and challenger turn writes a typed reading of the evidence before its argument,
> and the record keeps it with the packet it read.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/deliberator/laws/laws.md` | The deliberator's **locked constitution** (v1.10 after S245) | **LOCKED.** This sprint owes the clauses named below; any other clause you believe is wrong is a `drift-register.md` row plus a report |
| `agents/deliberator/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Add the rows; read `DLIB-NEV-06`, `DLIB-NEV-07`, `DLIB-OBS-06`, `DLIB-OBS-07`, `DLIB-TYP-01` |
| `docs/laws/*.md` | Conventions, ledger, drift register | `drift-register.md` is the one law-adjacent file you may append to |

Binding sections here: **`DLIB-TYP-01`** (names `DebateTurnRecord`'s fields), **`DLIB-NEV-06`** / **`DLIB-NEV-07`**
(never hide a failed debate; never record an empty turn), **`DLIB-OBS-01`** (the transcript is
reconstructable), **`DLIB-OBS-06`** (each role's frozen system prompt is offered to the prompt cache),
**`DLIB-OBS-07`** (the recipe digest names every module that shapes a prompt), **`DLIB-NEV-09`** (S245: no
unpinned fact about our code in a role prompt).

### The rule

1. **Before writing code**, read every law file in the map below, whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes, both.** `contracts/deliberator.py` gains fields, and the deliberator gains two guarantees. The
law cycle owed in this unit of work (deliberator v1.10 → **v1.11**):

- **Amend `DLIB-TYP-01`**: `DebateTurnRecord` also carries `reasoning` and `reasoning_error` (S205's
  rule: a type clause names the fields it requires).
- **New `DLIB-OUT-06`**: each defender and challenger turn records the guided reasoning its
  completion carried (readings of named values, with meaning and bearing, and gaps, written before
  its argument) **exactly as the model wrote it**, or records why it could not be read. A reasoning
  that cannot be read never fails the turn or the order.
- **New `DLIB-OUT-07`**: each debated order's record carries the decision and the evidence packet
  the roles were given.
- **PARAM:** the `max_tokens` row follows the new default (Scope 6).
- Changelog line, `test-plan.md` rows, clause IDs in the proving tests' docstrings, and the rollup in
  **both** `docs/laws/ledger.md` and `docs/laws/INDEX.md` (let `make ci` give the number).

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `contracts/deliberator.py` | `agents/deliberator/laws/laws.md` + `test-plan.md` | `DLIB-TYP-01` (amended) |
| New `kernel/deliberation_guided.py` (+ its frozen format module) | same; ADR-0010 | `DLIB-OUT-06`; `DLIB-OBS-06` (the guided system message is still one frozen, cacheable string per role) |
| `agents/deliberator/agent.py` and a new `agents/deliberator/guided_turn.py` | same | `DLIB-OUT-06`, `DLIB-NEV-06`, `DLIB-NEV-07` |
| `agents/deliberator/review_record.py` | same | `DLIB-OUT-06`, `DLIB-OUT-07`, `DLIB-OBS-01` |
| `agents/deliberator/prompt_recipe.py` | same | `DLIB-OBS-07`: every module that shapes the prompt is declared |
| `agents/deliberator/settings.py` (`max_tokens`) | same (PARAM table) | the PARAM row and the settings must agree (`make ci`) |

⚠️ **The one invariant: the judge does not change.** Its system prompt, its user message, its parse
and its verdict path stay byte-identical. The binding veto rests on the judge, so its format is a
later sprint's decision. If your change would touch any of it, stop and report.

---

## Goal

At merge, every defender and challenger turn is produced by a DSPy `ChainOfThought` program with a
typed reasoning field. The model reads the evidence before it argues: step 1 is the values it relies
on, each with what it means in this system and how it bears on the decision; step 2 is what is
missing; step 3 is the argument built from those. The runtime reproduces DSPy's rendering byte for
byte **without importing DSPy**, parses the reasoning strictly, and records it on the
`DeliberationRun` with the packet it read. The judge, the veto and every other agent are unchanged.

## Why (context)

The operator's direction (2026-09-30, [DL-250](../design-log.md) amendment) is to record the *guided*
reasoning, the structure DSPy imposes on the chain of thought, as the window into how a decision is
crafted. It can then be assessed in code for **completeness** (did the turn read the values that
matter?) and **truth** (does the value match the packet, and is the meaning the one our code gives
it?). Today nothing records how the referee read a single value. DL-250 measured traps in one live
packet: `pe=30` is a 0–100 sub-score and not the ratio; two different metrics share the name
`relative_strength`. And "DSPy" has never run: the compile step string-joins. This sprint is the
first in which DSPy defines what the model is asked to produce. **S247** will score the records
this sprint creates, so this sprint records and does not judge.

### Measured, 2026-09-30 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Calls per night | `sched-2026-09-28`: **24** defender, **24** challenger, **12** judge (12 orders × 2 rounds) | *[measured]* `LLMCall` rows 22:30–00:30 UTC |
| Latency per call since 2026-09-20 | challenger p50 **22.8 s**, p95 **39.1 s**, max **39.8 s**; defender p50 17.3 s, p95 20.9 s | *[measured]* `LLMCall.latency_ms` |
| Peer timeout | **120 s** (pack `DELIBERATOR_REQUEST_TIMEOUT_SECONDS`) | *[measured]* `orchestration/packs/trading_tunables.json` |
| Output tokens since 2026-09-01 | challenger p95 **2,720**, max **3,026**; defender p95 1,523, max 1,640; **0** stopped at `max_tokens` | *[measured]* `LLMCall.tokens_out` (vendor counts), `stop_reason` |
| Output cap | **4,096**: the code default (`agents/deliberator/settings.py:91`); **no pack override** | *[measured]* code + pack |
| Models | all three roles run **`claude-opus-5`**, effort `high` | *[measured]* `LLMCall.model`; pack |
| DSPy 3.3.1 rendering of this sprint's program | output order `['reasoning', 'argument']`; the signature's format block is **1,995** chars; the challenger system message becomes **9,058** chars (champion 6,764) | *[measured 2026-09-30]* `ChatAdapter.format_system_message` on the prototype below |
| DSPy's parse | header regex `\[\[ ## (\w+) ## \]\]`; a typed field goes through `json_repair.loads` then pydantic; the `[[ ## completed ## ]]` marker is **not** required | *[measured]* `dspy/adapters/chat_adapter.py:219`, `dspy/adapters/utils.py:187` |
| CI has no DSPy | every job runs `uv sync --frozen` (no extras) | *[measured]* `.github/workflows/ci.yml:36,76,103` |
| No image has DSPy | Dockerfiles copy `kernel/`, `contracts/`, `agents/<name>/`, never `scripts/`; the `optimizer` extra is in 0 of 15 | *[measured]* `agents/deliberator/Dockerfile:11-13`; DL-184 |
| Who reads `DeliberationRun` | execution: one node per PM run, by edge (`agents/execution/deliberation_gate.py:52`); `orchestration/verdict_sources.py:51` lists all, but only `scripts/deliberation_quality.py` calls it | *[measured]* grep |
| Cost of the readings | ≈ **+400–700** output tokens per debater turn ≈ **+$0.5–1 per night** at Opus 5 rates | *[ASSUMED — estimate]* 8–12 readings × ~45 tokens. **F1 measures it** |
| Latency added | ≈ **+6–10 s** per debater turn (≈ 73 tokens/s measured: 1,675 tokens in 22.8 s) | *[ASSUMED — derived]* **F1 measures it** |

---

## Scope — and what is deliberately NOT here

**Cut this branch from `main` after S245 has merged.** S246 embeds S245's champion prompts, and both
sprints edit the deliberator's law book.

1. **The typed shape, in the kernel.** In a new `kernel/deliberation_guided.py`, define pydantic
   models (the kernel may not import `contracts/`; contracts may import the kernel). Use exactly
   these field descriptions, because they are rendered to the model:

   ```python
   class EvidenceReading(BaseModel):
       metric: str = Field(description="the exact name as it appears in the evidence packet")
       value: str = Field(description="the value copied exactly as the packet writes it")
       meaning_here: str = Field(description="one clause: what this measures in THIS system, not in general finance")
       bears_on: Literal["supports", "against", "neutral"] = Field(description="how it bears on the decision under test")

   class GuidedReasoning(BaseModel):
       """Read before you argue: each later step may use only what the earlier steps established."""
       readings: list[EvidenceReading] = Field(description="step 1: every value your argument relies on, read from the packet")
       gaps: list[str] = Field(description="step 2: evidence the packet lacks, marks unavailable, or leaves unit/scope unknown")
   ```

   `value` is a **string** on purpose. The packet writes `5.87%`, `Semiconductors`, `2026-10-19` and
   lists, so a float would turn ordinary readings into parse failures, and a copied string is what
   S247 compares against the packet.
2. **The DSPy program, offline.** A pack-side module `scripts/deliberation_guided_program.py`
   (`Agent: tooling`) defines the signature and the program:

   ```python
   class DebateTurn(dspy.Signature):
       decision: str = dspy.InputField(desc="the decision under test")
       context: str = dspy.InputField(desc="the evidence packet for this decision; every value you read comes from here")
       transcript: str = dspy.InputField(desc="the debate so far")
       argument: str = dspy.OutputField(desc="step 3: your turn, at most ~5 sentences, built only from your readings and gaps")

   program = dspy.ChainOfThought(DebateTurn.with_instructions(<role prompt>), rationale_field_type=GuidedReasoning)
   ```

   Import `dspy` lazily, exactly as `kernel/dspy_optimizer.py` does, and cover the module with an
   injectable fake (the S119 pattern), because CI has no DSPy.
3. **Golden fixtures written by real DSPy.** A script `scripts/render_guided_turn_golden.py` runs the
   real program (`uv run --extra optimizer`, with `LITELLM_LOCAL_MODEL_COST_MAP=True` so LiteLLM does
   not reach the network) and writes `tests/fixtures/deliberation_guided_golden.json`. It must cover:
   - `ChatAdapter.format_system_message` for **fixture instructions** containing a blank line and a
     multi-line paragraph (DSPy indents every line; blank lines included);
   - `format_user_message_content(..., main_request=True)` for fixture inputs with multi-line
     `context` and `transcript`;
   - `ChatAdapter.parse` on **every completion in the Test plan's parse table** (B2), with either
     DSPy's parsed result or its exception type.

   **You may not hand-write this file.** If `uv sync --frozen --extra optimizer` fails in your
   session, stop and report; do not continue with a hand-made golden.
4. **The runtime, without DSPy.** In the kernel:
   - `GUIDED_TURN_PREFIX`, a frozen string: the field-description and structure block DSPy renders
     for this signature;
   - `guided_system(role_prompt)`, which is that prefix plus DSPy's objective wrapper around the role
     prompt;
   - `guided_user(decision, context, transcript)`;
   - `parse_guided_turn(completion)`, which returns reasoning and argument, or an error.

   The parser splits on DSPy's header regex and validates the `reasoning` JSON **strictly**
   (`json.loads` + pydantic). **This is the one named deviation from DSPy:** where DSPy's
   `json_repair` would silently repair malformed JSON, the runtime records a `reasoning_error`
   instead. A repaired reading is a reading the model did not quite write, and this record exists to
   check truth. The kernel module never imports `dspy`.
5. **The live path for the two debaters.**
   - A new `agents/deliberator/guided_turn.py` (`agent.py` is at **184** lines) makes the defender and
     challenger turns use `guided_system(DEFENDER_SYSTEM | CHALLENGER_SYSTEM)` and `guided_user(...)`
     through the same `_LedgerLLM`, so the ledger, stop reasons and outage handling are unchanged.
   - `DebateTurnRecord` gains `reasoning: GuidedReasoning | None = None` and
     `reasoning_error: str | None = None`.
   - The turn's **`text`**, which the next speaker and the judge see, is a deterministic rendering
     (table in the Test plan): one line per reading, then the gaps, then the argument. This keeps the
     definitions visible to the other side and to the judge, as they are today inside the free text,
     and lets the opponent contest a misreading.
   - When the reasoning cannot be read, `text` is the raw completion stripped, exactly as today, and
     `reasoning_error` says why. An empty completion still raises as today (`DLIB-NEV-07`).
6. **`max_tokens` default 4,096 → 8,192.** It is the tunable's own ceiling. Its `why` cites the
   measurement: challenger max **3,026** today, plus the readings. Billing is per generated token, so
   the cap costs nothing unless used. Update the PARAM row in the same commit.
7. **The record.**
   - `review_record.transcript_records` adds `reasoning` (the model dump, or `None`) and
     `reasoning_error` to each row.
   - `debate_record` adds the order's `decision` and `context`: the packet, once per order, because
     every turn of an order reads the same packet.
   - Old rows without these keys must still read everywhere they are read today. Grep every reader of
     `transcript` and `debates` and say which you checked.
8. **The recipe digest.** Add every new module that shapes a debater prompt to `PROMPT_MODULES`, and
   extend `tests/test_prompt_recipe.py`'s pinned import-graph roots to include the guided renderer.
   Otherwise the digest can miss it, which is the failure `DLIB-OBS-07` exists to prevent.
9. **The live check's instrument.** A script `scripts/guided_turn_replay.py` rebuilds recorded
   propositions through `orchestration/replay_corpus.py`, runs **defender r1 and challenger r1** on
   the guided path, and prints, per turn: parse ok or the error, the number of readings, latency,
   output tokens and stop reason. Cover it with a fake LLM. The planner runs it live.
10. **Law cycle** (above).

### Out of scope (do NOT build this sprint)

- **The judge.** It stays on today's prompt, message and parser (the ⚠️ invariant).
- **Scoring the readings** for completeness or truth: that is **S247**, on the nights this sprint
  records.
- **Renaming metrics or adding a glossary** (work-queue 97 b/c). Today's packet is the baseline S247
  measures against.
- **GEPA or any optimisation, and any real LLM call** in the build.
- **Changing the replay and eval harnesses** (`kernel.deliberate`, `orchestration/deliberation_replay.py`,
  `scripts/deliberation_eval.py`). They keep today's free-text path. Name the divergence in Return
  notes for S247.
- **`dspy` in any image or in the runtime import graph**, and any change to `pyproject.toml` extras.
- **The model's own thinking** (`display: "summarized"`): a separate, secondary record.

### The road not taken (LAW-06)

- **Install `dspy` in the deliberator image and call the program live.** Rejected: it re-imports the
  advisory DL-184 kept out of every image, puts LiteLLM on the live call path (outside our ledger,
  stop-reason and outage handling), and a DSPy upgrade would silently change live prompts. The
  golden fixtures give the same exact rendering with none of those costs.
- **Hand-roll the format and cite DSPy by name.** Rejected: that is what S119 did. The golden
  fixtures make DSPy's own output the definition, so the program S247 and GEPA later optimise is
  byte-identical to the one production runs.
- **Anthropic structured outputs (`output_config.format`) to force valid JSON.** Rejected for now: it
  changes both LLM adapters and the whole response shape, and moves the format away from DSPy's
  `ChatAdapter`. Reconsider if F1 shows parse failures above 5 %.
- **Lenient parsing with `json_repair`, as DSPy does.** Rejected: see Scope 4. A reading that had to
  be repaired is not the one the model wrote.
- **Show the readings to nobody (argument-only `text`).** Rejected: the definitions the judge sees
  today inside the free text would disappear from its input, a silent change to the veto's evidence.
- **A separate LLM call for the reasoning.** Rejected: a second call records a reconstruction, not
  how the turn was crafted, and doubles the cost.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Where the frozen prefix lives and how it is proven.** Recommended: a literal in a kernel module,
   proven equal to the DSPy golden by a CI test. The golden is regenerated only by the offline
   script.
2. **The exact `text` rendering of readings, gaps and argument.** The Test plan table is the
   starting point; decide the value and number formatting and record why.
3. **The `reasoning_error` vocabulary.** For example `missing field: argument`,
   `invalid JSON in reasoning`, `schema: <pydantic location>`. It must be short and bounded (the
   fail-open reason caps at 500 characters; follow that precedent).
4. **Where the packet is stored.** Recommended: `debates[ticker]["context"]`, not on `LLMCall`
   (`DLIB-OUT-05` forbids prompt text there).

🪤 **Take the next free DL number, then re-check it at merge.** After S245 the next is likely
**DL-252**; entries land at both ends of the log, so re-check.

---

## Blast radius — measured 2026-09-30

| What | Detail |
| --- | --- |
| Files changed | new `kernel/deliberation_guided.py` (+ a frozen-format module if you split); `contracts/deliberator.py` (**127**); `agents/deliberator/agent.py` (**184**, may not grow past 200) + new `agents/deliberator/guided_turn.py`; `agents/deliberator/review_record.py` (**100**); `agents/deliberator/prompt_recipe.py`; `agents/deliberator/settings.py`; new `scripts/deliberation_guided_program.py`, `scripts/render_guided_turn_golden.py`, `scripts/guided_turn_replay.py`; new `tests/fixtures/deliberation_guided_golden.json` + tests; laws (`laws.md`, `test-plan.md`, `ledger.md`, `INDEX.md`); `docs/design-log.md`; `pyproject.toml` |
| Agents affected | **deliberator** (proponent and opponent turns; the manager records). No agent imports another |
| Contract change? | **Yes**: two optional fields on `DebateTurnRecord`, so the law cycle above is mandatory |
| Graph vocabulary change? | **No new label or top-level property.** `DeliberationRun.transcript` rows and `debates[ticker]` gain keys. Confirm `kernel/graph_vocabulary.py` declares none of them; if it does, say so, because the deploy becomes a full `up` |
| New env keys / tunables | **None.** `max_tokens` changes its **default**, not an env key |
| Deploy implication | **Image-only retag** (unless the vocabulary check above says otherwise) |
| Rollback | Retag to the tag live before the deploy. A retag does **not** remove the rows written in the new shape: they stay, with extra keys the old code ignores. Nothing else is written |

🪤 **Both digests move for the debaters, by design.** The system message and the user message both
change, so `system_prompt_hash` and `prompt_recipe_hash` differ from every earlier debater call. The
judge's do not, because its prompt does not change (B7 proves it).

---

## Steps, in order

1. **Read the laws** (MUST RULE) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Generate the golden fixtures with real DSPy** (Scope 3) and commit them alone.
4. **Plant the failing tests first**: B1, B2, B3, B5, red against the empty implementation. Paste.
5. **Implement** Scope 1, 4, 5, 6, 7, 8, 9.
6. **Law cycle.**
7. **Prove the guards can fail (DL-70)**, each planted, red, pasted, restored:
   (a) change one character of the frozen prefix → B1 red;
   (b) make the parser lenient (repair malformed JSON) → B2's deviation row red;
   (c) drop `reasoning` from the transcript rows → B5 red;
   (d) raise on an unreadable reasoning → B4 red;
   (e) route the judge through the guided path → B7 red;
   (f) remove the guided module from `PROMPT_MODULES` → the recipe test red.
8. **`make ci` green**, redirected to a file, never piped.
9. **Fill the handback sections.**

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| B1 | 🎯 The runtime renders what DSPy renders | the golden fixture's instructions and inputs | `guided_system(instr)` and `guided_user(...)` are **byte-identical** to DSPy's golden output |
| B2 | 🎯 The runtime parses what DSPy parses | every row of the parse table below | the same result as DSPy's golden on every row, **except** the named deviation row, where the runtime returns a `reasoning_error` and DSPy repairs |
| B3 | 🎯 A debater turn carries its reading | the deliberator's `debate_turn` handler, fake LLM returning a valid guided completion, both roles | the reply's `DebateTurnRecord` has typed `reasoning`, `reasoning_error=None`, and `text` equal to the rendering table below. Cites `DLIB-OUT-06`, `DLIB-TYP-01` |
| B4 | An unreadable reasoning never fails the turn | fake LLM returning each error row of the parse table | the turn is returned, `text` = the raw completion stripped, `reasoning=None`, `reasoning_error` set, **no fail-open** for the order. Cites `DLIB-OUT-06`, `DLIB-NEV-06` |
| B5 | 🎯 The record keeps the reading and its packet | a full manager review with fake peers | `DeliberationRun.transcript` rows carry `reasoning` and `reasoning_error`; `debates[ticker]` carries `decision` and `context` equal to the proposition sent. Cites `DLIB-OUT-06`, `DLIB-OUT-07` |
| B6 | Old records still read | a `DeliberationRun` recorded in the old shape (no new keys) | every reader you found in Scope 7 handles it, and `DebateTurnRecord` validates it |
| B7 | 🪤 The judge is untouched | the verdict path | the judge's system and user messages are byte-identical to `JUDGE_SYSTEM` + `render_debate_prompt` output, and it parses as before |
| B8 | 🪤 No DSPy at run time | the kernel and agent import graph | no module under `kernel/`, `contracts/` or `agents/` imports `dspy`; no Dockerfile installs the `optimizer` extra |
| B9 | The digest covers the guided path | `tests/test_prompt_recipe.py`, extended roots | the guided modules are in `PROMPT_MODULES`; removing one fails |
| B10 | `max_tokens` default is 8,192, and the PARAM row agrees | settings + law table | as stated; the `why` cites 3,026 |
| B11 | The offline scripts run | fake `dspy` module; fake LLM | the golden writer produces the file's shape; the replay instrument prints one line per turn |

**Parse table (B2): one row per case class.**

| Case | Completion | DSPy (golden) | Runtime |
| --- | --- | --- | --- |
| valid | `reasoning` JSON + `argument` + `completed` | parsed | parsed, identical |
| no `completed` marker | valid sections, marker absent | parsed | parsed, identical |
| preamble before the first header | a sentence, then valid sections | parsed (the preamble is ignored) | parsed, identical |
| empty `readings` | `{"readings": [], "gaps": []}` | parsed | parsed, identical |
| `bears_on` outside the enum | `"support"` | error | `reasoning_error` |
| missing `argument` section | `reasoning` only | error | `reasoning_error` |
| **malformed JSON** (a trailing comma) | otherwise valid | **parsed** (`json_repair`) | **`reasoning_error`: the named deviation** |

**`text` rendering (B3): input → expected output.**

| Reasoning | Expected `text` |
| --- | --- |
| readings `pe`=`30` "0-100 banded sub-score of P/E" `against`; `atr_pct`=`2.935` "14-day ATR as percent of close" `neutral`; gaps `["no holdings context"]`; argument `A.` | `Readings:\n- pe = 30: 0-100 banded sub-score of P/E (against)\n- atr_pct = 2.935: 14-day ATR as percent of close (neutral)\nGaps:\n- no holdings context\nArgument: A.` |
| no readings, no gaps, argument `A.` | `Readings: none\nGaps: none\nArgument: A.` |

---

## Success factors

- [ ] B1–B11 pass; B1, B2, B3 and B5 were pasted **red** first.
- [ ] The golden fixture was written by real DSPy 3.3.1; the command and version are pasted.
- [ ] The judge's messages and parse are byte-identical to before (B7).
- [ ] No `dspy` in the runtime import graph or any image (B8).
- [ ] `DLIB-TYP-01` amended; `DLIB-OUT-06` and `DLIB-OUT-07` added; v1.11 Changelog; test-plan rows;
      rollups in `ledger.md` **and** `INDEX.md`.
- [ ] Design decisions recorded with rejected alternatives.
- [ ] All six DL-70 plants: planted, red, pasted, restored.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **A hand-made golden proves nothing.** B1 and B2 are only as good as the file; it must come from
real DSPy, and its generating command goes in the closeout.
🪤 **Indentation of the objective.** DSPy indents *every* line of the role prompt, blank ones too.
The champion prompts contain blank lines and `\n` inside examples, which is why the fixture
instructions must contain them.
🪤 **Trailing spaces.** DSPy's text has a space before some newlines (`(GuidedReasoning): `,
`your objective is: `). Keep them inside the string literal; the pre-commit whitespace hook only
sees line ends in source files.
🪤 **A lenient parser would look like success.** B2's deviation row exists so that "we parse
everything" cannot come from silently repairing what the model wrote.
🪤 **`text` is what the judge reads.** B7 proves the judge's *prompt* is unchanged, but the debater
text it reads is now rendered. That is intended; say so in Return notes, and do not "fix" it by
hiding the readings.
🪤 **`value` is a string.** A float would reject `5.87%` and `Semiconductors`, and the parse rate
would collapse for a reason that has nothing to do with the model's reading.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`). The pydantic
  models live in the kernel so `contracts/` can use them.
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `agents/deliberator/agent.py` **184**, `kernel/deliberation.py` **182**,
  `contracts/deliberator.py` **127**, `agents/deliberator/review_record.py` **100**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- `make ci` **every step** green, **100.00 % coverage floor**. Never through a pipe.
- Version bump: MINOR. **`uv.lock` is owed to the planner.**
- Secrets never through the worktree. **State which tree you ran in.** No proof here needs `.env`.

---

## Sequencing after merge

1. Planner: `uv lock`, Windows `make ci`, push, **`make gate-ran`** from the proving worktree, with the
   printed SHA checked against `git rev-parse HEAD`; the branch's CodeQL alerts diffed against the
   last merged branch.
2. Merge to `main` and push; post-merge CodeQL.
3. **Live check (planner, before the deploy, needs `.env`):** `scripts/guided_turn_replay.py` on the
   **10** most recent recorded propositions: **20 calls** (defender r1 + challenger r1), estimated
   **≈ $1.5–2.5**, budget stated before running. Pass: **≥ 19 of 20** parse; **0** `max_tokens`
   stops; challenger latency **≤ 60 s**; output tokens recorded against the baselines above. Record
   it in `docs/laws/functionality-checks.md`.
4. **Deploy:** image-only retag (this also carries S245 if not yet deployed). Record the rollback tag.
5. **F1 (first scheduled night):** every defender and challenger transcript row carries `reasoning`
   or `reasoning_error`; parse rate; readings per turn; debater output tokens and latency against
   this spec's baselines; **0** fail-opens caused by the format; the judge's `system_prompt_hash`
   **unchanged**. Read-only.
6. **S247** scores the recorded readings for completeness and truth, on these nights.

---

## Handover — paste this to the Claude cloud session

```text
Sprint 246 — every debate turn records how it read the evidence, before it argued.
Spec: docs/sprints/sprint-246-every-debate-turn-records-how-it-read-the-evidence.md on main
(read ALL of it, then CLAUDE.md). Repo: yury-gurevich/trading-agents.

Branch: sprint-246-every-debate-turn-records-how-it-read-the-evidence, cut from main AFTER S245 has
merged (check: docs/sprints/README.md's sprint-245 row reads MERGED). Never main. If your session
forces another branch name, use it and name it in the handback.
You have NO .env, NO gh, NO Azure and no route to download.pytorch.org. You DO need PyPI for
`uv sync --frozen --extra optimizer` (real DSPy 3.3.1, offline use only). If that fails, STOP and
report: never hand-write the golden fixture. Set LITELLM_LOCAL_MODEL_COST_MAP=True when importing
dspy. You cannot run `make gate-ran`: it is owed to the planner. Leave uv.lock untouched and say so.
Take the next free DL (likely DL-252; re-check on main).

This handover is complete: nobody will send you follow-up messages. If something in the spec is wrong
or blocked, record it in the handback (Return notes, "not done") and stop; do not wait.

What and why: the operator wants to record the GUIDED reasoning of the debate - DSPy ChainOfThought
with a typed reasoning field that the model writes BEFORE its argument: readings (metric, value
copied from the packet, meaning in THIS system, bearing), then gaps, then the argument - so it can
be scored later (S247) for completeness and truth. DSPy never runs in production: it renders the
format and parses offline into a golden fixture, and the runtime reproduces both byte for byte
without importing dspy, with one named deviation (strict JSON; no json_repair).

MUST RULE before any code: read, whole, agents/deliberator/laws/laws.md + test-plan.md,
docs/laws/conventions.md, docs/laws/drift-register.md. Fill the Law reading record first.

Law-cycle answer: YES (contract change + two guarantees). Deliberator v1.11: amend DLIB-TYP-01
(DebateTurnRecord also carries reasoning, reasoning_error); new DLIB-OUT-06 (each defender and
challenger turn records its guided reasoning exactly as written, or why it could not be read; an
unreadable reasoning never fails the turn or the order); new DLIB-OUT-07 (each debated order's record
carries the decision and the evidence packet); PARAM max_tokens row. Changelog, test-plan rows,
clause IDs in docstrings, rollups in docs/laws/ledger.md AND docs/laws/INDEX.md.

Build, in this order:
1. DL entry with the four decisions and rejected alternatives.
2. scripts/deliberation_guided_program.py (the signature and ChainOfThought program, exactly as the
   spec's Scope 2) and scripts/render_guided_turn_golden.py; run it with real DSPy; commit
   tests/fixtures/deliberation_guided_golden.json ALONE, with the command in the message.
3. Red first: B1, B2, B3, B5 (paste).
4. kernel/deliberation_guided.py: EvidenceReading + GuidedReasoning (exact field descriptions from
   Scope 1; value is a STRING), GUIDED_TURN_PREFIX (frozen), guided_system, guided_user,
   parse_guided_turn (DSPy's header regex; strict json.loads + pydantic; never imports dspy).
5. contracts: DebateTurnRecord.reasoning / .reasoning_error (optional, default None).
6. agents/deliberator/guided_turn.py: defender and challenger turns use the guided system and user
   messages through the same _LedgerLLM; text = the spec's rendering table; an unreadable reasoning
   -> text = raw completion stripped, reasoning None, reasoning_error set, the turn still returned;
   an empty completion still raises (DLIB-NEV-07).
7. review_record: transcript rows gain reasoning + reasoning_error; debates[ticker] gains decision +
   context. Grep every reader of transcript/debates; old rows must still read (B6).
8. settings: max_tokens default 4096 -> 8192 (why cites challenger max 3,026 + the readings); PARAM
   row.
9. PROMPT_MODULES + the recipe test's pinned roots.
10. scripts/guided_turn_replay.py (the planner's live instrument), fake-LLM covered.
11. Law cycle. 12. DL-70 plants (a)-(f): each red, pasted, restored. 13. make ci redirected to a
    file, exit 0, 100.00 %.

DO NOT:
- change the judge's prompt, message, parse or verdict path (B7), or anything execution reads.
- import dspy anywhere under kernel/, contracts/ or agents/, add it to an image, or change extras.
- repair malformed JSON, drop a turn, or fail an order because a reasoning is unreadable.
- validate or correct readings against the packet: record them exactly as written (scoring is S247).
- rename metrics, add a glossary, change the replay/eval harnesses, run GEPA, or make any real LLM
  call.
- hand-write or edit the golden fixture.
- grow any module past 200 (agent.py is 184); # noqa to bypass a rule.
- claim a live proof or GATE PROVEN: the replay check, the gate, the deploy and F1 are the planner's.
- pin a version: MINOR, next available at merge.

Handback — the planner returns it if ANY of these is missing:
[ ] Law reading record filled, including the law-cycle answer and contradictions/silences found.
[ ] The golden fixture's generating command and DSPy version, pasted; committed alone.
[ ] Test plan results: B1-B11, each with final test name, file, PASS, clause IDs cited.
[ ] The red runs of B1, B2, B3, B5 pasted before the implementation.
[ ] Each of the six DL-70 plants: what was planted, its red output, restored.
[ ] The list of transcript/debates readers you checked for old-row compatibility (B6).
[ ] Whether kernel/graph_vocabulary.py declares any key you added (retag vs full up).
[ ] Module line counts for every file touched (all < 200).
[ ] make ci: the file, exit code, passed/skipped, coverage 100.00 %, dependency audit, detect-secrets.
[ ] Exactly how uv.lock was touched (untouched and owed).
[ ] The design decisions under the DL you took, with rejected alternatives.
[ ] Return notes: scope held or moved; what you disagreed with after reading the laws; the
    replay/eval harness divergence for S247; that the judge now reads rendered readings.
[ ] Status: BUILT on the spec, and this sprint's README.md row leads with BUILT, in the same commit.
[ ] Owed items named: uv lock, make gate-ran, Windows make ci, the 20-call replay check, retag, F1.
Commit on the branch and PUSH it, then stop: no merge. Anything not met: "not done", never a
Result: for work not done.
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
Filled 2026-09-30 before the first code change. Read whole: `agents/deliberator/laws/laws.md` (v1.10),
`agents/deliberator/laws/test-plan.md`, `docs/laws/conventions.md`, `docs/laws/drift-register.md`.

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `contracts/deliberator.py` (`DebateTurnRecord`) | deliberator `laws.md` + `test-plan.md` | `DLIB-TYP-01` (amended: names `reasoning`, `reasoning_error`) | Yes: S205's rule means the new fields go into the clause text and the required-fields test, not only the model |
| `kernel/deliberation_guided.py`, `kernel/deliberation_guided_format.py` | same; conventions §3/§7 | `DLIB-OUT-06` (new), `DLIB-OBS-06` (one frozen system string per role), `DLIB-NEV-09` | Yes: `DLIB-NEV-09` binds any sentence about how our code behaves. The guided format states only the output structure, no fact about our code, so it needs no pin; checked, not assumed |
| `agents/deliberator/agent.py`, new `guided_turn.py` | same | `DLIB-OUT-06`, `DLIB-NEV-06`, `DLIB-NEV-07`, `DLIB-FAIL-01`/`-04`, `DLIB-OUT-03`/`-05` | Yes: `DLIB-NEV-07` decided the empty-argument case (DL-252 D3); `DLIB-OUT-05` rules out storing anything on `LLMCall` |
| `agents/deliberator/review_record.py` (+ `poll.py` carrying the proposition) | same | `DLIB-OUT-06`, `DLIB-OUT-07` (new), `DLIB-OBS-01`, `DLIB-OUT-02` | Yes: the packet goes on the order's `debates` entry, once (DL-252 D4) |
| `agents/deliberator/prompt_recipe.py` | same | `DLIB-OBS-07` | Yes: the three new modules are declared and the pinned roots gain `agents.deliberator.guided_turn` |
| `agents/deliberator/settings.py` (`max_tokens`) | same (`PARAM`) | `PARAM` `max_tokens` row | No |
| The judge (`verdict`, `judge_verdict`, `parse_verdict`) | same | `DLIB-TYP-03`, `DLIB-FAIL-04`, `DLIB-NEV-06` | Not touched (the ⚠️ invariant); B7 proves it |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **Yes, both**, as the
spec answers: two optional fields on `DebateTurnRecord` and two guarantees. Owed and done in this unit
of work: deliberator v1.10 → v1.11 (`DLIB-TYP-01` amended, `DLIB-OUT-06`, `DLIB-OUT-07`, `PARAM`
`max_tokens`), Changelog, test-plan rows, clause IDs in docstrings, rollups in `ledger.md` and
`INDEX.md`.

**Contradictions found between a law and this spec:** none that stop the sprint. Two readings to note:
(1) `DLIB-NEV-07` ("never records an empty debate turn") met a case the spec does not name: a
completion whose sections parse but whose `argument` is blank. DSPy accepts it; rendering it would put
`Argument: ` with nothing into the transcript. Resolved under the clause: the turn keeps its raw text
and records `reasoning_error = "empty field: argument"` (DL-252 D3), so nothing is dropped and nothing
empty is dressed up. (2) The `PARAM` table's `effort` (`max`) and `request_timeout_seconds` (`30.0`)
rows match `settings.py`, while the spec's measurements say `high` and 120 s: both come from the pack,
not the law. Not a contradiction; recorded so nobody "fixes" the table from the spec.

**Laws found silent where a decision was needed:** (1) Nothing says what a debater turn's `text` is when
the turn carries structure: `DLIB-OUT-02` says "per-ticker debate turns" and `DLIB-OBS-01` says the
transcript is reconstructable. The rendering is a design decision (DL-252 D2), and the new
`DLIB-OUT-06` names the reasoning, not the rendering. (2) No clause bounds the size of a
`DeliberationRun`; D4 stores the packet once per order for that reason. Neither is a drift (no law
disagrees with the code), so no register row.

**Clauses that were ⬜ and are now proven:** none were ⬜ before; `DLIB-OUT-06` and `DLIB-OUT-07` are new
and start proven by B3–B5; `DLIB-TYP-01` stays 🟩 with its required-fields test widened.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| B1 | *(builder fills)* | | | |

**Tests added beyond the plan:** *(builder fills)*

---

## Closeout — evidence

**Status:** *(BUILT at handback, MERGED at merge)*

**Tree the proofs ran in (and `.env` present?):** *(builder fills)*

**Result:** *(builder fills — what is now true, in the artefact's own words)*

**Files changed:** *(builder fills)*

**Design decisions:** *(builder fills — the DL taken, and where the rejected alternatives are)*

**Golden fixture:** *(builder fills — the command, DSPy version, commit)*

**Proof — the red run first:**

```text
(builder pastes)
```

**Proof — the green run:**

```text
(builder pastes)
```

**Guards planted:** *(builder fills — per plant (a)-(f))*

**Module line counts:** *(builder fills)*

**`make ci`:** *(builder fills — file, exit code, passed/skipped, coverage, dependency audit, detect-secrets)*

**`make gate-ran`:** *(planner — owed)*

**Not met / verified failing:** *(builder fills)*

---

## Return notes

- *(builder fills)*
