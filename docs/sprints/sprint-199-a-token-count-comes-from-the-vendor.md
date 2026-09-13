<!-- Agent: planning | Role: sprint handover — vendor token accounting and claimed prompt caching -->
# Sprint 199 — a recorded LLM cost is the provider's own number, and says so when it is not

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-199-a-token-count-from-the-vendor`
**Status:** BUILT
**Version:** *next available PATCH at merge*
**Effort:** M
**Decisions:** [DL-161](../design-log.md) the token/cache decision · [DL-160](../design-log.md) the 3.2× pricing error this closes · [DL-150](../design-log.md) the original word-count correction · work-queue **item 43**

> **Why this bump kind.** PATCH. No agent gains a capability. `DLIB-OBS-02` has promised
> per-calling-agent LLM spend attribution since S153 and the numbers behind it were word counts —
> the code could not deliver what the book already said. Prompt caching is not a new product
> behaviour either; it is the same call, billed correctly.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/deliberator/laws/laws.md` | The deliberator's **locked constitution** | LOCKED. Read-only during a build, except the amendment this sprint owes |
| `agents/deliberator/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read before relying on a clause |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status; `drift-register.md` is appendable |

Binding sections here: **`OBS`**, **`IDN`**, **`SEC`**.

### The law-cycle question

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**Yes.** No `contracts/` file changes, but the graph vocabulary gains three `LLMCall` properties and
the deliberator starts promising something it did not: that a recorded token count is the provider's
own, and that a claimed cache discount is falsifiable. Law cycle owed and done — see the record below.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `kernel/llm_ledger.py`, `kernel/llm_tokens.py` | `agents/deliberator/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `DLIB-OBS-02` promises spend attribution; `DLIB-IDN-02` permits shared `LLMCall` writes under ADR-0020 |
| `agents/deliberator/llm_anthropic.py`, `llm_openai.py` | same | `DLIB-OUT-03`, `DLIB-OUT-05`, `DLIB-FAIL-04` — a stopped completion is a failure with its reason named |
| `agents/operator/llm_anthropic.py` | `agents/operator/laws/laws.md` | shares the substrate ledger |
| `orchestration/packs/trading_graph_vocabulary.json` | `docs/laws/conventions.md` | a vocabulary move makes the deploy a full `up`, not a retag (S148/DL-85) |

⚠️ **The invariant this sprint must not break: an `LLMCall` carries no prompt or completion text.**
`DLIB-OUT-05` allows compact audit metadata only. Token counts and a provenance stamp are metadata;
a usage object must never be written through verbatim.

---

## Goal

Every `LLMCall` row records the token counts the provider itself reported, declares whether those
counts are vendor-measured or locally estimated, and records the cached input tokens a prompt-cache
marker actually bought — so a cost figure derived from the ledger is either a measurement or visibly
a floor, and never silently the wrong one.

## Why (context)

Work-queue item 43 has been open and ranked 🚨 since 2026-09-03. `kernel/llm_ledger.py` wrote
`max(1, len(text.split()))` into `tokens_in`/`tokens_out` — a **word** count — and the caller passed
`prompt=user`, so the system prompt was excluded entirely. Every cost figure this project has
published came off those rows, including `/audit-costs`.

🚨 **It stopped being an accuracy problem and became a spending one.** S173 Part B priced its sweep
off these counts, was **3.2× low**, and the correction was bought by spending **$58** on a single
round that produced no verdicts ([DL-160](../design-log.md)). The same trip measured
`cache_read` at **0 across all 2,957 calls**, with byte-identical system prompts within each round —
the discount was available the whole time and was never requested.

### Measured, 2026-09-13 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| `DEFENDER_SYSTEM` | **167 tokens** | *[measured]* `messages.count_tokens`, `claude-opus-5`, live API |
| `CHALLENGER_SYSTEM` | **2,561 tokens** | *[measured]* same call |
| `JUDGE_SYSTEM` | **2,474 tokens** | *[measured]* same call |
| `claude-opus-5` minimum cacheable prefix | **512 tokens** | *[measured — documentation]* so the defender prompt **cannot** cache and the other two can |
| `usage` fields the API returns | `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens` | *[measured]* one live call, response read back |
| Anthropic `input_tokens` excludes cached tokens | true | *[measured]* live cache-cold call returned `input_tokens=9`, both cache fields 0 |
| OpenAI `prompt_tokens` **includes** `cached_tokens` | true | *[measured — documentation]*; the opposite convention, hence the subtraction |
| Existing `LLMCall` rows on the spine | **1,177** | *[measured]* `select count(*) … label='LLMCall'` |
| Nightly LLM call volume, 2026-09-08..-11 | **2, 1, 1, 1** | *[measured]* grouped by `created_at` date — this is what killed live batch mode |
| `main` @ `020fd8f` fails `pip-audit` | **6 CVEs**, `httpx2`/`httpcore2` 2.9.1 | *[measured]* `uv run pip-audit` in the **main** checkout, before any of this work |

---

## Scope — and what is deliberately NOT here

1. **`kernel/llm_tokens.py`** — a normalised `LLMUsage` (`tokens_in` = *uncached* input), a dotted-path
   `usage_count` reader that degrades to 0 rather than raising, and `token_counts()` which prefers the
   vendor and stamps the fallback.
2. **`LLMCall` gains `cache_read_tokens`, `cache_write_tokens`, `token_source`** in the vocabulary pack,
   written by `kernel/llm_ledger.py`. `write_llm_call` defaults `token_source` to `estimated`, so a
   caller that forgets the stamp cannot be credited with a measurement.
3. **All three adapters report `last_usage`** — deliberator Anthropic, deliberator OpenAI (with the
   subtraction), operator Anthropic. Both agents forward it, **including on the stopped path**.
4. **`cache_control` on the deliberator's frozen role prompt** (5-minute TTL) and **on the batch
   harness's per-round system prompt** (`ttl: "1h"`).
5. **The pricer applies the cache rates** (`llm_pricing.json` gains `cache_multipliers`) and reports
   `estimated_calls`, so a total built on legacy rows declares itself a floor.

### Out of scope (do NOT build this sprint)

- **Batch mode for the live nightly debate.** Operator decision 2026-09-13, on the measured volume
  above. Harness only.
- **Backfilling the 1,177 existing rows.** They are estimates; `token_source` now says so. Item 43's
  own wording is "backfill nothing".
- **Item 44** (`LLMCall` carrying the code version that produced it). Adjacent, separately ranked,
  and it drags the same pack — deliberately left so this diff stays readable.
- **Turning `DLIB-OBS-02` green.** Correcting an input is not proving the claim. See the law record.

### The road not taken (LAW-06)

Recorded in full in [DL-161](../design-log.md): a 1.3× correction factor (rejected — the ratio is not
constant), folding cached tokens into `tokens_in` (rejected — three billing rates), a shared
vendor-field name table in the kernel (rejected — the two vendors' conventions are opposite and a
field map double-counts), live batch mode (rejected on measured volume), and caching the operator's
system prompt (rejected — `tools` renders ahead of `system` and varies per call).

---

## Blast radius — measured 2026-09-13

| What | Detail |
| --- | --- |
| Files changed | `kernel/llm_tokens.py` **137** (new), `kernel/llm_ledger.py` **132**, `kernel/__init__.py`, `agents/deliberator/llm_anthropic.py` **129**, `agents/deliberator/llm_openai.py` **126**, `agents/deliberator/agent.py` **178**, `agents/operator/llm_anthropic.py` **103**, `agents/operator/agent.py` **183**, `surfaces/dashboard/llm_cost_tokens.py` **101** (new), `surfaces/dashboard/llm_costs.py` **185**, `scripts/deliberation_replay_batch.py` **240**, two packs, laws + test-plan + two rollups |
| Agents affected | deliberator, operator — neither imports the other; both reach the ledger through `kernel` |
| Contract change? | **No** — no file in `contracts/` changes |
| Graph vocabulary change? | **Yes** — three new `LLMCall` properties |
| New env keys / tunables | **none** |
| Deploy implication | **Full `up`, never a retag.** The vocabulary pack moves, so a retagged image would meet the S148/[DL-85](../design-log.md) fail-closed write guard mid-cascade. Verify the *deployed* `GRAPH_VOCABULARY_B64` decodes byte-identical to the repo pack and declares `token_source`. |

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 Ledger records the vendor's counts | a capture with `LLMUsage` set | the row carries the provider's four numbers and `token_source="vendor"` |
| A2 | Absent usage stamps `estimated` | a capture with no usage | word counts survive, stamped `estimated` |
| A3 | 🪤 The two row shapes are distinguishable | a vendor row whose numbers equal the word counts | only `token_source` separates them |
| A4 | 🪤 A truncated completion still records what it burned | an LLM that sets usage then raises `max_tokens` | `tokens_out=4096` recorded, not 0 |
| A5 | 🪤 OpenAI cached tokens are subtracted | `prompt_tokens=3000`, `cached=2048` | `tokens_in=952`; `tokens_in + cache_read == prompt_tokens` |
| A6 | 🪤 Cached > prompt cannot go negative | `prompt_tokens=100`, `cached=500` | `tokens_in=0`, `cache_read=100` |
| A7 | The live system block carries a cache marker, 5-minute TTL | — | the exact block dict; no `ttl` key |
| A8 | The batch request carries a marker with `ttl: "1h"` | one `BatchRequest` | the exact block dict, and `custom_id` untouched |
| A9 | 🪤 The operator's system prompt is sent **unmarked** | a faked operator call | a plain string, because `tools` renders first |
| A10 | Cached tokens price at their own multipliers | a row with all four groups | `5.00 + 0.50 + 6.25` = `11.75` |
| A11 | 🪤 A catalogue without cache rates charges **full** input price | `cache_multipliers` deleted | fails expensive, never free |
| A12 | 🪤 A total built on legacy rows declares itself a floor | one legacy + one vendor row | `estimated_calls == 1` and the note says so |
| A13 | A stale usage never survives a failed call | a second call that raises | `last_usage is None` |

---

## Success factors

- [x] Every `LLMCall` the fleet writes carries the provider's own counts, or is stamped `estimated`.
- [x] Cached input tokens read and written are recorded, and priced at their own rates.
- [x] A truncated or refused completion still records its tokens (A4).
- [x] No `contracts/` change; no new env key or tunable.
- [x] Design decisions recorded with rejected alternatives — [DL-161](../design-log.md).
- [x] Law cycle done: `DLIB-OBS-05`, `DLIB-OBS-06`, laws **v1.4**, rollup derived by the gate.
- [x] Every new guard planted, watched red, restored — three, listed below.
- [x] Every touched module < 200 lines (`scripts/` is outside the size gate's scope, as before).
- [x] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **A cache marker that cannot cache looks exactly like one that can.** The defender prompt is 167
tokens against a 512-token minimum: the API accepts the marker, raises nothing, and reports
`cache_read_input_tokens: 0` forever. Do not read a zero there as a bug.

🪤 **Round 1 of any sweep will show no cache activity at all**, because it is the only all-defender
round. Read the role before reading the number.

🪤 **`git checkout <file>` in a worktree reverts to the index, not to your last edit.** Used to restore
a planted guard here and it wiped the implementation; re-applied by hand. Back the file up instead.

🪤 **The pricing pack and the code must move together.** Shipping `cache_control` without
`cache_multipliers` would have priced cache reads at the full input rate — a *new* wrong number in the
opposite direction from the one being fixed.

---

## Law reading record

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `kernel/llm_ledger.py`, `kernel/llm_tokens.py` | deliberator `laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `DLIB-OBS-02`, `DLIB-IDN-02`, `DLIB-OUT-03` | **Yes.** `DLIB-OBS-02` turned out to be ⬜, not 🟩 — so the clause my work serves was never proven. That changed what I claimed, not what I built (below). |
| `agents/deliberator/llm_anthropic.py` / `llm_openai.py` | same | `DLIB-OUT-05`, `DLIB-FAIL-04` | **Yes.** `DLIB-FAIL-04` names a stopped completion a *failure*; reading it is what prompted capturing usage on the raise path, which the planted guard then proved mattered. |
| `agents/operator/llm_anthropic.py` | operator `laws.md` | shared-ledger clauses | No. |
| vocabulary pack | `docs/laws/conventions.md` | — | **Yes.** Confirmed the deploy is a full `up`, recorded in Blast radius. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **Yes** — a new
guarantee, no `contracts/` change. Owed and done: `DLIB-OBS-05` and `DLIB-OBS-06` added, laws
**v1.3 → v1.4** with a Changelog line, a `test-plan.md` row per clause with clause IDs cited in the
test docstrings, and the rollup updated in **both** `docs/laws/ledger.md` and `docs/laws/INDEX.md`.

**Contradictions found between a law and this spec:** none.

**Laws found silent where a decision was needed:** none that needed a drift row. `DLIB-OBS-02` is
silent on *where* the numbers come from, which is precisely what `DLIB-OBS-05` now says.

**Clauses that were ⬜ and are now proven:** `DLIB-OBS-05` and `DLIB-OBS-06` — both **new**, both green.
🟠 **`DLIB-OBS-02` stays gray, deliberately.** It promises per-calling-agent spend attribution. This
sprint corrects the *numbers* that clause would be read through, and adds no functional deliberator
test that proves the attribution itself. Correcting an input is not proving the claim. Rollup
**17 / 54**, a number the coverage checker derived — it rejected my arithmetic twice before I stopped
doing arithmetic.

---

## Test plan results

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_ledger_records_the_vendors_own_counts` | `tests/test_llm_ledger_tokens.py` | PASS | `DLIB-OBS-05` |
| A2 | `test_ledger_stamps_a_word_count_as_estimated` | same | PASS | `DLIB-OBS-05` |
| A3 | `test_vendor_and_estimated_rows_are_distinguishable` | same | PASS | `DLIB-OBS-05` |
| A4 | `test_a_truncated_completion_still_records_what_it_burned` | `agents/deliberator/tests/test_ledger_usage_forwarding.py` | PASS | `DLIB-OBS-05` |
| A5 | `test_cached_tokens_are_subtracted_from_the_input_count` | `agents/deliberator/tests/test_llm_openai_usage.py` | PASS | `DLIB-OBS-05` |
| A6 | `test_more_cached_than_prompt_tokens_cannot_go_negative` | same | PASS | `DLIB-OBS-05` |
| A7 | `test_system_prompt_is_sent_as_a_cache_marked_block`, `test_live_path_uses_the_five_minute_ttl_not_the_one_hour_ttl` | `tests/test_deliberator_anthropic_cost.py` | PASS | `DLIB-OBS-06` |
| A8 | `test_the_submitted_system_block_carries_a_cache_marker`, `test_the_batch_path_uses_the_one_hour_ttl_not_the_default`, `test_caching_does_not_disturb_the_rest_of_the_request` | `tests/test_replay_batch_caching.py` | PASS | `DLIB-OBS-06` |
| A9 | `test_the_operator_system_prompt_is_sent_unmarked` | `agents/operator/tests/test_operator_llm_usage.py` | PASS | `DLIB-OBS-06` |
| A10 | `test_cached_tokens_are_priced_off_the_input_rate_at_their_own_multiplier`, `test_caching_is_cheaper_than_not_caching_for_the_same_work` | `surfaces/tests/test_dashboard_llm_cache_costs.py` | PASS | — (surfaces) |
| A11 | `test_a_catalogue_without_cache_rates_charges_full_input_price` | same | PASS | — |
| A12 | `test_a_total_built_on_word_counts_declares_itself_a_floor` | same | PASS | — |
| A13 | `test_a_failed_call_does_not_leave_the_previous_usage_behind`, `test_a_failed_operator_call_clears_the_previous_usage` | `tests/test_deliberator_anthropic_cost.py`, `agents/operator/tests/test_operator_llm_usage.py` | PASS | `DLIB-OBS-05` |

**Tests added beyond the plan:** `tests/test_llm_tokens.py` (7 tests on the port itself — dotted-path
reads, every unreadable shape, the all-zero-is-no-usage rule) and
`test_a_provider_that_reports_no_usage_falls_back_and_says_so`. Added because the port is where a
silent zero would be introduced, and a zero that prices as free is the failure mode this sprint
exists to remove.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/wt-s199`, branch
`sprint-199-a-token-count-from-the-vendor`, **no `.env`**. The three measurement numbers at the top
(`count_tokens` against the live API, the live `usage` shape, the spine row counts) were taken in the
**main** checkout where `.env` lives; no test depends on them.

**Result:** An `LLMCall` written by the deliberator or the operator now carries
`input_tokens`/`output_tokens` as the provider reported them, plus `cache_read_tokens` and
`cache_write_tokens`, plus `token_source` declaring the counts vendor-measured or estimated. The
deliberator's frozen role prompt is sent as a cache-marked block (5-minute TTL) and the batch
harness's per-round prompt as a `ttl: "1h"` block. `llm_cost_projection` prices the three input groups
at their own rates and reports `estimated_calls`, so a total containing legacy rows states that it is
a floor.

**Files changed:** as listed in Blast radius, plus `tests/test_llm_tokens.py`,
`tests/test_llm_ledger_tokens.py`, `tests/test_replay_batch_caching.py`,
`tests/test_deliberator_anthropic_cost.py` (split from `test_deliberator_anthropic.py` at the
200-line block), `agents/deliberator/tests/test_llm_openai_usage.py`,
`agents/deliberator/tests/test_ledger_usage_forwarding.py`,
`agents/operator/tests/test_operator_llm_usage.py`,
`surfaces/tests/test_dashboard_llm_cache_costs.py`, `uv.lock`, `pyproject.toml`.

**Design decisions:** recorded as [`DL-161`](../design-log.md) — five rejected alternatives with the
measurement that killed each.

**Guards planted (DL-70) — three, each watched red and restored:**

1. **`set_usage` moved into the success-only branch** of `_LedgerLLM.complete`.
   `test_a_truncated_completion_still_records_what_it_burned` → `assert 0 == 4096`. 🚨 **Not just
   missing — zero**: the estimate fallback sees an empty response, so the fleet's most expensive
   calls would have priced as free. Restored (and the finding is now a comment at the call site).
2. **`cache_control` removed** from `cacheable_system`. Two tests red:
   `test_system_prompt_is_sent_as_a_cache_marked_block` and
   `test_anthropic_client_returns_text_blocks`. Restored.
3. **OpenAI's `prompt_tokens` mapped straight across** instead of subtracting `cached_tokens`.
   `test_cached_tokens_are_subtracted_from_the_input_count` → `assert 3000 == 952`, and
   `test_more_cached_than_prompt_tokens_cannot_go_negative` → `assert 100 == 0`. Restored.

**Module line counts:** `kernel/llm_tokens.py` **137**, `kernel/llm_ledger.py` **132**,
`agents/deliberator/llm_anthropic.py` **129**, `agents/deliberator/llm_openai.py` **126**,
`agents/deliberator/agent.py` **178**, `agents/operator/llm_anthropic.py` **103**,
`agents/operator/agent.py` **183**, `surfaces/dashboard/llm_cost_tokens.py` **101**,
`surfaces/dashboard/llm_costs.py` **185**, `tests/test_deliberator_anthropic.py` **127**,
`tests/test_deliberator_anthropic_cost.py` **117**.

**`make ci`:** redirected to a file, read from the file, never piped. **Exit code 0.**
`2653 passed, 6 skipped`, coverage `100.00 %`. pip-audit `No known vulnerabilities found`.
detect-secrets `Passed` (both invocations).

🚨 **The gate was red on `main` before this sprint touched anything, and the fix is in this branch.**
`uv run pip-audit` in the **main** checkout at `020fd8f` reported **6 known vulnerabilities** —
`httpx2` and `httpcore2` at 2.9.1 (PYSEC-2026-3844 through -3849), transitive through `anthropic`.
Nothing in S199 introduced them and nothing in S199 could have passed the gate with them present, so
`uv lock --upgrade-package httpx2 --upgrade-package httpcore2` (→ **2.12.0** both) is committed
**separately and first** on this branch, with its own PATCH bump, so the CVE fix is not buried inside
a feature diff.

**`make gate-ran`:** see below — filled after the push.

**Not met / verified failing:** none. Two things deliberately not attempted and named above:
`DLIB-OBS-02` stays gray, and the 1,177 existing rows are not backfilled.

---

## Return notes

- **Scope held**, with one addition forced by measurement: `llm_pricing.json` + the pricer. Shipping
  the marker without the rates would have introduced a new wrong number instead of fixing one.
- **What I'd push back on in item 43's own wording:** it reads "small — capture `usage` and set
  `cache_control` at the two adapters". There are **three** adapters (the operator has its own
  Anthropic client — which is what item 7 is about), and the cache half is not small, because a
  discount that nothing records is not a discount. The split into 43a/43b/43c is the real shape.
- **What the next sprint should know:** output tokens dominate this bill, not input. Round 1 of the
  S173 sweep was ~$0.039/call at list price, of which roughly ¾ is output at `effort: max`. Caching
  and batch together reach maybe 30 % of it. The remaining lever is `effort`/`max_rounds` — the
  question the operator deliberately stopped on price, and it is now measurable without re-buying
  the measurement, because `cache_read_tokens` and real `tokens_out` are recorded per call.
- 🚨 **Found while measuring, unrelated to this diff and ranked above it — now work-queue item 50.**
  The veto failed open on **every order for four consecutive nights** (2026-09-08 → 09-11, the
  Anthropic credit balance hitting zero after S173's $58 round), **five orders reached the broker**
  recorded as `verdict: "uphold"`, and **zero Flags, zero Faults, zero Incidents** were raised.
  Credit is restored, so the next run will debate — but nothing detected it, and that is the second
  half of the operator's etalon bar failing.
