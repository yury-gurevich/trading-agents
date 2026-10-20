<!-- Agent: planning | Role: sprint handover -->
# Sprint 284 — A headline counts only for the company it names

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-284-a-headline-counts-only-for-the-company-it-names`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** M
**Decisions:** [DL-308](../design-log.md) (decided, nine decisions with the roads not taken) · work-queue 108 · [DL-264](../design-log.md) amendment 3 (where it was found)

> **Why this bump kind.** No new capability: the sentiment pillar already promises the ticker's news tone, and it scores other companies' news and market roundups as the ticker's. A PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`OUT`** (OUT-02, OUT-06, OUT-10, the new OUT-11), **`OBS`** (OBS-04), **`IDM`** (IDM-01), **`FAIL`** (FAIL-04), **`PARAM`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes: a new guarantee, no contract change.** The analyst now guarantees whose headlines its lexicon pillar scores. The cycle is written for you in Appendix section 2: `ANLZ-OUT-11` and a PARAM row in `agents/analyst/laws/laws.md` (v1.11 → v1.12, a Changelog line), its `test-plan.md` row naming your tests, the rollup **30 / 53 → 31 / 54** in both `docs/laws/ledger.md` and `docs/laws/INDEX.md`. Apply it exactly; the gate recomputes the rollup.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/analyst/domain/sentiment_subject.py` (new), `domain/data/company_names.json` (new) | `agents/analyst/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `ANLZ-OUT-11` (new): whose headlines score, the minimum, the unlisted ticker, the recorded counts |
| `agents/analyst/domain/scoring.py` | same | `ANLZ-OUT-02` (the optional `sentiment_score`), `ANLZ-OUT-10` (recorded constants), `ANLZ-OBS-04` (metric units), `ANLZ-IDM-01` (batch weights, unchanged) |
| `agents/analyst/settings.py` | same, its `PARAM` table | a new tunable needs its PARAM row (the PARAM/settings sync step) |
| `agents/analyst/tests/{helpers,test_analyst_agent,test_analyst_domain,test_sentiment_reading}.py` | same | five existing fixtures scored headlines that name no company; Appendix section 2 fixes them so their expected values hold |

⚠️ **`MarketData.news` does not change.** The provider still serves and records every headline; only the analyst's lexicon pillar reads fewer. If your change touches `agents/provider/`, `contracts/` or the debaters, stop and report.

---

## Goal

The analyst's lexicon sentiment pillar scores only the served headlines that name the ticker's company (a name from a bundled company table, or a ticker mark). Below two such headlines carrying a lexicon word, a name has no sentiment pillar and its blend renormalises. A ticker the table does not list scores on every headline as before. Every name with served news records how many headlines were served, how many were its own, and whether the filter applied.

## Why (context)

Work-queue 108: on `sched-2026-10-05` MRK cleared its confidence floor only on its sentiment score, while 7 of its 20 headlines were about Vaxcyte's vaccine trial. Finnhub's `/company-news` returns whatever mentions the symbol, and its `related` field only echoes the symbol asked for, so the feed cannot say whose news a headline is. Every night since, more than half of what the pillar reads is someone else's news.

### Measured, 2026-10-20 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Served headlines that name the ticker's company | **844 of 1,930 (44 %)**; 15 % another universe company only; 41 % neither | *[measured 2026-10-20]* `wq108_subject.py sched-2026-10-19` on the live `MarketData` snapshot (OneDrive `trading-agents-data/wq108-2026-10-20/`); hand alias table, a floor (it misses forms like *"Lillys"*) |
| The same share, night by night | 40 % to 46 % on nine nights, `sched-2026-10-05` to `sched-2026-10-19` | *[measured 2026-10-20]* `wq108_rule.py` |
| A replay of the analyst equals the record | 303 of 326 names over the nine nights (39 of 39 on 10-19); the 23 others are names held now and not then | *[measured 2026-10-20]* `s284_f1.py` on `main` `869734ad`: `f1_main_869734ad.txt` |
| Decisions this sprint changes over those nine nights | **2 of 303**: CL rejected → buy on 10-12 (0.637) and 10-19 (0.607); 213 confidences move by 0.01 or more, most up | *[measured 2026-10-20]* `s284_f1.py` on the prototype `2f44c5f8` (its production code = `573b44fa`'s): `f1_proto.txt` vs `f1_main_869734ad.txt` |
| Names left with no sentiment pillar at a minimum of 1 / 2 / 3 / 4 | 4 % / **15 %** / 38 % / 54 % | *[measured 2026-10-20]* `wq108_rule.py` (DL-308's table) |
| MRK's own 10-05 case under the rule | not replayed | *[ASSUMED — not measured]* MRK is held now, so its 10-05 decision cannot be replayed with today's book; and two of its seven Vaxcyte headlines name Merck, so they still count (Traps) |

---

## Scope — and what is deliberately NOT here

1. **The company table and the subject filter** (Appendix section 1): `company_names.json` with one entry per ticker of `scripts/universe_sp100.txt`; `sentiment_subject.py` with `own_headlines` and `subject_sentiment`; `scoring.py` calls `subject_sentiment` in place of `score_sentiment`; the tunable `sentiment_min_own_headlines` (2, bounds 1 to 10) in `settings.py`.
2. **The law cycle** (Appendix section 2): `ANLZ-OUT-11`, the PARAM row, v1.12, the test-plan row, both rollups.
3. **Five existing fixtures name their company** (Appendix section 2): `helpers.APPLE_NEWS` (two own, all-positive headlines) for three agent-level tests; the two blend tests keep one own headline and set `sentiment_min_own_headlines=1`. Every expected value stays as it was.
4. **Your tests A1 to A9** in `agents/analyst/tests/test_sentiment_subject.py`, under the names the test-plan row gives.

### Out of scope (do NOT build this sprint)

- **The debaters' packet.** It still lists every served headline; whether it should mark the scored ones is a separate question.
- **The provider's sentiment shadow and the forecaster's challengers** keep their own inputs.
- **Matching a headline to its main subject.** A headline that names two companies counts for both (*"takes aim at Pfizer and Merck"* counts for MRK).
- **No ADR reversal**, no contract change, no graph vocabulary change.

### The road not taken (LAW-06)

All in [DL-308](../design-log.md): dropping headlines at the provider (loses the record of what was served); a relevance field from the vendor (Finnhub has none); weighting each headline by relevance (no relevance model to weight with); a finance-tuned model (scores tone, not subject); Finnhub `/stock/profile2` names at run time (a vendor read a name a night, no brands, a replay would need them recorded); a minimum of 3 (38 % of names lose the pillar).

---

## The design decisions this sprint has to make

**None left: all nine are decided in [DL-308](../design-log.md)** (D1 to D9), measured first. If a law reading contradicts one, stop and report. Do not add a DL entry.

---

## Blast radius — measured 2026-10-20

| What | Detail |
| --- | --- |
| Files changed | new `agents/analyst/domain/sentiment_subject.py` **81**, new `agents/analyst/domain/data/company_names.json` (99 entries); `scoring.py` 187 → **191**; `settings.py` 152 → **161**; `laws.md`, `test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`; tests `helpers.py` 191 → **198**, `test_analyst_agent.py` 198 → **199**, `test_analyst_domain.py` **199**, `test_sentiment_reading.py` 187 → **192**; your new `test_sentiment_subject.py` (the planner's is **164**) |
| Agents affected | analyst only; it imports no other agent (the universe file is read as text by the test) |
| Contract change? | No (`ScoreBreakdown.metrics` is a free `dict[str, float]`) |
| Graph vocabulary change? | No new label or property: the three metrics travel inside the existing metrics map |
| New env keys / tunables | `sentiment_min_own_headlines` (`ANALYST_SENTIMENT_MIN_OWN_HEADLINES`), default 2: the default needs no env key; the analyst image reads it from the code |
| Deploy implication | **Image-only retag.** `agents/analyst/` **is a fidelity decision path**: the deploy restarts the fidelity count, so the planner deploys after the fidelity verdict, on the operator's word (DL-308 D9) |
| Rollback | Retag the analyst (and the fleet) back to the tag before this one. Nothing else to undo: no graph write, order, schema, pack or infra setting changes |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Write the tests A1 to A9** under the Test plan's names and run them on the unchanged tree: the file cannot import (`sentiment_subject` does not exist yet). Paste that red output.
3. **Apply Appendix section 1 exactly**, then **section 2 exactly**. Change nothing else.
4. **Prove the guards can fail (DL-70)**: plant B1 to B25 (Traps) one at a time against your tests alone; each must turn one red; restore each.
5. **Bump the version PATCH** to the next free number after `main`'s, `uv lock --offline`, stage `uv.lock`.
6. **`make ci` green** — every step, **redirected to a file, never piped**.
7. **Fill the handback sections** at the bottom of this file.

---

## Test plan

All in `agents/analyst/tests/test_sentiment_subject.py`; each docstring cites `ANLZ-OUT-11`. The names are fixed: the test-plan row in Appendix section 2 cites them.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 `test_a_headline_is_own_only_when_it_names_the_company` (parametrized) | MRK: *Merck's*, *Merck,*, *Mercker*, `$MRK`, `(MRK)`, `NYSE:MRK`, `NYSE: MRK`, a Vaxcyte headline that names no one, bare `MRK`, *"Vaxcyte Takes Aim at Pfizer and Merck"*; IBM bare; GE: *GE Vernova*, *GE Aerospace*; TGT: *Target cuts*, *Raises Price Target On Nike*, *price Target for Walmart*; META: *Metaverse*; MMM: *raises $3M* | own exactly for: the table name at word edges, the three marks, IBM's listed bare ticker, *GE Aerospace*, *Target cuts*, the Pfizer-and-Merck headline; not own for the rest |
| A2 | 🎯 `test_another_companys_news_does_not_move_the_score` | two own MRK headlines + two that are not | the score equals `score_sentiment` of the two own ones; served 4, own 2, filtered 1, articles 2 |
| A3 | `test_fewer_own_scored_headlines_than_the_minimum_is_no_pillar` | two own headlines, one carrying a lexicon word, minimum 2 | `(None, {served 4, own 2, filtered 1})`; at minimum 1 it scores the one |
| A4 | `test_the_minimum_counts_scored_headlines_with_their_weights` | two own scored headlines, one weighted 0.5 | the weighted score; `sentiment_batch_weighted_articles` 1.5 |
| A5 | 🪤 `test_a_ticker_the_table_does_not_list_scores_every_headline` | ticker `ZZZZ`, two scored headlines, **minimum 3** | every headline scored (no minimum on this path); filtered 0, own = served |
| A6 | `test_no_served_news_is_no_pillar_and_no_metrics` | MRK with no news; MRK with only others' news | `(None, {})`; then `(None, {served 2, own 0, filtered 1})` |
| A7 | `test_every_ticker_of_the_fleets_universe_is_in_the_company_table` | `scripts/universe_sp100.txt` read as text | 99 tickers, none missing from the table, no empty entry |
| A8 | `test_the_minimum_is_a_bounded_tunable_defaulting_to_two` | `AnalystSettings()` and 1, 0, 11 | default 2; 1 accepted; 0 and 11 raise naming the field |
| A9 | 🎯 `test_the_scorer_reads_own_headlines_by_its_settings_and_weights` | `score_candidate` on AAPL with three own headlines (one weighted 0.5) and two that are not; then minimum 4 | `sentiment_score` = the weighted own score / 100, own 3; at minimum 4 `sentiment_score` is None |

On the unchanged tree the whole file fails at import. After Appendix section 1 all nine pass.

---

## Success factors

- [ ] On the built tree, `s284_f1.py` over the nine nights (planner's F1) prints exactly the prototype's output (`f1_proto.txt`): the same two decisions change (CL, 10-12 and 10-19) and nothing else.
- [ ] `MarketData`, `contracts/`, the provider and the debaters unchanged; no existing test changed beyond Appendix section 2's four files.
- [ ] Design decisions recorded with rejected alternatives: DL-308, already on `main`.
- [ ] Law cycle done as Appendix section 2: `ANLZ-OUT-11` 🟩, rollup 31 / 54 in both rollups.
- [ ] B1 to B25 each planted, watched to fail against your tests alone, restored — stated per break.
- [ ] Every touched module < 200 lines, test files included (four sit at 192 to 199: add nothing to them).
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **A headline that names the company counts, whoever it is about.** *"Vaxcyte Takes Aim at Pfizer and Merck"* is MRK's own by the rule (A1 pins it). Do not try to find a headline's main subject; that is out of scope.
🪤 **The bare ticker is not a mark.** `MRK falls` is not MRK's own; only `$MRK`, `(MRK)` and an exchange prefix are. The bare ticker counts only where the table lists it as a name (IBM, AMD, CVS, UPS, RTX, GM). That is why *GE Vernova* is not GE's.
🪤 **The minimum counts headlines that carry a lexicon word**, `sentiment_articles`, not own headlines: A3 has two own headlines and one scored.
🪤 **The unlisted path has no minimum.** A5 uses minimum 3 so that a minimum applied there goes red (the planner's first version used 2 and missed it).
🪤 **Four test files sit at 192 to 199 lines.** `ruff format` grows them; measure after formatting. Add nothing to them beyond Appendix section 2.
🪤 **The `candidate` argument of `score_candidate` loses its `noqa: ARG001`**: it is used now. Do not put the `noqa` back.

**The breaks** (plant one at a time in production code, run your A1 to A9 alone, expect red, restore):

| # | Break | # | Break |
| --- | --- | --- | --- |
| B1 | `own_headlines` returns every headline | B14 | `sentiment_own_headlines` = served count |
| B2 | the *Price* look-behind removed | B15 | the `if not headlines` early return removed |
| B3 | the `(?![a-z])` word edge removed | B16 | `score_sentiment` called without weights |
| B4 | `$` dropped from the name look-behind | B17 | below the minimum returns `{}`, not the counts |
| B5 | no `$T` mark | B18 | `scoring.py` passes `"ZZZZ"` as the ticker |
| B6 | no `(T)` mark | B19 | `scoring.py` passes `2`, not the setting |
| B7 | no exchange mark | B20 | `scoring.py` drops `headline_weights` |
| B8 | the exchange mark's `\s?` removed | B21 | the default is 3 |
| B9 | `< min_own` → `<= min_own` | B22 | the lower bound is 0 |
| B10 | the minimum removed | B23 | the upper bound is 11 |
| B11 | the minimum applied to the unlisted path too | B24 | `XOM` renamed `ZZZZ` in the table |
| B12 | the unlisted path scores nothing | B25 | `XOM`'s entry emptied |
| B13 | `sentiment_subject_filtered` inverted | | |

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `scoring.py` **191**, `settings.py` **161**, `sentiment_subject.py` **81**, `helpers.py` **198**, `test_analyst_agent.py` **199**, `test_analyst_domain.py` **199**, `test_sentiment_reading.py` **192**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. The minimum is a tunable (a value), not a mode selector.
- Faults, not silent failure — `kernel.fault_boundary` (the scorer's existing boundary covers the new call).
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a pipe.**
- Version bump PATCH, `uv.lock` staged with it.
- Secrets never through the worktree — your worktree has **no `.env`**; F1 is the planner's, from a tree with the main checkout's `.env`. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0** from the branch's worktree; check the printed SHA against `git rev-parse HEAD`.
2. Planner's review: CodeQL set-diff against the baseline branch first; 12 blobs against `prototype_blobs.txt` (kit); the planner's tests on the built tree; B1 to B25 against Codex's tests alone; F1 (`s284_f1.py` from the built tree: equals `f1_proto.txt` byte for byte).
3. Merge to `main` locally and push; tag `v<version>`; post-merge CodeQL.
4. **Deploy: image-only retag, held for the fidelity verdict** (DL-308 D9), on the operator's word; record the rollback tag. F2 on the first weekday night after: 8 / 8; each scored name's metrics carry the three counts; `sentiment_subject_filtered` 1 on every universe name; no fault. Then close work-queue 108.

---

## Handover — paste this to Codex

```text
You are building Sprint 284 in the worktree ../ta-s284, on the branch
sprint-284-a-headline-counts-only-for-the-company-it-names. Never work on main. The worktree and
its venv are ready; never run a bare `uv sync` (it needs the network and you have none).

Read docs/sprints/sprint-284-a-headline-counts-only-for-the-company-it-names.md, whole, before
anything else. It is the spec, and its bottom sections are your handback. The Appendix holds the
production code, the law text and four test-fixture edits, which you apply exactly. Your work is
the tests A1 to A9, the breaks, the bump and the evidence.

In order:
1. Read agents/analyst/laws/laws.md and test-plan.md, docs/laws/conventions.md and
   docs/laws/drift-register.md. Fill the Law reading record in the spec BEFORE any code.
2. Write agents/analyst/tests/test_sentiment_subject.py with A1 to A9 under the exact names in the
   Test plan, each docstring citing ANLZ-OUT-11. Run it on the unchanged tree and paste the output
   into the Closeout: it must fail at import (agents.analyst.domain.sentiment_subject is missing).
3. Apply Appendix section 1 exactly (four files; sentiment_subject.py and company_names.json are
   new). Change nothing else in production code.
4. Apply Appendix section 2 exactly (analyst laws.md and test-plan.md, docs/laws/ledger.md,
   docs/laws/INDEX.md, and four existing test files). Change no other existing test. The
   test-plan row names your tests; if a name differs, your name is wrong.
5. Plant the breaks B1 to B25 (Traps) one at a time; each must turn at least one of your A1 to A9
   red; restore each before the next. Record each in the Closeout.
6. Bump the version PATCH to the next number after main's in pyproject.toml, run
   uv lock --offline, stage uv.lock. Run make ci redirected to a file and read the file. If the
   dependency audit is the only step that fails for want of network, say so; the planner runs it.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md, docs/design-log.md or docs/work-queue.md.

DO NOT: reach the network or any live service; run infra/ scripts, pwsh or any az command; change
contracts/, kernel/, agents/provider/, the deliberator, any pack or any Dockerfile; add or reword a
law clause beyond section 2; add a design-log entry; use noqa; let any module, test files
included, reach 200 lines; measure make ci through a pipe.

Traps (the spec's Traps section has them all): a headline that names the company counts whoever
it is about; the bare ticker is not a mark; the minimum counts headlines carrying a lexicon word;
A5 needs minimum 3; four test files sit at 192 to 199 lines, measure after ruff format; the noqa on
score_candidate's candidate argument is gone on purpose.

Two tiers when something does not fit. A wrong command, count, path or line number whose intent is
plain: correct it, record it in Return notes, and carry on. A law that contradicts the spec, an
existing test failing outside section 2's files, or a measurement in the spec that does not
reproduce: STOP and report. State anything not done as "not done" or "verified failing". Never
write a Result for work you have not done.
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
| *(to fill)* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(to fill)*

**Contradictions found between a law and this spec:** *(to fill)*

**Laws found silent where a decision was needed:** *(to fill)*

**Clauses that were ⬜ and are now proven:** *(to fill)*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | *(to fill)* | | | |

**Tests added beyond the plan:** *(to fill)*

---

## Closeout — evidence

**Status:** *(to fill)*

**Tree the proofs ran in (and `.env` present?):** *(to fill)*

**Result:** *(to fill)*

**Files changed:** *(to fill)*

**Design decisions:** recorded as [`DL-308`](../design-log.md) (planner, before the build).

**Proof — the red run first:**

```text
(to fill)
```

**Proof — the green run:**

```text
(to fill)
```

**Guards planted:** *(to fill)*

**Module line counts:** *(to fill)*

**`make ci`:** *(to fill)*

**`make gate-ran`:** *(the planner's, after push)*

**Not met / verified failing:** *(to fill)*

---

## Return notes

- *(to fill)*

---

## Appendix — the prototype (`proto-s284` `573b44fa`: `make ci` 5,221 passed, 100.00 %, every step green but the dependency audit on `aiohttp` 3.14.3, which `main` fixes before this branch is cut; 25 / 25 breaks red)

Apply with `git apply` from the worktree root. Section 1 is production code, section 2 the law cycle and the four test-fixture edits. Both come from one diff; apply section 1, then section 2.

### Section 1 — production code (4 files)

```diff
diff --git a/agents/analyst/domain/data/company_names.json b/agents/analyst/domain/data/company_names.json
new file mode 100644
index 00000000..8e895f8e
--- /dev/null
+++ b/agents/analyst/domain/data/company_names.json
@@ -0,0 +1,101 @@
+{
+  "AAPL": ["Apple", "iPhone"],
+  "ABBV": ["AbbVie"],
+  "ABT": ["Abbott"],
+  "ACN": ["Accenture"],
+  "ADBE": ["Adobe"],
+  "AMD": ["AMD", "Advanced Micro"],
+  "AMGN": ["Amgen"],
+  "AMT": ["American Tower"],
+  "AMZN": ["Amazon", "AWS"],
+  "AVGO": ["Broadcom"],
+  "AXP": ["American Express", "Amex"],
+  "BA": ["Boeing"],
+  "BAC": ["Bank of America", "BofA"],
+  "BKNG": ["Booking Holdings", "Booking.com"],
+  "BLK": ["BlackRock"],
+  "BMY": ["Bristol Myers", "Bristol-Myers"],
+  "C": ["Citigroup", "Citi"],
+  "CAT": ["Caterpillar"],
+  "CHTR": ["Charter Communications"],
+  "CL": ["Colgate"],
+  "CMCSA": ["Comcast", "NBCUniversal"],
+  "COF": ["Capital One"],
+  "COP": ["ConocoPhillips"],
+  "COST": ["Costco"],
+  "CRM": ["Salesforce"],
+  "CSCO": ["Cisco"],
+  "CVS": ["CVS", "Aetna"],
+  "CVX": ["Chevron"],
+  "DE": ["Deere"],
+  "DHR": ["Danaher"],
+  "DIS": ["Disney", "ESPN"],
+  "DOW": ["Dow Inc"],
+  "DUK": ["Duke Energy"],
+  "EMR": ["Emerson"],
+  "FDX": ["FedEx"],
+  "GD": ["General Dynamics"],
+  "GE": ["GE Aerospace", "General Electric"],
+  "GILD": ["Gilead"],
+  "GM": ["GM", "General Motors"],
+  "GOOG": ["Alphabet", "Google", "YouTube", "Waymo"],
+  "GOOGL": ["Alphabet", "Google", "YouTube", "Waymo"],
+  "GS": ["Goldman"],
+  "HD": ["Home Depot"],
+  "HON": ["Honeywell"],
+  "IBM": ["IBM"],
+  "INTC": ["Intel"],
+  "INTU": ["Intuit", "TurboTax"],
+  "JNJ": ["Johnson & Johnson", "J&J"],
+  "JPM": ["JPMorgan", "JP Morgan"],
+  "KHC": ["Kraft Heinz"],
+  "KO": ["Coca-Cola", "Coke"],
+  "LIN": ["Linde"],
+  "LLY": ["Eli Lilly", "Lilly"],
+  "LMT": ["Lockheed"],
+  "LOW": ["Lowe's", "Lowes"],
+  "LRCX": ["Lam Research"],
+  "MA": ["Mastercard"],
+  "MCD": ["McDonald's", "McDonalds"],
+  "MDLZ": ["Mondelez", "Oreo"],
+  "MDT": ["Medtronic"],
+  "MET": ["MetLife"],
+  "META": ["Meta", "Facebook", "Instagram", "WhatsApp"],
+  "MMM": ["3M"],
+  "MO": ["Altria"],
+  "MRK": ["Merck"],
+  "MS": ["Morgan Stanley"],
+  "MSFT": ["Microsoft", "Azure"],
+  "NEE": ["NextEra"],
+  "NFLX": ["Netflix"],
+  "NKE": ["Nike"],
+  "NOW": ["ServiceNow"],
+  "NVDA": ["Nvidia", "NVIDIA"],
+  "ORCL": ["Oracle"],
+  "PEP": ["PepsiCo", "Pepsi"],
+  "PFE": ["Pfizer"],
+  "PG": ["Procter", "P&G"],
+  "PM": ["Philip Morris"],
+  "PYPL": ["PayPal", "Venmo"],
+  "QCOM": ["Qualcomm"],
+  "RTX": ["RTX", "Raytheon", "Pratt & Whitney"],
+  "SBUX": ["Starbucks"],
+  "SCHW": ["Schwab"],
+  "SO": ["Southern Co", "Southern Company"],
+  "SPG": ["Simon Property"],
+  "T": ["AT&T"],
+  "TGT": ["Target"],
+  "TMO": ["Thermo Fisher"],
+  "TMUS": ["T-Mobile"],
+  "TSLA": ["Tesla"],
+  "TXN": ["Texas Instruments"],
+  "UNH": ["UnitedHealth", "Optum"],
+  "UNP": ["Union Pacific"],
+  "UPS": ["UPS"],
+  "USB": ["U.S. Bancorp", "US Bancorp"],
+  "V": ["Visa"],
+  "VZ": ["Verizon"],
+  "WFC": ["Wells Fargo"],
+  "WMT": ["Walmart"],
+  "XOM": ["Exxon"]
+}
diff --git a/agents/analyst/domain/scoring.py b/agents/analyst/domain/scoring.py
index 4c776083..b27a4093 100644
--- a/agents/analyst/domain/scoring.py
+++ b/agents/analyst/domain/scoring.py
@@ -16,7 +16,7 @@ from agents.analyst.domain.relative_strength import (
     score_relative_strength,
 )
 from agents.analyst.domain.score_arithmetic import record_arithmetic
-from agents.analyst.domain.sentiment_rules import score_sentiment
+from agents.analyst.domain.sentiment_subject import subject_sentiment
 from agents.analyst.domain.signal_selection import (
     Signal,
     fundamental_signals,
@@ -51,8 +51,7 @@ class ScoreBreakdown:


 def score_candidate(
-    candidate: Candidate,  # noqa: ARG001 - kept for call-site stability; the
-    # analyst now scores on its own technical evidence, not the scanner prior.
+    candidate: Candidate,
     bars: tuple[OHLCVBar, ...],
     fundamentals: dict[str, float],
     benchmark_bars: tuple[OHLCVBar, ...],
@@ -80,7 +79,12 @@ def score_candidate(
     )
     raw_fund, fmetrics = score_fundamental(fundamentals)
     fundamental = None if raw_fund is None else _bounded(raw_fund / 100.0)
-    raw_sent, smetrics = score_sentiment(news, headline_weights=headline_weights)
+    raw_sent, smetrics = subject_sentiment(
+        candidate.ticker,
+        news,
+        settings.sentiment_min_own_headlines,
+        headline_weights=headline_weights,
+    )
     sentiment = None if raw_sent is None else _bounded(raw_sent / 100.0)
     alpha = None if alpha_score is None else _bounded(alpha_score / 100.0)
     composite = _composite(technical, fundamental, sentiment, alpha, settings)
diff --git a/agents/analyst/domain/sentiment_subject.py b/agents/analyst/domain/sentiment_subject.py
new file mode 100644
index 00000000..09d6a0de
--- /dev/null
+++ b/agents/analyst/domain/sentiment_subject.py
@@ -0,0 +1,81 @@
+"""Which served headlines are about the ticker's own company, and their sentiment.
+
+Agent: analyst
+Role: score only the headlines that name a ticker's company (ANLZ-OUT-11, DL-308).
+External I/O: none (reads the company table bundled under domain/data).
+"""
+
+from __future__ import annotations
+
+import json
+import re
+from functools import cache
+from pathlib import Path
+from typing import TYPE_CHECKING
+
+from agents.analyst.domain.sentiment_rules import score_sentiment
+
+if TYPE_CHECKING:
+    from collections.abc import Mapping
+
+COMPANY_NAMES_FILE = Path(__file__).parent / "data" / "company_names.json"
+
+
+def load_company_names(path: Path = COMPANY_NAMES_FILE) -> dict[str, tuple[str, ...]]:
+    """Read the company table: ticker -> the names headlines use for it."""
+    raw: dict[str, list[str]] = json.loads(path.read_text(encoding="utf-8"))
+    return {ticker: tuple(names) for ticker, names in raw.items()}
+
+
+COMPANY_NAMES: dict[str, tuple[str, ...]] = load_company_names()
+
+
+@cache
+def _own_pattern(ticker: str) -> re.Pattern[str] | None:
+    """A name from the table, or a ticker mark: ``$T``, ``(T)``, ``NYSE:T``."""
+    names = COMPANY_NAMES.get(ticker)
+    if names is None:
+        return None
+    mark = re.escape(ticker)
+    named = [
+        rf"(?<![A-Za-z0-9$])(?<!Price )(?<!price ){re.escape(name)}(?![a-z])"
+        for name in names
+    ]
+    marks = [rf"\${mark}\b", rf"\({mark}\)", rf"\b[A-Z]{{2,}}:\s?{mark}\b"]
+    return re.compile("|".join(named + marks))
+
+
+def own_headlines(ticker: str, headlines: tuple[str, ...]) -> tuple[str, ...] | None:
+    """The headlines naming the ticker's company; None when the table lacks it."""
+    pattern = _own_pattern(ticker)
+    if pattern is None:
+        return None
+    return tuple(headline for headline in headlines if pattern.search(headline))
+
+
+def subject_sentiment(
+    ticker: str,
+    headlines: tuple[str, ...],
+    min_own: int,
+    *,
+    headline_weights: Mapping[str, float] | None = None,
+) -> tuple[float | None, dict[str, float]]:
+    """Score the ticker's own headlines; no pillar below ``min_own`` scored ones.
+
+    A ticker the company table does not list is scored on every served headline,
+    as before DL-308, and ``sentiment_subject_filtered`` reads 0. Names with no
+    served news return ``(None, {})`` exactly as ``score_sentiment`` does.
+    """
+    if not headlines:
+        return None, {}
+    own = own_headlines(ticker, headlines)
+    scored = headlines if own is None else own
+    counts = {
+        "sentiment_served_headlines": float(len(headlines)),
+        "sentiment_own_headlines": float(len(scored)),
+        "sentiment_subject_filtered": 0.0 if own is None else 1.0,
+    }
+    raw, metrics = score_sentiment(scored, headline_weights=headline_weights)
+    if raw is None or (own is not None and metrics["sentiment_articles"] < min_own):
+        return None, counts
+    return raw, {**metrics, **counts}
diff --git a/agents/analyst/settings.py b/agents/analyst/settings.py
index 48cd0a17..daef8661 100644
--- a/agents/analyst/settings.py
+++ b/agents/analyst/settings.py
@@ -88,6 +88,15 @@ class AnalystSettings(_StopTargetSettings):
         ge=0.0,
         le=1.0,
     )
+    sentiment_min_own_headlines: int = tunable(
+        2,
+        why=(
+            "Fewest own-company headlines carrying a lexicon word that make a "
+            "sentiment pillar; one headline alone swings it to 0 or 1 (DL-308)."
+        ),
+        ge=1,
+        le=10,
+    )
     benchmark_ticker: str = tunable(
         "SPY",
         why="Relative-strength benchmark; SPY tracks the scanner's S&P 500 universe.",
```

### Section 2 — the law cycle and the four test-fixture edits (8 files)

```diff
diff --git a/agents/analyst/laws/laws.md b/agents/analyst/laws/laws.md
index b6b30144..a406fbeb 100644
--- a/agents/analyst/laws/laws.md
+++ b/agents/analyst/laws/laws.md
@@ -1,6 +1,6 @@
 # `Analyst` — Laws

-**Prefix:** `ANLZ` · **status:** LOCKED v1.11 · **Owner:** Yury Gurevich
+**Prefix:** `ANLZ` · **status:** LOCKED v1.12 · **Owner:** Yury Gurevich

 > Score scanner candidates into evidence-backed trade recommendations — or explain clearly
 > why none qualify today.
@@ -112,6 +112,16 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   confidence was computed with (the pillar weights, the relative-strength weight, the confidence
   floor and span) and the names of the sub-scores averaged into its technical and fundamental scores.

+- **ANLZ-OUT-11** — The lexicon sentiment pillar scores only the served headlines that name the
+  ticker's company: a name from the bundled company table (`domain/data/company_names.json`),
+  matched case-sensitively, not inside a longer word and not right after *Price* or *price*; or a
+  ticker mark (`$T`, `(T)`, an exchange prefix such as `NYSE:T`). Fewer such headlines carrying a
+  lexicon word than `sentiment_min_own_headlines` → no sentiment pillar for that name, and the
+  blend renormalises over the pillars present. A ticker the table does not list is scored on every
+  served headline. Each name with served news records `sentiment_served_headlines`,
+  `sentiment_own_headlines` and `sentiment_subject_filtered`. Every ticker of the fleet's universe
+  has a table entry. `MarketData.news` is unchanged. *(Work-queue 108, DL-308.)*
+
 ---

 ## Prohibitions (`NEV`)
@@ -317,6 +327,7 @@ green only when a functional test cites its ID (conventions §3). Tests + status
 | `technical_weight` | `0.50` | `float ≥ 0.0, ≤ 1.0` | YES | Reference composite weight for the technical pillar |
 | `fundamental_weight` | `0.30` | `float ≥ 0.0, ≤ 1.0` | YES | Reference weight for the fundamental pillar; renormalised over present pillars |
 | `sentiment_weight` | `0.20` | `float ≥ 0.0, ≤ 1.0` | YES | Reference weight for the sentiment pillar; renormalised over present pillars |
+| `sentiment_min_own_headlines` | `2` | `int ≥ 1, ≤ 10` (headlines) | YES | Fewest own-company headlines carrying a lexicon word that make a sentiment pillar (`ANLZ-OUT-11`); one headline alone swings the pillar to 0 or 1; at 2, 15 % of names had no pillar over nine nights against 38 % at 3 (DL-308) |
 | `alpha158_pillar_weight` | `0.00` | `float ≥ 0.0, ≤ 1.0` | YES | Alpha158 fifth pillar; 0.00 = off; enable after 20-day IC comparison (ΔIC ≥ 0.02) |
 | `benchmark_ticker` | `"SPY"` | `str` | YES | Relative-strength benchmark; matches the scanner's universe |
 | `rs_window` | `20` | `int ≥ 2, ≤ 120` (bars) | YES | Relative-strength lookback (~one trading month) |
@@ -439,3 +450,8 @@ green only when a functional test cites its ID (conventions §3). Tests + status
 - v1.11 — amendment (S279 / DL-302, 2026-10-15). Adds and proves `ANLZ-PERF-02`: the held-stop
   read shares one `Fill` read across the book, where it read the label once per position. No
   threshold, stop check or recommendation changes; 29 / 52 → 30 / 53.
+
+- v1.12 — amendment (S284 / DL-308, 2026-10-20). Adds and proves `ANLZ-OUT-11`: the lexicon
+  sentiment pillar scores only the headlines that name the ticker's company, with no pillar below
+  `sentiment_min_own_headlines` (new PARAM row, default 2). Decisions change: over nine nights,
+  2 of 303 replayed. 30 / 53 → 31 / 54.
diff --git a/agents/analyst/laws/test-plan.md b/agents/analyst/laws/test-plan.md
index c2f54e4f..520383e7 100644
--- a/agents/analyst/laws/test-plan.md
+++ b/agents/analyst/laws/test-plan.md
@@ -34,6 +34,7 @@ Status: ⬜ gray (no passing test) · 🟩 green (≥1 passing test cites the ID
 | ANLZ-OUT-08 | Every stop/target proposal records applied and counterfactual mode, stop and target; the counterfactual never reaches the PM. | happy | _tbd_ | ⬜ |
 | ANLZ-OUT-09 | A held ticker's stop threshold is read through the shared stop-width resolver (PM lineage, else the position's width) over the weighted entry of its active lots; a latest close at or below it is a sell with exit_trigger stop whatever the confidence; above it no stop exit (judged on thesis); a live broker stop owns the exit and the check reports no breach; an unreadable book is a fault and an empty result, never a guessed stop. | at + beyond + above + live broker stop + multilot + unreadable | `tests/test_analyst_held_stop.py::test_a_close_at_or_beyond_the_decided_stop_is_a_forced_stop_sell`; `tests/test_analyst_held_stop.py::test_a_close_above_the_decided_stop_is_no_stop_exit`; `tests/test_analyst_held_stop.py::test_a_position_with_a_live_broker_stop_is_left_to_that_stop`; `test_exit_authority.py::test_graph_pull_forces_weighted_multilot_stop_sell`; `test_exit_authority.py::test_graph_pull_sells_above_stop_when_confidence_below_floor`; `test_exit_authority.py::test_graph_pull_holds_above_stop_when_confidence_above_floor`; `test_exit_authority.py::test_graph_pull_faults_on_multilot_different_stop_pct`; `tests/test_stop_width.py::test_all_three_readers_agree_on_the_decided_stop` | 🟩 |
 | ANLZ-OUT-10 | Each recommendation with quant metrics records its active pillar/RS/confidence constants and the ordered technical/fundamental sub-scores actually averaged. | defaults + all constants moved + real mean order + every recommendation path | `tests/test_score_arithmetic_analyst.py::test_analyst_records_every_constant_and_the_actual_mean_order`; `tests/test_score_arithmetic_analyst.py::test_each_recommendation_path_keeps_the_scored_arithmetic`; `tests/test_score_arithmetic_analyst.py::test_a_stop_sale_with_short_history_records_constants_and_empty_means`; `tests/test_score_arithmetic_analyst.py::test_the_packet_formula_reproduces_real_analyst_outputs` | 🟩 |
+| ANLZ-OUT-11 | The lexicon pillar scores only headlines that name the ticker's company (table name at word edges, not after *Price*; or a ticker mark); below the minimum no pillar; an unlisted ticker scores every headline; the counts are recorded; the fleet's universe is in the table; the minimum is a bounded tunable. | own/other/roundup + marks + minimum + unlisted + no news + universe + PARAM bounds + through `score_candidate` | `test_sentiment_subject.py::test_a_headline_is_own_only_when_it_names_the_company`, `::test_another_companys_news_does_not_move_the_score`, `::test_fewer_own_scored_headlines_than_the_minimum_is_no_pillar`, `::test_the_minimum_counts_scored_headlines_with_their_weights`, `::test_a_ticker_the_table_does_not_list_scores_every_headline`, `::test_no_served_news_is_no_pillar_and_no_metrics`, `::test_every_ticker_of_the_fleets_universe_is_in_the_company_table`, `::test_the_minimum_is_a_bounded_tunable_defaulting_to_two`, `::test_the_scorer_reads_own_headlines_by_its_settings_and_weights` | 🟩 |

 ## Prohibitions

diff --git a/agents/analyst/tests/helpers.py b/agents/analyst/tests/helpers.py
index 0897fc3b..0a8244b0 100644
--- a/agents/analyst/tests/helpers.py
+++ b/agents/analyst/tests/helpers.py
@@ -189,3 +189,10 @@ def wire_analyst(
         ).bind()
     AnalystAgent(bus, graph=graph, settings=settings, sink=sink).bind()
     return bus, graph, sink
+
+
+# Two headlines that name Apple, both all-positive (ANLZ-OUT-11 needs two own ones).
+APPLE_NEWS = (
+    "Apple profit surges to record as sales beat",
+    "Apple shares rally on record profit",
+)
diff --git a/agents/analyst/tests/test_analyst_agent.py b/agents/analyst/tests/test_analyst_agent.py
index c6049453..bb88c3e4 100644
--- a/agents/analyst/tests/test_analyst_agent.py
+++ b/agents/analyst/tests/test_analyst_agent.py
@@ -10,6 +10,7 @@ from __future__ import annotations
 from typing import Any

 from agents.analyst.tests.helpers import (
+    APPLE_NEWS,
     analyze_message,
     bars,
     candidate,
@@ -68,7 +69,7 @@ def test_recommendation_carries_sentiment_score_when_present() -> None:
     scan = candidate_set(candidate())
     bus, _graph, sink = wire_analyst(
         source_bars=bars(),
-        news={"AAPL": ("Profit surges to record as sales beat",)},
+        news={"AAPL": APPLE_NEWS},
     )

     response = bus.request(analyze_message(scan))
diff --git a/agents/analyst/tests/test_analyst_domain.py b/agents/analyst/tests/test_analyst_domain.py
index 95bf4891..a94f7df5 100644
--- a/agents/analyst/tests/test_analyst_domain.py
+++ b/agents/analyst/tests/test_analyst_domain.py
@@ -153,7 +153,7 @@ def test_zero_confidence_span_floors_confidence() -> None:
 def test_sentiment_blends_three_pillars_into_confidence() -> None:
     # Same 40-bar technical (450/11/100) + fundamentals -> 0.80 + an all-positive
     # headline -> 1.0. composite renormalises over the 0.50/0.30/0.20 weights.
-    settings = AnalystSettings()
+    settings = AnalystSettings(sentiment_min_own_headlines=1)
     fundamentals = {"peTTM": 8.0, "roeTTM": 20.0}
     news = ("Apple beats estimates and profit surges to record",)
     technical = (450.0 / 11.0) / 100.0
@@ -190,8 +190,8 @@ def test_sentiment_blends_three_pillars_into_confidence() -> None:

 def test_sentiment_without_fundamentals_two_pillar_blend() -> None:
     """Kills agents.analyst.domain.scoring.x_score_candidate__mutmut_54."""
-    settings = AnalystSettings()
-    news = ("Shares report profit and loss",)
+    settings = AnalystSettings(sentiment_min_own_headlines=1)
+    news = ("Apple shares report profit and loss",)
     score = score_candidate(candidate(), _rising_bars(40), {}, (), news, settings)

     assert score.sentiment_score == pytest.approx(0.5, abs=1e-9)
diff --git a/agents/analyst/tests/test_sentiment_reading.py b/agents/analyst/tests/test_sentiment_reading.py
index 24d4c983..6d523e2c 100644
--- a/agents/analyst/tests/test_sentiment_reading.py
+++ b/agents/analyst/tests/test_sentiment_reading.py
@@ -22,6 +22,7 @@ from agents.analyst.domain.sentiment_reading import (
 )
 from agents.analyst.store import write_analysis
 from agents.analyst.tests.helpers import (
+    APPLE_NEWS,
     analyze_message,
     bars,
     candidate,
@@ -126,7 +127,7 @@ def test_analyze_persists_sentiment_reading_node() -> None:
     scan = candidate_set(candidate())
     bus, graph, sink = wire_analyst(
         source_bars=bars(),
-        news={"AAPL": ("Profit surges to record as sales beat",)},
+        news={"AAPL": APPLE_NEWS},
     )

     response = bus.request(analyze_message(scan))
@@ -167,7 +168,7 @@ def test_analyze_aligns_both_scorer_readings_for_one_run() -> None:
     scan = candidate_set(candidate())
     bus, graph, sink = wire_analyst(
         source_bars=bars(),
-        news={"AAPL": ("Profit surges to record as sales beat",)},
+        news={"AAPL": APPLE_NEWS},
         sentiment={"AAPL": 0.58},
     )

diff --git a/docs/laws/INDEX.md b/docs/laws/INDEX.md
index 91244040..167a87e5 100644
--- a/docs/laws/INDEX.md
+++ b/docs/laws/INDEX.md
@@ -39,7 +39,7 @@ Each agent's law files live at `agents/<name>/laws/`:
 | Agent | `laws.md` | Green clauses | Notes |
 | --- | --- | --- | --- |
 | provider | ✅ LOCKED v1.10 (S266, DL-287) | 24 / 67 | S266 (DL-287) amends and re-proves `PROV-OUT-08`: barrier history ends on the run's as-of by lineage whenever the provider reaches it, missing lineage serves the fetch's UTC date, and a broken stored date fails before any fetch or history write (DRIFT-110); count unchanged; S255 (DL-269) amends and re-proves `PROV-OUT-02`: the regime records its four label thresholds; count unchanged; S251 amends `PROV-TRG-01` (every recorded data need, re-proven on graph-pull; DRIFT-082), `PROV-TRG-02` (the poll's key-and-edge bound, now green; DRIFT-086), `PROV-OUT-07` (served bars are raw; DRIFT-084) and narrows `PROV-OUT-04` (fetch time and fallback flag, now green; DRIFT-040); S249 adds and proves `PROV-TRG-05` (a `RunRequest`'s ingest serves the run's as-of whenever the provider reaches it; an unusable as-of is refused before any fetch; no run serves today; DRIFT-095); S243 adds and proves `PROV-OUT-09` (the extreme-move guard judges each ticker's newest session only; its √(n−1) ceiling stated) and amends `PROV-OUT-08`; S239 adds and proves `PROV-TRG-04` / `PROV-OUT-08` (the `BarrierHistory` per `AnalystRun`) and reconciles `PROV-TRG-02` with graph-pull; S238 adds and proves `PROV-OUT-07` (consolidated-tape volume, entitlement-respecting requests, loud refusal; DRIFT-080); DL-203 reconciles `PARAM` only; S213 adds FMP `^VIX` regime freshness evidence and proves `PROV-OUT-03` without adding clauses; S187 adds PARAM rows only; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
-| analyst | ✅ LOCKED v1.11 (S279, DL-302) | 30 / 53 | S279 (DL-302) adds and proves `ANLZ-PERF-02`: the held-stop read shares one lazy Fill read across the book and retains each lineage width; no decision changes. S259 (DL-276) reconciles `PARAM` only: the bounds of `scaled_stop_atr_multiplier` follow the code, no clause changes; S255 (DL-269) adds and proves `ANLZ-OUT-10`: each scored recommendation records its constants and actual mean order; S253 adds and proves `ANLZ-IN-05` (a candidate under `required_history_bars` is scored; only fewer than `min_history_bars` rejects; DRIFT-096); S251 adds and proves `ANLZ-OUT-09` (the held-position stop check; DRIFT-074) and names the graph-pull trigger in `ANLZ-TRG-02` (DRIFT-086); DL-203 reconciles `PARAM` only; S211 adds and proves `ANLZ-OBS-06` for decision-time favourable-excursion target evidence and missing-estimate rejection; S205 rewrites `ANLZ-TYP-01` into required fields without moving the count; S198 declares and proves `ANLZ-OBS-05`; S156 citation check plus S186's `ANLZ-OBS-04`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
+| analyst | ✅ LOCKED v1.12 (S284, DL-308) | 31 / 54 | S284 (DL-308) adds and proves `ANLZ-OUT-11`: the lexicon sentiment pillar scores only headlines that name the ticker's company. S279 (DL-302) adds and proves `ANLZ-PERF-02`: the held-stop read shares one lazy Fill read across the book and retains each lineage width; no decision changes. S259 (DL-276) reconciles `PARAM` only: the bounds of `scaled_stop_atr_multiplier` follow the code, no clause changes; S255 (DL-269) adds and proves `ANLZ-OUT-10`: each scored recommendation records its constants and actual mean order; S253 adds and proves `ANLZ-IN-05` (a candidate under `required_history_bars` is scored; only fewer than `min_history_bars` rejects; DRIFT-096); S251 adds and proves `ANLZ-OUT-09` (the held-position stop check; DRIFT-074) and names the graph-pull trigger in `ANLZ-TRG-02` (DRIFT-086); DL-203 reconciles `PARAM` only; S211 adds and proves `ANLZ-OBS-06` for decision-time favourable-excursion target evidence and missing-estimate rejection; S205 rewrites `ANLZ-TYP-01` into required fields without moving the count; S198 declares and proves `ANLZ-OBS-05`; S156 citation check plus S186's `ANLZ-OBS-04`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
 | scanner | ✅ LOCKED v1.5 (S259, DL-276) | 18 / 41 | S259 (DL-276) reconciles `PARAM` only: the upper bound of `min_average_volume` follows the code, no clause changes; S251 names the graph-pull trigger in `SCAN-TRG-02` (DRIFT-085) and narrows `SCAN-TYP-01`'s version sentence (DRIFT-060); DL-203 reconciles `PARAM` only; S205 rewrites `SCAN-TYP-01` into required fields and closes DRIFT-047 without moving the count; S183's `SCAN-OUT-06`/`SCAN-OUT-07`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
 | portfolio_manager | ✅ LOCKED v1 (S70), amended **v1.12** (S259, DL-276) | 33 / 51 | S259 (DL-276) reconciles `PARAM` only: the bounds of six rows follow the code, no clause changes; S251 narrows `PM-OBS-01`/`PM-OUT-06`/`PM-STA-04` (no PM snapshot; DRIFT-039), `PM-OBS-04` (per candidate; DRIFT-065), uses emitted strings in `PM-OUT-03` (DRIFT-037), names graph-pull in `PM-TRG-02` (DRIFT-086), narrows `PM-TYP-03`'s version sentence (DRIFT-060); files DRIFT-098; S240 adds and proves `PM-IN-05`: held names weighed once per ticker at the run's own snapshot marks, a resumed run at the snapshot of the run it resumes (DRIFT-079 closed); DL-203 reconciles `PARAM` only; S220 amends and re-proves `PM-NEV-08` / `PM-OBS-03`: correlated issuers contribute on the ADR-0030 `0.50..0.90` ramp and gate detail renders applied weights; S211 adds and proves `PM-OBS-05`: reward-risk compares measured target evidence against stop risk and can reject measured upside below measured downside at the configured floor; S210 amends `PM-NEV-06`/`PM-NEV-08`/`PM-NEV-09` so concentration ratios use deployed capital and deployment-floor evidence is explicit without moving the count; S208 declares and proves `PM-OBS-04`; S197 declared and proved `PM-OBS-03`; S184 made PM-NEV-07/08/09 green and closed the v1.3 widened PM-NEV-06 and PM-TYP-03 rows; S204 gives every clause a row and makes rowless clauses a hard gate |
 | deliberator | ✅ LOCKED v1.18 (S277, DL-289) | 35 / 66 | S277 (DL-289 amendment 4) adds and proves DLIB-FAIL-05, refusal-only sticky switching with one model-attributed row per attempt; re-proves DLIB-FAIL-01, DLIB-OUT-02 (always-written llm_switches) and DLIB-DEP-05 (handed-over fallback construction). S276 (DL-289 amendment 1) adds and proves DLIB-DEP-05 and DLIB-NEV-11; amended DLIB-OUT-02 re-proven for the models that answered; effort defaults to empty. Before that S257 (DL-274) reconciles `PARAM` only: `max_tokens` defaults to 16,384 with the same upper bound and `request_timeout_seconds` may reach 300, no clause changes; S256 (DL-272) adds and proves `DLIB-IDM-04` (settle-on-take and visible reply faults), `DLIB-OBS-08` (every completion, including a repeat, is its own row), and proves spend attribution `DLIB-OBS-02`; S255 (DL-269) adds and proves `DLIB-OUT-08`: recorded arithmetic reproduces before rendering, with first-failure withholding and old-packet parity; DRIFT-102/103 corrected; S254 / ADR-0032 adds and proves `DLIB-NEV-10`: prompt libraries reach vendors only through the agent's own client; before that S252 / DL-261: `DLIB-TRG-01` now proven for the key-and-edge candidate bound and order-property filter, 27 / 59. S246 adds and proves `DLIB-OUT-06` (each debater turn records its guided reasoning exactly as written, or why it could not be read, never failing the turn or the order) and `DLIB-OUT-07` (each debated order's record carries its decision and evidence packet), and amends `DLIB-TYP-01`; S245 adds and proves `DLIB-NEV-09` (every fact a role prompt states about our code is pinned to that code; the false calendar-day staleness fact removed, DRIFT-092); DL-203 reconciles `PARAM` only; S222 moves the vendor adapters to `kernel/` and proves `DLIB-SEC-02` key containment; S214 narrows `vetoed_tickers` to `overturn` verdicts only, routes unreadable judge answers through loud fail-open, and proves `DLIB-OUT-04`; S206 adds and proves `DLIB-NEV-08`; S205 rewrites and proves `DLIB-TYP-01`; S200 adds `DLIB-OBS-07` and turns `DLIB-IDM-02` green by hashing the system prompt too; S199 adds `DLIB-OBS-05`/`DLIB-OBS-06`; S172 proves concurrent-order record order and pending-reply handling; S194 added `DLIB-OBS-04`; S189 added stop-reason audit evidence; S167 added `DLIB-OBS-03` proof |
diff --git a/docs/laws/ledger.md b/docs/laws/ledger.md
index a91046c5..e5b3b3b5 100644
--- a/docs/laws/ledger.md
+++ b/docs/laws/ledger.md
@@ -37,7 +37,7 @@ and torn down to zero. Historical Neo4j rows remain valid evidence for the pre-S
 | --- | --- | --- | --- |
 | provider | ✅ v1.10 (LOCKED) | 24 / 67 | 🟨 partial — **24 of 67 clauses proven** after S266 (DL-287) amends and re-proves `PROV-OUT-08`: the barrier history ends on the run's as-of by lineage whenever the provider reaches it, missing lineage serves the fetch's UTC date, and a broken stored date raises before any fetch or history write (DRIFT-110); count unchanged; before that S255 (DL-269) amends and re-proves `PROV-OUT-02`: the regime records its four label thresholds; count unchanged; before that S251 (DL-260) amends four clauses to the code: `PROV-TRG-01` names every recorded data need (a bus request, an unconsumed `RunRequest`, an `AnalystRun`'s qualifying buys) and is re-proven with no bus event (DRIFT-082); `PROV-TRG-02` states the poll's key-and-edge bound and turns green (DRIFT-086); `PROV-OUT-07` says served bars are raw (DRIFT-084); `PROV-OUT-04` is narrowed to fetch time and the fallback flag and turns green (DRIFT-040, the vendor gap is work-queue 105); before that S249 (DL-256) adds and proves `PROV-TRG-05`: an ingest a `RunRequest` triggers serves that run's as-of whenever the provider reaches it (window, coverage check, regime, news and earnings anchors), an unusable as-of is refused before any fetch, and an ingest with no run serves today (DRIFT-095); before that S243 (DL-247) adds and proves `PROV-OUT-09`: the extreme-move guard judges each ticker's newest session only, against that session's cross-section, so a real extreme day in a name's history never drops it (DRIFT-088), and states the guard's √(n−1) ceiling (DRIFT-090, CORRECTED: the barrier path leans on the daily request's guard, DL-247 D4); `PROV-OUT-08` amended and re-proven; before that S239 (DL-241 D10) adds and proves `PROV-TRG-04` / `PROV-OUT-08` (the `BarrierHistory` per `AnalystRun`, one batched fetch, dropped tickers named, a failed fetch still written); before that S238 adds and proves `PROV-OUT-07`: a bar's volume is the consolidated tape's (the Alpaca feed defaults to SIP), a SIP request never ends inside the plan's 15-minute recent-data window, and a refusal fails loud with no IEX fallback (DRIFT-080); S213 sharpens and proves `PROV-OUT-03` for FMP `^VIX` freshness without adding clauses; S187 added PARAM rows only; S204 gives every clause a row and promotes missing rows to a hard gate; S169-sweep demoted `PROV-OUT-04` |
 | scanner | ✅ v1.5 (LOCKED) | 18 / 41 | 🟨 partial — **18 of 41 clauses proven**: S259 (DL-276) reconciles `PARAM` only (the upper bound of `min_average_volume` follows the code; no clause moves); S251 (DL-260) names the graph-pull trigger in `SCAN-TRG-02` (a `MarketData` with no `SCANNED_BY` edge, found by key and edge; DRIFT-085) and narrows `SCAN-TYP-01`'s version sentence (DRIFT-060), count unchanged; S205 rewrites `SCAN-TYP-01` into required fields and closes DRIFT-047 without moving the count; S183 added and proved `SCAN-OUT-06`/`SCAN-OUT-07`; S204 gives every clause a row and promotes missing rows to a hard gate |
-| analyst | ✅ v1.11 (LOCKED) | 30 / 53 | 🟨 partial — **30 of 53 clauses proven** after S279 (DL-302) adds and proves `ANLZ-PERF-02`: the held-stop read shares one lazy Fill read across the book and retains each lineage width, no decision changes; before that S259 (DL-276) reconciles `PARAM` only (the bounds of `scaled_stop_atr_multiplier` follow the code; no clause moves) and S255 (DL-269) adds and proves `ANLZ-OUT-10`: each scored recommendation records its constants and actual mean order; before that S253 (DL-263) adds and proves `ANLZ-IN-05`: a candidate under `required_history_bars` is scored on the indicators its bars allow, each missing core indicator visible as `<metric>_missing_bars`, and only fewer than `min_history_bars` rejects (DRIFT-096); before that S251 (DL-260) adds and proves `ANLZ-OUT-09`: a held position's stop check reads the shared stop-width resolver, a close at or below the decided stop is a forced `stop` sell, a live broker stop owns the exit, an unreadable book is a fault (DRIFT-074); `ANLZ-TRG-02` names the graph-pull trigger (DRIFT-086); before that S211 adds and proves `ANLZ-OBS-06`: decision-time favourable-excursion target evidence is measured from prior settled windows, serialized, and missing evidence rejects instead of falling back to a constant target; S205 rewrites `ANLZ-TYP-01` into required fields without moving the count; S198 adds and proves `ANLZ-OBS-05`; S186 adds and proves `ANLZ-OBS-04`; S204 gives every clause a row and promotes missing rows to a hard gate · S152 declared 3 new clauses (43→46) · S169-sweep demoted `ANLZ-OBS-01` |
+| analyst | ✅ v1.12 (LOCKED) | 31 / 54 | 🟨 partial — **31 of 54 clauses proven** after S284 (DL-308) adds and proves `ANLZ-OUT-11`: the lexicon sentiment pillar scores only headlines that name the ticker's company, no pillar below two; before that S279 (DL-302) adds and proves `ANLZ-PERF-02`: the held-stop read shares one lazy Fill read across the book and retains each lineage width, no decision changes; before that S259 (DL-276) reconciles `PARAM` only (the bounds of `scaled_stop_atr_multiplier` follow the code; no clause moves) and S255 (DL-269) adds and proves `ANLZ-OUT-10`: each scored recommendation records its constants and actual mean order; before that S253 (DL-263) adds and proves `ANLZ-IN-05`: a candidate under `required_history_bars` is scored on the indicators its bars allow, each missing core indicator visible as `<metric>_missing_bars`, and only fewer than `min_history_bars` rejects (DRIFT-096); before that S251 (DL-260) adds and proves `ANLZ-OUT-09`: a held position's stop check reads the shared stop-width resolver, a close at or below the decided stop is a forced `stop` sell, a live broker stop owns the exit, an unreadable book is a fault (DRIFT-074); `ANLZ-TRG-02` names the graph-pull trigger (DRIFT-086); before that S211 adds and proves `ANLZ-OBS-06`: decision-time favourable-excursion target evidence is measured from prior settled windows, serialized, and missing evidence rejects instead of falling back to a constant target; S205 rewrites `ANLZ-TYP-01` into required fields without moving the count; S198 adds and proves `ANLZ-OBS-05`; S186 adds and proves `ANLZ-OBS-04`; S204 gives every clause a row and promotes missing rows to a hard gate · S152 declared 3 new clauses (43→46) · S169-sweep demoted `ANLZ-OBS-01` |
 | forecaster | ✅ v1.10 (LOCKED) | 25 / 52 | 🟨 partial — **25 of 52 clauses proven** after S252 (DL-261): `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged; v1.9 (S251, DL-260) names the four legs in `FORE-IDN-01`, one recorded node per prediction in `FORE-OBS-01` (DRIFT-081) and the three shadow scorecards in `FORE-IDM-03` (DRIFT-083), all still gray, count unchanged; v1.8 (S243, DL-247) amends and re-proves `FORE-FAIL-04`: a designed "no claim" records a `warning`, a missing or broken input an `error` (DRIFT-089), count unchanged; after S241 (DL-243) adds and proves `FORE-OUT-08` (each claim settled once by EXP-018's rule from a provider-written `MarketData`; `barrier_scorecard` over EXP-018's fixed climatology), `FORE-IDM-05` (settled once, one pass per run) and `FORE-FAIL-05` (void with a named reason, never a false outcome), and amends and re-proves `FORE-IDN-02`/`TRG-01`/`OUT-03`; v1.6 (S239, DL-241 D10) re-words `FORE-IN-07`/`TRG-01`/`OUT-07`/`IDM-04`/`FAIL-04`/`NEV-04` for the provider-written history, count unchanged; before that the S239 follow-up amends and re-proves `FORE-TRG-01`/`FORE-TRG-02` (the deployed graph-pull loop fires `forecast_barrier` only; count unchanged); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim), each proven; 27 have a gray row |
 | portfolio_manager | ✅ v1 (LOCKED, amended **v1.12**) | 33 / 51 | 🟨 partial — **33 of 51 clauses proven** after S259 (DL-276) reconciles `PARAM` only (the bounds of six rows follow the code; no clause moves) and S251 (DL-260) narrows `PM-OBS-01`/`PM-OUT-06`/`PM-STA-04` to what `PMRun` and `OrderIntentResult` carry (the `portfolio_state_snapshot` promise withdrawn, DRIFT-039; `PM-STA-04` now green), makes `PM-OBS-04` per candidate (DRIFT-065), uses the emitted reason strings in `PM-OUT-03` (DRIFT-037), names the graph-pull trigger in `PM-TRG-02` (DRIFT-086) and narrows `PM-TYP-03`'s version sentence (DRIFT-060); DRIFT-098 filed for `PM-OUT-01`/`PM-TYP-03`; before that S240 adds and proves `PM-IN-05`: a run weighs each held ticker once at its own snapshot mark (adoption mark, then cost, as fallbacks) and a resumed run reads the snapshot of the run it resumes, closing DRIFT-079; `PM-IDN-01` stays gray (current-state conjunct proven, the whole-purpose boundary proof still owed); S220 amends and re-proves `PM-NEV-08` / `PM-OBS-03`: correlated issuers contribute on the ADR-0030 `0.50..0.90` ramp and gate detail renders the applied weights; S211 adds and proves `PM-OBS-05`: reward-risk now compares measured target evidence against stop risk, varies across measured profiles, and rejects measured upside below measured downside at the configured floor; S210 amends `PM-NEV-06`/`PM-NEV-08`/`PM-NEV-09` so concentration ratios use deployed capital and deployment-floor evidence is explicit without moving the count; S208 declares and proves `PM-OBS-04`; S197 declared and proved `PM-OBS-03`; S184 made PM-NEV-07/08/09 green and closed the v1.3 widened PM-NEV-06 and PM-TYP-03 rows |
 | deliberator | ✅ v1.18 (LOCKED) | 35 / 66 | S277 (DL-289 amendment 4) adds and proves DLIB-FAIL-05, refusal-only sticky switching with one model-attributed row per attempt; re-proves DLIB-FAIL-01, DLIB-OUT-02 (always-written llm_switches) and DLIB-DEP-05 (handed-over fallback construction). S276 (DL-289 amendment 1) adds and proves DLIB-DEP-05 and DLIB-NEV-11; amended DLIB-OUT-02 re-proven for the models that answered; effort defaults to empty. 🟨 partial — **35 of 66 clauses proven** after S257 (DL-274) reconciles `PARAM` only (the output cap 16,384, the peer wait up to 300 seconds; no clause moves) and S256 (DL-272) adds and proves `DLIB-IDM-04` (settle-on-take and visible reply faults), `DLIB-OBS-08` (every completion is its own row), and proves spend attribution `DLIB-OBS-02`; S255 (DL-269) adds and proves `DLIB-OUT-08`: recorded arithmetic reproduces before rendering, with first-failure withholding and old-packet parity; DRIFT-102/103 corrected; before that S254 / ADR-0032: `DLIB-NEV-10` proves prompt libraries use only the agent's own client; before that S252 (DL-261): `DLIB-TRG-01` now proven for the key-and-edge candidate bound and order-property filter, 27 / 59; before that S246 (DL-252) adds and proves `DLIB-OUT-06` (each defender and challenger turn records its guided reasoning, readings then gaps before the argument, exactly as written or why it could not be read, and an unreadable one never fails the turn or the order) and `DLIB-OUT-07` (each debated order's record carries its decision and evidence packet), and amends `DLIB-TYP-01` (`DebateTurnRecord.reasoning`, `.reasoning_error`); before that S245 (DL-251) adds and proves `DLIB-NEV-09`: every fact the challenger and judge prompts state about our code is pinned by a test that reads that code, the false calendar-day staleness fact and the stale name-correlation example are gone (DRIFT-092), and the champions rebuild byte for byte from pack-side sources; before that S222 moves its vendor adapters to `kernel/` and proves `DLIB-SEC-02` with a key-containment sentinel; S214 narrows `vetoed_tickers` to `overturn` verdicts only, routes unreadable judge answers through loud fail-open, and proves `DLIB-OUT-04`; S206 adds and proves `DLIB-NEV-08`: rendered debate-context verdicts name their enforcing check and agent, while descriptive stop-target regime evidence has no verdict; S205 rewrites and proves `DLIB-TYP-01`; S200 adds `DLIB-OBS-07` and promotes `DLIB-IDM-02`; S199 adds `DLIB-OBS-05`/`DLIB-OBS-06`; S172 proves concurrent-order record order and pending-reply handling; S194 adds `DLIB-OBS-04`; S189 added stop-reason audit evidence; S167 proves queryable fail-open causes |
```
