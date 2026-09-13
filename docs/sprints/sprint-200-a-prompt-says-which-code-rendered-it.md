<!-- Agent: planning | Role: sprint handover — prompt provenance on the LLM ledger -->
# Sprint 200 — a recorded prompt says which code rendered it, and what the whole question was

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-200-a-prompt-says-which-code-rendered-it`
**Status:** BUILT
**Version:** *next available PATCH at merge*
**Effort:** M
**Decisions:** [DL-162](../design-log.md) · work-queue **item 44** · **[DRIFT-056](../laws/drift-register.md) corrected** · **[DRIFT-057](../laws/drift-register.md) filed and corrected**

> **Why this bump kind.** PATCH. `DLIB-IDM-02` has claimed since S153 that recorded hashes *bound*
> what the model was asked, and only half the prompt was hashed — the code could not deliver what the
> book already said. The recipe digest is the instrument that makes an existing promise checkable, not
> a new capability.

---

## 🔴 MUST RULE — read the laws before any code

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/deliberator/laws/laws.md` | The deliberator's **locked constitution** | LOCKED; amendments only inside the law cycle this sprint owes |
| `agents/deliberator/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read before relying on a clause |
| `docs/laws/drift-register.md` | The correction worklist | The one law-adjacent file that may be appended to |

Binding sections here: **`IDM`**, **`OBS`**, **`OUT`**.

### The law-cycle question

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**Yes.** No `contracts/` change; the graph vocabulary gains two `LLMCall` properties and the
deliberator starts promising that a recorded prompt names the code that rendered it. Cycle owed and
done — record below.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `kernel/prompt_recipe.py`, `kernel/llm_ledger.py` | deliberator `laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `DLIB-IDM-02` (the bound), `DLIB-OUT-03` (what a row carries), `DLIB-OUT-05` (no payload text) |
| `agents/{deliberator,operator}/prompt_recipe.py` | both agents' law books | each writes the shared `LLMCall` under ADR-0020 |
| `orchestration/packs/trading_graph_vocabulary.json` | `docs/laws/conventions.md` | a vocabulary move makes the deploy a full `up` (S148/[DL-85](../design-log.md)) |

⚠️ **The invariant this sprint must not break: an `LLMCall` carries no prompt text.** `DLIB-OUT-05`
permits compact audit metadata only. The system prompt is **hashed, never stored** — asserted directly
by `test_the_system_prompt_text_is_never_stored`.

---

## Goal

Every `LLMCall` records a digest of the code that rendered its prompt, and a hash of the **system**
prompt beside the user prompt — so "is this stored hash comparable to today's renderer?" is answerable
from the row, and two calls that differed only in their system prompt stop being indistinguishable.

## Why (context)

Work-queue item 44, and [DRIFT-056](../laws/drift-register.md) which names the forced decision.
`DLIB-IDM-02` reads as though the recorded hashes bound what the model was asked; in fact
`prompt_hash` covered the **user string only**, so a role-prompt experiment — exactly the thing
ADR-0010 exists to run — left no trace. And with no renderer identity, a replay mismatch could not be
attributed: the model wandering and the prompt builder changing looked identical. S173 had to
re-derive [DL-104](../design-log.md)'s 56 % self-agreement from stored *verdicts* because its own runs
replay 0 of 18.

### Measured, 2026-09-13 — read before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Stored `defender:r1` turns that replay to their hash | **62 of 285 = 21.75 %** | *[re-measured]* `scripts/deliberation_reproducibility.py` against the live spine |
| The queue's carried figure | 57 of 280 = 20.36 % | *[carried — now superseded]* drifted as new runs landed; the register row is corrected to the new number |
| `PMRun` nodes on the spine | 69, **0 unreadable** | *[measured]* same run |
| Source `.py` files present in the agent image | yes | *[measured]* `agents/deliberator/Dockerfile` copies `kernel/`, `contracts/`, `agents/deliberator/` as source |
| `trading-agents` installed as a package in the image | **no** | *[measured]* `uv.lock` declares `source = { virtual = "." }`, so `importlib.metadata.version` would fail — this is why `code_version` was rejected |
| Deliberator recipe covers | **7 modules** | *[measured]* digest `19424f5b…` |
| Operator recipe covers | **3 modules** | *[measured]* digest `3fcfed8f…`, distinct from the deliberator's |

---

## Scope — and what is deliberately NOT here

1. **`kernel/prompt_recipe.py`** — `recipe_digest(modules)` hashes each module's dotted name and source
   bytes, order-independent, returning `unknown` if **any** module is unreadable.
2. **`LLMCall` gains `system_prompt_hash` and `prompt_recipe_hash`.** `prompt_recipe_hash` defaults to
   `unknown`, never to the running digest.
3. **Each agent declares its own module set** — `agents/deliberator/prompt_recipe.py` (7 modules) and
   `agents/operator/prompt_recipe.py` (3), with a test deriving the deliberator's from the real import
   graph.
4. **Law cycle** — `DLIB-OBS-07` added; `DLIB-IDM-02` ⬜ → 🟩; `DLIB-OUT-03` loses the word *rough*.
5. **Drift** — DRIFT-056 **CORRECTED**, DRIFT-057 filed and corrected.

### Out of scope

- **`code_version` on the row.** Rejected on measurement — see the road not taken.
- **Backfilling the existing 1,177 rows.** They have no recipe and now read `unknown`, which is true.
- **Making the 21.75 % go up.** This sprint makes the number *attributable*, not better. Raising it is
  a different question (should the renderer be stabilised, or old rows retired?) and needs this
  instrument first.

### The road not taken (LAW-06)

Full reasoning in [DL-162](../design-log.md):

- **`code_version` from the package metadata.** Rejected: the project is a `virtual` uv workspace, so
  it is not installed in the image and `importlib.metadata.version` raises. Reading `pyproject.toml`
  by path at runtime would work and adds a file dependency inside the veto path for a field that
  `DeployRecord` (S180) already answers better — it ties a running tag to the commit that built it.
- **A behavioural digest** — render a canonical fixture and hash the output. Tighter (a comment edit
  would not move it), rejected because the veto context is built from a `GraphStore`: a fixture render
  needs a fake graph inside the production call path, a far larger surface to be wrong in, guarding
  against nothing worse than an over-cautious mismatch.
- **Hashing the source of `contracts/` too.** Rejected: contracts carry payload shapes, not prompt
  text, so including them makes the digest move on every unrelated contract edit — a precise signal
  turned into noise.
- **Narrowing `DLIB-IDM-02`** to say the bound covers only the user context — DRIFT-056's second
  route. Rejected: the clause describes what we want to be true, and the cheaper half-truth would have
  retired the ambition instead of meeting it.

---

## Blast radius — measured 2026-09-13

| What | Detail |
| --- | --- |
| Files changed | `kernel/prompt_recipe.py` **88** (new), `kernel/llm_ledger.py` **153**, `agents/deliberator/prompt_recipe.py` **56** (new), `agents/operator/prompt_recipe.py` **29** (new), `agents/deliberator/agent.py` **180**, `agents/operator/agent.py` **185**, `agents/operator/ledger.py` **51**, the vocabulary pack, laws + test-plan + two rollups + drift register |
| Agents affected | deliberator, operator — neither imports the other |
| Contract change? | **No** |
| Graph vocabulary change? | **Yes** — `system_prompt_hash`, `prompt_recipe_hash` |
| New env keys / tunables | **none** |
| Deploy implication | **Full `up`, never a retag.** Pairs with S199, which also moved the pack — one `up` carries both. |

---

## Test plan

| # | Test | Must prove |
| --- | --- | --- |
| A1 | 🎯 System prompt hashed beside the user prompt | both hashes present and correct |
| A2 | 🪤 Two calls differing only in system prompt | same `prompt_hash`, different `system_prompt_hash` — DRIFT-056 in one assertion |
| A3 | 🪤 System prompt text never stored | the string appears in no property |
| A4 | Changing a module's source changes the digest | item 44's whole point |
| A5 | 🪤 Moving code between modules changes the digest | the module name is hashed too |
| A6 | 🪤 One unreadable module makes the digest `unknown` | fail loud, never partial |
| A7 | 🪤 An unrecorded renderer reads `unknown`, not the current one | the default must not lie about legacy rows |
| A8 | 🪤 The declared list covers the real import graph | the hand-maintained list cannot silently go stale |
| A9 | Operator declares its own recipe | distinct digest |
| A10 | 🎯 **Every** bound `DLIB-IDM-02` names is stamped | what earns the green, per DRIFT-056's instruction |
| A11 | 🪤 Token provenance and prompt provenance are independent | a CI-shaped `estimated` row still has a known renderer |

---

## Success factors

- [x] Every `LLMCall` names the renderer that produced its prompt, or reads `unknown`.
- [x] The system prompt is hashed; its text is never stored.
- [x] The declared module list is checked against the real import graph by a test.
- [x] No `contracts/` change, no new env key or tunable.
- [x] Design decisions recorded with rejected alternatives — [DL-162](../design-log.md).
- [x] Law cycle done: `DLIB-OBS-07` added, `DLIB-IDM-02` promoted, `DLIB-OUT-03` corrected, laws **v1.5**.
- [x] DRIFT-056 corrected by the route it named; DRIFT-057 filed and corrected.
- [x] Three guards planted, watched red, restored.
- [x] Every touched module < 200 lines.
- [x] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The declared module list is the entire correctness of the field.** A prompt-shaping module missing
from it produces the one failure that matters: two rows agreeing on the digest while their prompts were
built differently. A8 derives the list from the import graph so this fails in CI instead of in a year's
audit. Planting the omission of `context_stop` turned it red.

🪤 **The digest fails in the safe direction, and a comment edit moves it.** That is a false *"not
comparable"*, never a false *"comparable"*. Do not read a changed digest as proof a prompt changed;
read an **unchanged** digest as proof it did not.

🪤 **`prompt_recipe_hash` must never default to the running process's digest.** Every pre-S200 row
would then assert it came from today's code — strictly worse than the absence it replaces. A7 pins it.

🪤 **A sprint that changes what a recorded field *means* must re-read the clauses that describe it.**
S199 made `DLIB-OUT-03`'s word *rough* false the day it merged and did not notice. That is DRIFT-057,
and it is the cheapest class of drift to create.

---

## Law reading record

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `kernel/llm_ledger.py` | deliberator `laws.md` + `test-plan.md`; drift register | `DLIB-IDM-02`, `DLIB-OUT-03`, `DLIB-OUT-05` | **Yes, twice.** DRIFT-056 explicitly forbids closing on a test that exercises only the user half — that is why `test_llm_output_bounds.py` asserts all six bounds rather than the one I had fixed. And reading `DLIB-OUT-03` is how I found S199 had left the word *rough* false. |
| `kernel/prompt_recipe.py` | `docs/laws/conventions.md` | — | **Yes.** `import-linter` forbids `kernel → agents`, which is why the caller declares its own module set instead of the kernel guessing. |
| `agents/operator/prompt_recipe.py` | operator `laws.md` | shared-ledger clauses | **Yes.** It made clear the operator must not borrow the deliberator's digest — the field's whole purpose is to not make that kind of claim. |

**Law-cycle question:** **Yes** — a new guarantee, no `contracts/` change. Owed and done:
`DLIB-OBS-07` added, `DLIB-IDM-02` promoted ⬜ → 🟩, `DLIB-OUT-03` amended, laws **v1.4 → v1.5** with a
Changelog line, test-plan rows with clause IDs cited in docstrings, rollups updated in **both**
`docs/laws/ledger.md` and `docs/laws/INDEX.md`, and two drift rows resolved.

**Contradictions found between a law and this spec:** none.

**Laws found silent where a decision was needed:** none — `DLIB-OBS-07` fills the silence DRIFT-056
identified.

**Clauses that were ⬜ and are now proven:** `DLIB-OBS-07` (new) and **`DLIB-IDM-02`** (promoted).
Rollup **19 / 55**, derived by the coverage checker — it rejected my claim of 17/54 and told me the
right number, which is the only reason I am quoting it.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/wt-s200`, branch
`sprint-200-a-prompt-says-which-code-rendered-it`, **no `.env`**. The reproducibility re-measurement
(62/285) and the digest values were taken in the **main** checkout, where `.env` lives; no test depends
on them.

**Result:** An `LLMCall` written by the deliberator or operator now carries `system_prompt_hash` and
`prompt_recipe_hash`. The recipe is a sha256 over the dotted name and source bytes of every module that
shapes that agent's prompts — 7 for the deliberator (`context`, `context_market`, `context_pm`,
`context_stop`, `context_values`, `kernel.deliberation`, `kernel.deliberation_prompts`), 3 for the
operator (`evidence`, `grammar`, `prompts`). A row written before S200, or by code whose source cannot
be read, reads `unknown` rather than claiming the current renderer.

**Design decisions:** recorded as [`DL-162`](../design-log.md) — four rejected alternatives with the
measurement that killed each.

**Guards planted (DL-70) — three, each watched red and restored:**

1. **`context_stop` removed from the declared list.**
   `test_the_deliberator_declares_every_module_that_builds_its_prompt` red — and it caught
   `context_stop` *plus its own transitive imports*, which is the behaviour that makes the list
   maintainable. Restored.
2. **`prompt_recipe_hash` defaulted to a concrete digest** instead of `unknown`.
   `test_an_unrecorded_renderer_reads_as_unknown_not_as_this_one` red: `assert 'abc123' == 'unknown'`.
   Restored.
3. **`system_prompt_hash=digest_text(system_prompt)` removed** — the exact pre-S200 state.
   Three tests red, the decisive one being `assert '' != ''` in
   `test_two_calls_differing_only_in_system_prompt_are_distinguishable` — DRIFT-056 reproduced as a
   single failing assertion. Restored.

**Module line counts:** `kernel/prompt_recipe.py` **88**, `kernel/llm_ledger.py` **153**,
`agents/deliberator/prompt_recipe.py` **56**, `agents/operator/prompt_recipe.py` **29**,
`agents/deliberator/agent.py` **180**, `agents/operator/agent.py` **185**,
`agents/operator/ledger.py` **51**, `tests/test_prompt_recipe.py` **177**,
`tests/test_llm_ledger_provenance.py` **93**,
`agents/deliberator/tests/test_llm_output_bounds.py` **155**.

**`make ci`:** redirected to a file, read from the file, never piped. **Exit code 0.**
`2669 passed, 6 skipped`, coverage `100.00 %`. pip-audit `No known vulnerabilities found`.
detect-secrets `Passed`.

**`make gate-ran`:** filled after the push.

**Not met / verified failing:** none. Named and deliberately not attempted: `code_version` (rejected on
measurement), backfilling legacy rows, and raising the 21.75 % itself.

---

## Return notes

- **Scope held.** One thing grew: `DLIB-IDM-02`'s promotion was not in the original shape of item 44,
  but DRIFT-056 made it the honest close — hashing the system prompt without proving the clause would
  have left the register row open for no reason.
- **What I'd push back on in item 44's wording:** it says *"nothing records which code version produced
  an `LLMCall`"*, which reads as a request for a version string. A version string does not answer the
  question the item's own measurement poses — you would still have to know whether the renderer moved
  between two versions. A content digest answers it directly, and the repo already has a better
  version↔commit record in `DeployRecord`.
- **What the next sprint should know:** the 21.75 % is now *attributable* but not *improved*, and the
  instrument will not improve it. The open question this enables is a decision, not a build: when a
  replay mismatch is explained by a recipe change, is the right move to stabilise the renderer or to
  retire old rows from the corpus? Both are cheap once the rows say which they are.
- 🪤 **Deploy note:** this and S199 both move the vocabulary pack. Deploy them with **one** full `up`,
  and verify the deployed `GRAPH_VOCABULARY_B64` decodes byte-identical to the repo pack and declares
  `token_source`, `prompt_recipe_hash` **and** `system_prompt_hash` before trusting any write.
