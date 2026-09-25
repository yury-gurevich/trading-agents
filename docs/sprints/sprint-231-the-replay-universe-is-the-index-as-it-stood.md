<!-- Agent: planning | Role: sprint handover -->
# Sprint 231 — the replay universe is the S&P 500 as it stood on each day

**Phase:** Etalon-first continuous improvement (DL-19) · next leg P17, item **E17.2**
**Branch:** `sprint-231-the-replay-universe-is-the-index-as-it-stood`
**Status:** BUILT
**Version:** *next available MINOR at merge*
**Effort:** M
**Decisions:** [DL-226](../design-log.md) (the source: Wikipedia's change log + Alpaca SIP bars) ·
[R008](../research/survivorship-free-universe/INDEX.md) (the E17.1 measurement) · work-queue **82** ·
the builder records its own decisions as the next free DL number

> **Why this bump kind.** The replay tooling gains a dimension it did not have: a point-in-time
> universe instead of today's ~98 survivors. That is a MINOR. Nothing in `agents/`, `contracts/`,
> any image or any law book changes.

**Builder:** Codex. Every behaviour is pinned by a row in the test plan.
**If a number you measure differs from one written here, stop and report. Do not adjust and continue.**

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

**No agent law book binds `scripts/`.** What binds this sprint: [`docs/laws/conventions.md`](../laws/conventions.md)
(module header, no magic numbers, clause citations), the repo rules in `CLAUDE.md` (200-line block,
which covers `scripts/` since 2026-09-23; header `Agent:`/`Role:`/`External I/O:`), DL-226, and the
**licensing rule** stated in `scripts/replay_dataset.py`'s docstring: *the repository is public and
Alpaca SIP bars are licensed, so the cache lives outside the worktree and is never committed.*

### The rule

1. **Before writing code**, read the files in the map below — whole file, first time.
2. There is no agent `test-plan.md` for `scripts/`; the **test plan in this spec is the contract**.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a rule contradicts this spec, STOP and report.**
7. **If a rule is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Tests cite what they prove in their docstrings (there are no clause IDs here; cite the test-plan
   row, e.g. `"""S231-A4: ..."""`).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**The planner's expected answer is No.** Everything lives in `scripts/` and `tests/`; no agent, no
contract, no image. If your design needs an agent or `contracts/` change, stop and report.

### Element → rule map

| Element you will touch | Read first | Why it binds |
| --- | --- | --- |
| new `scripts/sp500_*.py`, `scripts/replay_universe.py` | `CLAUDE.md` (module size, header); `docs/laws/conventions.md` | every module < 200 lines, header required; named constants with a reason, no bare literals |
| `scripts/replay_dataset_sources.py` (86 lines) | its docstring; `scripts/replay_dataset.py` docstring | the licensing rule; `daily_bars` is also used by the existing cache build |
| `scripts/replay_dataset.py` (142), `scripts/exp013_regime_sizing.py` | read only | **must not change behaviour**: EXP-011 to EXP-013 reproduce from `bars.csv.gz` / `vix.csv.gz` via `load()` |
| `scripts/sp500_symbol_map.csv` (new, committed) | [R008](../research/survivorship-free-universe/measurement.md), DL-226 | facts only, each row with its evidence |

⚠️ **One invariant: no licensed or copied data enters the repo.** No bar, no fetched Wikipedia HTML,
no generated membership file is committed. Test fixtures are **synthetic** HTML that reproduces the
measured table structure, not copied article text. The cache path is outside the worktree, and the
builder must refuse a cache path inside it (A12).

---

## Goal

`scripts/replay_universe.py build` writes, into the existing replay cache directory, the S&P 500 as it
stood on every session from 2016-01-04: membership **episodes** reconstructed from Wikipedia's current
constituents and dated change log, corrected by a committed **symbol map**; split- and
dividend-adjusted Alpaca SIP daily bars for every episode, fetched only inside the episode's window;
and a **coverage report** that states member-session coverage and names every shortfall with a
reason. `--describe` prints it without fetching. The existing cache files and `load()` are untouched.

## Why (context)

P17's exit is ten years of out-of-sample, **survivorship-free** results. Today's replay dataset is the
~98 names the book trades now, projected back, which EXP-013 named as its largest limitation. E17.1
(R008) measured that the universe can be sourced on the plans we pay for. This sprint builds it, so
E17.3's harness has a universe to replay.

### Measured, 2026-09-25 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Where membership comes from | FMP → **402/403**, Finnhub → **403**; Wikipedia works | *[measured 2026-09-25]* R008 |
| The two source pages | constituents: `https://en.wikipedia.org/wiki/List_of_S%26P_500_companies`, table `id="constituents"`; changes: `https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500`, table `id="changes"` | *[measured]* The changes table **moved** to its own article on 2026-08-11 (revision comment *"move to [[Historical components of the S&P 500]]"*). Find tables **by id**, never by position |
| Constituents table | header `Symbol, Security, GICS Sector, GICS Sub-Industry, Headquarters Location, Date added, CIK, Founded`; **503** rows; symbols keep dots (`BRK.B`, `BF.B`) | *[measured]* revision `1375923233` |
| Changes table structure | 2 header rows; **only the header** uses `rowspan` (3 cells) and `colspan` (2 cells); body rows carry their own date, no spans; **409** body rows: **407** with 7 cells (date, added ticker, added security, removed ticker, removed security, reason, refs), **2** with 6 (no refs cell); every date is `Month D, YYYY`; **19** rows have no added ticker, **23** no removed ticker; **2** ticker cells carry a stray `" \|"` suffix (`ALLE \|`, `JCP \|`, `ITT \|`, all pre-2016) | *[measured]* revision `1376064088` |
| Reconstruction from the log alone | 244 changes since 2016; daily count **503–508**; **3** unreconciled records since 2016: `FLT` (2018), `RE` (2017), `SATS` (2026), each a **rename the log does not record** | *[measured]* R008; the three renames appear in Alpaca's name-change feed: FLT→CPAY 2024-03-25, RE→EG 2023-07-10, SATS→ECHO 2026-06-24 |
| Why the count reads 508 | an unrecorded rename leaves **both** tickers "members" (FLT *and* CPAY), so the count inflates | *[measured]* the three renames above account for the excess |
| Sessions | **2,697** SPY sessions 2016-01-04 → 2026-09-24; weekdays are 2,800 | *[measured]* 🪤 R008's first figure (95.3 %) divided by weekdays and was **understated**; over sessions it is **98.9 %** |
| Coverage before this sprint's fixes | member-sessions **1,369,517**; covered **1,354,817** (**98.9 %**); removed names **96.8 %**, current **99.4 %** | *[measured]* R008, recomputed over sessions |
| 🪤 Alpaca drops symbols from batches, silently | with `adjustment=raw`, 2016→2026, a **3-symbol** batch `DD,DOW,DUK` returned no `DOW`; a 50-symbol batch returned 49/50 (no `DOW`); `DLPH` likewise. Single requests return them: DOW **2,697** sessions, DLPH **503** bars 2016-01-04 → 2017-12-29. A short window (`DOW,XOM`, September 2026) returned both | *[measured]* The existing cache (`adjustment=all`) **has** DOW, so the drop is not universal. Never infer absence from a batch |
| Alpaca refuses recent SIP bars on our plan | `end` = today → **403**; yesterday works | *[measured]* |
| Renames Alpaca files under the **old** ticker | PSKY's line: `CBS` 2016-01-04 → 2019-12-04, `VIAC` 2019-12-05 → 2022-02-16, `PARA` from 2016 (!), `PSKY` from 2025-08-07; `MYL` → 2020-11-16, `VTRS` from 2020-11-12; `PX` 2016 → 2026-02-10, `LIN` from 2018-10-31; `APTV` from 2017-11-17 | *[measured]* single requests. `PARA` and `PX` run past their company's life: the tickers were **reused** |
| Renames Alpaca files under the **new** ticker | `META`, `CPAY`, `EG` have bars from 2016-01-04; `FB`, `FLT`, `RE` return none | *[measured]* |
| Ticker reuse | `TE` (TECO → T1 Energy 2025), `STI` (SunTrust → Solidion 2024), `MON` (bars to 2022, Monsanto left 2018), `PX`, `Q` (Quintiles 2017 → Qnity 2025), `SNDK` (SanDisk 2016 → spin-off 2025), `DOW` (Dow Chemical → Dow Inc 2019), `AA` (the 2016 Alcoa/Arconic split) | *[measured]* Alpaca name-change feed + bar ranges |
| Genuinely missing | `STI` and `TE` return **0** bars for their member windows, alone or batched; Tiingo has neither | *[measured]* 0.2 % of member-sessions |
| Alpaca's name-change feed | starts in practice in **2019** (0, 2, 2 rows for 2016–2018); misses mergers (`PX`→`LIN`, `MYL`→`VTRS`) | *[measured]* R008 follow-up |
| Membership boundary convention | a name added with effective date *D* is a member **from** *D*; a name removed on *D* is a member **through** the session before *D* | *[ASSUMED]* S&P announces changes "effective prior to the open" on *D*. Not measured; the effect is one session per change |
| Existing cache | `bars.csv.gz` 3.1 MB (263,005 rows, 98 names), `vix.csv.gz` 42 KB, in `~/OneDrive/trading-agents-data/` | *[measured]* |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first** (A1–A3), on synthetic fixtures. Watch them fail.
2. **`scripts/sp500_wiki.py`**: fetch the two pages (`requests`, a descriptive `User-Agent` as
   Wikipedia's policy requires) and parse them with the **standard library** (`html.parser`), finding
   each table **by id**. Return typed rows: `Constituent(symbol, security, date_added, cik)` and
   `Change(date, added, removed, reason)`, with tickers normalised (strip whitespace and a trailing
   `" |"`), empty cells as `None`, 6- or 7-cell rows read positionally, and the page's
   `"wgRevisionId"` extracted for the manifest.
3. **`scripts/sp500_membership.py`**: load the symbol map; reconstruct membership over a session list
   by undoing changes backwards from the current constituents to the start date, then replaying
   forwards; apply `rename` rows so a renamed line is **one line** with two consecutive episodes, never
   two concurrent members; return `Episode(line, ticker, first, last)` rows plus a reconciliation
   report: daily member count min/max, and every unreconciled record (an added ticker not in the set
   when undone), listed, never dropped.
4. **`scripts/sp500_symbol_map.csv`** (committed): the rows in *The symbol map* below, each with its
   evidence. Code reads it as data; **no ticker is hard-coded in Python.**
5. **`scripts/sp500_bars.py`**: turn episodes (and `bars` rows) into `(line, symbol, first, last)`
   windows; fetch them with `adjustment=all` through the existing `replay_dataset_sources.daily_bars`
   (give it a `start` keyword that defaults to today's `START`, so the existing build is unchanged);
   batch for speed, then **verify every window**: any symbol a batch returned empty or short is
   re-fetched **alone** before it may be called missing; keep only bars inside the window.
6. **`scripts/sp500_coverage.py`**: member-sessions per line, covered sessions, the ratio, and per-line
   shortfalls with a reason (`no bars`, `starts late`, `ends early`, `gap`). A named floor of **0.90**
   (the plan's E17.1 bar) with a comment citing it; the build exits non-zero below it.
7. **`scripts/replay_universe.py`**: the CLI. `build [--end YYYY-MM-DD] [--from-snapshot]` writes
   `sp500_pages.json.gz` (both HTML pages, their URLs, revision ids, fetch time), `sp500_sessions.csv.gz`
   (SPY's session dates, fetched in the same run), `sp500_membership.csv.gz`, `sp500_bars.csv.gz` and
   `sp500_coverage.json` into the existing cache directory (`replay_dataset.CACHE`, which honours
   `REPLAY_DATASET_DIR`). `--from-snapshot` rebuilds membership from the saved pages with no fetch.
   `--describe` prints the reconciliation and coverage report. `load_universe()` reads it back.
8. **Design decisions** recorded in `docs/design-log.md` (next free DL number) before implementing.

### The symbol map — seed rows (all evidence measured 2026-09-25 unless marked)

Columns: `kind,line,symbol,from,to,evidence`. Two kinds:

- `rename`: the line known today as `line` was `symbol` before `from`, and the change log does not say
  so. Reconstruction treats it as an internal switch: backwards past `from` the line's ticker becomes
  `symbol`; forwards it becomes `line` on `from`.
- `bars`: for the line's member-sessions in `[from, to]`, bars come from Alpaca `symbol`. It overrides
  the episode's ticker as the bar source inside that range only.

```csv
kind,line,symbol,from,to,evidence
rename,CPAY,FLT,2024-03-25,,alpaca name_change FLT->CPAY 2024-03-25
rename,EG,RE,2023-07-10,,alpaca name_change RE->EG 2023-07-10
rename,ECHO,SATS,2026-06-24,,alpaca name_change SATS->ECHO 2026-06-24
bars,PSKY,CBS,2016-01-04,2019-12-04,alpaca CBS bars end 2019-12-04; VIAC bars start 2019-12-05
bars,PSKY,VIAC,2019-12-05,2022-02-16,alpaca name_change VIAC->PARA 2022-02-17
bars,PSKY,PARA,2022-02-17,2025-08-06,alpaca PSKY bars start 2025-08-07
bars,VTRS,MYL,2016-01-04,2020-11-16,alpaca MYL bars end 2020-11-16; name_change VTRSV->VTRS 2020-11-17
bars,LIN,PX,2016-01-04,2018-10-30,alpaca LIN bars start 2018-10-31; PX bars after that are another issuer
bars,APTV,DLPH,2016-01-04,2017-12-04,alpaca DLPH single request 2016-01-04..2017-12-29; switch date ASSUMED (Aptiv rename)
```

Add **no** row you cannot evidence from this spec. The planner extends the map from the live coverage
report after merge; that is the loop by design, not a gap in your work.

### Out of scope (do NOT build this sprint)

- **The replay harness (E17.3)** and any change to `agents/researcher/domain/backtest.py`.
- **Any change to `bars.csv.gz`, `vix.csv.gz`, `load()` or the live-universe build.**
- **Fundamentals, sectors, news** for historical names: bars and membership only.
- **Automatic rename discovery** from Alpaca's feed (see *Road not taken*).
- **No network in tests.** Every test runs on synthetic fixtures and injected fetchers.
- **No new dependency.** Standard library plus what `pyproject.toml` already has (`requests`,
  `python-dotenv`).

### The road not taken (LAW-06)

- **`pandas.read_html`.** Rejected: pandas, numpy and lxml would join a public repo's dependency audit
  for one table whose structure is measured and regular (header-only spans, positional body rows).
  The operator offered to install it (2026-09-25); it was not needed.
- **Buy FMP's constituent data.** Rejected in DL-226: a plan upgrade for what the public log gives to
  within the three renames above. Revisit only if E17.4's fidelity check traces a miss to membership.
- **Derive renames automatically from Alpaca's name-change feed.** Rejected for now: the feed is empty
  before 2019 and misses mergers, so it cannot be the whole source; a committed map with evidence per
  row is auditable, and the feed stays the evidence the planner cites.
- **Fill missing names from Tiingo.** Rejected: Tiingo has neither STI nor TE (measured), and its
  500-symbol monthly cap is shared with the live fallback.
- **Commit a copied excerpt of the Wikipedia tables as a fixture.** Rejected: the text is CC BY-SA and
  the repo is public; a synthetic fixture with the measured structure tests the parser just as well.
- **Coverage over weekdays.** Rejected: it counts every market holiday as a gap (R008's first figure,
  corrected). Sessions are SPY's bar dates.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md`, with their rejected alternatives, BEFORE implementing (LAW-06).**

1. **The episode model:** how a line, its ticker episodes and `rename` rows are represented, and how
   the reconstruction stays symmetric (undo backwards, replay forwards, same result).
2. **Batch verification:** the rule for "short" (for example, fewer bars than the window's sessions
   minus a small tolerance) and how the single re-fetch is paced.
3. **The shortfall reasons** and how each is detected from bars and sessions alone.
4. **The file formats** of the five cache files, and how `--from-snapshot` reproduces a build.

🪤 **Take the next free DL number, then re-check it at merge.** The log's newest entry today is DL-226.

---

## Blast radius — measured 2026-09-25

| What | Detail |
| --- | --- |
| Files changed | new `scripts/sp500_wiki.py`, `scripts/sp500_membership.py`, `scripts/sp500_bars.py`, `scripts/sp500_coverage.py`, `scripts/replay_universe.py`, `scripts/sp500_symbol_map.csv`; edited `scripts/replay_dataset_sources.py` (**86**, a `start` keyword only); new tests `tests/sp500_fixtures.py`, `tests/test_sp500_*.py`, `tests/test_replay_universe.py` |
| Agents affected | **none** |
| Contract change? | **no** |
| Graph vocabulary change? | **no** (the build reads no graph) |
| New env keys / tunables | none; reuses `ALPACA_API_KEY`/`ALPACA_API_SECRET` and `REPLAY_DATASET_DIR` |
| Deploy implication | **none**: `scripts/` ships in no image |

🪤 **`scripts/` is outside the coverage floor** (`[tool.coverage.run] source` omits it), so `make ci`
will not force tests on these modules. **The test plan below is the contract**: every row must exist.

---

## Steps, in order

1. **Read the rules** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Plant the failing tests first** (A1–A3) and watch them fail. Paste the red output.
4. **Implement** scope items 2–7.
5. **Prove the guards can fail (DL-70)**: for A4, A8 and A12, break the implementation (drop the rename
   application; trust the batch; allow an in-repo cache path), watch each go red, restore.
6. **`make ci` green** — every step of the `ci:` target, **redirected to a file, never piped**.
7. **Fill the handback sections** at the bottom of this file. You have no network and no `.env`, so
   state plainly that no live build ran; the planner runs it.

---

## Test plan

Fixtures are **synthetic**: `tests/sp500_fixtures.py` builds HTML with the measured structure (two
header rows with `rowspan`/`colspan`, 7- and 6-cell body rows, a stray `" |"`, empty added/removed
cells, `Month D, YYYY` dates) and a small universe of made-up tickers. Fetchers are injected fakes.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 the changes table parses | synthetic `id="changes"` table: 2 header rows, a 7-cell row, a 6-cell row, `"ABC \|"`, an empty removed cell | typed `Change` rows; `"ABC"`; `removed is None`; dates parsed; the header rows are not data |
| A2 | the constituents table parses, found by id | a page with a decoy table first, then `id="constituents"` with `BRK.B` | `BRK.B` kept with its dot; the decoy is ignored; `revision_id` read from `"wgRevisionId"` |
| A3 | 🎯 reconstruction is exact on a known history | 6 current names, 4 dated changes, a session list | membership on each session equals the fixture's truth; the count is constant; undo-then-replay is symmetric |
| A4 | 🪤 a `rename` row prevents a double count | log adds `OLD` on *D1*; current list has `NEW`; map `rename,NEW,OLD,D2` | one line `NEW`, episodes `OLD [D1, D2-1]`, `NEW [D2, end]`; count constant. **Without the row:** the record is reported unreconciled and the count reads one high |
| A5 | unreconciled records are listed, never dropped | a log row adding a ticker that no longer exists and has no map row | it appears in the report with its date and ticker |
| A6 | 🪤 ticker reuse gives two episodes, and bars stay inside them | `DUP` removed on *D1*, re-added on *D3* (a different company); the fake fetcher returns `DUP` bars for every session | two episodes; bars between *D1* and *D3* are not used |
| A7 | a `bars` row switches the bar source inside its range only | line `NEWCO`, map `bars,NEWCO,OLDCO,from,to` | sessions in `[from, to]` read `OLDCO`; after `to`, `NEWCO` |
| A8 | 🪤 a symbol a batch drops is re-fetched alone | a fake that omits `DROP` from any multi-symbol call but returns it singly | `DROP` is covered; exactly one single re-fetch; a symbol empty both ways is reported `no bars` |
| A9 | coverage is counted over sessions, with reasons | episodes, sessions with a holiday gap, bars missing at a start, an end and a middle | member-sessions exclude non-sessions; reasons `starts late`, `ends early`, `gap`, `no bars`; the ratio is exact |
| A10 | the floor fails the build | coverage 0.89 | exit code non-zero and the shortfall printed; 0.90 passes |
| A11 | the existing cache is untouched | `REPLAY_DATASET_DIR` = a tmp dir holding `bars.csv.gz`/`vix.csv.gz` | the build writes only `sp500_*` files; the old files' bytes are unchanged; `replay_dataset.load()` still reads them |
| A12 | 🪤 the cache may not live in the repo | `REPLAY_DATASET_DIR` inside the repo root | the build refuses before fetching anything, and says why |
| A13 | `--from-snapshot` rebuilds with no network | a saved `sp500_pages.json.gz`; a fetcher that raises if called | the same membership as the original build; the fetcher was never called |
| A14 | `daily_bars` keeps its old behaviour | call without `start` | the request's `start` is today's `START`; with `start=` it is honoured |

---

## Success factors

- [ ] `replay_universe.py build` (with fakes) writes the five `sp500_*` files; `--describe` prints the
      reconciliation (count min/max, unreconciled records) and coverage (ratio, shortfalls by reason).
- [ ] A rename in the map yields one line, never a double count (A4); a reused ticker yields separate
      episodes whose bars stay inside their windows (A6).
- [ ] No symbol is called missing on a batch's word alone (A8).
- [ ] No licensed or copied data in the repo; the build refuses an in-repo cache path (A12).
- [ ] `bars.csv.gz`, `vix.csv.gz` and `load()` behave exactly as before (A11, A14).
- [ ] Design decisions recorded with rejected alternatives; law-cycle question answered No.
- [ ] Guards A4, A8, A12 planted, watched to fail, restored, stated per guard.
- [ ] Every touched Python module < 200 lines, with the header.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **A batch that omits a symbol looks exactly like a symbol with no history.** Measured on DOW and
DLPH. Verify every symbol before reporting it missing.
🪤 **A reused ticker returns real bars for the wrong company.** Measured on PX, PARA, MON, TE, STI.
Bars are valid only inside the window the membership (or a `bars` row) assigns.
🪤 **The changes table is no longer on the constituents page.** Fetch both pages; find tables by id.
🪤 **Weekdays are not sessions.** Counting them turned 98.9 % into 95.3 % in E17.1's first pass.
🪤 **`end` = today is refused (403)** on our plan: default `--end` to yesterday or earlier.
🪤 **The existing experiments read the existing files.** Touch `bars.csv.gz`, `vix.csv.gz` or `load()`
and EXP-011 to EXP-013 stop reproducing.
🪤 **Your worktree has no `.env` and no network.** Any "it works on live data" claim from it is
vacuous; prove on fixtures and say so.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to dodge a rule.
  📌 Current sizes: `replay_dataset.py` **142**, `replay_dataset_sources.py` **86**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:` (`Agent: tooling`, as the existing
  replay scripts do).
- No magic numbers: the 0.90 floor and any tolerance are named constants with a comment saying why.
- Faults, not silent failure: a missing symbol, an unreconciled record and a short window are
  reported, never skipped quietly.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving**, and check the printed
   SHA against `git rev-parse HEAD`.
2. Merge to `main` locally and push. 🪤 Not from the branch's own worktree. Post-merge CodeQL.
3. **No deploy.** `scripts/` ships in no image.
4. **Planner's live build (the functionality check):** from the main checkout with `.env`, run
   `replay_universe.py build --end <yesterday>`, then `--describe`. Pass: coverage **≥ 0.90** (expected
   ≥ 0.989, the pre-sprint measurement), unreconciled records since 2016 **0** with the three seed
   renames, daily count within **500–505** *[expected, not measured]*. Every shortfall listed with a
   reason; extend the symbol map for any that is a rename, with evidence, and rebuild
   `--from-snapshot`. Confirm no `sp500_*` file is inside the repo (`git status` clean). Record it in
   `docs/laws/functionality-checks.md`.

---

## Handover — paste this to Codex

```text
Sprint 231 — the replay universe is the S&P 500 as it stood on each day (P17, E17.2).
Spec: docs/sprints/sprint-231-the-replay-universe-is-the-index-as-it-stood.md (read all of it).

Branch: sprint-231-the-replay-universe-is-the-index-as-it-stood, in its own worktree. Never main.
You have NO network and NO .env. Build and prove everything on synthetic fixtures and injected fakes.
The planner runs the live build after merge.

MUST RULE before any code: no agent law book binds scripts/; read CLAUDE.md (200-line block covers
scripts/, module header), docs/laws/conventions.md, docs/laws/drift-register.md, DL-226 and
docs/research/survivorship-free-universe/measurement.md. Fill the Law reading record in the spec
BEFORE the first code change. Law-cycle answer expected: NO (scripts/ and tests/ only).

Build (scripts/ + tests/ only):
1. scripts/sp500_wiki.py: fetch the two Wikipedia pages (requests, descriptive User-Agent) and parse
   them with the STANDARD LIBRARY html.parser, tables found BY ID ("constituents", "changes").
   Measured structure: 2 header rows (header-only rowspan/colspan); body rows 7 cells (date, added
   ticker, added security, removed ticker, removed security, reason, refs) or 6 (no refs); dates
   "Month D, YYYY"; empty added/removed cells; stray " |" after some tickers; keep dots (BRK.B).
   Extract "wgRevisionId".
2. scripts/sp500_membership.py: load scripts/sp500_symbol_map.csv; reconstruct membership over a
   SESSION list (undo changes backwards from the current list, replay forwards); `rename` rows make a
   renamed line ONE line with two consecutive episodes, never two concurrent members; report daily
   count min/max and every unreconciled record (never drop one).
3. scripts/sp500_symbol_map.csv: exactly the seed rows in the spec. No row you cannot evidence.
4. scripts/sp500_bars.py: windows from episodes and `bars` rows; fetch with adjustment=all through
   replay_dataset_sources.daily_bars (add a `start` keyword defaulting to START); batch, then VERIFY
   EVERY SYMBOL: empty or short in a batch -> re-fetch alone before calling it missing; keep only bars
   inside the window.
5. scripts/sp500_coverage.py: member-sessions (sessions = SPY bar dates), covered, ratio, shortfalls
   with reasons (no bars / starts late / ends early / gap); named floor 0.90 with a comment; build
   exits non-zero below it.
6. scripts/replay_universe.py: CLI build [--end] [--from-snapshot], --describe, load_universe();
   writes sp500_pages.json.gz, sp500_sessions.csv.gz, sp500_membership.csv.gz, sp500_bars.csv.gz,
   sp500_coverage.json into replay_dataset.CACHE; REFUSES a cache path inside the repo.

Order: record design decisions (next free DL number, re-check at merge) -> plant tests A1-A3 and paste
the red run -> implement -> tests A4-A14 -> break A4, A8, A12 on purpose, watch them fail, restore ->
make ci redirected to a file (never piped), exit 0.

DO NOT:
- commit any bar, any fetched Wikipedia HTML, any generated membership file, or copied article text.
  Fixtures are SYNTHETIC. The repo is public; SIP bars are licensed.
- change bars.csv.gz, vix.csv.gz, load() or the live-universe build (EXP-011..013 reproduce from them).
- add pandas or any other dependency.
- trust a multi-symbol Alpaca batch: it silently dropped DOW and DLPH (measured).
- use bars outside a symbol's window: tickers are reused (PX, PARA, MON, TE, STI measured).
- count weekdays as sessions.
- hard-code a ticker in Python; the symbol map is data.
- pin a version number: MINOR bump, next available at merge, uv.lock staged with it.
- claim a live build ran. You have no network.

Handback: fill Law reading record, Test plan results, Closeout evidence (red and green output, guards,
line counts, make ci file + exit code, make gate-ran from the worktree at the full SHA), Return notes.
Set Status: BUILT and change this sprint's README.md row to lead with BUILT in the same commit.
Anything not met: say "not done" or "verified failing". Never write a Result for work not done.
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

| Element | Files read | Rules that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `scripts/sp500_*.py`, `scripts/replay_universe.py`, tests | `CLAUDE.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md`; DL-226; `docs/research/survivorship-free-universe/measurement.md`; this spec | No agent law book binds `scripts/`; modules need headers, stay below 200 lines, avoid magic numbers, and cite S231 test-plan rows. | Yes: kept the implementation split across small script modules and cited S231 rows instead of law IDs. |
| `scripts/replay_dataset_sources.py` | its docstring; `scripts/replay_dataset.py` docstring; this spec | Only add a backward-compatible `start` keyword defaulting to `START`; keep the existing live-universe cache build behavior unchanged. | Yes: changed only the `daily_bars` signature and request `start` parameter. |
| `scripts/replay_dataset.py`, `scripts/exp013_regime_sizing.py` | both files read before edits | The existing `bars.csv.gz`, `vix.csv.gz`, and `load()` behavior stay untouched because EXP-011..013 reproduce through that cache. | Yes: no edits to `replay_dataset.py`, `exp013_regime_sizing.py`, or existing cache files. |
| cache/output handling | `scripts/replay_dataset.py` docstring; DL-226; R008 measurement | Alpaca SIP bars are licensed and the repo is public, so generated `sp500_*` files and fetched pages live only outside the worktree. | Yes: added repo-cache refusal and synthetic fixtures only. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No. Scope is `scripts/` and `tests/` plus the required sprint/design/state documentation; no `contracts/`, no agent law book, no image, and no new agent guarantee.

**Contradictions found between a rule and this spec:** None.

**Rules found silent where a decision was needed:** None; implementation choices are recorded as DL-227 before code.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Row cited |
| --- | --- | --- | --- | --- |
| A1 | `test_changes_table_parses_measured_structure` | `tests/test_sp500_wiki.py` | PASS | S231-A1 |
| A2 | `test_constituents_table_parses_by_id_and_keeps_dots` | `tests/test_sp500_wiki.py` | PASS | S231-A2 |
| A3 | `test_membership_reconstruction_matches_known_history` | `tests/test_sp500_membership.py` | PASS | S231-A3 |
| A4 | `test_rename_row_prevents_double_count` | `tests/test_sp500_membership.py` | PASS; guard failed when rename mapping was disabled | S231-A4 |
| A5 | `test_unreconciled_records_are_listed` | `tests/test_sp500_membership.py` | PASS | S231-A5 |
| A6 | `test_ticker_reuse_keeps_bars_inside_each_episode` | `tests/test_sp500_bars.py` | PASS | S231-A6 |
| A7 | `test_bars_row_switches_source_inside_range_only` | `tests/test_sp500_bars.py` | PASS | S231-A7 |
| A8 | `test_batch_drop_is_refetched_before_missing` | `tests/test_sp500_bars.py` | PASS; guard failed when single-symbol verification was removed | S231-A8 |
| A9 | `test_coverage_counts_sessions_and_classifies_shortfalls` | `tests/test_sp500_coverage.py` | PASS | S231-A9 |
| A10 | `test_coverage_floor_fails_build_below_floor` | `tests/test_sp500_coverage.py` | PASS | S231-A10 |
| A11 | `test_universe_build_leaves_existing_replay_cache_untouched` | `tests/test_replay_universe.py` | PASS | S231-A11 |
| A12 | `test_universe_build_refuses_repo_cache_before_fetching` | `tests/test_replay_universe.py` | PASS; guard failed when repo-cache refusal was disabled | S231-A12 |
| A13 | `test_from_snapshot_rebuilds_without_wikipedia_fetch` | `tests/test_replay_universe.py` | PASS | S231-A13 |
| A14 | `test_daily_bars_start_default_is_backward_compatible` | `tests/test_replay_universe.py` | PASS | S231-A14 |

**Tests added beyond the plan:** None.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\trading-agents-sprint-231-the-replay-universe-is-the-index-as-it-stood`, branch `sprint-231-the-replay-universe-is-the-index-as-it-stood`; `.env` absent (`Test-Path .env` -> `False`).

**Result:** Built the fixture-proven S&P 500 point-in-time replay-universe builder. No live Wikipedia or Alpaca build ran.

**Files changed:** `scripts/sp500_wiki.py`, `scripts/sp500_membership.py`, `scripts/sp500_symbol_map.csv`, `scripts/sp500_bars.py`, `scripts/sp500_coverage.py`, `scripts/replay_universe.py`, `scripts/replay_universe_cache.py`, `scripts/replay_dataset_sources.py`, `tests/sp500_fixtures.py`, `tests/test_sp500_wiki.py`, `tests/test_sp500_membership.py`, `tests/test_sp500_bars.py`, `tests/test_sp500_coverage.py`, `tests/test_replay_universe.py`, `docs/design-log.md`, `docs/STATE.md`, this sprint doc, `docs/sprints/README.md`, `pyproject.toml`, `uv.lock`.

**Design decisions:** recorded as DL-227 in [`design-log.md`](../design-log.md) — line episodes, batch verification, shortfall reasons, cache file formats, and rejected alternatives.

**Proof — the red run first:**

```text
uv run pytest tests/test_sp500_wiki.py tests/test_sp500_membership.py --no-cov
collected 3 items
tests\test_sp500_wiki.py FF
tests\test_sp500_membership.py F
FAILED ... ModuleNotFoundError: No module named 'scripts.sp500_wiki'
FAILED ... ModuleNotFoundError: No module named 'scripts.sp500_membership'
3 failed in 3.45s
```

**Proof — the green run:**

```text
uv run pytest tests/test_sp500_wiki.py tests/test_sp500_membership.py tests/test_sp500_bars.py tests/test_sp500_coverage.py tests/test_replay_universe.py --no-cov
collected 14 items
tests\test_sp500_wiki.py ..
tests\test_sp500_membership.py ...
tests\test_sp500_bars.py ...
tests\test_sp500_coverage.py ..
tests\test_replay_universe.py ....
14 passed in 1.99s
```

**Guards planted:** A4 broken by disabling rename mapping -> `AssertionError: assert 3 == 2`; restored. A8 broken by removing single-symbol re-fetch -> `AssertionError: assert ('DROP',) in [('DROP', 'EMPTY', 'KEEP')]`; restored. A12 broken by disabling repo-cache refusal -> `Failed: DID NOT RAISE RuntimeError`; restored and generated in-repo cache files removed.

**Module line counts:** `sp500_wiki.py` 195; `sp500_membership.py` 179; `sp500_bars.py` 163; `sp500_coverage.py` 102; `replay_universe.py` 161; `replay_universe_cache.py` 138; `replay_dataset_sources.py` 90; tests all <= 145.

**`make ci`:** `make ci > $env:TEMP\s231-ci.txt 2>&1`, exit 0. `3233 passed, 6 skipped`, coverage `100.00 %`; dependency audit: `No unaccepted vulnerabilities; 1 accepted advisory re-checked`; detect-secrets tracked and untracked passed (`detect-secrets (untracked): scanning 13 new file(s)`).

**`make gate-ran`:** not done. Local branch is committed; remote push/CI/gate proof was not run from this no-network build worktree.

**Not met / verified failing:** Live build not done by design; no network or `.env`. Remote push and `make gate-ran` not done.

---

## Return notes

- The planner must run the live `replay_universe.py build --end <yesterday>` after merge with `.env`; this branch proved only synthetic fixtures and injected fakes.
- No `bars.csv.gz`, `vix.csv.gz`, generated membership, fetched Wikipedia HTML, or Alpaca bar file was committed.
