<!-- Agent: planning | Role: sprint handover -->
# Sprint 186 — A headline about twenty companies is not news about one

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-186-a-headline-about-twenty-companies-is-not-news-about-one`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** [DL-127](../design-log.md) the decision and its measurement · [DL-117](../design-log.md)
the diagnosis, and the retraction of its own alarming framing · [DL-112](../design-log.md) the last
time a sentiment number's meaning cost real vetoes

> **Why this bump kind.** **fix → PATCH.** No new capability. `score_sentiment` already promises *"the
> net-tone sub-score of each headline"* about **this ticker**; it delivers the net tone of every
> headline the vendor filed under this ticker, which is not the same set. The code is short of what
> it already claims.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/analyst/laws/laws.md` | The analyst's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report |
| `agents/analyst/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `agents/provider/laws/laws.md` | **LOCKED v1 since S69** — the news feed's own law | Same status. You are reading it to check whether the provider is required to say anything about relevance |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: analyst **`OUT`** (what the score means), **`OBS`** (metrics name their unit
and scope), **`TYP`**, **`PARAM`**.

### The rule

1. **Before writing code**, read `agents/analyst/laws/laws.md` — whole file, first time.
2. Read `agents/analyst/laws/test-plan.md` alongside it. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, that silence is a finding → `drift-register.md`.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?

**Probably not, and that is the answer to verify rather than assume.** The sentiment score keeps its
type, range and meaning; what changes is the *weighting inside the mean*. **But** [DL-112](../design-log.md)
is the precedent that matters: the last time a sentiment metric's meaning shifted without its name
following, the deliberator reported the feed as inconsistent and **vetoed real orders on it**. So:

- If you add or rename any `sentiment_*` metric, **the law cycle is owed** — the analyst's `OBS`
  clauses require metrics to name their unit and scope, and a weighted mean is a different scope from
  an unweighted one.
- 🪤 **`sentiment_articles` is the specific hazard.** It currently counts *headlines that scored*.
  Under weighting, "how many articles" and "how much weight" stop being the same number. Decide
  explicitly what it reports and whether its name still tells the truth — see design decision 3.

🪤 **The rollup is derived, not declared.** `make ci` recomputes it. Let the gate tell you the number.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/analyst/domain/sentiment_rules.py::score_sentiment` | `agents/analyst/laws/laws.md` + `test-plan.md` | The `OUT` clause defining what the sentiment score means; the `OBS` clause requiring metrics to name unit **and scope** (DL-112, DL-113) |
| `agents/analyst/domain/scoring.py` (call site) | same | The composite renormalises over *present* pillars — see the trap below |
| wherever the duplication count is computed | `agents/provider/laws/laws.md` (**LOCKED v1**) | Check whether the provider is required to declare news relevance. If it is silent, that silence is a drift row, **not** a licence to change the provider |

⚠️ **Do not change what the provider fetches, caps, or serves.** The duplication count is derived
from the batch the provider already returned, at **zero** API cost. If your change adds a request, a
vendor field, or a provider setting, stop and report.

---

## Goal

A headline the vendor filed under twenty tickers contributes **one twentieth** as much to each
ticker's sentiment as a headline filed under one. The score stops being an unweighted mean of
whatever the vendor attached, and starts being a mean weighted by how much each headline is
*about this company*.

## Why (context)

Finnhub `/company-news?symbol=X` returns market-wide content and `_parse_news` applies **no relevance
test**, so *"Which dow jones stocks are moving on Tuesday?"* counts once, in full, for each of the
**twenty** tickers it is filed under. `score_sentiment` is an **unweighted mean**, so this moves the
number — and the scanner ranks on it.

🪤 **The alarming version of this was already retracted, and the retraction stands.** DL-117's
original wording — *"mis-attributed news is buying stocks"* — was **wrong**. Every approved order
scores *higher* once contamination is removed (CSCO +14.3). This is **bidirectional noise**: the risk
is mis-ranking and false *rejection* as much as false approval. Ship it for accuracy, not for safety.

**The fix is cheap, vendor-independent and now bounded.** Cross-ticker duplication is computable from
the batch already in hand at zero API cost, and [DL-127](../design-log.md) measured what it does
downstream before committing to a shape.

### Measured, 2026-08-22 — read these before designing

All measured on `sched-2026-08-21`'s real news: **98 tickers, 1,255 headline slots, 784 distinct
headlines**. Method: sub-score → mean → composite (`tech 0.5 / fund 0.3 / senti 0.2`, renormalised
over present pillars) → `confidence = 0.3 + composite × 0.6`, against the **0.600** regime floor.

| Claim | Value | How it was measured |
| --- | --- | --- |
| Slots filed under ≥2 tickers | **50.9 %** | *[measured 2026-08-22]* cross-ticker count over the run's `MarketData.snapshot.news` |
| Slots filed under ≥5 tickers | **23.4 %** | *[measured]* 🚨 the work queue carried **19 %** — corrected |
| Slots filed under ≥10 tickers | **14.8 %** | *[measured]* |
| Baseline fidelity | recomputed confidence reproduced **every** stored value to 3 dp | *[measured]* this is what makes the deltas below trustworthy |
| Tickers losing sentiment entirely under **drop N≥5** | **4** (`CMCSA`, `GD`, `PEP`, `TXN`) | *[measured]* 🚨 the queue carried **1** — corrected |
| Tickers losing sentiment entirely under **1/n weighting** | **0** | *[measured]* |
| Max downstream confidence shift, **drop** | **0.0654** | *[measured]* |
| Max downstream confidence shift, **1/n** | **0.0338** | *[measured]* |
| Floor crossings at 0.600, **1/n** | **1** — `KO` 0.605 → 0.599 | *[measured]* a genuine borderline, moved by a hair |
| Raw sentiment moves >10 pts under **1/n** | **25 tickers**; largest `CAT` 50.0 → 93.3 | *[measured]* |
| Effect on the run's approved orders | *none of `C`/`AMZN`/`GOOG` crosses the floor* | *[measured]* — but this is **one run**; do not promise it generalises |

### The fixture — extracted 2026-08-24, so this is reproducible without the graph

`agents/analyst/tests/data/news_sched_2026_08_21.json` holds that run's **whole news batch**
(98 tickers, 1,255 slots, 784 distinct headlines) plus the **analyst baseline** it produced
(28 tickers: `technical_score`, `fundamental_score`, `sentiment_score`, `composite_score`,
`confidence`, and the three `sentiment_*` metrics). A worktree has no `.env`; this is what lets A6
run anyway. Verified on extraction: the unweighted recompute reproduced **28/28** stored confidences
to 3 dp, and `KO` lands on **0.599** under `1/n` — *[measured 2026-08-24]*. No alpha pillar was
active on this run, so the composite is the three-pillar one.

It also carries two edge paths as **real** data rather than synthetic: **`DOW`, `SCHW`, `USB`** are
baseline tickers with **no sentiment at all** (the renormalisation path the trap below describes —
note it is three tickers, not the two named in DL-127's prose), and **`DUK`, `GILD`, `MET`, `TGT`**
have news that is **entirely exclusive** (`n == 1` throughout), so A3 can assert byte-identity on
real headlines instead of a constructed case. 🪤 The largest `n` actually observed is **19**, not the
twenty of the title.

🚨 **`n_tickers` is counted over every ticker in `news` (98), not over `baseline` (28).** This is not
a detail. *[measured 2026-08-24]* counting `n` over only the scored candidates puts `KO` at
**0.600** — which does **not** cross the 0.600 floor, and the sprint's one floor crossing silently
disappears. Same code, different denominator, different headline result. `market.news` in
`score_candidates` is the batch; the candidate set is a subset of it.

🪤 **A ticker with no sentiment is already a first-class case.** `_composite` renormalises over
*present* pillars, so an absent sentiment scores on technical+fundamental rather than being treated as
neutral. `SCHW` and `DOW` took that path on 2026-08-21 with no incident. **This is why "loses its
signal" was the wrong thing to fear about dropping — and it is still why the count matters: 4 tickers
silently changing pillar-mix is a real effect, just not the one that was feared.**

---

## Scope — and what is deliberately NOT here

1. **Weight each headline by `1 / n_tickers`** inside `score_sentiment`'s mean, where `n_tickers` is
   the number of distinct tickers in **this batch** the headline appears under.
2. **The metrics keep telling the truth** — see design decision 3 and the DL-112 hazard above.
3. **A guard that the weighting is actually applied**, not merely available.

### Out of scope (do NOT build this sprint)

- **No provider change at all** — no new request, no vendor field, no new provider setting, no change
  to the news cap. The count comes from the batch already served.
- **No relevance model, no NLP, no entity extraction.** Duplication count only. If it needs a model,
  it is a different sprint.
- **No change to the lexicon**, the sub-score formula, or the `pos + neg == 0` skip.
- **No change to `sentiment_weight`** (0.2) or any composite weight.
- **No `1/sqrt(n)` variant.** Recorded as a road not taken in DL-127; revisit only with evidence.

### The road not taken (LAW-06)

Fully argued in [DL-127](../design-log.md). In brief:

- **Drop headlines filed under ≥N tickers.** Rejected: silences 4 tickers, discards 23.4 % of the
  slots, has **twice** the worst-case downstream shift, and its one floor crossing is an artefact of
  information loss rather than a correction. `N` is also a magic number that can drift.
- **`1 / sqrt(n)`.** Rejected for now: nothing measured suggests `1/n` is too aggressive — its
  downstream shift is already the smaller of the two — and an exponent reintroduces the tunable that
  `1/n` removes.
- **Leave it alone.** Rejected: bidirectional noise still mis-ranks, and the scanner ranks on this.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**
🪤 [DL-127](../design-log.md) already settles *drop vs weight* — **do not re-litigate it**. These are
the implementation questions it deliberately left open.

1. **Where does the duplication count get computed, and how does it reach `score_sentiment`?**
   🪤 **It cannot be `_parse_news`.** The count is a property of the **batch**, not of a headline, and
   the parser sees one ticker at a time — computing it there needs cross-ticker state in a per-ticker
   function. Options: compute it in the analyst as it scores the batch, or pass a prepared map. Say
   which and why. 🪤 **The scope is decided, not open:** count over the **whole** `market.news`
   batch that `score_candidates` holds, not over the candidate set — see the 🚨 above for the
   measured consequence of getting this backwards.
2. **What counts as "the same headline"?** Exact string match is the cheap answer and is what the
   measurement used. Consider whether normalisation (case, whitespace, the vendor's mojibake — the
   run's data contains `Today�s Session`) changes the count materially. **Measure before
   choosing**; do not add normalisation on instinct.
3. 🪤 **What do the metrics report now?** `sentiment_articles` counts *headlines that scored*. Under
   weighting, article count and total weight diverge. Either keep it as an article count and add a
   distinct weight metric with its own name, or rename. **DL-112 is the precedent: a metric whose
   name stopped matching its unit cost real vetoes.** Whichever you choose, the name must state the
   unit and the scope.
4. **What happens when a ticker's headlines are *all* highly duplicated?** The weights shrink but the
   mean is still well-defined (`num/den`), so the score survives — that is why `1/n` silences nobody.
   Confirm this in a test rather than assuming it.

🪤 **Take the next free DL number, then re-check it at merge.** As of 2026-08-22 the highest is
**DL-127**. The log has historic duplicates and a branch cut before another DL lands will collide
even when the number was free at branch time.

---

## Blast radius — measured 2026-08-22

| What | Detail |
| --- | --- |
| Files changed | `agents/analyst/domain/sentiment_rules.py` (**107** lines), `agents/analyst/domain/scoring.py` (**177 — 23 from the hard block**, split rather than squeeze), `agents/analyst/domain/analyze.py` (**137**, holds the batch), possibly `agents/analyst/domain/sentiment_reading.py` (58) |
| Agents affected | `analyst` only. 🪤 If the count is computed in the provider, you have crossed an agent boundary — don't |
| Contract change? | **Expected no.** If you add or rename a metric, re-answer the law-cycle question |
| Graph vocabulary change? | **No** — metrics ride inside existing properties. Verify, don't assume |
| New env keys / tunables | **None expected.** `1/n` is parameter-free by design (DL-127 reason 5) |
| Deploy implication | **Image-only retag.** 🪤 Verify by hashing `orchestration/packs/trading_graph_vocabulary.json` at the deployed commit and at `HEAD` |
| Behaviour change | **Yes, and it is the point.** 25 tickers move >10 sentiment points; 1 crosses the confidence floor. Expect scanner ranking to shift |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the four design decisions** in `docs/design-log.md` with rejected alternatives.
3. **Plant the failing tests first** (A1–A6) and watch them fail. Paste the red output.
4. **Implement** the `1/n` weighting.
5. **Law cycle** if design decision 3 renames or adds a metric.
6. **Reproduce the measurement** — re-score the committed fixture
   (`agents/analyst/tests/data/news_sched_2026_08_21.json`) through your code and confirm the numbers
   in the table above. No graph or `.env` access is needed. 🪤 If your `KO` does not land at
   **0.599**, something differs — the first thing to check is whether you counted `n` over all 98
   news tickers or only the 28 in `baseline`; find out before continuing.
7. **Prove the guards can fail (DL-70)** — set every weight to 1.0, watch A1 go red, restore.
8. **`make ci` green** — all 11 steps, **redirected to a file, never piped**.
9. **Fill the handback sections** and set **Status:** to `BUILT`.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 a headline filed under many tickers counts less than an exclusive one | two tickers, one shared headline + one exclusive, opposite polarity | the shared headline's pull is `1/n` of the exclusive one's — assert the **score**, not that a helper was called |
| A2 | a ticker whose headlines are *all* heavily shared still gets a score | every headline filed under ≥10 | score is not `None`; the mean is well-defined |
| A3 | 🪤 an exclusive-news ticker is completely unaffected | `DUK`, `GILD`, `MET`, `TGT` from the fixture — real tickers whose news is entirely `n == 1` | score is **byte-identical** to today's unweighted result, and their stored `confidence` is unchanged |
| A4 | headlines with no lexicon word are still skipped, not diluted | mixed | the `pos + neg == 0` skip survives weighting |
| A5 | the metrics name their unit and scope after weighting | any | whatever decision 3 chose is asserted here. **DL-112** |
| A6 | 🪤 the measured run reproduces | `agents/analyst/tests/data/news_sched_2026_08_21.json` — the whole 98-ticker batch | `KO` 0.605 → **0.599**, and **0** tickers lose their score. 🚨 count `n` over all 98, not the 28 in `baseline` |

---

## Success factors

- [ ] A headline filed under `n` tickers contributes `1/n` weight to each.
- [ ] **No ticker loses its sentiment score** that has one today (A6).
- [ ] A ticker with only exclusive news scores exactly as it does now (A3).
- [ ] Metrics state their unit and scope; DL-112's failure is not repeated (A5).
- [ ] **Zero** added provider requests, vendor fields or settings.
- [ ] No new tunable — `1/n` stays parameter-free.
- [ ] Design decisions recorded with rejected alternatives, before implementation.
- [ ] Law cycle done, or the law-cycle question answered No with a reason.
- [ ] Every new guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The count belongs to the batch, not the headline.** `_parse_news` sees one ticker at a time and
must keep returning every headline.
🪤 **`sentiment_articles` will start lying if you let it.** DL-112 is the precedent and it cost real
vetoes.
🪤 **The composite renormalises over present pillars.** Absent sentiment is not neutral — it changes
the pillar mix. This is why the "4 tickers lose their signal" number mattered.
🪤 **Do not re-litigate drop vs weight.** DL-127 measured it. If you think the measurement is wrong,
say so with numbers, do not quietly implement the other one.
🪤 **This is one run's evidence.** The measurement bounds the effect on `sched-2026-08-21`; it does
not prove the bound holds on every run. Do not write a success factor that claims it does.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. 🪤 But this sprint should add **no**
  tunable; if you find yourself wanting one, that is the `1/sqrt(n)` road not taken, and it is closed.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 11 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — redirect to a file and read the file.
- Version bump of the kind named at the top (fix → PATCH), `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving**, and **check the printed
   SHA against `git rev-parse HEAD`**.
2. Merge to `main` locally and push. 🪤 Check you are not on the branch already.
3. **Post-merge CodeQL** — `codeql.yml` runs only on `main` (work-queue item 31).
4. **Deploy: image-only retag** if the vocabulary hash is unchanged — verify, do not assume.
5. **Read the next scheduled run's scanner ranking and analyst confidences** against the pre-merge
   ones. The behaviour change is intended; confirm it looks like the measurement predicted.
   🚨 **Read those two numbers directly — do NOT read the acceptance verdict.** The deliberator has
   no LLM credit until **Sunday 2026-08-30** (operator-stated; `docs/STATE.md`), so every scheduled
   run until then fails acceptance on `debate_coverage: 0.0` and `failed_open_count > 0` **for a
   reason that has nothing to do with this sprint**. A red gate on the first post-merge night is the
   expected background state, not evidence about `1/n`. If you want a clean read, compare the
   analyst's per-ticker `confidence` and the scanner's ranking, ticker by ticker, against the
   pre-merge run.

---

## Handover — paste this to Codex

```text
Sprint 186 - a headline about twenty companies is not news about one.
Branch: sprint-186-a-headline-about-twenty-companies-is-not-news-about-one (create it BEFORE any
code, off main, never work on main). Full spec:
docs/sprints/sprint-186-a-headline-about-twenty-companies-is-not-news-about-one.md - read it whole.

THE PROBLEM. Finnhub /company-news?symbol=X returns market-wide content and _parse_news applies no
relevance test, so "Which dow jones stocks are moving on Tuesday?" counts once, in full, for each of
the twenty tickers it is filed under. score_sentiment is an unweighted mean, so this moves the
number, and the scanner ranks on it. Measured on sched-2026-08-21: 50.9% of headline slots are filed
under 2+ tickers, 23.4% under 5+, 14.8% under 10+.

WHAT SHIPS. Weight each headline by 1 / n_tickers inside score_sentiment's mean, where n_tickers is
how many distinct tickers in THIS BATCH the headline appears under. Nothing else.

SCOPE OF n - GET THIS WRONG AND EVERYTHING ELSE LOOKS RIGHT. Count n over the WHOLE market.news
batch that score_candidates holds (98 tickers on the fixture run), NOT over the candidate set or the
28 tickers in the fixture's baseline block. Measured 2026-08-24: counting over the candidates puts
KO at 0.600, which does NOT cross the 0.600 floor, and the sprint's one floor crossing vanishes.
Same code, different denominator, different result. analyze.py::score_candidates already holds
market.news; scoring.py is at 177 lines, 23 from the 200 hard block, so split rather than squeeze.

THE SHAPE IS ALREADY DECIDED - DO NOT RE-LITIGATE IT. DL-127 measured drop-at-N versus down-weight
through the real pipeline and chose down-weight: it silences 0 tickers where dropping silences 4
(CMCSA, GD, PEP, TXN), it discards 0% of slots where dropping discards 23.4%, and its worst
downstream confidence shift is 0.034 against drop's 0.065. If you think that measurement is wrong,
say so WITH NUMBERS - do not quietly implement the other one.

READ THE LAWS FIRST - THIS IS A GATE, NOT ADVICE.
- Read agents/analyst/laws/laws.md whole, plus its test-plan.md, docs/laws/conventions.md and
  docs/laws/drift-register.md, BEFORE you open an editor. Also read agents/provider/laws/laws.md -
  it is LOCKED v1 - to check whether the provider owes anything about news relevance. If it is
  silent, that silence is a drift row, NOT a licence to change the provider.
- Fill the "Law reading record" table at the bottom of the spec BEFORE your first code change.
- If a law contradicts the spec, STOP and report.

LAW-CYCLE QUESTION - answer it, do not assume. The score keeps its type, range and meaning, so
probably no clause is owed. BUT if you add or rename any sentiment_* metric, the cycle IS owed:
the analyst's OBS clauses require metrics to name unit AND scope. DL-112 is the precedent - the last
time a sentiment metric's name stopped matching its unit, the deliberator reported the feed as
inconsistent and VETOED REAL ORDERS on it.

FOUR DESIGN DECISIONS - record in docs/design-log.md with rejected alternatives BEFORE coding:
  1. Where is the duplication count computed and how does it reach score_sentiment? It CANNOT be
     _parse_news - the count is a property of the BATCH, not a headline, and the parser sees one
     ticker at a time. _parse_news must keep returning every headline.
  2. What counts as "the same headline"? Exact string match is what the measurement used. Check
     whether normalisation (case, whitespace, the vendor's mojibake - the real data contains
     "Today�s Session") changes the count materially. MEASURE before choosing.
  3. What do the metrics report now? sentiment_articles counts headlines that scored; under
     weighting, article count and total weight diverge. Keep it an article count and add a distinct
     weight metric, or rename - either way the name must state unit and scope. See DL-112.
  4. What happens when ALL of a ticker's headlines are heavily duplicated? The weights shrink but
     num/den is still well-defined, which is why 1/n silences nobody. Prove it in a test.

HARD LIMITS:
- ZERO provider change. No new request, no vendor field, no new provider setting, no change to the
  news cap. The count comes from the batch already served, at zero API cost. If your change adds a
  request, STOP and report.
- No relevance model, no NLP, no entity extraction. Duplication count only.
- No change to the lexicon, the sub-score formula, or the "pos + neg == 0" skip.
- No change to sentiment_weight (0.2) or any composite weight.
- NO NEW TUNABLE. 1/n is parameter-free by design (DL-127 reason 5). If you want an exponent, that
  is the 1/sqrt(n) road not taken and it is closed.

TESTS - plant them first, watch them fail, paste the red output:
  A1 a shared headline pulls 1/n as hard as an exclusive one. Assert the SCORE, not a helper call.
  A2 a ticker whose headlines are all heavily shared still gets a score (not None).
  A3 a ticker with only exclusive news scores byte-identically to today. The fixture has four real
     ones - DUK, GILD, MET, TGT - so this need not be synthetic. It also has three tickers with no
     sentiment at all (DOW, SCHW, USB) exercising the renormalisation path.
  A4 headlines with no lexicon word are still skipped, not diluted toward neutral.
  A5 the metrics name their unit and scope after weighting (DL-112).
  A6 reproduce the measurement from the committed fixture
     agents/analyst/tests/data/news_sched_2026_08_21.json - it holds the whole 98-ticker news batch
     plus the 28-ticker analyst baseline (technical/fundamental/sentiment/composite/confidence), so
     no graph or .env access is needed. KO 0.605 -> 0.599, and ZERO tickers lose their score.

CONTEXT YOU WILL NEED:
- _composite renormalises over PRESENT pillars, so absent sentiment is not neutral - it changes the
  pillar mix. SCHW and DOW took that path on 2026-08-21 with no incident.
- This is bidirectional noise, not a safety bug. DL-117's original "mis-attributed news is buying
  stocks" was RETRACTED - every approved order scores HIGHER once contamination is removed. Ship it
  for accuracy, not for safety, and do not write alarming wording back into the docs.
- The measurement bounds the effect on ONE run. Do not write a success factor claiming it
  generalises.
- Take the next free DL number and RE-CHECK IT AT MERGE. Highest as of 2026-08-22 is DL-127.

NO LLM UNTIL SUNDAY 2026-08-30. The deliberator is out of credit until then, so every scheduled run
fails acceptance on debate_coverage 0.0 for an unrelated reason. This sprint needs no LLM at any
point - if something you are doing seems to need one, you have left the scope. And when the
post-merge run is read, read the analyst confidences and scanner ranking directly; the red
acceptance verdict is background noise, not a verdict on this change.

GATE: make ci, all 11 steps, exit 0, 100.00% coverage. Redirect to a FILE and read the file - never
pipe it, because make ci | tail reports tail's exit code, not make's. Then push and run make
gate-ran FROM THE WORKTREE whose HEAD is the commit you are proving; check the printed SHA against
git rev-parse HEAD. Do not merge - hand back.

HANDBACK: fill the Law reading record, the Test plan results table, Closeout - evidence (real pasted
output, red run first), and Return notes. Set Status: to BUILT. State anything not met plainly as
"verified failing" or "not done". An incomplete handback is returned, not repaired.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02).

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?**

**Contradictions found between a law and this spec:**

**Laws found silent where a decision was needed:** *Check specifically whether the provider law says
anything about news relevance.*

**Clauses that were ⬜ and are now proven:**

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | | | | |
| A2 | | | | |
| A3 | | | | |
| A4 | | | | |
| A5 | | | | |
| A6 | | | | |

**Tests added beyond the plan:**

---

## Closeout — evidence

<!-- FILL THIS IN BEFORE HANDING BACK. A handback with this placeholder intact is not accepted. -->

**Status:** *not yet implemented.*

**Tree the proofs ran in (and `.env` present?):**

**Result:** *not yet implemented.*

**Files changed:**

**Design decisions:** *the four above, as a DL entry with rejected alternatives.*

**Proof — the red run first:**

**Proof — the green run:**

**The measurement reproduced (A6):** *`KO` 0.605 → ?, tickers losing their score → ?*

**Guards planted:**

**Module line counts:**

**`make ci`:** *exit code, passed/skipped counts, coverage %.*

**`make gate-ran`:** *worktree path and full 40-char SHA.*

**Not met / verified failing:**

---

## Return notes

-
